#!/usr/bin/env python
#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" Main program for codespell checker tool.

"""

import os
import sys
from optparse import OptionParser

from nuitka.tools.Basics import goHome
from nuitka.tools.quality.auto_format.AutoFormat import cleanupWindowsNewlines
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.Execution import callProcess, check_output, getExecutablePath
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
    command += filenames

    result = callProcess(command, logger=tools_logger if verbose else None)

    if result == 0:
        for filename in filenames:
            if areSamePaths(__file__, filename):
                continue

            contents = getFileContents(filename)
            old_contents = contents

            for word, replacement in replacements:
                contents = contents.replace(word, replacement)
                contents = contents.replace(word.title(), replacement.title())

            if old_contents != contents:
                putTextFileContents(filename, contents)
                cleanupWindowsNewlines(filename, filename)

    return result == 0


def main():
    parser = OptionParser()

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
        )
    )
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
