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

Uses many optimization supplying visitors imported from the optimizations package, these
can emit tags that can cause the re-execution of other optimization visitors, because
e.g. a new constant determined could make another optimization feasible.
"""

from .OptimizeModuleRecursion import ModuleRecursionVisitor
from .OptimizeVariableClosure import VariableClosureLookupVisitors
from .OptimizeRaises import OptimizeRaisesVisitor
from .OptimizeValuePropagation import ValuePropagationVisitor

from .Tags import TagSet

from nuitka import Options, TreeBuilding

from nuitka.oset import OrderedSet

from nuitka.Tracing import printLine

from logging import debug

_progress = Options.isShowProgress()

def optimizeTree( tree ):
    # Lots of conditions to take, pylint: disable=R0912
    if _progress:
        printLine( "Doing module local optimizations for '%s'." % tree.getFullName() )

    optimizations_queue = OrderedSet()
    tags = TagSet()

    # Seed optimization with tag that causes all steps to be run.
    tags.add( "new_code" )

    def refreshOptimizationsFromTags( optimizations_queue, tags ):
        if tags.check( "new_code" ):
            optimizations_queue.update( VariableClosureLookupVisitors )

        # Note: The import recursion cannot be done in "computeNode" due to circular
        # dependency and since it only needs to be done with "new_import" again, it
        # remains its own visitor.
        if tags.check( "new_code new_import" ):
            if not Options.shallMakeModule():
                optimizations_queue.add( ModuleRecursionVisitor )

        if tags.check( "new_code new_raise" ):
            optimizations_queue.add( OptimizeRaisesVisitor )

        if tags.check( "new_code new_statements new_constant new_builtin read_only_mvar" ):
            optimizations_queue.add( ValuePropagationVisitor )

        tags.clear()

    refreshOptimizationsFromTags( optimizations_queue, tags )

    while optimizations_queue:
        next_optimization = optimizations_queue.pop( last = False )

        debug( "Applying to '%s' optimization '%s':" % ( tree, next_optimization ) )

        next_optimization().execute( tree, on_signal = tags.onSignal )

        if not optimizations_queue or tags.check( "new_code" ):
            refreshOptimizationsFromTags( optimizations_queue, tags )

    return tree

def getImportedModules():
    return TreeBuilding.getImportedModules()

def optimizeWhole( main_module ):
    done_modules = set()

    result = optimizeTree( main_module )
    done_modules.add( main_module )

    if _progress:
        printLine( "Finished. %d more modules to go." % len( getImportedModules() ) )

    finished = False

    while not finished:
        finished = True

        for module in list( getImportedModules() ):
            if module not in done_modules:
                optimizeTree( module )

                done_modules.add( module )

                if _progress:
                    printLine(
                        "Finished. %d more modules to go." % (
                            len( getImportedModules() ) - len( done_modules )
                        )
                    )

                finished = False

    return result
