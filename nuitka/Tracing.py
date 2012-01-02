#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at a later time to
#     the PSF. With this version of Nuitka, using it for a Closed Source and
#     distributing the binary only is not allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Outputs to the user.

Printing with intends or plain, mostly a compensation for the print strageness. I want to
avoid "from __future__ import print_function" in every file out there, which makes adding
another print rather tedious. This should cover all calls/uses of "print" we have to do,
and the make it easy to simply to "print for_debug" without much hassle (braces).

"""

from __future__ import print_function

import sys

def printIndented( level, *what ):
    print( "    " * level, *what )

def printSeparator( level = 0 ):
    print( "    " * level, "*" * 10 )

def printLine( *what ):
    print( *what )

def printError( message ):
    print( message, file=sys.stderr )
