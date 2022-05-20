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
"""Code generation for package resources access."""

from nuitka.Options import shallMakeModule

from .CallCodes import getCallCodePosArgsQuick
from .CodeHelpers import (
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ImportCodes import getImportModuleNameHardCode


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
            needs_check=expression.mayRaiseException(BaseException),
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
            needs_check=expression.mayRaiseException(BaseException),
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
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )


def generateImportlibResourcesReadTextCallCode(to_name, expression, emit, context):
    (
        package_name,
        resource_name,
        encoding_name,
        errors_name,
    ) = generateChildExpressionsCode(expression=expression, emit=emit, context=context)

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

        getCallCodePosArgsQuick(
            to_name=result_name,
            called_name=read_text_function,
            expression=expression,
            arg_names=(package_name, resource_name, encoding_name, errors_name),
            needs_check=expression.mayRaiseException(BaseException),
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
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )
