#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Pyright handling for Nuitka.

Pyright is a static type checker for Python. For Nuitka, we use it in
a lenient mode, focusing on catching actual code errors rather than type
hinting issues, since the codebase is Python 2 compatible and does not
use type hints.
"""

import os
import sys

from nuitka.tools.testing.Common import my_print
from nuitka.utils.Execution import (
    check_output,
    executeProcess,
    getExecutablePath,
)


def _findPyrightBinary(basedpyright):
    """Find the pyright binary on the system.

    Args:
        basedpyright: If True, look for 'basedpyright' instead of 'pyright'.

    Returns:
        Path to the pyright executable.

    Raises:
        SystemExit if pyright is not found.
    """
    if os.name == "nt":
        extra_path = os.path.join(os.environ.get("APPDATA", ""), "npm")
    else:
        extra_path = None

    binary_name = "basedpyright" if basedpyright else "pyright"
    pyright_binary = getExecutablePath(binary_name, extra_dir=extra_path)

    if pyright_binary is None:
        return None

    return pyright_binary


_pyright_version = None


def getPyrightVersion(basedpyright):
    """Get the installed pyright version.

    Args:
        basedpyright: If True, use basedpyright instead of pyright.

    Returns:
        str - version string.
    """
    # False alarm, pylint: disable=global-statement
    global _pyright_version

    if _pyright_version is None:
        pyright_binary = _findPyrightBinary(basedpyright=basedpyright)

        if pyright_binary is None:
            return None

        version_output = check_output([pyright_binary, "--version"])

        if str is not bytes:
            version_output = version_output.decode("utf8")

        _pyright_version = version_output.strip()

    return _pyright_version


def _buildPyrightCommand(filenames, extra_options, basedpyright):
    """Build the pyright command line.

    Args:
        filenames: List of files to check.
        extra_options: Extra CLI options from environment variable.
        basedpyright: If True, use basedpyright instead of pyright.

    Returns:
        List of command arguments.
    """
    pyright_binary = _findPyrightBinary(basedpyright=basedpyright)

    if pyright_binary is None:
        binary_name = "basedpyright" if basedpyright else "pyright"
        sys.exit(
            "Error, %s is not installed. Install it with 'npm install -g %s'."
            % (binary_name, binary_name)
        )

    command = [pyright_binary]

    command.append("--level")
    command.append("warning")

    command.append("--warnings")

    if extra_options:
        command.extend(extra_options)

    command.extend(filenames)

    return command


def _cleanupPyrightOutput(output):
    """Clean up pyright output for display.

    Args:
        output: Raw stdout/stderr bytes.

    Returns:
        List of cleaned output lines.
    """
    if str is not bytes:
        output = output.decode("utf8")

    # Normalize Windows newlines.
    output = output.replace("\r\n", "\n")

    return [line for line in output.split("\n") if line]


def _executePyright(filenames, extra_options, basedpyright):
    """Execute pyright on the given files.

    Args:
        filenames: List of file paths to check.
        extra_options: Extra CLI options.
        basedpyright: If True, use basedpyright instead of pyright.

    Returns:
        int - exit code (0 on success, 1 on errors).
    """
    command = _buildPyrightCommand(
        filenames=filenames,
        extra_options=extra_options,
        basedpyright=basedpyright,
    )

    process_result = executeProcess(command)

    stdout = _cleanupPyrightOutput(process_result.stdout)
    stderr = _cleanupPyrightOutput(process_result.stderr)

    exit_code = 0

    if stderr:
        exit_code = 1
        for line in stderr:
            my_print(line)

    if stdout:
        exit_code = 1
        for line in stdout:
            my_print(line)

    sys.stdout.flush()

    return exit_code


def executePyright(filenames, verbose, basedpyright):
    """Run pyright on a list of files.

    Args:
        filenames: List of file paths to check.
        verbose: If True, output extra diagnostic information.
        basedpyright: If True, use basedpyright instead of pyright.

    Returns:
        int - exit code (0 on success, 1 on errors).
    """
    filenames = list(filenames)

    version = getPyrightVersion(basedpyright=basedpyright)
    if version is None:
        tool_name = "basedpyright" if basedpyright else "pyright"
        sys.exit(
            "Error, %s is not installed. Install it with 'npm install -g %s'."
            % (tool_name, tool_name)
        )

    tool_name = "basedpyright" if basedpyright else "pyright"
    my_print("Using %s version:" % tool_name, version)

    if verbose:
        my_print("Checking", filenames, "...")

    extra_options = os.getenv("PYRIGHT_EXTRA_OPTIONS", "").split()
    if "" in extra_options:
        extra_options.remove("")

    return _executePyright(filenames, extra_options, basedpyright=basedpyright)


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
