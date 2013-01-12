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
""" Variable closure taking.

This is not an actual optimization. It is rather the completion of early stages. The
variables are not immediately resolved to be bound to actual scopes, but only during these
steps.

Only after this is executed, the other things can make informed decisions.

"""

from .OptimizeBase import OptimizationVisitorBase

from nuitka import SyntaxErrors

from nuitka.Utils import python_version
from nuitka.Options import isFullCompat

# Note: We do the variable scope assignment, as an extra step from tree building, because
# it will build the tree without any consideration of evaluation order. And only the way
# these visitors are entered, will ensure this order.

# The main complexity is that there are two ways of visiting. One where variable lookups
# are to be done immediately, and one where it is delayed. This is basically class vs.
# function.

class VariableClosureLookupVisitorPhase1( OptimizationVisitorBase ):
    """ Variable closure phase 1: Find assignments and early closure references.

        In class context, a reference to a variable must be obeyed immediately, so
        that "variable = variable" takes first "variable" as a closure and then adds
        a new local "variable" to override it from there on. For the not early closure
        case of a function, this will not be done and only assigments shall add local
        variables, and references be ignored until phase 2.
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
        elif node.isExpressionTempVariableRef():
            if node.getVariable().getOwner().getParentVariableProvider() != node.getParentVariableProvider():
                node.setVariable(
                    node.getParentVariableProvider().addClosureVariable( node.getVariable() )
                )

                assert node.getVariable().isClosureReference()
        elif python_version >= 300 and node.isExpressionFunctionBody():
            # Take closure variables for non-local declarations.

            for non_local_names, source_ref in node.getNonlocalDeclarations():
                for non_local_name in non_local_names:
                    variable = node.getParentVariableProvider().getVariableForReference(
                        variable_name = non_local_name
                    )

                    node.addClosureVariable( variable )

                    if variable.isModuleVariableReference():
                        SyntaxErrors.raiseSyntaxError(
                            "no binding for nonlocal '%s' found" % (
                                non_local_name
                            ),
                            source_ref   = None if isFullCompat() else source_ref,
                            display_file = not isFullCompat(),
                            display_line = not isFullCompat()
                        )


class VariableClosureLookupVisitorPhase2( OptimizationVisitorBase ):
    """ Variable closure phase 2: Find assignments and references.

        In class context, a reference to a variable must be obeyed immediately, so
        that "variable = variable" takes first "variable" as a closure and then adds
        a new local "variable" to override it from there on.

        So, assignments for early closure, accesses will already have a variable set now,
        the others, only now.
    """


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

            # Need to catch functions with "exec" not allowed.
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
                        "unqualified exec is not allowed in function '%s' it contains a nested function with free variables" % parent_provider.getName(), # pylint: disable=C0301
                        (
                            node.source_ref.getFilename(),
                            exec_line_number,
                            None,
                            lines[ exec_line_number - 1 ]
                        )

                    )

    # For Python3, every function is supposed to take "__class__" as a reference, so make
    # sure that happens.
    if python_version >= 300:
        def onLeaveNode( self, node ):
            if node.isExpressionFunctionBody() and node.isClassClosureTaker():
                node.getVariableForReference(
                    variable_name = "__class__"
                )


class VariableClosureLookupVisitorPhase3( OptimizationVisitorBase ):
    """ Variable closure phase 3: Find errors.

        In this phase, the only task remaining is to find errors. We might e.g.
        detect that a "del" was executed on a shared variable, which is not
        allowed for Python 2.x, so it must be caught. The parsing wouldn't do
        that. Currently this phase is Python2 only, but that may change.
    """


    def onEnterNode( self, node ):
        if python_version < 300:
            if node.isStatementDelVariable() and \
                 node.getTargetVariableRef().getVariable().isShared():
                raise SyntaxError(
                        "can not delete variable '%s' referenced in nested scope" % node.getTargetVariableRef().getVariableName(), # pylint: disable=C0301
                        (
                            None, # TODO: Could easily provide the line number and file
                            None,
                            None,
                            None
                        )
                    )


if python_version < 300:
    VariableClosureLookupVisitors = (
        VariableClosureLookupVisitorPhase1,
        VariableClosureLookupVisitorPhase2,
        VariableClosureLookupVisitorPhase3
    )
else:
    VariableClosureLookupVisitors = (
        VariableClosureLookupVisitorPhase1,
        VariableClosureLookupVisitorPhase2,
    )
