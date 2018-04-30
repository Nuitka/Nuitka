#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Built-in staticmethod/classmethod nodes

These are good for optimizations, as they give a very well known result, changing
only the way a class member is being called. Being able to avoid going through a
C call to the built-ins resulting wrapper, will speed up things.
"""

from .ExpressionBases import ExpressionChildrenHavingBase
from .shapes.BuiltinTypeShapes import (
    ShapeTypeClassmethod,
    ShapeTypeStaticmethod
)


class ExpressionBuiltinStaticmethod(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_STATICMETHOD"

    named_children = (
        "value",
    )

    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def __init__(self, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "value" : value
            },
            source_ref = source_ref
        )

    def computeExpression(self, trace_collection):
        # TODO: Consider shape and predict exception raise or not.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def isKnownToBeIterable(self, count):
        return False

    def getTypeShape(self):
        return ShapeTypeStaticmethod


class ExpressionBuiltinClassmethod(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_CLASSMETHOD"

    named_children = (
        "value",
    )

    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def __init__(self, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "value" : value
            },
            source_ref = source_ref
        )

    def computeExpression(self, trace_collection):
        # TODO: Consider shape and predict exception raise or not.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def isKnownToBeIterable(self, count):
        return False

    def getTypeShape(self):
        return ShapeTypeClassmethod
