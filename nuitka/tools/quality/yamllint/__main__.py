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
from nuitka.Tracing import my_print
from nuitka.utils.FileOperations import resolveShellPatternToFilenames


def checkYamllint(document):
    import yamllint.cli  # pylint: disable=I0021,import-error

    my_print("Checking %r for proper yaml ..." % document, style="blue")
    try:

        yamllint.cli.run([document])
    except SystemExit as e:
        lint_result = e.code
    else:
        sys.exit("Error, yamllint didn't raise expected SystemExit exception.")

    if lint_result != 0:
        sys.exit("Error, no lint clean yaml.")

    my_print("OK.", style="blue")


def main():
    parser = OptionParser()

    _options, positional_args = parser.parse_args()

    if not positional_args:
        positional_args = ["nuitka/plugins/standard/*.yml"]

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
        sys.exit("No files found.")

    for filename in filenames:
        checkYamllint(filename)


if __name__ == "__main__":
    main()
