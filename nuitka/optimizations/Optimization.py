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
from nuitka.plugins.Plugins import Plugins
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.Tracing import (
    general,
    memory_logger,
    optimization_logger,
    progress_logger,
    recursion_logger,
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
    optimization_logger.info_fileoutput(
        "Doing module local optimizations for '{module_name}'.".format(
            module_name=module.getFullName()
        ),
        other_logger=progress_logger,
    )

    touched = False

    if _progress and Options.isShowMemory():
        memory_watch = MemoryWatch()

    while True:
        tag_set.clear()

        try:
            # print("Compute module")
            changed = module.computeModule()
        except BaseException:
            general.info("Interrupted while working on '%s'." % module)
            raise

        if changed:
            tag_set.add("var_usage")

        Graphs.onModuleOptimizationStep(module)

        # Search for local change tags.
        for tag in tag_set:
            if tag == "new_code":
                continue

            break
        else:
            optimization_logger.info_fileoutput(
                "Finished with the module.", other_logger=progress_logger
            )
            break

        if "new_code" in tag_set:
            tag_set.remove("new_code")

        optimization_logger.info_fileoutput(
            "Not finished with the module due to following change kinds: %s"
            % ",".join(sorted(tag_set)),
            other_logger=progress_logger,
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


pass_count = 0


def _restartProgress():
    closeProgressBar()

    global pass_count  # Singleton, pylint: disable=global-statement

    pass_count += 1

    optimization_logger.info_fileoutput(
        "PASS %d:" % pass_count, other_logger=progress_logger
    )

    setupProgressBar(
        stage="PASS %d" % pass_count,
        unit="module",
        total=ModuleRegistry.getRemainingModulesCount()
        + ModuleRegistry.getDoneModulesCount(),
    )


def _traceProgress(current_module):
    optimization_logger.info_fileoutput(
        """\
Optimizing module '{module_name}', {remaining:d} more modules to go \
after that.""".format(
            module_name=current_module.getFullName(),
            remaining=ModuleRegistry.getRemainingModulesCount(),
        ),
        other_logger=progress_logger,
    )

    # Progress bar and spammy tracing don't go along.
    if not _is_verbose:
        reportProgressBar(
            item=current_module.getFullName(),
            total=ModuleRegistry.getRemainingModulesCount()
            + ModuleRegistry.getDoneModulesCount(),
        )

    if _progress and Options.isShowMemory():
        output = "Memory usage {memory}:".format(
            memory=getHumanReadableProcessMemoryUsage()
        )

        memory_logger.info(output)


def _endProgress():
    closeProgressBar()


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

    _restartProgress()

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
    # collections of functions no longer used. This must be done after global
    # optimization due to cross module usages.
    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            for unused_function in current_module.getUnusedFunctions():
                Variables.updateVariablesFromCollection(
                    old_collection=unused_function.trace_collection,
                    new_collection=None,
                    source_ref=unused_function.getSourceReference(),
                )

                unused_function.trace_collection = None

            used_functions = tuple(
                function
                for function in current_module.subnode_functions
                if function in current_module.getUsedFunctions()
            )

            current_module.setChild("functions", used_functions)

    _endProgress()

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

    global pass_count  # Singleton, pylint: disable=global-statement

    # Second, "endless" pass.
    while not finished:
        finished = makeOptimizationPass()

    Graphs.endGraph(output_filename)
