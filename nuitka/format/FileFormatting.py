#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Core formatting utility for Nuitka."""

import re
import subprocess

from nuitka.utils.FileOperations import (
    getFileContentByLine,
    getFileContents,
    putTextFileContents,
)
from nuitka.utils.PrivatePipSpace import (
    getClangFormatBinaryPath,
    withPrivatePipSitePackagesPathAdded,
)


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


_warned_clang_format = False
_clang_format_path = False


def _getClangFormatPath(logger, assume_yes_for_downloads, reject_message):
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
        logger=logger,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )

    if _clang_format_path is None and not _warned_clang_format:
        if logger is not None:
            logger.warning("Need to accept clang-format download to format C files.")
        _warned_clang_format = True

    return _clang_format_path


def _cleanupClangFormat(logger, filename, assume_yes_for_downloads, reject_message):
    """Call clang-format on a given filename to format C code.

    Args:
        filename: path to the file
        logger: logger to use
        assume_yes_for_downloads: bool
    """

    clang_format_path = _getClangFormatPath(
        logger=logger,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )

    if clang_format_path:
        with withPrivatePipSitePackagesPathAdded(logger=logger):
            subprocess.call(
                [
                    clang_format_path,
                    "-i",
                    "-style={BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 120}",
                    filename,
                ]
            )


def formatC(
    logger,
    filename,
    effective_filename,
    check_only,
    assume_yes_for_downloads,
    reject_message,
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
        reject_message=reject_message,
    )
    cleanupWindowsNewlines(filename, effective_filename)

    return False


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
