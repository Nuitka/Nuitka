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

""" Main program for DLL checker tool.

"""

from __future__ import print_function

import sys
from optparse import OptionParser

from nuitka.utils.SharedLibraries import getPEFileInformation, getWindowsDLLVersion


def main():
    parser = OptionParser()

    parser.add_option(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="""\
Be verbose in output. Default is %default.""",
    )

    # TODO: Make use of options, so fa
    _options, positional_args = parser.parse_args()

    if not positional_args:
        sys.exit("No DLLs given.")

    for filename in positional_args:
        print(filename)
        print(getWindowsDLLVersion(filename))


if __name__ == "__main__":
    main()
