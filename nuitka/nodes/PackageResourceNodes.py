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
""" Nodes the represent ways to access package data for pkglib, pkg_resources, etc. """


from nuitka.specs.BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    extractBuiltinArgs,
)

from .ExpressionBases import ExpressionChildrenHavingBase
from .ExpressionShapeMixins import ExpressionBytesShapeExactMixin
from .ImportHardNodes import ExpressionImportModuleNameHardExists
from .NodeBases import SideEffectsFromChildrenMixin

pkgutil_get_data_spec = BuiltinParameterSpec(
    "pkg_util.get_data", ("package", "resource"), default_count=0
)


class ExpressionPkglibGetDataRef(ExpressionImportModuleNameHardExists):
    """Function reference pkgutil.get_data"""

    kind = "EXPRESSION_PKGLIB_GET_DATA_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExists.__init__(
            self,
            module_name="pkgutil",
            import_name="get_data",
            source_ref=source_ref,
        )

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkglibGetDataCall,
            builtin_spec=pkgutil_get_data_spec,
        )

        return result, "new_expression", "Call to 'strip' of str recognized."


class ExpressionPkglibGetDataCall(
    ExpressionBytesShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionChildrenHavingBase,
):
    kind = "EXPRESSION_PKGLIB_GET_DATA_CALL"

    named_children = ("package", "resource")

    def __init__(self, package, resource, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, {"package": package, "resource": resource}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
