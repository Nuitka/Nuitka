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
""" Optimizations through value propagation

This optimization steps attempts to look at the data flow and propagate values assigned
or their properties, and then to benefit from gained knowledge. The most work happens in
constraint collections.
"""

from .OptimizeBase import (
    OptimizationVisitorScopedBase,
    TreeOperations
)

from .ConstraintCollections import ConstraintCollectionModule

from nuitka.Variables import getModuleVariables

class ValuePropagationVisitor( OptimizationVisitorScopedBase ):
    def __init__( self ):
        self.constraint_collection = ConstraintCollectionModule( self.signalChange )

    def getConstraintCollection( self ):
        return self.constraint_collection

    def onEnterNode( self, node ):
        if node.isModule():
            self.constraint_collection.process( module = node )

            for variable in getModuleVariables( module = node ):
                old_value = variable.getReadOnlyIndicator()
                new_value = variable not in self.constraint_collection.written_module_variables

                if old_value is not new_value:
                    # Don't suddenly start to write.
                    assert not (new_value is False and old_value is True)

                    self.signalChange(
                        "read_only_mvar",
                        node.getSourceReference(),
                        "Determined variable '%s' is only read." % variable.getName()
                    )


                    variable.setReadOnlyIndicator( new_value )

            if False:
                print( self.constraint_collection.written_module_variables )
                node.dump()

            # This is a cheap way to only visit the module. TODO: Hide this away in a base
            # class or don't use visiting.
            raise TreeOperations.ExitVisit
