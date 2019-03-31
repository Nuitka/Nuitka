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
""" String related codes, str and unicode.

"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitCode
from .PythonAPICodes import generateCAPIObjectCode
from .TupleCodes import getTupleCreationCode


def generateBuiltinBytes1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BYTES1",
        arg_desc=(("bytes_arg", expression.getValue()),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinBytes3Code(to_name, expression, emit, context):
    encoding = expression.getEncoding()
    errors = expression.getErrors()

    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BYTES3",
        arg_desc=(
            ("bytes_arg", expression.getValue()),
            ("bytes_encoding", encoding),
            ("bytes_errors", errors),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinUnicodeCode(to_name, expression, emit, context):
    encoding = expression.getEncoding()
    errors = expression.getErrors()

    if encoding is None and errors is None:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="PyObject_Unicode",
            arg_desc=(
                (
                    "str_arg" if python_version < 300 else "unicode_arg",
                    expression.getValue(),
                ),
            ),
            may_raise=expression.mayRaiseException(BaseException),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            source_ref=expression.getCompatibleSourceReference(),
            emit=emit,
            context=context,
        )
    else:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="TO_UNICODE3",
            arg_desc=(
                ("unicode_arg", expression.getValue()),
                ("unicode_encoding", encoding),
                ("unicode_errors", errors),
            ),
            may_raise=expression.mayRaiseException(BaseException),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            source_ref=expression.getCompatibleSourceReference(),
            none_null=True,
            emit=emit,
            context=context,
        )


def generateBuiltinStrCode(to_name, expression, emit, context):
    if python_version < 300:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="PyObject_Str",
            arg_desc=(("str_arg", expression.getValue()),),
            may_raise=expression.mayRaiseException(BaseException),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            source_ref=expression.getCompatibleSourceReference(),
            emit=emit,
            context=context,
        )
    else:
        return generateBuiltinUnicodeCode(
            to_name=to_name, expression=expression, emit=emit, context=context
        )


def generateBuiltinChrCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_CHR",
        arg_desc=(("chr_arg", expression.getValue()),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinOrdCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ORD",
        arg_desc=(("ord_arg", expression.getValue()),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateStringContenationCode(to_name, expression, emit, context):
    values = expression.getValues()

    with withObjectCodeTemporaryAssignment(
        to_name, "string_concat_result", expression, emit, context
    ) as value_name:

        tuple_temp_name = context.allocateTempName("string_concat_values")

        # TODO: Consider using _PyUnicode_JoinArray which avoids the tuple,
        # but got all to be able to release arrays.
        getTupleCreationCode(
            to_name=tuple_temp_name, elements=values, emit=emit, context=context
        )

        emit(
            "%s = PyUnicode_Join( %s, %s );"
            % (value_name, context.getConstantCode(""), tuple_temp_name)
        )

        getErrorExitCode(
            check_name=value_name,
            release_name=tuple_temp_name,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateBuiltinFormatCode(to_name, expression, emit, context):
    value_name = context.allocateTempName("format_value")

    generateExpressionCode(
        to_name=value_name, expression=expression.getValue(), emit=emit, context=context
    )

    format_spec_name = context.allocateTempName("format_spec")

    format_spec = expression.getFormatSpec()

    if format_spec is None:
        emit("%s = %s;" % (format_spec_name, context.getConstantCode("")))
    else:
        generateExpressionCode(
            to_name=format_spec_name, expression=format_spec, emit=emit, context=context
        )

    with withObjectCodeTemporaryAssignment(
        to_name, "format_result", expression, emit, context
    ) as result_name:

        emit(
            "%s = BUILTIN_FORMAT( %s, %s );"
            % (result_name, value_name, format_spec_name)
        )

        getErrorExitCode(
            check_name=result_name,
            release_names=(value_name, format_spec_name),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateBuiltinAsciiCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyObject_ASCII",
        arg_desc=(("ascii_arg", expression.getValue()),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )
