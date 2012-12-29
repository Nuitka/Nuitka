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
""" Call node

Function calls and generally calling expressions are the same thing. This is very
important, because it allows to predict most things, and avoid expensive operations like
parameter parsing at run time.

The call can be computed with a call registry.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from nuitka.transform.optimizations.registry import CallRegistry

from .ConstantRefNode import CPythonExpressionConstantRef

class CPythonExpressionCall( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CALL"

    named_children = ( "called", "positional_args", "pairs", "list_star_arg", "dict_star_arg" )

    def __init__( self, called, positional_args, pairs, list_star_arg, dict_star_arg, source_ref ):
        assert called.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        assert type( pairs ) in ( list, tuple ), pairs

        for pair in pairs:
            assert pair.isExpressionKeyValuePair()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "called"          : called,
                "positional_args" : tuple( positional_args ),
                "pairs"           : tuple( pairs ),
                "list_star_arg"   : list_star_arg,
                "dict_star_arg"   : dict_star_arg
            },
            source_ref = source_ref
        )

    getCalled = CPythonExpressionChildrenHavingBase.childGetter( "called" )
    getPositionalArguments = CPythonExpressionChildrenHavingBase.childGetter( "positional_args" )
    setPositionalArguments = CPythonExpressionChildrenHavingBase.childSetter( "positional_args" )
    getNamedArgumentPairs = CPythonExpressionChildrenHavingBase.childGetter( "pairs" )
    setNamedArgumentPairs = CPythonExpressionChildrenHavingBase.childSetter( "pairs" )
    getStarListArg = CPythonExpressionChildrenHavingBase.childGetter( "list_star_arg" )
    setStarListArg = CPythonExpressionChildrenHavingBase.childSetter( "list_star_arg" )
    getStarDictArg = CPythonExpressionChildrenHavingBase.childGetter( "dict_star_arg" )
    setStarDictArg = CPythonExpressionChildrenHavingBase.childSetter( "dict_star_arg" )

    def isEmptyCall( self ):
        return not self.getPositionalArguments() and not self.getNamedArgumentPairs() and \
               not self.getStarListArg() and not self.getStarDictArg()

    def hasOnlyPositionalArguments( self ):
        return not self.getNamedArgumentPairs() and not self.getStarListArg() and \
               not self.getStarDictArg()

    def hasOnlyConstantArguments( self ):
        for positional_arg in self.getPositionalArguments():
            if not positional_arg.isExpressionConstantRef():
                return False

        for pair in self.getNamedArgumentPairs():
            if not pair.getKey().isExpressionConstantRef():
                return False

            if not pair.getValue().isExpressionConstantRef():
                return False

        list_star_arg = self.getStarListArg()

        if list_star_arg is not None and not list_star_arg.isExpressionConstantRef():
            return False

        dict_star_arg = self.getStarDictArg()

        if dict_star_arg is not None and not dict_star_arg.isExpressionConstantRef():
            return False

        return True

    def computeNode( self, constraint_collection ):
        star_list_arg = self.getStarListArg()

        if star_list_arg is not None:
            if star_list_arg.isExpressionMakeSequence():
                positional_args = self.getPositionalArguments()

                self.setPositionalArguments( positional_args + star_list_arg.getElements() )
                self.setStarListArg( None )
            elif star_list_arg.isExpressionConstantRef():
                if star_list_arg.isKnownToBeIterable( count = None ):
                    positional_args = self.getPositionalArguments()

                    constant_nodes = []

                    for constant in star_list_arg.getConstant():
                        constant_nodes.append(
                            CPythonExpressionConstantRef(
                                constant   = constant,
                                source_ref = star_list_arg.getSourceReference()
                            )
                        )

                    self.setPositionalArguments( positional_args + tuple( constant_nodes ) )
                    self.setStarListArg( None )

            star_dict_arg = self.getStarDictArg()

            if star_dict_arg is not None:
                if star_dict_arg.isExpressionMakeDict():
                    # TODO: Need to cleanup the named argument mess before it is possible.
                    pass
                elif star_dict_arg.isExpressionConstantRef():
                    # TODO: Need to cleanup the named argument mess before it is possible.
                    pass

        # There is a whole registry dedicated to this.
        return CallRegistry.computeCall( self, constraint_collection )

    def isKnownToBeIterable( self, count ):
        # Virtual method and unpredicted calls are unknown if they can be iterated at all,
        # pylint: disable=R0201,W0613
        return None

    def extractSideEffects( self ):
        return ( self, )
