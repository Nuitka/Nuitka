#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
""" C++ raw strings.

This contains the code to create raw string literals for C++ to represent the given values
and little more. Because this is hard to get right with the white space problems that C++
has here, we have a paranoid debug mode that compiles a test program to verify the correctness
of each literal. That's not fast of course.
"""
import os, re

from nuitka.__past__ import commands

def _pickRawDelimiter( value ):
    delimiter = "raw"

    while delimiter in value:
        delimiter = "_" + delimiter + "_"

    return delimiter

_paranoid_debug = False

def encodeString( value ):
    """ Encode a string, so that it gives a C++ raw string literal.

    """

    delimiter = _pickRawDelimiter( value )

    start = 'R"' + delimiter + "("
    end = ")" + delimiter + '"'

    result = start + value + end

    # Replace \n, \r and \0 in the raw strings. The \0 gives a silly warning from
    # gcc (bug reported) and \n and \r even lead to wrong strings. Somehow the
    # parser of the C++ doesn't yet play nice with these.

    def decide( match ):
        if match.group(0) == "\n":
            return end + r' "\n" ' + start
        elif match.group(0) == "\r":
            return end + r' "\r" ' + start
        elif match.group(0) == "\0":
            return end + r' "\0" ' + start
        elif match.group(0) == "??":
            return end + r' "??" ' + start
        else:
            return end + r' "\\" ' + start

    result = re.sub( "\n|\r|\0|\\\\|\\?\\?", decide, result )

    # If paranoid mode is enabled, the C++ raw literals are verified by putting them
    # through a compile and checking if a test program outputs the same value.
    if _paranoid_debug:
        source_file = open( "/tmp/raw_test.cpp", "w" )

        source_file.write( """
#include <stdio.h>
int main( int argc, char *argv[] )
{
    puts( %s );
}
""" % result )

        source_file.close()

        os.system( "g++ -std=c++0x /tmp/raw_test.cpp -o /tmp/raw_test" )

        check = commands.getoutput( "/tmp/raw_test" )

        assert check == value

    return result
