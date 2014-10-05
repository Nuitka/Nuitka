#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import ModuleRegistry, Options, Utils
from nuitka.Tracing import printLine

from .ConstraintCollections import ConstraintCollectionModule
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
    debug(
        "{source_ref} : {tags} : {message}".format(
            source_ref = source_ref.getAsString(),
            tags       = tags,
            message    = message
        )
    )
    tag_set.onSignal(tags)


def _optimizeModulePass(module):
    module.collection = ConstraintCollectionModule(
        signal_change = signalChange,
        module        = module
    )

    # Pick up parent package if any.
    _attemptRecursion(module)

    written_variables = module.collection.getWrittenVariables()

    for variable in module.getVariables():
        old_value = variable.getReadOnlyIndicator()
        new_value = variable not in written_variables

        if old_value is not new_value:
            # Don't suddenly start to write.
            assert not (new_value is False and old_value is True)

            module.collection.signalChange(
                "read_only_mvar",
                module.getSourceReference(),
                "Determined variable '{variable_name}' is only read.".format(
                    variable_name = variable.getName()
                )
            )

            variable.setReadOnlyIndicator(new_value)


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

        _optimizeModulePass(
            module = module
        )

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

    return touched


def optimizeShlibModule(module):
    # Pick up parent package if any.
    _attemptRecursion(module)

    # The tag set is global, so it can react to changes without context.
    # pylint: disable=W0603
    global tag_set
    tag_set = TagSet()

    module.considerImplicitImports(signal_change = signalChange)


def optimizeVariables(module):
    for function_body in module.getUsedFunctions():
        constraint_collection = function_body.constraint_collection
        if constraint_collection.unclear_locals:
            continue

        for closure_variable in function_body.getClosureVariables():
            # print "VAR", closure_variable

            variable_traces = constraint_collection.getVariableTraces(
                variable = closure_variable
            )

            empty = True
            for variable_trace in variable_traces:
                if variable_trace.isAssignTrace():
                    empty = False
                    break
                elif variable_trace.isInitTrace():
                    empty = False
                    break
                elif variable_trace.getDefiniteUsages():
                    # Checking definite is enough, the merges, we shall see
                    # them as well.
                    empty = False
                    break
                elif variable_trace.isEscaped():
                    # If the value is escape, we still need to keep it for that
                    # escape opportunity. This is only while that is not seen
                    # as a definite usage.
                    empty = False
                    break
                elif variable_trace.getReleases():
                    # Python3 only, but a "del" statement may occur and needs
                    # to prevent.
                    assert Utils.python_version >= 300
                    empty = False
                    break

            if empty:
                function_body.removeVariable(closure_variable)


def optimize():
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

        for current_module in ModuleRegistry.getDoneModules():
            if not current_module.isPythonShlibModule():
                optimizeVariables(current_module)

        if finished:
            break
