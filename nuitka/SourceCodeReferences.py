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
""" Source code reference record.

All the information to lookup line and file of a code location, together with the future
flags in use there.
"""

class SourceCodeReference:
    @classmethod
    def fromFilenameAndLine( cls, filename, line, future_spec, inside_exec ):
        result = cls()

        result.filename = filename
        result.line = line
        result.future_spec = future_spec
        result.inside_exec = inside_exec

        return result

    def __init__( self ):
        self.line = None
        self.filename = None
        self.future_spec = None
        self.inside_exec = False

    def __repr__( self ):
        return "<SourceCodeReference to %s:%s>" % ( self.filename, self.line )

    def atLineNumber( self, line ):
        assert int( line ) == line

        return SourceCodeReference.fromFilenameAndLine(
            filename    = self.filename,
            line        = line,
            future_spec = self.future_spec,
            inside_exec = self.inside_exec
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
        return SourceCodeReference.fromFilenameAndLine(
            filename    = self.filename,
            line        = self.line,
            future_spec = self.future_spec.clone(),
            inside_exec = True
        )

    def isExecReference( self ):
        return self.inside_exec

    def __cmp__( self, other ):
        if other is None:
            return -1

        assert isinstance( other, SourceCodeReference ), other

        result = cmp( self.filename, other.filename)

        if result == 0:
            result = cmp( self.line, other.line )

        return result

def fromFilename( filename, future_spec ):
    return SourceCodeReference.fromFilenameAndLine(
        filename    = filename,
        line        = 1,
        future_spec = future_spec,
        inside_exec = False
    )
