#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
from .ErrorCodes import getErrorExitCode


def generateCAPIObjectCodeCommon(to_name, capi, arg_desc, may_raise, ref_count,
                                 source_ref, emit, context, none_null = False):
    arg_names = []

    for arg_name, arg_expression in arg_desc:
        if arg_expression is None and none_null:
            arg_names.append("NULL")
        else:
            arg_name = context.allocateTempName(arg_name)

            generateExpressionCode(
                to_name    = arg_name,
                expression = arg_expression,
                emit       = emit,
                context    = context
            )

            arg_names.append(arg_name)

    context.setCurrentSourceCodeReference(source_ref)

    getCAPIObjectCode(
        to_name   = to_name,
        capi      = capi,
        arg_names = arg_names,
        may_raise = may_raise,
        ref_count = ref_count,
        emit      = emit,
        context   = context
    )


def generateCAPIObjectCode(to_name, capi, arg_desc, may_raise, source_ref, emit,
                           context, none_null = False):
    generateCAPIObjectCodeCommon(
        to_name    = to_name,
        capi       = capi,
        arg_desc   = arg_desc,
        may_raise  = may_raise,
        ref_count  = 1,
        source_ref = source_ref,
        emit       = emit,
        context    = context,
        none_null  = none_null
    )


def generateCAPIObjectCode0(to_name, capi, arg_desc, may_raise, source_ref,
                            emit, context, none_null = False):
    generateCAPIObjectCodeCommon(
        to_name    = to_name,
        capi       = capi,
        arg_desc   = arg_desc,
        may_raise  = may_raise,
        ref_count  = 0,
        source_ref = source_ref,
        emit       = emit,
        context    = context,
        none_null  = none_null
    )


def getCAPIObjectCode(to_name, capi, arg_names, may_raise, ref_count, emit,
                      context):
    emit(
        "%s = %s( %s );" % (
            to_name,
            capi,
            ", ".join(arg_names)
        )
    )

    getErrorExitCode(
        check_name    = to_name,
        release_names = (
            arg_name
            for arg_name in
            arg_names
            if arg_name != "NULL"
        ),
        needs_check   = may_raise,
        emit          = emit,
        context       = context
    )

    if ref_count:
        context.addCleanupTempName(to_name)


def getReferenceExportCode(base_name, emit, context):
    if not context.needsCleanup(base_name):
        emit("Py_INCREF( %s );" % base_name)
