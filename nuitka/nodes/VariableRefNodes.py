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
""" Node for variable references.

These represent all variable references in the node tree. Can be in assignments
and its expressions, changing the meaning of course dramatically.

"""

from nuitka import Variables, Builtins

from .NodeBases import (
    StatementChildrenHavingBase,
    ExpressionMixin,
    NodeBase
)

from .ConstantRefNodes import ExpressionConstantRef

def _isReadOnlyUnterdeterminedModuleVariable( variable ):
    return variable.isModuleVariable() and \
           variable.getReadOnlyIndicator() is None

def _isReadOnlyModuleVariable( variable ):
    return (
        variable.isModuleVariable() and \
        variable.getReadOnlyIndicator() is True
    ) or variable.isMaybeLocalVariable()


class ExpressionVariableRef( NodeBase, ExpressionMixin ):
    kind = "EXPRESSION_VARIABLE_REF"

    def __init__( self, variable_name, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

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

    def isTargetVariableRef( self ):
        return False

    def getVariableName( self ):
        return self.variable_name

    def getVariable( self ):
        return self.variable

    def setVariable( self, variable ):
        assert isinstance( variable, Variables.Variable ), repr( variable )
        assert self.variable is None

        self.variable = variable

    def computeExpression( self, constraint_collection ):
        assert self.variable is not None

        if _isReadOnlyUnterdeterminedModuleVariable( self.variable ):
            constraint_collection.assumeUnclearLocals()
            constraint_collection.signalChange( "new_expression", self.source_ref, "txt" )

        if _isReadOnlyModuleVariable( self.variable ):
            if self.variable_name in Builtins.builtin_exception_names:
                from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

                new_node = ExpressionBuiltinExceptionRef(
                    exception_name = self.variable_name,
                    source_ref     = self.getSourceReference()
                )

                # TODO: More like "removed_variable and new_constant" probably
                change_tags = "new_builtin"
                change_desc = "Module variable '%s' found to be builtin exception reference." % self.variable_name
            elif self.variable_name in Builtins.builtin_names:
                from .BuiltinRefNodes import ExpressionBuiltinRef

                new_node = ExpressionBuiltinRef(
                    builtin_name = self.variable_name,
                    source_ref   = self.getSourceReference()
                )

                # TODO: More like "removed_variable and new_constant" probably
                change_tags = "new_builtin"
                change_desc = "Module variable '%s' found to be builtin reference." % self.variable_name
            elif self.variable_name == "__name__":
                new_node = ExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getFullName(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__name__' with constant value."
            elif self.variable_name == "__package__":
                new_node = ExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getPackage(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__package__' with constant value."
            else:
                # Probably should give a warning once about it.
                new_node = self
                change_tags = None
                change_desc = None

            return new_node, change_tags, change_desc

        return self, None, None

    def onContentEscapes( self, constraint_collection ):
        constraint_collection.onVariableContentEscapes( self.variable )

    def isKnownToBeIterable( self, count ):
        return None

    def mayProvideReference( self ):
        # Variables are capable of "asObject0".
        return False

    def mayHaveSideEffects( self ):
        # TODO: Remembered traced could tell better.
        return True


class ExpressionTargetVariableRef( ExpressionVariableRef ):
    kind = "EXPRESSION_TARGET_VARIABLE_REF"

    def __init__( self, variable_name, source_ref ):
        ExpressionVariableRef.__init__( self, variable_name, source_ref )

        self.variable_version = None

    def getDetails( self ):
        if self.variable is None:
            return { "name" : self.variable_name }
        else:
            return {
                "name"     : self.variable_name,
                "variable" : self.variable,
                "version"  : self.variable_version
            }

    def makeCloneAt( self, source_ref ):
        result = self.__class__(
            variable_name = self.variable_name,
            source_ref    = source_ref
        )

        if self.variable is not None:
            result.setVariable( self.variable )

        return result

    def computeExpression( self, constraint_collection ):
        assert False

    def isTargetVariableRef( self ):
        return True

    def getVariableVersion( self ):
        assert self.variable_version is not None, self

        return self.variable_version

    def setVariable( self, variable ):
        ExpressionVariableRef.setVariable( self, variable )

        self.variable_version = variable.allocateTargetNumber()
        assert self.variable_version is not None


class ExpressionTempVariableRef( NodeBase, ExpressionMixin ):
    kind = "EXPRESSION_TEMP_VARIABLE_REF"

    def __init__( self, variable, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        self.variable = variable

    def getDetails( self ):
        return { "name" : self.variable.getName() }

    def getDetail( self ):
        return self.variable.getName()

    def makeCloneAt( self, source_ref ):
        return self.__class__(
            variable   = self.variable,
            source_ref = source_ref
        )

    def getVariableName( self ):
        return self.variable.getName()

    def getVariable( self ):
        return self.variable

    def isTargetVariableRef( self ):
        return False

    def computeExpression( self, constraint_collection ):
        # Nothing to do here.
        return self, None, None

    def onContentEscapes( self, constraint_collection ):
        constraint_collection.onVariableContentEscapes( self.variable )

    def mayRaiseException( self, exception_type ):
        # Can't happen
        return False

    def isKnownToBeIterableAtMin( self, count ):
        return None

        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            return friend.isKnownToBeIterableAtMin(
                count                 = count,
                constraint_collection = constraint_collection
            )
        else:
            return None

    def isKnownToBeIterableAtMax( self, count ):
        return None

        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            return friend.isKnownToBeIterableAtMax(
                count                 = count,
                constraint_collection = constraint_collection
            )
        else:
            return None

    def getIterationNext( self, constraint_collection ):
        return None

        friend = constraint_collection.getVariableValueFriend( self.variable )

        if friend is not None:
            return friend.getIterationNext(
                constraint_collection = constraint_collection
            )
        else:
            return None


    # Python3 only, it updates temporary variables that are closure variables.
    def setVariable( self, variable ):
        self.variable = variable


class ExpressionTargetTempVariableRef( ExpressionTempVariableRef ):
    kind = "EXPRESSION_TARGET_TEMP_VARIABLE_REF"

    def __init__( self, variable, source_ref ):
        ExpressionTempVariableRef.__init__( self, variable, source_ref )

        self.variable_version = variable.allocateTargetNumber()

    def computeExpression( self, constraint_collection ):
        assert False, self.parent

    def isTargetVariableRef( self ):
        return True

    def getVariableVersion( self ):
        return self.variable_version

    # Python3 only, it updates temporary variables that are closure variables.
    def setVariable( self, variable ):
        ExpressionTempVariableRef.setVariable( self, variable )

        self.variable_version = self.variable.allocateTargetNumber()


class StatementTempBlock( StatementChildrenHavingBase ):
    kind = "STATEMENT_TEMP_BLOCK"

    named_children = ( "body", )

    def __init__( self, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "body" : None
            },
            source_ref = source_ref.atInternal()
        )

        self.temp_variables = {}

    getBody = StatementChildrenHavingBase.childGetter( "body" )
    setBody = StatementChildrenHavingBase.childSetter( "body" )

    def getTempVariable( self, name ):
        assert name not in self.temp_variables, name

        result = Variables.TempVariable(
            owner         = self,
            variable_name = name
        )

        self.temp_variables[ name ] = result

        return result

    def getTempVariables( self ):
        return self.temp_variables.values()

    def mayHaveSideEffects( self ):
        return self.getBody().mayHaveSideEffects()

    def computeStatement( self, constraint_collection ):
        from nuitka.optimizations.ConstraintCollections import ConstraintCollectionTempBlock

        collection_temp_block = ConstraintCollectionTempBlock(
            constraint_collection
        )
        collection_temp_block.process( self )

        if self.getBody() is None:
            return None, "new_statements", "Removed empty temporary block"

        return self, None, None
