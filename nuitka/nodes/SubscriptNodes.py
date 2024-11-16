#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Subscript node.

Subscripts are important when working with lists and dictionaries. Tracking
them can allow to achieve more compact code, or predict results at compile time.

There is be a method "computeExpressionSubscript" to aid predicting them in the
other nodes.
"""

from nuitka.PythonVersions import python_version

from .ChildrenHavingMixins import ChildrenHavingExpressionSubscriptMixin
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import ExpressionBoolShapeExactMixin
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import (
    makeRaiseExceptionExpressionFromTemplate,
    wrapExpressionWithNodeSideEffects,
)
from .StatementBasesGenerated import (
    StatementAssignmentSubscriptBase,
    StatementDelSubscriptBase,
)


class StatementAssignmentSubscript(StatementAssignmentSubscriptBase):
    kind = "STATEMENT_ASSIGNMENT_SUBSCRIPT"

    named_children = ("source", "subscribed", "subscript")
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        return self.subnode_subscribed.computeExpressionSetSubscript(
            set_node=self,
            subscript=self.subnode_subscript,
            value_node=self.subnode_source,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getStatementNiceName():
        return "subscript assignment statement"


class StatementDelSubscript(StatementDelSubscriptBase):
    kind = "STATEMENT_DEL_SUBSCRIPT"

    named_children = ("subscribed", "subscript")
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        return self.subnode_subscribed.computeExpressionDelSubscript(
            del_node=self,
            subscript=self.subnode_subscript,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getStatementNiceName():
        return "subscript del statement"


class ExpressionSubscriptLookup(ChildrenHavingExpressionSubscriptMixin, ExpressionBase):
    kind = "EXPRESSION_SUBSCRIPT_LOOKUP"

    named_children = ("expression", "subscript")

    def __init__(self, expression, subscript, source_ref):
        ChildrenHavingExpressionSubscriptMixin.__init__(
            self,
            expression=expression,
            subscript=subscript,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        return self.subnode_expression.computeExpressionSubscript(
            lookup_node=self,
            subscript=self.subnode_subscript,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isKnownToBeIterable(count):
        return None


def makeExpressionSubscriptLookup(expression, subscript, source_ref):
    return ExpressionSubscriptLookup(
        expression=expression, subscript=subscript, source_ref=source_ref
    )


def makeExpressionIndexLookup(expression, index_value, source_ref):
    # TODO: Specialize index lookups to actual specific node.
    return makeExpressionSubscriptLookup(
        expression=expression,
        subscript=makeConstantRefNode(
            constant=index_value, source_ref=source_ref, user_provided=True
        ),
        source_ref=source_ref,
    )


def hasSubscript(value, subscript):
    """Check if a value has a subscript."""

    try:
        value[subscript]
    except Exception:  # Catch all the things, pylint: disable=broad-except
        return False
    else:
        return True


class ExpressionMatchSubscriptCheck(
    ExpressionBoolShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ChildrenHavingExpressionSubscriptMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_MATCH_SUBSCRIPT_CHECK"

    named_children = ("expression", "subscript")

    def __init__(self, expression, subscript, source_ref):
        ChildrenHavingExpressionSubscriptMixin.__init__(
            self,
            expression=expression,
            subscript=subscript,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # We do at least for compile time constants optimization here, but more
        # could be done, were we to consider shapes.
        source = self.subnode_expression
        subscript = self.subnode_subscript

        if source.isCompileTimeConstant() and subscript.isCompileTimeConstant():
            (
                result,
                tags,
                change_desc,
            ) = trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: hasSubscript(
                    source.getCompileTimeConstant(), subscript.getCompileTimeConstant()
                ),
                description="Subscript match check has been pre-computed.",
            )

            # If source has side effects, they must be evaluated.
            result = wrapExpressionWithNodeSideEffects(new_node=result, old_node=source)

            return result, tags, change_desc

        if subscript.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_subscript.mayRaiseException(exception_type)


class ExpressionSubscriptLookupForUnpack(ExpressionSubscriptLookup):
    kind = "EXPRESSION_SUBSCRIPT_LOOKUP_FOR_UNPACK"

    # TODO: Older Python doesn't need the slot.
    __slots__ = ("expected",)

    def __init__(self, expression, subscript, expected, source_ref):
        ExpressionSubscriptLookup.__init__(
            self, expression=expression, subscript=subscript, source_ref=source_ref
        )

        self.expected = expected

    def computeExpression(self, trace_collection):
        result = self.subnode_expression.computeExpressionSubscript(
            lookup_node=self,
            subscript=self.subnode_subscript,
            trace_collection=trace_collection,
        )

        result_node = result[0]

        # Rewrite exceptions to correct message.
        if (
            result_node.isExpressionRaiseException()
            and result_node.subnode_exception_type.isExpressionBuiltinMakeException()
            and result_node.subnode_exception_type.getExceptionName() == "IndexError"
        ):
            if python_version >= 0x360:
                return (
                    makeRaiseExceptionExpressionFromTemplate(
                        exception_type="ValueError",
                        template="not enough values to unpack (expected %d, got %d)",
                        template_args=(
                            makeConstantRefNode(
                                constant=self.expected, source_ref=self.source_ref
                            ),
                            self.subnode_subscript,
                        ),
                        source_ref=self.source_ref,
                    ),
                    "new_raise",
                    "Raising for unpack too short iterator.",
                )
            else:
                return (
                    makeRaiseExceptionExpressionFromTemplate(
                        exception_type="ValueError",
                        template="need more than %d value to unpack",
                        template_args=self.subnode_subscript,
                        source_ref=self.source_ref,
                    ),
                    "new_raise",
                    "Raising for unpack too short iterator.",
                )

        return result


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
