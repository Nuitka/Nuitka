#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Yield node.

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

        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionYield(ExpressionYieldBase):
    """Generator 'yield expression'."""

    kind = "EXPRESSION_YIELD"


class ExpressionYieldFrom(ExpressionYieldBase):
    """Python 3 generator 'yield from expression'.

    Delegates iteration and injected values/exceptions to the sub-iterator,
    evaluating to the sub-generator's return value.
    """

    kind = "EXPRESSION_YIELD_FROM"


class ExpressionYieldFromAwaitable(ExpressionYieldBase):
    """Python 3.5+ coroutine or async-generator suspension ('await', 'async for', 'async with').

    Operates like 'yield from' on an already-resolved awaitable slot result.
    """

    kind = "EXPRESSION_YIELD_FROM_AWAITABLE"


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
