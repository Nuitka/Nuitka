#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ExpressionBases import ExpressionChildrenHavingBase


class ExpressionCall(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL"

    named_children = ("called", "args", "kw")

    def __init__(self, called, args, kw, source_ref):
        assert called.isExpression()
        assert args.isExpression()
        assert kw.isExpression()

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"called": called, "args": args, "kw": kw},
            source_ref=source_ref,
        )

    getCalled = ExpressionChildrenHavingBase.childGetter("called")
    setCalled = ExpressionChildrenHavingBase.childSetter("called")
    getCallArgs = ExpressionChildrenHavingBase.childGetter("args")
    getCallKw = ExpressionChildrenHavingBase.childGetter("kw")

    def isExpressionCall(self):
        return True

    def computeExpression(self, trace_collection):
        called = self.getCalled()

        return called.computeExpressionCall(
            call_node=self,
            call_args=self.getCallArgs(),
            call_kw=self.getCallKw(),
            trace_collection=trace_collection,
        )

    def extractSideEffectsPreCall(self):
        args = self.getCallArgs()
        kw = self.getCallKw()

        return args.extractSideEffects() + kw.extractSideEffects()


class ExpressionCallNoKeywords(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL_NO_KEYWORDS"

    named_children = ("called", "args")

    def __init__(self, called, args, source_ref):
        assert called.isExpression()
        assert args.isExpression()

        ExpressionChildrenHavingBase.__init__(
            self, values={"called": called, "args": args}, source_ref=source_ref
        )

    getCalled = ExpressionChildrenHavingBase.childGetter("called")
    setCalled = ExpressionChildrenHavingBase.childSetter("called")
    getCallArgs = ExpressionChildrenHavingBase.childGetter("args")

    def computeExpression(self, trace_collection):
        return self.getCalled().computeExpressionCall(
            call_node=self,
            call_args=self.getCallArgs(),
            call_kw=None,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getCallKw():
        return None

    def isExpressionCall(self):
        return True

    def extractSideEffectsPreCall(self):
        args = self.getCallArgs()

        return args.extractSideEffects()


class ExpressionCallKeywordsOnly(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL_KEYWORDS_ONLY"

    named_children = ("called", "kw")

    def __init__(self, called, kw, source_ref):
        assert called.isExpression()
        assert kw.isExpression()

        ExpressionChildrenHavingBase.__init__(
            self, values={"called": called, "kw": kw}, source_ref=source_ref
        )

    getCalled = ExpressionChildrenHavingBase.childGetter("called")
    setCalled = ExpressionChildrenHavingBase.childSetter("called")
    getCallKw = ExpressionChildrenHavingBase.childGetter("kw")

    def computeExpression(self, trace_collection):
        called = self.getCalled()

        return called.computeExpressionCall(
            call_node=self,
            call_args=None,
            call_kw=self.getCallKw(),
            trace_collection=trace_collection,
        )

    @staticmethod
    def getCallArgs():
        return None

    def isExpressionCall(self):
        return True

    def extractSideEffectsPreCall(self):
        kw = self.getCallKw()

        return kw.extractSideEffects()


class ExpressionCallEmpty(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CALL_EMPTY"

    named_children = ("called",)

    def __init__(self, called, source_ref):
        assert called.isExpression()

        ExpressionChildrenHavingBase.__init__(
            self, values={"called": called}, source_ref=source_ref
        )

    getCalled = ExpressionChildrenHavingBase.childGetter("called")
    setCalled = ExpressionChildrenHavingBase.childSetter("called")

    def computeExpression(self, trace_collection):
        called = self.getCalled()

        return called.computeExpressionCall(
            call_node=self,
            call_args=None,
            call_kw=None,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getCallKw():
        return None

    @staticmethod
    def getCallArgs():
        return None

    def isExpressionCall(self):
        return True

    @staticmethod
    def extractSideEffectsPreCall():
        return ()


def makeExpressionCall(called, args, kw, source_ref):
    """ Make the most simple call node possible.

        By avoiding the more complex classes, we can achieve that there is
        less work to do for analysis.
    """
    has_kw = kw is not None and (
        not kw.isExpressionConstantRef() or kw.getConstant() != {}
    )
    has_args = args is not None and (
        not args.isExpressionConstantRef() or args.getConstant() != ()
    )

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
