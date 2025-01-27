#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes for functions and their creations.

Lambdas are functions too. The functions are at the core of the language and
have their complexities.

Creating a CPython function object is an optional thing. Some things might
only be used to be called directly, while knowing exactly what it is. So
the "ExpressionFunctionCreation" might be used to provide that kind of
CPython reference, and may escape.

Coroutines and generators live in their dedicated module and share base
classes.
"""

import inspect
import re

from nuitka import Options, Variables
from nuitka.Constants import isMutable
from nuitka.optimizations.TraceCollections import (
    TraceCollectionPureFunction,
    withChangeIndicationsTo,
)
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import (
    ParameterSpec,
    TooManyArguments,
    matchCall,
)
from nuitka.Tracing import optimization_logger, printError
from nuitka.tree.Extractions import updateVariableUsage
from nuitka.tree.SourceHandling import readSourceLines
from nuitka.tree.TreeHelpers import makeDictCreationOrConstant2

from .ChildrenHavingMixins import (
    ChildHavingBodyOptionalMixin,
    ChildrenHavingDefaultsTupleKwDefaultsOptionalAnnotationsOptionalFunctionRefMixin,
    ChildrenHavingFunctionValuesTupleMixin,
    ChildrenHavingKwDefaultsOptionalDefaultsTupleAnnotationsOptionalFunctionRefMixin,
)
from .CodeObjectSpecs import CodeObjectSpec
from .ContainerMakingNodes import makeExpressionMakeTupleOrConstant
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .FutureSpecs import fromFlags
from .IndicatorMixins import (
    EntryPointMixin,
    MarkUnoptimizedFunctionIndicatorMixin,
)
from .LocalsScopes import getLocalsDictHandle
from .NodeBases import (
    ClosureGiverNodeMixin,
    ClosureTakerMixin,
    SideEffectsFromChildrenMixin,
)
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpressionFromInstance,
    wrapExpressionWithSideEffects,
)
from .shapes.BuiltinTypeShapes import tshape_function


class MaybeLocalVariableUsage(Exception):
    pass


class ExpressionFunctionBodyBase(
    ClosureTakerMixin,
    ClosureGiverNodeMixin,
    ChildHavingBodyOptionalMixin,
    ExpressionBase,
):
    # TODO: The code_prefix should be a class attribute instead.
    __slots__ = (
        "provider",
        "taken",
        "name",
        "code_prefix",
        "code_name",
        "uids",
        "temp_variables",
        "temp_scopes",
        "preserver_id",
        "flags",
    )

    if python_version >= 0x300:
        __slots__ += ("qualname_provider", "non_local_declarations")

    # Might be None initially in some cases.
    named_children = ("body|optional+setter",)

    def __init__(self, provider, name, body, code_prefix, flags, source_ref):
        while provider.isExpressionOutlineBody():
            provider = provider.getParentVariableProvider()

        ChildHavingBodyOptionalMixin.__init__(
            self,
            body=body,
        )

        ClosureTakerMixin.__init__(self, provider=provider)

        ClosureGiverNodeMixin.__init__(self, name=name, code_prefix=code_prefix)

        ExpressionBase.__init__(self, source_ref)

        # Special things, "has_super" indicates presence of "super" in variable
        # usage, which modifies some behaviors.
        self.flags = flags or None

        # Hack: This allows some APIs to work although this is not yet
        # officially a child yet. Important during building.
        self.parent = provider

        if python_version >= 0x300:
            # Python3: Might be overridden by global statement on the class name.
            # TODO: Make this class only code.
            self.qualname_provider = provider

            # Non-local declarations if any.
            self.non_local_declarations = None

    @staticmethod
    def isExpressionFunctionBodyBase():
        return True

    def getEntryPoint(self):
        """Entry point for code.

        Normally ourselves. Only outlines will refer to their parent which
        technically owns them.

        """

        return self

    def getContainingClassDictCreation(self):
        current = self

        while not current.isCompiledPythonModule():
            if current.isExpressionClassBodyBase():
                return current

            current = current.getParentVariableProvider()

        return None

    def hasFlag(self, flag):
        return self.flags is not None and flag in self.flags

    def discardFlag(self, flag):
        if self.flags is not None:
            self.flags.discard(flag)

    @staticmethod
    def isEarlyClosure():
        """Early closure taking means immediate binding of references.

        Normally it's good to lookup name references immediately, but not for
        functions. In case of a function body it is not allowed to do that,
        because a later assignment needs to be queried first. Nodes need to
        indicate via this if they would like to resolve references at the same
        time as assignments.
        """

        return False

    def getLocalsScope(self):
        return self.locals_scope

    # TODO: Dubious function doing to distinct things, should be moved to users.
    def hasVariableName(self, variable_name):
        return (
            self.locals_scope.hasProvidedVariable(variable_name)
            or variable_name in self.temp_variables
        )

    def getProvidedVariables(self):
        if self.locals_scope is not None:
            return self.locals_scope.getProvidedVariables()
        else:
            return ()

    def getLocalVariables(self):
        return [
            variable
            for variable in self.getProvidedVariables()
            if variable.isLocalVariable()
        ]

    def getUserLocalVariables(self):
        return [
            variable
            for variable in self.getProvidedVariables()
            if variable.isLocalVariable() and not variable.isParameterVariable()
            if variable.getOwner() is self
        ]

    def getOutlineLocalVariables(self):
        result = []

        outlines = self.getTraceCollection().getOutlineFunctions()

        if outlines is None:
            return result

        for outline in outlines:
            result.extend(outline.getUserLocalVariables())

        return result

    def removeClosureVariable(self, variable):
        # Do not remove parameter variables of ours.
        assert not variable.isParameterVariable() or variable.getOwner() is not self

        self.locals_scope.unregisterClosureVariable(variable)

        self.taken.remove(variable)

        self.code_object.removeFreeVarname(variable.getName())

    def demoteClosureVariable(self, variable):
        assert variable.isLocalVariable()

        self.taken.remove(variable)

        assert variable.getOwner() is not self

        new_variable = Variables.LocalVariable(
            owner=self, variable_name=variable.getName()
        )
        for variable_trace in variable.traces:
            if variable_trace.getOwner() is self:
                new_variable.addTrace(variable_trace)
        new_variable.updateUsageState()

        self.locals_scope.unregisterClosureVariable(variable)
        self.locals_scope.registerProvidedVariable(new_variable)

        updateVariableUsage(
            provider=self, old_variable=variable, new_variable=new_variable
        )

    def hasClosureVariable(self, variable):
        return variable in self.taken

    def getVariableForAssignment(self, variable_name):
        # print("ASS func", self, variable_name)

        if self.hasTakenVariable(variable_name):
            result = self.getTakenVariable(variable_name)
        else:
            result = self.getProvidedVariable(variable_name)

        return result

    def getVariableForReference(self, variable_name):
        # print( "REF func", self, variable_name )

        if self.hasProvidedVariable(variable_name):
            result = self.getProvidedVariable(variable_name)
        else:
            result = self.getClosureVariable(variable_name=variable_name)

            # Remember that we need that closure variable for something, so
            # we don't create it again all the time.
            if not result.isModuleVariable():
                self.locals_scope.registerClosureVariable(result)

            entry_point = self.getEntryPoint()

            # For "exec" containing/star import containing, we raise this exception to indicate
            # that instead of merely a variable, to be assigned, we need to replace with locals
            # dict access.
            if (
                python_version < 0x300
                and not entry_point.isExpressionClassBodyBase()
                and not entry_point.isPythonMainModule()
                and result.isModuleVariable()
                and entry_point.isUnoptimized()
            ):
                raise MaybeLocalVariableUsage

        return result

    def getVariableForClosure(self, variable_name):
        # print( "getVariableForClosure", self.getCodeName(), variable_name, self.isUnoptimized() )

        if self.hasProvidedVariable(variable_name):
            return self.getProvidedVariable(variable_name)

        return self.takeVariableForClosure(variable_name)

    def takeVariableForClosure(self, variable_name):
        result = self.provider.getVariableForClosure(variable_name)
        self.taken.add(result)
        return result

    def createProvidedVariable(self, variable_name):
        # print("createProvidedVariable", self, variable_name)

        assert self.locals_scope, self

        return self.locals_scope.getLocalVariable(
            variable_name=variable_name, owner=self
        )

    def addNonlocalsDeclaration(self, names, user_provided, source_ref):
        """Add a nonlocal declared name.

        This happens during tree building, and is a Python3 only
        feature. We remember the names for later use through the
        function @consumeNonlocalDeclarations
        """
        if self.non_local_declarations is None:
            self.non_local_declarations = []

        self.non_local_declarations.append((names, user_provided, source_ref))

    def consumeNonlocalDeclarations(self):
        """Return the nonlocal declared names for this function.

        There may not be any, which is why we assigned it to
        None originally and now check and return empty tuple
        in that case.
        """

        result = self.non_local_declarations or ()
        self.non_local_declarations = None
        return result

    def getFunctionName(self):
        return self.name

    def getFunctionQualname(self):
        """Function __qualname__ new in CPython3.3

        Should contain some kind of full name descriptions for the closure to
        recognize and will be used for outputs.
        """

        function_name = self.getFunctionName()

        if python_version < 0x300:
            qualname_provider = self.getParentVariableProvider()
        else:
            qualname_provider = self.qualname_provider

        return qualname_provider.getChildQualname(function_name)

    def computeExpression(self, trace_collection):
        assert False

        # Function body is quite irreplaceable.
        return self, None, None

    def mayRaiseException(self, exception_type):
        body = self.subnode_body

        if body is None:
            return False
        else:
            return self.subnode_body.mayRaiseException(exception_type)

    def getFunctionInlineCost(self, values):
        """Cost of inlining this function with given arguments

        Returns: None or integer values, None means don't do it.
        """

        # For overload, pylint: disable=no-self-use,unused-argument
        return None

    def optimizeUnusedClosureVariables(self):
        """Gets called once module is complete, to consider giving up on closure variables."""

        changed = False

        for closure_variable in self.getClosureVariables():
            # Need to take closure of those either way
            if (
                closure_variable.isParameterVariable()
                and self.isExpressionGeneratorObjectBody()
            ):
                continue

            empty = self.trace_collection.hasEmptyTraces(closure_variable)

            if empty:
                changed = True

                self.trace_collection.signalChange(
                    "var_usage",
                    self.source_ref,
                    message="Remove unused closure variable '%s'."
                    % closure_variable.getName(),
                )

                self.removeClosureVariable(closure_variable)

        return changed

    def optimizeVariableReleases(self):
        for parameter_variable in self.getParameterVariablesWithManualRelease():
            read_only = self.trace_collection.hasReadOnlyTraces(parameter_variable)

            if read_only:
                self.trace_collection.signalChange(
                    "var_usage",
                    self.source_ref,
                    message="Schedule removal releases of unassigned parameter variable '%s'."
                    % parameter_variable.getName(),
                )

                self.removeVariableReleases(parameter_variable)


class ExpressionFunctionEntryPointBase(EntryPointMixin, ExpressionFunctionBodyBase):
    __slots__ = ("trace_collection", "code_object", "locals_scope", "auto_release")

    def __init__(
        self, provider, name, code_object, code_prefix, flags, auto_release, source_ref
    ):
        ExpressionFunctionBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            code_prefix=code_prefix,
            flags=flags,
            body=None,
            source_ref=source_ref,
        )

        EntryPointMixin.__init__(self)

        self.code_object = code_object

        provider.getParentModule().addFunction(self)

        if flags is not None and "has_exec" in flags:
            locals_kind = "python2_function_exec"
        else:
            locals_kind = "python_function"

        self.locals_scope = getLocalsDictHandle(
            "locals_%s" % self.getCodeName(), locals_kind, self
        )

        # Automatic parameter variable releases.
        self.auto_release = auto_release or None

    def getDetails(self):
        result = ExpressionFunctionBodyBase.getDetails(self)

        result["auto_release"] = tuple(sorted(self.auto_release or ()))

        return result

    def getCodeObject(self):
        return self.code_object

    def getChildQualname(self, function_name):
        return self.getFunctionQualname() + ".<locals>." + function_name

    def computeFunctionRaw(self, trace_collection):
        from nuitka.optimizations.TraceCollections import (
            TraceCollectionFunction,
        )

        trace_collection = TraceCollectionFunction(
            parent=trace_collection, function_body=self
        )
        old_collection = self.setTraceCollection(trace_collection)

        self.computeFunction(trace_collection)

        trace_collection.updateVariablesFromCollection(old_collection, self.source_ref)

    def computeFunction(self, trace_collection):
        statements_sequence = self.subnode_body

        # TODO: Lift this restriction to only functions here and it code generation.
        if statements_sequence is not None and self.isExpressionFunctionBody():
            if statements_sequence.subnode_statements[0].isStatementReturnNone():
                statements_sequence.finalize()
                self.setChildBody(None)

                statements_sequence = None

        if statements_sequence is not None:
            result = statements_sequence.computeStatementsSequence(
                trace_collection=trace_collection
            )

            if result is not statements_sequence:
                self.setChildBody(result)

    def removeVariableReleases(self, variable):
        assert variable in self.locals_scope.providing.values(), (self, variable)

        if self.auto_release is None:
            self.auto_release = set()

        self.auto_release.add(variable)

    def getParameterVariablesWithManualRelease(self):
        """Return the list of parameter variables that have release statements.

        These are for consideration if these can be dropped, and if so, they
        are releases automatically by function code.
        """
        return tuple(
            variable
            for variable in self.locals_scope.getProvidedVariables()
            if not self.auto_release or variable not in self.auto_release
            if variable.isParameterVariable()
            if variable.getOwner() is self
        )

    def isAutoReleaseVariable(self, variable):
        """Is this variable to be automatically released."""
        return self.auto_release is not None and variable in self.auto_release

    def getFunctionVariablesWithAutoReleases(self):
        """Return the list of function variables that should be released at exit."""
        if self.auto_release is None:
            return ()

        return tuple(
            variable
            for variable in self.locals_scope.getProvidedVariables()
            if variable in self.auto_release
        )

    @staticmethod
    def getConstantReturnValue():
        """Special function that checks if code generation allows to use common C code.

        Notes:
            This is only done for standard functions.

        """
        return False, False


class ExpressionFunctionBody(
    ExpressionNoSideEffectsMixin,
    MarkUnoptimizedFunctionIndicatorMixin,
    ExpressionFunctionEntryPointBase,
):
    # TODO: There should be more special ones than this general type in order to
    # not cover exec ones in the same object.

    kind = "EXPRESSION_FUNCTION_BODY"

    __slots__ = (
        "unoptimized_locals",
        "unqualified_exec",
        "doc",
        "return_exception",
        "needs_creation",
        "needs_direct",
        "cross_module_use",
        "parameters",
    )

    if python_version >= 0x300:
        __slots__ += ("qualname_setup",)

    def __init__(
        self,
        provider,
        name,
        code_object,
        doc,
        parameters,
        flags,
        auto_release,
        code_prefix,
        source_ref,
    ):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider=provider,
            name=name,
            code_object=code_object,
            code_prefix=code_prefix,
            flags=flags,
            auto_release=auto_release,
            source_ref=source_ref,
        )

        MarkUnoptimizedFunctionIndicatorMixin.__init__(self, flags)

        self.doc = doc

        # Indicator if the return value exception might be required.
        self.return_exception = False

        # Indicator if the function needs to be created as a function object.
        self.needs_creation = False

        # Indicator if the function is called directly.
        self.needs_direct = False

        # Indicator if the function is used outside of where it's defined.
        self.cross_module_use = False

        if python_version >= 0x300:
            self.qualname_setup = None

        self.parameters = parameters
        self.parameters.setOwner(self)

        for variable in self.parameters.getAllVariables():
            self.locals_scope.registerProvidedVariable(variable)

    def getDetails(self):
        return {
            "name": self.getFunctionName(),
            "ref_name": self.getCodeName(),
            "parameters": self.getParameters(),
            "code_object": self.code_object,
            "provider": self.provider.getCodeName(),
            "doc": self.doc,
            "flags": self.flags,
        }

    def getDetailsForDisplay(self):
        result = {
            "name": self.getFunctionName(),
            "provider": self.provider.getCodeName(),
            "flags": self.flags,
        }

        result.update(self.parameters.getDetails())

        if self.code_object:
            result.update(self.code_object.getDetails())

        if self.doc is not None:
            result["doc"] = self.doc

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert provider is not None

        parameter_spec_args = {}
        code_object_args = {}
        other_args = {}

        for key, value in args.items():
            if key.startswith("ps_"):
                parameter_spec_args[key] = value
            elif key.startswith("co_"):
                code_object_args[key] = value
            elif key == "code_flags":
                code_object_args["future_spec"] = fromFlags(args["code_flags"])
            else:
                other_args[key] = value

        parameters = ParameterSpec(**parameter_spec_args)
        code_object = CodeObjectSpec(**code_object_args)

        # The empty doc string and no doc string are distinguished by presence. The
        # most common case is going to be not present.
        if "doc" not in other_args:
            other_args["doc"] = None

        return cls(
            provider=provider,
            parameters=parameters,
            code_object=code_object,
            source_ref=source_ref,
            **other_args
        )

    @staticmethod
    def isExpressionFunctionBody():
        return True

    def getParent(self):
        assert False

    def getDoc(self):
        return self.doc

    def getParameters(self):
        return self.parameters

    def needsCreation(self):
        return self.needs_creation

    def markAsNeedsCreation(self):
        self.needs_creation = True

    def needsDirectCall(self):
        return self.needs_direct

    def markAsDirectlyCalled(self):
        self.needs_direct = True

    def isCrossModuleUsed(self):
        return self.cross_module_use

    def markAsCrossModuleUsed(self):
        self.cross_module_use = True

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # TODO: Until we have something to re-order the arguments, we need to
        # skip this. For the immediate need, we avoid this complexity, as a
        # re-ordering will be needed.

        assert False, self

    @staticmethod
    def isCompileTimeConstant():
        # TODO: It's actually pretty much compile time accessible maybe, but that
        # would require extra effort.
        return False

    # TODO: This is an overload that contradicts no side effects, this might be
    # used by outside code, not removed, but we should investigate this.
    def mayRaiseException(self, exception_type):
        body = self.subnode_body

        return body is not None and body.mayRaiseException(exception_type)

    def markAsExceptionReturnValue(self):
        self.return_exception = True

    def needsExceptionReturnValue(self):
        return self.return_exception

    def getConstantReturnValue(self):
        """Special function that checks if code generation allows to use common C code."""
        body = self.subnode_body

        if body is None:
            return True, None

        first_statement = body.subnode_statements[0]

        if first_statement.isStatementReturnConstant():
            constant_value = first_statement.getConstant()

            # TODO: For mutable constants, we could also have something, but it would require an indicator
            # flag to make a deep copy.
            if not isMutable(constant_value):
                return True, constant_value
            else:
                return False, False
        else:
            return False, False


class ExpressionFunctionPureBody(ExpressionFunctionBody):
    kind = "EXPRESSION_FUNCTION_PURE_BODY"

    __slots__ = (
        # These need only one optimization ever.
        "optimization_done",
    )

    def __init__(
        self,
        provider,
        name,
        code_object,
        doc,
        parameters,
        flags,
        auto_release,
        code_prefix,
        source_ref,
    ):
        ExpressionFunctionBody.__init__(
            self,
            provider=provider,
            name=name,
            code_object=code_object,
            doc=doc,
            parameters=parameters,
            flags=flags,
            auto_release=auto_release,
            code_prefix=code_prefix,
            source_ref=source_ref,
        )

        self.optimization_done = False

    def computeFunctionRaw(self, trace_collection):
        if self.optimization_done:
            for function_body in self.trace_collection.getUsedFunctions():
                trace_collection.onUsedFunction(function_body)

            return

        def mySignal(tag, source_ref, change_desc):
            if Options.is_verbose:
                optimization_logger.info(
                    "{source_ref} : {tags} : {message}".format(
                        source_ref=source_ref.getAsString(),
                        tags=tag,
                        message=(
                            change_desc()
                            if inspect.isfunction(change_desc)
                            else change_desc
                        ),
                    )
                )

            tags.add(tag)

        tags = set()

        while 1:
            trace_collection = TraceCollectionPureFunction(function_body=self)
            old_collection = self.setTraceCollection(trace_collection)

            with withChangeIndicationsTo(mySignal):
                self.computeFunction(trace_collection)

            trace_collection.updateVariablesFromCollection(
                old_collection, self.source_ref
            )

            if tags:
                tags.clear()
            else:
                break

        self.optimization_done = True


class ExpressionFunctionPureInlineConstBody(ExpressionFunctionBody):
    kind = "EXPRESSION_FUNCTION_PURE_INLINE_CONST_BODY"

    def getFunctionInlineCost(self, values):
        return 0


# TODO: Function direct call node ought to be here too.


def makeExpressionFunctionCreation(
    function_ref, defaults, kw_defaults, annotations, source_ref
):
    if kw_defaults is not None and kw_defaults.isExpressionConstantDictEmptyRef():
        kw_defaults = None

    assert function_ref.isExpressionFunctionRef()

    return ExpressionFunctionCreation(
        function_ref=function_ref,
        defaults=defaults,
        kw_defaults=kw_defaults,
        annotations=annotations,
        source_ref=source_ref,
    )


class ExpressionFunctionCreationMixin(SideEffectsFromChildrenMixin):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    @staticmethod
    def isExpressionFunctionCreation():
        return True

    def getName(self):
        return self.subnode_function_ref.getName()

    @staticmethod
    def getTypeShape():
        return tshape_function

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for (
            closure_variable
        ) in self.subnode_function_ref.getFunctionBody().getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addNameUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        kw_defaults = self.subnode_kw_defaults
        if kw_defaults is not None:
            kw_defaults.onContentEscapes(trace_collection)

        for default in self.subnode_defaults:
            default.onContentEscapes(trace_collection)

        # TODO: Function body may know something too.
        return self, None, None

    def mayRaiseException(self, exception_type):
        for default in self.subnode_defaults:
            if default.mayRaiseException(exception_type):
                return True

        kw_defaults = self.subnode_kw_defaults

        if kw_defaults is not None and kw_defaults.mayRaiseException(exception_type):
            return True

        annotations = self.subnode_annotations

        if annotations is not None and annotations.mayRaiseException(exception_type):
            return True

        return False

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Until we have something to re-order the keyword arguments, we
        # need to skip this. For the immediate need, we avoid this complexity,
        # as a re-ordering will be needed.
        if call_kw is not None and not call_kw.isExpressionConstantDictEmptyRef():
            return call_node, None, None

        if call_args is None:
            args_tuple = ()
        else:
            assert (
                call_args.isExpressionConstantTupleRef()
                or call_args.isExpressionMakeTuple()
            )

            args_tuple = call_args.getIterationValues()

        function_body = self.subnode_function_ref.getFunctionBody()

        # TODO: Actually the above disables it entirely, as it is at least
        # the empty dictionary node in any case. We will need some enhanced
        # interfaces for "matchCall" to work on.

        call_spec = function_body.getParameters()

        try:
            args_dict = matchCall(
                func_name=self.getName(),
                args=call_spec.getArgumentNames(),
                kw_only_args=call_spec.getKwOnlyParameterNames(),
                star_list_arg=call_spec.getStarListArgumentName(),
                star_dict_arg=call_spec.getStarDictArgumentName(),
                star_list_single_arg=False,
                num_defaults=call_spec.getDefaultCount(),
                num_pos_only=call_spec.getPosOnlyParameterCount(),
                positional=args_tuple,
                pairs=(),
            )

            values = [args_dict[name] for name in call_spec.getParameterNames()]

            # TODO: Not handling default values either yet.
            if None in values:
                return call_node, None, None

            # TODO: This is probably something that the matchCall ought to do
            # for us, but that will need cleanups. Also these functions and
            # nodes ought to work with ordered dictionaries maybe.
            if call_spec.getStarDictArgumentName():
                values[-1] = makeDictCreationOrConstant2(
                    keys=[value[0] for value in values[-1]],
                    values=[value[1] for value in values[-1]],
                    source_ref=call_node.source_ref,
                )

                star_list_offset = -2
            else:
                star_list_offset = -1

            if call_spec.getStarListArgumentName():
                values[star_list_offset] = makeExpressionMakeTupleOrConstant(
                    elements=values[star_list_offset],
                    user_provided=False,
                    source_ref=call_node.source_ref,
                )

            result = makeExpressionFunctionCall(
                function=self.makeClone(),
                values=values,
                source_ref=call_node.source_ref,
            )

            return (
                result,
                "new_statements",  # TODO: More appropriate tag maybe.
                """\
