#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation for standard CPython/API calls.

This is generic stuff.
"""

from .CodeHelpers import generateExpressionCode
from .ErrorCodes import getErrorExitCode, getReleaseCode


def generateCAPIObjectCodeCommon(
    to_name,
    capi,
    arg_desc,
    may_raise,
    conversion_check,
    ref_count,
    source_ref,
    emit,
    context,
    none_null=False,
):
    arg_names = []

    for arg_name, arg_expression in arg_desc:
        if arg_expression is None and none_null:
            arg_names.append("NULL")
        else:
            arg_name = context.allocateTempName(arg_name)

            generateExpressionCode(
                to_name=arg_name, expression=arg_expression, emit=emit, context=context
            )

            arg_names.append(arg_name)

    context.setCurrentSourceCodeReference(source_ref)

    getCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        arg_names=arg_names,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=ref_count,
        emit=emit,
        context=context,
    )


def generateCAPIObjectCode(
    to_name,
    capi,
    arg_desc,
    may_raise,
    conversion_check,
    source_ref,
    emit,
    context,
    none_null=False,
):
    generateCAPIObjectCodeCommon(
        to_name=to_name,
        capi=capi,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=1,
        source_ref=source_ref,
        emit=emit,
        context=context,
        none_null=none_null,
    )


def generateCAPIObjectCode0(
    to_name,
    capi,
    arg_desc,
    may_raise,
    conversion_check,
    source_ref,
    emit,
    context,
    none_null=False,
):
    generateCAPIObjectCodeCommon(
        to_name=to_name,
        capi=capi,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=0,
        source_ref=source_ref,
        emit=emit,
        context=context,
        none_null=none_null,
    )


def getCAPIObjectCode(
    to_name, capi, arg_names, may_raise, conversion_check, ref_count, emit, context
):
    # TODO: Use context manager here too.
    if to_name.c_type == "PyObject *":
        value_name = to_name
    else:
        value_name = context.allocateTempName("capi_result")

    emit(
        "%s = %s( %s );"
        % (value_name, capi, ", ".join(str(arg_name) for arg_name in arg_names))
    )

    getErrorExitCode(
        check_name=value_name,
        release_names=(arg_name for arg_name in arg_names if arg_name != "NULL"),
        needs_check=may_raise,
        emit=emit,
        context=context,
    )

    if ref_count:
        context.addCleanupTempName(value_name)

    if to_name is not value_name:
        to_name.getCType().emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            needs_check=conversion_check,
            emit=emit,
            context=context,
        )

        if ref_count:
            getReleaseCode(value_name, emit, context)


def getReferenceExportCode(base_name, emit, context):
    if not context.needsCleanup(base_name):
        emit("Py_INCREF( %s );" % base_name)
