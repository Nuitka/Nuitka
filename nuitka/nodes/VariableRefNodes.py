#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Builtins, VariableRegistry, Variables

from .ConstantRefNodes import ExpressionConstantRef
from .NodeBases import ExpressionMixin, NodeBase


def _isReadOnlyUnterdeterminedModuleVariable(variable):
    return variable.isModuleVariable() and \
           variable.getReadOnlyIndicator() is None

def _isReadOnlyModuleVariable(variable):
    return (
        variable.isModuleVariable() and \
        variable.getReadOnlyIndicator() is True
    ) or variable.isMaybeLocalVariable()


class ExpressionVariableRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_VARIABLE_REF"

    def __init__(self, variable_name, source_ref, variable = None):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.variable_name = variable_name
        self.variable = variable

        if variable is not None:
            assert variable.getName() == variable_name

        self.variable_trace = None

    def getDetails(self):
        if self.variable is None:
            return {
                "name" : self.variable_name
            }
        else:
            return {
                "name"     : self.variable_name,
                "variable" : self.variable
            }

    def getDetail(self):
        if self.variable is None:
            return self.variable_name
        else:
            return repr(self.variable)

    def makeCloneAt(self, source_ref):
        result = self.__class__(
            variable_name = self.variable_name,
            source_ref    = source_ref
        )

        result.variable = self.variable

        return result

    @staticmethod
    def isTargetVariableRef():
        return False

    def getVariableName(self):
        return self.variable_name

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        assert isinstance(variable, Variables.Variable), repr(variable)
        assert self.variable is None

        self.variable = variable

    def computeExpression(self, constraint_collection):
        variable = self.variable

        assert variable is not None

        self.variable_trace = constraint_collection.getVariableCurrentTrace(
            variable = variable
        )

        global_trace = VariableRegistry.getGlobalVariableTrace(variable)

        # TODO: Maybe local variables are factored into this strangely.
        if global_trace is None and variable.isModuleVariable():
            constraint_collection.assumeUnclearLocals()
        elif (variable.isModuleVariable() and not global_trace.hasDefiniteWrites() ) or \
             variable.isMaybeLocalVariable():
            if self.variable_name in Builtins.builtin_exception_names:
                from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

                new_node = ExpressionBuiltinExceptionRef(
                    exception_name = self.variable_name,
                    source_ref     = self.getSourceReference()
                )

                change_tags = "new_builtin_ref"
                change_desc = """\
Module variable '%s' found to be built-in exception reference.""" % (
                    self.variable_name
                )
            elif self.variable_name in Builtins.builtin_names and \
                 self.variable_name != "pow":
                from .BuiltinRefNodes import ExpressionBuiltinRef

                new_node = ExpressionBuiltinRef(
                    builtin_name = self.variable_name,
                    source_ref   = self.getSourceReference()
                )

                change_tags = "new_builtin_ref"
                change_desc = """\
Module variable '%s' found to be built-in reference.""" % (
                    self.variable_name
                )
            elif self.variable_name == "__name__":
                new_node = ExpressionConstantRef(
                    constant   = variable.getOwner().getParentModule().\
                                   getFullName(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = """\
Replaced read-only module attribute '__name__' with constant value."""
            elif self.variable_name == "__package__":
                new_node = ExpressionConstantRef(
                    constant   = variable.getOwner().getPackage(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = """\
Replaced read-only module attribute '__package__' with constant value."""
            else:
                # Probably should give a warning once about it.
                new_node = self
                change_tags = None
                change_desc = None

            return new_node, change_tags, change_desc

        return self, None, None

    def onContentEscapes(self, constraint_collection):
        constraint_collection.onVariableContentEscapes(self.variable)

    def isKnownToBeIterable(self, count):
        return None

    def mayHaveSideEffects(self):
        return not self.variable_trace.mustHaveValue()

    def mayRaiseException(self, exception_type):
        variable_trace = self.variable_trace

        return variable_trace is None or not self.variable_trace.mustHaveValue()


class ExpressionTempVariableRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_TEMP_VARIABLE_REF"

    def __init__(self, variable, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)

        self.variable = variable
        self.variable_trace = None

    def getDetails(self):
        return {
            "name" : self.variable.getName()
        }

    def getDetail(self):
        return self.variable.getName()

    def makeCloneAt(self, source_ref):
        return self.__class__(
            variable   = self.variable,
            source_ref = source_ref
        )

    def getVariableName(self):
        return self.variable.getName()

    def getVariable(self):
        return self.variable

    @staticmethod
    def isTargetVariableRef():
        return False

    def computeExpression(self, constraint_collection):
        self.variable_trace = constraint_collection.getVariableCurrentTrace(
            variable = self.variable
        )

        # Nothing to do here.
        return self, None, None

    def onContentEscapes(self, constraint_collection):
        constraint_collection.onVariableContentEscapes(self.variable)

    def mayHaveSideEffects(self):
        # Can't happen
        return False

    def mayRaiseException(self, exception_type):
        # Can't happen
        return False

    def isKnownToBeIterableAtMin(self, count):
        # TODO: See through the variable current trace.
        return None

    def isKnownToBeIterableAtMax(self, count):
        # TODO: See through the variable current trace.
        return None

    # Python3 only, it updates temporary variables that are closure variables.
    def setVariable(self, variable):
        self.variable = variable


class ExpressionTargetVariableRef(ExpressionVariableRef):
    kind = "EXPRESSION_TARGET_VARIABLE_REF"

    # TODO: Remove default and correct argument order later.
    def __init__(self, variable_name, source_ref, variable = None):
        ExpressionVariableRef.__init__(self, variable_name, source_ref)

        self.variable_version = None

        # TODO: Remove setVariable, once not needed anymore and in-line to
        # here.
        if variable is not None:
            self.setVariable(variable)
            assert variable.getName() == variable_name

    def getDetails(self):
        if self.variable is None:
            return {
                "name" : self.variable_name
            }
        else:
            return {
                "name"     : self.variable_name,
                "variable" : self.variable,
                "version"  : self.variable_version
            }

    def makeCloneAt(self, source_ref):
        result = self.__class__(
            variable_name = self.variable_name,
            source_ref    = source_ref,
            variable      = self.variable
        )

        return result

    def computeExpression(self, constraint_collection):
        assert False

    @staticmethod
    def isTargetVariableRef():
        return True

    def getVariableVersion(self):
        assert self.variable_version is not None, self

        return self.variable_version

    def setVariable(self, variable):
        ExpressionVariableRef.setVariable(self, variable)

        self.variable_version = variable.allocateTargetNumber()
        assert self.variable_version is not None


class ExpressionTargetTempVariableRef(ExpressionTempVariableRef):
    kind = "EXPRESSION_TARGET_TEMP_VARIABLE_REF"

    def __init__(self, variable, source_ref):
        ExpressionTempVariableRef.__init__(self, variable, source_ref)

        self.variable_version = variable.allocateTargetNumber()

    def computeExpression(self, constraint_collection):
        assert False, self.parent

    @staticmethod
    def isTargetVariableRef():
        return True

    def getVariableVersion(self):
        return self.variable_version

    # Python3 only, it updates temporary variables that are closure variables.
    def setVariable(self, variable):
        ExpressionTempVariableRef.setVariable(self, variable)

        self.variable_version = self.variable.allocateTargetNumber()
