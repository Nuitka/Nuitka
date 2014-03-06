#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Outputs to the user.

Printing with intends or plain, mostly a compensation for the print strangeness.

We want to avoid "from __future__ import print_function" in every file out
there, which makes adding another debug print rather tedious. This should
cover all calls/uses of "print" we have to do, and the make it easy to simply
to "print for_debug" without much hassle (braces).

"""

from __future__ import print_function

import sys

def printIndented(level, *what):
    print( "    " * level, *what )

def printSeparator(level = 0):
    print( "    " * level, "*" * 10 )

def printLine(*what):
    print( *what )

def printError(message):
    print( message, file=sys.stderr )
