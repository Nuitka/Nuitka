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
""" XML node tree handling

Means to create XML elements from Nuitka tree nodes and to convert the
XML tree to ASCII or output it.
"""

from nuitka import Tracing, Utils

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
    value = toString( xml ).rstrip()

    if Utils.getPythonVersion() > 300:
        value = value.decode( "utf-8" )

    Tracing.printLine( value )
