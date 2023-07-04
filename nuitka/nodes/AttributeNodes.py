#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Attribute nodes

Knowing attributes of an object is very important, esp. when it comes to 'self'
and objects and classes.

There will be a methods "computeExpression*Attribute" to aid predicting them,
with many variants for setting, deleting, and accessing. Also there is some
complication in the form of special lookups, that won't go through the normal
path, but just check slots.

Due to ``getattr`` and ``setattr`` built-ins, there is also a different in the
computations for objects and for compile time known strings. This reflects what
CPython also does with "tp_getattr" and "tp_getattro".

These nodes are therefore mostly delegating the work to expressions they
work on, and let them decide and do the heavy lifting of optimization
and annotation is happening in the nodes that implement these compute slots.
"""

from nuitka.__past__ import unicode

from .AttributeLookupNodes import ExpressionAttributeLookup
from .ChildrenHavingMixins import (
    ChildHavingExpressionMixin,
    ChildrenExpressionBuiltinGetattrMixin,
    ChildrenExpressionBuiltinSetattrMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionBasesGenerated import ExpressionBuiltinHasattrBase
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionNoneShapeExactMixin,
)
from .NodeMakingHelpers import (
    makeCompileTimeConstantReplacementNode,
    makeRaiseExceptionReplacementExpression,
    wrapExpressionWithNodeSideEffects,
)
from .StatementBasesGenerated import (
    StatementAssignmentAttributeBase,
    StatementDelAttributeBase,
)


class StatementAssignmentAttribute(StatementAssignmentAttributeBase):
    """Assignment to an attribute.

    Typically from code like: source.attribute_name = expression

    Both source and expression may be complex expressions, the source
    is evaluated first. Assigning to an attribute has its on slot on
    the source, which gets to decide if it knows it will work or not,
    and what value it will be.
    """

    kind = "STATEMENT_ASSIGNMENT_ATTRIBUTE"

    named_children = ("source", "expression")
    node_attributes = ("attribute_name",)

    def getAttributeName(self):
        return self.attribute_name

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.subnode_expression.computeExpressionSetAttribute(
            set_node=self,
            attribute_name=self.attribute_name,
            value_node=self.subnode_source,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getStatementNiceName():
        return "attribute assignment statement"


class StatementDelAttribute(StatementDelAttributeBase):
    """Deletion of an attribute.

    Typically from code like: del source.attribute_name

    The source may be complex expression. Deleting an attribute has its on
    slot on the source, which gets to decide if it knows it will work or
    not, and what value it will be.
    """

    kind = "STATEMENT_DEL_ATTRIBUTE"

    named_children = ("expression",)
    node_attributes = ("attribute_name",)

    def getAttributeName(self):
        return self.attribute_name

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.subnode_expression.computeExpressionDelAttribute(
            set_node=self,
            attribute_name=self.attribute_name,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getStatementNiceName():
        return "attribute del statement"


def makeExpressionAttributeLookup(expression, attribute_name, source_ref):
    from .AttributeNodesGenerated import attribute_classes

    attribute_class = attribute_classes.get(attribute_name)

    if attribute_class is not None:
        assert attribute_class.attribute_name == attribute_name
        return attribute_class(expression=expression, source_ref=source_ref)
    else:
        return ExpressionAttributeLookup(
            expression=expression, attribute_name=attribute_name, source_ref=source_ref
        )


class ExpressionBuiltinGetattr(ChildrenExpressionBuiltinGetattrMixin, ExpressionBase):
    """Built-in "getattr".

    Typical code like this: getattr(object_arg, name, default)

    The default is optional, but computed before the lookup is done.
    """

    kind = "EXPRESSION_BUILTIN_GETATTR"

    named_children = ("expression", "name", "default|optional")

    def __init__(self, expression, name, default, source_ref):
        ChildrenExpressionBuiltinGetattrMixin.__init__(
            self, expression=expression, name=name, default=default
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        default = self.subnode_default

        if default is None or not default.mayHaveSideEffects():
            attribute = self.subnode_name

            attribute_name = attribute.getStringValue()

            if attribute_name is not None:
                source = self.subnode_expression
                if source.isKnownToHaveAttribute(attribute_name):
                    # If source has side effects, they must be evaluated, before
                    # the lookup, meaning, a temporary variable should be assigned.
                    # For now, we give up in this case.

                    side_effects = source.extractSideEffects()

                    if not side_effects:
                        result = makeExpressionAttributeLookup(
                            expression=source,
                            attribute_name=attribute_name,
                            source_ref=self.source_ref,
                        )

                        result = wrapExpressionWithNodeSideEffects(
                            new_node=result, old_node=attribute
                        )

                        return (
                            result,
                            "new_expression",
                            """Replaced call to built-in 'getattr' with constant \
