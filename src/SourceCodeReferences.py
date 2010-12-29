#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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
""" Source code reference record.

All the information to lookup line and file of a code location, together with the future
flags in use there.
"""

class SourceCodeReference:
    @classmethod
    def fromFilenameAndLine( cls, filename, line, future_spec ):
        result = cls()

        result.filename = filename
        result.line = line
        result.future_spec = future_spec

        return result

    def __init__( self ):
        self.line = None
        self.filename = None
        self.future_spec = None

    def __repr__( self ):
        return "<SourceCodeReference to %s:%s>" % ( self.filename, self.line )

    def atLineNumber( self, line ):
        return SourceCodeReference.fromFilenameAndLine(
            filename    = self.filename,
            line        = line,
            future_spec = self.future_spec
        )

    def getLineNumber( self ):
        return self.line

    def getFilename( self ):
        return self.filename

    def getFutureSpec( self ):
        return self.future_spec

    def getAsString( self ):
        return "%s:%s" % ( self.filename, self.line )

    def getExecReference( self ):
        result = SourceCodeReference()

        result.line = self.line
        result.filename = self.filename

        result.future_spec = self.future_spec.clone()

        return result

def fromFilename( filename, future_spec ):
    return SourceCodeReference.fromFilenameAndLine( filename, 1, future_spec )
