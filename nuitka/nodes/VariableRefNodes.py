#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Node for variable references.

These represent all variable references in the node tree. Can be in assignments
and its expressions, changing the meaning of course dramatically.

"""

from nuitka import Builtins, Variables
from nuitka.ModuleRegistry import getOwnerFromCodeName
from nuitka.PythonVersions import (
    getUnboundLocalErrorErrorTemplate,
    python_version,
)
from nuitka.tree.TreeHelpers import makeStatementsSequenceFromStatements

from .ConstantRefNodes import makeConstantRefNode
from .DictionaryNodes import (
    ExpressionDictOperationIn,
    ExpressionDictOperationItem,
    ExpressionDictOperationNotIn,
    StatementDictOperationRemove,
    StatementDictOperationSet,
)
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .ModuleAttributeNodes import (
    ExpressionModuleAttributeLoaderRef,
    ExpressionModuleAttributeNameRef,
    ExpressionModuleAttributePackageRef,
    ExpressionModuleAttributeSpecRef,
)
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpression,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
)
from .OutlineNodes import ExpressionOutlineBody
from .ReturnNodes import makeStatementReturn
from .shapes.StandardShapes import tshape_unknown
from .SubscriptNodes import ExpressionSubscriptLookupForUnpack


class ExpressionVariableRefBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = "variable", "variable_trace"

    def __init__(self, variable, source_ref):
        ExpressionBase.__init__(self, source_ref)

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

    def onContentEscapes(self, trace_collection):
        trace_collection.onVariableContentEscapes(self.variable)

    def computeExpressionLen(self, len_node, trace_collection):
        if self.variable_trace is not None and self.variable_trace.isAssignTrace():
            value = self.variable_trace.getAssignNode().subnode_source

            shape = value.getValueShape()

            has_len = shape.hasShapeSlotLen()

            if has_len is False:
                # Any exception may be raised.
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                    template="object of type '%s' has no len()",
                    operation="len",
                    original_node=len_node,
                    value_node=self,
                )
            elif has_len is True:
                iter_length = value.getIterationLength()

                if iter_length is not None:
                    result = makeConstantRefNode(
                        constant=int(iter_length),  # make sure to downcast long
                        source_ref=len_node.getSourceReference(),
                    )

                    return (
                        result,
                        "new_constant",
                        lambda: "Predicted 'len' result of variable '%s'."
                        % self.getVariableName(),
                    )

        # The variable itself is to be considered escaped.
        trace_collection.markActiveVariableAsEscaped(self.variable)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return len_node, None, None

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        if self.variable_trace is not None:
            attribute_node = self.variable_trace.getAttributeNode()

            if attribute_node is not None:
                # The variable itself is to be considered escaped no matter what, since
                # we don't know exactly what the attribute is used for later on. We would
                # have to attach the variable to the result created here in such a way,
                # that e.g. calling it will make it escaped only.
                trace_collection.markActiveVariableAsEscaped(self.variable)

                return attribute_node.computeExpressionAttribute(
                    lookup_node=lookup_node,
                    attribute_name=attribute_name,
                    trace_collection=trace_collection,
                )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # The variable itself is to be considered escaped.
        trace_collection.markActiveVariableAsEscaped(self.variable)

        if not self.isKnownToHaveAttribute(attribute_name):
            trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        return not self.isKnownToHaveAttribute(attribute_name)

    def isKnownToHaveAttribute(self, attribute_name):
        if self.variable_trace is not None:
            type_shape = self.variable_trace.getTypeShape()

            if type_shape.isKnownToHaveAttribute(attribute_name):
                return True

            attribute_node = self.variable_trace.getAttributeNode()

            if attribute_node is not None:
                return attribute_node.isKnownToHaveAttribute(attribute_name)

        return None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        # TODO: For include modules, something might be possible here.
        return self.computeExpressionAttribute(
            lookup_node=import_node,
            attribute_name=import_name,
            trace_collection=trace_collection,
        )

    def computeExpressionComparisonIn(self, in_node, value_node, trace_collection):
        tags = None
        message = None

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(in_node)

        # TODO: Add "set" shape here as well.
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

    def getExpressionDictInConstant(self, value):
        return self.variable_trace.getDictInValue(value)

    def computeExpressionSetSubscript(
        self, set_node, subscript, value_node, trace_collection
    ):
        tags = None
        message = None

        # By default, an subscript may change everything about the lookup
        # source.
        if self.variable_trace.hasShapeDictionaryExact():
            result = StatementDictOperationSet(
                dict_arg=self,
                key=subscript,
                value=value_node,
                source_ref=set_node.getSourceReference(),
            )
            change_tags = "new_statements"
            change_desc = """\
