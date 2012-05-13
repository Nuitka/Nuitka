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
""" Node the calls to the 'dict' builtin.

"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .ConstantRefNode import CPythonExpressionConstantRef
from .ContainerMakingNodes import CPythonExpressionKeyValuePair

from .NodeMakingHelpers import getComputationResult

from nuitka.transform.optimizations.BuiltinOptimization import builtin_dict_spec

class CPythonExpressionBuiltinDict( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_DICT"

    named_children = ( "pos_arg", "pairs" )

    def __init__( self, pos_arg, pairs, source_ref ):
        assert type( pos_arg ) not in ( tuple, list ), source_ref
        assert type( pairs ) in ( tuple, list ), source_ref

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "pos_arg" : pos_arg,
                "pairs"   : tuple(
                    CPythonExpressionKeyValuePair(
                        CPythonExpressionConstantRef( key, source_ref ),
                        value,
                        value.getSourceReference()
                    )
                    for key, value in
                    pairs
                )
            },
            source_ref = source_ref
        )

    getPositionalArgument = CPythonExpressionChildrenHavingBase.childGetter( "pos_arg" )
    getNamedArgumentPairs = CPythonExpressionChildrenHavingBase.childGetter( "pairs" )

    def hasOnlyConstantArguments( self ):
        pos_arg = self.getPositionalArgument()

        if pos_arg is not None and not pos_arg.isCompileTimeConstant():
            return False

        for arg_pair in self.getNamedArgumentPairs():
            if not arg_pair.getKey().isCompileTimeConstant():
                return False
            if not arg_pair.getValue().isCompileTimeConstant():
                return False

        return True

    def computeNode( self, constraint_collection ):
        if self.hasOnlyConstantArguments():
            pos_arg = self.getPositionalArgument()

            if pos_arg is not None:
                pos_args = ( pos_arg, )
            else:
                pos_args = None

            return getComputationResult(
                node         = self,
                computation = lambda : builtin_dict_spec.simulateCall(
                    ( pos_args, self.getNamedArgumentPairs() )
                ),
                description = "Replace dict call with constant arguments"
            )
        else:
            return self, None, None
