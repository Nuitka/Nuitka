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
""" Builtin vars node.

Not used much, esp. not in the form with arguments. Maybe used in some meta programming,
and hopefully can be predicted, because at run time, it is hard to support.
"""


from .ExpressionBases import ExpressionChildHavingBase


class ExpressionBuiltinVars(ExpressionChildHavingBase):
    kind = "EXPRESSION_BUILTIN_VARS"

    named_child = "source"

    def __init__(self, source, source_ref):
        ExpressionChildHavingBase.__init__(self, value=source, source_ref=source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Should be possible to predict this.

        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None
