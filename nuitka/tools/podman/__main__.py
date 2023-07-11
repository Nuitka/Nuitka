#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Launcher for running a script inside a container

"""

import os
import shutil
import sys
from optparse import OptionParser

from nuitka.tools.release.Release import getBranchName
from nuitka.Tracing import OurLogger
from nuitka.utils.Execution import callProcess

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


def updateContainer(podman_path, container_tag_name, container_file_path):
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
            "--quiet",
            "--pull=newer",
            "--tag",
            container_tag_name,
            "-f",
            container_file_path,
        ]

        exit_code = callProcess(command)

        if exit_code:
            containers_logger.sysexit(
                "Failed to update container with exit code '%d'." % exit_code,
                exit_code=exit_code,
            )

        containers_logger.info(
            "Updated container '%s' successfully." % container_tag_name
        )

    finally:
        os.unlink(requirements_tmp_file)


def main():
    options = parseOptions()

    containers_logger.info(
        "Running in container '%s' this command: %s"
        % (options.container_id, options.command)
    )

    container_file_path = os.path.join(
        os.path.dirname(__file__), "containers", options.container_id + ".containerfile"
    )

    if not os.path.isfile(container_file_path):
        containers_logger.sysexit(
            "Error, no container ID '%s' found" % options.container_id
        )

    container_tag_name = "nuitka-build-%s-%s:latest" % (
        options.container_id.lower(),
        getBranchName(),
    )

    if not options.no_build_container:
        updateContainer(
            podman_path=options.podman_path,
            container_tag_name=container_tag_name,
            container_file_path=container_file_path,
        )

    command = [
        options.podman_path,
        "run",
        "--mount",
        "type=bind,source=.,dst=/src,relabel=shared",
    ]

    if options.network:
        command.append("--add-host=ssh.nuitka.net:116.202.30.188")
    else:
        command.append("--network=none")

    # May need to allow pbuilder to create device nodes, makes the container insecure
    # though.
    if options.pbuilder:
        command += ["--privileged"]

    dst_paths = []

    for path_desc in options.shared_paths:
        if path_desc.count("=") == 1:
            src_path, dst_path = path_desc.split("=")
            flags = ""
        else:
            src_path, dst_path, flags = path_desc.split("=", 2)
            flags = "," + flags

        src_path = os.path.expanduser(src_path)

        dst_paths.append(dst_path)

        command += [
            "--mount",
            "type=bind,source=%s,dst=%s,relabel=shared%s" % (src_path, dst_path, flags),
        ]

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
