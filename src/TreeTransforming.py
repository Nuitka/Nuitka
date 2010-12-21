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
""" Module with transformations of the tree.

Intended for locals/globals/eval replacement tricks, as well as hints being
applied here.

"""

import TreeOperations
import TreeBuilding
import Importing
import Nodes

from logging import warning

class TreeVisitorFixupNewStaticmethod:
    """ Delete the staticmethod decorator from __new__ methods if provided.

        CPython made these optional, and applies them to every __new__. Our
        later code will be confused if it encounters a decorator to what it
        already automatically decorated.
    """
    def __call__( self, node ):
        if node.isFunctionReference() and node.getName() == "__new__":
            decorators = node.getDecorators()

            if len( decorators ) == 1 and decorators[0].isVariableReference():
                if decorators[0].getVariable().getName() == "staticmethod":
                    # Reset the decorators. This does not attempt to deal with
                    # multiple of them being present.
                    node.decorators = ()
                    assert not node.getDecorators()



class TreeVisitorReplaceBuiltinCalls:
    """ Replace problematic builtins with alternative implementations.

    """

    def __init__( self, replacements ):
        self.replacements = replacements

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



def replaceBuiltinsCallsThatRequireInterpreter( tree, future_flags ):
    def _pickLocalsForNode( node ):
        provider = node.getParentVariableProvider()

        if provider.isModule():
            return Nodes.CPythonExpressionBuiltinCallGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return Nodes.CPythonExpressionBuiltinCallLocals(
                source_ref = node.getSourceReference()
            )

    def _pickGlobalsForNode( node ):
        return Nodes.CPythonExpressionBuiltinCallGlobals(
            source_ref = node.getSourceReference()
        )

    def globals_extractor( node ):
        assert node.isEmptyCall()

        return _pickGlobalsForNode( node )

    def locals_extractor( node ):
        assert node.isEmptyCall()

        return _pickLocalsForNode( node )


    def dir_extractor( node ):
        # Only treat the empty dir() call, leave the others alone for now.
        if not node.isEmptyCall():
            return None

        return Nodes.CPythonExpressionBuiltinCallDir(
            source_ref = node.getSourceReference()
        )

    def vars_extractor( node ):
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

    def eval_extractor( node ):
        assert node.hasOnlyPositionalArguments()

        positional_args = node.getPositionalArguments()

        return Nodes.CPythonExpressionBuiltinCallEval(
            source       = positional_args[0],
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            mode         = "eval",
            future_flags = future_flags,
            source_ref   = node.getSourceReference()
        )

    def execfile_extractor( node ):
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
            future_flags = future_flags,
            source_ref   = source_ref
        )

    def import_extractor( node ):
        if node.isFunctionCall() and node.hasOnlyPositionalArguments():
            positional_args = node.getPositionalArguments()

            if len( positional_args ) == 1 and positional_args[0].isConstantReference():
                module_name = positional_args[0].getConstant()

                if type( module_name ) is str and module_name.find( "." ) == -1:
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

    def chr_extractor( node ):
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


    def ord_extractor( node ):
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


    visitor = TreeVisitorReplaceBuiltinCalls(
        replacements = {
            "globals"    : globals_extractor,
            "locals"     : locals_extractor,
            "dir"        : dir_extractor,
            "vars"       : vars_extractor,
            "eval"       : eval_extractor,
            "execfile"   : execfile_extractor,
            "__import__" : import_extractor,
            "chr"        : chr_extractor,
            "ord"        : ord_extractor,
        }
    )

    TreeOperations.visitTree( tree, visitor )

    visitor = TreeVisitorFixupNewStaticmethod()

    TreeOperations.visitTree( tree, visitor )

class TreeVisitorOptimizeStaticExec:
    """ Inline constant execs.

    """
    def __init__( self, build_node ):
        self.build_node = build_node

    def __call__( self, node ):
        if node.isStatementExec() and node.getLocals() is None and node.getGlobals() is None:
            source = node.getSource()

            if source.isConstantReference():
                source_ref = node.getSourceReference()

                try:
                    new_node = self.build_node(
                        provider    = node.getParentVariableProvider(),
                        parent      = node.getParent(),
                        source_code = source.getConstant(),
                        filename    = source_ref.getFilename(),
                        line_offset = source_ref.getLineNumber() - 1
                    )

                    node.replaceWith( new_node )
                except SyntaxError:
                    warning( "Syntax error will be raised at runtime for exec at %s" % source_ref.getAsString() )


def replaceConstantExecs( tree, build_node ):
    visitor = TreeVisitorOptimizeStaticExec( build_node )

    TreeOperations.visitTree( tree, visitor )
