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
""" Integer related codes, long and int.

"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import generateChildExpressionsCode
from .ErrorCodes import getErrorExitCode
from .PythonAPICodes import generateCAPIObjectCode


def generateBuiltinLong1Code(to_name, expression, emit, context):
    assert python_version < 300

    value = expression.getValue()

    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "PyNumber_Long",
        arg_desc   = (
            ("long_arg", value),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinLong2Code(to_name, expression, emit, context):
    assert python_version < 300

    value_name, base_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = TO_LONG2( %s, %s );" % (
            to_name,
            value_name,
            base_name
        )
    )

    getErrorExitCode(
        check_name    = to_name,
        release_names = (value_name, base_name),
        emit          = emit,
        context       = context
    )

    context.addCleanupTempName(to_name)


def generateBuiltinInt1Code(to_name, expression, emit, context):
    value = expression.getValue()

    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "PyNumber_Int",
        arg_desc   = (
            ("int_arg", value),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context,
    )


def generateBuiltinInt2Code(to_name, expression, emit, context):
    value_name, base_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = TO_INT2( %s, %s );" % (
            to_name,
            value_name,
            base_name
        )
    )

    getErrorExitCode(
        check_name    = to_name,
        release_names = (value_name, base_name),
        emit          = emit,
        context       = context
    )

    context.addCleanupTempName(to_name)
