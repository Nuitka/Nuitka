#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Trace collection (also often still referred to as constraint collection).

At the core of value propagation there is the collection of constraints that
allow to propagate knowledge forward or not.

This is about collecting these constraints and to manage them.
"""

import contextlib
from logging import debug

from nuitka import Tracing, Variables
from nuitka.__past__ import iterItems  # Python3 compatibility.
from nuitka.containers.oset import OrderedSet
from nuitka.importing.ImportCache import (
    getImportedModuleByName,
    isImportedModuleByName
)
from nuitka.ModuleRegistry import addUsedModule
from nuitka.nodes.NodeMakingHelpers import getComputationResult
from nuitka.PythonVersions import python_version
from nuitka.utils.InstanceCounters import counted_del, counted_init

from .VariableTraces import (
    VariableTraceAssign,
    VariableTraceInit,
    VariableTraceLoopMerge,
    VariableTraceMerge,
    VariableTraceUninit,
    VariableTraceUnknown
)

signalChange = None


class CollectionTracingMixin(object):
    def __init__(self):
        # For functions, when we are in here, the currently active one,
        self.variable_actives = {}

    def getVariableCurrentTrace(self, variable):
        return self.getVariableTrace(
            variable = variable,
            version  = self.getCurrentVariableVersion(variable)
        )

    def markCurrentVariableTrace(self, variable, version):
        self.variable_actives[variable] = version

    def getCurrentVariableVersion(self, variable):
        try:
            return self.variable_actives[variable]
        except KeyError:
            # Initialize variables on the fly.
            if not self.hasVariableTrace(variable, 0):
                self.initVariable(variable)

            self.markCurrentVariableTrace(variable, 0)

            return self.variable_actives[variable]

    def getActiveVariables(self):
        return self.variable_actives.keys()

    def markActiveVariableAsUnknown(self, variable):
        current = self.getVariableCurrentTrace(
            variable = variable,
        )

        if not current.isUnknownTrace():
            version = variable.allocateTargetNumber()

            self.addVariableTrace(
                variable = variable,
                version  = version,
                trace    = VariableTraceUnknown(
                    owner    = self.owner,
                    variable = variable,
                    version  = version,
                    previous = current
                )
            )

            self.markCurrentVariableTrace(variable, version)

    def markActiveVariableAsLoopMerge(self, variable):
        current = self.getVariableCurrentTrace(
            variable = variable,
        )

        version = variable.allocateTargetNumber()

        result = VariableTraceLoopMerge(
            variable = variable,
            version  = version,
            previous = current
        )

        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = result
        )

        self.markCurrentVariableTrace(variable, version)

        return result

    def markActiveVariablesAsUnknown(self):
        for variable in self.getActiveVariables():
            if variable.isTempVariable():
                continue

            self.markActiveVariableAsUnknown(variable)


class CollectionStartpointMixin(object):
    # Many things are traces, pylint: disable=too-many-instance-attributes

    def __init__(self):
        # Variable assignments performed in here, last issued number, only used
        # to determine the next number that should be used for a new assignment.
        self.variable_versions = {}

        # The full trace of a variable with a version for the function or module
        # this is.
        self.variable_traces = {}

        self.break_collections = None
        self.continue_collections = None
        self.return_collections = None
        self.exception_collections = None

        self.outline_functions = None

        self.locals_dict_shape = None
        # TODO: This is really a value shape, isn't it.
        self.locals_dict = None

        # Dictionary of local dicts, e.g. multiple classes, nested or not, can
        # produce that situation. The key is the locals_scope object of the
        # locals dictionary. This stores the shape and the value traces for
        # the keys.
        self.locals_dict_values = {}

        self.locals_dict_shapes = {}

    def getLoopBreakCollections(self):
        return self.break_collections

    def onLoopBreak(self, collection = None):
        if collection is None:
            collection = self

        self.break_collections.append(
            TraceCollectionBranch(
                parent = collection,
                name   = "loop break"
            )
        )

    def getLoopContinueCollections(self):
        return self.continue_collections

    def onLoopContinue(self, collection = None):
        if collection is None:
            collection = self

        self.continue_collections.append(
            TraceCollectionBranch(
                parent = collection,
                name   = "loop continue"
            )
        )

    def onFunctionReturn(self, collection = None):
        if collection is None:
            collection = self

        if self.return_collections is not None:
            self.return_collections.append(
                TraceCollectionBranch(
                    parent = collection,
                    name   = "return"
                )
            )

    def onExceptionRaiseExit(self, raisable_exceptions, collection = None):
        # TODO: We might want to track per exception, pylint: disable=unused-argument

        if collection is None:
            collection = self

        if self.exception_collections is not None:
            self.exception_collections.append(
                TraceCollectionBranch(
                    parent = collection,
                    name   = "exception"
                )
            )

    def getFunctionReturnCollections(self):
        return self.return_collections

    def getExceptionRaiseCollections(self):
        return self.exception_collections

    def hasVariableTrace(self, variable, version):
        return (variable, version) in self.variable_traces

    def getVariableTrace(self, variable, version):
        return self.variable_traces[(variable, version)]

    def getVariableTraces(self, variable):
        result = []

        for key, variable_trace in iterItems(self.variable_traces):
            candidate = key[0]

            if variable is candidate:
                result.append(variable_trace)

        return result

    def getVariableTracesAll(self):
        return self.variable_traces

    def addVariableTrace(self, variable, version, trace):
        key = variable, version

        assert key not in self.variable_traces, (key, self)
        self.variable_traces[key] = trace

    def addVariableMergeMultipleTrace(self, variable, traces):
        version = variable.allocateTargetNumber()

        trace_merge = VariableTraceMerge(
            variable = variable,
            version  = version,
            traces   = traces
        )

        self.addVariableTrace(variable, version, trace_merge)

        return version
#         return version, trace_merge

    def dumpTraces(self):
        debug("Constraint collection state: %s", self)
        for _variable_desc, variable_trace in sorted(iterItems(self.variable_traces)):

            # debug( "%r: %r", variable_trace )
            variable_trace.dump()

    def dumpActiveTraces(self):
        Tracing.printSeparator()
        Tracing.printLine("Active are:")
        for variable, _version in sorted(self.variable_actives.iteritems()):
            self.getVariableCurrentTrace(variable).dump()

        Tracing.printSeparator()

    def initVariableUnknown(self, variable):
        trace = VariableTraceUnknown(
            owner    = self.owner,
            variable = variable,
            version  = 0,
            previous = None
        )

        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = trace
        )

        return trace

    def _initVariableInit(self, variable):
        trace = VariableTraceInit(
            owner    = self.owner,
            variable = variable,
            version  = 0
        )

        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = trace
        )

        return trace

    def _initVariableUninit(self, variable):
        trace = VariableTraceUninit(
            owner    = self.owner,
            variable = variable,
            version  = 0,
            previous = None
        )

        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = trace
        )

        return trace

    def updateVariablesFromCollection(self, old_collection):
        Variables.updateVariablesFromCollection(old_collection, self)

    @contextlib.contextmanager
    def makeLocalsDictContext(self, locals_scope):
        old_locals_dict = self.locals_dict
        old_locals_dict_shape = self.locals_dict_shape

        self.locals_dict_shape = locals_scope.getTypeShape()
        self.locals_dict = {}

        yield

        self.locals_dict = old_locals_dict
        self.locals_dict_shape = old_locals_dict_shape

    def setLocalsDictShape(self, locals_scope, locals_dict_shape):
        self.locals_dict_shapes[locals_scope] = locals_dict_shape
        self.locals_dict_values[locals_scope] = {}

        self.locals_dict_shape = locals_dict_shape

    def getLocalsDictShape(self, locals_scope):
        return self.locals_dict_shapes[locals_scope]

    @contextlib.contextmanager
    def makeAbortStackContext(self, catch_breaks, catch_continues,
                              catch_returns, catch_exceptions):
        if catch_breaks:
            old_break_collections = self.break_collections
            self.break_collections = []
        if catch_continues:
            old_continue_collections = self.continue_collections
            self.continue_collections = []
        if catch_returns:
            old_return_collections = self.return_collections
            self.return_collections = []
        if catch_exceptions:
            old_exception_collections = self.exception_collections
            self.exception_collections = []

        yield

        if catch_breaks:
            self.break_collections = old_break_collections
        if catch_continues:
            self.continue_collections = old_continue_collections
        if catch_returns:
            self.return_collections = old_return_collections
        if catch_exceptions:
            self.exception_collections = old_exception_collections

    def initVariable(self, variable):
        if variable.isParameterVariable():
            result = self._initVariableInit(variable)
        elif variable.isLocalVariable():
            result = self._initVariableUninit(variable)
        elif variable.isModuleVariable():
            result = self.initVariableUnknown(variable)
        elif variable.isTempVariable():
            result = self._initVariableUninit(variable)
        else:
            assert False, variable

        assert result.getVariable() is variable

        return result

    def addOutlineFunction(self, outline):
        if self.outline_functions is None:
            self.outline_functions = [outline]
        else:
            self.outline_functions.append(outline)

    def getOutlineFunctions(self):
        return self.outline_functions

    def onLocalsDictSet(self, variable_name, value):
        # No real tracing of values yet, pylint: disable=unused-argument

        self.locals_dict[variable_name] = None

        # TODO: For Python2 we know for a fact that it cannot happen, but for
        # Python3 we could check current dictionary shape.
        may_raise = python_version >= 300

        if may_raise:
            self.onExceptionRaiseExit(BaseException)

        return may_raise

    def onLocalsDictDel(self, variable_name):
        self.locals_dict[variable_name] = None

        # TODO: For Python2 we know for a fact that it cannot happen, but for
        # Python3 we could check current dictionary shape.
        may_raise = python_version >= 300

        if may_raise:
            self.onExceptionRaiseExit(BaseException)

        return may_raise

    def onLocalsDictGet(self, variable_name):
        if variable_name not in self.locals_dict and None not in self.locals_dict:
            return False

        return None

    def onLocalsDictEscaped(self):
        if self.locals_dict is not None:
            self.locals_dict[None] = None



class TraceCollectionBase(CollectionTracingMixin):
    __del__ = counted_del()

    @counted_init
    def __init__(self, owner, name, parent):
        CollectionTracingMixin.__init__(self)

        self.owner = owner
        self.parent = parent
        self.name = name

        # Value state extra information per node.
        self.value_states = {}

    def __repr__(self):
        return "<%s for %s at 0x%x>" % (
            self.__class__.__name__,
            self.name,
            id(self)
        )

    @staticmethod
    def signalChange(tags, source_ref, message):
        # This is monkey patched from another module.
        signalChange(tags, source_ref, message)

    def onUsedModule(self, module_name):
        return self.parent.onUsedModule(module_name)

    @staticmethod
    def mustAlias(a, b):
        if a.isExpressionVariableRef() and b.isExpressionVariableRef():
            return a.getVariable() is b.getVariable()

        return False

    @staticmethod
    def mustNotAlias(a, b):
        # TODO: not yet really implemented
        if a.isExpressionConstantRef() and b.isExpressionConstantRef():
            if a.isMutable() or b.isMutable():
                return True

        return False

    def removeKnowledge(self, node):
        pass

    def onControlFlowEscape(self, node):
        # TODO: One day, we should trace which nodes exactly cause a variable
        # to be considered escaped, pylint: disable=unused-argument

        for variable in self.getActiveVariables():
            if variable.isModuleVariable():
                # print variable

                self.markActiveVariableAsUnknown(variable)

            elif variable.isLocalVariable() and \
                (python_version >= 300 or variable.isSharedTechnically() is not False):
                # TODO: Could be limited to shared variables that are actually
                # written to. Most of the time, that won't be the case.

                self.markActiveVariableAsUnknown(variable)

    def removeAllKnowledge(self):
        self.markActiveVariablesAsUnknown()

    def getVariableTrace(self, variable, version):
        return self.parent.getVariableTrace(variable, version)

    def hasVariableTrace(self, variable, version):
        return self.parent.hasVariableTrace(variable, version)

    def addVariableTrace(self, variable, version, trace):
        self.parent.addVariableTrace(variable, version, trace)

    def addVariableMergeMultipleTrace(self, variable, traces):
        return self.parent.addVariableMergeMultipleTrace(variable, traces)

    def onVariableSet(self, assign_node):
        version = assign_node.getVariableVersion()
        variable = assign_node.getVariable()

        # TODO: The variable, version and assign_node are redundant to pass.
        variable_trace = VariableTraceAssign(
            owner       = self.owner,
            assign_node = assign_node,
            variable    = variable,
            version     = version,
            previous    = self.getVariableCurrentTrace(
                variable = variable
            )
        )

        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = variable_trace
        )

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableDel(self, variable, version):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        old_trace = self.getVariableCurrentTrace(variable)

        variable_trace = VariableTraceUninit(
            owner    = self.owner,
            variable = variable,
            version  = version,
            previous = old_trace
        )

        # Assign to not initialized again.
        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = variable_trace
        )

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

    def onLocalsUsage(self, locals_owner):
        self.onLocalsDictEscaped()

        result = []

        include_closure = locals_owner.isExpressionFunctionBody() and \
                          not locals_owner.isUnoptimized()

        for variable in self.getActiveVariables():
            if variable.isLocalVariable() and \
               (variable.getOwner() is locals_owner or
                include_closure and locals_owner.hasClosureVariable(variable)) and \
               variable.getName() != ".0":
                variable_trace = self.getVariableCurrentTrace(
                    variable
                )

                variable_trace.addNameUsage()

                result.append(
                    (
                        variable,
                        variable_trace.getVersion()
                    )
                )

        return result

    def onVariableContentEscapes(self, variable):
        self.getVariableCurrentTrace(variable).onValueEscape()

    def onExpression(self, expression, allow_none = False):
        if expression is None and allow_none:
            return None

        assert expression.isExpression(), expression
        assert expression.parent, expression

        # Now compute this expression, allowing it to replace itself with
        # something else as part of a local peep hole optimization.
        r = expression.computeExpressionRaw(
            trace_collection = self
        )
        assert type(r) is tuple, expression

        new_node, change_tags, change_desc = r

        if change_tags is not None:
            # This is mostly for tracing and indication that a change occurred
            # and it may be interesting to look again.
            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        if new_node is not expression:
            expression.replaceWith(new_node)

        return new_node

    def onStatement(self, statement):
        try:
            assert statement.isStatement(), statement

            new_statement, change_tags, change_desc = \
              statement.computeStatement(self)

            # print new_statement, change_tags, change_desc
            if new_statement is not statement:
                self.signalChange(
                    change_tags,
                    statement.getSourceReference(),
                    change_desc
                )

            return new_statement
        except Exception:
            Tracing.printError(
                "Problem with statement at %s:" %
                statement.getSourceReference().getAsString()
            )
            raise

    def mergeBranches(self, collection_yes, collection_no):
        """ Merge two alternative branches into this trace.

            This is mostly for merging conditional branches, or other ways
            of having alternative control flow. This deals with up to two
            alternative branches to both change this collection.
        """

        # Refuse to do stupid work
        if collection_yes is None and collection_no is None:
            return None
        elif collection_yes is None or collection_no is None:
            # Handle one branch case, we need to merge versions backwards as
            # they may make themselves obsolete.
            return self.mergeMultipleBranches(
                collections = (self, collection_yes or collection_no)
            )
        else:
            return self.mergeMultipleBranches(
                collections = (collection_yes, collection_no)
            )

    def mergeMultipleBranches(self, collections):
        assert collections

        # Optimize for length 1, which is trivial merge and needs not a
        # lot of work.
        if len(collections) == 1:
            self.replaceBranch(collections[0])
            return None

        variable_versions = {}

        for collection in collections:
            for variable, version in iterItems(collection.variable_actives):
                if variable not in variable_versions:
                    variable_versions[variable] = set([version])
                else:
                    variable_versions[variable].add(version)

        for collection in collections:
            for variable, versions in iterItems(variable_versions):
                if variable not in collection.variable_actives:
                    versions.add(0)

        self.variable_actives = {}

#         merge_traces = None

        for variable, versions in iterItems(variable_versions):
            if len(versions) == 1:
                version, = versions
            else:
                version = self.addVariableMergeMultipleTrace(
                    variable = variable,
                    traces   = [
                        self.getVariableTrace(variable, version)
                        for version in
                        versions
                    ]
                )

#                 if merge_traces is None:
#                     merge_traces = [trace_merge]
#                 else:
#                     merge_traces.append(trace_merge)

            self.markCurrentVariableTrace(variable, version)

        # Return "None", or turn the list into a tuple for memory savings.
#         return merge_traces and tuple(merge_traces)

    def replaceBranch(self, collection_replace):
        self.variable_actives.update(collection_replace.variable_actives)
        collection_replace.variable_actives = None

    def onLoopBreak(self, collection = None):
        if collection is None:
            collection = self

        return self.parent.onLoopBreak(collection)

    def onLoopContinue(self, collection = None):
        if collection is None:
            collection = self

        return self.parent.onLoopContinue(collection)

    def onFunctionReturn(self, collection = None):
        if collection is None:
            collection = self

        return self.parent.onFunctionReturn(collection)

    def onExceptionRaiseExit(self, raisable_exceptions, collection = None):
        if collection is None:
            collection = self

        return self.parent.onExceptionRaiseExit(raisable_exceptions, collection)

    def getLoopBreakCollections(self):
        return self.parent.getLoopBreakCollections()

    def getLoopContinueCollections(self):
        return self.parent.getLoopContinueCollections()

    def getFunctionReturnCollections(self):
        return self.parent.getFunctionReturnCollections()

    def getExceptionRaiseCollections(self):
        return self.parent.getExceptionRaiseCollections()

    def makeAbortStackContext(self, catch_breaks, catch_continues,
                              catch_returns, catch_exceptions):
        return self.parent.makeAbortStackContext(
            catch_breaks     = catch_breaks,
            catch_continues  = catch_continues,
            catch_returns    = catch_returns,
            catch_exceptions = catch_exceptions
        )

    def makeLocalsDictContext(self, locals_scope):
        return self.parent.makeLocalsDictContext(locals_scope)

    def onLocalsDictSet(self, variable_name, value):
        return self.parent.onLocalsDictSet(variable_name, value)

    def onLocalsDictDel(self, variable_name):
        return self.parent.onLocalsDictDel(variable_name)

    def onLocalsDictGet(self, variable_name):
        return self.parent.onLocalsDictGet(variable_name)

    def onLocalsDictEscaped(self):
        self.parent.onLocalsDictEscaped()

    def setLocalsDictShape(self, locals_scope, locals_dict_shape):
        self.parent.setLocalsDictShape(
            locals_scope      = locals_scope,
            locals_dict_shape = locals_dict_shape
        )

    def getLocalsDictShape(self):
        return self.parent.getLocalsDictShape()

    def getCompileTimeComputationResult(self, node, computation, description):
        new_node, change_tags, message = getComputationResult(
            node        = node,
            computation = computation,
            description = description
        )

        if change_tags == "new_raise":
            self.onExceptionRaiseExit(BaseException)

        return new_node, change_tags, message

    def getIteratorNextCount(self, iter_node):
        return self.value_states.get(iter_node, None)

    def initIteratorValue(self, iter_node):
        # TODO: More complex state information will be needed eventually.
        self.value_states[iter_node] = 0

    def onIteratorNext(self, iter_node):
        if iter_node in self.value_states:
            self.value_states[iter_node] += 1

    def resetValueStates(self):
        for key in self.value_states:
            self.value_states[key] = None

    def addOutlineFunction(self, outline):
        self.parent.addOutlineFunction(outline)


class TraceCollectionBranch(TraceCollectionBase):
    def __init__(self, name, parent):
        TraceCollectionBase.__init__(
            self,
            owner  = parent.owner,
            name   = name,
            parent = parent
        )

        self.variable_actives = dict(parent.variable_actives)

    def computeBranch(self, branch):
        if branch.isStatementsSequence():
            result = branch.computeStatementsSequence(
                trace_collection = self
            )

            if result is not branch:
                branch.replaceWith(result)
        else:
            self.onExpression(
                expression = branch
            )

    def initVariable(self, variable):
        variable_trace = self.parent.initVariable(variable)
        assert variable_trace.getVersion() == 0

        self.variable_actives[variable] = 0

        return variable_trace

    def onLocalsDictSet(self, variable_name, value):
        return self.parent.onLocalsDictSet(variable_name, value)

    def onLocalsDictGet(self, variable_name):
        return self.parent.onLocalsDictGet(variable_name)

    def onLocalsDictEscaped(self):
        return self.parent.onLocalsDictEscaped()


    def dumpTraces(self):
        Tracing.printSeparator()
        self.parent.dumpTraces()
        Tracing.printSeparator()

    def dumpActiveTraces(self):
        Tracing.printSeparator()
        Tracing.printLine("Active are:")
        for variable, _version in sorted(self.variable_actives.iteritems()):
            self.getVariableCurrentTrace(variable).dump()

        Tracing.printSeparator()


class TraceCollectionFunction(CollectionStartpointMixin,
                              TraceCollectionBase):
    def __init__(self, parent, function_body):
        assert function_body.isExpressionFunctionBody() or \
               function_body.isExpressionGeneratorObjectBody() or \
               function_body.isExpressionCoroutineObjectBody() or \
               function_body.isExpressionAsyncgenObjectBody(), function_body

        CollectionStartpointMixin.__init__(self)

        TraceCollectionBase.__init__(
            self,
            owner  = function_body,
            name   = "collection_" + function_body.getCodeName(),
            parent = parent
        )

        if function_body.isExpressionFunctionBody():
            for parameter_variable in function_body.getParameters().getAllVariables():
                self._initVariableInit(parameter_variable)
                self.variable_actives[parameter_variable] = 0

        for closure_variable in function_body.getClosureVariables():
            self.initVariableUnknown(closure_variable)
            self.variable_actives[closure_variable] = 0



class TraceCollectionModule(CollectionStartpointMixin,
                            TraceCollectionBase):
    def __init__(self, module):
        assert module.isCompiledPythonModule(), module

        CollectionStartpointMixin.__init__(self)

        TraceCollectionBase.__init__(
            self,
            owner  = module,
            name   = "module:" + module.getFullName(),
            parent = None
        )

        self.used_modules = OrderedSet()

    def onUsedModule(self, module_name):
        assert type(module_name) is str, module_name

        self.used_modules.add(module_name)

        if isImportedModuleByName(module_name):
            module = getImportedModuleByName(module_name)
            addUsedModule(module)

    def getUsedModules(self):
        return self.used_modules
