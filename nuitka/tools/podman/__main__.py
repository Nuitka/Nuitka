#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Launcher for running a script inside a container.

Podman and Docker should both work, but the first one is recommended.
"""

import os
import shutil
import sys
from optparse import OptionParser

from nuitka.tools.release.Release import (
    getBranchName,
    getBranchRemoteIdentifier,
)
from nuitka.Tracing import OurLogger
from nuitka.utils.Download import getCachedDownloadedMinGW64
from nuitka.utils.Execution import (
    callProcess,
    check_output,
    getExecutablePath,
    withEnvironmentPathAdded,
)
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    putTextFileContents,
)
from nuitka.utils.Utils import getArchitecture, isWin32Windows

from .Podman import getPodmanExecutablePath

containers_logger = OurLogger("Nuitka-Containers", base_style="blue")


def parseOptions():
    parser = OptionParser()

    parser.add_option(
        "--container-id",
        action="store",
        dest="container_id",
        default="CI",
        help="""
Name of the container to use. Defaults to "CI" which is used for testing
Nuitka with Linux.
""",
    )

    parser.add_option(
        "--no-build-container",
        action="store_true",
        dest="no_build_container",
        help="""
Do not update the the container, use it if updating was done recently.
""",
    )

    parser.add_option(
        "--command",
        action="store",
        dest="command",
        help="""
Command to execute, all in one value.
""",
    )

    parser.add_option(
        "--podman-path",
        action="store",
        dest="podman_path",
        default=None,
        help="""
Podman binary in case you do not have it in your path.
""",
    )

    parser.add_option(
        "--podman-verbose",
        action="store_false",
        dest="quiet",
        default=True,
        help="""
Dot not use podman quietly, giving more messages during build.""",
    )

    parser.add_option(
        "--shared-path",
        action="append",
        dest="shared_paths",
        default=[],
        help="""
Path to share with container, use "--shared-path=src=dst" format for directory names.
""",
    )

    parser.add_option(
        "--network",
        action="store_true",
        dest="network",
        default=False,
        help="""
This container run should be allowed to use network.
""",
    )

    parser.add_option(
        "--isolated",
        action="store_true",
        dest="isolated",
        default=None,
        help="""
This container run should not be provided host access of any kind.
""",
    )

    parser.add_option(
        "--no-isolated",
        action="store_false",
        dest="isolated",
        default=None,
        help="""
This container run should be provided host access even if the name suggests otherwise.
""",
    )

    parser.add_option(
        "--pbuilder",
        action="store_true",
        dest="pbuilder",
        default=False,
        help="""
