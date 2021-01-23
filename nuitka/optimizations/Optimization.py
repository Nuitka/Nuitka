#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import os

from nuitka import ModuleRegistry, Options, Variables
from nuitka.importing import ImportCache
from nuitka.nodes.LocalsScopes import LocalsDictHandle, getLocalsDictHandles
from nuitka.plugins.Plugins import Plugins
from nuitka.Tracing import (
    general,
    memory_logger,
    optimization_logger,
    progress_logger,
    recursion_logger,
    reportProgressBar,
)
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import makePath
from nuitka.utils.MemoryUsage import (
    MemoryWatch,
    getHumanReadableProcessMemoryUsage,
)

from . import Graphs, TraceCollections
from .BytecodeDemotion import demoteCompiledModuleToBytecode
from .Tags import TagSet

_progress = Options.isShowProgress()
_is_verbose = Options.isVerbose()


def _attemptRecursion(module):
    new_modules = module.attemptRecursion()

    if Options.isShowInclusion():
        for new_module in new_modules:
            recursion_logger.info(
                "{source_ref} : {tags} : {message}".format(
                    source_ref=new_module.getSourceReference().getAsString(),
                    tags="new_code",
                    message="Recursed to module package.",
                )
            )


tag_set = None


def signalChange(tags, source_ref, message):
    """Indicate a change to the optimization framework."""
    if message is not None:
        # Try hard to not call a delayed evaluation of node descriptions.

        if _is_verbose:
            optimization_logger.info(
                "{source_ref} : {tags} : {message}".format(
                    source_ref=source_ref.getAsString(),
                    tags=tags,
                    message=message() if inspect.isfunction(message) else message,
                )
            )

    tag_set.onSignal(tags)


# Use this globally from there, without cyclic dependency.
TraceCollections.signalChange = signalChange


def optimizeCompiledPythonModule(module):
    if _progress:
        progress_logger.info(
            "Doing module local optimizations for '{module_name}'.".format(
                module_name=module.getFullName()
            )
        )

    touched = False

    if _progress and Options.isShowMemory():
        memory_watch = MemoryWatch()

    while True:
        tag_set.clear()

        try:
            # print("Compute module")
            module.computeModule()
        except BaseException:
            general.info("Interrupted while working on '%s'." % module)
            raise

        Graphs.onModuleOptimizationStep(module)

        # Search for local change tags.
        for tag in tag_set:
            if tag == "new_code":
                continue

            break
        else:
            if _progress:
                progress_logger.info("Finished with the module.")
            break

        if _progress:
            if "new_code" in tag_set:
                tag_set.remove("new_code")

            progress_logger.info(
                "Not finished with the module due to following change kinds: %s"
                % ",".join(sorted(tag_set))
            )

        # Otherwise we did stuff, so note that for return value.
        touched = True

    if _progress and Options.isShowMemory():
        memory_watch.finish()

        memory_logger.info(
            "Memory usage changed during optimization of '%s': %s"
            % (module.getFullName(), memory_watch.asStr())
        )

    Plugins.considerImplicitImports(module=module, signal_change=signalChange)

    return touched


def optimizeUncompiledPythonModule(module):
    full_name = module.getFullName()
    if _progress:
        progress_logger.info(
            "Doing module dependency considerations for '{module_name}':".format(
                module_name=full_name
            )
        )

    for used_module_name, used_module_path in module.getUsedModules():
        used_module = ImportCache.getImportedModuleByNameAndPath(
            used_module_name, used_module_path
        )
        ModuleRegistry.addUsedModule(used_module)

    package_name = full_name.getPackageName()

    if package_name is not None:
        used_module = ImportCache.getImportedModuleByName(package_name)
        ModuleRegistry.addUsedModule(used_module)

    Plugins.considerImplicitImports(module=module, signal_change=signalChange)


def optimizeShlibModule(module):
    # Pick up parent package if any.
    _attemptRecursion(module)

    Plugins.considerImplicitImports(module=module, signal_change=signalChange)


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


def areReadOnlyTraces(variable_traces):
    """Do these traces contain any writes."""

    # Many cases immediately return, that is how we do it here,
    for variable_trace in variable_traces:
        if variable_trace.isAssignTrace():
            return False
        elif variable_trace.isInitTrace():
            pass
        elif variable_trace.isDeletedTrace():
            # A "del" statement can do this, and needs to prevent variable
            # from being not released.

            return False
        elif variable_trace.isUninitTrace():
            pass
        elif variable_trace.isUnknownTrace():
            return False
        elif variable_trace.isMergeTrace():
            pass
        elif variable_trace.isLoopTrace():
            pass
        else:
            assert False, variable_trace

    return True