Subscript assignment to dictionary lowered to dictionary assignment."""

            trace_collection.removeKnowledge(self)

            result2, change_tags2, change_desc2 = result.computeStatementOperation(
                trace_collection
            )

            if result2 is not result:
                trace_collection.signalChange(
                    tags=change_tags,
                    source_ref=self.source_ref,
                    message=change_desc,
                )

                return result2, change_tags2, change_desc2
            else:
                return result, change_tags, change_desc

        trace_collection.removeKnowledge(self)

        trace_collection.removeKnowledge(value_node)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception might be raised.
        if set_node.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, tags, message

    def computeExpressionDelSubscript(self, del_node, subscript, trace_collection):
        tags = None
        message = None

        if self.variable_trace.hasShapeDictionaryExact():
            result = StatementDictOperationRemove(
                dict_arg=self,
                key=subscript,
                source_ref=del_node.getSourceReference(),
            )
            change_tags = "new_statements"
            change_desc = """\
Subscript del to dictionary lowered to dictionary del."""

            trace_collection.removeKnowledge(self)

            result2, change_tags2, change_desc2 = result.computeStatementOperation(
                trace_collection
            )

            if result2 is not result:
                trace_collection.signalChange(
                    tags=change_tags,
                    source_ref=self.source_ref,
                    message=change_desc,
                )

                return result2, change_tags2, change_desc2
            else:
                return result, change_tags, change_desc

        # By default, an subscript may change everything about the lookup
        # source.
        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception might be raised.
        if del_node.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return del_node, tags, message

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        tags = None
        message = None

        if self.variable_trace.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionDictOperationItem(
                    dict_arg=self,
                    key=subscript,
                    source_ref=lookup_node.getSourceReference(),
                ),
                change_tags="new_expression",
                change_desc="""\
