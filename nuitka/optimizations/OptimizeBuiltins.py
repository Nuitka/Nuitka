#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
""" Replace builtins with alternative implementations more optimized or capable of the task.

TODO: Split in two phases, such that must be replaced (locals(), globals() and such that
are just a good idea to replace (range(), etc)
"""

from .OptimizeBase import OptimizationVisitorBase

from nuitka import TreeOperations, Importing, Nodes

from nuitka.Utils import getPythonVersion

import math

_builtin_names = [ str( x ) for x in __builtins__.keys() ]
assert "int" in _builtin_names, __builtins__.keys()

class OptimizationDispatchingVisitorBase( OptimizationVisitorBase ):

    def __init__( self, dispatch_dict ):
        self.dispatch_dict = dispatch_dict

    def __call__( self, node ):
        key = self.getKey( node )

        if key in self.dispatch_dict:
            new_node = self.dispatch_dict[ key ]( node )

            if new_node is not None:
                node.replaceWith( new_node = new_node )

                if new_node.isStatement() and node.parent.isStatementExpression():
                    node.parent.replaceWith( new_node )

                TreeOperations.assignParent( node.parent )

                if new_node.isConstantReference():
                    self.signalChange(
                        "new_constant",
                        node.getSourceReference(),
                        message = "Replaced %s with constant result." % node.kind
                    )
                elif new_node.isBuiltin():
                    self.signalChange(
                        "new_builtin",
                        node.getSourceReference(),
                        message = "Replaced call to builtin %s with builtin call." % new_node.kind
                    )




class ReplaceBuiltinsVisitor( OptimizationDispatchingVisitorBase ):
    def __init__( self ):
        OptimizationDispatchingVisitorBase.__init__(
            self,
            dispatch_dict = {
                "globals"    : self.globals_extractor,
                "locals"     : self.locals_extractor,
                "dir"        : self.dir_extractor,
                "vars"       : self.vars_extractor,
                "eval"       : self.eval_extractor,
                "execfile"   : self.execfile_extractor,
                "__import__" : self.import_extractor,
                "chr"        : self.chr_extractor,
                "ord"        : self.ord_extractor,
                "type"       : self.type_extractor,
                "range"      : self.range_extractor,
# TODO: There is a case of len overload in the CPython test suite that we do not yet
# discover, because we have no test for write to module level variable yet, which is
# a potential breaker for every builtin replacement.
#                "len"        : self.len_extractor,
            }
        )

    def getKey( self, node ):
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            called = node.getCalledExpression()

            if called.isVariableReference():
                variable = called.getVariable()

                if variable.isModuleVariable():
                    return variable.getName()


    def globals_extractor( self, node ):
        assert node.isEmptyCall()

        return self._pickGlobalsForNode( node )

    def locals_extractor( self, node ):
        assert node.isEmptyCall()

        return self._pickLocalsForNode( node )

    def dir_extractor( self, node ):
        # Only treat the empty dir() call, leave the others alone for now.
        if not node.isEmptyCall():
            return None

        return Nodes.CPythonExpressionBuiltinDir(
            source_ref = node.getSourceReference()
        )

    def vars_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 0:
            return Nodes.CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )
        elif len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinVars(
                source     = positional_args[ 0 ],
                source_ref = node.getSourceReference()
            )
        else:
            assert False

    def eval_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        return Nodes.CPythonExpressionBuiltinEval(
            source       = positional_args[0],
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            source_ref   = node.getSourceReference()
        )

    def execfile_extractor( self, node ):
        assert node.parent.isStatementExpression()

        positional_args = node.getPositionalArguments()

        source_ref = node.getSourceReference()

        source_node = Nodes.CPythonExpressionFunctionCall(
            called_expression = Nodes.CPythonExpressionAttributeLookup(
                expression = Nodes.CPythonExpressionBuiltinOpen(
                    filename   = positional_args[0],
                    mode       = Nodes.makeConstantReplacementNode(
                        constant = "rU",
                        node     = node
                    ),
                    buffering  = None,
                    source_ref = source_ref
                ),
                attribute = "read",
                source_ref = source_ref
            ),
            positional_args = (),
            named_args = (),
            list_star_arg = None,
            dict_star_arg = None,
            source_ref    = source_ref
        )

        return Nodes.CPythonStatementExec(
            source       = source_node,
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            source_ref   = source_ref
        )

    def import_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1 and positional_args[0].isConstantReference():
            module_name = positional_args[0].getConstant()

            if type( module_name ) is str and "." not in module_name:
                _module_package, module_name, _module_filename = Importing.findModule(
                    module_name    = module_name,
                    parent_package = node.getParentModule().getPackage()
                )

                return Nodes.CPythonExpressionBuiltinImport(
                    module_name     = module_name,
                    source_ref      = node.getSourceReference()
                )

    def chr_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinChr(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )


    def ord_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinOrd(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )

    def type_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinType1(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )
        elif len( positional_args ) == 3:
            return Nodes.CPythonExpressionBuiltinType3(
                type_name  = positional_args[0],
                bases      = positional_args[1],
                type_dict  = positional_args[2],
                source_ref = node.getSourceReference()
            )

    def range_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) >= 1 and len( positional_args ) <= 3:
            low = positional_args[0]
            high = positional_args[1] if len( positional_args ) > 1 else None
            step = positional_args[2] if len( positional_args ) > 2 else None

            return Nodes.CPythonExpressionBuiltinRange(
                low        = low,
                high       = high,
                step       = step,
                source_ref = node.getSourceReference()
            )

    def len_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinLen(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )

    def _pickLocalsForNode( self, node ):
        """ Pick a locals default for the given node. """

        provider = node.getParentVariableProvider()

        if provider.isModule():
            return Nodes.CPythonExpressionBuiltinGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return Nodes.CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )

    def _pickGlobalsForNode( self, node ):
        """ Pick a globals default for the given node. """

        return Nodes.CPythonExpressionBuiltinGlobals(
            source_ref = node.getSourceReference()
        )


