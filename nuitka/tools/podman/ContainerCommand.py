#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Running Nuitka commands inside containers.

This is the main command integration for the ``nuitka --container`` option.

spell-checker: ignore Containerfile
"""

import os
import re
import shlex
import sys

from nuitka.options.Options import (
    getContainerIsolated,
    getContainerNetwork,
    getContainerNoBuild,
    getContainerPodmanPath,
    getContainerPodmanVerbose,
    getContainerPrivileged,
    getContainerPythonVersion,
    getContainerRequirements,
    getContainerSharedPaths,
    getContainerWheelsDir,
    getMainArgs,
    shallExecuteImmediately,
)
from nuitka.plugins.Plugins import (
    activatePlugins,
    getContainerFileContents,
    onContainerSelection,
    redactCommandLineArg,
)
from nuitka.Tracing import containers_logger
from nuitka.utils.Execution import quoteForShell
from nuitka.utils.FileOperations import (
    putTextFileContents,
    withTemporaryDirectory,
)

from .Container import getContainerPython, makeCompileCommand, runContainer
from .Podman import getPodmanExecutablePath

_container_wheels_dir = "/Nuitka-wheels"


def _makeRequirementsInstallCommand(
    container_name,
    container_python_version,
    requirements,
    wheels_dir_in_container,
):
    """Create the command to install user provided requirements and wheels in the container.

    Args:
        container_name: name of the container to use.
        container_python_version: str or None, Python version to use inside the
          container.
        requirements: sequence of pip requirement arguments.
        wheels_dir_in_container: str or None, directory with wheels inside the
          container.

    Returns:
        str, command to install the requirements and wheels inside the container.
    """
    python_binary = quoteForShell(
        getContainerPython(container_name, container_python_version)
    )

    requirement_args = []

    for requirement in requirements:
        requirement_args += shlex.split(requirement)

    install_args = [quoteForShell(argument) for argument in requirement_args]

    if wheels_dir_in_container is not None:
        # Unquoted, so the shell expands the wheel files.
        install_args.append("%s/*.whl" % wheels_dir_in_container)

    pip_install = (
        "%s -m pip install ${NUITKA_PIP_FLAGS} "
        "--disable-pip-version-check --no-warn-script-location" % python_binary
    )

    return "%s --upgrade pip && %s --upgrade %s" % (
        pip_install,
        pip_install,
        " ".join(install_args),
    )


def _getWheelsDir():
    """Get and validate the host directory with wheels.

    Returns:
        str or None, absolute path of the wheels directory.
    """
    wheels_dir = getContainerWheelsDir()

    if wheels_dir is None:
        return None

    wheels_dir = os.path.abspath(os.path.expanduser(wheels_dir))

    if not os.path.isdir(wheels_dir):
        return containers_logger.sysexit(
            "Error, wheels directory '%s' does not exist or is not a directory."
            % wheels_dir
        )

    if not any(
        filename.endswith(".whl")
        and not filename.startswith(".")
        and os.path.isfile(os.path.join(wheels_dir, filename))
        for filename in os.listdir(wheels_dir)
    ):
        return containers_logger.sysexit(
            "Error, no wheel files found in '%s'." % wheels_dir
        )

    return wheels_dir


def _addContainerPackageInstall(
    container_command,
    logged_command,
    container_name,
    container_python_version,
    requirements,
    wheels_dir,
):
    """Prepend the package installation to the container commands.

    Args:
        container_command: command to execute inside the container.
        logged_command: the command as shown in the output.
        container_name: name of the container to use.
        container_python_version: str or None, Python version to use inside the
          container.
        requirements: sequence of pip requirement arguments.
        wheels_dir: str or None, host directory with wheels.

    Returns:
        tuple of command and logged command with the installation prepended.
    """
    if not requirements and wheels_dir is None:
        return container_command, logged_command

    install_command = _makeRequirementsInstallCommand(
        container_name=container_name,
        container_python_version=container_python_version,
        requirements=requirements,
        wheels_dir_in_container=(
            _container_wheels_dir if wheels_dir is not None else None
        ),
    )

    return (
        "%s && %s" % (install_command, container_command),
        "%s && %s" % (install_command, logged_command),
    )


def runNuitkaInContainer(container_name, container_command):
    """Run the compilation or a command inside the selected container.

    Notes:
        This activates plugins, since they can provide container files and
        may want to react to the container selection.

    Args:
        container_name: name of the container to use.
        container_command: command to run inside the container instead of
          compiling, or None.

    Returns:
        None, exits with the container run exit code.
    """
    activatePlugins()

    onContainerSelection(container_name)

    container_python_version = getContainerPythonVersion()

    if container_python_version is not None and not re.match(
        r"^\d+\.\d+\.\d+$", container_python_version
    ):
        return containers_logger.sysexit(
            "Error, '--container-python-version' must be a full version like '3.12.3'."
        )

    if container_command is None:
        container_command = makeCompileCommand(
            container_name=container_name,
            container_python_version=container_python_version,
            args=sys.argv[1:],
            main_args=getMainArgs(),
            execute_immediately=shallExecuteImmediately(),
        )

        # The output shows the command with the values of sensitive options
        # redacted, as the compilation inside the container will do.
        logged_command = makeCompileCommand(
            container_name=container_name,
            container_python_version=container_python_version,
            args=[redactCommandLineArg(arg) for arg in sys.argv[1:]],
            main_args=getMainArgs(),
            execute_immediately=shallExecuteImmediately(),
        )
    else:
        logged_command = container_command

    requirements = getContainerRequirements()
    wheels_dir = _getWheelsDir()

    container_command, logged_command = _addContainerPackageInstall(
        container_command=container_command,
        logged_command=logged_command,
        container_name=container_name,
        container_python_version=container_python_version,
        requirements=requirements,
        wheels_dir=wheels_dir,
    )

    if (requirements or wheels_dir is not None) and not getContainerNetwork():
        containers_logger.info(
            "Enabling network access for container package installation."
        )

    # Make the Nuitka package importable inside the container even when the
    # working directory is a project rather than the Nuitka checkout.
    nuitka_package_dir = os.path.dirname(
        os.path.realpath(sys.modules["nuitka"].__file__)
    )
    source_mount_destination = "/nuitka-src/nuitka"

    shared_paths = list(getContainerSharedPaths())

    if wheels_dir is not None:
        shared_paths.append("%s=%s" % (wheels_dir, _container_wheels_dir))

    shared_paths.append("%s=%s" % (nuitka_package_dir, source_mount_destination))

    pythonpath_prefix = "export PYTHONPATH=/nuitka-src${PYTHONPATH:+:$PYTHONPATH}; "

    container_command = pythonpath_prefix + container_command
    logged_command = pythonpath_prefix + logged_command

    podman_path = getContainerPodmanPath()

    if podman_path is None:
        podman_path = getPodmanExecutablePath(containers_logger)

        assert podman_path is not None

    # The selected container file is written here from plugin provided
    # contents, if any.
    container_file_contents = getContainerFileContents(container_name)

    with withTemporaryDirectory(
        containers_logger, prefix="nuitka-plugin-container-"
    ) as plugin_container_dir:
        plugin_container_files = {}

        if container_file_contents is not None:
            container_file_path = os.path.join(
                plugin_container_dir, container_name + ".containerfile"
            )
            putTextFileContents(container_file_path, container_file_contents)

            plugin_container_files[container_name] = container_file_path

        runContainer(
            container_name=container_name,
            command=container_command,
            logged_command=logged_command,
            no_build=getContainerNoBuild(),
            podman_path=podman_path,
            quiet=not getContainerPodmanVerbose(),
            shared_paths=shared_paths,
            network=bool(requirements)
            or wheels_dir is not None
            or getContainerNetwork(),
            isolated=getContainerIsolated(),
            privileged=getContainerPrivileged(),
            plugin_container_files=plugin_container_files,
            container_python_version=container_python_version,
        )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
