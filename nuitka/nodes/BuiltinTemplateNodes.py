#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes related to t-strings

These will most often be used for outputs, and not optimizable and
generally these should not be that much about performance critical.

"""

from .ExpressionBasesGenerated import (
    ExpressionTemplateInterpolationBase,
    ExpressionTemplateStringBase,
)


class ExpressionTemplateString(ExpressionTemplateStringBase):
    kind = "EXPRESSION_TEMPLATE_STRING"

    named_children = ("interpolations|tuple",)
    node_attributes = ("str_values",)

    def __init__(self, str_values, interpolations, source_ref):
        ExpressionTemplateStringBase.__init__(
            self,
            interpolations=interpolations,
            str_values=str_values,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        return self, None, None


class ExpressionTemplateInterpolation(ExpressionTemplateInterpolationBase):
    kind = "EXPRESSION_TEMPLATE_INTERPOLATION"

    named_children = ("value", "format_spec|optional")
    node_attributes = (
        "str_value",
        "conversion",
    )

    def __init__(self, value, format_spec, str_value, conversion, source_ref):
        assert conversion == -1, conversion

        ExpressionTemplateInterpolationBase.__init__(
            self,
            value=value,
            format_spec=format_spec,
            str_value=str_value,
            conversion=conversion,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        return self, None, None


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
