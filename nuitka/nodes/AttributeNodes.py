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

from .AttributeLookupNodes import ExpressionAttributeLookup
from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .NodeBases import StatementChildHavingBase, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    makeCompileTimeConstantReplacementNode,
    wrapExpressionWithNodeSideEffects,
)


class StatementAssignmentAttribute(StatementChildrenHavingBase):
    """Assignment to an attribute.

    Typically from code like: source.attribute_name = expression

    Both source and expression may be complex expressions, the source
    is evaluated first. Assigning to an attribute has its on slot on
    the source, which gets to decide if it knows it will work or not,
    and what value it will be.
    """

    __slots__ = ("attribute_name",)

    kind = "STATEMENT_ASSIGNMENT_ATTRIBUTE"

    named_children = ("source", "expression")

    def __init__(self, expression, attribute_name, source, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values={"expression": expression, "source": source},
            source_ref=source_ref,
        )

        self.attribute_name = attribute_name

    def getDetails(self):
        return {"attribute_name": self.attribute_name}

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


class StatementDelAttribute(StatementChildHavingBase):
    """Deletion of an attribute.

    Typically from code like: del source.attribute_name

    The source may be complex expression. Deleting an attribute has its on
    slot on the source, which gets to decide if it knows it will work or
    not, and what value it will be.
    """

    kind = "STATEMENT_DEL_ATTRIBUTE"

    named_child = "expression"

    __slots__ = ("attribute_name",)

    def __init__(self, expression, attribute_name, source_ref):
        StatementChildHavingBase.__init__(self, value=expression, source_ref=source_ref)

        self.attribute_name = attribute_name

    def getDetails(self):
        return {"attribute_name": self.attribute_name}

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


class ExpressionAttributeLookupSpecial(ExpressionAttributeLookup):
    """Special lookup up an attribute of an object.

    Typically from code like this: with source: pass

    These directly go to slots, and are performed for with statements
    of Python2.7 or higher.
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_SPECIAL"

    def computeExpression(self, trace_collection):
        return self.subnode_expression.computeExpressionAttributeSpecial(
            lookup_node=self,
            attribute_name=self.attribute_name,
            trace_collection=trace_collection,
        )


class ExpressionBuiltinGetattr(ExpressionChildrenHavingBase):
    """Built-in "getattr".

    Typical code like this: getattr(object_arg, name, default)

    The default is optional, but computed before the lookup is done.
    """

    kind = "EXPRESSION_BUILTIN_GETATTR"

    named_children = ("expression", "name", "default")

    def __init__(self, expression, name, default, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"expression": expression, "name": name, "default": default},
            source_ref=source_ref,
        )

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


class ExpressionBuiltinSetattr(ExpressionChildrenHavingBase):
    """Built-in "setattr".

    Typical code like this: setattr(source, attribute, value)
    """

    kind = "EXPRESSION_BUILTIN_SETATTR"

    named_children = ("expression", "attribute", "value")

    def __init__(self, expression, name, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"expression": expression, "attribute": name, "value": value},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # Note: Might be possible to predict or downgrade to mere attribute set.
        return self, None, None


class ExpressionBuiltinHasattr(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_HASATTR"

    named_children = ("expression", "attribute")

    def __init__(self, expression, name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"expression": expression, "attribute": name},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # We do at least for compile time constants optimization here, but more
        # could be done, were we to know shapes.
        source = self.subnode_expression

        if source.isCompileTimeConstant():
            attribute = self.subnode_attribute

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


class ExpressionAttributeCheck(ExpressionChildHavingBase):
    kind = "EXPRESSION_ATTRIBUTE_CHECK"

    named_child = "expression"

    __slots__ = ("attribute_name",)

    def __init__(self, expression, attribute_name, source_ref):
        ExpressionChildHavingBase.__init__(
            self, value=expression, source_ref=source_ref
        )

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

            return result, "new_constant", "Attribute check has been pre-computed."

        # Attribute check is implemented by getting an attribute.
        if source.mayRaiseExceptionAttributeLookup(BaseException, self.attribute_name):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    def getAttributeName(self):
        return self.attribute_name
