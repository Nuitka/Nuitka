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


from .NodeBases import CPythonExpressionChildrenHavingBase

from .NodeMakingHelpers import getComputationResult, makeConstantReplacementNode

class CPythonExpressionMakeSequenceBase( CPythonExpressionChildrenHavingBase ):
    named_children = ( "elements", )

    def __init__( self, sequence_kind, elements, source_ref ):
        assert sequence_kind in ( "TUPLE", "LIST", "SET" ), sequence_kind

        for element in elements:
            assert element.isExpression(), element

        self.sequence_kind = sequence_kind.lower()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "elements" : tuple( elements ),
            },
            source_ref = source_ref

        )

    def isExpressionMakeSequence( self ):
        return True

    def getSequenceKind( self ):
        return self.sequence_kind

    getElements = CPythonExpressionChildrenHavingBase.childGetter( "elements" )

    def getSimulator( self ):
        # Abstract method, pylint: disable=R0201,W0613
        return None

    def computeNode( self ):
        for element in self.getElements():
            if not element.isExpressionConstantRef() or element.isMutable():
                return self, None, None
        else:
            simulator = self.getSimulator()
            assert simulator is not None

            # The simulator is in fact callable if not None, pylint: disable=E1102
            return getComputationResult(
                node        = self,
                computation = lambda : simulator(
                    element.getConstant()
                    for element in
                    self.getElements()
                ),
                description = "%s with constant arguments" % simulator
            )

    def isKnownToBeIterable( self, count ):
        return count == len( self.getElements() )

    def getUnpacked( self, count ):
        # For every child except dictionaries, it's this easy.
        assert count == len( self.getElements() )

        return self.getElements()


class CPythonExpressionMakeTuple( CPythonExpressionMakeSequenceBase ):
    kind = "EXPRESSION_MAKE_TUPLE"

    def __init__( self, elements, source_ref ):
        CPythonExpressionMakeSequenceBase.__init__(
            self,
            sequence_kind = "TUPLE",
            elements      = elements,
            source_ref    = source_ref
        )

    def getSimulator( self ):
        return tuple


class CPythonExpressionMakeList( CPythonExpressionMakeSequenceBase ):
    kind = "EXPRESSION_MAKE_LIST"

    def __init__( self, elements, source_ref ):
        CPythonExpressionMakeSequenceBase.__init__(
            self,
            sequence_kind = "LIST",
            elements      = elements,
            source_ref    = source_ref
        )

    def getSimulator( self ):
        return list


class CPythonExpressionMakeSet( CPythonExpressionMakeSequenceBase ):
    kind = "EXPRESSION_MAKE_SET"

    def __init__( self, elements, source_ref ):
        CPythonExpressionMakeSequenceBase.__init__(
            self,
            sequence_kind = "SET",
            elements      = elements,
            source_ref    = source_ref
        )

    def getSimulator( self ):
        return set


class CPythonExpressionKeyValuePair( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_KEY_VALUE_PAIR"

    named_children = ( "key", "value" )

    def __init__( self, key, value, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "key"   : key,
                "value" : value
            },
            source_ref = source_ref
        )

    getKey = CPythonExpressionChildrenHavingBase.childGetter( "key" )
    getValue = CPythonExpressionChildrenHavingBase.childGetter( "value" )

    def computeNode( self ):
        return self, None, None


class CPythonExpressionMakeDict( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_MAKE_DICT"

    named_children = ( "pairs", )

    def __init__( self, pairs, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "pairs" : tuple( pairs ),
            },
            source_ref = source_ref
        )

    getPairs = CPythonExpressionChildrenHavingBase.childGetter( "pairs" )

    def computeNode( self ):
        pairs = self.getPairs()

        for pair in pairs:
            key = pair.getKey()

            if not key.isExpressionConstantRef() or key.isMutable():
                return self, None, None

            value = pair.getValue()

            if not value.isExpressionConstantRef() or value.isMutable():
                return self, None, None

        constant_value = dict.fromkeys(
            [
                pair.getKey().getConstant()
                for pair in
                pairs
            ],
            None
        )

        for pair in pairs:
            constant_value[ pair.getKey().getConstant() ] = pair.getValue().getConstant()

        new_node = makeConstantReplacementNode(
            constant = constant_value,
            node     = self
        )

        return new_node, "new_constant", "Created dictionary found to be constant."

    def getUnpacked( self, count ):
        assert False