attribute '%s' to mere attribute lookup"""
                            % attribute_name,
                        )

        return self, None, None


class ExpressionBuiltinSetattr(
    ExpressionNoneShapeExactMixin, ChildrenExpressionBuiltinSetattrMixin, ExpressionBase
):
    """Built-in "setattr".

    Typical code like this: setattr(source, attribute, value)
    """

    kind = "EXPRESSION_BUILTIN_SETATTR"

    named_children = ("expression", "name", "value")

    def __init__(self, expression, name, value, source_ref):
        ChildrenExpressionBuiltinSetattrMixin.__init__(
            self,
            expression=expression,
            name=name,
            value=value,
        )

        ExpressionBase.__init__(self, source_ref)

    # TODO: Enable this.
    # auto_compute_handling="wait_constant:attribute,raise"

    def computeExpressionConstantAttribute(self, trace_collection):
        return ExpressionAttributeLookup(
            expression=self.subnode_expression,
            attribute_name=self.subnode_attribute.getCompileTimeConstant(),
            source_ref=self.source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Might be possible to predict or downgrade to mere attribute set
        # in case of a compile time string attribute value.
        return self, None, None


class ExpressionBuiltinHasattr(ExpressionBuiltinHasattrBase):
    kind = "EXPRESSION_BUILTIN_HASATTR"

    named_children = ("expression", "name")

    auto_compute_handling = "wait_constant:name,raise"

    def computeExpression(self, trace_collection):
        # We do at least for compile time constants optimization here, but more
        # could be done, were we to know shapes.
        source = self.subnode_expression

        if source.isCompileTimeConstant():
            attribute = self.subnode_name

            attribute_name = attribute.getStringValue()

            # TODO: Something needs to be done if it has no string value.
            if attribute_name is not None:

                # If source or attribute have side effects, they must be
                # evaluated, before the lookup.
                (
                    result,
                    tags,
                    change_desc,
                ) = trace_collection.getCompileTimeComputationResult(
                    node=self,
                    computation=lambda: hasattr(
                        source.getCompileTimeConstant(), attribute_name
                    ),
                    description="Call to 'hasattr' pre-computed.",
                )

                result = wrapExpressionWithNodeSideEffects(
                    new_node=result, old_node=attribute
                )
                result = wrapExpressionWithNodeSideEffects(
                    new_node=result, old_node=source
                )

                return result, tags, change_desc

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionConstantName(self, trace_collection):
        attribute_name = self.subnode_name.getCompileTimeConstant()

        if type(attribute_name) not in (str, unicode):
            result = makeRaiseExceptionReplacementExpression(
                expression=self,
                exception_type="TypeError",
                exception_value="attribute name must be string",
            )

            return (
                result,
                "new_raise",
                "Call to hasattr with non-str type %s attribute name"
                % type(attribute_name),
            )

        if str is not unicode:
            attribute_name = attribute_name.encode()

        result = ExpressionAttributeCheck(
            expression=self.subnode_expression,
            attribute_name=attribute_name,
            source_ref=self.source_ref,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Built-in 'hasattr' with constant attribute name.",
        )


class ExpressionAttributeCheck(
    ExpressionBoolShapeExactMixin, ChildHavingExpressionMixin, ExpressionBase
):
    kind = "EXPRESSION_ATTRIBUTE_CHECK"

    named_children = ("expression",)

    __slots__ = ("attribute_name",)

    def __init__(self, expression, attribute_name, source_ref):
        ChildHavingExpressionMixin.__init__(self, expression=expression)

        ExpressionBase.__init__(self, source_ref)

        self.attribute_name = attribute_name

    def getDetails(self):
        return {"attribute_name": self.attribute_name}

    def computeExpression(self, trace_collection):
        source = self.subnode_expression

        # For things that know their attributes, we can statically optimize this
        # into true or false, preserving side effects of course.
        has_attribute = source.isKnownToHaveAttribute(self.attribute_name)
        if has_attribute is not None:
            result = makeCompileTimeConstantReplacementNode(
                value=has_attribute, node=self, user_provided=False
            )

            # If source has side effects, they must be evaluated.
            result = wrapExpressionWithNodeSideEffects(new_node=result, old_node=source)

            return (
                result,
                "new_constant",
                "Attribute check has been pre-computed to '%s'." % has_attribute,
            )

        # Attribute check does not raise is implemented by getting an attribute.
        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_expression.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    if str is bytes:

        @staticmethod
        def mayRaiseExceptionOperation():
            return False

    else:

        def mayRaiseExceptionOperation(self):
            return self.subnode_expression.mayRaiseExceptionAttributeLookup(
                BaseException, self.attribute_name
            )

    def getAttributeName(self):
        return self.attribute_name
