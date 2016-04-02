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
""" Constraint collection

At the core of value propagation there is the collection of constraints that
allow to propagate knowledge forward or not.

This is about collecting these constraints and to manage them.
"""

import contextlib
from logging import debug

from nuitka import Tracing, VariableRegistry
from nuitka.__past__ import iterItems  # Python3 compatibility.
from nuitka.containers.oset import OrderedSet
from nuitka.importing.ImportCache import (
    getImportedModuleByName,
    isImportedModuleByName
)
from nuitka.ModuleRegistry import addUsedModule
from nuitka.nodes.NodeMakingHelpers import getComputationResult
from nuitka.PythonVersions import python_version

from .VariableTraces import (
    VariableTraceAssign,
    VariableTraceInit,
    VariableTraceLoopMerge,
    VariableTraceMerge,
    VariableTraceUninit,
    VariableTraceUnknown
)

signalChange = None

class VariableUsageTrackingMixin:

    def initVariable(self, variable):
        if variable.isParameterVariable():
            result = self._initVariableInit(variable)
        elif variable.isLocalVariable():
            result = self._initVariableUninit(variable)
        elif variable.isMaybeLocalVariable():
            result = self._initVariableUnknown(variable)
        elif variable.isModuleVariable():
            result = self._initVariableUnknown(variable)
        elif variable.isTempVariable():
            result = self._initVariableUninit(variable)
        else:
            assert False, variable

        assert result.getVariable() is variable

        return result


class CollectionTracingMixin:
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
            self.markActiveVariableAsUnknown(variable)


