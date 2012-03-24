#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Control the flow of optimizations applied to node tree.

Uses many optimization supplying visitors imported from the optimizations package, these
can emit tags that can cause the re-execution of other optimization visitors, because
e.g. a new constant determined could make another optimization feasible.
"""

from .OptimizeModuleRecursion import ModuleRecursionVisitor
from .OptimizeConstantExec import OptimizeExecVisitor
from .OptimizeVariableClosure import (
    VariableClosureLookupVisitors,
    ModuleVariableUsageAnalysisVisitor
)
from .OptimizeRaises import OptimizeRaisesVisitor
from .OptimizeValuePropagation import ValuePropagationVisitor

# Populate call registry.
from . import OptimizeBuiltinCalls
OptimizeBuiltinCalls.register()

# Populate slice registry
from . import OptimizeSlices
OptimizeSlices.register()

# Populate subscript registry
from . import OptimizeSubscripts
OptimizeSubscripts.register()

from .Tags import TagSet

from nuitka import Options, TreeRecursion

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

        if tags.check( "new_code new_statements" ):
            optimizations_queue.add( ModuleVariableUsageAnalysisVisitor )

        if tags.check( "new_code new_constant" ):
            if Options.shallOptimizeStringExec():
                optimizations_queue.add( OptimizeExecVisitor )

        if tags.check( "new_code new_raise" ):
            optimizations_queue.add( OptimizeRaisesVisitor )

        if tags.check( "new_code new_statements new_constant new_builtin" ):
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

def getOtherModules():
    return list( TreeRecursion.imported_modules.values() )

def optimizeWhole( main_module ):
    done_modules = set()

    result = optimizeTree( main_module )
    done_modules.add( main_module )

    if _progress:
        printLine( "Finished. %d more modules to go." % len( getOtherModules() ) )

    finished = False

    while not finished:
        finished = True

        for other_module in getOtherModules():
            if other_module not in done_modules:
                optimizeTree( other_module )

                done_modules.add( other_module )

                if _progress:
                    printLine( "Finished. %d more modules to go." % ( len( getOtherModules() ) - len( done_modules ) ) )

                finished = False

    return result
