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

""" Main program for autoformat tool.

"""

from optparse import OptionParser

from nuitka.Progress import enableProgressBar, wrapWithProgressBar
from nuitka.tools.quality.autoformat.Autoformat import autoformat
from nuitka.tools.quality.Git import getStagedFileChangeDesc
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.FileOperations import resolveShellPatternToFilenames


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
        "--check-only",
        action="store_true",
        dest="check_only",
        default=False,
        help="""For CI testing, check if it's properly formatted. Default is %default.""",
    )

    parser.add_option(
        "--no-progressbar",
        action="store_false",
        dest="progress_bar",
        default=True,
        help="""Disable progress bar outputs (if tqdm is installed).
Defaults to off.""",
    )

    options, positional_args = parser.parse_args()

    if options.from_commit:
        assert not positional_args
        for desc in getStagedFileChangeDesc():
            autoformat(desc["src_path"], git_stage=desc)
    else:
        if not positional_args:
            positional_args = ["bin", "nuitka", "setup.py", "tests/*/run_all.py"]

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
            tools_logger.sysexit("No files found.")

        result = 0

        if options.progress_bar:
            enableProgressBar()

        for filename in wrapWithProgressBar(
            filenames, stage="Autoformat", unit="files"
        ):
            if autoformat(filename, git_stage=False, check_only=options.check_only):
                result += 1

        if options.check_only and result > 0:
            tools_logger.sysexit(
                """Error, bin/autoformat-nuitka-source would make changes to %d files, \
make sure to have commit hook installed."""
                % result
            )
        elif result > 0:
            tools_logger.info("autoformat: Changes to formatting of %d files" % result)
        else:
            tools_logger.info("autoformat: No files needed formatting changes.")


if __name__ == "__main__":
    main()
