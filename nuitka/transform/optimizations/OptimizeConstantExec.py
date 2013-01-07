#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Optimization step that inlines exec where it's parameter is known.

Replace exec with string constant as parameters with the code inlined instead. This is an
optimization that is easy to do and useful for large parts of the CPython test suite that
exec constant strings.

It avoids non-compiled code and might be useful to make lazy people's usage of exec with
dynamic string built from constants to generate code on the fly performant as well.

When it strikes, it tags with "new_code", because the fresh code requires a restart of all
steps.

"""

from .OptimizeBase import OptimizationVisitorBase, warning

from nuitka.nodes.ExecEvalNodes import CPythonStatementExecInline

from nuitka import TreeBuilding

class OptimizeExecVisitor( OptimizationVisitorBase ):
    """ Inline constant execs.

    """
    def onEnterNode( self, node ):
        if node.isStatementExec() and node.getGlobals() is None and node.getLocals() is None:
            source = node.getSourceCode()

            if source.isExpressionConstantRef():
                source_ref = node.getSourceReference().getExecReference()

                try:
                    new_node = CPythonStatementExecInline(
                        provider    = node.getParentVariableProvider(),
                        source_ref  = source_ref
                    )
                    new_node.parent = node.getParent()

                    body = TreeBuilding.buildReplacementTree(
                        provider    = new_node,
                        source_code = source.getConstant(),
                        source_ref  = source_ref
                    )

                    body.parent = new_node

                    new_node.setBody( body )

                    node.replaceWith( new_node )

                    self.signalChange(
                        "new_code",
                        source_ref,
                        "Replaced 'exec' with known constant parameter with inlined code."
                    )
                except SyntaxError:
                    warning(
                        "Syntax error will be raised at runtime for exec at '%s'." %
                        source_ref.getAsString()
                    )
