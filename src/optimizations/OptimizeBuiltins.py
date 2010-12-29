#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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

from optimizations.OptimizeBase import OptimizationVisitorBase

import TreeOperations
import Importing
import Nodes

import math

class ReplaceBuiltinsVisitor( OptimizationVisitorBase ):
    def __init__( self ):
        self.replacements = {
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
            "range"      : self.range_extractor
        }

    def __call__( self, node ):
        if node.isFunctionCall():
            called = node.getCalledExpression()

            if called.isVariableReference():
                variable = called.getVariable()

                if variable.isModuleVariable():
                    var_name = variable.getName()

                    if var_name in self.replacements:
                        replacement_extractor = self.replacements[ var_name ]

                        new_node = replacement_extractor( node )

                        if new_node is not None:
                            node.replaceWith( new_node = new_node )

                            if new_node.isStatement() and node.parent.isStatementExpression():
                                node.parent.replaceWith( new_node )

                            TreeOperations.assignParent( node.parent )

                            if new_node.isConstantReference():
                                self.signalChange( "new_constant" )


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

        return Nodes.CPythonExpressionBuiltinCallDir(
            source_ref = node.getSourceReference()
        )

    def vars_extractor( self, node ):
        assert node.hasOnlyPositionalArguments()

        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 0:
            return Nodes.CPythonExpressionBuiltinCallLocals(
                source_ref = node.getSourceReference()
            )
        elif len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinCallVars(
                source     = positional_args[ 0 ],
                source_ref = node.getSourceReference()
            )
        else:
            assert False

    def eval_extractor( self, node ):
        assert node.hasOnlyPositionalArguments()

        positional_args = node.getPositionalArguments()

        return Nodes.CPythonExpressionBuiltinCallEval(
            source       = positional_args[0],
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            mode         = "eval",
            source_ref   = node.getSourceReference()
        )

    def execfile_extractor( self, node ):
        assert node.parent.isStatementExpression()

        assert node.hasOnlyPositionalArguments()
        positional_args = node.getPositionalArguments()

        source_ref = node.getSourceReference()

        source_node = Nodes.CPythonExpressionFunctionCall(
            called_expression = Nodes.CPythonExpressionAttributeLookup(
                expression = Nodes.CPythonExpressionBuiltinCallOpen(
                    filename   = positional_args[0],
                    mode       = Nodes.CPythonExpressionConstant(
                        constant   = "rU",
                        source_ref = source_ref
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
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            positional_args = node.getPositionalArguments()

            if len( positional_args ) == 1 and positional_args[0].isConstantReference():
                module_name = positional_args[0].getConstant()

                if type( module_name ) is str and "." not in module_name:
                    module_package, module_name, module_filename = Importing.findModule(
                        module_name    = module_name,
                        parent_package = node.getParentModule().getPackage()
                    )

                    return Nodes.CPythonExpressionImport(
                        module_package  = module_package,
                        module_name     = module_name,
                        module_filename = module_filename,
                        source_ref      = node.getSourceReference()
                    )
        else:
            return None

    def chr_extractor( self, node ):
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            positional_args = node.getPositionalArguments()

            if len( positional_args ) == 1:
                if positional_args[0].isConstantReference():
                    try:
                        return Nodes.CPythonExpressionConstant(
                            constant   = chr( positional_args[0] ),
                            source_ref = node.getSourceReference()
                        )
                    except:
                        return None
                else:
                    return Nodes.CPythonExpressionBuiltinCallChr(
                        value      = positional_args[0],
                        source_ref = node.getSourceReference()
                    )


    def ord_extractor( self, node ):
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            positional_args = node.getPositionalArguments()

            if len( positional_args ) == 1:
                if positional_args[0].isConstantReference():
                    try:
                        return Nodes.CPythonExpressionConstant(
                            constant   = ord( positional_args[0] ),
                            source_ref = node.getSourceReference()
                        )
                    except:
                        return None
                else:
                    return Nodes.CPythonExpressionBuiltinCallOrd(
                        value      = positional_args[0],
                        source_ref = node.getSourceReference()
                    )

    def type_extractor( self, node ):
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            positional_args = node.getPositionalArguments()

            if len( positional_args ) == 1:
                return Nodes.CPythonExpressionBuiltinCallType1(
                    value = positional_args[0],
                    source_ref = node.getSourceReference()
                )
            elif len( positional_args ) == 3:
                return Nodes.CPythonExpressionBuiltinCallType3(
                    type_name = positional_args[0],
                    bases     = positional_args[1],
                    type_dict = positional_args[2],
                    source_ref = node.getSourceReference()
                )

    def range_extractor( self, node ):
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            positional_args = node.getPositionalArguments()

            if len( positional_args ) == 1:
                arg1 = positional_args[0]

                if arg1.isConstantReference():
                    constant = arg1.getConstant()

                    # Negative values are empty, so don't check against 0.
                    if type(constant) in (int, long) and constant <= 256:
                        return Nodes.CPythonExpressionConstant(
                            constant   = range( constant ),
                            source_ref = node.getSourceReference()
                        )
            elif len( positional_args ) == 2:
                arg1, arg2 = positional_args

                if arg1.isConstantReference() and arg2.isConstantReference():
                    constant1 = arg1.getConstant()
                    constant2 = arg2.getConstant()

                    if type(constant1) in (int, long) and type(constant2) in (int, long) and constant2 - constant1 <= 256:
                        return Nodes.CPythonExpressionConstant(
                            constant   = range( constant1, constant2 ),
                            source_ref = node.getSourceReference()
                        )
            elif len( positional_args ) == 3:
                arg1, arg2, arg3 = positional_args

                if arg1.isConstantReference() and arg2.isConstantReference() and arg3.isConstantReference():
                    constant1 = arg1.getConstant()
                    constant2 = arg2.getConstant()
                    constant3 = arg3.getConstant()

                    if type(constant1) in (int, long) and type(constant2) in (int, long) and type(constant3) in (int, long):
                        if constant3 == 0:

                            # TODO: Add this node type, for now let the real range builtin
                            # do it, but that leaves us no chance to know in advance.
                            return None

                            return Nodes.CPythonExpressionRaiseException(
                                exception_type = Nodes.CPythonExpressionVariable(
                                    variable_name = "ValueError",
                                    source_ref    = node.getSourceReference()
                                ),
                                exception_value = Nodes.CPythonExpressionConstant(
                                    constant   = "range() step argument must not be zero",
                                    source_ref = node.getSourceReference()
                                ),
                                exception_trace = None,
                                source_ref = node.getSourceReference()
                            )
                        else:
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

                            # print constant1, constant2, constant3, range( constant1, constant2, constant3 ), estimate

                            assert len( range( constant1, constant2, constant3 ) ) == estimate, node.getSourceReference()

                            if estimate <= 256:
                                return Nodes.CPythonExpressionConstant(
                                    constant   = range( constant1, constant2, constant3 ),
                                    source_ref = node.getSourceReference()
                                )

    def _pickLocalsForNode( self, node ):
        """ Pick a locals default for the given node. """

        provider = node.getParentVariableProvider()

        if provider.isModule():
            return Nodes.CPythonExpressionBuiltinCallGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return Nodes.CPythonExpressionBuiltinCallLocals(
                source_ref = node.getSourceReference()
            )

    def _pickGlobalsForNode( self, node ):
        """ Pick a globals default for the given node. """

        return Nodes.CPythonExpressionBuiltinCallGlobals(
            source_ref = node.getSourceReference()
        )
