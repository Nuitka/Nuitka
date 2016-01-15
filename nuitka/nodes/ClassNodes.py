#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for classes and their creations.

The classes are are at the core of the language and have their complexities.

"""

from nuitka.PythonVersions import python_version

from .Checkers import checkStatementsSequenceOrNone
from .FunctionNodes import ExpressionFunctionBodyBase
from .IndicatorMixins import MarkLocalsDictIndicator
from .NodeBases import ChildrenHavingMixin, ExpressionChildrenHavingBase


class ExpressionClassBody(ExpressionFunctionBodyBase, MarkLocalsDictIndicator):
    kind = "EXPRESSION_CLASS_BODY"

    named_children = (
        "body",
    )

    checkers = {
        # TODO: Is "None" really an allowed value.
        "body" : checkStatementsSequenceOrNone
    }

    def __init__(self, provider, name, doc, flags, source_ref):
        while provider.isExpressionOutlineBody():
            provider = provider.getParentVariableProvider()

        ExpressionFunctionBodyBase.__init__(
            self,
            provider    = provider,
            name        = name,
            is_class    = True,
            code_prefix = "class",
            flags       = flags,
            source_ref  = source_ref
        )

        MarkLocalsDictIndicator.__init__(self)

        self.doc = doc

        assert self.isEarlyClosure()

    def getDetails(self):
        return {
            "name"       : self.getFunctionName(),
            "ref_name"   : self.getCodeName(),
            "provider"   : self.provider.getCodeName(),
            "doc"        : self.doc
        }

    def getDetail(self):
        return "named %s" % self.getFunctionName()

    getBody = ChildrenHavingMixin.childGetter("body")
    setBody = ChildrenHavingMixin.childSetter("body")

    def getDoc(self):
        return self.doc

    def getVariableForClosure(self, variable_name):
        # print( "getVariableForClosure", self, variable_name )

        # The class bodies provide no closure, except under CPython3.x, there
        # they provide "__class__" but nothing else.

        if variable_name == "__class__":
            if python_version < 300:
                return self.provider.getVariableForClosure(
                    "__class__"
                )
            else:
                return ExpressionFunctionBodyBase.getVariableForClosure(
                    self,
                    variable_name = "__class__"
                )
        else:
            return self.provider.getVariableForClosure(
                variable_name
            )

    def markAsDirectlyCalled(self):
        pass

    def markAsExecContaining(self):
        pass

    def markAsUnqualifiedExecContaining(self, source_ref):
        pass

    def mayHaveSideEffects(self):
        # The function definition has no side effects, calculating the defaults
        # would be, but that is done outside of this.
        return False

    def mayRaiseException(self, exception_type):
        return self.getBody().mayRaiseException(exception_type)


class ExpressionSelectMetaclass(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SELECT_METACLASS"

    named_children = (
        "metaclass",
        "bases"
    )

    def __init__(self, metaclass, bases, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "metaclass" : metaclass,
                "bases"     : bases
            },
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        # TODO: Meta class selection is very computable, and should be done.
        return self, None, None

    getMetaclass = ExpressionChildrenHavingBase.childGetter("metaclass")
    getBases = ExpressionChildrenHavingBase.childGetter("bases")


class ExpressionBuiltinType3(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_TYPE3"

    named_children = ("type_name", "bases", "dict")

    def __init__(self, type_name, bases, type_dict, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "type_name" : type_name,
                "bases"     : bases,
                "dict"      : type_dict
            },
            source_ref = source_ref
        )

    getTypeName = ExpressionChildrenHavingBase.childGetter("type_name")
    getBases = ExpressionChildrenHavingBase.childGetter("bases")
    getDict = ExpressionChildrenHavingBase.childGetter("dict")

    def computeExpression(self, constraint_collection):
        # TODO: Should be compile time computable if bases and dict are.

        return self, None, None
