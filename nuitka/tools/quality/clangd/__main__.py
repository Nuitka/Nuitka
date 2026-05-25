#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Main program for clangd C code checker tool."""

import os
import sys

from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.Basics import goHome
from nuitka.tools.quality.Git import addGitArguments, getGitPaths
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.Execution import executeProcess, getExecutablePath
from nuitka.utils.FileOperations import resolveShellPatternToFilenames


def _isIgnoredCFile(filename):
    """Check if a C source file should be ignored.

    Args:
        filename: str - path to the file.

    Returns:
        bool - True if the file should be ignored.
    """
    path_parts = os.path.normpath(filename).replace("\\", "/").split("/")

    if "inline_copy" in path_parts:
        return True

    return False


def _resolveFilenames(options, positional_args):
    """Resolve C source filenames from options and positional arguments.

    Args:
        options: parsed options object.
        positional_args: list of positional arguments.

    Returns:
        list of filenames to check.
    """
    positional_args = getGitPaths(
        options=options,
        positional_args=positional_args,
        default_positional_args=(
            "nuitka/build/static_src",
            "nuitka/build/include",
        ),
    )

    if options.verbose:
        my_print("Working on: %s" % " ".join(positional_args))

    positional_args = sum(
        (
            resolveShellPatternToFilenames(positional_arg)
            for positional_arg in positional_args
        ),
        [],
    )

    filenames = list(
        scanTargets(positional_args, suffixes=(".c", ".h"), ignore_list=[])
    )

    filenames = [filename for filename in filenames if not _isIgnoredCFile(filename)]

    filenames.sort()

    return filenames


def _parseArguments():
    """Parse command-line arguments.

    Returns:
        tuple: (options, positional_args)
    """
    parser = makeOptionsParser(usage=None, epilog=None)

    addGitArguments(parser)

    parser.add_option(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="""\
Be verbose in output. Default is %default.""",
    )

    parser.add_option(
        "--not-installed-is-no-error",
        action="store_true",
        dest="not_installed_is_no_error",
        default=False,
        help="""\
Do not error if clangd is not installed. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    return options, positional_args


def _checkClangdFile(filename):
    """Run clangd --check on a single C source file.

    Args:
        filename: str - path to the file.

    Returns:
        tuple: (exit_code, stderr_text)
    """
    command = ["clangd", "--check=%s" % filename]

    process_result = executeProcess(command)

    stderr = process_result.stderr

    if str is not bytes:
        if stderr is not None:
            stderr = stderr.decode("utf8")

    return process_result.exit_code, stderr


def _filterClangdDiagnostics(stderr):
    """Extract diagnostic lines from clangd stderr output.

    Strips the useless timestamp from lines and keeps only the
    diagnostic content.  clangd outputs lines like::

        E[12:34:56.789] [diag_code] Line N: message

    which get trimmed to::

        [diag_code] Line N: message

    Args:
        stderr: str - raw stderr output from clangd.

    Returns:
        list of diagnostic line strings (E and W lines only).
    """
    if not stderr:
        return []

    result = []
    for line in stderr.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not (stripped.startswith("E[") or stripped.startswith("W[")):
            continue

        # Strip the "[HH:MM:SS.mmm]" timestamp right after the severity marker.
        bracket_end = stripped.find("] ", 2)
        if bracket_end != -1:
            stripped = stripped[bracket_end + 2 :]

        result.append(stripped)

    return result


def _checkFiles(filenames, verbose):
    """Run clangd --check on a list of files.

    Args:
        filenames: list of file paths.
        verbose: bool - if True, print OK for each file that passes.

    Returns:
        int - exit code (0 on success, 1 on errors).
    """
    exit_code = 0

    for filename in filenames:
        file_exit_code, stderr = _checkClangdFile(filename)

        diagnostics = _filterClangdDiagnostics(stderr)

        if diagnostics:
            exit_code = file_exit_code
            my_print("\n%s:" % filename)
            for line in diagnostics:
                my_print("  %s" % line)
        elif file_exit_code != 0:
            exit_code = file_exit_code
            my_print("\n%s: clangd exited with code %d" % (filename, file_exit_code))
        elif verbose:
            my_print("%s: OK" % filename)

    return exit_code


def main():
    options, positional_args = _parseArguments()

    if options.not_installed_is_no_error:
        if getExecutablePath("clangd") is None:
            tools_logger.warning(
                "clangd is not installed: SKIPPED",
                style="yellow",
            )
            return tools_logger.sysexit(exit_code=0)

    goHome()

    filenames = _resolveFilenames(options=options, positional_args=positional_args)

    if not filenames:
        tools_logger.info("No matching C source files found.")
        return 0

    if not os.path.exists(".clangd"):
        tools_logger.warning(
            "No .clangd configuration found. "
            "Run 'python misc/vscode_config_gen.py' to generate one.",
            style="yellow",
        )

    my_print("Checking %d C source file(s) with clangd..." % len(filenames))

    exit_code = _checkFiles(filenames, verbose=options.verbose)

    sys.stdout.flush()

    if exit_code == 0:
        my_print("OK")

    return tools_logger.sysexit(exit_code=exit_code)


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
