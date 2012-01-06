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
""" Handling of syntax errors.

Format SyntaxError/IndentationError exception for output, as well as
raise it for the given source code reference.
"""

def formatOutput( e ):
    reason, ( filename, lineno, colno, message ) = e.args

    if colno is not None:
        colno = colno - len( message ) + len( message.lstrip() )

        return """\
  File "%s", line %d
    %s
    %s^
%s: %s""" % (
            filename,
            lineno,
            message.strip(),
            " " * (colno-1) if colno is not None else "",
            e.__class__.__name__,
            reason
         )
    else:
        return """\
  File "%s", line %d
    %s
%s: %s""" % (
            filename,
            lineno,
            message.strip(),
            e.__class__.__name__,
            reason
         )

def raiseSyntaxError( reason, source_ref ):
    source = open( source_ref.getFilename(), 'rU' ).readlines()

    raise SyntaxError(
        reason,
        (
            source_ref.getFilename(),
            source_ref.getLineNumber(),
            None,
            source[ source_ref.getLineNumber() - 1 ],
        )
    )
