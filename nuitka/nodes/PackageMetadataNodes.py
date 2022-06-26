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
""" Nodes the represent ways to access metadata pkg_resources, importlib.resources etc.

"""


from nuitka.Constants import isCompileTimeConstantValue
from nuitka.Options import isStandaloneMode, shallMakeModule
from nuitka.specs.BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    extractBuiltinArgs,
)
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Importing import importFromCompileTime
from nuitka.utils.Utils import withNoDeprecationWarning

from .ContainerMakingNodes import makeExpressionMakeList
from .ExpressionBases import (
    ExpressionBase,
    ExpressionChildHavingBase,
    ExpressionChildTupleHavingBase,
    ExpressionNoSideEffectsMixin,
)
from .ImportHardNodes import ExpressionImportModuleNameHardExists

pkg_resources_require_spec = BuiltinParameterSpec(
    "pkg_resources.require", (), default_count=0, list_star_arg="requirements"
)
pkg_resources_get_distribution_spec = BuiltinParameterSpec(
    "pkg_resources.get_distribution", ("dist",), default_count=0
)


def _getPkgResourcesModule():
    """Helper for importing pkg_resources from installation at compile time.

    This is not for using the inline copy, but the one from the actual
    installation of the user. It suppresses warnings and caches the value
    avoid making more __import__ calls that necessary.
    """

    return importFromCompileTime("pkg_resources", must_exist=True)


class ExpressionPkgResourcesRequireRef(ExpressionImportModuleNameHardExists):
    """Function reference pkg_resources.require"""

    kind = "EXPRESSION_PKG_RESOURCES_REQUIRE_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExists.__init__(
            self,
            module_name="pkg_resources",
            import_name="require",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

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


class ExpressionPkgResourcesRequireCall(ExpressionChildTupleHavingBase):
    kind = "EXPRESSION_PKG_RESOURCES_REQUIRE_CALL"

    named_child = "requirements"

    __slots__ = ("attempted",)

    def __init__(self, requirements, source_ref):
        ExpressionChildTupleHavingBase.__init__(
            self, value=requirements, source_ref=source_ref
        )

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def _replaceWithCompileTimeValue(self, trace_collection):
        require = _getPkgResourcesModule().require
        ResolutionError = _getPkgResourcesModule().ResolutionError
        InvalidRequirement = (
            _getPkgResourcesModule().extern.packaging.requirements.InvalidRequirement
        )

        args = tuple(
            element.getCompileTimeConstant() for element in self.subnode_requirements
        )

        try:
            distributions = require(*args)
        except ResolutionError:
            inclusion_logger.warning(
                "Cannot find requirement '%s' at '%s', expect potential run time problem. Could also be dead code."
                % (",".join(repr(s) for s in args), self.source_ref.getAsString())
            )

            self.attempted = True

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except (TypeError, InvalidRequirement):
            self.attempted = True

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find requirements '%s' at '%s' due to unhandled %s. Please report this bug."
                % (
                    ",".join(repr(s) for s in args),
                    self.source_ref.getAsString(),
                    repr(e),
                )
            )
        else:
            result = makeExpressionMakeList(
                elements=[
                    ExpressionPkgResourcesDistributionValueRef(
                        distribution=distribution, source_ref=self.source_ref
                    )
                    for distribution in distributions
                ],
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_expression",
                "Compile time predicted 'pkg_resources.require' result",
            )

    def computeExpression(self, trace_collection):
        if self.attempted or not pkg_resources_require_spec.isCompileTimeComputable(
            self.subnode_requirements
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        with withNoDeprecationWarning():
            return self._replaceWithCompileTimeValue(trace_collection)


class ExpressionPkgResourcesGetDistributionRef(ExpressionImportModuleNameHardExists):
    """Function reference pkg_resources.get_distribution"""

    kind = "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExists.__init__(
            self,
            module_name="pkg_resources",
            import_name="get_distribution",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionPkgResourcesGetDistributionCall,
            builtin_spec=pkg_resources_get_distribution_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'pkg_resources.require' recognized.",
        )


