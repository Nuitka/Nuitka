#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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


from .OptimizeBase import OptimizationVisitorBase

from nuitka import TreeOperations, Nodes

class VariableClosureLookupVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isVariableReference() and node.getVariable() is None:
            node.setVariable(
                node.getParentVariableProvider().getVariableForReference(
                    variable_name = node.getVariableName()
                )
            )


class ModuleVariableWriteCheck:
    def __init__( self, variable_name ):
        self.variable_name = variable_name
        self.result = False

    def __call__( self, node ):
        if node.isAssignToVariable() or node.isListContraction():
            for variable in node.getTargetVariables():
                if variable.isModuleVariableReference():
                    if variable.getReferenced().getName() == self.variable_name:
                        self.result = True
                        raise TreeOperations.ExitVisit

    def getResult( self ):
        return self.result



def doesWriteModuleVariable( node, variable_name ):
    visitor = ModuleVariableWriteCheck(
        variable_name = variable_name
    )

    assert node.getBody() is not None, ( node, node.getSourceReference() )

    TreeOperations.visitScope(
        tree    = node.getBody(),
        visitor = visitor
    )

    return visitor.getResult()

class ModuleVariableVisitorBase( OptimizationVisitorBase ):
    def __call__( self, node ):
        # TODO: Temporary only, while it breaks with execs
        raise TreeOperations.ExitVisit

        if node.isModule():
            variables = node.getVariables()

            for variable in sorted( variables, key = lambda x : x.getName() ):
                self.onModuleVariable( variable )

            # This is a cheap way to only visit the module. TODO: Hide
            # this away in a base class.
            raise TreeOperations.ExitVisit

    def onModuleVariable( self, variable ):
        assert False


class ModuleVariableUsageAnalysisVisitor( ModuleVariableVisitorBase ):
    def onModuleVariable( self, variable ):
        references = variable.getReferences()

        write_count = 0

        for reference in references:
            # print "  REF by", reference, reference.getOwner()

            does_write = doesWriteModuleVariable(
                node          = reference.getOwner(),
                variable_name = variable.getName()
            )

            if does_write:
                write_count += 1

        was_read_only = variable.getReadOnlyIndicator()
        is_read_only = write_count == 0

        variable.setReadOnlyIndicator( write_count == 0 )

        if is_read_only and not was_read_only:
            self.signalChange(
                "read_only_mvar",
                variable.getOwner().getSourceReference(),
                "Determined variable '%s' is only read." % variable.getName()
            )


class ModuleVariableReadReplacement:
    def __init__( self, variable_name, make_node ):
        self.variable_name = variable_name
        self.make_node = make_node

        self.result = 0

    def __call__( self, node ):
        if node.isVariableReference() and node.getVariableName() == self.variable_name:
            node.replaceWith(
                self.make_node( node )
            )

            self.result += 1

class ModuleVariableReadOnlyVisitor( ModuleVariableVisitorBase ):
    def onModuleVariable( self, variable ):
        if variable.getReadOnlyIndicator():
            variable_name = variable.getName()

            if variable_name == "__name__":
                def makeNode( node ):
                    return Nodes.makeConstantReplacementNode(
                        constant = variable.getOwner().getName(),
                        node     = node
                    )

                visitor = ModuleVariableReadReplacement(
                    variable_name = variable_name,
                    make_node     = makeNode
                )

                TreeOperations.visitTree(
                    tree    = variable.getOwner(),
                    visitor = visitor
                )

                if visitor.result > 0:
                    self.signalChange(
                        "new_constant",
                        variable.getOwner().getSourceReference(),
                        "Replaced read-only module attribute %s with constant value." % variable_name
                    )
