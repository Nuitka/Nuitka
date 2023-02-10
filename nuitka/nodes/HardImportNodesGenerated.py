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
# We are not avoiding these in generated code at all
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long
# pylint: disable=I0021,too-many-instance-attributes
# pylint: disable=I0021,too-many-return-statements


"""Hard import nodes

WARNING, this code is GENERATED. Modify the template HardImportReferenceNode.py.j2 instead!

spell-checker: ignore append capitalize casefold center clear copy count decode encode endswith expandtabs extend find format formatmap get haskey index insert isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem remove replace reverse rfind rindex rjust rpartition rsplit rstrip setdefault sort split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default delete encoding end errors fillchar index item iterable keepends key maxsplit new old pairs prefix sep start stop sub suffix table tabsize value width
"""
import os
from abc import abstractmethod

from nuitka.Options import shallMakeModule
from nuitka.PythonVersions import python_version
from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs
from nuitka.specs.HardImportSpecs import (
    ctypes_cdll_before_38_spec,
    ctypes_cdll_since_38_spec,
    importlib_metadata_backport_distribution_spec,
    importlib_metadata_backport_entry_points_spec,
    importlib_metadata_backport_metadata_spec,
    importlib_metadata_backport_version_spec,
    importlib_metadata_distribution_spec,
    importlib_metadata_entry_points_before_310_spec,
    importlib_metadata_entry_points_since_310_spec,
    importlib_metadata_metadata_spec,
    importlib_metadata_version_spec,
    importlib_resources_read_binary_spec,
    importlib_resources_read_text_spec,
    os_listdir_spec,
    os_path_basename_spec,
    os_path_exists_spec,
    os_path_isdir_spec,
    os_path_isfile_spec,
    os_uname_spec,
    pkg_resources_get_distribution_spec,
    pkg_resources_iter_entry_points_spec,
    pkg_resources_require_spec,
    pkg_resources_resource_stream_spec,
    pkg_resources_resource_string_spec,
    pkgutil_get_data_spec,
)

