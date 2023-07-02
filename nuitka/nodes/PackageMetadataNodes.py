#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.Options import isStandaloneMode
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Importing import importFromCompileTime
from nuitka.utils.Utils import withNoDeprecationWarning

from .AttributeNodes import makeExpressionAttributeLookup
from .ContainerMakingNodes import (
    ExpressionMakeSequenceMixin,
    makeExpressionMakeList,
    makeExpressionMakeTuple,
)
from .DictionaryNodes import ExpressionMakeDictMixin, makeExpressionMakeDict
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .ExpressionBasesGenerated import (
    ExpressionImportlibMetadataBackportEntryPointsValueRefBase,
    ExpressionImportlibMetadataBackportEntryPointValueRefBase,
    ExpressionImportlibMetadataBackportSelectableGroupsValueRefBase,
    ExpressionImportlibMetadataEntryPointsValueRefBase,
    ExpressionImportlibMetadataEntryPointValueRefBase,
    ExpressionImportlibMetadataSelectableGroupsValueRefBase,
)
from .HardImportNodesGenerated import (
    ExpressionImportlibMetadataBackportEntryPointsCallBase,
    ExpressionImportlibMetadataBackportVersionCallBase,
    ExpressionImportlibMetadataDistributionCallBase,
    ExpressionImportlibMetadataEntryPointsBefore310CallBase,
    ExpressionImportlibMetadataEntryPointsSince310CallBase,
    ExpressionImportlibMetadataVersionCallBase,
    ExpressionPkgResourcesGetDistributionCallBase,
    ExpressionPkgResourcesIterEntryPointsCallBase,
    ExpressionPkgResourcesRequireCallBase,
)
from .KeyValuePairNodes import (
    makeExpressionKeyValuePairConstantKey,
    makeKeyValuePairExpressionsFromKwArgs,
)


def _getPkgResourcesModule():
    """Helper for importing pkg_resources from installation at compile time.

    This is not for using the inline copy, but the one from the actual
    installation of the user. It suppresses warnings and caches the value
    avoid making more __import__ calls that necessary.
    """

    return importFromCompileTime("pkg_resources", must_exist=True)


class ExpressionPkgResourcesRequireCall(ExpressionPkgResourcesRequireCallBase):
    kind = "EXPRESSION_PKG_RESOURCES_REQUIRE_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
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
                "Cannot find requirement %s at '%s', expect potential run time problem, unless this is unused code."
                % (",".join(repr(s) for s in args), self.source_ref.getAsString())
            )

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except (TypeError, InvalidRequirement):
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
                elements=tuple(
                    ExpressionPkgResourcesDistributionValueRef(
                        distribution=distribution, source_ref=self.source_ref
                    )
                    for distribution in distributions
                ),
                source_ref=self.source_ref,
            )

            trace_collection.onExceptionRaiseExit(BaseException)

            return (
                result,
                "new_expression",
                "Compile time predicted 'pkg_resources.require' result",
            )


class ExpressionPkgResourcesGetDistributionCall(
    ExpressionPkgResourcesGetDistributionCallBase
):
    kind = "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        get_distribution = _getPkgResourcesModule().get_distribution
        DistributionNotFound = _getPkgResourcesModule().DistributionNotFound

        arg = self.subnode_dist.getCompileTimeConstant()

        try:
            distribution = get_distribution(arg)
        except DistributionNotFound:
            inclusion_logger.info(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, unless this is unused code."
                % (arg, self.source_ref.getAsString())
            )

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


class ImportlibMetadataVersionCallMixin(object):
    __slots__ = ()

    def _getImportlibMetadataModule(self):
        return importFromCompileTime(self.importlib_metadata_name, must_exist=True)

    def replaceWithCompileTimeValue(self, trace_collection):
        version = self._getImportlibMetadataModule().version
        PackageNotFoundError = self._getImportlibMetadataModule().PackageNotFoundError

        arg = self.subnode_distribution_name.getCompileTimeConstant()

        try:
            distribution = version(arg)
        except PackageNotFoundError:
            inclusion_logger.info(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, unless this is unused code."
                % (arg, self.source_ref.getAsString())
            )

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
                "Compile time predicted '%s.version' result"
                % self.importlib_metadata_name,
            )


