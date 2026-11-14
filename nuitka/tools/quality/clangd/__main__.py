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
from nuitka.utils.FileOperations import (
    getPathWithForwardSlashes,
    resolveShellPatternsToFilenames,
)
from nuitka.utils.PrivatePipSpace import (
    getClangdBinaryPath,
    getPrivatePipSitePackagesEnvironment,
)
from nuitka.utils.Utils import isWin32Windows

# clangd can hang on some files, and a stuck checker is worse than a
# reported timeout. Generated helper files can take a few minutes.
_clangd_check_timeout = 300


def _isIgnoredCFile(filename):
    """Check if a C source file should be ignored.

    Args:
        filename: str - path to the file.

    Returns:
        bool - True if the file should be ignored.
    """
    path_parts = getPathWithForwardSlashes(os.path.normpath(filename)).split("/")

    if "inline_copy" in path_parts:
        return True

    if os.path.basename(filename) == "OnefileSplashScreen.cpp":
        return not isWin32Windows()

    # This uses ucontext and is not buildable on Windows.
    if os.path.basename(filename) == "HelpersDumpBacktraces.c":
        return isWin32Windows()

    # Kept for reference only, not part of any build.
    if os.path.basename(filename) == "MetaPathBasedLoaderSource.c":
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

    positional_args = resolveShellPatternsToFilenames(positional_args)

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
        "--assume-yes-for-downloads",
        action="store_true",
        dest="assume_yes_for_downloads",
        default=False,
        help="""\
Allow download and execution of tools if needed. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    return options, positional_args


def _checkClangdFile(clangd_path, filename, verbose):
    """Run clangd --check on a single C source file.

    Args:
        clangd_path: str - path to the clangd executable.
        filename: str - path to the file.
        verbose: bool - if True, echo command.

    Returns:
        tuple: (exit_code, stderr_text)
    """
    command = [
        clangd_path,
        # Background indexing can make a single check take minutes or hang
        # indefinitely, and it is not needed for checking a single file.
        "--background-index=0",
        "--check=%s" % filename,
    ]

    if verbose:
        my_print("Running: %s" % " ".join(command))

    try:
        process_result = executeProcess(
            command,
            env=getPrivatePipSitePackagesEnvironment(binary_path=clangd_path),
            timeout=_clangd_check_timeout,
        )
    except Exception as e:
        if e.__class__.__name__ == "TimeoutExpired":
            return (
                1,
                "E[timeout] clangd check did not finish within %d seconds"
                % _clangd_check_timeout,
            )

        raise

    stderr = process_result.stderr

    if str is not bytes and stderr is not None:
        stderr = stderr.decode("utf8", "replace")

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
        tuple: list of diagnostic line strings (E and W lines only), and the
        number of lines that were filtered as known false positives.
    """
    if not stderr:
        return [], 0

    result = []
    suppressed_count = 0

    for line in stderr.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith(("E[", "W[")):
            continue

        # Strip the "[HH:MM:SS.mmm]" timestamp right after the severity marker.
        bracket_end = stripped.find("] ", 2)
        if bracket_end != -1:
            stripped = stripped[bracket_end + 2 :]

        if "Failed to resolve URI" in stripped:
            suppressed_count += 1
            continue

        if (
            "DefineOutline" in stripped
            and "Couldn't find a suitable implementation file" in stripped
        ):
            suppressed_count += 1
            continue

        if "The new replacement overlaps with an existing replacement" in stripped:
            suppressed_count += 1
            continue

        if "Class body in wrong file" in stripped:
            suppressed_count += 1
            continue

        if (
            "Cannot extract break/continue without corresponding loop/switch statement"
            in stripped
        ):
            suppressed_count += 1
            continue

        result.append(stripped)

    return result, suppressed_count


def _checkFiles(clangd_path, filenames, verbose):
    """Run clangd --check on a list of files.

    Args:
        clangd_path: str - path to the clangd executable.
        filenames: list of file paths.
        verbose: bool - if True, print OK for each file that passes.

    Returns:
        int - exit code (0 on success, 1 on errors).
    """
    exit_code = 0

    for filename in filenames:
        file_exit_code, stderr = _checkClangdFile(
            clangd_path=clangd_path, filename=filename, verbose=verbose
        )

        diagnostics, suppressed_count = _filterClangdDiagnostics(stderr)

        if diagnostics:
            exit_code = 1
            my_print("\n%s:" % filename)
            for line in diagnostics:
                my_print("  %s" % line)
        elif file_exit_code != 0 and suppressed_count == 0:
            # A non-zero exit without any diagnostic means clangd failed
            # internally, e.g. because the configuration is broken or the
            # process crashed. Do not silently accept that.
            exit_code = 1
            my_print(
                "\n%s: clangd exited with code %d without any diagnostics"
                % (filename, file_exit_code)
            )
        elif verbose:
            my_print("%s: OK" % filename)

    return exit_code


def main():
    options, positional_args = _parseArguments()

    clangd_path = getExecutablePath("clangd")

    if clangd_path is None:
        clangd_path = getClangdBinaryPath(
            logger=tools_logger,
            assume_yes_for_downloads=options.assume_yes_for_downloads,
        )

        if clangd_path is None:
            return tools_logger.sysexit(
                "Error, clangd is not installed. Use '--assume-yes-for-downloads'."
            )

    goHome()

    filenames = _resolveFilenames(options=options, positional_args=positional_args)

    if not filenames:
        tools_logger.info("No matching C source files found.")
        return 0

    if not os.path.exists(".clangd"):
        return tools_logger.sysexit(
            """\
No .clangd configuration found. \
Run 'python misc/vscode_config_gen.py' to generate one.\
""",
        )

    my_print("Checking %d C source file(s) with clangd..." % len(filenames))

    exit_code = _checkFiles(
        clangd_path=clangd_path, filenames=filenames, verbose=options.verbose
    )

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
