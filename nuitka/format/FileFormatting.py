#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Core formatting utility for Nuitka."""

import os
import re
import subprocess

from nuitka.Tracing import general
from nuitka.utils.Execution import check_call, check_output
from nuitka.utils.FileOperations import (
    getFileContentByLine,
    getFileContents,
    putBinaryFileContents,
    putTextFileContents,
)
from nuitka.utils.PrivatePipSpace import (
    getBlackBinaryPath,
    getClangFormatBinaryPath,
    getIsortBinaryPath,
    withPrivatePipSitePackagesPathAdded,
)

BLACK_SKIP_LIST = [
    "tests/basics/ClassesTest_2.py",
    "tests/basics/ExecEvalTest_2.py",
    "tests/basics/HelloWorldTest_2.py",
    "tests/basics/OverflowFunctionsTest_2.py",
    "tests/basics/PrintingTest_2.py",
    "tests/benchmarks/binary-trees.py",
    "tests/benchmarks/comparisons/GeneratorFunctionVsGeneratorExpression.py",
    "tests/benchmarks/constructs/InplaceOperationLongAdd_27.py",
    "tests/benchmarks/constructs/InplaceOperationUnicodeAdd_27.py",
    "tests/benchmarks/constructs/RichComparisonConditionStrings.py",
    "tests/programs/syntax_errors/IndentationErroring.py",
    "tests/syntax/ClosureDel_2.py",
    "tests/syntax/ExecWithNesting_2.py",
    "tests/syntax/IndentationError.py",
    "tests/syntax/StarImportExtra.py",
    "tests/syntax/SyntaxError.py",
    "tests/type_inference/Test1.py",
    "tests/type_inference/Test2.py",
    "tests/type_inference/Test3.py",
    "tests/type_inference/Test4.py",
    "tests/benchmarks/pystone.py",
]
BLACK_SKIP_LIST = tuple(os.path.normpath(path) for path in BLACK_SKIP_LIST)


def cleanupWindowsNewlines(filename, effective_filename):
    """Remove Windows new-lines from a file."""

    with open(filename, "rb") as f:
        source_code = f.read()

    updated_code = source_code.replace(b"\r\n", b"\n")
    updated_code = updated_code.replace(b"\n\r", b"\n")

    # Smuggle consistency replacement in here.
    if (
        "AutoFormat.py" not in effective_filename
        and "Formatting.py" not in effective_filename
    ):
        updated_code = updated_code.replace(b'.decode("utf-8")', b'.decode("utf8")')
        updated_code = updated_code.replace(b'.encode("utf-8")', b'.encode("utf8")')
        updated_code = updated_code.replace(b"# spellchecker", b"# spell-checker")

        def replacer(match):
            return b"PYTHON_VERSION %s %s" % (match.group(1), match.group(2).lower())

        updated_code = re.sub(
            b"PYTHON_VERSION\\s+([=<>]+)\\s+(0x3[A-F])", replacer, updated_code
        )

    if updated_code != source_code:
        with open(filename, "wb") as out_file:
            out_file.write(updated_code)


def cleanupTrailingWhitespace(filename):
    """Remove trailing white spaces from a file."""
    source_lines = list(getFileContentByLine(filename, encoding="utf8"))

    clean_lines = [line.rstrip().replace("\t", "    ") for line in source_lines]

    while clean_lines and clean_lines[-1] == "":
        del clean_lines[-1]

    if clean_lines != source_lines or (clean_lines and clean_lines[-1] != ""):
        putTextFileContents(filename, contents=clean_lines, encoding="utf8")


def _cleanupPyLintComments(logger, filename, effective_filename):
    """Cleanup pylint comments in a file.

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
    """
    try:
        new_code = old_code = getFileContents(filename, encoding="utf8")
    except UnicodeDecodeError:
        if logger is not None:
            logger.warning(
                "Problem with file %s not having UTF8 encoding." % effective_filename
            )
        raise

    def replacer(part):
        def changePyLintTagName(pylint_token):
            pylint_token = pylint_token.strip()
            # Save line length for this until isort is better at long lines.
            if pylint_token == "useless-suppression":
                return "I0021"
            else:
                return pylint_token

        return part.group(1) + ",".join(
            sorted(
                set(
                    changePyLintTagName(token)
                    for token in part.group(2).split(",")
                    if token
                )
            )
        )

    new_code = re.sub(r"(pylint\: disable=)\s*(.*)", replacer, new_code, flags=re.M)

    if new_code != old_code:
        putTextFileContents(filename, new_code, encoding="utf8")


def _cleanupImportRelative(filename, effective_filename):
    """Make imports of Nuitka package when possible."""

    if os.path.basename(effective_filename) == "__main__.py":
        return

    package_name = os.path.dirname(effective_filename).replace(os.path.sep, ".")

    if not package_name.startswith("nuitka."):
        return

    source_code = getFileContents(filename, encoding="utf8")
    updated_code = re.sub(
        r"from %s import" % package_name, "from . import", source_code
    )
    updated_code = re.sub(r"from %s\." % package_name, "from .", source_code)

    if source_code != updated_code:
        putTextFileContents(filename, contents=updated_code, encoding="utf8")


def _cleanupImportSortOrder(
    logger, filename, effective_filename, assume_yes_for_downloads
):
    """Cleanup import sort order in a file using isort.

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
        assume_yes_for_downloads: bool
    """
    _cleanupImportRelative(filename, effective_filename)

    isort_path = getIsortBinaryPath(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )

    if isort_path is None:
        return

    isort_call = [isort_path]

    contents = getFileContents(filename, encoding="utf8")

    start_index = None
    if "\n# isort:start" in contents:
        parts = contents.splitlines()

        start_index = parts.index("# isort:start")
        contents = "\n".join(parts[start_index + 1 :]) + "\n"

        putTextFileContents(filename, contents=contents, encoding="utf8")

    with withPrivatePipSitePackagesPathAdded():
        isort_output = check_output(
            isort_call
            + [
                "-q",
                "--stdout",
                "--order-by-type",
                "--multi-line=VERTICAL_HANGING_INDENT",
                "--trailing-comma",
                "--project=nuitka",
                "--float-to-top",
                # spell-checker: ignore thirdparty
                "--thirdparty=SCons",
                filename,
            ]
        )

    if isort_output == b"" and contents != "":
        if logger is not None:
            logger.warning(
                "The 'isort' failed to handle '%s' properly." % effective_filename
            )
    else:
        putBinaryFileContents(filename, isort_output)

    cleanupWindowsNewlines(filename, effective_filename)

    if start_index is not None:
        contents = getFileContents(filename, encoding="utf8")

        contents = "\n".join(parts[: start_index + 1]) + "\n\n" + contents.lstrip("\n")

        putTextFileContents(filename, contents=contents, encoding="utf8")


_warned_clang_format = False
_clang_format_path = False


def _getClangFormatPath(logger, assume_yes_for_downloads):
    """Get the path to the clang-format executable.

    Args:
        logger: logger to use
        assume_yes_for_downloads: bool
    """
    # pylint: disable=global-statement
    global _warned_clang_format, _clang_format_path

    if _warned_clang_format:
        return None

    if _clang_format_path is not False:
        return _clang_format_path

    _clang_format_path = getClangFormatBinaryPath(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )

    if _clang_format_path is None and not _warned_clang_format:
        if logger is not None:
            logger.warning("Need to accept clang-format download to format C files.")
        _warned_clang_format = True

    return _clang_format_path


def _cleanupClangFormat(logger, filename, assume_yes_for_downloads=False):
    """Call clang-format on a given filename to format C code.

    Args:
        filename: path to the file
        logger: logger to use
        assume_yes_for_downloads: bool
    """

    clang_format_path = _getClangFormatPath(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )

    if clang_format_path:
        with withPrivatePipSitePackagesPathAdded():
            subprocess.call(
                [
                    clang_format_path,
                    "-i",
                    "-style={BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 120}",
                    filename,
                ]
            )


def formatPython(
    logger, filename, effective_filename, ignore_errors, assume_yes_for_downloads=False
):
    """Format Python source code.

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
        ignore_errors: bool - if errors should be ignored
        assume_yes_for_downloads: bool - if downloads are allowed
    """
    cleanupWindowsNewlines(filename, effective_filename)

    if (
        not os.path.basename(os.path.dirname(os.path.abspath(effective_filename)))
        .lower()
        .startswith("chinese")
    ) and os.path.basename(effective_filename) != "SocketUsing.py":
        _cleanupImportSortOrder(
            logger=logger,
            filename=filename,
            effective_filename=effective_filename,
            assume_yes_for_downloads=assume_yes_for_downloads,
        )

    _cleanupPyLintComments(
        logger=logger, filename=filename, effective_filename=effective_filename
    )

    if effective_filename not in BLACK_SKIP_LIST:
        black_path = getBlackBinaryPath(
            logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
        )

        if black_path is None:
            if logger is None:
                logger = general

            return logger.sysexit("Error, cannot find 'black' binary.")

        black_call = [black_path]

        old_contents = getFileContents(filename, "rb")

        try:
            with withPrivatePipSitePackagesPathAdded():
                check_call(black_call + ["-q", "--fast", filename])
        except Exception:  # pylint: disable=broad-except
            if logger is not None:
                logger.warning("Problem formatting for '%s'." % effective_filename)

            if not ignore_errors:
                raise

        if getFileContents(filename) == "" and old_contents != b"":
            if ignore_errors:
                if logger is not None:
                    logger.warning("Problem formatting for '%s'." % effective_filename)
            else:
                if logger is None:
                    logger = general

                return logger.sysexit(
                    "Problem formatting for '%s'." % effective_filename
                )

    cleanupWindowsNewlines(filename, effective_filename)


def formatC(
    logger, filename, effective_filename, check_only, assume_yes_for_downloads=False
):
    """Format C/C++ source code.

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
        check_only: bool - if only checking is to be done
        assume_yes_for_downloads: bool - if downloads are allowed
    """
    if check_only:
        try:
            getFileContents(filename, encoding="ascii")
        except UnicodeDecodeError:
            if logger:
                logger.warning(
                    "All C files must be pure ASCII, need to convert it manually."
                )
            return True

    cleanupWindowsNewlines(filename, effective_filename)
    _cleanupClangFormat(
        logger=logger,
        filename=filename,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )
    cleanupWindowsNewlines(filename, effective_filename)

    return False


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