def areEmptyTraces(variable_traces):
    """Do these traces contain any writes or accesses."""
    # Many cases immediately return, that is how we do it here,
    # pylint: disable=too-many-return-statements

    for variable_trace in variable_traces:
        if variable_trace.isAssignTrace():
            return False
        elif variable_trace.isInitTrace():
            return False
        elif variable_trace.isDeletedTrace():
            # A "del" statement can do this, and needs to prevent variable
            # from being removed.

            return False
        elif variable_trace.isUninitTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isUnknownTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isMergeTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isLoopTrace():
            return False
        else:
            assert False, variable_trace

    return True


def optimizeUnusedClosureVariables(function_body):
    changed = False

    for closure_variable in function_body.getClosureVariables():
        # print "VAR", closure_variable

        # Need to take closure of those.
        if (
            closure_variable.isParameterVariable()
            and function_body.isExpressionGeneratorObjectBody()
        ):
            continue

        variable_traces = function_body.trace_collection.getVariableTraces(
            variable=closure_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            changed = True

            signalChange(
                "var_usage",
                function_body.getSourceReference(),
                message="Remove unused closure variable '%s'."
                % closure_variable.getName(),
            )

            function_body.removeClosureVariable(closure_variable)

    return changed


def optimizeVariableReleases(function_body):
    changed = False

    for parameter_variable in function_body.getParameterVariablesWithManualRelease():

        variable_traces = function_body.trace_collection.getVariableTraces(
            variable=parameter_variable
        )

        read_only = areReadOnlyTraces(variable_traces)
        if read_only:
            changed = True

            signalChange(
                "var_usage",
                function_body.getSourceReference(),
                message="Schedule removal releases of unassigned parameter variable '%s'."
                % parameter_variable.getName(),
            )

            function_body.removeVariableReleases(parameter_variable)

    return changed


def optimizeLocalsDictsHandles():
    # Lots of cases, pylint: disable=too-many-branches

    changed = False

    locals_scopes = getLocalsDictHandles()

    for locals_scope_name, locals_scope in locals_scopes.items():
        # Limit to Python2 classes for now:
        if type(locals_scope) is not LocalsDictHandle:
            continue

        if locals_scope.isMarkedForPropagation():
            locals_scope.finalize()

            del locals_scopes[locals_scope_name]

            assert locals_scope not in locals_scopes
            continue

        propagate = True

        for variable in locals_scope.variables.values():
            for variable_trace in variable.traces:
                if variable_trace.isAssignTrace():
                    # For assign traces we want the value to not have a side effect,
                    # then we can push it down the line. TODO: Once temporary
                    # variables and dictionary building allows for unset values
                    # remove this
                    if (
                        variable_trace.getAssignNode().subnode_source.mayHaveSideEffects()
                    ):
                        propagate = False
                        break
                elif variable_trace.isDeletedTrace():
                    propagate = False
                    break
                elif variable_trace.isMergeTrace():
                    propagate = False
                    break
                elif variable_trace.isUninitTrace():
                    pass
                elif variable_trace.isUnknownTrace():
                    propagate = False
                    break
                else:
                    assert False, (variable, variable_trace)

        if propagate:
            locals_scope.markForLocalsDictPropagation()

    return changed


def optimizeUnusedUserVariables(function_body):
    changed = False

    for local_variable in function_body.getUserLocalVariables():
        variable_traces = function_body.trace_collection.getVariableTraces(
            variable=local_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            function_body.removeUserVariable(local_variable)

            signalChange(
                "var_usage",
                function_body.getSourceReference(),
                message="Remove unused local variable '%s'." % local_variable.getName(),
            )

            changed = True

    outlines = function_body.trace_collection.getOutlineFunctions()

    if outlines is not None:
        for outline in outlines:
            for local_variable in outline.getUserLocalVariables():
                variable_traces = function_body.trace_collection.getVariableTraces(
                    variable=local_variable
                )

                empty = areEmptyTraces(variable_traces)
                if empty:
                    outline.removeUserVariable(local_variable)

                    signalChange(
                        "var_usage",
                        outline.getSourceReference(),
                        message="Remove unused local variable '%s'."
                        % local_variable.getName(),
                    )

                    changed = True

    return changed


def optimizeUnusedTempVariables(provider):
    remove = None

    for temp_variable in provider.getTempVariables():
        variable_traces = provider.trace_collection.getVariableTraces(
            variable=temp_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            if remove is None:
                remove = []

            remove.append(temp_variable)

    if remove:
        for temp_variable in remove:
            provider.removeTempVariable(temp_variable)

        return True
    else:
        return False


def optimizeUnusedAssignments(provider):
    for _trace_collection in provider.getTraceCollections():
        # TODO: Find things to do here.
        pass

    return False


def optimizeVariables(module):
    changed = False

    try:
        try:
            for function_body in module.getUsedFunctions():
                if Variables.complete:
                    if optimizeUnusedUserVariables(function_body):
                        changed = True

                    if optimizeUnusedClosureVariables(function_body):
                        changed = True

                    if optimizeVariableReleases(function_body):
                        changed = True

                if optimizeUnusedTempVariables(function_body):
                    changed = True
        except Exception:
            print("Problem with", function_body)
            raise  #

        if optimizeUnusedUserVariables(module):
            changed = True

        if optimizeUnusedTempVariables(module):
            changed = True

    #        TODO: Global optimizations could go here maybe, so far we can do all
    #        the things in assign nodes themselves based on last trace.
    #        if optimizeUnusedAssignments(module):
    #            changed = True
    except Exception:
        print("Problem with", module)
        raise

    return changed


def _traceProgress(current_module):
    if _progress:
        output = """\
Optimizing module '{module_name}', {remaining:d} more modules to go \
after that.""".format(
            module_name=current_module.getFullName(),
            remaining=ModuleRegistry.getRemainingModulesCount(),
        )
        progress_logger.info(output)

    reportProgressBar(
        stage="Optimization",
        unit=" modules",
        item=current_module.getFullName(),
        total=ModuleRegistry.getRemainingModulesCount()
        + ModuleRegistry.getDoneModulesCount(),
    )

    if _progress and Options.isShowMemory():
        output = "Memory usage {memory}:".format(
            memory=getHumanReadableProcessMemoryUsage()
        )

        memory_logger.info(output)


def restoreFromXML(text):
    from nuitka.nodes.NodeBases import fromXML
    from nuitka.TreeXML import fromString

    xml = fromString(text)

    module = fromXML(provider=None, xml=xml)

    return module


def makeOptimizationPass():
    """Make a single pass for optimization, indication potential completion."""

    # Controls complex optimization

    finished = True

    ModuleRegistry.startTraversal()

    while True:
        current_module = ModuleRegistry.nextModule()

        if current_module is None:
            break

        _traceProgress(current_module)

        # The tag set is global, so it can react to changes without context.
        # pylint: disable=global-statement
        global tag_set
        tag_set = TagSet()

        changed = optimizeModule(current_module)

        if changed:
            finished = False

    # Unregister collection traces from now unused code, dropping the trace
    # collections of functions no longer used.
    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            for unused_function in current_module.getUnusedFunctions():
                Variables.updateVariablesFromCollection(
                    old_collection=unused_function.trace_collection,
                    new_collection=None,
                    source_ref=unused_function.getSourceReference(),
                )

                unused_function.trace_collection = None

    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            if optimizeVariables(current_module):
                finished = False

            used_functions = current_module.getUsedFunctions()

            for unused_function in current_module.getUnusedFunctions():
                unused_function.trace_collection = None

            used_functions = tuple(
                function
                for function in current_module.subnode_functions
                if function in used_functions
            )

            current_module.setChild("functions", used_functions)

    if Variables.complete:
        if optimizeLocalsDictsHandles():
            finished = False

    return finished


def _getCacheFilename(module):
    module_cache_dir = os.path.join(getCacheDir(), "module-cache")
    makePath(module_cache_dir)

    return os.path.join(module_cache_dir, module.getFullName().asString() + ".xml")


def _checkXMLPersistence():
    for module in ModuleRegistry.getDoneModules():
        if not module.isCompiledPythonModule():
            continue

        text = module.asXmlText()
        with open(_getCacheFilename(module), "w") as f:
            f.write(text)


def optimize(output_filename):
    Graphs.startGraph()

    # First pass.
    if _progress:
        progress_logger.info("PASS 1:")

    makeOptimizationPass()
    Variables.complete = True

    if _progress:
        progress_logger.info("PASS 2:")

    finished = makeOptimizationPass()

    if Options.isExperimental("check_xml_persistence"):
        _checkXMLPersistence()

    # Demote compiled modules to bytecode, now that imports had a chance to be resolved, and
    # dependencies were handled.
    for module in ModuleRegistry.getDoneModules():
        if (
            module.isCompiledPythonModule()
            and module.getCompilationMode() == "bytecode"
        ):
            demoteCompiledModuleToBytecode(module)

    pass_count = 2
    # Second, "endless" pass.
    while not finished:
        pass_count += 1

        if _progress:
            progress_logger.info("PASS %d:" % pass_count)

        finished = makeOptimizationPass()

    Graphs.endGraph(output_filename)