class ExpressionPkgResourcesGetDistributionCall(ExpressionChildHavingBase):
    kind = "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_CALL"

    named_child = "dist"

    __slots__ = ("attempted",)

    def __init__(self, dist, source_ref):
        ExpressionChildHavingBase.__init__(self, value=dist, source_ref=source_ref)

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def _replaceWithCompileTimeValue(self, trace_collection):
        get_distribution = _getPkgResourcesModule().get_distribution
        DistributionNotFound = _getPkgResourcesModule().DistributionNotFound

        arg = self.subnode_dist.getCompileTimeConstant()

        try:
            distribution = get_distribution(arg)
        except DistributionNotFound:
            inclusion_logger.warning(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, could also be dead code."
                % (arg, self.source_ref.getAsString())
            )

            self.attempted = True

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find distribution '%s' at '%s' due to unhandled %s. Please report this bug."
                % (arg, self.source_ref.getAsString(), repr(e))
            )
        else:
            result = ExpressionPkgResourcesDistributionValueRef(
                distribution=distribution, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Compile time predicted 'pkg_resources.get_distribution' result",
            )

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_get_distribution_spec.isCompileTimeComputable(
                (self.subnode_dist,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        with withNoDeprecationWarning():
            return self._replaceWithCompileTimeValue(trace_collection)


importlib_metadata_version_spec = BuiltinParameterSpec(
    "importlib.metadata.version", ("distribution_name",), default_count=0
)


class ExpressionImportlibMetadataVersionRef(ExpressionImportModuleNameHardExists):
    """Function reference importlib.metadata.version"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_VERSION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExists.__init__(
            self,
            module_name="importlib.metadata",
            import_name="version",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

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


class ExpressionImportlibMetadataBackportVersionRef(
    ExpressionImportModuleNameHardExists
):
    """Function reference importlib_metadata.version"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExists.__init__(
            self,
            module_name="importlib_metadata",
            import_name="version",
            module_guaranteed=not shallMakeModule(),
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibMetadataBackportVersionCall,
            builtin_spec=importlib_metadata_version_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'importlib_metadata.version' recognized.",
        )


def _getImportlibMetadataModule():
    """Helper for importing importlib.metadata from installation at compile time.

    This is not for using the inline copy, but the one from the actual
    installation of the user. It suppresses warnings and caches the value
    avoid making more __import__ calls that necessary.
    """

    return importFromCompileTime("importlib.metadata", must_exist=True)


class ExpressionImportlibMetadataVersionCall(ExpressionChildHavingBase):
    kind = "EXPRESSION_IMPORTLIB_METADATA_VERSION_CALL"

    named_child = "distribution_name"

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):
        ExpressionChildHavingBase.__init__(
            self, value=distribution_name, source_ref=source_ref
        )

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def _replaceWithCompileTimeValue(self, trace_collection):
        version = _getImportlibMetadataModule().version
        PackageNotFoundError = _getImportlibMetadataModule().PackageNotFoundError

        arg = self.subnode_distribution_name.getCompileTimeConstant()

        try:
            distribution = version(arg)
        except PackageNotFoundError:
            inclusion_logger.warning(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, could also be dead code."
                % (arg, self.source_ref.getAsString())
            )

            self.attempted = True

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find distribution '%s' at '%s' due to unhandled %s. Please report this bug."
                % (arg, self.source_ref.getAsString(), repr(e))
            )
        else:
            from .ConstantRefNodes import makeConstantRefNode

            result = makeConstantRefNode(
                constant=distribution, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Compile time predicted 'importlib.metadata.version' result",
            )

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_get_distribution_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        with withNoDeprecationWarning():
            return self._replaceWithCompileTimeValue(trace_collection)


def _getImportlibMetadataBackportModule():
    """Helper for importing importlib_metadata from installation at compile time.

    This is not for using the inline copy, but the one from the actual
    installation of the user. It suppresses warnings and caches the value
    avoid making more __import__ calls that necessary.
    """

    return importFromCompileTime("importlib_metadata", must_exist=True)


class ExpressionImportlibMetadataBackportVersionCall(ExpressionChildHavingBase):
    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_CALL"

    named_child = "distribution_name"

    __slots__ = ("attempted",)

    def __init__(self, distribution_name, source_ref):
        ExpressionChildHavingBase.__init__(
            self, value=distribution_name, source_ref=source_ref
        )

        # In module mode, we expect a changing environment, cannot optimize this
        self.attempted = shallMakeModule()

    def _replaceWithCompileTimeValue(self, trace_collection):
        version = _getImportlibMetadataBackportModule().version
        PackageNotFoundError = (
            _getImportlibMetadataBackportModule().PackageNotFoundError
        )

        arg = self.subnode_distribution_name.getCompileTimeConstant()

        try:
            distribution = version(arg)
        except PackageNotFoundError:
            inclusion_logger.warning(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, could also be dead code."
                % (arg, self.source_ref.getAsString())
            )

            self.attempted = True

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find distribution '%s' at '%s' due to unhandled %s. Please report this bug."
                % (arg, self.source_ref.getAsString(), repr(e))
            )
        else:
            from .ConstantRefNodes import makeConstantRefNode

            result = makeConstantRefNode(
                constant=distribution, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Compile time predicted 'importlib_metadata.version' result",
            )

    def computeExpression(self, trace_collection):
        if (
            self.attempted
            or not pkg_resources_get_distribution_spec.isCompileTimeComputable(
                (self.subnode_distribution_name,)
            )
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        with withNoDeprecationWarning():
            return self._replaceWithCompileTimeValue(trace_collection)


# TODO: This is much like a compile time variable, but not a good compile time
# constant, have that too. Treating it as semi-constant, we should get away
# with.


class ExpressionPkgResourcesDistributionValueRef(
    ExpressionNoSideEffectsMixin, ExpressionBase
):
    kind = "EXPRESSION_PKG_RESOURCES_DISTRIBUTION_VALUE_REF"

    __slots__ = ("distribution", "computed_attribute")

    preserved_attributes = ("py_version", "platform", "version", "project_name")

    def __init__(self, distribution, source_ref):
        with withNoDeprecationWarning():
            Distribution = importFromCompileTime(
                "pkg_resources", must_exist=True
            ).Distribution

            preserved_attributes = self.preserved_attributes
            if not isStandaloneMode():
                preserved_attributes += ("location",)

            distribution = Distribution(
                **dict(
                    (key, getattr(distribution, key)) for key in preserved_attributes
                )
            )

        ExpressionBase.__init__(self, source_ref=source_ref)

        self.distribution = distribution
        self.computed_attribute = None

    def finalize(self):
        del self.distribution

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def getTruthValue():
        return True

    def computeExpressionRaw(self, trace_collection):
        # Cannot compute any further, this is already the best.
        return self, None, None

    def isKnownToHaveAttribute(self, attribute_name):
        if self.computed_attribute is None:
            self.computed_attribute = hasattr(self.distribution, attribute_name)

        return self.computed_attribute

    def getKnownAttributeValue(self, attribute_name):
        return getattr(self.distribution, attribute_name)

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        if self.computed_attribute is None:
            self.computed_attribute = hasattr(self.distribution, attribute_name)

        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if not self.computed_attribute or isCompileTimeConstantValue(
            getattr(self.distribution, attribute_name, None)
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: getattr(self.distribution, attribute_name),
                description="Attribute '%s' pre-computed." % (attribute_name),
            )

        return lookup_node, None, None
