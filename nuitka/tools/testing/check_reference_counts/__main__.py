#!/usr/bin/env python
#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Tool to compare output of CPython and Nuitka.

"""

from __future__ import print_function

import os
import sys
from optparse import OptionParser

from nuitka.tools.testing.Common import checkReferenceCount, getTempDir
from nuitka.utils.Execution import check_call
from nuitka.utils.Importing import importFileAsModule


def main():
    parser = OptionParser()

    parser.add_option(
        "--checked-module",
        action="store",
        dest="checked_module",
        help="""\
Module with main() function to be checked for reference count stability.""",
    )

    options, positional_args = parser.parse_args()

    if positional_args:
        parser.print_help()

        sys.exit("\nError, no positional argument allowed.")

    # First with pure Python.
    checked_module = importFileAsModule(options.checked_module)
    checkReferenceCount(checked_module.main)

    temp_dir = getTempDir()
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--module",
        options.checked_module,
        "--output-dir",
        temp_dir,
    ]

    check_call(command)


if __name__ == "__main__":
    nuitka_package_dir = os.path.normpath(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    )

    # Unchanged, running from checkout, use the parent directory, the nuitka
    # package ought be there.
    sys.path.insert(0, nuitka_package_dir)

    main()
