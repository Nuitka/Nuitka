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
""" Call node

Function calls and generally calling expressions are the same thing. This is
very important, because it allows to predict most things, and avoid expensive
operations like parameter parsing at run time.

There will be a method "computeExpressionCall" to aid predicting them in other
nodes.
"""

from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)


class ExpressionCall(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL"

    named_children = ("called", "args", "kwargs")

    def __init__(self, called, args, kwargs, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"called": called, "args": args, "kwargs": kwargs},
            source_ref=source_ref,
        )

    @staticmethod
    def isExpressionCall():
        return True

    def computeExpression(self, trace_collection):
        called = self.subnode_called

        return called.computeExpressionCall(
            call_node=self,
            call_args=self.subnode_args,
            call_kw=self.subnode_kwargs,
            trace_collection=trace_collection,
        )

    def extractSideEffectsPreCall(self):
        args = self.subnode_args
        kw = self.subnode_kwargs

        return args.extractSideEffects() + kw.extractSideEffects()


class ExpressionCallNoKeywords(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL_NO_KEYWORDS"

    named_children = ("called", "args")

    subnode_kwargs = None

    def __init__(self, called, args, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"called": called, "args": args}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        called = self.subnode_called

        return called.computeExpressionCall(
            call_node=self,
            call_args=self.subnode_args,
            call_kw=None,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isExpressionCall():
        return True

    def extractSideEffectsPreCall(self):
        args = self.subnode_args

        return args.extractSideEffects()


class ExpressionCallKeywordsOnly(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL_KEYWORDS_ONLY"

    named_children = ("called", "kwargs")

    subnode_args = None

    def __init__(self, called, kwargs, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"called": called, "kwargs": kwargs}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        called = self.subnode_called

        return called.computeExpressionCall(
            call_node=self,
            call_args=None,
            call_kw=self.subnode_kwargs,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isExpressionCall():
        return True

    def extractSideEffectsPreCall(self):
        kw = self.subnode_kwargs

        return kw.extractSideEffects()


class ExpressionCallEmpty(ExpressionChildHavingBase):
    kind = "EXPRESSION_CALL_EMPTY"

    named_child = "called"

    subnode_args = None
    subnode_kwargs = None

    def __init__(self, called, source_ref):
        ExpressionChildHavingBase.__init__(self, value=called, source_ref=source_ref)

    def computeExpression(self, trace_collection):
        called = self.subnode_called

        return called.computeExpressionCall(
            call_node=self,
            call_args=None,
            call_kw=None,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isExpressionCall():
        return True

    @staticmethod
    def extractSideEffectsPreCall():
        return ()


def makeExpressionCall(called, args, kw, source_ref):
    """Make the most simple call node possible.

    By avoiding the more complex classes, we can achieve that there is
    less work to do for analysis.
    """
    has_kw = kw is not None and not kw.isExpressionConstantDictEmptyRef()

    has_args = args is not None and not args.isExpressionConstantTupleEmptyRef()

    if has_kw:
        if has_args:
            return ExpressionCall(called, args, kw, source_ref)
        else:
            return ExpressionCallKeywordsOnly(called, kw, source_ref)
    else:
        if has_args:
            return ExpressionCallNoKeywords(called, args, source_ref)
        else:
            return ExpressionCallEmpty(called, source_ref)
