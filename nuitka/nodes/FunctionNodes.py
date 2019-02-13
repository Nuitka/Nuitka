#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options, Variables
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import ParameterSpec, TooManyArguments, matchCall
from nuitka.tree.Extractions import updateVariableUsage

from .Checkers import checkStatementsSequenceOrNone
from .CodeObjectSpecs import CodeObjectSpec
from .ExpressionBases import (
    CompileTimeConstantExpressionBase,
    ExpressionBase,
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .FutureSpecs import fromFlags
from .IndicatorMixins import EntryPointMixin, MarkUnoptimizedFunctionIndicatorMixin
from .LocalsScopes import getLocalsDictHandle, setLocalsDictType
from .NodeBases import (
    ClosureGiverNodeMixin,
    ClosureTakerMixin,
    SideEffectsFromChildrenMixin,
)
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseExceptionReplacementExpressionFromInstance,
    wrapExpressionWithSideEffects,
)


class MaybeLocalVariableUsage(Exception):
    pass


class ExpressionFunctionBodyBase(
    ClosureTakerMixin, ClosureGiverNodeMixin, ExpressionChildHavingBase
):

    named_child = "body"

    checker = checkStatementsSequenceOrNone

    def __init__(self, provider, name, body, code_prefix, flags, source_ref):
        while provider.isExpressionOutlineBody():
            provider = provider.getParentVariableProvider()

        ExpressionChildHavingBase.__init__(
            self,
            value=body,  # Might be None initially in some cases.
            source_ref=source_ref,
        )

        ClosureTakerMixin.__init__(self, provider=provider)

        ClosureGiverNodeMixin.__init__(self, name=name, code_prefix=code_prefix)

        # Special things, "has_super" indicates presence of "super" in variable
        # usage, which modifies some behaviors.
        self.flags = flags or None

        # Hack: This allows some APIs to work although this is not yet
        # officially a child yet. Important during building.
        self.parent = provider

        # Python3.4: Might be overridden by global statement on the class name.
        # TODO: Make this class only code.
        if python_version >= 340:
            self.qualname_provider = provider

        # Non-local declarations.
        self.non_local_declarations = []

    @staticmethod
    def isExpressionFunctionBodyBase():
        return True

    def getEntryPoint(self):
        """ Entry point for code.

            Normally ourselves. Only outlines will refer to their parent which
            technically owns them.

        """

        return self

    def getContainingClassDictCreation(self):
        current = self

        while not current.isCompiledPythonModule():
            if current.isExpressionClassBody():
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
        """ Early closure taking means immediate binding of references.

        Normally it's good to lookup name references immediately, but not for
        functions. In case of a function body it is not allowed to do that,
        because a later assignment needs to be queried first. Nodes need to
        indicate via this if they would like to resolve references at the same
        time as assignments.
        """

        return False

    def hasVariableName(self, variable_name):
        return variable_name in self.providing or variable_name in self.temp_variables

    def getVariables(self):
        return self.providing.values()

    def getLocalVariables(self):
        return [
            variable
            for variable in self.providing.values()
            if variable.isLocalVariable()
        ]

    def getLocalVariableNames(self):
        return [
            variable.getName()
            for variable in self.providing.values()
            if variable.isLocalVariable()
        ]

    def getUserLocalVariables(self):
        return tuple(
            variable
            for variable in self.providing.values()
            if variable.isLocalVariable() and not variable.isParameterVariable()
            if variable.getOwner() is self
        )

    def getOutlineLocalVariables(self):
        outlines = self.getTraceCollection().getOutlineFunctions()

        if outlines is None:
            return ()

        result = []

        for outline in outlines:
            result.extend(outline.getUserLocalVariables())

        return tuple(result)

    def removeClosureVariable(self, variable):
        # Do not remove parameter variables of ours.
        assert not variable.isParameterVariable() or variable.getOwner() is not self

        variable_name = variable.getName()

        if variable_name in self.providing:
            del self.providing[variable.getName()]

        self.taken.remove(variable)

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

        self.providing[variable.getName()] = new_variable

        updateVariableUsage(
            provider=self, old_variable=variable, new_variable=new_variable
        )

    def hasClosureVariable(self, variable):
        return variable in self.taken

    def removeUserVariable(self, variable):
        assert variable in self.providing.values(), (self, self.providing, variable)

        del self.providing[variable.getName()]

        assert not variable.isParameterVariable() or variable.getOwner() is not self

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
                self.registerProvidedVariable(result)

            entry_point = self.getEntryPoint()

            # For "exec" containing/star import containing, we raise this exception to indicate
            # that instead of merely a variable, to be assigned, we need to replace with locals
            # dict access.
            if (
                python_version < 300
                and not entry_point.isExpressionClassBody()
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

        return Variables.LocalVariable(owner=self, variable_name=variable_name)

    def addNonlocalsDeclaration(self, names, source_ref):
        self.non_local_declarations.append((names, source_ref))

    def consumeNonlocalDeclarations(self):
        result = self.non_local_declarations
        self.non_local_declarations = ()
        return result

    def getFunctionName(self):
        return self.name

    def getFunctionQualname(self):
        """ Function __qualname__ new in CPython3.3

        Should contain some kind of full name descriptions for the closure to
        recognize and will be used for outputs.
        """

        function_name = self.getFunctionName()

        if python_version < 340:
            provider = self.getParentVariableProvider()
        else:
            provider = self.qualname_provider

        if provider.isCompiledPythonModule():
            return function_name
        elif provider.isExpressionClassBody():
            return provider.getFunctionQualname() + "." + function_name
        else:
            return provider.getFunctionQualname() + ".<locals>." + function_name

    def computeExpression(self, trace_collection):
        assert False

        # Function body is quite irreplaceable.
        return self, None, None

    def mayRaiseException(self, exception_type):
        body = self.getBody()

        if body is None:
            return False
        else:
            return self.getBody().mayRaiseException(exception_type)

    getBody = ExpressionChildHavingBase.childGetter("body")
    setBody = ExpressionChildHavingBase.childSetter("body")


class ExpressionFunctionEntryPointBase(EntryPointMixin, ExpressionFunctionBodyBase):
    def __init__(self, provider, name, code_object, code_prefix, flags, source_ref):
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

        if "has_exec" in flags or python_version >= 300:
            self.locals_dict_name = "locals_%s" % (self.getCodeName(),)

            if "has_exec" in flags:
                setLocalsDictType(self.locals_dict_name, "python2_function_exec")
            else:
                setLocalsDictType(self.locals_dict_name, "python3_function")

        else:
            # TODO: There should be a locals scope for non-dict/mapping too.
            self.locals_dict_name = None

    def getFunctionLocalsScope(self):
        if self.locals_dict_name is None:
            return None
        else:
            return getLocalsDictHandle(self.locals_dict_name)

    def getCodeObject(self):
        return self.code_object

    def computeFunctionRaw(self, trace_collection):
        from nuitka.optimizations.TraceCollections import TraceCollectionFunction

        trace_collection = TraceCollectionFunction(
            parent=trace_collection, function_body=self
        )
        old_collection = self.setTraceCollection(trace_collection)

        self.computeFunction(trace_collection)

        trace_collection.updateVariablesFromCollection(old_collection)

    def computeFunction(self, trace_collection):
        statements_sequence = self.getBody()

        if statements_sequence is not None and not statements_sequence.getStatements():
            statements_sequence.setStatements(None)
            statements_sequence = None

        if statements_sequence is not None:
            result = statements_sequence.computeStatementsSequence(
                trace_collection=trace_collection
            )

            if result is not statements_sequence:
                self.setBody(result)


class ExpressionFunctionBody(
    MarkUnoptimizedFunctionIndicatorMixin, ExpressionFunctionEntryPointBase
):
    kind = "EXPRESSION_FUNCTION_BODY"

    named_children = ("body",)

    checkers = {
        # TODO: Is "None" really an allowed value.
        "body": checkStatementsSequenceOrNone
    }

    if python_version >= 340:
        qualname_setup = None

    def __init__(self, provider, name, code_object, doc, parameters, flags, source_ref):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider=provider,
            name=name,
            code_object=code_object,
            code_prefix="function",
            flags=flags,
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

        self.parameters = parameters
        self.parameters.setOwner(self)

        for variable in self.parameters.getAllVariables():
            self.registerProvidedVariable(variable)

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

    def getDetail(self):
        return "named %s with %s" % (self.getFunctionName(), self.parameters)

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

    def isCompileTimeConstant(self):
        # TODO: It's actually pretty much compile time accessible maybe.
        return None

    def mayHaveSideEffects(self):
        # The function definition has no side effects, calculating the defaults
        # would be, but that is done outside of this.
        return False

    def mayRaiseException(self, exception_type):
        return self.getBody().mayRaiseException(exception_type)

    def markAsExceptionReturnValue(self):
        self.return_exception = True

    def needsExceptionReturnValue(self):
        return self.return_exception


def convertNoneConstantOrEmptyDictToNone(node):
    if node is None:
        return None
    elif node.isExpressionConstantRef() and node.getConstant() is None:
        return None
    elif node.isExpressionConstantRef() and node.getConstant() == {}:
        return None
    else:
        return node


# TODO: Function direct call node ought to be here too.


class ExpressionFunctionCreation(
    SideEffectsFromChildrenMixin, ExpressionChildrenHavingBase
):

    kind = "EXPRESSION_FUNCTION_CREATION"

    # Note: The order of evaluation for these is a bit unexpected, but
    # true. Keyword defaults go first, then normal defaults, and annotations of
    # all kinds go last.

    # A bug of CPython3.x not fixed before version 3.4, see bugs.python.org/issue16967
    kw_defaults_before_defaults = python_version < 340

    if kw_defaults_before_defaults:
        named_children = ("kw_defaults", "defaults", "annotations", "function_ref")
    else:
        named_children = ("defaults", "kw_defaults", "annotations", "function_ref")

    checkers = {"kw_defaults": convertNoneConstantOrEmptyDictToNone}

    def __init__(self, function_ref, defaults, kw_defaults, annotations, source_ref):
        assert kw_defaults is None or kw_defaults.isExpression()
        assert annotations is None or annotations.isExpression()
        assert function_ref.isExpressionFunctionRef()

        ExpressionChildrenHavingBase.__init__(
            self,
            values={
                "function_ref": function_ref,
                "defaults": tuple(defaults),
                "kw_defaults": kw_defaults,
                "annotations": annotations,
            },
            source_ref=source_ref,
        )

        self.variable_closure_traces = None

    def getName(self):
        return self.getFunctionRef().getName()

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for closure_variable in (
            self.getFunctionRef().getFunctionBody().getClosureVariables()
        ):
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addClosureUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        # TODO: Function body may know something too.
        return self, None, None

    getFunctionRef = ExpressionChildrenHavingBase.childGetter("function_ref")
    getDefaults = ExpressionChildrenHavingBase.childGetter("defaults")
    getKwDefaults = ExpressionChildrenHavingBase.childGetter("kw_defaults")
    getAnnotations = ExpressionChildrenHavingBase.childGetter("annotations")

    def mayRaiseException(self, exception_type):
        for default in self.getDefaults():
            if default.mayRaiseException(exception_type):
                return True

        kw_defaults = self.getKwDefaults()

        if kw_defaults is not None and kw_defaults.mayRaiseException(exception_type):
            return True

        annotations = self.getAnnotations()

        if annotations is not None and annotations.mayRaiseException(exception_type):
            return True

        return False

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):

        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Until we have something to re-order the keyword arguments, we
        # need to skip this. For the immediate need, we avoid this complexity,
        # as a re-ordering will be needed.
        if call_kw is not None and (
            not call_kw.isExpressionConstantRef() or call_kw.getConstant() != {}
        ):
            return call_node, None, None

        if call_kw is not None:
            return call_node, None, None

        if call_args is None:
            args_tuple = ()
        else:
            assert (
                call_args.isExpressionConstantRef() or call_args.isExpressionMakeTuple()
            )

            args_tuple = call_args.getIterationValues()

        function_body = self.getFunctionRef().getFunctionBody()

        # TODO: Actually the above disables it entirely, as it is at least
        # the empty dictionary node in any case. We will need some enhanced
        # interfaces for "matchCall" to work on.

        call_spec = function_body.getParameters()

        try:
            args_dict = matchCall(
                func_name=self.getName(),
                args=call_spec.getArgumentNames(),
                star_list_arg=call_spec.getStarListArgumentName(),
                star_dict_arg=call_spec.getStarDictArgumentName(),
                num_defaults=call_spec.getDefaultCount(),
                num_posonly=call_spec.getPositionalOnlyCount(),
                positional=args_tuple,
                pairs=(),
            )

            values = [args_dict[name] for name in call_spec.getParameterNames()]

            result = ExpressionFunctionCall(
                function=self, values=values, source_ref=call_node.getSourceReference()
            )

            return (
                result,
                "new_statements",  # TODO: More appropriate tag maybe.
                """\
Replaced call to created function body '%s' with direct \
function call."""
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

    def getCallCost(self, values):
        # TODO: Ought to use values. If they are all constant, how about we
        # assume no cost, pylint: disable=unused-argument

        function_body = self.getFunctionRef().getFunctionBody()

        if function_body.isExpressionClassBody():
            if function_body.getBody().getStatements()[0].isStatementReturn():
                return 0

            return None

        if True or not Options.isExperimental("function_inlining"):
            return None

        if function_body.isExpressionGeneratorObjectBody():
            # TODO: That's not even allowed, is it?
            assert False

            return None

        # TODO: Lying for the demo, this is too limiting, but needs frames to
        # be allowed twice in a context.
        if function_body.mayRaiseException(BaseException):
            return 60

        return 20

    def createOutlineFromCall(self, provider, values):
        from nuitka.optimizations.FunctionInlining import convertFunctionCallToOutline

        return convertFunctionCallToOutline(
            provider=provider, function_ref=self.getFunctionRef(), values=values
        )

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


class ExpressionFunctionRef(ExpressionBase):
    kind = "EXPRESSION_FUNCTION_REF"

    __slots__ = "function_body", "code_name"

    def __init__(self, source_ref, function_body=None, code_name=None):
        assert function_body is not None or code_name is not None
        assert code_name != "None"

        ExpressionBase.__init__(self, source_ref=source_ref)

        self.function_body = function_body
        self.code_name = code_name

    def finalize(self):
        del self.parent
        del self.function_body

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
        function_body = self.getFunctionBody()

        owning_module = function_body.getParentModule()

        # Make sure the owning module is added to the used set. This is most
        # important for helper functions, or modules, which otherwise have
        # become unused.
        from nuitka.ModuleRegistry import addUsedModule

        addUsedModule(owning_module)

        needs_visit = owning_module.addUsedFunction(function_body)

        if needs_visit:
            function_body.computeFunctionRaw(trace_collection)

        # TODO: Function collection may now know something.
        return self, None, None

    def mayHaveSideEffects(self):
        # Using a function has no side effects.
        return False

    def mayRaiseException(self, exception_type):
        return False


class ExpressionFunctionCall(ExpressionChildrenHavingBase):
    """ Shared function call.

        This is for calling created function bodies with multiple users. Not
        clear if such a thing should exist. But what this will do is to have
        respect for the fact that there are multiple such calls.
    """

    kind = "EXPRESSION_FUNCTION_CALL"

    named_children = ("function", "values")

    def __init__(self, function, values, source_ref):
        assert function.isExpressionFunctionCreation()

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"function": function, "values": tuple(values)},
            source_ref=source_ref,
        )

        self.variable_closure_traces = None

    def computeExpression(self, trace_collection):
        function = self.getFunction()

        values = self.getArgumentValues()

        # TODO: This needs some design.
        cost = function.getCallCost(values)

        function_body = function.getFunctionRef().getFunctionBody()

        if function_body.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if cost is not None and cost < 50:
            result = function.createOutlineFromCall(
                provider=self.getParentVariableProvider(), values=values
            )

            return (
                result,
                "new_statements",
                "Function call to '%s' in-lined." % function_body.getCodeName(),
            )

        self.variable_closure_traces = []

        for closure_variable in function_body.getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addClosureUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        return self, None, None

    def mayRaiseException(self, exception_type):
        function = self.getFunction()

        if (
            function.getFunctionRef()
            .getFunctionBody()
            .mayRaiseException(exception_type)
        ):
            return True

        values = self.getArgumentValues()

        for value in values:
            if value.mayRaiseException(exception_type):
                return True

        return False

    getFunction = ExpressionChildrenHavingBase.childGetter("function")
    getArgumentValues = ExpressionChildrenHavingBase.childGetter("values")

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


# Needed for Python3.3 and higher
class ExpressionFunctionQualnameRef(CompileTimeConstantExpressionBase):
    kind = "EXPRESSION_FUNCTION_QUALNAME_REF"

    __slots__ = ("function_body",)

    def __init__(self, function_body, source_ref):
        CompileTimeConstantExpressionBase.__init__(self, source_ref=source_ref)

        self.function_body = function_body

    def finalize(self):
        del self.parent
        del self.function_body

    def computeExpressionRaw(self, trace_collection):
        result = makeConstantReplacementNode(
            node=self, constant=self.function_body.getFunctionQualname()
        )

        return (
            result,
            "new_constant",
            "Executed '__qualname__' resolution to '%s'."
            % self.function_body.getFunctionQualname(),
        )
