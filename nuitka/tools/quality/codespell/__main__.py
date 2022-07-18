#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
import subprocess
import sys
from optparse import OptionParser

from nuitka.tools.Basics import goHome
from nuitka.tools.quality.auto_format.AutoFormat import cleanupWindowsNewlines
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print
from nuitka.utils.Execution import withEnvironmentPathAdded
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

    command = [
        "codespell",
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

    if os.name == "nt":
        extra_path = os.path.join(sys.prefix, "Scripts")
    else:
        extra_path = None

    with withEnvironmentPathAdded("PATH", extra_path):
        result = subprocess.call(command)

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
                cleanupWindowsNewlines(filename)

    if verbose:
        if result != 0:
            my_print("FAILED.")
        else:
            my_print("OK.")

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
        sys.exit(
            "\nError, please correct the spelling problems found or extend 'misc/codespell-ignore.txt' if applicable."
        )


if __name__ == "__main__":
    main()
