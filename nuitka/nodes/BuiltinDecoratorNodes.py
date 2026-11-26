#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes for the 'staticmethod' and 'classmethod' built-ins."""

from .ExpressionBasesGenerated import (
    ExpressionBuiltinClassmethodBase,
    ExpressionBuiltinStaticmethodBase,
)
from .shapes.BuiltinTypeShapes import tshape_classmethod, tshape_staticmethod


class BuiltinStaticmethodClassmethodMixin(object):
    __slots__ = ()

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    auto_compute_handling = "final,no_raise"

    # TODO: Make it part of auto-compute through the shape provided.
    @staticmethod
    def isKnownToBeIterable(count):
        # pylint: disable=unused-argument
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    # TODO: Should be automatic due to 'final'.
    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    # TODO: Should be an 'auto_compute_handling' property.
    def mayHaveSideEffect(self):
        return self.subnode_value.mayHaveSideEffect()

    def extractSideEffects(self):
        return self.subnode_value.extractSideEffects()


class ExpressionBuiltinStaticmethod(
    BuiltinStaticmethodClassmethodMixin, ExpressionBuiltinStaticmethodBase
):
    kind = "EXPRESSION_BUILTIN_STATICMETHOD"

    # TODO: Allow 'named_children' to be in mixin classes instead.
    named_children = ("value",)

    @staticmethod
    def getTypeShape():
        return tshape_staticmethod


class ExpressionBuiltinClassmethod(
    BuiltinStaticmethodClassmethodMixin, ExpressionBuiltinClassmethodBase
):
    kind = "EXPRESSION_BUILTIN_CLASSMETHOD"

    named_children = ("value",)

    @staticmethod
    def getTypeShape():
        return tshape_classmethod


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
