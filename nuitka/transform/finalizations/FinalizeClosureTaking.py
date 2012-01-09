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
""" Finalize the closure.

If a taker wants a variable, make sure that the closure taker in between all do forward it
for this use or else it will not be available. We do this late so it is easier to remove
closure variables and keep track of references, by not having it spoiled with these
transitive only references.

"""

from .FinalizeBase import FinalizationVisitorScopedBase

class FinalizeClosureTaking( FinalizationVisitorScopedBase ):
    def onEnterNode( self, node ):
        assert node.isClosureVariableTaker(), node

        # print node, node.provider

        for variable in node.getClosureVariables():
            referenced = variable.getReferenced()
            referenced_owner = referenced.getOwner()

            assert not referenced.isModuleVariable()

            current = node.getParent()

            # print referenced

            while current is not referenced_owner:
                if current.isClosureVariableTaker():
                    for current_variable in current.getClosureVariables():
                        if current_variable.getReferenced() is referenced:
                            break
                    else:
                        # print "ADD", current, referenced
                        current.addClosureVariable( referenced )


                current = current.getParent()
