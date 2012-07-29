#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Variable closure taking.

Run away, don't read it, quick. Heavily underdocumented rules are implemented here.

"""

from .OptimizeBase import OptimizationVisitorScopedBase

from nuitka.Utils import python_version

# TODO: The variable closure thing looks like it should be collapsed into tree building,
# this does not at all depend on completion of the node tree. Just the not early closure
# kinds need to make an extra pass, once their body is complete, in order to assign the
# variable.

class VariableClosureLookupVisitorPhase2( OptimizationVisitorScopedBase ):
    """ Variable closure phase 2: Find assignments and early closure references.

        In class context, a reference to a variable must be obeyed immediately, so
        that "variable = variable" takes first "variable" as a closure and then adds
        a new local "variable" to override it from there on. For the not early closure
        case of a function, this will not be done and only assigments shall add local
        variables, and references be ignored until phase 3.
    """

    def onEnterNode( self, node ):
        if node.isExpressionTargetVariableRef():
            if node.getVariable() is None:
                provider = node.getParentVariableProvider()

                node.setVariable(
                    provider.getVariableForAssignment(
                        variable_name = node.getVariableName()
                    )
                )
        elif node.isExpressionVariableRef():
            if node.getVariable() is None:
                provider = node.getParentVariableProvider()

                if provider.isEarlyClosure():
                    node.setVariable(
                        provider.getVariableForReference(
                            variable_name = node.getVariableName()
                        )
                    )


class VariableClosureLookupVisitorPhase3( OptimizationVisitorScopedBase ):
    def onEnterNode( self, node ):
        if node.isExpressionVariableRef() and node.getVariable() is None:
            provider = node.getParentVariableProvider()

            # print "Late reference", node.getVariableName(), "for", provider, "caused at", node, "of", node.getParent()

            variable = provider.getVariableForReference(
                variable_name = node.getVariableName()
            )

            node.setVariable(
                variable
            )

            assert not (node.getParent().isStatementDelVariable())

            if python_version < 300 and provider.isExpressionFunctionBody() and \
               variable.isReference() and \
                 (not variable.isModuleVariableReference() or \
                  not variable.isFromGlobalStatement() ):

                parent_provider = provider.getParentVariableProvider()

                while parent_provider.isExpressionFunctionBody() and parent_provider.isClassDictCreation():
                    parent_provider = parent_provider.getParentVariableProvider()

                if parent_provider.isExpressionFunctionBody() and parent_provider.isUnqualifiedExec():
                    lines = open( node.source_ref.getFilename(), "rU" ).readlines()
                    exec_line_number = parent_provider.getExecSourceRef().getLineNumber()

                    raise SyntaxError(
                        "unqualified exec is not allowed in function '%s' it contains a nested function with free variables" % parent_provider.getName(),
                        (
                            node.source_ref.getFilename(),
                            exec_line_number,
                            None,
                            lines[ exec_line_number - 1 ]
                        )

                    )

    if python_version >= 300:
        def onLeaveNode( self, node ):
            if node.isExpressionFunctionBody() and node.isClassClosureTaker():
                node.getVariableForReference(
                    variable_name = "__class__"
                )

class VariableClosureLookupVisitorPhase4( OptimizationVisitorScopedBase ):
    def onEnterNode( self, node ):
        if python_version < 300:
            if node.isStatementDelVariable() and \
                 node.getTargetVariableRef().getVariable().isShared():
                raise SyntaxError(
                        "can not delete variable '%s' referenced in nested scope" % node.getTargetVariableRef().getVariableName(),
                        (
                            None, # TODO: Could easily provide the line number and file
                            None,
                            None,
                            None
                        )
                    )


VariableClosureLookupVisitors = (
    VariableClosureLookupVisitorPhase2,
    VariableClosureLookupVisitorPhase3,
    VariableClosureLookupVisitorPhase4
)
