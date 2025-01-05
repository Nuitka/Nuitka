#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes the represent ways to access package data for pkglib, pkg_resources, etc. """

from nuitka.importing.Importing import locateModule, makeModuleUsageAttempt
from nuitka.importing.ImportResolving import resolveModuleName
from nuitka.utils.Importing import importFromCompileTime

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import (
    ExpressionBytesShapeExactMixin,
    ExpressionStrShapeExactMixin,
)
from .HardImportNodesGenerated import (
    ExpressionImportlibResourcesBackportFilesCallBase,
    ExpressionImportlibResourcesBackportReadBinaryCallBase,
    ExpressionImportlibResourcesBackportReadTextCallBase,
    ExpressionImportlibResourcesFilesCallBase,
    ExpressionImportlibResourcesReadBinaryCallBase,
    ExpressionImportlibResourcesReadTextBefore313CallBase,
    ExpressionImportlibResourcesReadTextSince313CallBase,
    ExpressionPkgResourcesResourceStreamCallBase,
    ExpressionPkgResourcesResourceStringCallBase,
    ExpressionPkgutilGetDataCallBase,
)
from .NodeBases import SideEffectsFromChildrenMixin


class ExpressionPkgutilGetDataCall(
    (
        ExpressionBytesShapeExactMixin
        if str is not bytes
        else ExpressionStrShapeExactMixin
    ),
    SideEffectsFromChildrenMixin,
    ExpressionPkgutilGetDataCallBase,
):
    kind = "EXPRESSION_PKGUTIL_GET_DATA_CALL"

    named_children = ("package", "resource")

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionPkgResourcesResourceStringCall(
    (
        ExpressionBytesShapeExactMixin
        if str is not bytes
        else ExpressionStrShapeExactMixin
    ),
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
    """Call to "importlib.resources.read_binary" """

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


class ExpressionImportlibResourcesBackportReadBinaryCall(
    SideEffectsFromChildrenMixin,
    ExpressionImportlibResourcesBackportReadBinaryCallBase,
):
    """Call to "importlib.resources.read_binary" """

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_READ_BINARY_CALL"

    def __init__(self, package, resource, source_ref):
        ExpressionImportlibResourcesBackportReadBinaryCallBase.__init__(
            self,
            package=package,
            resource=resource,
            source_ref=source_ref,
        )

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


def makeExpressionImportlibResourcesReadTextBefore313Call(
    package, resource, encoding, errors, source_ref
):
    # Avoid making things optional.
    if encoding is None:
        encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)
    if errors is None:
        errors = makeConstantRefNode(constant="strict", source_ref=source_ref)

    return ExpressionImportlibResourcesReadTextBefore313Call(
        package=package,
        resource=resource,
        encoding=encoding,
        errors=errors,
        source_ref=source_ref,
    )


def makeExpressionImportlibResourcesReadTextSince313Call(
    package, resources, encoding, errors, source_ref
):
    # Avoid making things optional.
    if encoding is None:
        encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)
    if errors is None:
        errors = makeConstantRefNode(constant="strict", source_ref=source_ref)

    return ExpressionImportlibResourcesReadTextSince313Call(
        package=package,
        resources=resources,
        encoding=encoding,
        errors=errors,
        source_ref=source_ref,
    )


class ExpressionImportlibResourcesReadTextBefore313Call(
    SideEffectsFromChildrenMixin,
    ExpressionImportlibResourcesReadTextBefore313CallBase,
):
    """Call to "importlib.resources.read_text" """

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_BEFORE_313_CALL"

    python_version_spec = ">= 0x370"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionImportlibResourcesReadTextSince313Call(
    SideEffectsFromChildrenMixin,
    ExpressionImportlibResourcesReadTextSince313CallBase,
):
    """Call to "importlib.resources.read_text" """

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_SINCE_313_CALL"

    python_version_spec = ">= 0x3D0"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


def makeExpressionImportlibResourcesBackportReadTextCall(
    package, resource, encoding, errors, source_ref
):
    # Avoid making things optional.
    if encoding is None:
        encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)
    if errors is None:
        errors = makeConstantRefNode(constant="strict", source_ref=source_ref)

    return ExpressionImportlibResourcesBackportReadTextCall(
        package=package,
        resource=resource,
        encoding=encoding,
        errors=errors,
        source_ref=source_ref,
    )


class ExpressionImportlibResourcesBackportReadTextCall(
    SideEffectsFromChildrenMixin,
    ExpressionImportlibResourcesBackportReadTextCallBase,
):
    """Call to "importlib_resources.read_text" """

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_READ_TEXT_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionImportlibResourcesFilesCallMixin:
    __slots__ = ()

    def _getImportlibResourcesModule(self):
        return importFromCompileTime(self.importlib_resources_name, must_exist=True)

    # TODO: Looks as if this could be a convenience function of more general use.
    def makeModuleUsageAttempt(self, package_name):
        _package_name, module_filename, module_kind, finding = locateModule(
            module_name=package_name,
            parent_package=None,
            level=0,
        )

        return makeModuleUsageAttempt(
            module_name=package_name,
            filename=module_filename,
            module_kind=module_kind,
            finding=finding,
            level=0,
            source_ref=self.source_ref,
            reason="%s.files call" % self.importlib_resources_name,
        )

    # TODO: In standalone mode we could know a lot better.
    @staticmethod
    def mayRaiseExceptionOperation():
        return True

    # Only for the not fixed ones.
    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        package_name = self.subnode_package.getCompileTimeConstant()

        if type(package_name) is str:
            package_name = resolveModuleName(package_name)
            trace_collection.onModuleUsageAttempt(
                self.makeModuleUsageAttempt(package_name)
            )

            result = self.makeImportlibResourcesFilesCallFixedExpression(
                package_name=package_name, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Detected '%s.files' with constant package name '%s'."
                % (self.importlib_resources_name, package_name),
            )

        return self, None, None


class ExpressionImportlibResourcesFilesCallFixed(
    ExpressionImportlibResourcesFilesCallMixin, ExpressionBase
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_FILES_CALL_FIXED"
    python_version_spec = ">= 0x370"
    importlib_resources_name = "importlib.resources"

    __slots__ = (
        "package_name",
        "module_usage_attempt",
    )

    def __init__(self, package_name, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.package_name = resolveModuleName(package_name)

        self.module_usage_attempt = self.makeModuleUsageAttempt(
            package_name=package_name
        )

    def finalize(self):
        del self.module_usage_attempt

    def getPackageNameUsed(self):
        return makeConstantRefNode(
            constant=self.package_name.asString(), source_ref=self.source_ref
        )

    def computeExpressionRaw(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onModuleUsageAttempt(self.module_usage_attempt)

        return self, None, None


class ExpressionImportlibResourcesBackportFilesCallFixed(
    ExpressionImportlibResourcesFilesCallMixin, ExpressionBase
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_CALL_FIXED"
    importlib_resources_name = "importlib_resources"

    __slots__ = (
        "package_name",
        "module_usage_attempt",
    )

    def __init__(self, package_name, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.package_name = resolveModuleName(package_name)

        self.module_usage_attempt = self.makeModuleUsageAttempt(
            package_name=package_name
        )

    def finalize(self):
        del self.module_usage_attempt

    def getPackageNameUsed(self):
        return makeConstantRefNode(
            constant=self.package_name.asString(), source_ref=self.source_ref
        )

    def computeExpressionRaw(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onModuleUsageAttempt(self.module_usage_attempt)

        return self, None, None


class ExpressionImportlibResourcesFilesCall(
    ExpressionImportlibResourcesFilesCallMixin,
    ExpressionImportlibResourcesFilesCallBase,
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_FILES_CALL"
    python_version_spec = ">= 0x370"
    importlib_resources_name = "importlib.resources"
    makeImportlibResourcesFilesCallFixedExpression = (
        ExpressionImportlibResourcesFilesCallFixed
    )

    named_children = ("package",)

    __slots__ = ("module_usage_attempt",)

    def __init__(self, package, source_ref):
        ExpressionImportlibResourcesFilesCallBase.__init__(
            self, package=package, source_ref=source_ref
        )

        self.module_usage_attempt = None

    def getPackageNameUsed(self):
        return self.subnode_package


class ExpressionImportlibResourcesBackportFilesCall(
    ExpressionImportlibResourcesFilesCallMixin,
    ExpressionImportlibResourcesBackportFilesCallBase,
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_CALL"
    importlib_resources_name = "importlib_resources"
    makeImportlibResourcesFilesCallFixedExpression = (
        ExpressionImportlibResourcesBackportFilesCallFixed
    )

    named_children = ("package",)

    __slots__ = ("module_usage_attempt",)

    def __init__(self, package, source_ref):
        ExpressionImportlibResourcesBackportFilesCallBase.__init__(
            self, package=package, source_ref=source_ref
        )

        self.module_usage_attempt = None

    def getPackageNameUsed(self):
        return self.subnode_package


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
