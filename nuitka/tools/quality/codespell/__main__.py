#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Main program for codespell checker tool."""

import os
import re
import sys

from nuitka.format.FileFormatting import cleanupWindowsNewlines
from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.Basics import goHome
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.Execution import (
    callProcessChunked,
    check_output,
    getExecutablePath,
)
from nuitka.utils.FileOperations import (
    areSamePaths,
    getFileContents,
    putTextFileContents,
    resolveShellPatternToFilenames,
)

replacements = [
    ("organizational", "organisational"),
    ("developer manual", "Developer Manual"),
    ("user manual", "User Manual"),
]


def _isSpellcheckerIgnoringFile(filename):
    return "spell-checker: disable" in getFileContents(filename)


def _isGeneratedFile(contents):
    for line in contents.splitlines()[:20]:
        if "WARNING, this code is GENERATED" in line:
            return True
    return False


def _checkIgnoreWords(contents):
    ignored_words = []
    lines = contents.splitlines()
    clean_lines = []

    for line in lines:
        match = re.search(r"spell-checker:\s*ignore\s+(.*)", line)
        if match:
            # Add words found to the list of ignored words, we need to check matches
            # for them.
            words = match.group(1).replace(",", " ").split()
            ignored_words.extend(words)

            # verify if the word is present in the file, checking the line too, but
            # ignoring the command itself.
            line = line[: match.start()] + line[match.end() :]

        clean_lines.append(line)

    if not ignored_words:
        return []

    clean_content = "\n".join(clean_lines).lower()

    unused = []
    for word in ignored_words:
        # Check if the word is present in the file, as a substring (e.g. CamelCase).
        if word.lower() not in clean_content:
            unused.append(word)

    return unused


def runCodespell(filenames, verbose, write):
    if verbose:
        my_print("Consider", " ".join(filenames))

    if os.name == "nt":
        extra_path = os.path.join(sys.prefix, "Scripts")
    else:
        extra_path = None

    codespell_binary = getExecutablePath("codespell", extra_dir=extra_path)

    codespell_version = check_output([codespell_binary, "--version"])

    if str is not bytes:
        codespell_version = codespell_version.decode("utf8").strip()

    my_print("Using codespell version:", codespell_version)

    command = [
        codespell_binary,
        "-f",
        "-I",
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
            "misc/codespell-ignore.txt",
        ),
    ]

    if write:
        command.append("-w")

    result = callProcessChunked(
        command, filenames, logger=tools_logger if verbose else None
    )

    # Check for unnecessary ignores, but only if the file is cleanly passing
    # codespell check itself.
    found_superfluous_ignores = False

    if result == 0:
        for filename in filenames:
            if areSamePaths(__file__, filename):
                continue

            contents = getFileContents(filename)

            if not _isGeneratedFile(contents):
                unused_ignores = _checkIgnoreWords(contents)

                if unused_ignores:
                    my_print(
                        "%s: Error, unused ignore words: %s"
                        % (filename, ",".join(unused_ignores))
                    )
                    found_superfluous_ignores = True

            old_contents = contents
            for word, replacement in replacements:
                contents = contents.replace(word, replacement)
                contents = contents.replace(word.title(), replacement.title())

            if old_contents != contents:
                putTextFileContents(filename, contents)
                cleanupWindowsNewlines(filename, filename)

    return result == 0 and not found_superfluous_ignores


def main():
    parser = makeOptionsParser(usage="%prog [options]", epilog=None)

    parser.add_option(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="""Show what it is doing. Default is %default.""",
    )

    parser.add_option(
        "--write",
        "-w",
        action="store_true",
        dest="write",
        default=False,
        help="""Write changes to the files. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    if not positional_args:
        positional_args = [
            "bin",
            "nuitka",
            "rpm",
            "misc",
            "tests/*/run_all.py",
            "*.rst",
        ]
        goHome()

    my_print("Working on:", positional_args)

    positional_args = sum(
        (
            resolveShellPatternToFilenames(positional_arg)
            for positional_arg in positional_args
        ),
        [],
    )

    filenames = list(
        scanTargets(
            positional_args,
            suffixes=(".py", ".scons", ".rst", ".txt", ".j2", ".md", ".c", ".h"),
            ignore_list=("get-pip-2.6.py",),
        )
    )

    filenames = [
        filename for filename in filenames if not _isSpellcheckerIgnoringFile(filename)
    ]
    if not filenames:
        sys.exit("No files found.")

    result = runCodespell(
        filenames=filenames, verbose=options.verbose, write=options.write
    )

    if result:
        my_print("OK.")
    else:
        my_print("FAILED.")
        tools_logger.sysexit(
            "\nError, please correct the spelling problems found or extend 'misc/codespell-ignore.txt' if applicable."
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
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