class CollectionStartpointMixin:
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

    def getLoopBreakCollections(self):
        return self.break_collections

    def onLoopBreak(self, collection = None):
        if collection is None:
            collection = self

        self.break_collections.append(
            ConstraintCollectionBranch(
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
            ConstraintCollectionBranch(
                parent = collection,
                name   = "loop continue"
            )
        )

    def onFunctionReturn(self, collection = None):
        if collection is None:
            collection = self

        if self.return_collections is not None:
            self.return_collections.append(
                ConstraintCollectionBranch(
                    parent = collection,
                    name   = "return"
                )
            )

    def onExceptionRaiseExit(self, raisable_exceptions, collection = None):
        # TODO: We might want to track per exception, pylint: disable=W0613

        if collection is None:
            collection = self

        if self.exception_collections is not None:
            self.exception_collections.append(
                ConstraintCollectionBranch(
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

    def _initVariableUnknown(self, variable):
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

    def updateFromCollection(self, old_collection):
        VariableRegistry.updateFromCollection(old_collection, self)

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

class ConstraintCollectionBase(CollectionTracingMixin):
    def __init__(self, owner, name, parent):
        CollectionTracingMixin.__init__(self)

        self.owner = owner
        self.parent = parent
        self.name = name

        # Trust variable_traces, should go away later on, for now we use it to
        # disable optimization.
        self.removes_knowledge = False

    def __repr__(self):
        return "<%s for %s %d>" % (
            self.__class__.__name__,
            self.name,
            id(self)
        )

    @staticmethod
    def signalChange(tags, source_ref, message):
        # This is monkey patched from another module, pylint: disable=E1102
        signalChange(tags, source_ref, message)

    def onUsedModule(self, module):
        return self.parent.onUsedModule(module)

    @staticmethod
    def mustAlias(a, b):
        if a.isExpressionVariableRef() and b.isExpressionVariableRef():
            return a.getVariable() is b.getVariable()

        return False

    @staticmethod
    def mustNotAlias(a, b):
        # TODO: not yet really implemented, pylint: disable=W0613
        return False

    def removeKnowledge(self, node):
        pass

    def onControlFlowEscape(self, node):
        # TODO: One day, we should trace which nodes exactly cause a variable
        # to be considered escaped, pylint: disable=W0613

        for variable in self.getActiveVariables():
            if variable.isModuleVariable():
                # print variable

                self.markActiveVariableAsUnknown(variable)

            elif python_version >= 300 or variable.isSharedTechnically():
                # print variable

                # TODO: Could be limited to shared variables that are actually
                # written to. Most of the time, that won't be the case.

                self.markActiveVariableAsUnknown(variable)


    def removeAllKnowledge(self):
        # Temporary, we don't have to have this anyway, this will just disable
        # all uses of variable traces for optimization.
        self.removes_knowledge = True

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
        variable_ref = assign_node.getTargetVariableRef()

        version = variable_ref.getVariableVersion()
        variable = variable_ref.getVariable()

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


    def onVariableDel(self, variable_ref):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        variable = variable_ref.getVariable()
        version = variable_ref.getVariableVersion()

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


    def onLocalsUsage(self):
        for variable in self.getActiveVariables():

            # TODO: Currently this is a bit difficult to express in a positive
            # way, but we want to have only local variables.
            if not variable.isTempVariable() and \
               not variable.isModuleVariable():
                variable_trace = self.getVariableCurrentTrace(
                    variable
                )

                variable_trace.addNameUsage()


    def onVariableRelease(self, variable):
        current = self.getVariableCurrentTrace(variable)

        # Annotate that releases to the trace, it may be important knowledge.
        current.addRelease()

        return current


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
            constraint_collection = self
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

            if new_node.isExpressionVariableRef() or \
               new_node.isExpressionTempVariableRef():
                # Remember the reference for constraint collection.
                assert new_node.variable_trace.hasDefiniteUsages()

        # We add variable reference nodes late to their traces, only after they
        # are actually produced, and not resolved to something else, so we do
        # not have them dangling, and the code complexity inside of their own
        # "computeExpression" functions.
        if new_node.isExpressionVariableRef() or \
           new_node.isExpressionTempVariableRef():
            if new_node.getVariable().isMaybeLocalVariable():
                variable_trace = self.getVariableCurrentTrace(
                    variable = new_node.getVariable().getMaybeVariable()
                )
                variable_trace.addUsage()

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
            pass
        elif collection_yes is None or collection_no is None:
            # Handle one branch case, we need to merge versions backwards as
            # they may make themselves obsolete.
            self.mergeMultipleBranches(
                collections = (self, collection_yes or collection_no)
            )
        else:
            self.mergeMultipleBranches(
                collections = (collection_yes,collection_no)
            )

    def mergeMultipleBranches(self, collections):
        assert len(collections) > 0

        # Optimize for length 1, which is trivial merge and needs not a
        # lot of work.
        if len(collections) == 1:
            self.replaceBranch(collections[0])
            return

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

            self.markCurrentVariableTrace(variable, version)

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

    def getCompileTimeComputationResult(self, node, computation, description):
        new_node, change_tags, message = getComputationResult(
            node        = node,
            computation = computation,
            description = description
        )

        if change_tags == "new_raise":
            self.onExceptionRaiseExit(BaseException)

        return new_node, change_tags, message


class ConstraintCollectionBranch(ConstraintCollectionBase):
    def __init__(self, name, parent):
        ConstraintCollectionBase.__init__(
            self,
            owner  = parent.owner,
            name   = name,
            parent = parent
        )

        self.variable_actives = dict(parent.variable_actives)

    def computeBranch(self, branch):
        if branch.isStatementsSequence():
            result = branch.computeStatementsSequence(
                constraint_collection = self
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




class ConstraintCollectionFunction(CollectionStartpointMixin,
                                   ConstraintCollectionBase,
                                   VariableUsageTrackingMixin):
    def __init__(self, parent, function_body):
        assert function_body.isExpressionFunctionBody() or \
               function_body.isExpressionClassBody() or \
               function_body.isExpressionGeneratorObjectBody() or \
               function_body.isExpressionCoroutineObjectBody(), function_body

        CollectionStartpointMixin.__init__(self)

        ConstraintCollectionBase.__init__(
            self,
            owner  = function_body,
            name   = "function_" + str(function_body),
            parent = parent
        )


class ConstraintCollectionModule(CollectionStartpointMixin,
                                 ConstraintCollectionBase,
                                 VariableUsageTrackingMixin):
    def __init__(self, module):
        CollectionStartpointMixin.__init__(self)

        ConstraintCollectionBase.__init__(
            self,
            owner  = module,
            name   = "module",
            parent = None
        )

        self.used_modules = OrderedSet()

    def onUsedModule(self, module_name):
        self.used_modules.add(module_name)

        if isImportedModuleByName(module_name):
            module = getImportedModuleByName(module_name)
            addUsedModule(module)

    def getUsedModules(self):
        return self.used_modules
