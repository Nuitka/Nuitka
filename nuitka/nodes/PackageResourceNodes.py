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
""" Nodes the represent ways to access package data for pkglib, pkg_resources, etc. """

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionShapeMixins import (
    ExpressionBytesShapeExactMixin,
    ExpressionStrShapeExactMixin,
)
from .HardImportNodesGenerated import (
    ExpressionImportlibResourcesReadBinaryCallBase,
    ExpressionImportlibResourcesReadTextCallBase,
    ExpressionPkgResourcesResourceStreamCallBase,
    ExpressionPkgResourcesResourceStringCallBase,
    ExpressionPkgutilGetDataCallBase,
)
from .NodeBases import SideEffectsFromChildrenMixin


class ExpressionPkgutilGetDataCall(
    ExpressionBytesShapeExactMixin
    if str is not bytes
    else ExpressionStrShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionPkgutilGetDataCallBase,
):
    kind = "EXPRESSION_PKGUTIL_GET_DATA_CALL"

    named_children = ("package", "resource")

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionPkgResourcesResourceStringCall(
    ExpressionBytesShapeExactMixin
    if str is not bytes
    else ExpressionStrShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionPkgResourcesResourceStringCallBase,
):

    kind = "EXPRESSION_PKG_RESOURCES_RESOURCE_STRING_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionPkgResourcesResourceStreamCall(
    ExpressionPkgResourcesResourceStreamCallBase
):
    kind = "EXPRESSION_PKG_RESOURCES_RESOURCE_STREAM_CALL"

    def __init__(self, package_or_requirement, resource_name, source_ref):
        ExpressionPkgResourcesResourceStreamCallBase.__init__(
            self,
            package_or_requirement=package_or_requirement,
            resource_name=resource_name,
            source_ref=source_ref,
        )

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionImportlibResourcesReadBinaryCall(
    SideEffectsFromChildrenMixin,
    ExpressionImportlibResourcesReadBinaryCallBase,
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_BINARY_CALL"

    python_version_spec = ">= 0x370"

    def __init__(self, package, resource, source_ref):
        ExpressionImportlibResourcesReadBinaryCallBase.__init__(
            self,
            package=package,
            resource=resource,
            source_ref=source_ref,
        )

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


def makeExpressionImportlibResourcesReadTextCall(
    package, resource, encoding, errors, source_ref
):
    # Avoid making things optional.
    if encoding is None:
        encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)
    if errors is None:
        errors = makeConstantRefNode(constant="strict", source_ref=source_ref)

    return ExpressionImportlibResourcesReadTextCall(
        package=package,
        resource=resource,
        encoding=encoding,
        errors=errors,
        source_ref=source_ref,
    )


class ExpressionImportlibResourcesReadTextCall(
    SideEffectsFromChildrenMixin,
    ExpressionImportlibResourcesReadTextCallBase,
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_CALL"

    python_version_spec = ">= 0x370"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
