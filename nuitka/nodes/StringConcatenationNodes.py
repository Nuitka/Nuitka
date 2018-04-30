#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node dedicated to "".join() code pattern.

This is used for Python 3.6 fstrings re-formulation and has pretty direct
code alternative to actually looking up that method from the empty string
object, so it got a dedicated node, also to perform optimizations specific
to this.
"""
from .ExpressionBases import ExpressionChildrenHavingBase
from .shapes.BuiltinTypeShapes import ShapeTypeStrOrUnicode


class ExpressionStringConcatenation(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_STRING_CONCATENATION"

    named_children = (
        "values",
    )

    def __init__(self, values, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "values" : tuple(values),
            },
            source_ref = source_ref
        )

    def getTypeShape(self):
        return ShapeTypeStrOrUnicode

    def computeExpression(self, trace_collection):
        # TODO: Could remove itself if only one argument or merge arguments
        # of mergable types.
        return self, None, None


    getValues = ExpressionChildrenHavingBase.childGetter("values")