This container run should be allowed to use pbuilder.
""",
    )

    options, positional_args = parser.parse_args()

    if positional_args:
        containers_logger.sysexit(
            "This command takes no positional arguments, check help output."
        )

    if options.podman_path is None:
        options.podman_path = getPodmanExecutablePath(containers_logger)

        assert options.podman_path is not None

    return options


def isPodman(podman_path):
    return "podman" in os.path.normcase(os.path.basename(podman_path))


def updateContainer(podman_path, container_tag_name, container_file_path, quiet):
    requirements_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "requirements-devel.txt"
    )

    if not os.path.exists(requirements_file):
        containers_logger.sysexit(
            "Error, cannot find expected requirements-devel.txt file."
        )

    containers_logger.info("Updating container '%s'..." % container_tag_name)

    requirements_tmp_file = os.path.join(
        os.path.dirname(container_file_path), "requirements-devel.txt"
    )

    shutil.copy(requirements_file, requirements_tmp_file)

    try:
        command = [
            podman_path,
            "build",
            # Tolerate errors checking for image download, and use old one
            "--tag",
            container_tag_name,
            "-f",
            container_file_path,
        ]

        if quiet:
            command.append("--quiet")

        if isPodman(podman_path):
            # Podman only.
            command.append("--pull=newer")
        else:
            # Context directory needed for Docker.
            command.append(".")

        exit_code = callProcess(command)

        if exit_code:
            containers_logger.sysexit(
                "Failed to update container with exit code '%d'. Command used was: %s"
                % (exit_code, " ".join(command)),
                exit_code=exit_code,
            )

        containers_logger.info(
            "Updated container '%s' successfully." % container_tag_name
        )

    finally:
        os.unlink(requirements_tmp_file)


def getCppPath():
    cpp_path = getExecutablePath("cpp_path")

    # Windows extra ball, attempt the downloaded one.
    if isWin32Windows() and cpp_path is None:
        from nuitka.Options import assumeYesForDownloads

        mingw64_gcc_path = getCachedDownloadedMinGW64(
            target_arch=getArchitecture(),
            assume_yes_for_downloads=assumeYesForDownloads(),
            download_ok=True,
        )

        with withEnvironmentPathAdded("PATH", os.path.dirname(mingw64_gcc_path)):
            cpp_path = getExecutablePath("cpp")

            os.environ["CPP_PATH"] = cpp_path

    if cpp_path is None:
        containers_logger.sysexit(
            "Error, need 'cpp' binary to execute this container file using.'"
        )

    return cpp_path


def _makeMountDesc(options, src_path, dst_path, flags):
    src_path = os.path.expanduser(src_path)

    mount_desc = "type=bind,source=%s,dst=%s" % (src_path, dst_path)

    if isPodman(options.podman_path):
        mount_desc += ",relabel=shared"

    if flags:
        mount_desc += ",%s" % flags

    if options.isolated:
        mount_desc += ",ro"

    return mount_desc


def _checkIsolated(options, container_tag_name):
    if options.isolated:
        containers_logger.info("Running isolated as per user choice.")
    # Auto-isolate by container name.
    elif "isolated" in container_tag_name.lower() and options.isolated is None:
        containers_logger.info("Running isolated as per container name default.")
        options.isolated = True
    elif options.isolated is False:
        containers_logger.info("Running NOT isolated as per user choice.")
    else:
        containers_logger.info("Running NOT isolated as per default.")


def _checkContainerArgument(options, default_container_directory):
    if ("/" in options.container_id or "\\" in options.container_id) and os.path.exists(
        options.container_id
    ):
        container_file_path = options.container_id

        if container_file_path.endswith(".in"):
            container_file_path_template = container_file_path
            container_file_path = container_file_path[:-3]
        else:
            container_file_path_template = None

        options.container_id = changeFilenameExtension(
            os.path.basename(container_file_path), ""
        )
    else:
        container_file_path = os.path.join(
            default_container_directory, options.container_id + ".containerfile"
        )
        container_file_path_template = container_file_path + ".in"

    return container_file_path_template, container_file_path


def main():
    options = parseOptions()

    if options.command is None:
        options.command = "python3 -m nuitka --version"

    containers_logger.info(
        "Running in container '%s' this command: %s"
        % (options.container_id, options.command)
    )

    default_container_directory = os.path.join(os.path.dirname(__file__), "containers")

    container_file_path_template, container_file_path = _checkContainerArgument(
        options=options, default_container_directory=default_container_directory
    )

    if container_file_path_template is not None and os.path.isfile(
        container_file_path_template
    ):
        # Check requirement.
        cpp_path = getCppPath()
        command = [
            cpp_path,
            "-E",
            "-I",
            default_container_directory,
            container_file_path_template,
        ]

        output = check_output(command, shell=False)
        if str is not bytes:
            output = output.decode("utf8")

        putTextFileContents(container_file_path, output, encoding="utf8")

    if not os.path.isfile(container_file_path):
        containers_logger.sysexit(
            "Error, no container ID '%s' found at '%s'."
            % (options.container_id, container_file_path)
        )

    getBranchRemoteIdentifier()

    container_tag_name = "nuitka-build-%s-%s:latest" % (
        options.container_id.lower(),
        getBranchRemoteIdentifier() + "-" + getBranchName(),
    )

    _checkIsolated(options, container_tag_name)

    if not options.no_build_container:
        updateContainer(
            podman_path=options.podman_path,
            container_tag_name=container_tag_name,
            container_file_path=container_file_path,
            quiet=options.quiet,
        )

    command = [options.podman_path, "run"]

    command.extend(
        (
            "--mount",
            _makeMountDesc(options=options, src_path=".", dst_path="/src", flags=""),
        )
    )

    if options.network:
        command.append("--add-host=ssh.nuitka.net:116.202.30.188")
    else:
        command.append("--network=none")

    # May need to allow pbuilder to create device nodes, makes the container insecure
    # though.
    if options.pbuilder:
        command += ["--privileged"]

    for path_desc in options.shared_paths:
        if path_desc.count("=") == 1:
            src_path, dst_path = path_desc.split("=")
            flags = ""
        else:
            src_path, dst_path, flags = path_desc.split("=", 2)

        src_path = os.path.expanduser(src_path)

        command.extend(
            (
                "--mount",
                _makeMountDesc(
                    options=options, src_path=src_path, dst_path=dst_path, flags=flags
                ),
            )
        )

    # Interactive if possible only.
    if sys.stdout.isatty():
        command.append("-it")

    command += [
        container_tag_name,
        "bash",
        "-l",
        "-c",
        "cd /src;" + options.command + "; exit $?",
    ]

    exit_code = callProcess(command, shell=False, logger=containers_logger)

    containers_logger.sysexit(
        "Finished container run with exit code '%d'." % exit_code, exit_code=exit_code
    )


if __name__ == "__main__":
    main()

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
