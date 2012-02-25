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
""" Replace builtins with alternative implementations more optimized or capable of the task.

"""

from .OptimizeBase import (
    OptimizationDispatchingVisitorBase,
    OptimizationVisitorBase,
    makeBuiltinExceptionRefReplacementNode,
    makeBuiltinRefReplacementNode
)

from nuitka.nodes.ImportNodes import CPythonExpressionImportModule

from nuitka.Utils import getPythonVersion

from nuitka.Builtins import builtin_exception_names, builtin_names

from . import BuiltinOptimization

# TODO: The maybe local variable should have a read only indication too, but right
# now it's not yet done.

def _isReadOnlyModuleVariable( variable ):
    return ( variable.isModuleVariable() and variable.getReadOnlyIndicator() is True ) or \
           variable.isMaybeLocalVariable()



class ReplaceBuiltinsExceptionsVisitor( OptimizationVisitorBase ):
    def onEnterNode( self, node ):
        if node.isExpressionVariableRef():
            variable = node.getVariable()

            if variable is not None:
                variable_name = variable.getName()

                if variable_name in builtin_exception_names and _isReadOnlyModuleVariable( variable ):
                    new_node = makeBuiltinExceptionRefReplacementNode(
                        exception_name = variable.getName(),
                        node           = node
                    )

                    node.replaceWith( new_node )

                    self.signalChange(
                        "new_raise",
                        node.getSourceReference(),
                        message = "Replaced access to read only module variable with exception %s." % (
                           variable.getName()
                        )
                    )

                    assert node.parent is new_node.parent
