#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import PythonVersions, SyntaxErrors, Variables
from nuitka.nodes.NodeMakingHelpers import makeConstantReplacementNode
from nuitka.nodes.ReturnNodes import StatementGeneratorReturn
from nuitka.Options import isFullCompat
from nuitka.Utils import python_version
from nuitka.VariableRegistry import addVariableUsage, isSharedLogically

from .Operations import VisitorNoopMixin, visitTree
from .ReformulationFunctionStatements import addFunctionVariableReleases


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

        for non_local_names, source_ref in node.getNonlocalDeclarations():
            for non_local_name in non_local_names:
                variable = node.getClosureVariable(
                    variable_name = non_local_name
                )

                node.registerProvidedVariable(variable)

                if variable.isModuleVariable():
                    SyntaxErrors.raiseSyntaxError(
                        "no binding for nonlocal '%s' found" % (
                            non_local_name
                        ),
                        source_ref   = None
                                         if isFullCompat() and \
                                         python_version < 340 else
                                       source_ref,
                        display_file = not isFullCompat() or \
                                       python_version >= 340,
                        display_line = not isFullCompat() or \
                                       python_version >= 340
                    )

    @staticmethod
    def _handleQualnameSetup(node):
        if node.qualname_setup is not None:
            if node.isClassDictCreation():
                class_assign, qualname_assign = node.qualname_setup
                class_variable = class_assign.getTargetVariableRef().getVariable()

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
                function_variable_ref = node.qualname_setup
                function_variable = function_variable_ref.getVariable()

                if function_variable.isModuleVariable():
                    node.qualname_provider = node.getParentModule()

            # TODO: Actually for nested global classes, this approach
            # may not work, as their "qualname" will be wrong. In that
            # case a dedicated node for "qualname" references might be
            # needed.

            node.qualname_setup = None

    def onEnterNode(self, node):
        # Mighty complex code with lots of branches and statements, but it
        # couldn't be less without making it more difficult.
        # pylint: disable=R0912,R0915

        if node.isExpressionTargetVariableRef():
            provider = node.getParentVariableProvider()

            if node.getVariable() is None:
                variable_name = node.getVariableName()

                variable = provider.getVariableForAssignment(
                    variable_name = variable_name
                )

                node.setVariable(variable)

            addVariableUsage(node.getVariable(), provider)
        elif node.isExpressionTargetTempVariableRef():
            provider = node.getParentVariableProvider()

            addVariableUsage(node.getVariable(), provider)
        elif node.isExpressionVariableRef():
            if node.getVariable() is None:
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
                    if variable.getOwner() is not provider:
                        if python_version >= 340 or \
                           (python_version >= 300 and \
                            variable.isModuleVariable()):
                            variable = Variables.MaybeLocalVariable(
                                owner          = provider,
                                maybe_variable = variable
                            )

                    node.setVariable(variable)
        elif node.isExpressionTempVariableRef():
            if node.getVariable().getOwner() != node.getParentVariableProvider():
                node.setVariable(
                    node.getParentVariableProvider().addClosureVariable(
                        node.getVariable()
                    )
                )
        elif node.isExpressionFunctionBody():
            if python_version >= 300:
                self._handleNonLocal(node)

            for variable in node.getParameters().getAllVariables():
                addVariableUsage(variable, node)

            # Python3.4 allows for class declarations to be made global, even
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

                    if current.isPythonModule():
                        break

                    assert current.isExpressionFunctionBody()

                    if current.isClassDictCreation():
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
        elif node.isStatementBreakLoop() or node.isStatementContinueLoop():
            current = node

            while True:
                if current.isPythonModule() or \
                   current.isExpressionFunctionBody():
                    if node.isStatementContinueLoop():
                        message = "'continue' not properly in loop"
                        col_offset   = 16 if python_version >= 300 else None
                        display_line = True
                        source_line  = None
                    else:
                        message = "'break' outside loop"

                        if isFullCompat():
                            col_offset   = 2 if python_version >= 300 else None
                            display_line = True
                            source_line  = "" if python_version >= 300 else None
                        else:
                            col_offset   = 13
                            display_line = True
                            source_line  = None

                    SyntaxErrors.raiseSyntaxError(
                        message,
                        source_ref   = node.getSourceReference(),
                        col_offset   = col_offset,
                        display_line = display_line,
                        source_line  = source_line
                    )

                current = current.getParent()

                if current.isStatementLoop():
                    break

    def onLeaveNode(self, node):
        # Return statements in generators are not really that, instead they are
        # exception raises, fix that up now. Doing it right from the onset,
        # would be a bit more difficult, as the knowledge that something is a
        # generator, requires a second pass.
        if node.isStatementReturn() and \
           node.getParentVariableProvider().isGenerator():
            return_value = node.getExpression()

            if python_version < 330:
                if not return_value.isExpressionConstantRef() or \
                   return_value.getConstant() is not None:
                    SyntaxErrors.raiseSyntaxError(
                        "'return' with argument inside generator",
                        source_ref = node.getSourceReference(),
                    )

            node.replaceWith(
                StatementGeneratorReturn(
                    expression = return_value,
                    source_ref = node.getSourceReference()
                )
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

        node.setVariable(
            variable
        )

        # Need to catch functions with "exec" and closure variables not allowed.
        if python_version < 300 and \
           not was_taken and \
           provider.isExpressionFunctionBody() and \
           variable.getOwner() is not provider:
            parent_provider = provider.getParentVariableProvider()

            while parent_provider.isExpressionFunctionBody() and \
                  parent_provider.isClassDictCreation():
                parent_provider = parent_provider.getParentVariableProvider()

            if parent_provider.isExpressionFunctionBody() and \
               parent_provider.isUnqualifiedExec():
                SyntaxErrors.raiseSyntaxError(
                    reason       = PythonVersions.\
                                     getErrorMessageExecWithNestedFunction() % \
                                     parent_provider.getName(),
                    source_ref   = parent_provider.getExecSourceRef(),
                    col_offset   = None,
                    display_file = True,
                    display_line = True,
                    source_line  = None
                )


    def onEnterNode(self, node):
        if node.isExpressionVariableRef():
            provider = node.getParentVariableProvider()

            if node.getVariable() is None:
                self._attachVariable(node, provider)

            addVariableUsage(node.getVariable(), provider)
        elif node.isExpressionTempVariableRef():
            provider = node.getParentVariableProvider()

            addVariableUsage(node.getVariable(), provider)


    # For Python3, every function in a class is supposed to take "__class__" as
    # a reference, so make sure that happens.
    if python_version >= 300:
        def onLeaveNode(self, node):
            if node.isExpressionFunctionBody() and node.isClassClosureTaker():
                if python_version < 340 or True: # TODO: Temporarily reverted:
                    node.getVariableForReference(
                        variable_name = "__class__"
                    )
                else:
                    parent_provider = node.getParentVariableProvider()

                    variable = parent_provider.getTempVariable(
                        temp_scope = None,
                        name       = "__class__"
                    )

                    node.addClosureVariable(variable)


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
            variable = node.getTargetVariableRef().getVariable()

            if not variable.isModuleVariable() and \
               isSharedLogically(variable):
                SyntaxErrors.raiseSyntaxError(
                    reason       = """\
can not delete variable '%s' referenced in nested scope""" % (
                       variable.getName()
                    ),
                    source_ref   = (
                        None if isFullCompat() else node.getSourceReference()
                    ),
                    display_file = not isFullCompat(),
                    display_line = not isFullCompat()
                )
        elif node.isStatementsFrame():
            node.updateVarNames()


def completeVariableClosures(tree):
    visitors = (
        VariableClosureLookupVisitorPhase1(),
        VariableClosureLookupVisitorPhase2(),
        VariableClosureLookupVisitorPhase3()
    )

    for visitor in visitors:
        visitTree(tree, visitor)

        if tree.isPythonModule():
            for function in tree.getFunctions():
                visitTree(function, visitor)

    if tree.isPythonModule():
        for function in tree.getFunctions():
            addFunctionVariableReleases(function)
    else:
        # For "eval" code, this will need to be done differently, not done
        # yet-
        assert False
