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

    def __init__( self, called_expression, positional_args, pairs, list_star_arg, dict_star_arg, source_ref ):
        assert called_expression.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        assert type( pairs ) in ( list, tuple ), pairs

        for pair in pairs:
            assert pair.isExpressionKeyValuePair()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "called"          : called_expression,
                "positional_args" : tuple( positional_args ),
                "pairs"           : tuple( pairs ),
                "list_star_arg"   : list_star_arg,
                "dict_star_arg"   : dict_star_arg
            },
            source_ref = source_ref
        )

        assert self.getChild( "called" ) is called_expression

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
        return CallRegistry.computeCall( self )

    def isKnownToBeIterable( self, count ):
        # Virtual method and unpredicted calls are unknown if they can be iterated at all,
        # pylint: disable=R0201,W0613
        return None
