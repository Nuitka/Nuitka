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
""" Propagate exception raising upwards, maintaining side effects, and removing useless try constructs.

"""

from .OptimizeBase import OptimizationVisitorBase

from ..TreeOperations import RestartVisit

from nuitka.nodes.SideEffectNode import CPythonExpressionSideEffects

from nuitka.nodes.ExceptionNodes import CPythonStatementRaiseException

from nuitka.nodes.StatementNodes import CPythonStatementExpressionOnly

from nuitka.nodes.NodeMakingHelpers import makeStatementsSequenceReplacementNode


class OptimizeRaisesVisitor( OptimizationVisitorBase ):
    def onEnterNode( self, node ):
        if node.isExpressionRaiseException():
            while node.parent.isExpressionSideEffects():
                node = node.parent

            if node.parent.isOperation():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isExpressionCallComplex():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isExpressionCallSimple():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isExpressionCall():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isStatementExpressionOnly():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isStatementRaiseException():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isStatementReturn():
                self.trimEvaluation(
                    node = node.parent
                )

    def trimEvaluation( self, node ):
        old_children = node.getVisitableNodes()
        new_children = []

        for child in old_children:
            new_children.append( child )

            if child.isExpressionRaiseException() or (
                child.isExpressionSideEffects() and \
                child.getExpression().isExpressionRaiseException() ):
                break
        else:
            assert False

        side_effects = [
            new_child
            for new_child in
            new_children[:-1]
            if new_child.mayHaveSideEffects( None )
        ]

        raise_exception = new_children[-1]

        if raise_exception.isExpressionSideEffects():
            side_effects.extend( raise_exception.getSideEffects() )
            raise_exception = raise_exception.getExpression()

        if node.isExpression():
            if side_effects:
                node.replaceWith(
                    new_node = CPythonExpressionSideEffects(
                        side_effects = side_effects,
                        expression   = raise_exception,
                        source_ref   = raise_exception.getSourceReference()
                    )
                )

                message = "Detected expression exception was propagated to expression upwards while maintaining side effects." # pylint: disable=C0301
            else:
                node.replaceWith(
                    new_node = raise_exception
                )

                message = "Detected expression exception was propagated to expression upwards."

            self.signalChange(
                "new_raise",
                node.getSourceReference(),
                message
            )

            raise RestartVisit
        elif node.isStatement():
            raise_node = CPythonStatementRaiseException(
                exception_type  = raise_exception.getExceptionType(),
                exception_value = raise_exception.getExceptionValue(),
                exception_trace = None,
                exception_cause = None,
                source_ref      = raise_exception.getSourceReference()
            )

            if side_effects:
                side_effects = tuple(
                    CPythonStatementExpressionOnly(
                        expression = side_effect,
                        source_ref = side_effect.getSourceReference()
                    )
                    for side_effect in side_effects
                )

                node.replaceWith(
                    makeStatementsSequenceReplacementNode(
                        statements = side_effects + ( raise_node, ),
                        node       = node
                    )
                )
            else:
                node.replaceWith(
                    new_node = raise_node
                )

            self.signalChange(
                "new_raise new_statements",
                node.getSourceReference(),
                "Detected expression exception was converted to raise exception statement."
            )

            raise RestartVisit
        else:
            assert False

    # TODO: Make use of this.
    @staticmethod
    def matchesException( catched_exceptions, raised_exception ):
        if catched_exceptions is None:
            return True

        # TODO: Why can raised_exception be None at all?
        if raised_exception is not None:
            for catched_exception in catched_exceptions:
                # Both are builtin exception references of the same name
                if catched_exception.isExpressionBuiltinExceptionRef() and \
                   raised_exception.isExpressionBuiltinExceptionRef():
                    # TODO: Could check run time objects from builtins for subclass relationship
                    if catched_exception.getExceptionName() == raised_exception.getExceptionName():
                        return True

                # Catched in builtin exception reference, and raised is an builtin one too.
                if catched_exception.isExpressionBuiltinExceptionRef() and \
                     raised_exception.isExpressionBuiltinMakeException():
                    # TODO: Could check run time objects from builtins for subclass relationship
                    if catched_exception.getExceptionName() == raised_exception.getExceptionName():
                        return True



        return None
