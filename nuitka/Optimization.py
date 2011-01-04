#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
""" Control the folow of optimizations applied to node tree.

Uses many optimization supplying visitors imported from the optimizations package, these
can emit tags that can cause the re-execution of other optimization visitors, because
e.g. a new constant determined could make another optimization feasible.
"""

from optimizations.OptimizeModuleRecursion import ModuleRecursionVisitor
from optimizations.OptimizeConstantExec import OptimizeExecVisitor
from optimizations.OptimizeVariableClosure import VariableClosureLookupVisitor
from optimizations.OptimizeBuiltins import ReplaceBuiltinsVisitor, PrecomputeBuiltinsVisitor
from optimizations.OptimizeStaticMethodFixup import FixupNewStaticMethodVisitor
from optimizations.OptimizeConstantOperations import OptimizeOperationVisitor
from optimizations.OptimizeUnpacking import ReplaceUnpackingVisitor
from optimizations.OptimizeStatements import StatementSequencesCleanupVisitor

import Options

from oset import OrderedSet

from logging import debug, info

class Tags( set ):
    def onSignal( self, signal ):
        if type(signal) == str:
            signal = signal.split()

        for tag in signal:
            self.add( tag )

    def check( self, tag ):
        return tag in self

def optimizeTree( tree ):
    optimizations_queue = OrderedSet()
    tags = Tags()

    tags.add( "new_code" )

    def refreshOptimizationsFromTags( optimizations_queue, tags ):
        if tags.check( "new_code" ):
            optimizations_queue.add( FixupNewStaticMethodVisitor )

        if tags.check( "new_code" ) or tags.check( "new_constant" ):
            if Options.shallOptimizeStringExec():
                optimizations_queue.add( OptimizeExecVisitor )

        # TODO: Split the __import__ one out.
        if tags.check( "new_code" ) or tags.check( "new_constant" ):
            if Options.shallFollowImports():
                optimizations_queue.add( ModuleRecursionVisitor )

        if tags.check( "new_code" ) or tags.check( "new_constant" ):
            optimizations_queue.add( ReplaceBuiltinsVisitor )

        if tags.check( "new_builtin" ) or tags.check( "new_constant" ):
            optimizations_queue.add( PrecomputeBuiltinsVisitor )

        if tags.check( "new_code" ) or tags.check( "new_constant" ):
            optimizations_queue.add( OptimizeOperationVisitor )

        if tags.check( "new_code" ):
            optimizations_queue.add( VariableClosureLookupVisitor )

        if tags.check( "new_code" ) or tags.check( "new_constant" ):
            optimizations_queue.add( ReplaceUnpackingVisitor )

        if tags.check( "new_code" ) or tags.check( "new_statements" ):
            optimizations_queue.add( StatementSequencesCleanupVisitor )

        tags.clear()

    refreshOptimizationsFromTags( optimizations_queue, tags )

    while optimizations_queue:
        next_optimization = optimizations_queue.pop()

        for module in [ tree ] + getOtherModules():
            debug( "Applying to '%s' optimization '%s':" % ( module, next_optimization ) )

            next_optimization().execute( module, on_signal = tags.onSignal )

        if not optimizations_queue:
            refreshOptimizationsFromTags( optimizations_queue, tags )

    return tree

def getOtherModules():
    return ModuleRecursionVisitor.imported_modules.values()
