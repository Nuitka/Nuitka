#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
)
from nuitka.nodes.FunctionNodes import MaybeLocalVariableUsage
from nuitka.nodes.NodeMakingHelpers import makeConstantReplacementNode
from nuitka.nodes.VariableRefNodes import (
    ExpressionLocalsVariableRef,
    ExpressionVariableRef
)
from nuitka.PythonVersions import (
    getErrorMessageExecWithNestedFunction,
    python_version
)

from .Operations import VisitorNoopMixin, visitTree
from .ReformulationFunctionStatements import addFunctionVariableReleases
from .SyntaxErrors import raiseSyntaxError

# Note: We do the variable scope assignment, as an extra step from tree
# building, because tree building creates the tree without any consideration of
# evaluation order. And the ordered way these visitors are entered, will ensure
# this order.

# The main complexity is that there are two ways of visiting. One where variable
# lookups are to be done immediately, and one where it is delayed. This is
# basically class vs. function scope handling.

class VariableClosureLookupVisitorPhase1(VisitorNoopMixin):
    """ Variable closure phase 1: Find assignments and early closure references.

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

        for non_local_names, source_ref in node.consumeNonlocalDeclarations():
            for non_local_name in non_local_names:

                variable = node.takeVariableForClosure(
                    variable_name = non_local_name
                )

                node.registerProvidedVariable(variable)

                if variable.isModuleVariable():
                    raiseSyntaxError(
                        "no binding for nonlocal '%s' found" % (
                            non_local_name
                        ),
                        source_ref
                    )


                variable.addVariableUser(node)

    @staticmethod
    def _handleQualnameSetup(node):
        if node.qualname_setup is not None:
            if node.isExpressionClassBody():
                class_variable_name, qualname_assign = node.qualname_setup

                class_variable = node.getParentVariableProvider().getVariableForAssignment(
                    class_variable_name
                )

                if class_variable.isModuleVariable():
                    qualname_node = qualname_assign.getAssignSource()

                    qualname_node.replaceWith(
                        makeConstantReplacementNode(
                            constant = class_variable.getName(),
                            node     = qualname_node
                        )
                    )

                    node.qualname_provider = node.getParentModule()
            else:
                function_variable = node.getParentVariableProvider().getVariableForAssignment(
                    node.qualname_setup
                )

                if function_variable.isModuleVariable():
                    node.qualname_provider = node.getParentModule()

            # TODO: Actually for nested global classes, this approach
            # may not work, as their "qualname" will be wrong. In that
            # case a dedicated node for "qualname" references might be
            # needed.

            node.qualname_setup = None

    def onLeaveNode(self, node):
        if node.isStatementAssignmentVariableName():
            provider = node.getParentVariableProvider()

            variable = provider.getVariableForAssignment(
                variable_name = node.getVariableName()
            )

            node.replaceWith(
                StatementAssignmentVariable(
                    variable   = variable,
                    source     = node.subnode_source,
                    source_ref = node.source_ref
                )
            )

            variable.addVariableUser(provider)
        elif node.isStatementDelVariableName():
            provider = node.getParentVariableProvider()

            variable = provider.getVariableForAssignment(
                variable_name = node.getVariableName()
            )

            node.replaceWith(
                StatementDelVariable(
                    variable   = variable,
                    tolerant   = node.tolerant,
                    source_ref = node.source_ref
                )
            )

            variable.addVariableUser(provider)

    def onEnterNode(self, node):
        # Mighty complex code with lots of branches and statements, but it
        # couldn't be less without making it more difficult.
        # pylint: disable=too-many-branches,too-many-statements

        if node.isExpressionVariableNameRef():
            provider = node.getParentVariableProvider()

            if provider.isEarlyClosure():
                variable = provider.getVariableForReference(
                    variable_name = node.getVariableName()
                )

                # Python3.4 version respects closure variables taken can be
                # overridden by writes to locals. It should be done for
                # globals too, on all versions, but for Python2 the locals
                # dictionary is avoided unless "exec" appears, so it's not
                # done.
                owner = variable.getOwner()
                user = provider

                while user is not owner:
                    if user.isExpressionFunctionBody() or \
                       user.isExpressionClassBody():
                        break

                    user = user.getParentVariableProvider()

                if owner is not user:
                    if python_version >= 340 or \
                       (python_version >= 300 and \
                        variable.isModuleVariable()):

                        node.replaceWith(
                            ExpressionLocalsVariableRef(
                                variable_name     = node.getVariableName(),
                                fallback_variable = variable,
                                source_ref        = node.getSourceReference()
                            )
                        )

                    else:
                        node.replaceWith(
                            ExpressionVariableRef(
                                variable   = variable,
                                source_ref = node.source_ref
                            )
                        )
                else:
                    node.replaceWith(
                        ExpressionVariableRef(
                            variable   = variable,
                            source_ref = node.source_ref
                        )
                    )

                variable.addVariableUser(provider)
        elif node.isExpressionTempVariableRef():
            if node.getVariable().getOwner() != node.getParentVariableProvider():
                node.getParentVariableProvider().addClosureVariable(
                    node.getVariable()
                )
        elif node.isExpressionGeneratorObjectBody():
            self._handleNonLocal(node)

            # Only Python3.4 or later allows for generators to have qualname.
            if python_version >= 340:
                self._handleQualnameSetup(node)
        elif node.isExpressionCoroutineObjectBody():
            self._handleNonLocal(node)

            self._handleQualnameSetup(node)
        elif node.isExpressionAsyncgenObjectBody():
            self._handleNonLocal(node)

            self._handleQualnameSetup(node)
        elif node.isExpressionClassBody():
            self._handleNonLocal(node)

            # Python3.4 allows for class declarations to be made global, even
            # after they were declared, so we need to fix this up.
            if python_version >= 340:
                self._handleQualnameSetup(node)
        elif node.isExpressionFunctionBody():
            self._handleNonLocal(node)

            # Python 3.4 allows for class declarations to be made global, even
            # after they were declared, so we need to fix this up.
            if python_version >= 340:
                self._handleQualnameSetup(node)
        # Attribute access of names of class functions should be mangled, if
        # they start with "__", but do not end in "__" as well.
        elif node.isExpressionAttributeLookup() or \
             node.isStatementAssignmentAttribute() or \
             node.isStatementDelAttribute():
            attribute_name = node.getAttributeName()

            if attribute_name.startswith("__") and \
               not attribute_name.endswith("__"):
                seen_function = False

                current = node

                while True:
                    current = current.getParentVariableProvider()

                    if current.isCompiledPythonModule():
                        break

                    if current.isExpressionClassBody():
                        if seen_function:
                            node.setAttributeName(
                                "_%s%s" % (
                                    current.getName().lstrip('_'),
                                    attribute_name
                                )
                            )

                        break
                    else:
                        seen_function = True
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

                    raiseSyntaxError(
                        message,
                        node.getSourceReference(),
                    )


class VariableClosureLookupVisitorPhase2(VisitorNoopMixin):
    """ Variable closure phase 2: Find assignments and references.

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

        was_taken = provider.hasTakenVariable(variable_name)

        variable = provider.getVariableForReference(
            variable_name = variable_name
        )

        # Need to catch functions with "exec" and closure variables not allowed.
        if python_version < 300 and \
           not was_taken and \
           provider.isExpressionFunctionBodyBase() and \
           variable.getOwner() is not provider:
            parent_provider = provider.getParentVariableProvider()

            while parent_provider.isExpressionClassBody():
                parent_provider = parent_provider.getParentVariableProvider()

            if parent_provider.isExpressionFunctionBody() and \
               parent_provider.isUnqualifiedExec():
                raiseSyntaxError(
                    getErrorMessageExecWithNestedFunction() % parent_provider.getName(),
                    node.getSourceReference(),
                    display_line = False # Wrong line anyway
                )

        return variable

    def onEnterNode(self, node):
        if node.isExpressionVariableNameRef():
            provider = node.getParentVariableProvider()

            try:
                variable = self._attachVariable(node, provider)
            except MaybeLocalVariableUsage:
                variable_name = node.getVariableName()

                node.replaceWith(
                    ExpressionLocalsVariableRef(
                        variable_name     = variable_name,
                        fallback_variable = node.getParentModule().getVariableForReference(variable_name),
                        source_ref        = node.getSourceReference()
                    )
                )
            else:
                node.replaceWith(
                    ExpressionVariableRef(
                        variable   = variable,
                        source_ref = node.source_ref
                    )
                )

                variable.addVariableUser(provider)

        elif node.isExpressionVariableRef():
            provider = node.getParentVariableProvider()

            variable = node.getVariable()

            if variable is None:
                try:
                    variable = self._attachVariable(node, provider)
                except MaybeLocalVariableUsage:
                    variable_name = node.getVariableName()

                    node.replaceWith(
                        ExpressionLocalsVariableRef(
                            variable_name     = variable_name,
                            fallback_variable = node.getParentModule().getVariableForReference(variable_name),
                            source_ref        = node.getSourceReference()
                        )
                    )
                else:
                    node.setVariable(
                        variable
                    )

                    variable.addVariableUser(provider)
            else:
                variable.addVariableUser(provider)


class VariableClosureLookupVisitorPhase3(VisitorNoopMixin):
    """ Variable closure phase 3: Find errors and complete frame variables.

        In this phase, we can do some fix-ups and find errors. We might e.g.
        detect that a "del" was executed on a shared variable, which is not
        allowed for Python 2.x, so it must be caught. The parsing wouldn't do
        that.

        Also, frame objects for functions should learn their variable names.
    """

    def onEnterNode(self, node):
        if python_version < 300 and node.isStatementDelVariable():
            variable = node.getVariable()

            if not variable.isModuleVariable() and \
               variable.isSharedAmongScopes():
                raiseSyntaxError(
                    """\
can not delete variable '%s' referenced in nested scope""" % (
                       variable.getName()
                    ),
                    node.getSourceReference()
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

                    node.registerProvidedVariable(class_var)
                    while node != class_var.getOwner():
                        node = node.getParentVariableProvider()
                        node.registerProvidedVariable(class_var)


def completeVariableClosures(tree):
    visitors = (
        VariableClosureLookupVisitorPhase1(),
        VariableClosureLookupVisitorPhase2(),
        VariableClosureLookupVisitorPhase3()
    )

    for visitor in visitors:
        visitTree(tree, visitor)
