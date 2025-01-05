#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Yield node.

The yield node returns to the caller of the generator and therefore may execute
absolutely arbitrary code, from the point of view of this code. It then returns
something, which may often be 'None', but doesn't have to be.

TODO: Often it will be used as a statement, which may also be reflected in a
dedicated node to save a bit of memory.
"""

from nuitka.PythonVersions import python_version

from .ChildrenHavingMixins import ChildHavingExpressionMixin
from .ExpressionBases import ExpressionBase


class ExpressionYieldBase(ChildHavingExpressionMixin, ExpressionBase):
    named_children = ("expression",)

    if python_version >= 0x300:
        __slots__ = ("exception_preserving",)
    else:
        __slots__ = ()

    def __init__(self, expression, source_ref):
        ChildHavingExpressionMixin.__init__(self, expression=expression)

        ExpressionBase.__init__(self, source_ref)

        if python_version >= 0x300:
            self.exception_preserving = False

    if python_version >= 0x300:

        def markAsExceptionPreserving(self):
            self.exception_preserving = True

        def isExceptionPreserving(self):
            return self.exception_preserving

    else:

        @staticmethod
        def isExceptionPreserving():
            return False

    def computeExpression(self, trace_collection):
        # TODO: That's actually only needed if the value is mutable.
        trace_collection.removeKnowledge(self.subnode_expression)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)
        # Nothing possible really here.
        return self, None, None


class ExpressionYield(ExpressionYieldBase):
    """Yielding an expression.

    Typical code: yield expression

    Can only happen in a generator. Kind of explicitly suspends and
    resumes the execution. The user may inject any kind of exception
    or give any return value. The value of "None" is the most common
    though, esp. if it's not used.

    """

    kind = "EXPRESSION_YIELD"


class ExpressionYieldFrom(ExpressionYieldBase):
    """Yielding from an expression.

    Typical code: yield from expression (Python3)

    Can only happen in a generator and only in Python3. Similar to yield,
    but implies a loop and exception propagation to the yield from generator
    if such. Kind of explicitly suspends and resumes the execution. The
    user may inject any kind of exception or give any return value. Having
    a return value is what makes Python3 generators special, and with yield
    from, that value is the expression result.
    """

    kind = "EXPRESSION_YIELD_FROM"


class ExpressionYieldFromAwaitable(ExpressionYieldBase):
    """Yielding from an expression.

    Typical code: await x, async for ..., async with (Python3.5)

    Can only happen in a coroutine or asyncgen and only in Python3.5
    or higher.

    Similar to yield from. The actual lookups of awaitable go through
    slots and have dedicated nodes.
    """

    kind = "EXPRESSION_YIELD_FROM_AWAITABLE"


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
