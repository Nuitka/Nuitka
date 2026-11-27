#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Attribute assignment, deletion, check, and built-in access nodes.

Attribute operations delegate prediction and optimization to
'computeExpression*Attribute' slots on the target expression, mirroring
CPython's 'tp_getattr'/'tp_getattro' split between compile-time known
attribute names and dynamic 'getattr'/'setattr'/'delattr'/'hasattr' calls.
"""

from nuitka.PythonVersions import python_version

from .AttributeLookupNodes import ExpressionAttributeLookup
from .ChildrenHavingMixins import ChildHavingExpressionMixin
from .ExpressionBases import ExpressionBase
from .ExpressionBasesGenerated import (
    ExpressionBuiltinDelattrBase,
    ExpressionBuiltinGetattrBase,
    ExpressionBuiltinHasattrBase,
    ExpressionBuiltinSetattrBase,
)
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionNoneShapeExactMixin,
)
from .NodeMakingHelpers import (
    makeCompileTimeConstantReplacementNode,
    makeRaiseExceptionReplacementExpression,
    wrapExpressionWithNodeSideEffects,
    wrapExpressionWithSideEffects,
)
from .StatementBasesGenerated import (
    StatementAssignmentAttributeBase,
    StatementDelAttributeBase,
)


class StatementAssignmentAttribute(StatementAssignmentAttributeBase):
    """Assignment to an attribute.

    Typically from code like: expression.attribute_name = source

    Both source and expression may be complex expressions; source is
    evaluated first. Attribute assignment dispatches to a slot on
    expression ('computeExpressionSetAttribute').
    """

    kind = "STATEMENT_ASSIGNMENT_ATTRIBUTE"

    named_children = ("source", "expression")
    node_attributes = ("attribute_name",)
    auto_compute_handling = "operation"

    def getAttributeName(self):
        return self.attribute_name

    def computeStatementOperation(self, trace_collection):
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

    Typically from code like: del expression.attribute_name

    Attribute deletion dispatches to a slot on expression
    ('computeExpressionDelAttribute').
    """

    kind = "STATEMENT_DEL_ATTRIBUTE"

    named_children = ("expression",)
    node_attributes = ("attribute_name",)
    auto_compute_handling = "operation"

    def getAttributeName(self):
        return self.attribute_name

    def computeStatementOperation(self, trace_collection):
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


class ExpressionBuiltinGetattr(ExpressionBuiltinGetattrBase):
    """Built-in 'getattr'.

    Typical code like this: getattr(expression, name, default)

    The default is optional, but computed before the lookup is done.
    """

    kind = "EXPRESSION_BUILTIN_GETATTR"

    named_children = ("expression", "name", "default|optional")

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    auto_compute_handling = "wait_constant:name,raise"

    def computeExpressionConstantName(self, trace_collection):
        if not self.subnode_name.isExpressionConstantStrOrUnicodeRef():
            attribute_name_type = self.subnode_name.getCompileTimeConstantType()

            # CPython 3.11 added the type to the 'getattr' error message.
            if python_version >= 0x3B0:
                exception_value = (
                    "attribute name must be string, not '%s'"
                    % attribute_name_type.__name__
                )
            else:
                exception_value = "getattr(): attribute name must be string"

            side_effects = [self.subnode_expression]

            if self.subnode_default is not None:
                side_effects.append(self.subnode_default)

            result = wrapExpressionWithSideEffects(
                side_effects=tuple(side_effects),
                old_node=self,
                new_node=makeRaiseExceptionReplacementExpression(
                    expression=self,
                    exception_type="TypeError",
                    exception_value=exception_value,
                ),
            )

            return (
                result,
                "new_raise",
                "Call to 'getattr' with non-str type '%s' attribute name."
                % attribute_name_type.__name__,
            )

        default = self.subnode_default

        if default is None or not default.mayHaveSideEffects():
            attribute_name = self.subnode_name.getCompileTimeConstant()

            if str is bytes and self.subnode_name.isExpressionConstantUnicodeRef():
                try:
                    attribute_name = attribute_name.encode("ascii")
                except UnicodeEncodeError:
                    return self, None, None

            source = self.subnode_expression
            if source.isKnownToHaveAttribute(attribute_name):
                side_effects = source.extractSideEffects()

                if not side_effects:
                    result = makeExpressionAttributeLookup(
                        expression=source,
                        attribute_name=attribute_name,
                        source_ref=self.source_ref,
                    )

                    return (
                        result,
                        "new_expression",
                        """Replaced call to built-in 'getattr' with constant \
attribute '%s' to mere attribute lookup""" % attribute_name,
                    )

        return self, None, None

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionBuiltinSetattr(
    ExpressionNoneShapeExactMixin, ExpressionBuiltinSetattrBase
):
    kind = "EXPRESSION_BUILTIN_SETATTR"

    named_children = ("expression", "name", "value")

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    auto_compute_handling = "wait_constant:name,raise"

    def computeExpressionConstantName(self, trace_collection):
        if not self.subnode_name.isExpressionConstantStrOrUnicodeRef():
            attribute_name_type = self.subnode_name.getCompileTimeConstantType()

            result = wrapExpressionWithSideEffects(
                side_effects=(self.subnode_expression, self.subnode_value),
                old_node=self,
                new_node=makeRaiseExceptionReplacementExpression(
                    expression=self,
                    exception_type="TypeError",
                    exception_value="attribute name must be string, not '%s'"
                    % attribute_name_type.__name__,
                ),
            )

            return (
                result,
                "new_raise",
                "Call to 'setattr' with non-str type '%s' attribute name."
                % attribute_name_type.__name__,
            )

        return self, None, None

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True

    def computeExpressionDrop(self, statement, trace_collection):
        if self.subnode_name.isExpressionConstantStrOrUnicodeRef():
            attribute_name = self.subnode_name.getCompileTimeConstant()

            if str is bytes and self.subnode_name.isExpressionConstantUnicodeRef():
                try:
                    attribute_name = attribute_name.encode("ascii")
                except UnicodeEncodeError:
                    return statement, None, None

            result = StatementAssignmentAttribute(
                expression=self.subnode_expression,
                attribute_name=attribute_name,
                source=self.subnode_value,
                source_ref=self.source_ref,
            )

            del self.parent

            return (
                result,
                "new_statements",
                "Reduced 'setattr' with constant attribute name to attribute assignment.",
            )

        return statement, None, None


