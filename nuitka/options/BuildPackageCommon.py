#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
This module provides common functionality for build package backends.

It stores global state about the project that is being built, e.g. the
expected data files.
"""

from nuitka.__past__ import Iterable, unicode

_project_expected_data_files = None


def getProjectExpectedDataFiles():
    return _project_expected_data_files


def setProjectExpectedDataFiles(project_expected_data_files):
    global _project_expected_data_files  # singleton, pylint: disable=global-statement
    _project_expected_data_files = project_expected_data_files


def reportBuildError(logger, name, command, stdout, stderr):
    if str is not bytes:
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")

    logger.sysexit(
        """\
Error, failed to extract build configuration via '%(name)s'.
Error output from '%(name)s' configuration extraction:
Command used: %(command)s
stdout: %(stdout)s
stderr: %(stderr)s"""
        % {
            "name": name,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
        }
    )


def convertNuitkaOption(option, value):
    """Convert a [tool.nuitka] option to command line arguments."""
    option = "--" + option.lstrip("-")

    if value is None or value == "":
        yield option
    elif isinstance(value, bool):
        if value:
            yield option
        else:
            yield "--no" + option.lstrip("-")
    elif isinstance(value, Iterable) and not isinstance(value, (unicode, bytes, str)):
        for val in value:
            yield "%s=%s" % (option, val)
    else:
        yield "%s=%s" % (option, value)


def applyNuitkaProjectOptions(pyproject_data):
    """Apply options from [tool.nuitka] and [nuitka] sections of pyproject.toml.

    Args:
        pyproject_data: Parsed pyproject.toml data.

    Returns:
        List of command line arguments derived from the Nuitka sections.
    """
    result = []

    tool_nuitka = pyproject_data.get("tool", {}).get("nuitka", {})
    if tool_nuitka:
        for option, value in tool_nuitka.items():
            for converted in convertNuitkaOption(option, value):
                result.append(converted)

    nuitka = pyproject_data.get("nuitka", {})
    if nuitka:
        for option, value in nuitka.items():
            for converted in convertNuitkaOption(option, value):
                result.append(converted)

    return result


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
