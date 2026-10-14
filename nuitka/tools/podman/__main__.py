#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Launcher for running a script inside a container.

Podman and Docker should both work, but the first one is recommended.
"""

from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.Tracing import containers_logger

from .Container import getContainerPython, runContainer
from .Podman import getPodmanExecutablePath


def parseOptions():
    parser = makeOptionsParser(usage=None, epilog=None)

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


def main():
    options = parseOptions()

    if options.command is None:
        options.command = "%s -m nuitka --version" % getContainerPython(
            options.container_id
        )

    runContainer(
        container_name=options.container_id,
        command=options.command,
        no_build=options.no_build_container,
        podman_path=options.podman_path,
        quiet=options.quiet,
        shared_paths=options.shared_paths,
        network=options.network,
        isolated=options.isolated,
        privileged=options.pbuilder,
        plugin_container_files={},
    )


if __name__ == "__main__":
    main()

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
