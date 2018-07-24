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
""" Control the flow of optimizations applied to node tree.

Applies abstract execution on all so far known modules until no more
optimization is possible. Every successful optimization to anything might
make others possible.
"""


import inspect
from logging import debug, info

from nuitka import ModuleRegistry, Options, Variables
from nuitka.importing import ImportCache
from nuitka.nodes.LocalsScopes import LocalsDictHandle, getLocalsDictHandles
from nuitka.plugins.Plugins import Plugins
from nuitka.Tracing import printLine
from nuitka.utils import MemoryUsage

from . import Graphs, TraceCollections
from .BytecodeDemotion import demoteCompiledModuleToBytecode
from .Tags import TagSet

_progress = Options.isShowProgress()
_is_verbose = Options.isVerbose()

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
        # Try hard to not call a delayed evaluation of node descriptions.

        if _is_verbose:
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
        info(
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

        info(
            "Memory usage changed during optimization of '%s': %s" % (
                module.getFullName(),
                memory_watch.asStr()
            )
        )

    Plugins.considerImplicitImports(
        module        = module,
        signal_change = signalChange
    )

    return touched


def optimizeUncompiledPythonModule(module):
    if _progress:
        info(
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

    Plugins.considerImplicitImports(
        module        = module,
        signal_change = signalChange
    )


def optimizeShlibModule(module):
    # Pick up parent package if any.
    _attemptRecursion(module)

    Plugins.considerImplicitImports(
        module        = module,
        signal_change = signalChange
    )


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
        else:
            assert False, variable_trace

    return empty


def optimizeUnusedClosureVariables(function_body):
    changed = False

    for closure_variable in function_body.getClosureVariables():
        # print "VAR", closure_variable

        # Need to take closure of those.
        if closure_variable.isParameterVariable() and \
           function_body.isExpressionGeneratorObjectBody():
            continue

        variable_traces = function_body.trace_collection.getVariableTraces(
            variable = closure_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            changed = True

            signalChange(
                "var_usage",
                function_body.getSourceReference(),
                message = "Remove unused closure variable '%s'." % closure_variable.getName()
            )

            function_body.removeClosureVariable(closure_variable)

    return changed


def optimizeLocalsDictsHandles():
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
                    # then we can push it down the line.
                    if variable_trace.getAssignNode().getAssignSource().mayHaveSideEffects():
                        propagate = False
                        break
                elif variable_trace.isUninitTrace():
                    pass

                elif variable_trace.isMergeTrace():
                    propagate = False
                    break
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

    for local_variable in function_body.getUserLocalVariables() + function_body.getOutlineLocalVariables():
        variable_traces = function_body.trace_collection.getVariableTraces(
            variable = local_variable
        )

        empty = areEmptyTraces(variable_traces)
        if empty:
            signalChange(
                "var_usage",
                function_body.getSourceReference(),
                message = "Remove unused local variable '%s'." % local_variable.getName()
            )

            function_body.removeUserVariable(local_variable)
            changed = True

    return changed


def optimizeUnusedTempVariables(provider):
    remove = None

    for temp_variable in provider.getTempVariables():
        variable_traces = provider.trace_collection.getVariableTraces(
            variable = temp_variable
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

                if optimizeUnusedTempVariables(function_body):
                    changed = True
        except Exception:
            print("Problem with", function_body)
            raise#

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

    info(output)


def restoreFromXML(text):
    from nuitka.TreeXML import fromString
    from nuitka.nodes.NodeBases import fromXML
    xml = fromString(text)

    module = fromXML(
        provider = None,
        xml      = xml
    )

    return module


def makeOptimizationPass(initial_pass):
    """ Make a single pass for optimization, indication potential completion.

    """
    # Controls complex optimization, pylint: disable=too-many-branches

    finished = True

    ModuleRegistry.startTraversal()

    if _progress:
        if initial_pass:
            info("Initial optimization pass.")
        else:
            info("Next global optimization pass.")

    while True:
        current_module = ModuleRegistry.nextModule()

        if current_module is None:
            break

        if _progress:
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
            for function in current_module.getUnusedFunctions():
                Variables.updateVariablesFromCollection(
                    old_collection = function.trace_collection,
                    new_collection = None
                )

                function.trace_collection = None

    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            if optimizeVariables(current_module):
                finished = False

            used_functions = current_module.getUsedFunctions()

            for unused_function in current_module.getUnusedFunctions():
                unused_function.trace_collection = None

            used_functions = tuple(
                function
                for function in
                current_module.getFunctions()
                if function in used_functions
            )

            current_module.setFunctions(used_functions)

    if Variables.complete:
        if optimizeLocalsDictsHandles():
            finished = False

    return finished


def _checkXMLPersistence():
    new_roots = ModuleRegistry.root_modules.__class__()  # @UndefinedVariable

    for module in tuple(ModuleRegistry.getDoneModules()):
        ModuleRegistry.root_modules.remove(module)

        if module.isPythonShlibModule():
            continue

        text = module.asXmlText()
        open("out.xml", 'w').write(text)
        restored = restoreFromXML(text)
        retext = restored.asXmlText()
        open("out2.xml", 'w').write(retext)

        assert module.getOutputFilename() == restored.getOutputFilename(), \
           (module.getOutputFilename(),restored.getOutputFilename())

        # The variable versions give diffs.
        if True: # To manually enable, pylint: disable=W0125
            import difflib
            diff = difflib.unified_diff(
                text.splitlines(),
                retext.splitlines(),
                "xml orig",
                "xml reloaded"
            )
            for line in diff:
                printLine(line)

        new_roots.add(restored)

    ModuleRegistry.root_modules = new_roots
    ModuleRegistry.startTraversal()



def optimize(output_filename):
    Graphs.startGraph()

    # First pass.
    if _progress:
        info("PASS 1:")

    makeOptimizationPass(initial_pass = True)
    Variables.complete = True

    finished = makeOptimizationPass(initial_pass = False)

    if Options.isExperimental("check_xml_persistence"):
        _checkXMLPersistence()

    # Demote compiled modules to bytecode, now that imports had a chance to be resolved, and
    # dependencies were handled.
    for module in ModuleRegistry.getDoneUserModules():
        if module.isCompiledPythonModule() and \
           module.mode == "bytecode":
            demoteCompiledModuleToBytecode(module)

    if _progress:
        info("PASS 2 ... :")

    # Second, "endless" pass.
    while not finished:
        finished = makeOptimizationPass(initial_pass = False)

    Graphs.endGraph(output_filename)
