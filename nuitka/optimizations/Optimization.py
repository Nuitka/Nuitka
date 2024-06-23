#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Control the flow of optimizations applied to node tree.

Applies abstract execution on all so far known modules until no more
optimization is possible. Every successful optimization to anything might
make others possible.
"""

import inspect

from nuitka import ModuleRegistry, Options, Variables
from nuitka.importing.Importing import addExtraSysPaths
from nuitka.importing.Recursion import considerUsedModules
from nuitka.plugins.Plugins import Plugins
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.Tracing import general, optimization_logger, progress_logger
from nuitka.utils.MemoryUsage import MemoryWatch, reportMemoryUsage
from nuitka.utils.Timing import TimerReport

from . import Graphs
from .BytecodeDemotion import demoteCompiledModuleToBytecode
from .Tags import TagSet
from .TraceCollections import fetchMergeCounts, withChangeIndicationsTo

tag_set = None


def signalChange(tags, source_ref, message):
    """Indicate a change to the optimization framework."""
    if message is not None:
        # Try hard to not call a delayed evaluation of node descriptions.

        if Options.is_verbose:
            optimization_logger.info(
                "{source_ref} : {tags} : {message}".format(
                    source_ref=source_ref.getAsString(),
                    tags=tags,
                    message=message() if inspect.isfunction(message) else message,
                )
            )

        # assert pass_count < 2

    tag_set.onSignal(tags)


def optimizeCompiledPythonModule(module):
    optimization_logger.info_if_file(
        "Doing module local optimizations for '{module_name}'.".format(
            module_name=module.getFullName()
        ),
        other_logger=progress_logger,
    )

    touched = False

    if Options.isShowProgress() and Options.isShowMemory():
        memory_watch = MemoryWatch()

    # Temporary workaround, since we do some optimization based on the last pass results
    # that are then not yet fully seen in the traces yet until another time around, we
    # allow to continue the loop even without changes one more time.
    unchanged_count = 0

    # Count the micro passes, so we can see how often we looped
    micro_pass = 0

    while True:
        micro_pass += 1

        tag_set.clear()

        try:
            # print("Compute module")
            with withChangeIndicationsTo(signalChange):
                scopes_were_incomplete = module.computeModule()
        except SystemExit:
            raise
        except BaseException:
            general.info("Interrupted while working on '%s'." % module)
            raise

        if scopes_were_incomplete:
            tag_set.add("var_usage")

        Graphs.onModuleOptimizationStep(module)

        # Search for local change tags.
        if not tag_set:
            unchanged_count += 1

            if unchanged_count == 1 and pass_count == 1:
                optimization_logger.info_if_file(
                    "Not changed, but retrying one more time.",
                    other_logger=progress_logger,
                )
                continue

            optimization_logger.info_if_file(
                "Finished with the module.", other_logger=progress_logger
            )
            break

        unchanged_count = 0

        optimization_logger.info_if_file(
            "Not finished with the module due to following change kinds: %s"
            % ",".join(sorted(tag_set)),
            other_logger=progress_logger,
        )

        # Otherwise we did stuff, so note that for return value.
        touched = True

    if Options.isShowProgress() and Options.isShowMemory():
        memory_watch.finish(
            "Memory usage changed during optimization of '%s'" % (module.getFullName())
        )

    considerUsedModules(module=module, pass_count=pass_count)

    return touched, micro_pass


def optimizeUncompiledPythonModule(module):
    full_name = module.getFullName()
    progress_logger.info(
        "Doing module dependency considerations for '{module_name}':".format(
            module_name=full_name
        )
    )

    # Pick up parent package if any.
    module.attemptRecursion()

    considerUsedModules(module=module, pass_count=pass_count)

    Plugins.considerImplicitImports(module=module)


def optimizeExtensionModule(module):
    # Pick up parent package if any.
    module.attemptRecursion()

    Plugins.considerImplicitImports(module=module)


def optimizeModule(module):
    # The tag set is global, so it can track changes without context.
    # pylint: disable=global-statement
    global tag_set
    tag_set = TagSet()

    addExtraSysPaths(Plugins.getModuleSysPathAdditions(module.getFullName()))

    if module.isPythonExtensionModule():
        optimizeExtensionModule(module)
        return False, 0
    elif module.isCompiledPythonModule():
        return optimizeCompiledPythonModule(module)
    else:
        optimizeUncompiledPythonModule(module)
        return False, 0


pass_count = 0
last_total = 0


def _restartProgress():
    global pass_count  # Singleton, pylint: disable=global-statement

    closeProgressBar()
    pass_count += 1

    optimization_logger.info_if_file(
        "PASS %d:" % pass_count, other_logger=progress_logger
    )

    if not Options.is_verbose or optimization_logger.isFileOutput():
        setupProgressBar(
            stage="PASS %d" % pass_count,
            unit="module",
            total=ModuleRegistry.getRemainingModulesCount()
            + ModuleRegistry.getDoneModulesCount(),
            min_total=last_total,
        )


def _traceProgressModuleStart(current_module):
    optimization_logger.info_if_file(
        """\
