#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node the calls to the 'open' builtin.

This is a rather two sided beast, as it may be read or write. And we would like to be able
to track it, so we can include files into the executable, or write more efficiently.
"""

from .NodeBases import ExpressionChildrenHavingBase


class ExpressionBuiltinOpen(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_OPEN"

    named_children = (
        "filename",
        "mode",
        "buffering"
    )

    def __init__(self, filename, mode, buffering, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "filename"  : filename,
                "mode"      : mode,
                "buffering" : buffering
            },
            source_ref = source_ref
        )

    getFilename = ExpressionChildrenHavingBase.childGetter("filename")
    getMode = ExpressionChildrenHavingBase.childGetter("mode")
    getBuffering = ExpressionChildrenHavingBase.childGetter("buffering")

    def computeExpression(self, constraint_collection):
        # Note: Quite impossible to predict without further assumptions, but we could look
        # at the arguments at least.
        return self, None, None
