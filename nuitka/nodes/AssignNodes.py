#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Assignment related nodes.

All kinds of assignment targets as well as the assignment statement and
expression are located here. These are the core of value control flow.

Note: Currently there is also assignment to keeper nodes in KeeperNodes,
that should be unified at some point.

"""

from .NodeBases import StatementChildrenHavingBase


# Delayed import into multiple branches is not an issue, pylint: disable=W0404

class StatementAssignmentVariable(StatementChildrenHavingBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE"

    named_children = (
        "source",
        "variable_ref"
    )

    def __init__(self, variable_ref, source, source_ref):
        assert variable_ref is not None, source_ref
        assert source is not None, source_ref

        assert variable_ref.isTargetVariableRef()

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"       : source,
                "variable_ref" : variable_ref
            },
            source_ref = source_ref
        )

        self.inplace_suspect = None

    def getDetail(self):
        variable_ref = self.getTargetVariableRef()
        variable = variable_ref.getVariable()

        if variable is not None:
            return "to variable %s" % variable
        else:
            return "to variable %s" % self.getTargetVariableRef()

    getTargetVariableRef = StatementChildrenHavingBase.childGetter(
        "variable_ref"
    )
    getAssignSource = StatementChildrenHavingBase.childGetter(
        "source"
    )

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def isInplaceSuspect(self):
        return self.inplace_suspect

    def mayRaiseException(self, exception_type):
        return self.getAssignSource().mayRaiseException(exception_type)

    def computeStatement(self, constraint_collection):
        # Assignment source may re-compute here:
        constraint_collection.onExpression(self.getAssignSource())

        constraint_collection.onVariableSet(
            assign_node = self,
        )

        # TODO: Remove this, it's old.
        return constraint_collection._onStatementAssignmentVariable(self)


class StatementAssignmentAttribute(StatementChildrenHavingBase):
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
            "attribute" : self.attribute_name
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
        constraint_collection.onExpression(self.getAssignSource())
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it
        # away.
        if source.willRaiseException(BaseException):
            from .NodeMakingHelpers import \
                makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

            return result, "new_raise", """\
Attribute assignment raises exception in assigned value, removed assignment."""

        constraint_collection.onExpression(self.getLookupSource())
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            from .NodeMakingHelpers import \
                makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source
                )
            )

            return result, "new_raise", """\
Attribute assignment raises exception in source, removed assignment."""

        return self, None, None


class StatementAssignmentSubscript(StatementChildrenHavingBase):
    kind = "STATEMENT_ASSIGNMENT_SUBSCRIPT"

    named_children = (
        "source",
        "expression",
        "subscript"
    )

    def __init__(self, expression, subscript, source, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "subscript"  : subscript
            },
            source_ref = source_ref
        )

    getSubscribed = StatementChildrenHavingBase.childGetter("expression")
    getSubscript = StatementChildrenHavingBase.childGetter("subscript")
    getAssignSource = StatementChildrenHavingBase.childGetter("source")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getAssignSource()
        )
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it
        # away.
        if source.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

            return result, "new_raise", """\
Subscript assignment raises exception in assigned value, removed assignment."""

        constraint_collection.onExpression(self.getSubscribed())
        subscribed = self.getSubscribed()

        if subscribed.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    subscribed
                )
            )

            return result, "new_raise", """\
Subscript assignment raises exception in subscribed, removed assignment."""

        constraint_collection.onExpression(
            self.getSubscript()
        )
        subscript = self.getSubscript()

        if subscript.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    subscribed,
                    subscript
                )
            )

            return result, "new_raise", """
Subscript assignment raises exception in subscript value, removed \
assignment."""

        return self, None, None


class StatementAssignmentSlice(StatementChildrenHavingBase):
    kind = "STATEMENT_ASSIGNMENT_SLICE"

    named_children = (
        "source",
        "expression",
        "lower",
        "upper"
    )

    def __init__(self, expression, lower, upper, source, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            },
            source_ref = source_ref
        )

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")
    getLower = StatementChildrenHavingBase.childGetter("lower")
    getUpper = StatementChildrenHavingBase.childGetter("upper")
    getAssignSource = StatementChildrenHavingBase.childGetter("source")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getAssignSource())
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it
        # away.
        if source.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

            return result, "new_raise", """\
Slice assignment raises exception in assigned value, removed assignment."""

        constraint_collection.onExpression(self.getLookupSource())
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source
                )
            )

            return result, "new_raise", """\
Slice assignment raises exception in sliced value, removed assignment."""

        constraint_collection.onExpression( self.getLower(), allow_none = True )
        lower = self.getLower()

        if lower is not None and lower.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source,
                    lower
                )
            )

            return result, "new_raise", """\
