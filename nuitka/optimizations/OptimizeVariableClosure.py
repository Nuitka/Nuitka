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

class VariableClosureLookupVisitorPhase1( OptimizationVisitorBase ):
    """ Variable closure phase 1: Find global statements and follow them.

        Global statements outside an inlined exec statement need to be treated differently
        than inside. They affect the upper level at least, or potentially all levels below
        the exec.
    """

    def __call__( self, node ):
        if node.isStatementDeclareGlobal():
            provider = node.getParentVariableProvider()

            inside_exec = node.getSourceReference().isExecReference()

            if inside_exec:
                assert False
            else:
                module = provider.getParentModule()

                for variable_name in node.getVariableNames():
                    module_variable = module.getVariableForAssignment(
                        variable_name = variable_name
                    )

                    closure_variable = provider._addClosureVariable(
                        variable         = module_variable,
                        global_statement = True
                    )

                    if isinstance( provider, Nodes.CPythonClosureGiver ):
                        provider.registerProvidedVariable(
                            variable = closure_variable
                        )


            # Remove the global statement, so we don't repeat this ever, the effect of
            # above is permanent.
            node.replaceWith(
                new_node = Nodes.CPythonStatementPass(
                    source_ref = node.getSourceReference()
                )
            )


class VariableClosureLookupVisitorPhase2( OptimizationVisitorBase ):
    """ Variable closure phase 2: Find assignments and early closure references.

        In class context, a reference to a variable must be obeyed immediately, so
        that"variable = variable" takes first "variable" as a closure and then adds
        a new local"variable" to override it from there on. For the not early closure
        case of a function, this will not be done and only assigments shall add local
        variables, and references be ignored until phase 3.

    """

    def __call__( self, node ):
        if node.isAssignToVariable():
            variable_ref = node.getTargetVariableRef()

            if variable_ref.getVariable() is None:
                provider = node.getParentVariableProvider()

                variable_ref.setVariable(
                    provider.getVariableForAssignment(
                        variable_name = variable_ref.getVariableName()
                    )
                )
        elif node.isVariableReference():
            if node.getVariable() is None:
                if not node.getParent().isAssignToVariable():
                    provider = node.getParentVariableProvider()

                    if provider.isEarlyClosure():
                        node.setVariable(
                            provider.getVariableForReference(
                                variable_name = node.getVariableName()
                            )
                        )

class VariableClosureLookupVisitorPhase3( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isVariableReference() and node.getVariable() is None:
            provider = node.getParentVariableProvider()

            # print "Late reference", node.getVariableName(), "for", provider, "caused at", node, "of", node.getParent()

            node.setVariable(
                provider.getVariableForReference(
                    variable_name = node.getVariableName()
                )
            )

        # List contractions need to take the assign target as a closure variable. This is
        # also a wart, which is required.
        if node.isListContractionBody():
            for target in node.getTargets():
                for sub_target in target.getAssignTargetVariableNodes():
                    node.getClosureVariable(
                        variable_name = sub_target.getTargetVariableRef().getVariableName()
                    )

VariableClosureLookupVisitors = (
    VariableClosureLookupVisitorPhase1,
    VariableClosureLookupVisitorPhase2,
    VariableClosureLookupVisitorPhase3
)


class ModuleVariableWriteCheck:
    def __init__( self, variable_name ):
        self.variable_name = variable_name
        self.result = False

    def __call__( self, node ):
        if node.isAssignToVariable():
            variable = node.getTargetVariableRef().getVariable()

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
