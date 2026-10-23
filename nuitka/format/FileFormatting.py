#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Core formatting utility for Nuitka."""

import re
import subprocess

from nuitka.utils.FileOperations import (
    getFileContentByLine,
    getFileContents,
    putBinaryFileContents,
    putTextFileContents,
)
from nuitka.utils.PrivatePipSpace import (
    getClangFormatBinaryPath,
    withPrivatePipSitePackagesPathAdded,
)
from nuitka.utils.Utils import counted

# Typographic dash and hyphen variants to be normalized to a plain dash.
_dash_characters = (
    "\u2010",  # HYPHEN
    "\u2011",  # NON-BREAKING HYPHEN
    "\u2012",  # FIGURE DASH
    "\u2013",  # EN DASH
    "\u2014",  # EM DASH
    "\u2015",  # HORIZONTAL BAR
)

# Fill width for 'spell-checker: ignore' word lists, matching the generated
# files emitted by the specialization tooling.
_spell_checker_ignore_width = 90

_spell_checker_ignore_pattern = re.compile(b"^(.*spell-checker:\\s*ignore)(\\s+)(.*)$")

_spell_checker_word_pattern = re.compile(b"^[A-Za-z0-9_.+-]+$")

# Prefixes made up of these are considered plain comments, whereas anything
# with prose before the directive is not merged and wrapped, since that would
# repeat the prose on every line.
_spell_checker_plain_prefix_pattern = re.compile(b"^[ \t#/!*-]*$")


def _wrapSpellCheckerIgnoreWords(prefix, words, separator):
    """Fill the ignored words into lines of the given prefix.

    Args:
        prefix: bytes - the line prefix, including 'spell-checker: ignore'
        words: sequence of bytes - sorted and de-duplicated words
        separator: bytes - separator to use between the words

    Returns:
        List of bytes lines.
    """

    result = []
    current_line = b""

    for word in words:
        if not current_line:
            current_line = word
        elif (
            len(prefix) + len(current_line) + len(separator) + len(word)
            <= _spell_checker_ignore_width
        ):
            current_line += separator + word
        else:
            result.append(prefix + current_line)
            current_line = word

    result.append(prefix + current_line)

    return result


def _parseSpellCheckerIgnoreLine(line):
    """Parse a 'spell-checker: ignore' line.

    Args:
        line: bytes - the line to parse

    Returns:
        Tuple of prefix, word list, words, and plainness, or None if the line
        is not a plain word list.
    """

    match = _spell_checker_ignore_pattern.match(line)

    if match is None:
        return None

    # Restore standard spacing after comma in the prose before the directive.
    prefix = re.sub(
        b"(,[a-zA-Z])",
        lambda m: b", " + m.group(0)[1:],
        match.group(1),
    )

    word_list = match.group(3)
    words = word_list.replace(b",", b" ").split()

    # Only consider plain word lists, otherwise leave code or prose following
    # the directive alone.
    if not words or not all(_spell_checker_word_pattern.match(word) for word in words):
        return None

    is_plain = (
        _spell_checker_plain_prefix_pattern.match(
            prefix.rsplit(b"spell-checker:", 1)[0]
        )
        is not None
    )

    return prefix + b" ", word_list, words, is_plain


