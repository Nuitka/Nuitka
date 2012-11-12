#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Node for variable references.

These represent all variable references in the node tree. Can be in assignments and it
expressions, changing the meaning of course dramatically.

"""

from nuitka import Variables, Builtins, Options

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase, CPythonExpressionMixin

from .BuiltinReferenceNodes import (
    CPythonExpressionBuiltinExceptionRef,
    CPythonExpressionBuiltinRef
)

from .ConstantRefNode import CPythonExpressionConstantRef

def _isReadOnlyModuleVariable( variable ):
    return ( variable.isModuleVariable() and variable.getReadOnlyIndicator() is True ) or \
           variable.isMaybeLocalVariable()


class CPythonExpressionVariableRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_VARIABLE_REF"

    def __init__( self, variable_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.variable_name = variable_name
        self.variable = None

    def getDetails( self ):
        if self.variable is None:
            return { "name" : self.variable_name }
        else:
            return { "name" : self.variable_name, "variable" : self.variable }

    def getDetail( self ):
        if self.variable is None:
            return self.variable_name
        else:
            return repr( self.variable )

    def makeCloneAt( self, source_ref ):
        result = self.__class__(
            variable_name = self.variable_name,
            source_ref    = source_ref
        )

        result.variable = self.variable

        return result

    def getVariableName( self ):
        return self.variable_name

    def getVariable( self ):
        return self.variable

    def setVariable( self, variable, replace = False ):
        assert isinstance( variable, Variables.Variable ), repr( variable )

        assert self.variable is None or replace

        self.variable = variable

    def computeNode( self, constraint_collection ):
        assert self.variable is not None

        if _isReadOnlyModuleVariable( self.variable ):
            if self.variable_name in Builtins.builtin_exception_names:
                new_node = CPythonExpressionBuiltinExceptionRef(
                    exception_name = self.variable_name,
                    source_ref     = self.getSourceReference()
                )

                # TODO: More like "removed_variable and new_constant" probably
                change_tags = "new_builtin"
                change_desc = "Module variable '%s' found to be builtin exception reference." % self.variable_name
            elif self.variable_name in Builtins.builtin_names:
                new_node = CPythonExpressionBuiltinRef(
                    builtin_name = self.variable_name,
                    source_ref   = self.getSourceReference()
                )

                # TODO: More like "removed_variable and new_constant" probably
                change_tags = "new_builtin"
                change_desc = "Module variable '%s' found to be builtin reference." % self.variable_name
            elif self.variable_name == "__name__":
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getFullName(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__name__' with constant value."
            elif self.variable_name == "__doc__":
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getDoc(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__doc__' with constant value."
            elif self.variable_name == "__package__":
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getPackage(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__package__' with constant value."
            elif self.variable_name == "__file__":
                # TODO: We have had talks of this becoming more dynamic, but currently it isn't so.
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getFilename(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__file__' with constant value."
            else:
                # Probably should give a warning once about it.
                new_node = self
                change_tags = None
                change_desc = None

            return new_node, change_tags, change_desc

        # TODO: Enable the below, once we can trust that the corruption of mutable
        # constants is detected.
        if not Options.isExperimental():
            return self, None, None

        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None and not friend.mayHaveSideEffects( None ) and friend.isNode():
            assert hasattr( friend, "makeCloneAt" ), friend

            new_node = friend.makeCloneAt(
                source_ref = self.source_ref,
            )

            change_desc = "Assignment source of '%s' propagated, as it has no side effects." % self.variable.getName()

            return new_node, "new_expression", change_desc

        return self, None, None

    def isKnownToBeIterable( self, count ):
        return None

    def mayHaveSideEffects( self, constraint_collection ):
        if constraint_collection is None:
            return True

        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            # TODO: There is no friend that say "known to not be defined"
            return False
        else:
            return True


class CPythonExpressionTargetVariableRef( CPythonExpressionVariableRef ):
    kind = "EXPRESSION_TARGET_VARIABLE_REF"

    def computeNode( self, constraint_collection ):
        assert False


class CPythonExpressionTempVariableRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_TEMP_VARIABLE_REF"

    def __init__( self, variable, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.variable = variable

    def getDetails( self ):
        return { "name" : self.variable.getName() }

    def getDetail( self ):
        return self.variable.getName()

    def getVariableName( self ):
        return self.variable.getName()

    def getVariable( self ):
        return self.variable

    def computeNode( self, constraint_collection ):
        # Nothing to do here.
        return self, None, None

    def mayRaiseException( self, exception_type ):
        # Can't happen
        return False

    def isKnownToBeIterableAtMin( self, count, constraint_collection ):
        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            return friend.isKnownToBeIterableAtMin(
                count                 = count,
                constraint_collection = constraint_collection
            )
        else:
            return None

    def isKnownToBeIterableAtMax( self, count, constraint_collection ):
        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            return friend.isKnownToBeIterableAtMax(
                count                 = count,
                constraint_collection = constraint_collection
            )
        else:
            return None

    def getIterationNext( self, constraint_collection ):
        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            return friend.getIterationNext(
                constraint_collection = constraint_collection
            )
        else:
            return None


class CPythonStatementTempBlock( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_TEMP_BLOCK"

    named_children = ( "body", )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__(
            self,
            source_ref = source_ref.atInternal()
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "body" : None
            }
        )

        self.temp_variables = set()

    def getTempVariable( self, name ):
        assert name not in self.temp_variables

        result = Variables.TempVariable(
            owner         = self,
            variable_name = name
        )

        self.temp_variables.add( result )

        return result

    def getTempVariables( self ):
        return self.temp_variables

    def mayHaveSideEffects( self, constraint_collection ):
        return self.getBody().mayHaveSideEffects( constraint_collection )
