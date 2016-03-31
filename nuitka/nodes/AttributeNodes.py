#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator

from .NodeBases import (
    ExpressionChildrenHavingBase,
    StatementChildrenHavingBase
)
from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects


class StatementAssignmentAttribute(StatementChildrenHavingBase):
    """ Assignment to an attribute.

        Typically from code like: source.attribute_name = expression

        Both source and expression may be complex expressions, the source
        is evaluated first. Assigning to an attribute has its on slot on
        the source, which gets to decide if it knows it will work or not,
        and what value it will be.
    """

    kind = "STATEMENT_ASSIGNMENT_ATTRIBUTE"

    named_children = (
        "source",
        "expression"
    )

    def __init__(self, expression, attribute_name, source, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "source"     : source,
            },
            source_ref = source_ref
        )

        self.attribute_name = attribute_name

    def getDetails(self):
        return {
            "attribute_name" : self.attribute_name
        }

    def getDetail(self):
        return "to attribute %s" % self.attribute_name

    def getAttributeName(self):
        return self.attribute_name

    def setAttributeName(self, attribute_name):
        self.attribute_name = attribute_name

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")
    getAssignSource = StatementChildrenHavingBase.childGetter("source")

    def computeStatement(self, constraint_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            constraint_collection = constraint_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.getLookupSource().computeExpressionSetAttribute(
            set_node              = self,
            attribute_name        = self.attribute_name,
            value_node            = self.getAssignSource(),
            constraint_collection = constraint_collection
        )

    def getStatementNiceName(self):
        return "attribute assignment statement"


class StatementDelAttribute(StatementChildrenHavingBase):
    """ Deletion of an attribute.

        Typically from code like: del source.attribute_name

        The source may be complex expression. Deleting an attribute has its on
        slot on the source, which gets to decide if it knows it will work or
        not, and what value it will be.
    """
    kind = "STATEMENT_DEL_ATTRIBUTE"

    named_children = (
        "expression",
    )

    def __init__(self, expression, attribute_name, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.attribute_name = attribute_name

    def getDetails(self):
        return {
            "attribute_name" : self.attribute_name
        }

    def getDetail(self):
        return "to attribute %s" % self.attribute_name

    def getAttributeName(self):
        return self.attribute_name

    def setAttributeName(self, attribute_name):
        self.attribute_name = attribute_name

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")

    def computeStatement(self, constraint_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            constraint_collection = constraint_collection,
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.getLookupSource().computeExpressionDelAttribute(
            set_node              = self,
            attribute_name        = self.attribute_name,
            constraint_collection = constraint_collection
        )

    def getStatementNiceName(self):
        return "attribute del statement"


class ExpressionAttributeLookup(ExpressionChildrenHavingBase):
    """ Looking up an attribute of an object.

        Typically code like: source.attribute_name
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP"

    named_children = (
        "source",
    )

    def __init__(self, source, attribute_name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source" : source
            },
            source_ref = source_ref
        )

        self.attribute_name = attribute_name

    def getAttributeName(self):
        return self.attribute_name

    def setAttributeName(self, attribute_name):
        self.attribute_name = attribute_name

    def getDetails(self):
        return {
            "attribute_name" : self.getAttributeName()
        }

    def getDetail(self):
        return "attribute %s from %s" % (
            self.getAttributeName(),
            self.getLookupSource()
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter(
        "source"
    )

    def computeExpression(self, constraint_collection):
        return self.getLookupSource().computeExpressionAttribute(
            lookup_node           = self,
            attribute_name        = self.getAttributeName(),
            constraint_collection = constraint_collection
        )

    def mayRaiseException(self, exception_type):
        return self.getLookupSource().mayRaiseExceptionAttributeLookup(
            exception_type = exception_type,
            attribute_name = self.getAttributeName()
        )

    def isKnownToBeIterable(self, count):
        # TODO: Could be known. We would need for computeExpressionAttribute to
        # either return a new node, or a decision maker.
        return None


class ExpressionAttributeLookupSpecial(ExpressionAttributeLookup):
    """ Special lookup up an attribute of an object.

        Typically from code like this: with source: pass

        These directly go to slots, and are performed for with statements
        of Python2.7 or higher.
    """


    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_SPECIAL"

    def computeExpression(self, constraint_collection):
        return self.getLookupSource().computeExpressionAttributeSpecial(
            lookup_node           = self,
            attribute_name        = self.getAttributeName(),
            constraint_collection = constraint_collection
        )


class ExpressionBuiltinGetattr(ExpressionChildrenHavingBase):
    """ Built-in "getattr".

        Typical code like this: getattr(source, attribute, default)

        The default is optional, but computed before the lookup is done.
    """

    kind = "EXPRESSION_BUILTIN_GETATTR"

    named_children = ("source", "attribute", "default")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, object_arg, name, default, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object_arg,
                "attribute" : name,
                "default"   : default
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("source")
    getAttribute = ExpressionChildrenHavingBase.childGetter("attribute")
    getDefault = ExpressionChildrenHavingBase.childGetter("default")

    def computeExpression(self, constraint_collection):
        constraint_collection.onExceptionRaiseExit(BaseException)

        default = self.getDefault()

        if default is None or not default.mayHaveSideEffects():
            attribute = self.getAttribute()

            attribute_name = attribute.getStringValue()

            if attribute_name is not None:
                source = self.getLookupSource()
                if source.isKnownToHaveAttribute(attribute_name):
                    # If source has side effects, they must be evaluated, before
                    # the lookup, meaning, a temporary variable should be assigned.
                    # For now, we give up in this case.

                    side_effects = source.extractSideEffects()

                    if not side_effects:
                        result = ExpressionAttributeLookup(
                            source         = source,
                            attribute_name = attribute_name,
                            source_ref     = self.source_ref
                        )

                        result = wrapExpressionWithNodeSideEffects(
                            new_node = result,
                            old_node = attribute
                        )

                        return (
                            result,
                            "new_expression",
                            """Replaced call to built-in 'getattr' with constant \
attribute '%s' to mere attribute lookup""" % attribute_name
                        )

        return self, None, None


class ExpressionBuiltinSetattr(ExpressionChildrenHavingBase):
    """ Built-in "setattr".

        Typical code like this: setattr(source, attribute, value)
    """

    kind = "EXPRESSION_BUILTIN_SETATTR"

    named_children = ("source", "attribute", "value")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, object_arg, name, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object_arg,
                "attribute" : name,
                "value"     : value
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("source")
    getAttribute = ExpressionChildrenHavingBase.childGetter("attribute")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, constraint_collection):
        constraint_collection.onExceptionRaiseExit(BaseException)

        # Note: Might be possible to predict or downgrade to mere attribute set.
        return self, None, None


class ExpressionBuiltinHasattr(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_HASATTR"

    named_children = ("source", "attribute")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, object_arg, name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object_arg,
                "attribute" : name,
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("source")
    getAttribute = ExpressionChildrenHavingBase.childGetter("attribute")

    def computeExpression(self, constraint_collection):
        # We do at least for compile time constants optimization here, but more
        # could be done, were we to know shapes.
        source = self.getLookupSource()

        if source.isCompileTimeConstant():
            attribute = self.getAttribute()

            attribute_name = attribute.getStringValue()

            if attribute_name is not None:

                # If source or attribute have side effects, they must be
                # evaluated, before the lookup.
                result, tags, change_desc = constraint_collection.getCompileTimeComputationResult(
                    node        = self,
                    computation = lambda : hasattr(
                        source.getCompileTimeConstant(),
                        attribute_name
                    ),
                    description = "Call to 'hasattr' pre-computed."
                )

                result = wrapExpressionWithNodeSideEffects(
                    new_node = result,
                    old_node = attribute
                )
                result = wrapExpressionWithNodeSideEffects(
                    new_node = result,
                    old_node = source
                )

                return result, tags, change_desc

        constraint_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
