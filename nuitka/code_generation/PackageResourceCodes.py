#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for package resources access."""

from nuitka.Options import shallMakeModule

from .BuiltinCodes import getBuiltinCallViaSpecCode
from .CallCodes import (
    getCallCodeKwPairs,
    getCallCodeKwSplit,
    getCallCodeNoArgs,
    getCallCodePosArgsQuick,
)
from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionCode,
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ConstantCodes import addDistributionMetadataValue
from .DictCodes import getDictionaryCreationCode
from .ErrorCodes import getErrorExitCode
from .ImportCodes import getImportModuleNameHardCode
from .PythonAPICodes import generateCAPIObjectCode
from .TupleCodes import getTupleCreationCode


def generatePkglibGetDataCallCode(to_name, expression, emit, context):
    package_name, resource_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "get_data_value", expression, emit, context
    ) as result_name:
        # TODO: Have global cached forms of hard attribute lookup results too.
        get_data_function = context.allocateTempName("get_data_function", unique=True)

        getImportModuleNameHardCode(
            to_name=get_data_function,
            module_name="pkgutil",
            import_name="get_data",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=get_data_function,
            expression=expression,
            arg_names=(package_name, resource_name),
            emit=emit,
            context=context,
        )


def generatePkgResourcesDistributionValueCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "distribution_value", expression, emit, context
    ) as result_name:
        distribution_class_name = context.allocateTempName(
            "distribution_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=distribution_class_name,
            module_name="pkg_resources",
            import_name="Distribution",
            needs_check=False,
            emit=emit,
            context=context,
        )

        kw_names = expression.__class__.preserved_attributes
        dict_value_names = [
            context.getConstantCode(getattr(expression.distribution, kw_name))
            for kw_name in kw_names
        ]

        # Standalone mode, has a different location.
        if "location" not in kw_names:
            kw_names += ("location",)
        dict_value_names.append(
            'LOOKUP_BUILTIN_STR("__nuitka_binary_dir")',
        )

        getCallCodeKwSplit(
            to_name=result_name,
            called_name=distribution_class_name,
            kw_names=kw_names,
            dict_value_names=dict_value_names,
            needs_check=False,
            emit=emit,
            context=context,
        )


def generateImportlibMetadataEntryPointsSince310CallCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "entrypoints_value", expression, emit, context
    ) as result_name:
        entry_points_function_name = context.allocateTempName(
            "importlib_metadata_entry_points_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_points_function_name,
            module_name="importlib.metadata",
            import_name="entry_points",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodeKwPairs(
            to_name=result_name,
            expression=expression,
            pairs=expression.subnode_params,
            called_name=entry_points_function_name,
            called_attribute_name=None,
            emit=emit,
            context=context,
        )


def generateImportlibMetadataBackportEntryPointsCallCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "entrypoints_value", expression, emit, context
    ) as result_name:
        entry_points_function_name = context.allocateTempName(
            "importlib_metadata_backport_entry_points_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_points_function_name,
            module_name="importlib_metadata",
            import_name="entry_points",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodeKwPairs(
            to_name=result_name,
            expression=expression,
            pairs=expression.subnode_params,
            called_name=entry_points_function_name,
            called_attribute_name=None,
            emit=emit,
            context=context,
        )


def generateImportlibMetadataDistributionValueCode(to_name, expression, emit, context):
    distribution = expression.distribution
    original_name = expression.original_name

    addDistributionMetadataValue(
        distribution_name=original_name,
        distribution=distribution,
        reason="static analysis",
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "distribution_value", expression, emit, context
    ) as value_name:
        emit(
            """%(to_name)s = Nuitka_Distribution_New(tstate, %(name)s);"""
            % {
                "to_name": value_name,
                "name": context.getConstantCode(original_name),
            }
        )

        getErrorExitCode(check_name=value_name, emit=emit, context=context)

        context.addCleanupTempName(value_name)


def generatePkgResourcesEntryPointValueCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "entry_point_value", expression, emit, context
    ) as result_name:
        entry_point_class_name = context.allocateTempName(
            "entry_point_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_point_class_name,
            module_name="pkg_resources",
            import_name="EntryPoint",
            needs_check=False,
            emit=emit,
            context=context,
        )

        kw_names = expression.__class__.preserved_attributes
        dict_value_names = [
            context.getConstantCode(getattr(expression.entry_point, kw_name))
            for kw_name in kw_names
        ]

        getCallCodeKwSplit(
            to_name=result_name,
            called_name=entry_point_class_name,
            kw_names=kw_names,
            dict_value_names=dict_value_names,
            needs_check=False,
            emit=emit,
            context=context,
        )


def generateImportlibMetadataEntryPointValueCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "entry_point_value", expression, emit, context
    ) as result_name:
        entry_point_class_name = context.allocateTempName(
            "entry_point_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_point_class_name,
            module_name="importlib.metadata",
            import_name="EntryPoint",
            needs_check=False,
            emit=emit,
            context=context,
        )

        kw_names = expression.__class__.preserved_attributes
        dict_value_names = [
            context.getConstantCode(getattr(expression.entry_point, kw_name))
            for kw_name in kw_names
        ]

        getCallCodeKwSplit(
            to_name=result_name,
            called_name=entry_point_class_name,
            kw_names=kw_names,
            dict_value_names=dict_value_names,
            needs_check=False,
            emit=emit,
            context=context,
        )


def generateImportlibMetadataBackportEntryPointValueCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "entry_point_value", expression, emit, context
    ) as result_name:
        entry_point_class_name = context.allocateTempName(
            "backport_entry_point_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_point_class_name,
            module_name="importlib_metadata",
            import_name="EntryPoint",
            needs_check=False,
            emit=emit,
            context=context,
        )

        kw_names = expression.__class__.preserved_attributes
        dict_value_names = [
            context.getConstantCode(getattr(expression.entry_point, kw_name))
            for kw_name in kw_names
        ]

        getCallCodeKwSplit(
            to_name=result_name,
            called_name=entry_point_class_name,
            kw_names=kw_names,
            dict_value_names=dict_value_names,
            needs_check=False,
            emit=emit,
            context=context,
        )


def generateImportlibMetadataSelectableGroupsValueCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "selectable_groups_value", expression, emit, context
    ) as result_name:
        selectable_group_class_name = context.allocateTempName(
            "selectable_groups_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=selectable_group_class_name,
            module_name="importlib.metadata",
            import_name="SelectableGroups",
            needs_check=False,
            emit=emit,
            context=context,
        )

        selectable_group_dict = context.allocateTempName("selectable_group_dict")

        getDictionaryCreationCode(
            to_name=selectable_group_dict,
            pairs=expression.subnode_pairs,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=selectable_group_class_name,
            expression=expression,
            arg_names=(selectable_group_dict,),
            emit=emit,
            context=context,
        )


def generateImportlibMetadataBackportSelectableGroupsValueCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "selectable_groups_value", expression, emit, context
    ) as result_name:
        selectable_group_class_name = context.allocateTempName(
            "backport_selectable_groups_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=selectable_group_class_name,
            module_name="importlib_metadata",
            import_name="SelectableGroups",
            needs_check=False,
            emit=emit,
            context=context,
        )

        selectable_group_dict = context.allocateTempName("selectable_group_dict")

        getDictionaryCreationCode(
            to_name=selectable_group_dict,
            pairs=expression.subnode_pairs,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=selectable_group_class_name,
            expression=expression,
            arg_names=(selectable_group_dict,),
            emit=emit,
            context=context,
        )


def generateImportlibMetadataEntryPointsValueCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "entry_points_class_value", expression, emit, context
    ) as result_name:
        entry_points_class_name = context.allocateTempName(
            "entry_points_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_points_class_name,
            module_name="importlib.metadata",
            import_name="EntryPoints",
            needs_check=False,
            emit=emit,
            context=context,
        )

        selectable_group_tuple = context.allocateTempName("selectable_group_dict")

        getTupleCreationCode(
            to_name=selectable_group_tuple,
            elements=expression.subnode_elements,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=entry_points_class_name,
            expression=expression,
            arg_names=(selectable_group_tuple,),
            emit=emit,
            context=context,
        )


