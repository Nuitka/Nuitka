#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ExpressionBasesGenerated import (
    ExpressionBuiltinClassmethodBase,
    ExpressionBuiltinStaticmethodBase,
)
from .shapes.BuiltinTypeShapes import tshape_classmethod, tshape_staticmethod


class BuiltinStaticmethodClassmethodMixin(object):
    __slots__ = ()

    # There is nothing to compute for it as a value.
    auto_compute_handling = "final,no_raise"

    # TODO: Make it part of auto-compute through a the shape provided.
    @staticmethod
    def isKnownToBeIterable(count):
        # pylint: disable=unused-argument
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    # TODO: should be automatic due to final
    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    # TODO: should be a auto_compute property.
    def mayHaveSideEffect(self):
        return self.subnode_value.mayHaveSideEffect()

    def extractSideEffects(self):
        return self.subnode_value.extractSideEffects()


class ExpressionBuiltinStaticmethod(
    BuiltinStaticmethodClassmethodMixin, ExpressionBuiltinStaticmethodBase
):
    kind = "EXPRESSION_BUILTIN_STATICMETHOD"

    # TODO: Allow these to be in class classes instead.
    named_children = ("value",)

    @staticmethod
    def getTypeShape():
        return tshape_staticmethod


class ExpressionBuiltinClassmethod(
    BuiltinStaticmethodClassmethodMixin, ExpressionBuiltinClassmethodBase
):
    kind = "EXPRESSION_BUILTIN_CLASSMETHOD"

    # TODO: Allow these to be in mixin classes instead.
    named_children = ("value",)

    @staticmethod
    def getTypeShape():
        return tshape_classmethod
