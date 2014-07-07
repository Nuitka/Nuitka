#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)


def getCAPIObjectCode(to_name, capi, arg_names, ref_count, emit, context):
    emit(
        "%s = %s( %s );" % (
            to_name,
            capi,
            ", ".join(arg_names)
        )
    )

    getReleaseCodes(
        release_names = (
            arg_name
            for arg_name in
            arg_names
            if arg_name != "NULL"
        ),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    if ref_count:
        context.addCleanupTempName(to_name)


def getCAPIIntCode(res_name, capi, args, emit, context):
    emit(
        "%s = %s( %s );" % (
            res_name,
            capi,
            ", ".join(args)
        )
    )

    # TODO: Order, potentially
    for arg in args:
        getReleaseCode(
            release_name = arg,
            emit         = emit,
            context      = context
        )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
        emit      = emit,
        context   = context
    )


def getReferenceExportCode(base_name, context):
    if context.needsCleanup(base_name):
        return base_name
    else:
        return "INCREASE_REFCOUNT( %s )" % base_name
