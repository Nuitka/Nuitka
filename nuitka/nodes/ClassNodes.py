#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import ExpressionChildrenHavingBase

class ExpressionSelectMetaclass(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SELECT_METACLASS"

    named_children = ( "metaclass", "bases", )

    def __init__(self, metaclass, bases, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "metaclass" : metaclass,
                "bases"     : bases
            },
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        # TODO: Meta class selection is very computable, and should be done.
        return self, None, None

    getMetaclass = ExpressionChildrenHavingBase.childGetter("metaclass")
    getBases = ExpressionChildrenHavingBase.childGetter( "bases" )


class ExpressionBuiltinType3(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_TYPE3"

    named_children = ( "type_name", "bases", "dict" )

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

    getTypeName = ExpressionChildrenHavingBase.childGetter( "type_name" )
    getBases = ExpressionChildrenHavingBase.childGetter( "bases" )
    getDict = ExpressionChildrenHavingBase.childGetter( "dict" )

    def computeExpression(self, constraint_collection):
        # TODO: Should be compile time computable if bases and dict are.

        return self, None, None
