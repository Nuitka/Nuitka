#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements


"""Hard import nodes

WARNING, this code is GENERATED. Modify the template HardImportReferenceNode.py.j2 instead!

spell-checker: ignore __prepare__ append args autograph capitalize casefold center chars
spell-checker: ignore clear copy count decode default delete dist distribution_name encode
spell-checker: ignore encoding end endswith errors exit_code expandtabs
spell-checker: ignore experimental_attributes experimental_autograph_options
spell-checker: ignore experimental_compile experimental_follow_type_hints
spell-checker: ignore experimental_implements experimental_relax_shapes extend fillchar
spell-checker: ignore find format format_map formatmap fromkeys func get group handle
spell-checker: ignore has_key haskey index input_signature insert isalnum isalpha isascii
spell-checker: ignore isdecimal isdigit isidentifier islower isnumeric isprintable isspace
spell-checker: ignore istitle isupper item items iterable iteritems iterkeys itervalues
spell-checker: ignore jit_compile join keepends key keys kwargs ljust lower lstrip
spell-checker: ignore maketrans maxsplit mode name new old p package
spell-checker: ignore package_or_requirement pairs partition path pop popitem prefix
spell-checker: ignore prepare reduce_retracing remove replace resource resource_name
spell-checker: ignore reverse rfind rindex rjust rpartition rsplit rstrip s sep setdefault
spell-checker: ignore sort split splitlines start startswith stop strip sub suffix
spell-checker: ignore swapcase table tabsize title translate update upper use_errno
spell-checker: ignore use_last_error value values viewitems viewkeys viewvalues width
spell-checker: ignore winmode zfill
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
    importlib_resources_backport_files_spec,
    importlib_resources_backport_read_binary_spec,
    importlib_resources_backport_read_text_spec,
    importlib_resources_files_spec,
    importlib_resources_read_binary_spec,
    importlib_resources_read_text_spec,
    os_listdir_spec,
    os_lstat_spec,
    os_path_abspath_spec,
    os_path_basename_spec,
    os_path_dirname_spec,
    os_path_exists_spec,
    os_path_isabs_spec,
    os_path_isdir_spec,
    os_path_isfile_spec,
    os_path_normpath_spec,
    os_stat_spec,
    os_uname_spec,
    pkg_resources_get_distribution_spec,
    pkg_resources_iter_entry_points_spec,
    pkg_resources_require_spec,
    pkg_resources_resource_stream_spec,
    pkg_resources_resource_string_spec,
    pkgutil_get_data_spec,
    sys_exit_spec,
    tensorflow_function_spec,
)

from .ChildrenHavingMixins import (
    ChildHavingDistMixin,
    ChildHavingDistributionNameMixin,
    ChildHavingExitCodeOptionalMixin,
    ChildHavingPackageMixin,
    ChildHavingParamsTupleMixin,
    ChildHavingPathMixin,
    ChildHavingPathOptionalMixin,
    ChildHavingPMixin,
    ChildHavingRequirementsTupleMixin,
    ChildHavingSMixin,
    ChildrenHavingFuncOptionalInputSignatureOptionalAutographOptionalJitCompileOptionalReduceRetracingOptionalExperimentalImplementsOptionalExperimentalAutographOptionsOptionalExperimentalAttributesOptionalExperimentalRelaxShapesOptionalExperimentalCompileOptionalExperimentalFollowTypeHintsOptionalMixin,
    ChildrenHavingGroupNameOptionalMixin,
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalMixin,
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalWinmodeOptionalMixin,
    ChildrenHavingPackageOrRequirementResourceNameMixin,
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin,
    ChildrenHavingPackageResourceMixin,
    ChildrenHavingPathOptionalDirFdOptionalFollowSymlinksOptionalMixin,
    ChildrenHavingPathOptionalDirFdOptionalMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
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
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalWinmodeOptionalMixin,
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
        "use_last_error|optional",
        "winmode|optional",
    )

    __slots__ = ("attempted",)

    spec = ctypes_cdll_since_38_spec

    def __init__(
        self, name, mode, handle, use_errno, use_last_error, winmode, source_ref
    ):

        ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalWinmodeOptionalMixin.__init__(
            self,
            name=name,
            mode=mode,
            handle=handle,
            use_errno=use_errno,
            use_last_error=use_last_error,
            winmode=winmode,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not ctypes_cdll_since_38_spec.isCompileTimeComputable(
            (
                self.subnode_name,
                self.subnode_mode,
                self.subnode_handle,
                self.subnode_use_errno,
                self.subnode_use_last_error,
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
    ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalMixin,
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
        "use_last_error|optional",
    )

    __slots__ = ("attempted",)

    spec = ctypes_cdll_before_38_spec

    def __init__(self, name, mode, handle, use_errno, use_last_error, source_ref):

        ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalMixin.__init__(
            self,
            name=name,
            mode=mode,
            handle=handle,
            use_errno=use_errno,
            use_last_error=use_last_error,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not ctypes_cdll_before_38_spec.isCompileTimeComputable(
            (
                self.subnode_name,
                self.subnode_mode,
                self.subnode_handle,
                self.subnode_use_errno,
                self.subnode_use_last_error,
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


hard_import_node_classes[ExpressionImportlibMetadataBackportDistributionRef] = (
    importlib_metadata_backport_distribution_spec
)


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


hard_import_node_classes[ExpressionImportlibMetadataBackportEntryPointsRef] = (
    importlib_metadata_backport_entry_points_spec
)


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


hard_import_node_classes[ExpressionImportlibMetadataBackportMetadataRef] = (
    importlib_metadata_backport_metadata_spec
)


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


hard_import_node_classes[ExpressionImportlibMetadataBackportVersionRef] = (
    importlib_metadata_backport_version_spec
)


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


hard_import_node_classes[ExpressionImportlibMetadataDistributionRef] = (
    importlib_metadata_distribution_spec
)


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

        self.attempted = False

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


hard_import_node_classes[ExpressionImportlibMetadataEntryPointsRef] = (
    importlib_metadata_entry_points_since_310_spec
)


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

        self.attempted = False

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

        self.attempted = False

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


hard_import_node_classes[ExpressionImportlibMetadataMetadataRef] = (
    importlib_metadata_metadata_spec
)


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

        self.attempted = False

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


hard_import_node_classes[ExpressionImportlibMetadataVersionRef] = (
    importlib_metadata_version_spec
)


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

        self.attempted = False

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


class ExpressionImportlibResourcesBackportFilesRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_resources.files"""

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_resources",
            import_name="files",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            ExpressionImportlibResourcesBackportFilesCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibResourcesBackportFilesCall,
            builtin_spec=importlib_resources_backport_files_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_resources.files' recognized.",
        )