class ExpressionBuiltinDelattr(
    ExpressionNoneShapeExactMixin, ExpressionBuiltinDelattrBase
):
    kind = "EXPRESSION_BUILTIN_DELATTR"

    named_children = ("expression", "name")

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    auto_compute_handling = "wait_constant:name,raise"

    def computeExpressionConstantName(self, trace_collection):
        if not self.subnode_name.isExpressionConstantStrOrUnicodeRef():
            attribute_name_type = self.subnode_name.getCompileTimeConstantType()

            result = wrapExpressionWithSideEffects(
                side_effects=(self.subnode_expression,),
                old_node=self,
                new_node=makeRaiseExceptionReplacementExpression(
                    expression=self,
                    exception_type="TypeError",
                    exception_value="attribute name must be string, not '%s'"
                    % attribute_name_type.__name__,
                ),
            )

            return (
                result,
                "new_raise",
                "Call to 'delattr' with non-str type '%s' attribute name."
                % attribute_name_type.__name__,
            )

        return self, None, None

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True

    def computeExpressionDrop(self, statement, trace_collection):
        if self.subnode_name.isExpressionConstantStrOrUnicodeRef():
            attribute_name = self.subnode_name.getCompileTimeConstant()

            if str is bytes and self.subnode_name.isExpressionConstantUnicodeRef():
                try:
                    attribute_name = attribute_name.encode("ascii")
                except UnicodeEncodeError:
                    return statement, None, None

            result = StatementDelAttribute(
                expression=self.subnode_expression,
                attribute_name=attribute_name,
                source_ref=self.source_ref,
            )

            del self.parent

            return (
                result,
                "new_statements",
                "Reduced 'delattr' with constant attribute name to attribute deletion.",
            )

        return statement, None, None


class ExpressionBuiltinHasattr(ExpressionBuiltinHasattrBase):
    kind = "EXPRESSION_BUILTIN_HASATTR"

    named_children = ("expression", "name")

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    auto_compute_handling = "wait_constant:name,raise"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True

    def computeExpressionConstantName(self, trace_collection):
        if not self.subnode_name.isExpressionConstantStrOrUnicodeRef():
            attribute_name_type = self.subnode_name.getCompileTimeConstantType()

            # CPython 3.11 added the type to the 'hasattr' error message.
            if python_version >= 0x3B0:
                exception_value = (
                    "attribute name must be string, not '%s'"
                    % attribute_name_type.__name__
                )
            else:
                exception_value = "hasattr(): attribute name must be string"

            result = wrapExpressionWithSideEffects(
                side_effects=(self.subnode_expression,),
                old_node=self,
                new_node=makeRaiseExceptionReplacementExpression(
                    expression=self,
                    exception_type="TypeError",
                    exception_value=exception_value,
                ),
            )

            return (
                result,
                "new_raise",
                "Call to hasattr with non-str type '%s' attribute name."
                % attribute_name_type.__name__,
            )

        attribute_name = self.subnode_name.getCompileTimeConstant()

        if str is bytes and self.subnode_name.isExpressionConstantUnicodeRef():
            try:
                attribute_name = attribute_name.encode("ascii")
            except UnicodeEncodeError:
                return self, None, None

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

        has_attribute = source.isKnownToHaveAttribute(self.attribute_name)
        if has_attribute is not None:
            result = makeCompileTimeConstantReplacementNode(
                value=has_attribute, node=self, user_provided=False
            )

            result = wrapExpressionWithNodeSideEffects(new_node=result, old_node=source)

            return (
                result,
                "new_constant",
                "Attribute check has been pre-computed to '%s'." % has_attribute,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_expression.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    # Python2 'hasattr' swallows all exceptions, while Python3 only catches 'AttributeError'.
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


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
