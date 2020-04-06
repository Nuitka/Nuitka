#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.ModuleRegistry import getOwnerFromCodeName
from nuitka.PythonVersions import python_version

from .DictionaryNodes import (
    ExpressionDictOperationGet,
    ExpressionDictOperationIn,
    ExpressionDictOperationNotIn,
    StatementDictOperationRemove,
    StatementDictOperationSet,
)
from .ExpressionBases import ExpressionBase
from .ModuleAttributeNodes import (
    ExpressionModuleAttributeLoaderRef,
    ExpressionModuleAttributeNameRef,
    ExpressionModuleAttributePackageRef,
    ExpressionModuleAttributeSpecRef,
)
from .NodeMakingHelpers import makeRaiseExceptionReplacementExpression
from .shapes.StandardShapes import tshape_unknown


class ExpressionVariableNameRef(ExpressionBase):
    """ These are used before the actual variable object is known from VariableClosure.

    """

    kind = "EXPRESSION_VARIABLE_NAME_REF"

    __slots__ = "variable_name", "provider"

    def __init__(self, provider, variable_name, source_ref):
        assert not provider.isExpressionOutlineBody(), source_ref

        ExpressionBase.__init__(self, source_ref=source_ref)

        self.variable_name = variable_name

        self.provider = provider

    def finalize(self):
        del self.parent
        del self.provider

    @staticmethod
    def isExpressionVariableNameRef():
        return True

    def getDetails(self):
        return {"variable_name": self.variable_name, "provider": self.provider}

    def getVariableName(self):
        return self.variable_name

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    @staticmethod
    def needsFallback():
        return True


class ExpressionVariableLocalNameRef(ExpressionVariableNameRef):
    """ These are used before the actual variable object is known from VariableClosure.

        The special thing about this as opposed to ExpressionVariableNameRef is that
        these must remain local names and cannot fallback to outside scopes. This is
        used for __annotations__.

    """

    kind = "EXPRESSION_VARIABLE_LOCAL_NAME_REF"

    @staticmethod
    def needsFallback():
        return False


class ExpressionVariableRefBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = "variable", "variable_trace"

    def __init__(self, variable, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

        self.variable = variable
        self.variable_trace = None

    def finalize(self):
        del self.parent
        del self.variable
        del self.variable_trace

    def getVariableName(self):
        return self.variable.getName()

    def getVariable(self):
        return self.variable

    def getVariableTrace(self):
        return self.variable_trace

    def getTypeShape(self):
        if self.variable_trace is None:
            return tshape_unknown
        else:
            return self.variable_trace.getTypeShape()

    def computeExpressionComparisonIn(self, in_node, value_node, trace_collection):
        tags = None
        message = None

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(in_node)

        if self.variable_trace.hasShapeDictionaryExact():
            tags = "new_expression"
            message = """\
Check '%s' on dictionary lowered to dictionary '%s'.""" % (
                in_node.comparator,
                in_node.comparator,
            )

            if in_node.comparator == "In":
                in_node = ExpressionDictOperationIn(
                    key=value_node,
                    dict_arg=self,
                    source_ref=in_node.getSourceReference(),
                )
            else:
                in_node = ExpressionDictOperationNotIn(
                    key=value_node,
                    dict_arg=self,
                    source_ref=in_node.getSourceReference(),
                )

        # Any exception may be raised.
        if in_node.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return in_node, tags, message

    def computeExpressionSetSubscript(
        self, set_node, subscript, value_node, trace_collection
    ):
        tags = None
        message = None

        # By default, an subscript may change everything about the lookup
        # source.
        if self.variable_trace.hasShapeDictionaryExact():
            set_node = StatementDictOperationSet(
                dict_arg=self,
                key=subscript,
                value=value_node,
                source_ref=set_node.getSourceReference(),
            )

            tags = "new_statements"
            message = """\
Subscript assignment to dictionary lowered to dictionary assignment."""

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception might be raised.
        if set_node.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, tags, message

    def computeExpressionDelSubscript(self, del_node, subscript, trace_collection):
        tags = None
        message = None

        # By default, an subscript may change everything about the lookup
        # source.
        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        if self.variable_trace.hasShapeDictionaryExact():
            del_node = StatementDictOperationRemove(
                dict_arg=self, key=subscript, source_ref=del_node.getSourceReference()
            )

            tags = "new_statements"
            message = """\
Subscript del to dictionary lowered to dictionary del."""

        # Any exception might be raised.
        if del_node.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return del_node, tags, message

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        tags = None
        message = None

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        if self.variable_trace.hasShapeDictionaryExact():
            lookup_node = ExpressionDictOperationGet(
                dict_arg=self,
                key=subscript,
                source_ref=lookup_node.getSourceReference(),
            )

            tags = "new_expression"
            message = """\
Subscript look-up to dictionary lowered to dictionary look-up."""

        # Any exception might be raised.
        if lookup_node.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, tags, message

    def _applyReplacement(self, trace_collection, replacement):
        trace_collection.signalChange(
            "new_expression",
            self.source_ref,
            "Value propagated for '%s' from '%s'."
            % (self.variable.getName(), replacement.getSourceReference().getAsString()),
        )

        # Special case for in-place assignments.
        if self.parent.isExpressionOperationInplace():
            statement = self.parent.parent

            if statement.isStatementAssignmentVariable():
                statement.unmarkAsInplaceSuspect()

        # Need to compute the replacement still.
        return replacement.computeExpressionRaw(trace_collection)


_hard_names = ("dir", "eval", "exec", "execfile", "locals", "vars", "super")


class ExpressionVariableRef(ExpressionVariableRefBase):
    kind = "EXPRESSION_VARIABLE_REF"

    __slots__ = ()

    def __init__(self, variable, source_ref):
        assert variable is not None

        ExpressionVariableRefBase.__init__(
            self, variable=variable, source_ref=source_ref
        )

    def getDetails(self):
        return {"variable": self.variable}

    def getDetailsForDisplay(self):
        return {
            "variable_name": self.variable.getName(),
            "owner": self.variable.getOwner().getCodeName(),
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is ExpressionVariableRef, cls

        owner = getOwnerFromCodeName(args["owner"])
        variable = owner.getProvidedVariable(args["variable_name"])

        return cls(variable=variable, source_ref=source_ref)

    @staticmethod
    def isTargetVariableRef():
        return False

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        assert isinstance(variable, Variables.Variable), repr(variable)

        self.variable = variable

    def computeExpressionRaw(self, trace_collection):
        # Terribly detailed, pylint: disable=too-many-branches,too-many-statements

        variable = self.variable
        assert variable is not None

        self.variable_trace = trace_collection.getVariableCurrentTrace(
            variable=variable
        )

        replacement = self.variable_trace.getReplacementNode(self)
        if replacement is not None:
            return self._applyReplacement(trace_collection, replacement)

        if not self.variable_trace.mustHaveValue():
            # TODO: This could be way more specific surely.
            trace_collection.onExceptionRaiseExit(BaseException)

        if variable.isModuleVariable() and variable.hasDefiniteWrites() is False:
            variable_name = self.variable.getName()

            if variable_name in Builtins.builtin_exception_names:
                if not self.variable.getOwner().getModuleDictScope().isEscaped():
                    from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

                    new_node = ExpressionBuiltinExceptionRef(
                        exception_name=self.variable.getName(),
                        source_ref=self.getSourceReference(),
                    )

                    change_tags = "new_builtin_ref"
                    change_desc = """\
Module variable '%s' found to be built-in exception reference.""" % (
                        variable_name
                    )
                else:
                    self.variable_trace.addUsage()

                    new_node = self
                    change_tags = None
                    change_desc = None

            elif variable_name in Builtins.builtin_names:
                if (
                    variable_name in _hard_names
                    or not self.variable.getOwner().getModuleDictScope().isEscaped()
                ):
                    from .BuiltinRefNodes import makeExpressionBuiltinRef

                    new_node = makeExpressionBuiltinRef(
                        builtin_name=variable_name, source_ref=self.getSourceReference()
                    )

                    change_tags = "new_builtin_ref"
                    change_desc = """\
Module variable '%s' found to be built-in reference.""" % (
                        variable_name
                    )
                else:
                    self.variable_trace.addUsage()

                    new_node = self
                    change_tags = None
                    change_desc = None
            elif variable_name == "__name__":
                new_node = ExpressionModuleAttributeNameRef(
                    variable=variable, source_ref=self.getSourceReference()
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__name__' with module attribute reference."""
            elif variable_name == "__package__":
                new_node = ExpressionModuleAttributePackageRef(
                    variable=variable, source_ref=self.getSourceReference()
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__package__' with module attribute reference."""
            elif variable_name == "__loader__" and python_version >= 300:
                new_node = ExpressionModuleAttributeLoaderRef(
                    variable=variable, source_ref=self.getSourceReference()
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__loader__' with module attribute reference."""
            elif variable_name == "__spec__" and python_version >= 340:
                new_node = ExpressionModuleAttributeSpecRef(
                    variable=variable, source_ref=self.getSourceReference()
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__spec__' with module attribute reference."""
            else:
                self.variable_trace.addUsage()

                # Probably should give a warning once about it.
                new_node = self
                change_tags = None
                change_desc = None

            return new_node, change_tags, change_desc

        self.variable_trace.addUsage()

        if self.variable_trace.mustNotHaveValue():
            assert self.variable.isLocalVariable(), self.variable

            variable_name = self.variable.getName()

            result = makeRaiseExceptionReplacementExpression(
                expression=self,
                exception_type="UnboundLocalError",
                exception_value="""\
local variable '%s' referenced before assignment"""
                % variable_name,
            )

            return (
                result,
                "new_raise",
                "Variable access of not initialized variable '%s'" % variable_name,
            )

        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):

        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onControlFlowEscape(self)

        if (
            not Variables.complete
            and self.variable.getName() in _hard_names
            and self.variable.isModuleVariable()
        ):
            # Just inform the collection that all escaped.
            trace_collection.onLocalsUsage(self.getParentVariableProvider())

        return call_node, None, None

    def hasShapeDictionaryExact(self):
        return self.variable_trace.hasShapeDictionaryExact()

    def onContentEscapes(self, trace_collection):
        trace_collection.onVariableContentEscapes(self.variable)

    def isKnownToBeIterable(self, count):
        return None

    def mayHaveSideEffects(self):
        return not self.variable_trace.mustHaveValue()

    def mayRaiseException(self, exception_type):
        return self.variable_trace is None or not self.variable_trace.mustHaveValue()

    def mayRaiseExceptionBool(self, exception_type):
        return (
            self.variable_trace is None
            or not self.variable_trace.mustHaveValue()
            or not self.variable_trace.getTypeShape().hasShapeSlotBool()
        )


class ExpressionTempVariableRef(ExpressionVariableRefBase):
    kind = "EXPRESSION_TEMP_VARIABLE_REF"

    def __init__(self, variable, source_ref):
        assert variable.isTempVariable()

        ExpressionVariableRefBase.__init__(
            self, variable=variable, source_ref=source_ref
        )

    def getDetailsForDisplay(self):
        return {
            "temp_name": self.variable.getName(),
            "owner": self.variable.getOwner().getCodeName(),
        }

    def getDetails(self):
        return {"variable": self.variable}

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is ExpressionTempVariableRef, cls

        owner = getOwnerFromCodeName(args["owner"])

        variable = owner.getTempVariable(None, args["temp_name"])

        return cls(variable=variable, source_ref=source_ref)

    @staticmethod
    def isTargetVariableRef():
        return False

    def computeExpressionRaw(self, trace_collection):
        self.variable_trace = trace_collection.getVariableCurrentTrace(
            variable=self.variable
        )

        replacement = self.variable_trace.getReplacementNode(self)
        if replacement is not None:
            return self._applyReplacement(trace_collection, replacement)

        self.variable_trace.addUsage()

        # Nothing to do here.
        return self, None, None

    def computeExpressionNext1(self, next_node, trace_collection):
        if self.variable_trace.isAssignTrace():
            value = self.variable_trace.getAssignNode().getAssignSource()

            # TODO: Add iteration handles to trace collections instead.
            current_index = trace_collection.getIteratorNextCount(value)
            trace_collection.onIteratorNext(value)

            if value.hasShapeSlotNext():
                if (
                    current_index is not None
                    # TODO: Change to iteration handles.
                    and value.isKnownToBeIterableAtMin(current_index + 1)
                    and value.canPredictIterationValues()
                ):

                    # TODO: Make use of this, pylint: disable=W0125
                    candidate = value.getIterationValue(current_index)

                    if False:
                        return (
                            candidate,
                            "new_expression",
                            "Predicted 'next' value from iteration.",
                        )
            else:
                # TODO: Could ask it about exception predictability for that case
                # or warn about it at least.
                pass
                # assert False, value

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return next_node, None, None

    def onContentEscapes(self, trace_collection):
        trace_collection.onVariableContentEscapes(self.variable)

    def mayHaveSideEffects(self):
        # Can't happen with temporary variables.
        return False

    def mayRaiseException(self, exception_type):
        # Can't happen with temporary variables.
        return False

    def mayRaiseExceptionImportName(self, exception_type, import_name):
        if self.variable_trace is not None and self.variable_trace.isAssignTrace():
            return (
                self.variable_trace.getAssignNode()
                .getAssignSource()
                .mayRaiseExceptionImportName(exception_type, import_name)
            )

        else:
            return ExpressionBase.mayRaiseExceptionImportName(
                self, exception_type, import_name
            )

    def isKnownToBeIterableAtMin(self, count):
        # TODO: See through the variable current trace.
        return None

    def isKnownToBeIterableAtMax(self, count):
        # TODO: See through the variable current trace.
        return None