Optimizing module '{module_name}', {remaining:d} more modules to go \
after that.""".format(
            module_name=current_module.getFullName(),
            remaining=ModuleRegistry.getRemainingModulesCount(),
        ),
        other_logger=progress_logger,
    )

    reportProgressBar(
        item=current_module.getFullName(),
        total=ModuleRegistry.getRemainingModulesCount()
        + ModuleRegistry.getDoneModulesCount(),
        update=False,
    )

    if Options.isShowProgress() and Options.isShowMemory():
        reportMemoryUsage(
            "optimization/%d/%s" % (pass_count, current_module.getFullName()),
            (
                (
                    "Total memory usage before optimizing module '%s'"
                    % current_module.getFullName()
                )
                if Options.isShowProgress() or Options.isShowMemory()
                else None
            ),
        )


def _traceProgressModuleEnd(current_module):
    reportProgressBar(
        item=current_module.getFullName(),
        total=ModuleRegistry.getRemainingModulesCount()
        + ModuleRegistry.getDoneModulesCount(),
        update=True,
    )


def _endProgress():
    global last_total  # Singleton, pylint: disable=global-statement
    last_total = closeProgressBar()


def restoreFromXML(text):
    from nuitka.nodes.NodeBases import fromXML
    from nuitka.TreeXML import fromString

    xml = fromString(text)

    module = fromXML(provider=None, xml=xml)

    return module


def makeOptimizationPass():
    """Make a single pass for optimization, indication potential completion."""

    finished = True

    ModuleRegistry.startTraversal()

    _restartProgress()

    main_module = None
    stdlib_phase_done = False

    while True:
        current_module = ModuleRegistry.nextModule()

        if current_module is None:
            if main_module is not None and pass_count == 1:
                considerUsedModules(module=main_module, pass_count=-1)

                stdlib_phase_done = True
                main_module = None
                continue

            break

        if current_module.isMainModule() and not stdlib_phase_done:
            main_module = current_module

        _traceProgressModuleStart(current_module)

        module_name = current_module.getFullName()

        with TimerReport(
            message="Optimizing %s" % module_name, decider=False
        ) as module_timer:
            changed, micro_passes = optimizeModule(current_module)

        ModuleRegistry.addModuleOptimizationTimeInformation(
            module_name=module_name,
            pass_number=pass_count,
            time_used=module_timer.getDelta(),
            micro_passes=micro_passes,
            merge_counts=fetchMergeCounts(),
        )

        _traceProgressModuleEnd(current_module)

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
                unused_function.finalize()

            current_module.subnode_functions = tuple(
                function
                for function in current_module.subnode_functions
                if function in current_module.getUsedFunctions()
            )

    _endProgress()

    return finished


def optimizeModules(output_filename):
    Graphs.startGraph()

    finished = makeOptimizationPass()

    # Demote compiled modules to bytecode, now that imports had a chance to be resolved, and
    # dependencies were handled.
    for module in ModuleRegistry.getDoneModules():
        if (
            module.isCompiledPythonModule()
            and module.getCompilationMode() == "bytecode"
        ):
            demoteCompiledModuleToBytecode(module)

    # Second, "endless" pass.
    while not finished:
        finished = makeOptimizationPass()

    Graphs.endGraph(output_filename)


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
