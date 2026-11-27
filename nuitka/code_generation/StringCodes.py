#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""String related codes, str and unicode."""

from nuitka.PythonVersions import python_version

from .CallCodes import getCallCodePosVariableKeywordVariableArgs
from .CodeHelpers import (
    decideConversionCheckNeeded,
    withObjectCodeTemporaryAssignment,
)
from .PythonAPICodes import (
    CArg,
    ConstantArg,
    OptionalArg,
    TupleArg,
    generateCAPIObjectCode,
    makeArgDescFromExpression,
)

_template_string_conversion_codes = {
    ord("a"): 3,
    ord("r"): 2,
    ord("s"): 1,
}


def _getTemplateInterpolationConversionCode(conversion):
    """Map AST conversion ordinal (-1 for none) to '_PyInterpolation_Build' FVC code."""
    if conversion == -1:
        return 0

    return _template_string_conversion_codes[conversion]


def generateBuiltinBytes1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BYTES1",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinBytes3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BYTES3",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinUnicodeCode(to_name, expression, emit, context):
    encoding = expression.subnode_encoding
    errors = expression.subnode_errors

    if encoding is None and errors is None:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="BUILTIN_UNICODE1",
            tstate=False,
            arg_desc=(
                (
                    "str_arg" if python_version < 0x300 else "unicode_arg",
                    expression.subnode_value,
                ),
            ),
            may_raise=expression.mayRaiseExceptionOperation(),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            source_ref=expression.getCompatibleSourceReference(),
            emit=emit,
            context=context,
        )
    else:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="BUILTIN_UNICODE3",
            tstate=False,
            arg_desc=makeArgDescFromExpression(expression),
            may_raise=expression.mayRaiseExceptionOperation(),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            source_ref=expression.getCompatibleSourceReference(),
            none_null=True,
            emit=emit,
            context=context,
        )


def generateBuiltinStrCode(to_name, expression, emit, context):
    if python_version < 0x300:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="BUILTIN_STR",
            tstate=False,
            arg_desc=makeArgDescFromExpression(expression),
            may_raise=expression.mayRaiseExceptionOperation(),
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
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinOrdCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ORD",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateStringConcatenationCode(to_name, expression, emit, context):
    # TODO: Consider using _PyUnicode_JoinArray which avoids the tuple,
    # but got all to be able to release arrays.
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyUnicode_Join",
        tstate=False,
        arg_desc=(
            ConstantArg(""),
            TupleArg("string_concat_values", expression.subnode_values),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinFormatCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_FORMAT",
        tstate=True,
        arg_desc=(
            ("format_value", expression.subnode_value),
            OptionalArg("format_spec", expression.subnode_format_spec, ConstantArg("")),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinAsciiCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyObject_ASCII",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateStrOperationCode(to_name, expression, emit, context):
    api_name = expression.kind.rsplit("_")[-1]

    if str is bytes:
        api_name = "STR_" + api_name
    else:
        api_name = "UNICODE_" + api_name

    # This operation has no default available for compile time.
    none_null = expression.isExpressionStrOperationDecode3()

    generateCAPIObjectCode(
        to_name=to_name,
        capi=api_name,
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
        none_null=none_null,
    )


def generateBytesOperationCode(to_name, expression, emit, context):
    assert str is not bytes

    api_name = "BYTES_" + expression.kind.rsplit("_")[-1]

    generateCAPIObjectCode(
        to_name=to_name,
        capi=api_name,
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateStrFormatMethodCode(to_name, expression, emit, context):
    if str is bytes:
        called_name = "str_builtin_format"
    else:
        called_name = "unicode_builtin_format"

    with withObjectCodeTemporaryAssignment(
        to_name, "format_result", expression, emit, context
    ) as result_name:
        getCallCodePosVariableKeywordVariableArgs(
            to_name=result_name,
            expression=expression,
            called_name=called_name,
            call_args=(expression.subnode_str_arg,) + expression.subnode_args,
            pairs=expression.subnode_pairs,
            emit=emit,
            context=context,
        )


def generateTemplateStringCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="_PyTemplate_Build",
        tstate=False,
        arg_desc=(
            ConstantArg(expression.str_values),
            TupleArg("template_values", expression.subnode_interpolations),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateTemplateInterpolationCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="_PyInterpolation_Build",
        tstate=False,
        arg_desc=(
            ("value_value", expression.subnode_value),
            ConstantArg(expression.str_value),
            CArg(_getTemplateInterpolationConversionCode(expression.conversion)),
            OptionalArg(
                "format_spec_value",
                expression.subnode_format_spec,
                ConstantArg(""),
            ),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