Replaced call to created function body '%s' with direct function call."""
                % self.getName(),
            )

        except TooManyArguments as e:
            result = wrapExpressionWithSideEffects(
                new_node=makeRaiseExceptionReplacementExpressionFromInstance(
                    expression=call_node, exception=e.getRealException()
                ),
                old_node=call_node,
                side_effects=call_node.extractSideEffectsPreCall(),
            )

            return (
                result,
                "new_raise",  # TODO: More appropriate tag maybe.
                """Replaced call to created function body '%s' to argument \
error"""
                % self.getName(),
            )

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


class ExpressionFunctionCreationOld(
    ExpressionFunctionCreationMixin,
    ChildrenHavingKwDefaultsOptionalDefaultsTupleAnnotationsOptionalFunctionRefMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_FUNCTION_CREATION_OLD"

    python_version_spec = "< 0x300"
    # Note: The order of evaluation for these is a bit unexpected, but
    # true. Keyword defaults go first, then normal defaults, and annotations of
    # all kinds go last.

    # A bug of CPython3.x was not fixed before version 3.4, this is to allow
    # code generation to detect which one is used. bugs.python.org/issue16967
    kw_defaults_before_defaults = True

    named_children = (
        "kw_defaults|optional",
        "defaults|tuple",
        "annotations|optional",
        "function_ref",
    )

    __slots__ = ("variable_closure_traces",)

    def __init__(self, kw_defaults, defaults, annotations, function_ref, source_ref):
        ChildrenHavingKwDefaultsOptionalDefaultsTupleAnnotationsOptionalFunctionRefMixin.__init__(
            self,
            kw_defaults=kw_defaults,
            defaults=defaults,
            annotations=annotations,
            function_ref=function_ref,
        )

        ExpressionBase.__init__(self, source_ref)

        self.variable_closure_traces = None


class ExpressionFunctionCreation(
    ExpressionFunctionCreationMixin,
    ChildrenHavingDefaultsTupleKwDefaultsOptionalAnnotationsOptionalFunctionRefMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_FUNCTION_CREATION"

    python_version_spec = ">= 0x340"

    # A bug of CPython3.x was not fixed before version 3.4, this is to allow
    # code generation to detect which one is used. bugs.python.org/issue16967
    kw_defaults_before_defaults = False

    named_children = (
        "defaults|tuple",
        "kw_defaults|optional",
        "annotations|optional",
        "function_ref",
    )

    __slots__ = ("variable_closure_traces",)

    def __init__(self, defaults, kw_defaults, annotations, function_ref, source_ref):
        ChildrenHavingDefaultsTupleKwDefaultsOptionalAnnotationsOptionalFunctionRefMixin.__init__(
            self,
            kw_defaults=kw_defaults,
            defaults=defaults,
            annotations=annotations,
            function_ref=function_ref,
        )

        ExpressionBase.__init__(self, source_ref)

        self.variable_closure_traces = None


if python_version < 0x300:
    ExpressionFunctionCreation = ExpressionFunctionCreationOld


class ExpressionFunctionRef(ExpressionNoSideEffectsMixin, ExpressionBase):
    kind = "EXPRESSION_FUNCTION_REF"

    __slots__ = "function_body", "code_name", "function_source"

    def __init__(self, source_ref, function_body=None, code_name=None):
        assert function_body is not None or code_name is not None
        assert code_name != "None"

        ExpressionBase.__init__(self, source_ref)

        self.function_body = function_body
        self.code_name = code_name
        self.function_source = None

    def finalize(self):
        del self.parent
        del self.function_body
        del self.function_source

    def getName(self):
        return self.function_body.getName()

    def getDetails(self):
        return {"function_body": self.function_body}

    def getDetailsForDisplay(self):
        return {"code_name": self.getFunctionBody().getCodeName()}

    def getFunctionBody(self):
        if self.function_body is None:
            module_code_name, _ = self.code_name.split("$$$", 1)

            from nuitka.ModuleRegistry import getModuleFromCodeName

            module = getModuleFromCodeName(module_code_name)

            self.function_body = module.getFunctionFromCodeName(self.code_name)

        return self.function_body

    def computeExpressionRaw(self, trace_collection):
        trace_collection.onUsedFunction(self.getFunctionBody())

        # TODO: Function after collection may now know something.
        return self, None, None

    def getFunctionSourceCode(self):
        if self.function_source is None:
            try:
                lines = readSourceLines(self.getFunctionBody().source_ref)

                # This needs to match "inspect.findsource".
                pat = re.compile(
                    r"^(\s*def\s)|(\s*async\s+def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)"
                )

                line_number = self.source_ref.line - 1

                while line_number > 0:
                    line = lines[line_number]

                    if pat.match(line):
                        break

                    line_number = line_number - 1

                self.function_source = (
                    "".join(inspect.getblock(lines[line_number:])),
                    line_number,
                )
            except Exception:
                printError(
                    "Problem with retrieving source code of '%s' at %s"
                    % (self.getFunctionSuperQualifiedName(), self.source_ref)
                )
                raise

        return self.function_source

    def getFunctionSuperQualifiedName(self):
        return "%s.%s" % (
            self.getParentModule().getFullName(),
            self.getFunctionBody().getFunctionQualname(),
        )


def makeExpressionFunctionCall(function, values, source_ref):
    assert function.isExpressionFunctionCreation()

    return ExpressionFunctionCall(
        function=function, values=tuple(values), source_ref=source_ref
    )


class ExpressionFunctionCall(ChildrenHavingFunctionValuesTupleMixin, ExpressionBase):
    """Shared function call.

    This is for calling created function bodies with multiple users. Not
    clear if such a thing should exist. But what this will do is to have
    respect for the fact that there are multiple such calls.
    """

    kind = "EXPRESSION_FUNCTION_CALL"

    __slots__ = ("variable_closure_traces",)

    named_children = ("function", "values|tuple")

    def __init__(self, function, values, source_ref):
        ChildrenHavingFunctionValuesTupleMixin.__init__(
            self,
            function=function,
            values=values,
        )

        ExpressionBase.__init__(self, source_ref)

        self.variable_closure_traces = None

    def computeExpression(self, trace_collection):
        function = self.subnode_function
        function_body = function.subnode_function_ref.getFunctionBody()

        if function_body.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        values = self.subnode_values

        for value in values:
            value.onContentEscapes(trace_collection)

        # Ask for function for its cost.
        cost = function_body.getFunctionInlineCost(values)

        if cost is not None and cost < 50:
            from nuitka.optimizations.FunctionInlining import (
                convertFunctionCallToOutline,
            )

            result = convertFunctionCallToOutline(
                provider=self.getParentVariableProvider(),
                function_body=function_body,
                values=values,
                call_source_ref=self.source_ref,
            )

            return (
                result,
                "new_statements",
                lambda: "Function call to '%s' in-lined." % function_body.getCodeName(),
            )

        self.variable_closure_traces = []

        for closure_variable in function_body.getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addNameUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        return self, None, None

    def mayRaiseException(self, exception_type):
        function = self.subnode_function

        if function.subnode_function_ref.getFunctionBody().mayRaiseException(
            exception_type
        ):
            return True

        values = self.subnode_values

        for value in values:
            if value.mayRaiseException(exception_type):
                return True

        return False

    def getClosureVariableVersions(self):
        return self.variable_closure_traces

    def onContentEscapes(self, trace_collection):
        for value in self.subnode_values:
            value.onContentEscapes(trace_collection)


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
