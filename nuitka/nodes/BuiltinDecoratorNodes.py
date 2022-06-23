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

from .ExpressionBases import ExpressionChildHavingBase
from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions
from .shapes.BuiltinTypeShapes import tshape_classmethod, tshape_staticmethod


class ExpressionBuiltinStaticmethodClassmethodBase(ExpressionChildHavingBase):
    named_child = "value"

    def __init__(self, value, source_ref):
        ExpressionChildHavingBase.__init__(self, value=value, source_ref=source_ref)

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def isKnownToBeIterable(count):
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    # TODO: Side effect from child mixin should do these, there is one for multiple children.
    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def mayHaveSideEffect(self):
        return self.subnode_value.mayHaveSideEffect()

    def extractSideEffects(self):
        return self.subnode_value.extractSideEffects()

    def computeExpressionDrop(self, statement, trace_collection):
        result = makeStatementOnlyNodesFromExpressions(
            self.subnode_value.extractSideEffects()
        )

        return (
            result,
            "new_statements",
            "Removed unused %r call." % self.getTypeShape().getTypeName(),
        )


class ExpressionBuiltinStaticmethod(ExpressionBuiltinStaticmethodClassmethodBase):
    kind = "EXPRESSION_BUILTIN_STATICMETHOD"

    @staticmethod
    def getTypeShape():
        return tshape_staticmethod


class ExpressionBuiltinClassmethod(ExpressionBuiltinStaticmethodClassmethodBase):
    kind = "EXPRESSION_BUILTIN_CLASSMETHOD"

    @staticmethod
    def getTypeShape():
        return tshape_classmethod
