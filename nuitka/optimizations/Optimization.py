#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .Tags import TagSet

from nuitka import ModuleRegistry, Options

from nuitka.Tracing import printLine

from .ConstraintCollections import ConstraintCollectionModule

from logging import debug

_progress = Options.isShowProgress()

def _optimizeModulePass( module, tag_set ):
    def signalChange( tags, source_ref, message ):
        """ Indicate a change to the optimization framework.

        """
        debug( "%s : %s : %s" % ( source_ref.getAsString(), tags, message ) )

        tag_set.onSignal( tags )

    constraint_collection = ConstraintCollectionModule( signalChange )
    constraint_collection.process( module = module )

    written_variables = constraint_collection.getWrittenVariables()

    for variable in module.getVariables():
        old_value = variable.getReadOnlyIndicator()
        new_value = variable not in written_variables

        if old_value is not new_value:
            # Don't suddenly start to write.
            assert not (new_value is False and old_value is True)

            constraint_collection.signalChange(
                "read_only_mvar",
                module.getSourceReference(),
                "Determined variable '%s' is only read." % variable.getName()
            )

            variable.setReadOnlyIndicator( new_value )

def optimizeModule( module ):
    if _progress:
        printLine( "Doing module local optimizations for '%s'." % module.getFullName() )

    tag_set = TagSet()
    touched = False

    while True:
        tag_set.clear()

        _optimizeModulePass(
            module  = module,
            tag_set = tag_set
        )

        if not tag_set:
            break

        touched = True

    return touched

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
                    "Optimizing module '%s', %d more modules to go after that." % (
                        current_module.getFullName(),
                        ModuleRegistry.remainingCount()
                    )
                )

            changed = optimizeModule( current_module )

            if changed:
                finished = False

        if finished:
            break