class PrecomputeBuiltinsVisitor( OptimizationDispatchingVisitorBase ):
    def __init__( self ):
        OptimizationDispatchingVisitorBase.__init__(
            self,
            dispatch_dict = {
#                "globals"    : self.globals_extractor,
#                "locals"     : self.locals_extractor,
#                "dir"        : self.dir_extractor,
#                "vars"       : self.vars_extractor,
                "chr"        : self.chr_extractor,
                "ord"        : self.ord_extractor,
                "type1"      : self.type1_extractor,
                "range"      : self.range_extractor
            }
        )

    def getKey( self, node ):
        if node.isBuiltin():
            return node.kind.replace( "EXPRESSION_BUILTIN_", "" ).lower()


    def chr_extractor( self, node ):
        value = node.getValue()

        if value.isConstantReference():
            value = value.getConstant()

            try:
                return Nodes.makeConstantReplacementNode(
                    constant = chr( value ),
                    node     = node
                )
            except:
                pass

    def ord_extractor( self, node ):
        value = node.getValue()

        if value.isConstantReference():
            value = value.getConstant()

            try:
                return Nodes.makeConstantReplacementNode(
                    constant = ord( value ),
                    node     = node
                )
            except:
                pass


    def type1_extractor( self, node ):
        value = node.getValue()

        if value.isConstantReference():
            value = value.getConstant()

            if value is not None:
                type_name = value.__class__.__name__

                assert (type_name in _builtin_names), (type_name, _builtin_names)

                result = Nodes.CPythonExpressionVariableRef(
                    variable_name = type_name,
                    source_ref    = node.getSourceReference()
                )

                result.setVariable(
                    variable = node.getParentModule().getVariableForReference(
                        variable_name = type_name
                    )
                )

                self.signalChange(
                    "new_variable",
                    node.getSourceReference(),
                    message = "Replaced predictable type lookup with result '%s'." % type_name
                )

                return result


    def range_extractor( self, node ):
        low  = node.getLow()
        high = node.getHigh()
        step = node.getStep()

        def isRangePredictable( node ):
            if node.isConstantReference():
                return node.isNumberConstant()
            else:
                return False

        if high is None and step is None:
            if isRangePredictable( low ):
                constant = low.getConstant()

                if type( constant ) is float:
                    if getPythonVersion() < 270:
                        constant = int( constant )
                    else:
                        # TODO: Add this node type, for now let the real range builtin do
                        # it, but that leaves the optimizer no chance to know in advance.
                        return None

                # Negative values are empty, so don't check against 0.
                if constant <= 256:

                    return Nodes.makeConstantReplacementNode(
                        constant = range( constant ),
                        node     = node
                    )
        elif step is None:
            if isRangePredictable( low ) and isRangePredictable( high ):
                constant1 = low.getConstant()
                constant2 = high.getConstant()

                if type( constant1 ) is float:
                    if getPythonVersion() < 270:
                        constant1 = int( constant1 )
                    else:
                        # TODO: Add this node type, for now let the real range builtin do
                        # it, but that leaves the optimizer no chance to know in advance.
                        return None
                if type( constant2 ) is float:
                    if getPythonVersion() < 270:
                        constant2 = int( constant2 )
                    else:
                        # TODO: Add this node type, for now let the real range builtin do
                        # it, but that leaves the optimizer no chance to know in advance.
                        return None

                if constant2 - constant1 <= 256:
                    return Nodes.makeConstantReplacementNode(
                        constant = range( constant1, constant2 ),
                        node     = node
                    )
        else:
            if isRangePredictable( low ) and isRangePredictable( high ) and isRangePredictable( step ):
                constant1 = low.getConstant()
                constant2 = high.getConstant()
                constant3 = step.getConstant()

                if type( constant1 ) is float:
                    if getPythonVersion() < 270:
                        constant1 = int( constant1 )
                    else:
                        # TODO: Add this node type, for now let the real range builtin do
                        # it, but that leaves the optimizer no chance to know in advance.
                        return None
                if type( constant2 ) is float:
                    if getPythonVersion() < 270:
                        constant2 = int( constant2 )
                    else:
                        # TODO: Add this node type, for now let the real range builtin do
                        # it, but that leaves the optimizer no chance to know in advance.
                        return None
                if type( constant3 ) is float:
                    if getPythonVersion() < 270:
                        constant3 = int( constant3 )
                    else:
                        # TODO: Add this node type, for now let the real range builtin do
                        # it, but that leaves the optimizer no chance to know in advance.
                        return None

                if constant3 == 0:
                    # TODO: Add this node type, for now let the real range builtin
                    # do it, but that leaves the optimizer no chance to know in
                    # advance.
                    return None

                    return Nodes.CPythonExpressionRaiseException(
                        exception_type = Nodes.CPythonExpressionVariable(
                            variable_name = "ValueError",
                            source_ref    = node.getSourceReference()
                        ),
                        exception_value = Nodes.makeConstantReplacementNode(
                            constant = "range() step argument must not be zero",
                            node     = node
                        ),
                        exception_trace = None,
                        source_ref = node.getSourceReference()
                    )

                if constant1 < constant2:
                    if constant3 < 0:
                        estimate = 0
                    else:
                        estimate = math.ceil( float( constant2 - constant1 ) / constant3 )
                else:
                    if constant3 > 0:
                        estimate = 0
                    else:
                        estimate = math.ceil( float( constant2 - constant1 ) / constant3 )

                estimate = round( estimate )

                assert len( range( constant1, constant2, constant3 ) ) == estimate, node.getSourceReference()

                if estimate <= 256:
                    return Nodes.makeConstantReplacementNode(
                        constant = range( constant1, constant2, constant3 ),
                        node     = node
                    )


    def len_extractor( self, node ):
        value = node.getValue()

        if value.isConstantReference() and value.isIterableConstant():
            return Nodes.makeConstantReplacementNode(
                constant = len( value.getConstant() ),
                node     = node
            )