class ExpressionImportlibMetadataVersionCall(
    ImportlibMetadataVersionCallMixin, ExpressionImportlibMetadataVersionCallBase
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_VERSION_CALL"
    python_version_spec = ">= 0x380"
    importlib_metadata_name = "importlib.metadata"


class ExpressionImportlibMetadataBackportVersionCall(
    ImportlibMetadataVersionCallMixin,
    ExpressionImportlibMetadataBackportVersionCallBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_CALL"
    importlib_metadata_name = "importlib_metadata"


# TODO: This is much like a compile time variable, but not a good compile time
# constant, have that too. Treating it as semi-constant, we should get away
# with.


class ExpressionPkgResourcesDistributionValueRef(
    ExpressionNoSideEffectsMixin, ExpressionBase
):
    kind = "EXPRESSION_PKG_RESOURCES_DISTRIBUTION_VALUE_REF"

    __slots__ = ("distribution", "computed_attributes")

    preserved_attributes = ("py_version", "platform", "version", "project_name")

    def __init__(self, distribution, source_ref):
        with withNoDeprecationWarning():
            Distribution = _getPkgResourcesModule().Distribution

            preserved_attributes = self.preserved_attributes
            if not isStandaloneMode():
                preserved_attributes += ("location",)

            distribution = Distribution(
                **dict(
                    (key, getattr(distribution, key)) for key in preserved_attributes
                )
            )

        ExpressionBase.__init__(self, source_ref)

        self.distribution = distribution
        self.computed_attributes = {}

    def finalize(self):
        del self.distribution

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def getTruthValue():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    def computeExpressionRaw(self, trace_collection):
        # Cannot compute any further, this is already the best.
        return self, None, None

    def isKnownToHaveAttribute(self, attribute_name):
        if attribute_name not in self.computed_attributes:
            self.computed_attributes[attribute_name] = hasattr(
                self.distribution, attribute_name
            )

        return self.computed_attributes[attribute_name]

    def getKnownAttributeValue(self, attribute_name):
        return getattr(self.distribution, attribute_name)

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if (
            self.isKnownToHaveAttribute(attribute_name)
            and isCompileTimeConstantValue(
                getattr(self.distribution, attribute_name, None)
            )
            and (attribute_name != "location" or not isStandaloneMode())
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: getattr(self.distribution, attribute_name),
                description="Attribute '%s' pre-computed." % (attribute_name),
            )

        return lookup_node, None, None

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        return not self.isKnownToHaveAttribute(attribute_name)


class ExpressionImportlibMetadataDistributionValueRef(
    ExpressionNoSideEffectsMixin, ExpressionBase
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_VALUE_REF"

    # This is also usable with the backport, generated code finds what is working for it.

    __slots__ = ("distribution", "original_name", "computed_attributes")

    def __init__(self, distribution, original_name, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.distribution = distribution
        self.original_name = original_name
        self.computed_attributes = {}

    def getDetails(self):
        return {"distribution": self.distribution, "original_name": self.original_name}

    def finalize(self):
        del self.distribution

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def getTruthValue():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    def computeExpressionRaw(self, trace_collection):
        # Cannot compute any further, this is already the best.
        return self, None, None


class ExpressionPkgResourcesIterEntryPointsCall(
    ExpressionPkgResourcesIterEntryPointsCallBase
):
    kind = "EXPRESSION_PKG_RESOURCES_ITER_ENTRY_POINTS_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        iter_entry_points = _getPkgResourcesModule().iter_entry_points
        DistributionNotFound = _getPkgResourcesModule().DistributionNotFound

        group = self.subnode_group.getCompileTimeConstant()
        if self.subnode_name is not None:
            name = self.subnode_name.getCompileTimeConstant()
        else:
            name = None

        try:
            # Get entry point from generator, we cannot delay.
            entry_points = tuple(iter_entry_points(group=group, name=name))
        except DistributionNotFound:
            inclusion_logger.info(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, unless this is unused code."
                % (group, self.source_ref.getAsString())
            )

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find distribution '%s' at '%s' due to unhandled %s. Please report this bug."
                % (group, self.source_ref.getAsString(), repr(e))
            )
        else:
            result = makeExpressionMakeList(
                elements=tuple(
                    ExpressionPkgResourcesEntryPointValueRef(
                        entry_point=entry_point, source_ref=self.source_ref
                    )
                    for entry_point in entry_points
                ),
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_expression",
                "Compile time predicted 'pkg_resources.iter_entry_points' result",
            )


class ExpressionPkgResourcesEntryPointValueRef(
    ExpressionNoSideEffectsMixin, ExpressionBase
):
    kind = "EXPRESSION_PKG_RESOURCES_ENTRY_POINT_VALUE_REF"

    __slots__ = ("entry_point", "computed_attributes")

    preserved_attributes = ("name", "module_name", "attrs", "extras")

    def __init__(self, entry_point, source_ref):
        with withNoDeprecationWarning():
            EntryPoint = _getPkgResourcesModule().EntryPoint

            entry_point = EntryPoint(
                **dict(
                    (key, getattr(entry_point, key))
                    for key in self.preserved_attributes
                )
            )

        ExpressionBase.__init__(self, source_ref)

        self.entry_point = entry_point
        self.computed_attributes = {}

    def finalize(self):
        del self.entry_point
        del self.computed_attributes

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
        if attribute_name not in self.computed_attributes:
            self.computed_attributes[attribute_name] = hasattr(
                self.entry_point, attribute_name
            )

        return self.computed_attributes[attribute_name]

    def getKnownAttributeValue(self, attribute_name):
        return getattr(self.entry_point, attribute_name)

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if self.isKnownToHaveAttribute(attribute_name) and isCompileTimeConstantValue(
            getattr(self.entry_point, attribute_name, None)
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: getattr(self.entry_point, attribute_name),
                description="Attribute '%s' pre-computed." % (attribute_name),
            )

        return lookup_node, None, None


class ImportlibMetadataDistributionCallMixin(object):
    __slots__ = ()

    def _getImportlibMetadataModule(self):
        return importFromCompileTime(self.importlib_metadata_name, must_exist=True)

    def replaceWithCompileTimeValue(self, trace_collection):
        distribution_func = self._getImportlibMetadataModule().distribution
        PackageNotFoundError = self._getImportlibMetadataModule().PackageNotFoundError

        arg = self.subnode_distribution_name.getCompileTimeConstant()

        try:
            distribution = distribution_func(arg)
        except PackageNotFoundError:
            inclusion_logger.info(
                "Cannot find distribution '%s' at '%s', expect potential run time problem, unless this is unused code."
                % (arg, self.source_ref.getAsString())
            )

            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find distribution '%s' at '%s' due to unhandled %s. Please report this bug."
                % (arg, self.source_ref.getAsString(), repr(e))
            )
        else:
            # Remember the original name, distributions can other names.
            result = ExpressionImportlibMetadataDistributionValueRef(
                distribution=distribution, original_name=arg, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Compile time predicted '%s.distribution' result"
                % self.importlib_metadata_name,
            )


class ExpressionImportlibMetadataDistributionCall(
    ImportlibMetadataDistributionCallMixin,
    ExpressionImportlibMetadataDistributionCallBase,
):
    """Represents call to importlib.metadata.distribution(distribution_name)"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_CALL"

    python_version_spec = ">= 0x380"

    importlib_metadata_name = "importlib.metadata"


class ExpressionImportlibMetadataBackportDistributionCall(
    ImportlibMetadataDistributionCallMixin,
    ExpressionImportlibMetadataDistributionCallBase,
):
    """Represents call to importlib_metadata.distribution(distribution_name)"""

    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_CALL"
    importlib_metadata_name = "importlib_metadata"


def makeExpressionImportlibMetadataMetadataCall(distribution_name, source_ref):
    return makeExpressionAttributeLookup(
        expression=ExpressionImportlibMetadataDistributionCall(
            distribution_name=distribution_name, source_ref=source_ref
        ),
        attribute_name="metadata",
        source_ref=source_ref,
    )


def makeExpressionImportlibMetadataBackportMetadataCall(distribution_name, source_ref):
    return makeExpressionAttributeLookup(
        expression=ExpressionImportlibMetadataBackportDistributionCall(
            distribution_name=distribution_name, source_ref=source_ref
        ),
        attribute_name="metadata",
        source_ref=source_ref,
    )


class ExpressionImportlibMetadataEntryPointValueMixin(object):
    __slots__ = ()

    preserved_attributes = ("name", "value", "group")

    def _getImportlibMetadataModule(self):
        return importFromCompileTime(self.importlib_metadata_name, must_exist=True)

    def finalize(self):
        del self.entry_point
        del self.computed_attributes

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
        if attribute_name not in self.computed_attributes:
            self.computed_attributes[attribute_name] = hasattr(
                self.entry_point, attribute_name
            )

        return self.computed_attributes[attribute_name]

    def getKnownAttributeValue(self, attribute_name):
        return getattr(self.entry_point, attribute_name)

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if self.isKnownToHaveAttribute(attribute_name) and isCompileTimeConstantValue(
            getattr(self.entry_point, attribute_name, None)
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: getattr(self.entry_point, attribute_name),
                description="Attribute '%s' pre-computed." % (attribute_name),
            )

        return lookup_node, None, None


class ExpressionImportlibMetadataEntryPointValueRef(
    ExpressionNoSideEffectsMixin,
    ExpressionImportlibMetadataEntryPointValueMixin,
    ExpressionImportlibMetadataEntryPointValueRefBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINT_VALUE_REF"

    python_version_spec = ">= 0x380"

    __slots__ = ("entry_point", "computed_attributes")

    auto_compute_handling = "final,no_raise"

    importlib_metadata_name = "importlib.metadata"

    def __init__(self, entry_point, source_ref):
        ExpressionImportlibMetadataEntryPointValueRefBase.__init__(self, source_ref)

        EntryPoint = self._getImportlibMetadataModule().EntryPoint

        entry_point = EntryPoint(
            **dict(
                (key, getattr(entry_point, key)) for key in self.preserved_attributes
            )
        )

        self.entry_point = entry_point
        self.computed_attributes = {}


class ExpressionImportlibMetadataBackportEntryPointValueRef(
    ExpressionNoSideEffectsMixin,
    ExpressionImportlibMetadataEntryPointValueMixin,
    ExpressionImportlibMetadataBackportEntryPointValueRefBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINT_VALUE_REF"

    __slots__ = ("entry_point", "computed_attributes")

    auto_compute_handling = "final,no_raise"

    importlib_metadata_name = "importlib_metadata"

    def __init__(self, entry_point, source_ref):
        ExpressionImportlibMetadataBackportEntryPointValueRefBase.__init__(
            self, source_ref
        )

        EntryPoint = self._getImportlibMetadataModule().EntryPoint

        entry_point = EntryPoint(
            **dict(
                (key, getattr(entry_point, key)) for key in self.preserved_attributes
            )
        )

        self.entry_point = entry_point
        self.computed_attributes = {}


class ExpressionImportlibMetadataSelectableGroupsValueRef(
    ExpressionMakeDictMixin, ExpressionImportlibMetadataSelectableGroupsValueRefBase
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_SELECTABLE_GROUPS_VALUE_REF"

    python_version_spec = ">= 0x3a0"

    named_children = ("pairs|tuple",)

    auto_compute_handling = "final,no_raise"

    # TODO: Derived from dict shape is missing here.
    @staticmethod
    def isKnownToBeHashable():
        return False


class ExpressionImportlibMetadataBackportSelectableGroupsValueRef(
    ExpressionMakeDictMixin,
    ExpressionImportlibMetadataBackportSelectableGroupsValueRefBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_SELECTABLE_GROUPS_VALUE_REF"

    named_children = ("pairs|tuple",)

    auto_compute_handling = "final,no_raise"

    # TODO: Derived from dict shape is missing here.
    @staticmethod
    def isKnownToBeHashable():
        return False


class ExpressionImportlibMetadataEntryPointsValueRef(
    ExpressionMakeSequenceMixin,
    ExpressionImportlibMetadataBackportEntryPointsValueRefBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_VALUE_REF"

    python_version_spec = ">= 0x3a0"

    named_children = ("elements|tuple",)

    auto_compute_handling = "final,no_raise"

    # TODO: Derived from dict shape is missing here.
    @staticmethod
    def isKnownToBeHashable():
        return False

    @staticmethod
    def getSequenceName():
        """Get name for use in traces"""
        return "importlib.metadata.EntryPoints"


class ExpressionImportlibMetadataBackportEntryPointsValueRef(
    ExpressionMakeSequenceMixin, ExpressionImportlibMetadataEntryPointsValueRefBase
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_VALUE_REF"

    named_children = ("elements|tuple",)

    auto_compute_handling = "final,no_raise"

    @staticmethod
    def getSequenceName():
        """Get name for use in traces"""
        return "importlib_metadata.EntryPoints"

    # TODO: Derived from dict shape is missing here.
    @staticmethod
    def isKnownToBeHashable():
        return False


class ExpressionImportlibMetadataEntryPointsCallMixin(object):
    __slots__ = ()

    def _getImportlibMetadataModule(self):
        return importFromCompileTime(self.importlib_metadata_name, must_exist=True)

    def replaceWithCompileTimeValue(self, trace_collection):
        metadata_importlib = self._getImportlibMetadataModule()

        constant_args = dict(
            (param.getKeyCompileTimeConstant(), param.getValueCompileTimeConstant())
            for param in self.subnode_params
        )

        try:
            entry_points_result = metadata_importlib.entry_points(**constant_args)
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            inclusion_logger.sysexit(
                "Error, failed to find entrypoints at '%s' due to unhandled %s. Please report this bug."
                % (self.source_ref.getAsString(), repr(e))
            )
        else:
            if (
                hasattr(metadata_importlib, "SelectableGroups")
                and type(entry_points_result) is metadata_importlib.SelectableGroups
            ):
                pairs = [
                    makeExpressionKeyValuePairConstantKey(
                        key=key,
                        value=self.makeEntryPointsValueRef(
                            elements=tuple(
                                self.makeEntryPointValueRef(
                                    entry_point=entry_point, source_ref=self.source_ref
                                )
                                for entry_point in value
                            ),
                            source_ref=self.source_ref,
                        ),
                    )
                    for key, value in entry_points_result.items()
                ]

                result = self.makeSelectableGroupsValueRef(
                    pairs=tuple(pairs), source_ref=self.source_ref
                )
            elif type(entry_points_result) is dict:
                pairs = [
                    makeExpressionKeyValuePairConstantKey(
                        key=key,
                        value=makeExpressionMakeTuple(
                            elements=tuple(
                                self.makeEntryPointValueRef(
                                    entry_point=entry_point, source_ref=self.source_ref
                                )
                                for entry_point in value
                            ),
                            source_ref=self.source_ref,
                        ),
                    )
                    for key, value in entry_points_result.items()
                ]

                result = makeExpressionMakeDict(
                    pairs=tuple(pairs), source_ref=self.source_ref
                )
            elif (
                hasattr(metadata_importlib, "EntryPoints")
                and type(entry_points_result) is metadata_importlib.EntryPoints
            ):
                result = self.makeEntryPointsValueRef(
                    elements=tuple(
                        self.makeEntryPointValueRef(
                            entry_point=entry_point, source_ref=self.source_ref
                        )
                        for entry_point in entry_points_result
                    ),
                    source_ref=self.source_ref,
                )

            else:
                assert False, type(entry_points_result)

            return (
                result,
                "new_expression",
                "Compile time predicted '%s' result" % self.importlib_metadata_name,
            )


class ExpressionImportlibMetadataEntryPointsBefore310Call(
    ExpressionImportlibMetadataEntryPointsCallMixin,
    ExpressionImportlibMetadataEntryPointsBefore310CallBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_BEFORE310_CALL"

    # TODO: How to be sure, this is picked up on top of base class python
    # version spec
    python_version_spec = ">= 0x380"

    importlib_metadata_name = "importlib.metadata"

    makeEntryPointValueRef = ExpressionImportlibMetadataEntryPointValueRef

    # For the mixing to work properly.
    subnode_params = ()


def makeExpressionImportlibMetadataEntryPointsSince310Call(params, source_ref):
    return ExpressionImportlibMetadataEntryPointsSince310Call(
        params=makeKeyValuePairExpressionsFromKwArgs(params), source_ref=source_ref
    )


class ExpressionImportlibMetadataEntryPointsSince310Call(
    ExpressionImportlibMetadataEntryPointsCallMixin,
    ExpressionImportlibMetadataEntryPointsSince310CallBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_SINCE310_CALL"

    importlib_metadata_name = "importlib.metadata"

    makeEntryPointsValueRef = ExpressionImportlibMetadataEntryPointsValueRef
    makeEntryPointValueRef = ExpressionImportlibMetadataEntryPointValueRef
    makeSelectableGroupsValueRef = ExpressionImportlibMetadataSelectableGroupsValueRef


def makeExpressionImportlibMetadataBackportEntryPointsCall(params, source_ref):
    return ExpressionImportlibMetadataBackportEntryPointsCall(
        params=makeKeyValuePairExpressionsFromKwArgs(params), source_ref=source_ref
    )


class ExpressionImportlibMetadataBackportEntryPointsCall(
    ExpressionImportlibMetadataEntryPointsCallMixin,
    ExpressionImportlibMetadataBackportEntryPointsCallBase,
):
    kind = "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_CALL"

    importlib_metadata_name = "importlib_metadata"

    makeEntryPointsValueRef = ExpressionImportlibMetadataBackportEntryPointsValueRef
    makeEntryPointValueRef = ExpressionImportlibMetadataBackportEntryPointValueRef
    makeSelectableGroupsValueRef = (
        ExpressionImportlibMetadataBackportSelectableGroupsValueRef
    )
