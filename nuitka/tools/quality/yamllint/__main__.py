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

""" Main program for yamllint checker tool.

"""

import os
import sys

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought be there.
sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

# isort:start

from optparse import OptionParser

from nuitka.tools.Basics import goHome
from nuitka.tools.quality.ScanSources import scanTargets
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.FileOperations import resolveShellPatternToFilenames

from .YamlChecker import checkYamlSchema


def main():
    parser = OptionParser()

    parser.add_option(
        "--update-checksum",
        dest="update_checksum",
        action="store_true",
        default=False,
        help="""\
Update the version checksum after checking, so Nuitka knowns it can be trusted.""",
    )

    options, positional_args = parser.parse_args()

    if not positional_args:
        positional_args = [
            "nuitka/plugins/standard/*.yml",
            "nuitka/plugins/commercial/*.yml",
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
        scanTargets(
            positional_args,
            suffixes=(".yaml",),
        )
    )
    if not filenames:
        tools_logger.sysexit("No files found.")

    for filename in filenames:
        checkYamlSchema(
            filename=filename,
            effective_filename=filename,
            update=options.update_checksum,
            logger=tools_logger,
        )


if __name__ == "__main__":
    main()