def _cleanupSpellCheckerIgnores(contents):
    """Sort, de-duplicate and fill 'spell-checker: ignore' lines.

    Consecutive plain lines are treated as a single sequence of words that is
    sorted and then filled into lines again.

    Args:
        contents: bytes - the contents of the file

    Returns:
        bytes - the contents with 'spell-checker: ignore' lines cleaned up.
    """

    lines = contents.split(b"\n")

    result = []
    index = 0
    line_count = len(lines)

    while index < line_count:
        ignore_line = _parseSpellCheckerIgnoreLine(lines[index])

        if ignore_line is None:
            result.append(lines[index])
            index += 1
            continue

        prefix, word_list, words, is_plain = ignore_line
        use_commas = b"," in word_list
        all_words = list(words)
        merged_lines = 1

        index += 1

        # Merge with consecutive plain lines of the same kind and prefix.
        while is_plain and index < line_count:
            next_ignore_line = _parseSpellCheckerIgnoreLine(lines[index])

            if (
                next_ignore_line is None
                or not next_ignore_line[3]
                or next_ignore_line[0] != prefix
            ):
                break

            all_words.extend(next_ignore_line[2])
            use_commas = use_commas or b"," in next_ignore_line[1]

            merged_lines += 1
            index += 1

        words = sorted(set(all_words))
        separator = b"," if use_commas else b" "

        # Only fill merged lines again, a single line is left as is, to not
        # repeat a prose prefix over and over.
        if merged_lines == 1:
            result.append(prefix + separator.join(words))
        else:
            result.extend(
                _wrapSpellCheckerIgnoreWords(
                    prefix=prefix, words=words, separator=separator
                )
            )

    return b"\n".join(result)


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

        # Normalize 'spell-checker: ignore' lines:
        # - Prose prefix: restore standard spacing after comma.
        # - Word list: no spaces after commas (word1,word2), sorted with
        #   duplicates removed, like we do for pylint disables, with
        #   consecutive lines filled up to the line length.
        updated_code = _cleanupSpellCheckerIgnores(updated_code)

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
        cleanupWindowsNewlines(filename, filename)


def cleanupDashes(filename):
    """Replace typographic dashes and hyphens with standard dashes in text files.

    Args:
        filename: path to the file
    """

    source_code = getFileContents(filename, mode="rb")

    updated_code = source_code

    for dash_character in _dash_characters:
        updated_code = updated_code.replace(dash_character.encode("utf8"), b"-")

    if updated_code != source_code:
        putBinaryFileContents(filename, updated_code)


_clang_format_path = False


def _getClangFormatPath(logger, assume_yes_for_downloads, reject_message):
    """Get the path to the clang-format executable.

    Args:
        logger: logger to use
        assume_yes_for_downloads: bool
    """
    # pylint: disable=global-statement
    global _clang_format_path

    if _clang_format_path is False:
        clang_format_path = getClangFormatBinaryPath(
            logger=logger,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message=reject_message,
        )

        if clang_format_path is not None or reject_message is not None:
            _clang_format_path = clang_format_path
        else:
            return None

    if _clang_format_path is None and reject_message is not None and logger is not None:
        with counted("clang_format_warned") as count:
            if count == 1:
                logger.warning(
                    "Need to accept clang-format download to format C files."
                )

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
        with withPrivatePipSitePackagesPathAdded(binary_path=clang_format_path):
            subprocess.call(
                [
                    clang_format_path,
                    "-i",
                    "-style={BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 120}",
                    filename,
                ]
            )


def _cleanupEmDashes(filename):
    """Replace em-dashes and en-dashes with regular dashes in C files."""

    with open(filename, "rb") as f:
        source_code = f.read()

    updated_code = source_code.replace(b"\xe2\x80\x94", b"-")
    updated_code = updated_code.replace(b"\xe2\x80\x93", b"-")

    if updated_code != source_code:
        with open(filename, "wb") as out_file:
            out_file.write(updated_code)


def formatC(
    logger,
    filename,
    effective_filename,
    assume_yes_for_downloads,
    reject_message,
):
    """Format C/C++ source code.

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
        assume_yes_for_downloads: bool - if downloads are allowed
    """
    _cleanupEmDashes(filename)

    try:
        getFileContents(filename, encoding="ascii")
    except UnicodeDecodeError:
        line_no = 0

        with open(filename, "rb") as f:
            for line_no, line in enumerate(f, start=1):
                try:
                    line.decode("ascii")
                except UnicodeDecodeError:
                    break

        return logger.sysexit(
            "All C files must be pure ASCII, need to convert it manually: %s (line %d)"
            % (effective_filename, line_no)
        )

    cleanupWindowsNewlines(filename, effective_filename)
    _cleanupClangFormat(
        logger=logger,
        filename=filename,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )
    cleanupWindowsNewlines(filename, effective_filename)


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
