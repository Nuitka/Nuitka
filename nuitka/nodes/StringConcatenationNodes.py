#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionChildHavingBase
from .shapes.BuiltinTypeShapes import tshape_str_or_unicode


class ExpressionStringConcatenation(ExpressionChildHavingBase):
    kind = "EXPRESSION_STRING_CONCATENATION"

    named_child = "values"
    getValues = ExpressionChildHavingBase.childGetter("values")

    def __init__(self, values, source_ref):
        assert values

        ExpressionChildHavingBase.__init__(
            self, value=tuple(values), source_ref=source_ref
        )

    def getTypeShape(self):
        return tshape_str_or_unicode

    def computeExpression(self, trace_collection):
        # TODO: Could remove itself if only one argument or merge arguments
        # of mergable types.
        streaks = []

        start = None

        values = self.subnode_values

        for count, value in enumerate(values):
            if value.isCompileTimeConstant() and value.hasShapeUnicodeExact():
                if start is None:
                    start = count
            else:
                if start is not None:
                    if start != count - 1:
                        streaks.append((start, count))

                start = None

        # Catch final one too.
        if start is not None:
            if start != len(values) - 1:
                streaks.append((start, len(values)))

        if streaks:
            values = list(values)

            for streak in reversed(streaks):
                new_element = makeConstantRefNode(
                    constant="".join(
                        value.getCompileTimeConstant()
                        for value in values[streak[0] : streak[1]]
                    ),
                    source_ref=values[streak[0]].source_ref,
                )

                values[streak[0] : streak[1]] = (new_element,)

            if len(values) > 1:
                self.setChild("values", values)
                return (
                    self,
                    "new_constant",
                    "Partially combined strings for concatenation",
                )

        if len(values) == 1 and values[0].hasShapeUnicodeExact():
            return (
                values[0],
                "new_constant",
                "Removed strings concatenation of one value.",
            )

        return self, None, None