def generateImportlibMetadataBackportEntryPointsValueCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "entry_points_class_value", expression, emit, context
    ) as result_name:
        entry_points_class_name = context.allocateTempName(
            "backport_entry_points_class", unique=True
        )

        getImportModuleNameHardCode(
            to_name=entry_points_class_name,
            module_name="importlib_metadata",
            import_name="EntryPoints",
            needs_check=False,
            emit=emit,
            context=context,
        )

        selectable_group_tuple = context.allocateTempName("selectable_group_dict")

        getTupleCreationCode(
            to_name=selectable_group_tuple,
            elements=expression.subnode_elements,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=entry_points_class_name,
            expression=expression,
            arg_names=(selectable_group_tuple,),
            emit=emit,
            context=context,
        )


def generatePkgResourcesRequireCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "require_value", expression, emit, context
    ) as result_name:
        (requirement_arg_names,) = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        require_function_name = context.allocateTempName(
            "require_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=require_function_name,
            module_name="pkg_resources",
            import_name="require",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=require_function_name,
            expression=expression,
            arg_names=requirement_arg_names,
            emit=emit,
            context=context,
        )


def generatePkgResourcesGetDistributionCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "get_distribution_value", expression, emit, context
    ) as result_name:
        (dist_arg_name,) = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        get_distribution_function_name = context.allocateTempName(
            "get_distribution_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=get_distribution_function_name,
            module_name="pkg_resources",
            import_name="get_distribution",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=get_distribution_function_name,
            expression=expression,
            arg_names=(dist_arg_name,),
            emit=emit,
            context=context,
        )


def generatePkgResourcesIterEntryPointsCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "iter_entry_points_value", expression, emit, context
    ) as result_name:
        group_arg_name, name_arg_name = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        iter_entry_points_function_name = context.allocateTempName(
            "iter_entry_points_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=iter_entry_points_function_name,
            module_name="pkg_resources",
            import_name="iter_entry_points",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=iter_entry_points_function_name,
            expression=expression,
            arg_names=(
                (
                    group_arg_name,
                    name_arg_name,
                )
                if name_arg_name is not None
                else (group_arg_name,)
            ),
            emit=emit,
            context=context,
        )


def generateImportlibMetadataVersionCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "version_value", expression, emit, context
    ) as result_name:
        (dist_arg_name,) = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        version_function_name = context.allocateTempName(
            "importlib_metadata_version_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=version_function_name,
            module_name="importlib.metadata",
            import_name="version",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=version_function_name,
            expression=expression,
            arg_names=(dist_arg_name,),
            emit=emit,
            context=context,
        )


def generateImportlibMetadataBackportVersionCallCode(
    to_name, expression, emit, context
):
    with withObjectCodeTemporaryAssignment(
        to_name, "version_value", expression, emit, context
    ) as result_name:
        (dist_arg_name,) = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        version_function_name = context.allocateTempName(
            "importlib_metadata_backport_version_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=version_function_name,
            module_name="importlib_metadata",
            import_name="version",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=version_function_name,
            expression=expression,
            arg_names=(dist_arg_name,),
            emit=emit,
            context=context,
        )


def generateImportlibMetadataDistributionCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "distribution_value", expression, emit, context
    ) as result_name:
        (dist_arg_name,) = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

        get_distribution_function_name = context.allocateTempName(
            "distribution_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=get_distribution_function_name,
            module_name=expression.importlib_metadata_name,
            import_name="distribution",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=get_distribution_function_name,
            expression=expression,
            arg_names=(dist_arg_name,),
            emit=emit,
            context=context,
        )


def generatePkgResourcesResourceStringCallCode(to_name, expression, emit, context):
    package_name, resource_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "resource_string_value", expression, emit, context
    ) as result_name:
        resource_string_function = context.allocateTempName(
            "resource_string_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=resource_string_function,
            module_name="pkg_resources",
            import_name="resource_string",
            needs_check=not shallMakeModule(),
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=resource_string_function,
            expression=expression,
            arg_names=(package_name, resource_name),
            emit=emit,
            context=context,
        )


