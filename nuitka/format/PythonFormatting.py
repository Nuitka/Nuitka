#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Python formatting utility for Nuitka.

This contains the logic to format Python source code.
"""

import ast
import os
import re

from nuitka.utils.Execution import check_call, check_output
from nuitka.utils.FileOperations import (
    getFileContents,
    putBinaryFileContents,
    putTextFileContents,
)
from nuitka.utils.PrivatePipSpace import (
    getBlackBinaryPath,
    getIsortBinaryPath,
    withPrivatePipSitePackagesPathAdded,
)

from .FileFormatting import cleanupWindowsNewlines

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

    with withPrivatePipSitePackagesPathAdded(logger=logger):
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


def _cleanupClassTrailingCommas(filename):
    """Cleanup trailing commas in class definitions with a single base class.

    Args:
        filename: path to the file
    """
    try:
        source_code = getFileContents(filename, encoding="utf8")
    except UnicodeDecodeError:
        return

    # We need to parse the code to find class definitions, if it is not valid
    # syntax, we can't do anything about it.
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return

    # Scan for classes with a single base class and a trailing comma.
    candidates = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        if len(node.bases) != 1:
            continue

        if node.keywords:
            continue

        candidates.append(node)

    if not candidates:
        return

    # Go backwards, so we don't mess up offsets if we modify the code.
    candidates.sort(key=lambda node: node.lineno, reverse=True)

    source_lines = source_code.splitlines()

    for node in candidates:
        # The only base class node.
        base_node = node.bases[0]

        # The end of the base class.
        end_lineno = base_node.end_lineno
        end_col_offset = base_node.end_col_offset

        # Check if there is a comma after the base class.
        line = source_lines[end_lineno - 1]
        remainder = line[end_col_offset:]

        # If strict match, we can just check the first character.
        if remainder.lstrip().startswith(","):
            # Find the comma position in the line.
            comma_index = remainder.find(",") + end_col_offset

            # Remove the comma.
            source_lines[end_lineno - 1] = (
                source_lines[end_lineno - 1][:comma_index]
                + source_lines[end_lineno - 1][comma_index + 1 :]
            )

    new_code = "\n".join(source_lines)
    if source_code.endswith("\n") and not new_code.endswith("\n"):
        new_code += "\n"

    if new_code != source_code:
        putTextFileContents(filename, new_code, encoding="utf8")


def formatPython(
    logger, filename, effective_filename, ignore_errors, assume_yes_for_downloads
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
        _cleanupClassTrailingCommas(filename=filename)

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
            return logger.sysexit("Error, cannot find 'black' binary.")

        black_call = [black_path, "-q", "--fast", filename]
        # logger.info("Executing: %s" % " ".join(black_call))

        old_contents = getFileContents(filename, "rb")

        try:
            with withPrivatePipSitePackagesPathAdded(logger=logger):
                check_call(black_call)
        except Exception:  # pylint: disable=broad-except
            logger.warning("Problem formatting for '%s'." % effective_filename)

            if not ignore_errors:
                raise

        if getFileContents(filename) == "" and old_contents != b"":
            if ignore_errors:
                logger.warning("Problem formatting for '%s'." % effective_filename)
            else:
                return logger.sysexit(
                    "Problem formatting for '%s'." % effective_filename
                )

    cleanupWindowsNewlines(filename, effective_filename)


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
