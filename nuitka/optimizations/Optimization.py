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
from logging import debug, info

from nuitka import ModuleRegistry, Options, VariableRegistry
from nuitka.importing import ImportCache
from nuitka.optimizations import Graphs, TraceCollections
from nuitka.plugins.Plugins import Plugins
from nuitka.Tracing import printLine
from nuitka.utils import MemoryUsage

from .BytecodeDemotion import demoteCompiledModuleToBytecode
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


def optimizeCompiledPythonModule(module):
    if _progress:
        printLine(
            "Doing module local optimizations for '{module_name}'.".format(
                module_name = module.getFullName()
            )
        )

    touched = False

    if _progress and Options.isShowMemory():
        memory_watch = MemoryUsage.MemoryWatch()

    while True:
        tag_set.clear()

        try:
            module.computeModule()
        except BaseException:
            info("Interrupted while working on '%s'." % module)
            raise

        Graphs.onModuleOptimizationStep(module)

        # Search for local change tags.
        for tag in tag_set:
            if tag == "new_code":
                continue

            break
        else:
            break

        # Otherwise we did stuff, so note that for return value.
        touched = True

    if _progress and Options.isShowMemory():
        memory_watch.finish()

        printLine(
            "Memory usage changed during optimization of '%s': %s" % (
                module.getFullName(),
                memory_watch.asStr()
            )
        )

    Plugins.considerImplicitImports(module, signal_change = signalChange)

    return touched

def optimizeUncompiledPythonModule(module):
    if _progress:
        printLine(
            "Doing module dependency considerations for '{module_name}':".format(
                module_name = module.getFullName()
            )
        )

    for used_module_name in module.getUsedModules():
        used_module = ImportCache.getImportedModuleByName(used_module_name)
        ModuleRegistry.addUsedModule(used_module)

    package_name = module.getPackage()

    if package_name is not None:
        used_module = ImportCache.getImportedModuleByName(package_name)
        ModuleRegistry.addUsedModule(used_module)


def optimizeShlibModule(module):
    # Pick up parent package if any.
    _attemptRecursion(module)

    Plugins.considerImplicitImports(module, signal_change = signalChange)


def optimizeModule(module):
    if module.isPythonShlibModule():
        optimizeShlibModule(module)
        changed = False
    elif module.isCompiledPythonModule():
        changed = optimizeCompiledPythonModule(module)
    else:
        optimizeUncompiledPythonModule(module)
        changed = False

    return changed


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
    if module.isCompiledPythonModule():
        for function_body in module.getUsedFunctions():
            if not VariableRegistry.complete:
                continue

            optimizeUnusedUserVariables(function_body)

            optimizeUnusedClosureVariables(function_body)

            optimizeUnusedTempVariables(function_body)

        optimizeUnusedTempVariables(module)


def _traceProgress(current_module):
    output = """\
Optimizing module '{module_name}', {remaining:d} more modules to go \
after that.""".format(
            module_name = current_module.getFullName(),
            remaining   = ModuleRegistry.remainingCount(),
    )

    if Options.isShowMemory():
        output += "Memory usage {memory}:".format(
            memory = MemoryUsage.getHumanReadableProcessMemoryUsage()
        )

    printLine(output)


def makeOptimizationPass(initial_pass):
    """ Make a single pass for optimization, indication potential completion.

    """
    finished = True

    ModuleRegistry.startTraversal()

    if _progress:
        if initial_pass:
            printLine("Initial optimization pass.")
        else:
            printLine("Next global optimization pass.")

    while True:
        current_module = ModuleRegistry.nextModule()

        if current_module is None:
            break

        if _progress:
            _traceProgress(current_module)

        # The tag set is global, so it can react to changes without context.
        # pylint: disable=W0603
        global tag_set
        tag_set = TagSet()

        changed = optimizeModule(current_module)

        if changed:
            finished = False

    # Unregister collection traces from now unused code, dropping the trace
    # collections of functions no longer used.
    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            for function in current_module.getUnusedFunctions():
                VariableRegistry.updateFromCollection(
                    old_collection = function.constraint_collection,
                    new_collection = None
                )

                function.constraint_collection = None

    for current_module in ModuleRegistry.getDoneModules():
        optimizeVariables(current_module)

    return finished


def optimize():
    Graphs.startGraph()

    # First pass.
    if _progress:
        info("PASS 1:")

    makeOptimizationPass(False)
    VariableRegistry.considerCompletion()
    finished = makeOptimizationPass(False)

    # Demote to bytecode if now.
    for module in ModuleRegistry.getDoneUserModules():
        if module.isPythonShlibModule():
            continue

        if module.mode == "bytecode":
            demoteCompiledModuleToBytecode(module)

    # Second, endless pass.
    if _progress:
        info("PASS 2..:")

    while not finished:
        finished = makeOptimizationPass(True)

    Graphs.endGraph()