hard_import_node_classes[ExpressionImportlibResourcesBackportFilesRef] = (
    importlib_resources_backport_files_spec
)


class ExpressionImportlibResourcesBackportFilesCallBase(
    ChildHavingPackageMixin, ExpressionBase
):
    """Base class for ImportlibResourcesBackportFilesCall

    Generated boiler plate code.
    """

    named_children = ("package",)

    __slots__ = ("attempted",)

    spec = importlib_resources_backport_files_spec

    def __init__(self, package, source_ref):

        ChildHavingPackageMixin.__init__(
            self,
            package=package,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_resources_backport_files_spec.isCompileTimeComputable(
                (self.subnode_package,)
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


class ExpressionImportlibResourcesBackportReadBinaryRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_resources.read_binary"""

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_READ_BINARY_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_resources",
            import_name="read_binary",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            ExpressionImportlibResourcesBackportReadBinaryCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibResourcesBackportReadBinaryCall,
            builtin_spec=importlib_resources_backport_read_binary_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_resources.read_binary' recognized.",
        )


hard_import_node_classes[ExpressionImportlibResourcesBackportReadBinaryRef] = (
    importlib_resources_backport_read_binary_spec
)


class ExpressionImportlibResourcesBackportReadBinaryCallBase(
    ExpressionBytesShapeExactMixin, ChildrenHavingPackageResourceMixin, ExpressionBase
):
    """Base class for ImportlibResourcesBackportReadBinaryCall

    Generated boiler plate code.
    """

    named_children = (
        "package",
        "resource",
    )

    __slots__ = ("attempted",)

    spec = importlib_resources_backport_read_binary_spec

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
            or not importlib_resources_backport_read_binary_spec.isCompileTimeComputable(
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


class ExpressionImportlibResourcesBackportReadTextRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib_resources.read_text"""

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_READ_TEXT_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib_resources",
            import_name="read_text",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import (
            makeExpressionImportlibResourcesBackportReadTextCall,
        )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=makeExpressionImportlibResourcesBackportReadTextCall,
            builtin_spec=importlib_resources_backport_read_text_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_resources.read_text' recognized.",
        )


hard_import_node_classes[ExpressionImportlibResourcesBackportReadTextRef] = (
    importlib_resources_backport_read_text_spec
)


class ExpressionImportlibResourcesBackportReadTextCallBase(
    ExpressionStrShapeExactMixin,
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin,
    ExpressionBase,
):
    """Base class for ImportlibResourcesBackportReadTextCall

    Generated boiler plate code.
    """

    named_children = (
        "package",
        "resource",
        "encoding|optional",
        "errors|optional",
    )

    __slots__ = ("attempted",)

    spec = importlib_resources_backport_read_text_spec

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
            or not importlib_resources_backport_read_text_spec.isCompileTimeComputable(
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


class ExpressionImportlibResourcesFilesRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    """Function reference importlib.resources.files"""

    kind = "EXPRESSION_IMPORTLIB_RESOURCES_FILES_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib.resources",
            import_name="files",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .PackageResourceNodes import ExpressionImportlibResourcesFilesCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibResourcesFilesCall,
            builtin_spec=importlib_resources_files_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib.resources.files' recognized.",
        )


hard_import_node_classes[ExpressionImportlibResourcesFilesRef] = (
    importlib_resources_files_spec
)


class ExpressionImportlibResourcesFilesCallBase(
    ChildHavingPackageMixin, ExpressionBase
):
    """Base class for ImportlibResourcesFilesCall

    Generated boiler plate code.
    """

    named_children = ("package",)

    __slots__ = ("attempted",)

    spec = importlib_resources_files_spec

    def __init__(self, package, source_ref):

        ChildHavingPackageMixin.__init__(
            self,
            package=package,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_resources_files_spec.isCompileTimeComputable(
                (self.subnode_package,)
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


hard_import_node_classes[ExpressionImportlibResourcesReadBinaryRef] = (
    importlib_resources_read_binary_spec
)


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

        self.attempted = False

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


hard_import_node_classes[ExpressionImportlibResourcesReadTextRef] = (
    importlib_resources_read_text_spec
)


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

        self.attempted = False

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

        self.attempted = False

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


class ExpressionOsLstatRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.lstat"""

    kind = "EXPRESSION_OS_LSTAT_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="os",
            import_name="lstat",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsLstatCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsLstatCall,
            builtin_spec=os_lstat_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.lstat' recognized.",
        )


hard_import_node_classes[ExpressionOsLstatRef] = os_lstat_spec


class ExpressionOsLstatCallBase(
    ChildrenHavingPathOptionalDirFdOptionalMixin, ExpressionBase
):
    """Base class for OsLstatCall

    Generated boiler plate code.
    """

    named_children = (
        "path|optional",
        "dir_fd|optional",
    )

    __slots__ = ("attempted",)

    spec = os_lstat_spec

    def __init__(self, path, dir_fd, source_ref):

        ChildrenHavingPathOptionalDirFdOptionalMixin.__init__(
            self,
            path=path,
            dir_fd=dir_fd,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not os_lstat_spec.isCompileTimeComputable(
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


class ExpressionOsPathAbspathRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.abspath"""

    kind = "EXPRESSION_OS_PATH_ABSPATH_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="abspath",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathAbspathCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathAbspathCall,
            builtin_spec=os_path_abspath_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.abspath' recognized.",
        )


hard_import_node_classes[ExpressionOsPathAbspathRef] = os_path_abspath_spec


class ExpressionOsPathAbspathCallBase(ChildHavingPathMixin, ExpressionBase):
    """Base class for OsPathAbspathCall

    Generated boiler plate code.
    """

    named_children = ("path",)

    __slots__ = ("attempted",)

    spec = os_path_abspath_spec

    def __init__(self, path, source_ref):

        ChildHavingPathMixin.__init__(
            self,
            path=path,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_abspath_spec.isCompileTimeComputable(
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

        self.attempted = False

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


class ExpressionOsPathDirnameRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.dirname"""

    kind = "EXPRESSION_OS_PATH_DIRNAME_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="dirname",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathDirnameCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathDirnameCall,
            builtin_spec=os_path_dirname_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.dirname' recognized.",
        )


hard_import_node_classes[ExpressionOsPathDirnameRef] = os_path_dirname_spec


class ExpressionOsPathDirnameCallBase(ChildHavingPMixin, ExpressionBase):
    """Base class for OsPathDirnameCall

    Generated boiler plate code.
    """

    named_children = ("p",)

    __slots__ = ("attempted",)

    spec = os_path_dirname_spec

    def __init__(self, p, source_ref):

        ChildHavingPMixin.__init__(
            self,
            p=p,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_dirname_spec.isCompileTimeComputable(
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

        self.attempted = False

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


class ExpressionOsPathIsabsRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.isabs"""

    kind = "EXPRESSION_OS_PATH_ISABS_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="isabs",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathIsabsCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathIsabsCall,
            builtin_spec=os_path_isabs_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.isabs' recognized.",
        )


hard_import_node_classes[ExpressionOsPathIsabsRef] = os_path_isabs_spec


class ExpressionOsPathIsabsCallBase(
    ExpressionBoolShapeExactMixin, ChildHavingSMixin, ExpressionBase
):
    """Base class for OsPathIsabsCall

    Generated boiler plate code.
    """

    named_children = ("s",)

    __slots__ = ("attempted",)

    spec = os_path_isabs_spec

    def __init__(self, s, source_ref):

        ChildHavingSMixin.__init__(
            self,
            s=s,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_isabs_spec.isCompileTimeComputable(
            (self.subnode_s,)
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

        self.attempted = False

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

        self.attempted = False

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


class ExpressionOsPathNormpathRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.path.normpath"""

    kind = "EXPRESSION_OS_PATH_NORMPATH_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name=os.path.__name__,
            import_name="normpath",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsPathNormpathCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsPathNormpathCall,
            builtin_spec=os_path_normpath_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.path.normpath' recognized.",
        )


hard_import_node_classes[ExpressionOsPathNormpathRef] = os_path_normpath_spec


class ExpressionOsPathNormpathCallBase(ChildHavingPathMixin, ExpressionBase):
    """Base class for OsPathNormpathCall

    Generated boiler plate code.
    """

    named_children = ("path",)

    __slots__ = ("attempted",)

    spec = os_path_normpath_spec

    def __init__(self, path, source_ref):

        ChildHavingPathMixin.__init__(
            self,
            path=path,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not os_path_normpath_spec.isCompileTimeComputable(
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


class ExpressionOsStatRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference os.stat"""

    kind = "EXPRESSION_OS_STAT_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="os",
            import_name="stat",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import ExpressionOsStatCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionOsStatCall,
            builtin_spec=os_stat_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'os.stat' recognized.",
        )


hard_import_node_classes[ExpressionOsStatRef] = os_stat_spec


class ExpressionOsStatCallBase(
    ChildrenHavingPathOptionalDirFdOptionalFollowSymlinksOptionalMixin, ExpressionBase
):
    """Base class for OsStatCall

    Generated boiler plate code.
    """

    named_children = (
        "path|optional",
        "dir_fd|optional",
        "follow_symlinks|optional",
    )

    __slots__ = ("attempted",)

    spec = os_stat_spec

    def __init__(self, path, dir_fd, follow_symlinks, source_ref):

        ChildrenHavingPathOptionalDirFdOptionalFollowSymlinksOptionalMixin.__init__(
            self,
            path=path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )

        ExpressionBase.__init__(self, source_ref)

        self.attempted = False

    def computeExpression(self, trace_collection):
        if self.attempted or not os_stat_spec.isCompileTimeComputable(
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

        self.attempted = False

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


hard_import_node_classes[ExpressionPkgResourcesGetDistributionRef] = (
    pkg_resources_get_distribution_spec
)


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


hard_import_node_classes[ExpressionPkgResourcesIterEntryPointsRef] = (
    pkg_resources_iter_entry_points_spec
)


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


hard_import_node_classes[ExpressionPkgResourcesResourceStreamRef] = (
    pkg_resources_resource_stream_spec
)


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


hard_import_node_classes[ExpressionPkgResourcesResourceStringRef] = (
    pkg_resources_resource_string_spec
)


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

        self.attempted = False

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


class ExpressionSysExitRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference sys.exit"""

    kind = "EXPRESSION_SYS_EXIT_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="sys",
            import_name="exit",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .OsSysNodes import makeExpressionSysExitCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=makeExpressionSysExitCall,
            builtin_spec=sys_exit_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'sys.exit' recognized.",
        )


hard_import_node_classes[ExpressionSysExitRef] = sys_exit_spec


class ExpressionSysExitCallBase(ChildHavingExitCodeOptionalMixin, ExpressionBase):
    """Base class for SysExitCall

    Generated boiler plate code.
    """

    named_children = ("exit_code|optional",)

    __slots__ = ("attempted",)

    spec = sys_exit_spec

    def __init__(self, exit_code, source_ref):

        ChildHavingExitCodeOptionalMixin.__init__(
            self,
            exit_code=exit_code,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not sys_exit_spec.isCompileTimeComputable(
            (self.subnode_exit_code,)
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


class ExpressionTensorflowFunctionRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference tensorflow.function"""

    kind = "EXPRESSION_TENSORFLOW_FUNCTION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="tensorflow",
            import_name="function",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen on call trace before this. On next pass, if
        # replaced, we might be better but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        from .TensorflowNodes import ExpressionTensorflowFunctionCall

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionTensorflowFunctionCall,
            builtin_spec=tensorflow_function_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'tensorflow.function' recognized.",
        )


hard_import_node_classes[ExpressionTensorflowFunctionRef] = tensorflow_function_spec


class ExpressionTensorflowFunctionCallBase(
    ChildrenHavingFuncOptionalInputSignatureOptionalAutographOptionalJitCompileOptionalReduceRetracingOptionalExperimentalImplementsOptionalExperimentalAutographOptionsOptionalExperimentalAttributesOptionalExperimentalRelaxShapesOptionalExperimentalCompileOptionalExperimentalFollowTypeHintsOptionalMixin,
    ExpressionBase,
):
    """Base class for TensorflowFunctionCall

    Generated boiler plate code.
    """

    named_children = (
        "func|optional",
        "input_signature|optional",
        "autograph|optional",
        "jit_compile|optional",
        "reduce_retracing|optional",
        "experimental_implements|optional",
        "experimental_autograph_options|optional",
        "experimental_attributes|optional",
        "experimental_relax_shapes|optional",
        "experimental_compile|optional",
        "experimental_follow_type_hints|optional",
    )

    __slots__ = ("attempted",)

    spec = tensorflow_function_spec

    def __init__(
        self,
        func,
        input_signature,
        autograph,
        jit_compile,
        reduce_retracing,
        experimental_implements,
        experimental_autograph_options,
        experimental_attributes,
        experimental_relax_shapes,
        experimental_compile,
        experimental_follow_type_hints,
        source_ref,
    ):

        ChildrenHavingFuncOptionalInputSignatureOptionalAutographOptionalJitCompileOptionalReduceRetracingOptionalExperimentalImplementsOptionalExperimentalAutographOptionsOptionalExperimentalAttributesOptionalExperimentalRelaxShapesOptionalExperimentalCompileOptionalExperimentalFollowTypeHintsOptionalMixin.__init__(
            self,
            func=func,
            input_signature=input_signature,
            autograph=autograph,
            jit_compile=jit_compile,
            reduce_retracing=reduce_retracing,
            experimental_implements=experimental_implements,
            experimental_autograph_options=experimental_autograph_options,
            experimental_attributes=experimental_attributes,
            experimental_relax_shapes=experimental_relax_shapes,
            experimental_compile=experimental_compile,
            experimental_follow_type_hints=experimental_follow_type_hints,
        )

        ExpressionBase.__init__(self, source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not tensorflow_function_spec.isCompileTimeComputable(
            (
                self.subnode_func,
                self.subnode_input_signature,
                self.subnode_autograph,
                self.subnode_jit_compile,
                self.subnode_reduce_retracing,
                self.subnode_experimental_implements,
                self.subnode_experimental_autograph_options,
                self.subnode_experimental_attributes,
                self.subnode_experimental_relax_shapes,
                self.subnode_experimental_compile,
                self.subnode_experimental_follow_type_hints,
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
