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
""" Optimizations through value propagation

This optimization steps attempts to look at the data flow and propagate values assigned
or their properties, and then to benefit from gained knowledge. The most work happens in
constraint collections.
"""

from .OptimizeBase import (
    OptimizationVisitorBase,
    ExitVisit
)

from .ConstraintCollections import ConstraintCollectionModule

from nuitka.Variables import getModuleVariables

class ValuePropagationVisitor( OptimizationVisitorBase ):
    def __init__( self ):
        self.constraint_collection = ConstraintCollectionModule( self.signalChange )

    def getConstraintCollection( self ):
        return self.constraint_collection

    def onEnterNode( self, node ):
        if node.isModule():
            self.constraint_collection.process( module = node )

            written_variables = self.constraint_collection.getWrittenVariables()

            for variable in getModuleVariables( module = node ):
                old_value = variable.getReadOnlyIndicator()
                new_value = variable not in written_variables

                if old_value is not new_value and new_value:
                    # Don't suddenly start to write.
                    assert not (new_value is False and old_value is True)

                    self.signalChange(
                        "read_only_mvar",
                        node.getSourceReference(),
                        "Determined variable '%s' is only read." % variable.getName()
                    )


                    variable.setReadOnlyIndicator( new_value )

            if False:
                print( self.constraint_collection.getWrittenVariables() )
                node.dump()

            # This is a cheap way to only visit the module. TODO: Hide this away in a base
            # class or don't use visiting.
            raise ExitVisit
