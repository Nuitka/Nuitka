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
""" XML node tree handling

Means to create XML elements from Nuitka tree nodes and to convert the
XML tree to ASCII or output it.
"""

from nuitka import Tracing

try:
    import lxml.etree
except ImportError:
    lxml = None

def makeNodeElement( node ):
    result = lxml.etree.Element(
        "node",
        kind   = node.__class__.__name__.replace( "CPython", "" ),
        source = "%s" % node.getSourceReference().getLineNumber()
    )

    for key, value in node.getDetails().iteritems():
        value = str( value )

        if value.startswith( "<" ) and value.endswith( ">" ):
            value = value[1:-1]

        result.set( key, str( value ) )

#    result.text = str( node )

    return result

def toString( xml ):
    return lxml.etree.tostring( xml, pretty_print = True )

def dump( xml  ):
    Tracing.printLine( toString( xml ).rstrip() )
