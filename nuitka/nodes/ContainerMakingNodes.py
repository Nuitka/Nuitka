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
""" Nodes that build containers.

"""


from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

class CPythonExpressionMakeSequence( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_MAKE_SEQUENCE"

    named_children = ( "elements", )

    def __init__( self, sequence_kind, elements, source_ref ):
        assert sequence_kind in ( "TUPLE", "LIST" ), sequence_kind

        for element in elements:
            assert element.isExpression(), element

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.sequence_kind = sequence_kind.lower()

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "elements" : tuple( elements ),
            }
        )

    def getSequenceKind( self ):
        return self.sequence_kind

    getElements = CPythonChildrenHaving.childGetter( "elements" )



class CPythonExpressionMakeSet( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_MAKE_SET"

    named_children = ( "values", )

    def __init__( self, values, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "values" : tuple( values )
            }
        )

    getValues = CPythonChildrenHaving.childGetter( "values" )


class CPythonExpressionKeyValuePair( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_KEY_VALUE_PAIR"

    named_children = ( "key", "value" )

    def __init__( self, key, value, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "key"   : key,
                "value" : value
            }
        )

    getKey = CPythonChildrenHaving.childGetter( "key" )
    getValue = CPythonChildrenHaving.childGetter( "value" )


class CPythonExpressionMakeDict( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_MAKE_DICT"

    named_children = ( "pairs", )

    def __init__( self, pairs, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "pairs" : tuple( pairs ),
            }
        )

    getPairs = CPythonChildrenHaving.childGetter( "pairs" )
