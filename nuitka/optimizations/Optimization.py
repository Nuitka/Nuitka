#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

Applies constraint collection on all so far known modules until no more
optimization is possible. Every successful optimization to anything might
make others possible.
"""


from logging import debug

from nuitka import ModuleRegistry, Options, VariableRegistry
from nuitka.optimizations import TraceCollections
from nuitka.plugins.PluginBase import Plugins
from nuitka.Tracing import printLine
from nuitka.utils import Utils

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
                message    = message
            )
        )

    tag_set.onSignal(tags)

# Use this globally from there, without cyclic dependency.
TraceCollections.signalChange = signalChange


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
        memory_watch = Utils.MemoryWatch()

    while True:
        tag_set.clear()

        module.computeModule()

        if not tag_set:
            break

        touched = True

    if _progress:
        memory_watch.finish()

        printLine(
            "Memory usage changed during optimization of '%s': %s" % (
                module.getFullName(),
                memory_watch.asStr()
            )
        )

    return touched or module.hasUnclearLocals()


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
            elif variable_trace.getDefiniteUsages():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                empty = False
                break
        elif variable_trace.isUnknownTrace():
            if variable_trace.getDefiniteUsages():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                empty = False
                break
        elif variable_trace.isMergeTrace():
            if variable_trace.getDefiniteUsages():
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


def optimizeUnusedClosureVariables(function_body):
    for closure_variable in function_body.getClosureVariables():
        # print "VAR", closure_variable

        variable_traces = function_body.constraint_collection.getVariableTraces(
            variable = closure_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            function_body.removeClosureVariable(closure_variable)


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
        constraint_collection = function_body.constraint_collection
        if constraint_collection.unclear_locals:
            continue

        optimizeUnusedUserVariables(function_body)

        optimizeUnusedClosureVariables(function_body)

        optimizeUnusedTempVariables(function_body)

    optimizeUnusedTempVariables(module)


def optimize():
    # This is somewhat complex with many cases, pylint: disable=R0912

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
                        memory      = Utils.getHumanReadableProcessMemoryUsage()
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

        if not VariableRegistry.complete:
            VariableRegistry.complete = True

            finished = False

        for current_module in ModuleRegistry.getDoneModules():
            if not current_module.isPythonShlibModule():
                optimizeVariables(current_module)

        if finished:
            break
