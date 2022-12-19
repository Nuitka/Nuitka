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
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long

"""Hard import nodes

WARNING, this code is GENERATED. Modify the template HardImportReferenceNode.py.j2 instead!

spell-checker: ignore capitalize casefold center clear copy count decode encode endswith expandtabs find format formatmap get haskey hex index isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem replace rfind rindex rjust rpartition rsplit rstrip setdefault split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default encoding end errors fillchar iterable keepends key maxsplit new old pairs prefix sep start sub suffix table tabsize width
"""
from abc import abstractmethod

from nuitka.Options import shallMakeModule
from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs
from nuitka.specs.HardImportSpecs import (
    importlib_metadata_backport_distribution_spec,
    importlib_metadata_backport_metadata_spec,
    importlib_metadata_backport_version_spec,
    importlib_metadata_distribution_spec,
    importlib_metadata_metadata_spec,
    importlib_metadata_version_spec,
    pkg_resources_get_distribution_spec,
    pkg_resources_iter_entry_points_spec,
    pkg_resources_require_spec,
)

from .ChildrenHavingMixins import (
    ChildrenHavingDistMixin,
    ChildrenHavingDistributionNameMixin,
    ChildrenHavingGroupNameMixin,
    ChildrenHavingRequirementsTupleMixin,
)
from .ExpressionBases import ExpressionBase
from .ImportHardNodes import ExpressionImportModuleNameHardExistsSpecificBase

hard_import_node_classes = {}


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
    ChildrenHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportDistributionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):

        ChildrenHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_distribution_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
    ChildrenHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportMetadataCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):

        ChildrenHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_metadata_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
    ChildrenHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataBackportVersionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):

        ChildrenHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_backport_version_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
            module_guaranteed=not shallMakeModule(),
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
    ChildrenHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataDistributionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):

        ChildrenHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_distribution_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
            module_guaranteed=not shallMakeModule(),
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
    ChildrenHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataMetadataCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):

        ChildrenHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_metadata_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
            module_guaranteed=not shallMakeModule(),
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
    ChildrenHavingDistributionNameMixin, ExpressionBase
):
    """Base class for ImportlibMetadataVersionCall

    Generated boiler plate code.
    """

    named_children = ("distribution_name",)

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):

        ChildrenHavingDistributionNameMixin.__init__(
            self,
            distribution_name=distribution_name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not importlib_metadata_version_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
    ChildrenHavingDistMixin, ExpressionBase
):
    """Base class for PkgResourcesGetDistributionCall

    Generated boiler plate code.
    """

    named_children = ("dist",)

    __slots__ = ("attempted",)

    def __init__(self, dist, source_ref):

        ChildrenHavingDistMixin.__init__(
            self,
            dist=dist,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_get_distribution_spec.isCompileTimeComputable(
                (self.subnode_dist,),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
    ChildrenHavingGroupNameMixin, ExpressionBase
):
    """Base class for PkgResourcesIterEntryPointsCall

    Generated boiler plate code.
    """

    named_children = ("group", "name")

    __slots__ = ("attempted",)

    def __init__(self, group, name, source_ref):

        ChildrenHavingGroupNameMixin.__init__(
            self,
            group=group,
            name=name,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_iter_entry_points_spec.isCompileTimeComputable(
                (
                    self.subnode_group,
                    self.subnode_name,
                ),
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass


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
    ChildrenHavingRequirementsTupleMixin, ExpressionBase
):
    """Base class for PkgResourcesRequireCall

    Generated boiler plate code.
    """

    named_children = ("requirements",)

    __slots__ = ("attempted",)

    def __init__(self, requirements, source_ref):

        ChildrenHavingRequirementsTupleMixin.__init__(
            self,
            requirements=requirements,
        )

        ExpressionBase.__init__(self, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def computeExpression(self, trace_collection):
        if self.attempted or not pkg_resources_require_spec.isCompileTimeComputable(
            self.subnode_requirements
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return self.replaceWithCompileTimeValue(trace_collection)

    @abstractmethod
    def replaceWithCompileTimeValue(self, trace_collection):
        pass