Subscript look-up to dictionary lowered to dictionary look-up.""",
            )

        if subscript.isCompileTimeConstant():
            attribute_node = self.variable_trace.getAttributeNode()

            if attribute_node is not None:
                # TODO: That could probably be one single question.
                if (
                    attribute_node.isCompileTimeConstant()
                    and not attribute_node.isMutable()
                ):
                    return trace_collection.getCompileTimeComputationResult(
                        node=lookup_node,
                        computation=lambda: attribute_node.getCompileTimeConstant()[
                            subscript.getCompileTimeConstant()
                        ],
                        description="Subscript of variable immutable value.",
                    )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

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
                statement.removeMarkAsInplaceSuspect()

        # Need to compute the replacement still.
        return replacement.computeExpressionRaw(trace_collection)

    def getTruthValue(self):
        return self.variable_trace.getTruthValue()

    def getComparisonValue(self):
        return self.variable_trace.getComparisonValue()


_hard_names = ("dir", "eval", "exec", "execfile", "locals", "vars", "super")


class ExpressionVariableRef(ExpressionVariableRefBase):
    kind = "EXPRESSION_VARIABLE_REF"

    __slots__ = ()

    def __init__(self, variable, source_ref):
        assert variable is not None

        ExpressionVariableRefBase.__init__(
            self, variable=variable, source_ref=source_ref
        )

    @staticmethod
    def isExpressionVariableRef():
        return True

    @staticmethod
    def isExpressionVariableRefOrTempVariableRef():
        return True

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
            # TODO: This could be way more specific surely, either NameError or UnboundLocalError
            # could be decided from context.
            trace_collection.onExceptionRaiseExit(BaseException)

        very_trusted_node = self.variable_trace.getAttributeNodeVeryTrusted()
        if very_trusted_node is not None:
            return (
                very_trusted_node.makeClone(),
                "new_expression",
                lambda: "Forward propagating value of %s from very trusted %s value."
                % (self.getVariableName(), very_trusted_node.kind),
            )

        if variable.isModuleVariable() and (
            variable.hasDefiniteWrites() is False or variable.getName() == "super"
        ):
            variable_name = self.variable.getName()

            if variable_name in Builtins.builtin_exception_names:
                if not self.variable.getOwner().getLocalsScope().isEscaped():
                    from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

                    new_node = ExpressionBuiltinExceptionRef(
                        exception_name=self.variable.getName(),
                        source_ref=self.source_ref,
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
                    or not self.variable.getOwner().getLocalsScope().isEscaped()
                ):
                    from .BuiltinRefNodes import makeExpressionBuiltinRef

                    new_node = makeExpressionBuiltinRef(
                        builtin_name=variable_name,
                        locals_scope=self.getFunctionsLocalsScope(),
                        source_ref=self.source_ref,
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
                    variable=variable, source_ref=self.source_ref
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__name__' with module attribute reference."""
            elif variable_name == "__package__":
                new_node = ExpressionModuleAttributePackageRef(
                    variable=variable, source_ref=self.source_ref
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__package__' with module attribute reference."""
            elif variable_name == "__loader__" and python_version >= 0x300:
                new_node = ExpressionModuleAttributeLoaderRef(
                    variable=variable, source_ref=self.source_ref
                )

                change_tags = "new_expression"
                change_desc = """\
Replaced read-only module attribute '__loader__' with module attribute reference."""
            elif variable_name == "__spec__" and python_version >= 0x300:
                new_node = ExpressionModuleAttributeSpecRef(
                    variable=variable, source_ref=self.source_ref
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
                exception_value=getUnboundLocalErrorErrorTemplate() % variable_name,
            )

            return (
                result,
                "new_raise",
                "Variable access of not initialized variable '%s'" % variable_name,
            )

        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        if self.variable_trace is not None:
            attribute_node = self.variable_trace.getAttributeNode()

            if attribute_node is not None:
                # The variable itself is to be considered escaped no matter what, since
                # we don't know exactly what the attribute is used for later on. We would
                # have to attach the variable to the result created here in such a way,
                # that e.g. calling it will make it escaped only.
                trace_collection.markActiveVariableAsEscaped(self.variable)

                return attribute_node.computeExpressionCallViaVariable(
                    call_node=call_node,
                    variable_ref_node=self,
                    call_args=call_args,
                    call_kw=call_kw,
                    trace_collection=trace_collection,
                )

        # The called and the arguments escape for good.
        self.onContentEscapes(trace_collection)
        if call_args is not None:
            call_args.onContentEscapes(trace_collection)
        if call_kw is not None:
            call_kw.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        if (
            self.variable.getName() in _hard_names
            and self.variable.isIncompleteModuleVariable()
        ):
            # Just inform the collection that all escaped.
            trace_collection.onLocalsUsage(locals_scope=self.getFunctionsLocalsScope())

        return call_node, None, None

    def computeExpressionBool(self, trace_collection):
        if self.variable_trace is not None:
            attribute_node = self.variable_trace.getAttributeNode()

            if attribute_node is not None:
                if (
                    attribute_node.isCompileTimeConstant()
                    and not attribute_node.isMutable()
                ):
                    return (
                        bool(attribute_node.getCompileTimeConstant()),
                        attribute_node.makeClone(),
                        "Using trusted constant's truth value.",
                    )

        # TODO: This is probably only default stuff here, that could be compressed.
        if not self.mayRaiseException(BaseException) and self.mayRaiseExceptionBool(
            BaseException
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

        return None, None, None

    def collectVariableAccesses(self, emit_read, emit_write):
        emit_read(self.variable)

    def hasShapeListExact(self):
        return (
            self.variable_trace is not None and self.variable_trace.hasShapeListExact()
        )

    def hasShapeDictionaryExact(self):
        return (
            self.variable_trace is not None
            and self.variable_trace.hasShapeDictionaryExact()
        )

    def hasShapeStrExact(self):
        return (
            self.variable_trace is not None and self.variable_trace.hasShapeStrExact()
        )

    def hasShapeUnicodeExact(self):
        return (
            self.variable_trace is not None
            and self.variable_trace.hasShapeUnicodeExact()
        )

    def hasShapeBoolExact(self):
        return (
            self.variable_trace is not None and self.variable_trace.hasShapeBoolExact()
        )

    @staticmethod
    def isKnownToBeIterable(count):
        return None

    def mayHaveSideEffects(self):
        return self.variable_trace is None or not self.variable_trace.mustHaveValue()

    def mayRaiseException(self, exception_type):
        return self.variable_trace is None or not self.variable_trace.mustHaveValue()

    def mayRaiseExceptionBool(self, exception_type):
        return (
            self.variable_trace is None
            or not self.variable_trace.mustHaveValue()
            or not self.variable_trace.getTypeShape().hasShapeSlotBool()
        )

    def getFunctionsLocalsScope(self):
        return self.getParentVariableProvider().getLocalsScope()


class ExpressionVariableOrBuiltinRef(ExpressionVariableRef):
    kind = "EXPRESSION_VARIABLE_OR_BUILTIN_REF"

    __slots__ = ("locals_scope",)

    def __init__(self, variable, locals_scope, source_ref):
        ExpressionVariableRef.__init__(self, variable=variable, source_ref=source_ref)

        self.locals_scope = locals_scope

    def getDetails(self):
        return {"variable": self.variable, "locals_scope": self.locals_scope}

    def getFunctionsLocalsScope(self):
        return self.locals_scope


def makeExpressionVariableRef(variable, locals_scope, source_ref):
    if variable.getName() in _hard_names:
        return ExpressionVariableOrBuiltinRef(
            variable=variable, locals_scope=locals_scope, source_ref=source_ref
        )
    else:
        return ExpressionVariableRef(variable=variable, source_ref=source_ref)


# Note: Temporary variable references are to be guaranteed to not raise
# therefore no side effects.
class ExpressionTempVariableRef(
    ExpressionNoSideEffectsMixin, ExpressionVariableRefBase
):
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

    @staticmethod
    def isExpressionTempVariableRef():
        return True

    @staticmethod
    def isExpressionVariableRefOrTempVariableRef():
        return True

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is ExpressionTempVariableRef, cls

        owner = getOwnerFromCodeName(args["owner"])

        variable = owner.getTempVariable(None, args["temp_name"])

        return cls(variable=variable, source_ref=source_ref)

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

    def _makeIterationNextReplacementNode(
        self, trace_collection, next_node, iterator_assign_node
    ):
        from .OperatorNodes import makeExpressionOperationBinaryInplace
        from .VariableAssignNodes import makeStatementAssignmentVariable

        provider = trace_collection.getOwner()

        outline_body = ExpressionOutlineBody(
            provider=provider,
            name="next_value_accessor",
            source_ref=self.source_ref,
        )

        if next_node.isExpressionSpecialUnpack():
            source = ExpressionSubscriptLookupForUnpack(
                expression=ExpressionTempVariableRef(
                    variable=iterator_assign_node.tmp_iterated_variable,
                    source_ref=self.source_ref,
                ),
                subscript=ExpressionTempVariableRef(
                    variable=iterator_assign_node.tmp_iteration_count_variable,
                    source_ref=self.source_ref,
                ),
                expected=next_node.getExpected(),
                source_ref=self.source_ref,
            )
        else:
            source = ExpressionSubscriptLookupForUnpack(
                expression=ExpressionTempVariableRef(
                    variable=iterator_assign_node.tmp_iterated_variable,
                    source_ref=self.source_ref,
                ),
                subscript=ExpressionTempVariableRef(
                    variable=iterator_assign_node.tmp_iteration_count_variable,
                    source_ref=self.source_ref,
                ),
                expected=None,
                source_ref=self.source_ref,
            )

        statements = (
            makeStatementAssignmentVariable(
                variable=iterator_assign_node.tmp_iteration_next_variable,
                source=source,
                source_ref=self.source_ref,
            ),
            makeStatementAssignmentVariable(
                variable=iterator_assign_node.tmp_iteration_count_variable,
                source=makeExpressionOperationBinaryInplace(
                    left=ExpressionTempVariableRef(
                        variable=iterator_assign_node.tmp_iteration_count_variable,
                        source_ref=self.source_ref,
                    ),
                    right=makeConstantRefNode(constant=1, source_ref=self.source_ref),
                    operator="IAdd",
                    source_ref=self.source_ref,
                ),
                source_ref=self.source_ref,
            ),
            makeStatementReturn(
                expression=ExpressionTempVariableRef(
                    variable=iterator_assign_node.tmp_iteration_next_variable,
                    source_ref=self.source_ref,
                ),
                source_ref=self.source_ref,
            ),
        )

        outline_body.setChildBody(makeStatementsSequenceFromStatements(*statements))

        return False, trace_collection.computedExpressionResultRaw(
            outline_body,
            change_tags="new_expression",
            change_desc=lambda: "Iterator 'next' converted to %s."
            % iterator_assign_node.getIterationIndexDesc(),
        )

    def computeExpressionNext1(self, next_node, trace_collection):
        iteration_source_node = self.variable_trace.getIterationSourceNode()

        if iteration_source_node is not None:
            if iteration_source_node.parent.isStatementAssignmentVariableIterator():
                iterator_assign_node = iteration_source_node.parent

                if iterator_assign_node.tmp_iterated_variable is not None:
                    return self._makeIterationNextReplacementNode(
                        trace_collection=trace_collection,
                        next_node=next_node,
                        iterator_assign_node=iterator_assign_node,
                    )

            iteration_source_node.onContentIteratedEscapes(trace_collection)

            if iteration_source_node.mayHaveSideEffectsNext():
                trace_collection.onControlFlowEscape(self)

        else:
            self.onContentEscapes(trace_collection)

            # Any code could be run, note that.
            if self.mayHaveSideEffectsNext():
                trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return True, (next_node, None, None)

    def mayRaiseExceptionImportName(self, exception_type, import_name):
        if self.variable_trace is not None and self.variable_trace.isAssignTrace():
            return self.variable_trace.getAssignNode().subnode_source.mayRaiseExceptionImportName(
                exception_type, import_name
            )

        else:
            return True

    @staticmethod
    def isKnownToBeIterableAtMin(count):
        # TODO: See through the variable current trace.
        return None


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
