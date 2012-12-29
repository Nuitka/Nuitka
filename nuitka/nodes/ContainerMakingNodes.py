#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Nodes that build containers.

"""


from .NodeBases import CPythonExpressionChildrenHavingBase, CPythonSideEffectsFromChildrenMixin

from .NodeMakingHelpers import getComputationResult, makeConstantReplacementNode

class CPythonExpressionMakeSequenceBase( CPythonSideEffectsFromChildrenMixin, \
                                         CPythonExpressionChildrenHavingBase ):
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

    def computeNode( self, constraint_collection ):
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
        return count is None or count == len( self.getElements() )

    def getIterationValue( self, count, constraint_collection ):
        return self.getElements()[ count ]

    def getIterationLength( self, constraint_collection ):
        return len( self.getElements() )

    def canPredictIterationValues( self, constraint_collection ):
        return True

    def getTruthValue( self, constraint_collection ):
        return self.getIterationLength( constraint_collection ) > 0


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

    def computeNode( self, constraint_collection ):
        return self, None, None


class CPythonExpressionMakeDict( CPythonSideEffectsFromChildrenMixin, \
                                 CPythonExpressionChildrenHavingBase ):
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

    def computeNode( self, constraint_collection ):
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

    def isKnownToBeIterable( self, count ):
        return count is None or count == len( self.getPairs() )

    def getIterationLength( self, constraint_collection ):
        return len( self.getPairs() )

    def canPredictIterationValues( self, constraint_collection ):
        return True

    def getIterationValue( self, count, constraint_collection ):
        return self.getPairs()[ count ].getKey()

    def getTruthValue( self, constraint_collection ):
        return self.getIterationLength( constraint_collection ) > 0
