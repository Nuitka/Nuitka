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
""" Control the flow of optimizations applied to node tree.

Applies abstract execution on all so far known modules until no more
optimization is possible. Every successful optimization to anything might
make others possible.
"""


import inspect
from logging import debug, info, warning

from nuitka import ModuleRegistry, Options, VariableRegistry
from nuitka.optimizations import TraceCollections
from nuitka.plugins.Plugins import Plugins
from nuitka.Tracing import printLine
from nuitka.utils import MemoryUsage

from .Tags import TagSet

_progress = Options.isShowProgress()

def _attemptRecursion(module):
    new_modules = module.attemptRecursion()

    for new_module in new_modules:
        debug(
            "{source_ref} : {tags} : {message}".format(
                source_ref = new_module.getSourceReference().getAsString(),
                tags       = "new_code",
                message    = "Recursed to module package."
            )
        )


tag_set = None

def signalChange(tags, source_ref, message):
    """ Indicate a change to the optimization framework.

    """
    if message is not None:
        debug(
            "{source_ref} : {tags} : {message}".format(
                source_ref = source_ref.getAsString(),
                tags       = tags,
                message    = message() if inspect.isfunction(message) else message
            )
        )

    tag_set.onSignal(tags)

# Use this globally from there, without cyclic dependency.
TraceCollections.signalChange = signalChange

graph = None
computation_counters = {}

def optimizePythonModule(module):
    if _progress:
        printLine(
            "Doing module local optimizations for '{module_name}'.".format(
                module_name = module.getFullName()
            )
        )

    # The tag set is global, so it can react to changes without context.
    # pylint: disable=W0603
    global tag_set
    tag_set = TagSet()

    touched = False

    if _progress:
        memory_watch = MemoryUsage.MemoryWatch()

    while True:
        tag_set.clear()

        try:
            module.computeModule()
        except BaseException:
            info("Interrupted while working on '%s'." % module)
            raise

        if not tag_set:
            break

        if graph is not None:
            computation_counters[module] = computation_counters.get(module, 0) + 1
            module_graph = module.asGraph(computation_counters[module])

            graph.subgraph(module_graph)

        touched = True

    if _progress:
        memory_watch.finish()

        printLine(
            "Memory usage changed during optimization of '%s': %s" % (
                module.getFullName(),
                memory_watch.asStr()
            )
        )

    Plugins.considerImplicitImports(module, signal_change = signalChange)

    return touched


def optimizeShlibModule(module):
    # Pick up parent package if any.
    _attemptRecursion(module)

    # The tag set is global, so it can react to changes without context.
    # pylint: disable=W0603
    global tag_set
    tag_set = TagSet()

    Plugins.considerImplicitImports(module, signal_change = signalChange)


def areEmptyTraces(variable_traces):
    empty = True

    for variable_trace in variable_traces:
        if variable_trace.isAssignTrace():
            empty = False
            break
        elif variable_trace.isInitTrace():
            empty = False
            break
        elif variable_trace.isUninitTrace():
            if variable_trace.getPrevious():
                # A "del" statement can do this, and needs to prevent variable
                # from being removed.

                empty = False
                break
            elif variable_trace.hasDefiniteUsages():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                empty = False
                break
        elif variable_trace.isUnknownTrace():
            if variable_trace.hasDefiniteUsages():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                empty = False
                break
        elif variable_trace.isMergeTrace():
            if variable_trace.hasDefiniteUsages():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                empty = False
                break
        elif variable_trace.isEscaped():
            assert False, variable_trace

            # If the value is escape, we still need to keep it for that
            # escape opportunity. This is only while that is not seen
            # as a definite usage.
            empty = False
            break
        else:
            assert False, variable_trace

    return empty


def areReadOnlyTraces(variable_traces):
    read_only = True

    for variable_trace in variable_traces:
        if variable_trace.isAssignTrace():
            read_only = False
            break
        elif variable_trace.isInitTrace():
            read_only = False
            break

    return read_only


def optimizeUnusedClosureVariables(function_body):
    for closure_variable in function_body.getClosureVariables():
        # print "VAR", closure_variable

        # Need to take closure of
        if closure_variable.isParameterVariable() and \
           function_body.isExpressionGeneratorObjectBody():
            continue

        if function_body.hasFlag("has_super") and closure_variable.getName() in ("__class__", "self"):
            continue

        variable_traces = function_body.constraint_collection.getVariableTraces(
            variable = closure_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            signalChange(
                "var_usage",
                function_body.getSourceReference(),
                message = "Remove unused closure variable."
            )

            function_body.removeClosureVariable(closure_variable)
        else:
            read_only = areReadOnlyTraces(variable_traces)

            if read_only:
                global_trace = closure_variable.getGlobalVariableTrace()

                if global_trace is not None:
                    if not global_trace.hasWritesOutsideOf(function_body):
                        function_body.demoteClosureVariable(closure_variable)

                        signalChange(
                            "var_usage",
                            function_body.getSourceReference(),
                            message = "Turn read-only usage of unassigned closure variable to local variable."
                        )


def optimizeUnusedUserVariables(function_body):
    for local_variable in function_body.getUserLocalVariables():
        variable_traces = function_body.constraint_collection.getVariableTraces(
            variable = local_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            function_body.removeUserVariable(local_variable)


def optimizeUnusedTempVariables(provider):
    for temp_variable in provider.getTempVariables():

        variable_traces = provider.constraint_collection.getVariableTraces(
            variable = temp_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            provider.removeTempVariable(temp_variable)


def optimizeVariables(module):
    for function_body in module.getUsedFunctions():
        if not VariableRegistry.complete:
            continue

        optimizeUnusedUserVariables(function_body)

        optimizeUnusedClosureVariables(function_body)

        optimizeUnusedTempVariables(function_body)

    optimizeUnusedTempVariables(module)


def optimize():
    # This is somewhat complex with many cases, pylint: disable=R0912

    # We maintain this globally to make it accessible, pylint: disable=W0603
    global graph

    if Options.shouldCreateGraph():

        try:
            from graphviz import Digraph # pylint: disable=F0401,I0021
            graph = Digraph('G')
        except ImportError:
            warning("Cannot import graphviz module, no graphing capability.")

    while True:
        finished = True

        ModuleRegistry.startTraversal()

        while True:
            current_module = ModuleRegistry.nextModule()

            if current_module is None:
                break

            if _progress:
                printLine(
                    """\
Optimizing module '{module_name}', {remaining:d} more modules to go \
after that. Memory usage {memory}:""".format(
                        module_name = current_module.getFullName(),
                        remaining   = ModuleRegistry.remainingCount(),
                        memory      = MemoryUsage.getHumanReadableProcessMemoryUsage()
                    )
                )

            if current_module.isPythonShlibModule():
                optimizeShlibModule(current_module)
            else:
                changed = optimizePythonModule(current_module)

                if changed:
                    finished = False

        # Unregister collection traces from now unused code.
        for current_module in ModuleRegistry.getDoneModules():
            if not current_module.isPythonShlibModule():
                for function in current_module.getUnusedFunctions():
                    VariableRegistry.updateFromCollection(
                        old_collection = function.constraint_collection,
                        new_collection = None
                    )

                    function.constraint_collection = None

        if VariableRegistry.considerCompletion():
            finished = False

        for current_module in ModuleRegistry.getDoneModules():
            if not current_module.isPythonShlibModule():
                optimizeVariables(current_module)

        if finished:
            break


    if graph is not None:
        graph.engine = "dot"
        graph.graph_attr["rankdir"] = "TB"
        graph.render("something.dot")

        printLine(graph.source)
