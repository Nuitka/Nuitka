#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
This module provides common functionality for build package backends.

It stores global state about the project that is being built, e.g. the
project name and the expected data files.
"""

_project_name = None
_project_expected_data_files = None


def getProjectName():
    return _project_name


def setProjectName(project_name):
    global _project_name  # singleton, pylint: disable=global-statement
    _project_name = project_name


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


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
