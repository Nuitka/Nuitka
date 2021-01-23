#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node for the calls to the 'next' built-in and unpacking special next.

    The unpacking next has only special that it raises a different exception
    text, explaining things about its context.
"""

from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase,
)


class ExpressionBuiltinNext1(ExpressionBuiltinSingleArgBase):
    __slots__ = ("may_not_raise",)

    kind = "EXPRESSION_BUILTIN_NEXT1"

    def __init__(self, value, source_ref):
        ExpressionBuiltinSingleArgBase.__init__(
            self, value=value, source_ref=source_ref
        )

        self.may_not_raise = False

    def computeExpression(self, trace_collection):
        self.may_not_raise, result = self.subnode_value.computeExpressionNext1(
            next_node=self, trace_collection=trace_collection
        )

        return result

    def mayRaiseExceptionOperation(self):
        return not self.may_not_raise

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_value.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )


class ExpressionSpecialUnpack(ExpressionBuiltinNext1):
    __slots__ = ("count", "expected", "starred")

    kind = "EXPRESSION_SPECIAL_UNPACK"

    def __init__(self, value, count, expected, starred, source_ref):
        ExpressionBuiltinNext1.__init__(self, value=value, source_ref=source_ref)

        self.count = int(count)

        # TODO: Unused before 3.5 or higher, and even then starred is rare, maybe specialize for it.
        self.expected = int(expected)
        self.starred = starred

    def getDetails(self):
        result = ExpressionBuiltinNext1.getDetails(self)
        result["count"] = self.getCount()
        result["expected"] = self.getExpected()
        result["starred"] = self.getStarred()
        return result

    def getCount(self):
        return self.count

    def getExpected(self):
        return self.expected

    def getStarred(self):
        return self.starred


class ExpressionBuiltinNext2(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_NEXT2"

    named_children = ("iterator", "default")

    def __init__(self, iterator, default, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"iterator": iterator, "default": default},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: The "iterator" should be investigated here, if it is iterable,
        # or if the default is raising.

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
