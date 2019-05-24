#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Main program for autoformat tool.

"""

import glob
import sys
from optparse import OptionParser

from nuitka.tools.Basics import goHome
from nuitka.tools.quality.Git import getStagedFileChangeDesc
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print

from .Autoformat import autoformat


def resolveShellPatternToFilenames(pattern):
    return glob.glob(pattern)


def main():
    parser = OptionParser()

    parser.add_option(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="""Default is %default.""",
    )

    parser.add_option(
        "--from-commit",
        action="store_true",
        dest="from_commit",
        default=False,
        help="""From commit hook, do not descend into directories. Default is %default.""",
    )

    parser.add_option(
        "--abort-on-parsing-error",
        action="store_true",
        dest="abort",
        default=False,
        help="""Stop if an error occurs, or continue. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    if options.from_commit:
        assert not positional_args
        for desc in getStagedFileChangeDesc():
            autoformat(desc["src_path"], git_stage=desc, abort=options.abort)
    else:
        if not positional_args:
            positional_args = [
                "bin",
                "nuitka",
                # "tests/*/run_all.py"
            ]

        my_print("Working on:", positional_args)

        positional_args = sum(
            (
                resolveShellPatternToFilenames(positional_arg)
                for positional_arg in positional_args
            ),
            [],
        )

        goHome()

        filenames = list(
            scanTargets(positional_args, (".py", ".scons", ".rst", ".txt", ".j2"))
        )
        if not filenames:
            sys.exit("No files found.")

        for filename in filenames:
            autoformat(filename, git_stage=False, abort=options.abort)


if __name__ == "__main__":
    main()
