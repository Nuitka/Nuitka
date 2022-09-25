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

import os

from nuitka.Options import shallMakeModule
from nuitka.specs.BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    extractBuiltinArgs,
)

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import (
    ExpressionBase,
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
    ExpressionNoSideEffectsMixin,
)
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionBytesShapeExactMixin,
    ExpressionStrShapeExactMixin,
)
from .ImportHardNodes import ExpressionImportModuleNameHardExistsSpecificBase
from .NodeBases import SideEffectsFromChildrenMixin

pkgutil_get_data_spec = BuiltinParameterSpec(
    "pkg_util.get_data", ("package", "resource"), default_count=0
)
pkg_resources_resource_string_spec = BuiltinParameterSpec(
    "pkg_resources.resource_string",
    ("package_or_requirement", "resource_name"),
    default_count=0,
)
pkg_resources_resource_stream_spec = BuiltinParameterSpec(
    "pkg_resources.resource_stream",
    ("package_or_requirement", "resource_name"),
    default_count=0,
)
importlib_resources_read_binary_spec = BuiltinParameterSpec(
    "importlib.resources.read_binary",
    ("package", "resource"),
    default_count=0,
)
importlib_resources_read_text_spec = BuiltinParameterSpec(
    "importlib.resources.read_text",
    ("package", "resource", "encoding", "errors"),
    default_count=2,
)


class ExpressionPkglibGetDataRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference pkgutil.get_data"""

    kind = "EXPRESSION_PKGLIB_GET_DATA_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkgutil",
            import_name="get_data",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkglibGetDataCall,
            builtin_spec=pkgutil_get_data_spec,
        )

        return result, "new_expression", "Call to 'pkgutil.get_data' recognized."


class ExpressionPkglibGetDataCall(
    ExpressionBytesShapeExactMixin
    if str is not bytes
    else ExpressionStrShapeExactMixin,
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


class ExpressionPkgResourcesResourceStringRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference pkg_resources.resource_string"""

    kind = "EXPRESSION_PKG_RESOURCES_RESOURCE_STRING_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkg_resources",
            import_name="resource_string",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgResourcesResourceStringCall,
            builtin_spec=pkg_resources_resource_string_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkg_resources.resource_string' recognized.",
        )


class ExpressionPkgResourcesResourceStringCall(
    ExpressionBytesShapeExactMixin
    if str is not bytes
    else ExpressionStrShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionChildrenHavingBase,
):

    kind = "EXPRESSION_PKG_RESOURCES_RESOURCE_STRING_CALL"

    named_children = ("package", "resource")

    # Renamed arguments, otherwise similar to pkgutil.get_data
    def __init__(self, package_or_requirement, resource_name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            {"package": package_or_requirement, "resource": resource_name},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionPkgResourcesResourceStreamRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference pkg_resources.resource_stream"""

    kind = "EXPRESSION_PKG_RESOURCES_RESOURCE_STREAM_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkg_resources",
            import_name="resource_stream",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgResourcesResourceStreamCall,
            builtin_spec=pkg_resources_resource_stream_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkg_resources.resource_stream' recognized.",
        )


class ExpressionPkgResourcesResourceStreamCall(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_PKG_RESOURCES_RESOURCE_STREAM_CALL"

    named_children = ("package", "resource")

    def __init__(self, package_or_requirement, resource_name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            {"package": package_or_requirement, "resource": resource_name},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionImportlibResourcesReadBinaryRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.resources.read_binary"""

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_BINARY_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.resources",
            import_name="read_binary",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibResourcesReadBinaryCall,
            builtin_spec=importlib_resources_read_binary_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.resources.read_binary' recognized.",
        )


class ExpressionImportlibResourcesReadBinaryCall(
    ExpressionBytesShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionChildrenHavingBase,
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_BINARY_CALL"

    named_children = ("package", "resource")

    def __init__(self, package, resource, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, {"package": package, "resource": resource}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionImportlibResourcesReadTextRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.resources.read_text"""

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.resources",
            import_name="read_text",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibResourcesReadTextCall,
            builtin_spec=importlib_resources_read_text_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.resources.read_text' recognized.",
        )


class ExpressionImportlibResourcesReadTextCall(
    ExpressionStrShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionChildrenHavingBase,
):
    kind = "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_CALL"

    named_children = ("package", "resource", "encoding", "errors")

    def __init__(self, package, resource, encoding, errors, source_ref):
        if encoding is None:
            encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)
        if errors is None:
            errors = makeConstantRefNode(constant="strict", source_ref=source_ref)

        ExpressionChildrenHavingBase.__init__(
            self,
            {
                "package": package,
                "resource": resource,
                "encoding": encoding,
                "errors": errors,
            },
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


os_uname_spec = BuiltinParameterSpec(
    "os.uname",
    (),
    default_count=0,
)


# TODO: These types of nodes need a better organisation and potentially be generated.
class ExpressionOsUnameRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.uname"""

    kind = "EXPRESSION_OS_UNAME_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="os",
            import_name="uname",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsUnameCall,
            builtin_spec=os_uname_spec,
        )

        return result, "new_expression", "Call to 'os.uname' recognized."


class ExpressionOsUnameCall(
    # TODO: We don*t have this
    # ExpressionTupleShapeDerivedMixin,
    ExpressionNoSideEffectsMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_OS_UNAME_CALL"

    @staticmethod
    def finalize():
        pass

    def computeExpressionRaw(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathTestCallBase(
    ExpressionBoolShapeExactMixin,
    ExpressionChildHavingBase,
):
    named_child = "path"

    def __init__(self, path, source_ref):
        ExpressionChildHavingBase.__init__(self, value=path, source_ref=source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathExistsCall(ExpressionOsPathTestCallBase):
    kind = "EXPRESSION_OS_PATH_EXISTS_CALL"


class ExpressionOsPathIsfileCall(ExpressionOsPathTestCallBase):
    kind = "EXPRESSION_OS_PATH_ISFILE_CALL"


class ExpressionOsPathIsdirCall(ExpressionOsPathTestCallBase):
    kind = "EXPRESSION_OS_PATH_ISDIR_CALL"


class ExpressionOsPathTestRefBase(ExpressionImportModuleNameHardExistsSpecificBase):
    """Base class for function reference like os.path.exists"""

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name=self.spec.name.split(".")[-1],
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=self.call_node_class,
            builtin_spec=self.spec,
        )

        return result, "new_expression", "Call to '%s' recognized." % self.spec.name


class ExpressionOsPathExistsRef(ExpressionOsPathTestRefBase):
    """Function reference os.path.exists"""

    kind = "EXPRESSION_OS_PATH_EXISTS_REF"

    spec = BuiltinParameterSpec("os.path.exists", ("path",), default_count=0)

    call_node_class = ExpressionOsPathExistsCall


class ExpressionOsPathIsfileRef(ExpressionOsPathTestRefBase):
    """Function reference os.path.isfile"""

    kind = "EXPRESSION_OS_PATH_ISFILE_REF"

    spec = BuiltinParameterSpec("os.path.isfile", ("path",), default_count=0)

    call_node_class = ExpressionOsPathIsfileCall


class ExpressionOsPathIsdirRef(ExpressionOsPathTestRefBase):
    """Function reference os.path.isdir"""

    kind = "EXPRESSION_OS_PATH_ISDIR_REF"

    spec = BuiltinParameterSpec("os.path.isdir", ("path",), default_count=0)

    call_node_class = ExpressionOsPathIsdirCall