Slice assignment raises exception in lower slice boundary value, removed \
assignment."""

        constraint_collection.onExpression( self.getUpper(), allow_none = True )
        upper = self.getUpper()

        if upper is not None and upper.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source,
                    lower,
                    upper
                )
            )

            return result, "new_raise", """\
Slice assignment raises exception in upper slice boundary value, removed \
assignment."""

        return self, None, None


class StatementDelVariable(StatementChildrenHavingBase):
    kind = "STATEMENT_DEL_VARIABLE"

    named_children = (
        "variable_ref",
    )

    def __init__(self, variable_ref, tolerant, source_ref):
        assert variable_ref is not None
        assert variable_ref.isTargetVariableRef()
        assert tolerant is True or tolerant is False

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "variable_ref" : variable_ref
            },
            source_ref = source_ref
        )

        self.tolerant = tolerant

    def getDetail(self):
        variable_ref = self.getTargetVariableRef()
        variable = variable_ref.getVariable()

        if variable is not None:
            return "to variable %s" % variable
        else:
            return "to variable %s" % self.getTargetVariableRef()

    def getDetails(self):
        return {
            "tolerant" : self.tolerant
        }

    # TODO: Value propagation needs to make a difference based on this.
    def isTolerant(self):
        return self.tolerant

    getTargetVariableRef = StatementChildrenHavingBase.childGetter(
        "variable_ref"
    )

    def computeStatement(self, constraint_collection):
        variable = self.getTargetVariableRef().getVariable()

        trace = constraint_collection.getVariableCurrentTrace(variable)

        # Optimize away tolerant "del" that is not needed.
        if trace.isUninitTrace():
            if self.isTolerant():
                return (
                    None,
                    "new_statements",
                    "Removed tolerate del without effect."
                )

        constraint_collection.onVariableDel(
            target_node = self.getTargetVariableRef()
        )

        return self, None, None

    def mayHaveSideEffects(self):
        return True

    def mayRaiseException(self, exception_type):
        if self.tolerant:
            return False
        else:
            variable = self.getTargetVariableRef().getVariable()

            # Temp variables won't raise.
            if variable.isTempVariableReference():
                return False

            return True


class StatementDelAttribute(StatementChildrenHavingBase):
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
        return { "attribute" : self.attribute_name }

    def getDetail(self):
        return "to attribute %s" % self.attribute_name

    def getAttributeName(self):
        return self.attribute_name

    def setAttributeName(self, attribute_name):
        self.attribute_name = attribute_name

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getLookupSource())
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = lookup_source,
                node       = self
            )

        return self, None, None


class StatementDelSubscript(StatementChildrenHavingBase):
    kind = "STATEMENT_DEL_SUBSCRIPT"

    named_children = (
        "expression",
        "subscript"
    )

    def __init__(self, expression, subscript, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "subscript"  : subscript
            },
            source_ref = source_ref
        )

    getSubscribed = StatementChildrenHavingBase.childGetter("expression")
    getSubscript = StatementChildrenHavingBase.childGetter("subscript")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getSubscribed())
        subscribed = self.getSubscribed()

        if subscribed.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = subscribed,
                node       = self
            )

            return result, "new_raise", """\
Subscript del raises exception in subscribed value, removed del"""

        constraint_collection.onExpression(self.getSubscript())
        subscript = self.getSubscript()

        if subscript.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    subscribed,
                    subscript
                )
            )

            return result, "new_raise", """\
Subscript del raises exception in subscribt value, removed del"""

        return self, None, None


class StatementDelSlice(StatementChildrenHavingBase):
    kind = "STATEMENT_DEL_SLICE"

    named_children = (
        "expression",
        "lower",
        "upper"
    )

    def __init__(self, expression, lower, upper, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            },
            source_ref = source_ref
        )

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")
    getLower = StatementChildrenHavingBase.childGetter("lower")
    getUpper = StatementChildrenHavingBase.childGetter("upper")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getLookupSource())
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = lookup_source,
                node       = self
            )

            return result, "new_raise", """\
Slice del raises exception in sliced value, removed del"""


        constraint_collection.onExpression(self.getLower(), allow_none = True)
        lower = self.getLower()

        if lower is not None and lower.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    lookup_source,
                    lower
                )
            )

            return result, "new_raise", """
Slice del raises exception in lower slice boundary value, removed del"""

        constraint_collection.onExpression(self.getUpper(), allow_none = True)
        upper = self.getUpper()

        if upper is not None and upper.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    lookup_source,
                    lower,
                    upper
                )
            )

            return result, "new_raise", """
Slice del raises exception in upper slice boundary value, removed del"""

        return self, None, None