def generateImportlibResourcesReadBinaryCallCode(to_name, expression, emit, context):
    package_name, resource_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "read_binary_value", expression, emit, context
    ) as result_name:
        read_binary_function = context.allocateTempName(
            "read_binary_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=read_binary_function,
            module_name="importlib.resources",
            import_name="read_binary",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=read_binary_function,
            expression=expression,
            arg_names=(package_name, resource_name),
            emit=emit,
            context=context,
        )


def generateImportlibResourcesReadTextCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "read_text_value", expression, emit, context
    ) as result_name:
        read_text_function = context.allocateTempName("read_text_function", unique=True)

        getImportModuleNameHardCode(
            to_name=read_text_function,
            module_name="importlib.resources",
            import_name="read_text",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getBuiltinCallViaSpecCode(
            spec=expression.spec,
            to_name=result_name,
            called_name=read_text_function,
            expression=expression,
            emit=emit,
            context=context,
        )


def generateImportlibResourcesFilesCallCode(to_name, expression, emit, context):
    package_name = generateChildExpressionCode(
        expression=expression.getPackageNameUsed(),
        child_name="package_name",
        emit=emit,
        context=context,
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "files_value", expression, emit, context
    ) as result_name:
        files_function = context.allocateTempName("files_function", unique=True)

        getImportModuleNameHardCode(
            to_name=files_function,
            module_name=expression.importlib_resources_name,
            import_name="files",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=files_function,
            expression=expression,
            arg_names=(package_name,),
            emit=emit,
            context=context,
        )


def generatePkgResourcesResourceStreamCallCode(to_name, expression, emit, context):
    package_name, resource_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "resource_stream_value", expression, emit, context
    ) as result_name:
        resource_stream_function = context.allocateTempName(
            "resource_stream_function", unique=True
        )

        getImportModuleNameHardCode(
            to_name=resource_stream_function,
            module_name="pkg_resources",
            import_name="resource_stream",
            needs_check=not shallMakeModule(),
            emit=emit,
            context=context,
        )

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=resource_stream_function,
            expression=expression,
            arg_names=(package_name, resource_name),
            emit=emit,
            context=context,
        )


def generateOsUnameCallCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "os_uname_value", expression, emit, context
    ) as result_name:
        os_uname_function = context.allocateTempName("os_uname_function", unique=True)

        getImportModuleNameHardCode(
            to_name=os_uname_function,
            module_name="os",
            import_name="uname",
            needs_check=False,
            emit=emit,
            context=context,
        )

        getCallCodeNoArgs(
            to_name=result_name,
            called_name=os_uname_function,
            expression=expression,
            emit=emit,
            context=context,
        )


def generateOsPathExistsCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_FILE_EXISTS",
        tstate=True,
        arg_desc=(("exists_arg", expression.subnode_path),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathIsfileCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_FILE_ISFILE",
        tstate=True,
        arg_desc=(("isfile_arg", expression.subnode_path),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathIsdirCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_FILE_ISDIR",
        tstate=True,
        arg_desc=(("isdir_arg", expression.subnode_path),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathBasenameCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_BASENAME",
        tstate=True,
        arg_desc=(("path_arg", expression.subnode_p),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathDirnameCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_DIRNAME",
        tstate=True,
        arg_desc=(("path_arg", expression.subnode_p),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathNormpathCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_NORMPATH",
        tstate=True,
        arg_desc=(("path_arg", expression.subnode_path),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathAbspathCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_ABSPATH",
        tstate=True,
        arg_desc=(("path_arg", expression.subnode_path),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsPathIsabsCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_PATH_ISABS",
        tstate=True,
        arg_desc=(("path_arg", expression.subnode_s),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateOsListdirCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_LISTDIR",
        tstate=True,
        arg_desc=(("path_arg", expression.subnode_path),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateOsStatCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_STAT",
        tstate=True,
        arg_desc=(
            ("path_arg", expression.subnode_path),
            ("dir_fd_arg", expression.subnode_dir_fd),
            ("follow_symlinks_arg", expression.subnode_follow_symlinks),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateOsLstatCallCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="OS_LSTAT",
        tstate=True,
        arg_desc=(
            ("path_arg", expression.subnode_path),
            ("dir_fd_arg", expression.subnode_dir_fd),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


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
