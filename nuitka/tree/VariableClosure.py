#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

This is the completion of variable object completion. The variables were not
immediately resolved to be bound to actual scopes, but are only now.

Only after this is executed, variable reference nodes can be considered
complete.
"""

from nuitka.nodes.FunctionNodes import MaybeLocalVariableUsage
from nuitka.nodes.LocalsDictNodes import (
    ExpressionLocalsVariableRef,
    ExpressionLocalsVariableRefOrFallback,
    StatementLocalsDictOperationDel,
    StatementLocalsDictOperationSet,
)
from nuitka.nodes.NodeMakingHelpers import (
    makeConstantReplacementNode,
    mergeStatements,
)
from nuitka.nodes.OperatorNodes import makeExpressionOperationBinaryInplace
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableDelNodes import makeStatementDelVariable
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    makeExpressionVariableRef,
)
from nuitka.nodes.VariableReleaseNodes import makeStatementReleaseVariable
from nuitka.PythonVersions import (
    getErrorMessageExecWithNestedFunction,
    python_version,
)
from nuitka.Variables import isSharedAmongScopes, releaseSharedScopeInformation

from .Operations import VisitorNoopMixin, visitTree
from .ReformulationFunctionStatements import addFunctionVariableReleases
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .SyntaxErrors import raiseSyntaxError

# Note: We do the variable scope assignment, as an extra step from tree
# building, because tree building creates the tree without any consideration of
# evaluation order. And the ordered way these visitors are entered, will ensure
# this order.

# The main complexity is that there are two ways of visiting. One where variable
# lookups are to be done immediately, and one where it is delayed. This is
# basically class vs. function scope handling.


class VariableClosureLookupVisitorPhase1(VisitorNoopMixin):
    """Variable closure phase 1: Find assignments and early closure references.

    In class context, a reference to a variable must be obeyed immediately,
    so that "variable = variable" takes first "variable" as a closure and
    then adds a new local "variable" to override it from there on. For the
    not early closure case of a function, this will not be done and only
    assignments shall add local variables, and references will be ignored
    until phase 2.
    """

    @staticmethod
    def _handleNonLocal(node):
        # Take closure variables for non-local declarations.

        for (
            non_local_names,
            user_provided,
            source_ref,
        ) in node.consumeNonlocalDeclarations():
            for non_local_name in non_local_names:
                variable = node.takeVariableForClosure(variable_name=non_local_name)

                if variable.isModuleVariable() and user_provided:
                    raiseSyntaxError(
                        "no binding for nonlocal '%s' found" % (non_local_name),
                        source_ref,
                    )

                if node.isExpressionClassBody() and non_local_name == "__class__":
                    pass
                else:
                    node.getLocalsScope().registerClosureVariable(variable)

                variable.addVariableUser(node)

    @staticmethod
    def _handleQualnameSetup(node):
        if node.qualname_setup is not None:
            provider = node.getParentVariableProvider()

            if node.isExpressionClassBody():
                class_variable_name, qualname_assign = node.qualname_setup

                if provider.hasProvidedVariable(class_variable_name):
                    class_variable = provider.getVariableForReference(
                        class_variable_name
                    )

                    if class_variable.isModuleVariable():
                        qualname_node = qualname_assign.subnode_source

                        new_node = makeConstantReplacementNode(
                            constant=class_variable.getName(),
                            node=qualname_node,
                            user_provided=True,
                        )

                        parent = qualname_node.parent
                        qualname_node.finalize()
                        parent.replaceChild(qualname_node, new_node)

                        node.qualname_provider = node.getParentModule()
            else:
                if provider.hasProvidedVariable(node.qualname_setup):
                    function_variable = provider.getVariableForReference(
                        node.qualname_setup
                    )

                    if function_variable.isModuleVariable():
                        node.qualname_provider = node.getParentModule()

            # TODO: Actually for nested global classes, this approach
            # may not work, as their "qualname" will be wrong. In that
            # case a dedicated node for "qualname" references might be
            # needed.

            node.qualname_setup = None

    @staticmethod
    def _shouldUseLocalsDict(provider, variable_name):
        return provider.isExpressionClassBody() and (
            not provider.hasProvidedVariable(variable_name)
            or provider.getProvidedVariable(variable_name).getOwner() is provider
        )

    def onLeaveNode(self, node):
        if node.isStatementAssignmentVariableName():
            variable_name = node.getVariableName()
            provider = node.provider

            # Classes always assign to locals dictionary except for closure
            # variables taken.
            if self._shouldUseLocalsDict(provider, variable_name):
                if node.subnode_source.isExpressionOperationInplace():
                    temp_scope = provider.allocateTempScope("class_inplace")

                    tmp_variable = provider.allocateTempVariable(
                        temp_scope=temp_scope, name="value"
                    )

                    statements = mergeStatements(
                        statements=(
                            makeStatementAssignmentVariable(
                                variable=tmp_variable,
                                source=node.subnode_source.subnode_left,
                                source_ref=node.source_ref,
                            ),
                            makeTryFinallyStatement(
                                provider=provider,
                                tried=(
                                    makeStatementAssignmentVariable(
                                        variable=tmp_variable,
                                        source=makeExpressionOperationBinaryInplace(
                                            left=ExpressionTempVariableRef(
                                                variable=tmp_variable,
                                                source_ref=node.source_ref,
                                            ),
                                            right=node.subnode_source.subnode_right,
                                            operator=node.subnode_source.getOperator(),
                                            source_ref=node.source_ref,
                                        ),
                                        source_ref=node.source_ref,
                                    ),
                                    StatementLocalsDictOperationSet(
                                        locals_scope=provider.getLocalsScope(),
                                        variable_name=variable_name,
                                        value=ExpressionTempVariableRef(
                                            variable=tmp_variable,
                                            source_ref=node.source_ref,
                                        ),
                                        source_ref=node.source_ref,
                                    ),
                                ),
                                final=makeStatementReleaseVariable(
                                    variable=tmp_variable, source_ref=node.source_ref
                                ),
                                source_ref=node.source_ref,
                            ),
                        )
                    )

                    node.parent.replaceStatement(node, statements)

                else:
                    new_node = StatementLocalsDictOperationSet(
                        locals_scope=provider.getLocalsScope(),
                        variable_name=variable_name,
                        value=node.subnode_source,
                        source_ref=node.source_ref,
                    )

                    node.parent.replaceChild(node, new_node)
            else:
                variable = provider.getVariableForAssignment(
                    variable_name=variable_name
                )

                new_node = makeStatementAssignmentVariable(
                    variable=variable,
                    source=node.subnode_source,
                    source_ref=node.source_ref,
                )

                variable.addVariableUser(provider)

                node.parent.replaceChild(node, new_node)

            del node.parent
            del node.provider
        elif node.isStatementDelVariableName():
            variable_name = node.getVariableName()

            provider = node.provider

            if self._shouldUseLocalsDict(provider, variable_name):
                # Classes always assign to locals dictionary except for closure
                # variables taken.
                new_node = StatementLocalsDictOperationDel(
                    locals_scope=provider.getLocalsScope(),
                    variable_name=variable_name,
                    tolerant=node.tolerant,
                    source_ref=node.source_ref,
                )
            else:
                variable = provider.getVariableForAssignment(
                    variable_name=variable_name
                )

                new_node = makeStatementDelVariable(
                    variable=variable,
                    tolerant=node.tolerant,
                    source_ref=node.source_ref,
                )

                variable.addVariableUser(provider)

            parent = node.parent
            node.finalize()

            parent.replaceChild(node, new_node)

    def onEnterNode(self, node):
        # Mighty complex code with lots of branches, but we aim to get rid of it.
        # pylint: disable=too-many-branches

        if node.isExpressionVariableNameRef():
            provider = node.provider

            if provider.isExpressionClassBody():
                if node.needsFallback():
                    variable = provider.getVariableForReference(
                        variable_name=node.getVariableName()
                    )

                    new_node = ExpressionLocalsVariableRefOrFallback(
                        locals_scope=provider.getLocalsScope(),
                        variable_name=node.getVariableName(),
                        fallback=makeExpressionVariableRef(
                            variable=variable,
                            locals_scope=provider.getLocalsScope(),
                            source_ref=node.source_ref,
                        ),
                        source_ref=node.source_ref,
                    )

                    variable.addVariableUser(provider)
                else:
                    new_node = ExpressionLocalsVariableRef(
                        locals_scope=provider.getLocalsScope(),
                        variable_name=node.getVariableName(),
                        source_ref=node.source_ref,
                    )

                parent = node.parent
                node.finalize()

                parent.replaceChild(node, new_node)
        elif node.isExpressionTempVariableRef():
            if node.getVariable().getOwner() != node.getParentVariableProvider():
                node.getParentVariableProvider().addClosureVariable(node.getVariable())
        elif node.isExpressionGeneratorObjectBody():
            if python_version >= 0x300:
                self._handleNonLocal(node)

            # Only Python3.4 or later allows for generators to have qualname.
            if python_version >= 0x340:
                self._handleQualnameSetup(node)
        elif node.isExpressionCoroutineObjectBody():
            self._handleNonLocal(node)

            self._handleQualnameSetup(node)
        elif node.isExpressionAsyncgenObjectBody():
            self._handleNonLocal(node)

            self._handleQualnameSetup(node)
        elif node.isExpressionClassBody():
            if python_version >= 0x300:
                self._handleNonLocal(node)

            # Python3.4 allows for class declarations to be made global, even
            # after they were declared, so we need to fix this up.
            if python_version >= 0x340:
                self._handleQualnameSetup(node)
        elif node.isExpressionFunctionBody():
            if python_version >= 0x300:
                self._handleNonLocal(node)

            # Python 3.4 allows for class declarations to be made global, even
            # after they were declared, so we need to fix this up.
            if python_version >= 0x340:
                self._handleQualnameSetup(node)
        # Check if continue and break are properly in loops. If not, raise a
        # syntax error.
        elif node.isStatementLoopBreak() or node.isStatementLoopContinue():
            current = node

            while True:
                current = current.getParent()

                if current.isStatementLoop():
                    break

                if current.isParentVariableProvider():
                    if node.isStatementLoopContinue():
                        message = "'continue' not properly in loop"
                    else:
                        message = "'break' outside loop"

                    raiseSyntaxError(message, node.getSourceReference())


class VariableClosureLookupVisitorPhase2(VisitorNoopMixin):
    """Variable closure phase 2: Find assignments and references.

    In class context, a reference to a variable must be obeyed immediately,
    so that "variable = variable" takes first "variable" as a closure and
    then adds a new local "variable" to override it from there on.

    So, assignments for early closure, accesses will already have a
    variable set now, the others, only in this phase.
    """

    @staticmethod
    def _attachVariable(node, provider):
        # print "Late reference", node.getVariableName(), "for", provider, "caused at", node, "of", node.getParent()

        variable_name = node.getVariableName()

        variable = provider.getVariableForReference(variable_name=variable_name)

        # Need to catch functions with "exec" and closure variables not allowed.
        if python_version < 0x300 and provider.isExpressionFunctionBodyBase():
            was_taken = provider.hasTakenVariable(variable_name)

            if not was_taken and variable.getOwner() is not provider:
                parent_provider = provider.getParentVariableProvider()

                while parent_provider.isExpressionClassBody():
                    parent_provider = parent_provider.getParentVariableProvider()

                if (
                    parent_provider.isExpressionFunctionBody()
                    and parent_provider.isUnqualifiedExec()
                ):
                    raiseSyntaxError(
                        getErrorMessageExecWithNestedFunction()
                        % parent_provider.getName(),
                        node.getSourceReference(),
                        display_line=False,  # Wrong line anyway
                    )

        return variable

    def onEnterNode(self, node):
        if node.isExpressionVariableNameRef():
            provider = node.provider

            try:
                variable = self._attachVariable(node, provider)
            except MaybeLocalVariableUsage:
                variable_name = node.getVariableName()

                new_node = ExpressionLocalsVariableRefOrFallback(
                    locals_scope=provider.getLocalsScope(),
                    variable_name=variable_name,
                    fallback=makeExpressionVariableRef(
                        variable=node.getParentModule().getVariableForReference(
                            variable_name
                        ),
                        locals_scope=provider.getLocalsScope(),
                        source_ref=node.source_ref,
                    ),
                    source_ref=node.source_ref,
                )
            else:
                new_node = makeExpressionVariableRef(
                    variable=variable,
                    locals_scope=provider.getLocalsScope(),
                    source_ref=node.source_ref,
                )

                variable.addVariableUser(provider)

            parent = node.parent
            node.finalize()

            parent.replaceChild(node, new_node)


class VariableClosureLookupVisitorPhase3(VisitorNoopMixin):
    """Variable closure phase 3: Find errors and complete frame variables.

    In this phase, we can do some fix-ups and find errors. We might e.g.
    detect that a "del" was executed on a shared variable, which is not
    allowed for Python 2.x, so it must be caught. The parsing wouldn't do
    that.

    Also, frame objects for functions should learn their variable names.
    """

    def onEnterNode(self, node):
        if python_version < 0x300 and node.isStatementDelVariable():
            variable = node.getVariable()

            if not variable.isModuleVariable() and isSharedAmongScopes(variable):
                raiseSyntaxError(
                    """\
can not delete variable '%s' referenced in nested scope"""
                    % (variable.getName()),
                    node.getSourceReference(),
                )
        elif node.isStatementsFrame():
            node.updateLocalNames()
        elif node.isExpressionFunctionBodyBase():
            addFunctionVariableReleases(node)

            # Python3 is influenced by the mere use of a variable named as
            # "super". So we need to prepare ability to take closure.
            if node.hasFlag("has_super"):
                if not node.hasVariableName("__class__"):
                    class_var = node.takeVariableForClosure("__class__")
                    class_var.addVariableUser(node)

                    node.getLocalsScope().registerClosureVariable(class_var)
                    while node != class_var.getOwner():
                        node = node.getParentVariableProvider()
                        node.getLocalsScope().registerClosureVariable(class_var)


def completeVariableClosures(tree):
    visitors = (
        VariableClosureLookupVisitorPhase1(),
        VariableClosureLookupVisitorPhase2(),
        VariableClosureLookupVisitorPhase3(),
    )

    for visitor in visitors:
        visitTree(tree, visitor)

    # Only used to detect syntax errors.
    releaseSharedScopeInformation(tree)
