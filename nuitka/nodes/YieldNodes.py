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
""" Yield node.

The yield node returns to the caller of the generator and therefore may execute
absolutely arbitrary code, from the point of view of this code. It then returns
something, which may often be 'None', but doesn't have to be.

Often it will be used as a statement, which should also be reflected in a
dedicated node.
"""

from .NodeBases import ExpressionChildrenHavingBase


class ExpressionYield(ExpressionChildrenHavingBase):
    """ Yielding an expression.

        Typical code: yield expression

        Can only happen in a generator. Kind of explicitly suspends and
        resumes the execution. The user may inject any kind of exception
        or give any return value. The value of "None" is the most common
        though, esp. if it's not used.

    """


    kind = "EXPRESSION_YIELD"

    named_children = ("expression",)

    def __init__(self, expression, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.exception_preserving = False

    def markAsExceptionPreserving(self):
        self.exception_preserving = True

    def isExceptionPreserving(self):
        return self.exception_preserving

    getExpression = ExpressionChildrenHavingBase.childGetter("expression")

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getExpression())

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(self)

        constraint_collection.onExceptionRaiseExit(BaseException)
        # Nothing possible really here.
        return self, None, None


class ExpressionYieldFrom(ExpressionChildrenHavingBase):
    """ Yielding from an expression.

        Typical code: yield from expression (Python3)

        Can only happen in a generator and only in Python3. Similar to yield,
        but implies a loop and exception propagation to the yield from generator
        if such. Kind of explicitly suspends and resumes the execution. The
        user may inject any kind of exception or give any return value. Having
        a return value is what makes Python3 generators special, and with yield
        from, that value is the expression result.
    """
    kind = "EXPRESSION_YIELD_FROM"

    named_children = ("expression",)

    def __init__(self, expression, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.exception_preserving = False

    def markAsExceptionPreserving(self):
        self.exception_preserving = True

    def isExceptionPreserving(self):
        return self.exception_preserving

    getExpression = ExpressionChildrenHavingBase.childGetter("expression")

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getExpression())

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(self)

        constraint_collection.onExceptionRaiseExit(BaseException)

        # Nothing possible really here.
        return self, None, None
