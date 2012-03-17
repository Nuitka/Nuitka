#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
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

        self.set_line = True

    def __repr__( self ):
        return "<%s to %s:%s>" % ( self.__class__.__name__, self.filename, self.line )

    def clone( self, line ):
        result = SourceCodeReference.fromFilenameAndLine(
            filename    = self.filename,
            line        = line,
            future_spec = self.future_spec,
            inside_exec = self.inside_exec
        )

        result.set_line = self.set_line

        return result

    def atLineNumber( self, line ):
        assert int( line ) == line

        return self.clone( line )

    def getLineNumber( self ):
        return self.line

    def getFilename( self ):
        return self.filename

    def getFutureSpec( self ):
        return self.future_spec

    def getAsString( self ):
        return "%s:%s" % ( self.filename, self.line )

    def getExecReference( self ):
        return self.__class__.fromFilenameAndLine(
            filename    = self.filename,
            line        = self.line,
            future_spec = self.future_spec.clone(),
            inside_exec = True
        )

    def isExecReference( self ):
        return self.inside_exec

    def shallSetCurrentLine( self ):
        return self.set_line

    def __cmp__( self, other ):
        if other is None:
            return -1

        assert isinstance( other, SourceCodeReference ), other

        result = cmp( self.filename, other.filename)

        if result == 0:
            result = cmp( self.line, other.line )

        return result

    def atInternal( self ):
        if self.set_line:
            result = self.clone( self.line )
            result.set_line = False

            return result
        else:
            return self


def fromFilename( filename, future_spec ):
    return SourceCodeReference.fromFilenameAndLine(
        filename    = filename,
        line        = 1,
        future_spec = future_spec,
        inside_exec = False
    )
