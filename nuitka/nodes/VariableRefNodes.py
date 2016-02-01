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
""" Node for variable references.

These represent all variable references in the node tree. Can be in assignments
and its expressions, changing the meaning of course dramatically.

"""

from nuitka import Builtins, Variables

from .ConstantRefNodes import ExpressionConstantRef
from .DictionaryNodes import (
    ExpressionDictOperationGet,
    ExpressionDictOperationIn,
    ExpressionDictOperationNOTIn,
    StatementDictOperationRemove,
    StatementDictOperationSet
)
from .NodeBases import ExpressionMixin, NodeBase


class ExpressionVariableRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_VARIABLE_REF"

    def __init__(self, variable_name, source_ref, variable = None):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.variable_name = variable_name
        self.variable = variable

        if variable is not None:
            assert variable.getName() == variable_name

        self.variable_trace = None

        self.global_trace = None

    def getDetails(self):
        if self.variable is None:
            return {
                "variable_name" : self.variable_name
            }
        else:
            return {
                "variable_name" : self.variable_name,
                "variable"      : self.variable
            }

    def getDetail(self):
        if self.variable is None:
            return self.variable_name
        else:
            return repr(self.variable)

    @staticmethod
    def isTargetVariableRef():
        return False

    def getVariableName(self):
        return self.variable_name

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        assert isinstance(variable, Variables.Variable), repr(variable)

        self.variable = variable

    def computeExpression(self, constraint_collection):
        variable = self.variable

        assert variable is not None

        self.variable_trace = constraint_collection.getVariableCurrentTrace(
            variable = variable
        )

        replacement = self.variable_trace.getReplacementNode(self)

        if replacement is not None:
            constraint_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Value propagated for '%s' from '%s'." % (
                    self.variable.getName(),
                    replacement.getSourceReference().getAsString()
                )
            )

            # Need to compute the replacement still.
            return replacement.computeExpression(constraint_collection)

        if not self.variable_trace.mustHaveValue():
            # TODO: This could be way more specific surely.
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )

        self.global_trace = variable.getGlobalVariableTrace()

        # TODO: Maybe local variables are factored into this strangely.
        if self.global_trace is not None and \
           (variable.isModuleVariable() and not self.global_trace.hasDefiniteWrites() ) or \
             variable.isMaybeLocalVariable():
            if self.variable_name in Builtins.builtin_exception_names:
                from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

                new_node = ExpressionBuiltinExceptionRef(
                    exception_name = self.variable_name,
                    source_ref     = self.getSourceReference()
                )

                change_tags = "new_builtin_ref"
                change_desc = """\
Module variable '%s' found to be built-in exception reference.""" % (
                    self.variable_name
                )
            elif self.variable_name in Builtins.builtin_names and \
                 self.variable_name != "pow":
                from .BuiltinRefNodes import ExpressionBuiltinRef

                new_node = ExpressionBuiltinRef(
                    builtin_name = self.variable_name,
                    source_ref   = self.getSourceReference()
                )

                change_tags = "new_builtin_ref"
                change_desc = """\
Module variable '%s' found to be built-in reference.""" % (
                    self.variable_name
                )
            elif self.variable_name == "__name__":
                new_node = ExpressionConstantRef(
                    constant   = variable.getOwner().getParentModule().\
                                   getFullName(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = """\
Replaced read-only module attribute '__name__' with constant value."""
            elif self.variable_name == "__package__":
                new_node = ExpressionConstantRef(
                    constant   = variable.getOwner().getPackage(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = """\
Replaced read-only module attribute '__package__' with constant value."""
            else:
                self.variable_trace.addUsage()

                # Probably should give a warning once about it.
                new_node = self
                change_tags = None
                change_desc = None

            return new_node, change_tags, change_desc

        self.variable_trace.addUsage()

        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw,
                              constraint_collection):

        constraint_collection.onExceptionRaiseExit(BaseException)

        constraint_collection.onControlFlowEscape(self)

        if self.global_trace is None and \
           self.variable_name in ("dir", "eval", "exec", "execfile", "locals", "vars") and \
           self.variable.isModuleVariable():
            # Just inform the collection that all escaped.
            constraint_collection.onLocalsUsage()

        return call_node, None, None

    def computeExpressionSetSubscript(self, set_node, subscript, value_node,
                                      constraint_collection):
        tags = None
        message = None

        # By default, an subscript may change everything about the lookup
        # source.
        if self.variable_trace.hasShapeDictionaryExact():
            set_node = StatementDictOperationSet(
                dict_arg   = self,
                key        = subscript,
                value      = value_node,
                source_ref = set_node.getSourceReference()
            )

            tags = "new_statements"
            message = """\
Subscript assignment to dictionary lowered to dictionary assignment."""

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(self)

        # Any exception might be raised.
        if set_node.mayRaiseException(BaseException):
            constraint_collection.onExceptionRaiseExit(BaseException)

        return set_node, tags, message

    def computeExpressionDelSubscript(self, del_node, subscript,
                                      constraint_collection):
        tags = None
        message = None

        # By default, an subscript may change everything about the lookup
        # source.
        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(self)

        if self.variable_trace.hasShapeDictionaryExact():
            del_node = StatementDictOperationRemove(
                dict_arg   = self,
                key        = subscript,
                source_ref = del_node.getSourceReference()
            )

            tags = "new_statements"
            message = """\
Subscript del to dictionary lowered to dictionary del."""


        # Any exception might be raised.
        if del_node.mayRaiseException(BaseException):
            constraint_collection.onExceptionRaiseExit(BaseException)

        return del_node, tags, message

    def computeExpressionSubscript(self, lookup_node, subscript, constraint_collection):
        tags = None
        message = None

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(self)

        if self.variable_trace.hasShapeDictionaryExact():
            lookup_node = ExpressionDictOperationGet(
                dict_arg   = self,
                key        = subscript,
                source_ref = lookup_node.getSourceReference()
            )

            tags = "new_expression"
            message = """\
Subscript look-up to dictionary lowered to dictionary look-up."""

        # Any exception might be raised.
        if lookup_node.mayRaiseException(BaseException):
            constraint_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, tags, message

    def computeExpressionComparisonIn(self, in_node, value_node, constraint_collection):
        tags = None
        message = None

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(in_node)

        if self.variable_trace.hasShapeDictionaryExact():
            tags = "new_expression"
            message = """\
Check '%s' on dictionary lowered to dictionary '%s'.""" % (
                in_node.comparator,
                in_node.comparator
            )

            if in_node.comparator == "In":
                in_node = ExpressionDictOperationIn(
                    key        = value_node,
                    dict_arg   = self,
                    source_ref = in_node.getSourceReference()
                )
            else:
                in_node = ExpressionDictOperationNOTIn(
                    key        = value_node,
                    dict_arg   = self,
                    source_ref = in_node.getSourceReference()
                )


        # Any exception may be raised.
        if in_node.mayRaiseException(BaseException):
            constraint_collection.onExceptionRaiseExit(BaseException)

        return in_node, tags, message

    def hasShapeDictionaryExact(self):
        return self.variable_trace.hasShapeDictionaryExact()

    def onContentEscapes(self, constraint_collection):
        constraint_collection.onVariableContentEscapes(self.variable)

    def isKnownToBeIterable(self, count):
        return None

    def mayHaveSideEffects(self):
        return not self.variable_trace.mustHaveValue()

    def mayRaiseException(self, exception_type):
        variable_trace = self.variable_trace

        return variable_trace is None or not self.variable_trace.mustHaveValue()


class ExpressionTempVariableRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_TEMP_VARIABLE_REF"

    def __init__(self, variable, source_ref):
        assert variable.isTempVariable()

        NodeBase.__init__(self, source_ref = source_ref)

        self.variable = variable
        self.variable_trace = None

    def getDetailsForDisplay(self):
        return {
            "name" : self.variable.getName()
        }

    def getDetails(self):
        return {
            "variable" : self.variable
        }

    def getDetail(self):
        return self.variable.getName()

    def getVariableName(self):
        return self.variable.getName()

    def getVariable(self):
        return self.variable

    @staticmethod
    def isTargetVariableRef():
        return False

    def computeExpression(self, constraint_collection):
        self.variable_trace = constraint_collection.getVariableCurrentTrace(
            variable = self.variable
        )

        replacement = self.variable_trace.getReplacementNode(self)

        if replacement is not None:
            return replacement, "new_expression", "Value propagated for temp '%s'." % self.variable.getName()

        self.variable_trace.addUsage()
        # Nothing to do here.
        return self, None, None

    def onContentEscapes(self, constraint_collection):
        constraint_collection.onVariableContentEscapes(self.variable)

    def mayHaveSideEffects(self):
        # Can't happen
        return False

    def mayRaiseException(self, exception_type):
        # Can't happen
        return False

    def isKnownToBeIterableAtMin(self, count):
        # TODO: See through the variable current trace.
        return None

    def isKnownToBeIterableAtMax(self, count):
        # TODO: See through the variable current trace.
        return None

    # Python3 only, it updates temporary variables that are closure variables.
    def setVariable(self, variable):
        self.variable = variable