from .ChildrenHavingMixins import (
    ChildHavingDistMixin,
    ChildHavingDistributionNameMixin,
    ChildHavingParamsTupleMixin,
    ChildHavingPathMixin,
    ChildHavingPathOptionalMixin,
    ChildHavingPMixin,
    ChildHavingRequirementsTupleMixin,
    ChildrenHavingGroupNameOptionalMixin,
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLasterrorOptionalMixin,
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLasterrorOptionalWinmodeOptionalMixin,
    ChildrenHavingPackageOrRequirementResourceNameMixin,
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin,
    ChildrenHavingPackageResourceMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import (
    ExpressionBytesShapeExactMixin,
    ExpressionDictShapeExactMixin,
    ExpressionStrShapeExactMixin,
)
from .ImportHardNodes import ExpressionImportModuleNameHardExistsSpecificBase

hard_import_node_classes = {}


class ExpressionCtypesCdllRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference ctypes.CDLL"""

    kind = "EXPRESSION_CTYPES_CDLL_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="ctypes",
            import_name="CDLL",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        if python_version >= 0x380:
            from .CtypesNodes import ExpressionCtypesCdllSince38Call

            result = extractBuiltinArgs(
                node=call_node,
                builtin_class=ExpressionCtypesCdllSince38Call,
                builtin_spec=ctypes_cdll_since_38_spec,
            )

            return (
                result,
                "new_expression",
                "Call to 'ctypes.CDLL' recognized.",
            )

        if python_version < 0x380:
            from .CtypesNodes import ExpressionCtypesCdllBefore38Call

            result = extractBuiltinArgs(
                node=call_node,
                builtin_class=ExpressionCtypesCdllBefore38Call,
                builtin_spec=ctypes_cdll_before_38_spec,
            )

            return (
                result,
                "new_expression",
                "Call to 'ctypes.CDLL' recognized.",
            )


hard_import_node_classes[ExpressionCtypesCdllRef] = ctypes_cdll_since_38_spec


class ExpressionCtypesCdllSince38CallBase(
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLasterrorOptionalWinmodeOptionalMixin,
    ExpressionBase,
):
    """Base class for CtypesCdllCall

    Generated boiler plate code.
    """

    python_version_spec = ">= 0x380"

    named_children = (
        "name",
        "mode|optional",
        "handle|optional",
        "use_errno|optional",
        "use_lasterror|optional",
        "winmode|optional",
    )

    __slots__ = ("attempted",)

    spec = ctypes_cdll_since_38_spec

    def __init__(
        self, name, mode, handle, use_errno, use_lasterror, winmode, source_ref
    ):

        ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLasterrorOptionalWinmodeOptionalMixin.__init__(
            self,
            name=name,
            mode=mode,
            handle=handle,
            use_errno=use_errno,
            use_lasterror=use_lasterror,
            winmode=winmode,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not ctypes_cdll_since_38_spec.isCompileTimeComputable(
            (
                self.subnode_name,
                self.subnode_mode,
                self.subnode_handle,
                self.subnode_use_errno,
                self.subnode_use_lasterror,
                self.subnode_winmode,
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionCtypesCdllBefore38CallBase(
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLasterrorOptionalMixin,
    ExpressionBase,
):
    """Base class for CtypesCdllCall

    Generated boiler plate code.
    """

    python_version_spec = "< 0x380"

    named_children = (
        "name",
        "mode|optional",
        "handle|optional",
        "use_errno|optional",
        "use_lasterror|optional",
    )

    __slots__ = ("attempted",)

    spec = ctypes_cdll_before_38_spec

    def __init__(self, name, mode, handle, use_errno, use_lasterror, source_ref):

        ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLasterrorOptionalMixin.__init__(
            self,
            name=name,
            mode=mode,
            handle=handle,
            use_errno=use_errno,
            use_lasterror=use_lasterror,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not ctypes_cdll_before_38_spec.isCompileTimeComputable(
            (
                self.subnode_name,
                self.subnode_mode,
                self.subnode_handle,
                self.subnode_use_errno,
                self.subnode_use_lasterror,
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataBackportDistributionRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_metadata.distribution"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_metadata",
            import_name="distribution",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            ExpressionImportlibMetadataBackportDistributionCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibMetadataBackportDistributionCall,
            builtin_spec=importlib_metadata_backport_distribution_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_metadata.distribution' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataBackportDistributionRef
] = importlib_metadata_backport_distribution_spec


class ExpressionImportlibMetadataBackportDistributionCallBase(
    ChildHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportDistributionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_backport_distribution_spec

    def __init__(self, distribution_name, source_ref):

        ChildHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_distribution_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataBackportEntryPointsRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_metadata.entry_points"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_metadata",
            import_name="entry_points",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            makeExpressionImportlibMetadataBackportEntryPointsCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=makeExpressionImportlibMetadataBackportEntryPointsCall,
            builtin_spec=importlib_metadata_backport_entry_points_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_metadata.entry_points' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataBackportEntryPointsRef
] = importlib_metadata_backport_entry_points_spec


class ExpressionImportlibMetadataBackportEntryPointsCallBase(
    ChildHavingParamsTupleMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportEntryPointsCall

    Generated boiler plate code.
    """

    named_children = ("params|tuple",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_backport_entry_points_spec

    def __init__(self, params, source_ref):

        ChildHavingParamsTupleMixin.__init__(
            self,
            params=params,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_entry_points_spec.isCompileTimeComputable(
                () + self.subnode_params
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataBackportMetadataRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_metadata.metadata"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_METADATA_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_metadata",
            import_name="metadata",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            makeExpressionImportlibMetadataBackportMetadataCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=makeExpressionImportlibMetadataBackportMetadataCall,
            builtin_spec=importlib_metadata_backport_metadata_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_metadata.metadata' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataBackportMetadataRef
] = importlib_metadata_backport_metadata_spec


class ExpressionImportlibMetadataBackportMetadataCallBase(
    ChildHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportMetadataCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_backport_metadata_spec

    def __init__(self, distribution_name, source_ref):

        ChildHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_metadata_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataBackportVersionRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_metadata.version"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_metadata",
            import_name="version",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            ExpressionImportlibMetadataBackportVersionCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibMetadataBackportVersionCall,
            builtin_spec=importlib_metadata_backport_version_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_metadata.version' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataBackportVersionRef
] = importlib_metadata_backport_version_spec


class ExpressionImportlibMetadataBackportVersionCallBase(
    ChildHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportVersionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_backport_version_spec

    def __init__(self, distribution_name, source_ref):

        ChildHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_version_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataDistributionRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.metadata.distribution"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.metadata",
            import_name="distribution",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            ExpressionImportlibMetadataDistributionCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibMetadataDistributionCall,
            builtin_spec=importlib_metadata_distribution_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.metadata.distribution' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataDistributionRef
] = importlib_metadata_distribution_spec


class ExpressionImportlibMetadataDistributionCallBase(
    ChildHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataDistributionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_distribution_spec

    def __init__(self, distribution_name, source_ref):

        ChildHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_distribution_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataEntryPointsRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.metadata.entry_points"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.metadata",
            import_name="entry_points",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        if python_version >= 0x3A0:
            from .PackageMetadataNodes import (
                makeExpressionImportlibMetadataEntryPointsSince310Call,
            )

            result = extractBuiltinArgs(
                node=call_node,
                builtin_class=makeExpressionImportlibMetadataEntryPointsSince310Call,
                builtin_spec=importlib_metadata_entry_points_since_310_spec,
            )

            return (
                result,
                "new_expression",
                "Call to 'importlib.metadata.entry_points' recognized.",
            )

        if python_version < 0x3A0:
            from .PackageMetadataNodes import (
                ExpressionImportlibMetadataEntryPointsBefore310Call,
            )

            result = extractBuiltinArgs(
                node=call_node,
                builtin_class=ExpressionImportlibMetadataEntryPointsBefore310Call,
                builtin_spec=importlib_metadata_entry_points_before_310_spec,
            )

            return (
                result,
                "new_expression",
                "Call to 'importlib.metadata.entry_points' recognized.",
            )


hard_import_node_classes[
    ExpressionImportlibMetadataEntryPointsRef
] = importlib_metadata_entry_points_since_310_spec


class ExpressionImportlibMetadataEntryPointsSince310CallBase(
    ChildHavingParamsTupleMixin, ExpressionBase
):
    """Base class for ImportlibMetadataEntryPointsCall

    Generated boiler plate code.
    """

    python_version_spec = ">= 0x3a0"

    named_children = ("params|tuple",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_entry_points_since_310_spec

    def __init__(self, params, source_ref):

        ChildHavingParamsTupleMixin.__init__(
            self,
            params=params,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_entry_points_since_310_spec.isCompileTimeComputable(
                () + self.subnode_params
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataEntryPointsBefore310CallBase(
    ExpressionDictShapeExactMixin, ExpressionBase
):
    """Base class for ImportlibMetadataEntryPointsCall

    Generated boiler plate code.
    """

    python_version_spec = "< 0x3a0"

    __slots__ = ("attempted",)

    spec = importlib_metadata_entry_points_before_310_spec

    def __init__(self, source_ref):

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def finalize(self):
        del self.parent

    def computeExpressionRaw(self, trace_collection):
        if self.attempted:
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataMetadataRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.metadata.metadata"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_METADATA_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.metadata",
            import_name="metadata",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            makeExpressionImportlibMetadataMetadataCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=makeExpressionImportlibMetadataMetadataCall,
            builtin_spec=importlib_metadata_metadata_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.metadata.metadata' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataMetadataRef
] = importlib_metadata_metadata_spec


class ExpressionImportlibMetadataMetadataCallBase(
    ChildHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataMetadataCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_metadata_spec

    def __init__(self, distribution_name, source_ref):

        ChildHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_metadata_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionImportlibMetadataVersionRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.metadata.version"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_VERSION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.metadata",
            import_name="version",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            ExpressionImportlibMetadataVersionCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibMetadataVersionCall,
            builtin_spec=importlib_metadata_version_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.metadata.version' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibMetadataVersionRef
] = importlib_metadata_version_spec


class ExpressionImportlibMetadataVersionCallBase(
    ChildHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataVersionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    spec = importlib_metadata_version_spec

    def __init__(self, distribution_name, source_ref):

        ChildHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_version_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


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
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            ExpressionImportlibResourcesReadBinaryCall,
        )

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


hard_import_node_classes[
    ExpressionImportlibResourcesReadBinaryRef
] = importlib_resources_read_binary_spec


class ExpressionImportlibResourcesReadBinaryCallBase(
    ExpressionBytesShapeExactMixin, ChildrenHavingPackageResourceMixin, ExpressionBase
):
    """Base class for ImportlibResourcesReadBinaryCall

    Generated boiler plate code.
    """

    named_children = (
        "package",
        "resource",
    )

    __slots__ = ("attempted",)

    spec = importlib_resources_read_binary_spec

    def __init__(self, package, resource, source_ref):

        ChildrenHavingPackageResourceMixin.__init__(
            self,
            package=package,
            resource=resource,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_resources_read_binary_spec.isCompileTimeComputable(
                (
                    self.subnode_package,
                    self.subnode_resource,
                )
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


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
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            makeExpressionImportlibResourcesReadTextCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=makeExpressionImportlibResourcesReadTextCall,
            builtin_spec=importlib_resources_read_text_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.resources.read_text' recognized.",
        )


hard_import_node_classes[
    ExpressionImportlibResourcesReadTextRef
] = importlib_resources_read_text_spec


class ExpressionImportlibResourcesReadTextCallBase(
    ExpressionStrShapeExactMixin,
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin,
    ExpressionBase,
):
    """Base class for ImportlibResourcesReadTextCall

    Generated boiler plate code.
    """

    named_children = (
        "package",
        "resource",
        "encoding|optional",
        "errors|optional",
    )

    __slots__ = ("attempted",)

    spec = importlib_resources_read_text_spec

    def __init__(self, package, resource, encoding, errors, source_ref):

        ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin.__init__(
            self,
            package=package,
            resource=resource,
            encoding=encoding,
            errors=errors,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_resources_read_text_spec.isCompileTimeComputable(
                (
                    self.subnode_package,
                    self.subnode_resource,
                    self.subnode_encoding,
                    self.subnode_errors,
                )
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionOsListdirRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.listdir"""

    kind = "EXPRESSION_OS_LISTDIR_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="os",
            import_name="listdir",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsListdirCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsListdirCall,
            builtin_spec=os_listdir_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.listdir' recognized.",
        )


hard_import_node_classes[ExpressionOsListdirRef] = os_listdir_spec


class ExpressionOsListdirCallBase(ChildHavingPathOptionalMixin, ExpressionBase):
    """Base class for OsListdirCall

    Generated boiler plate code.
    """

    named_children = ("path|optional",)

    __slots__ = ("attempted",)

    spec = os_listdir_spec

    def __init__(self, path, source_ref):

        ChildHavingPathOptionalMixin.__init__(
            self,
            path=path,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not os_listdir_spec.isCompileTimeComputable(
            (self.subnode_path,)
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionOsPathBasenameRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.basename"""

    kind = "EXPRESSION_OS_PATH_BASENAME_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="basename",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathBasenameCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathBasenameCall,
            builtin_spec=os_path_basename_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.basename' recognized.",
        )


hard_import_node_classes[ExpressionOsPathBasenameRef] = os_path_basename_spec


class ExpressionOsPathBasenameCallBase(ChildHavingPMixin, ExpressionBase):
    """Base class for OsPathBasenameCall

    Generated boiler plate code.
    """

    named_children = ("p",)

    __slots__ = ("attempted",)

    spec = os_path_basename_spec

    def __init__(self, p, source_ref):

        ChildHavingPMixin.__init__(
            self,
            p=p,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_basename_spec.isCompileTimeComputable(
            (self.subnode_p,)
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionOsPathExistsRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.exists"""

    kind = "EXPRESSION_OS_PATH_EXISTS_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="exists",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathExistsCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathExistsCall,
            builtin_spec=os_path_exists_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.exists' recognized.",
        )


hard_import_node_classes[ExpressionOsPathExistsRef] = os_path_exists_spec


class ExpressionOsPathExistsCallBase(ChildHavingPathMixin, ExpressionBase):
    """Base class for OsPathExistsCall

    Generated boiler plate code.
    """

    named_children = ("path",)

    __slots__ = ("attempted",)

    spec = os_path_exists_spec

    def __init__(self, path, source_ref):

        ChildHavingPathMixin.__init__(
            self,
            path=path,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_exists_spec.isCompileTimeComputable(
            (self.subnode_path,)
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionOsPathIsdirRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.isdir"""

    kind = "EXPRESSION_OS_PATH_ISDIR_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="isdir",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathIsdirCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathIsdirCall,
            builtin_spec=os_path_isdir_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.isdir' recognized.",
        )


hard_import_node_classes[ExpressionOsPathIsdirRef] = os_path_isdir_spec


class ExpressionOsPathIsdirCallBase(ChildHavingPathMixin, ExpressionBase):
    """Base class for OsPathIsdirCall

    Generated boiler plate code.
    """

    named_children = ("path",)

    __slots__ = ("attempted",)

    spec = os_path_isdir_spec

    def __init__(self, path, source_ref):

        ChildHavingPathMixin.__init__(
            self,
            path=path,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_isdir_spec.isCompileTimeComputable(
            (self.subnode_path,)
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionOsPathIsfileRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.isfile"""

    kind = "EXPRESSION_OS_PATH_ISFILE_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="isfile",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathIsfileCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathIsfileCall,
            builtin_spec=os_path_isfile_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.isfile' recognized.",
        )


hard_import_node_classes[ExpressionOsPathIsfileRef] = os_path_isfile_spec


class ExpressionOsPathIsfileCallBase(ChildHavingPathMixin, ExpressionBase):
    """Base class for OsPathIsfileCall

    Generated boiler plate code.
    """

    named_children = ("path",)

    __slots__ = ("attempted",)

    spec = os_path_isfile_spec

    def __init__(self, path, source_ref):

        ChildHavingPathMixin.__init__(
            self,
            path=path,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_isfile_spec.isCompileTimeComputable(
            (self.subnode_path,)
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


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
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsUnameCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsUnameCall,
            builtin_spec=os_uname_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.uname' recognized.",
        )


hard_import_node_classes[ExpressionOsUnameRef] = os_uname_spec


class ExpressionOsUnameCallBase(ExpressionBase):
    """Base class for OsUnameCall

    Generated boiler plate code.
    """

    __slots__ = ("attempted",)

    spec = os_uname_spec

    def __init__(self, source_ref):

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def finalize(self):
        del self.parent

    def computeExpressionRaw(self, trace_collection):
        if self.attempted:
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionPkgResourcesGetDistributionRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference pkg_resources.get_distribution"""

    kind = "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkg_resources",
            import_name="get_distribution",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            ExpressionPkgResourcesGetDistributionCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgResourcesGetDistributionCall,
            builtin_spec=pkg_resources_get_distribution_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkg_resources.get_distribution' recognized.",
        )


hard_import_node_classes[
    ExpressionPkgResourcesGetDistributionRef
] = pkg_resources_get_distribution_spec


class ExpressionPkgResourcesGetDistributionCallBase(
    ChildHavingDistMixin, ExpressionBase
):
    """Base class for PkgResourcesGetDistributionCall

    Generated boiler plate code.
    """

    named_children = ("dist",)

    __slots__ = ("attempted",)

    spec = pkg_resources_get_distribution_spec

    def __init__(self, dist, source_ref):

        ChildHavingDistMixin.__init__(
            self,
            dist=dist,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_get_distribution_spec.isCompileTimeComputable(
                (self.subnode_dist,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionPkgResourcesIterEntryPointsRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference pkg_resources.iter_entry_points"""

    kind = "EXPRESSION_PKG_RESOURCES_ITER_ENTRY_POINTS_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkg_resources",
            import_name="iter_entry_points",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import (
            ExpressionPkgResourcesIterEntryPointsCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgResourcesIterEntryPointsCall,
            builtin_spec=pkg_resources_iter_entry_points_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkg_resources.iter_entry_points' recognized.",
        )


hard_import_node_classes[
    ExpressionPkgResourcesIterEntryPointsRef
] = pkg_resources_iter_entry_points_spec


class ExpressionPkgResourcesIterEntryPointsCallBase(
    ChildrenHavingGroupNameOptionalMixin, ExpressionBase
):
    """Base class for PkgResourcesIterEntryPointsCall

    Generated boiler plate code.
    """

    named_children = (
        "group",
        "name|optional",
    )

    __slots__ = ("attempted",)

    spec = pkg_resources_iter_entry_points_spec

    def __init__(self, group, name, source_ref):

        ChildrenHavingGroupNameOptionalMixin.__init__(
            self,
            group=group,
            name=name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_iter_entry_points_spec.isCompileTimeComputable(
                (
                    self.subnode_group,
                    self.subnode_name,
                )
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionPkgResourcesRequireRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference pkg_resources.require"""

    kind = "EXPRESSION_PKG_RESOURCES_REQUIRE_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkg_resources",
            import_name="require",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageMetadataNodes import ExpressionPkgResourcesRequireCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgResourcesRequireCall,
            builtin_spec=pkg_resources_require_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkg_resources.require' recognized.",
        )


hard_import_node_classes[ExpressionPkgResourcesRequireRef] = pkg_resources_require_spec


class ExpressionPkgResourcesRequireCallBase(
    ChildHavingRequirementsTupleMixin, ExpressionBase
):
    """Base class for PkgResourcesRequireCall

    Generated boiler plate code.
    """

    named_children = ("requirements|tuple",)

    __slots__ = ("attempted",)

    spec = pkg_resources_require_spec

    def __init__(self, requirements, source_ref):

        ChildHavingRequirementsTupleMixin.__init__(
            self,
            requirements=requirements,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not pkg_resources_require_spec.isCompileTimeComputable(
            () + self.subnode_requirements
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


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
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            ExpressionPkgResourcesResourceStreamCall,
        )

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


hard_import_node_classes[
    ExpressionPkgResourcesResourceStreamRef
] = pkg_resources_resource_stream_spec


class ExpressionPkgResourcesResourceStreamCallBase(
    ChildrenHavingPackageOrRequirementResourceNameMixin, ExpressionBase
):
    """Base class for PkgResourcesResourceStreamCall

    Generated boiler plate code.
    """

    named_children = (
        "package_or_requirement",
        "resource_name",
    )

    __slots__ = ("attempted",)

    spec = pkg_resources_resource_stream_spec

    def __init__(self, package_or_requirement, resource_name, source_ref):

        ChildrenHavingPackageOrRequirementResourceNameMixin.__init__(
            self,
            package_or_requirement=package_or_requirement,
            resource_name=resource_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_resource_stream_spec.isCompileTimeComputable(
                (
                    self.subnode_package_or_requirement,
                    self.subnode_resource_name,
                )
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


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
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            ExpressionPkgResourcesResourceStringCall,
        )

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


hard_import_node_classes[
    ExpressionPkgResourcesResourceStringRef
] = pkg_resources_resource_string_spec


class ExpressionPkgResourcesResourceStringCallBase(
    ChildrenHavingPackageOrRequirementResourceNameMixin, ExpressionBase
):
    """Base class for PkgResourcesResourceStringCall

    Generated boiler plate code.
    """

    named_children = (
        "package_or_requirement",
        "resource_name",
    )

    __slots__ = ("attempted",)

    spec = pkg_resources_resource_string_spec

    def __init__(self, package_or_requirement, resource_name, source_ref):

        ChildrenHavingPackageOrRequirementResourceNameMixin.__init__(
            self,
            package_or_requirement=package_or_requirement,
            resource_name=resource_name,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_resource_string_spec.isCompileTimeComputable(
                (
                    self.subnode_package_or_requirement,
                    self.subnode_resource_name,
                )
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionPkgutilGetDataRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference pkgutil.get_data"""

    kind = "EXPRESSION_PKGUTIL_GET_DATA_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="pkgutil",
            import_name="get_data",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import ExpressionPkgutilGetDataCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgutilGetDataCall,
            builtin_spec=pkgutil_get_data_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkgutil.get_data' recognized.",
        )


hard_import_node_classes[ExpressionPkgutilGetDataRef] = pkgutil_get_data_spec


class ExpressionPkgutilGetDataCallBase(
    ChildrenHavingPackageResourceMixin, ExpressionBase
):
    """Base class for PkgutilGetDataCall

    Generated boiler plate code.
    """

    named_children = (
        "package",
        "resource",
    )

    __slots__ = ("attempted",)

    spec = pkgutil_get_data_spec

    def __init__(self, package, resource, source_ref):

        ChildrenHavingPackageResourceMixin.__init__(
            self,
            package=package,
            resource=resource,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not pkgutil_get_data_spec.isCompileTimeComputable(
            (
                self.subnode_package,
                self.subnode_resource,
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        try:
            return self.replaceWithCompileTimeValue(trace_collection)
        finally:
            self.attempted = True

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionOperation():
        return True
