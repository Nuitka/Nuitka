#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Built-in codes

This is code generation for built-in references, and some built-ins like int,
long, etc.
"""
from nuitka import Builtins

from .ConstantCodes import getConstantCode
from .ErrorCodes import getAssertionCode, getErrorExitCode, getReleaseCodes


def getBuiltinRefCode(to_name, builtin_name, emit, context):
    emit(
        "%s = LOOKUP_BUILTIN( %s );" % (
            to_name,
            getConstantCode(
                constant = builtin_name,
                context  = context
            )
        )
    )

    getAssertionCode(
        check = "%s != NULL" % to_name,
        emit  = emit
    )

    # Gives no reference


def getBuiltinAnonymousRefCode(to_name, builtin_name, emit):
    emit(
        "%s = (PyObject *)%s;" % (
            to_name,
            Builtins.builtin_anon_codes[builtin_name]
        )
    )


def getBuiltinSuperCode(to_name, type_name, object_name, emit, context):
    emit(
        "%s = BUILTIN_SUPER( %s, %s );" % (
            to_name,
            type_name if type_name is not None else "NULL",
            object_name if object_name is not None else "NULL"
        )
    )

    getReleaseCodes(
        release_names = (type_name, object_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getBuiltinType3Code(to_name, type_name, bases_name, dict_name, emit,
                        context):
    emit(
        "%s = BUILTIN_TYPE3( %s, %s, %s, %s );" % (
            to_name,
            getConstantCode(
                constant = context.getModuleName(),
                context  = context
            ),
            type_name,
            bases_name,
            dict_name
        ),
    )

    getReleaseCodes(
        release_names = (type_name, bases_name, dict_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getBuiltinLong2Code(to_name, base_name, value_name, emit, context):
    emit(
        "%s = TO_LONG2( %s, %s );" % (
            to_name,
            value_name,
            base_name
        )
    )

    getReleaseCodes(
        release_names = (value_name, base_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getBuiltinInt2Code(to_name, base_name, value_name, emit, context):
    emit(
        "%s = TO_INT2( %s, %s );" % (
            to_name,
            value_name,
            base_name
        )
    )

    getReleaseCodes(
        release_names = (value_name, base_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)
