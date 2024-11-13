#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Built-in codes

This is code generation for built-in references, and some built-ins like range,
bin, etc.
"""

from nuitka import Builtins
from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import (
    getAssertionCode,
    getErrorExitBoolCode,
    getErrorExitCode,
)
from .PythonAPICodes import generateCAPIObjectCode


def generateBuiltinAbsCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ABS",
        tstate=False,
        arg_desc=(("abs_arg", expression.subnode_operand),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinRefCode(to_name, expression, emit, context):
    builtin_name = expression.getBuiltinName()

    with withObjectCodeTemporaryAssignment(
        to_name, "builtin_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = LOOKUP_BUILTIN(%s);"
            % (value_name, context.getConstantCode(constant=builtin_name))
        )

        getAssertionCode(check="%s != NULL" % value_name, emit=emit)

        # Gives no reference


def generateBuiltinAnonymousRefCode(to_name, expression, emit, context):
    builtin_name = expression.getBuiltinName()

    with withObjectCodeTemporaryAssignment(
        to_name, "builtin_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = (PyObject *)%s;"
            % (value_name, Builtins.builtin_anon_codes[builtin_name])
        )


def generateBuiltinType1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_TYPE1",
        tstate=False,
        arg_desc=(("type_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinType3Code(to_name, expression, emit, context):
    type_name, bases_name, dict_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "type3_result", expression, emit, context
    ) as value_name:
        emit(
            "%s = BUILTIN_TYPE3(tstate, %s, %s, %s, %s);"
            % (
                value_name,
                context.getConstantCode(constant=context.getModuleName().asString()),
                type_name,
                bases_name,
                dict_name,
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(type_name, bases_name, dict_name),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateBuiltinInputCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_INPUT",
        tstate=True,
        arg_desc=(("input_arg", expression.subnode_prompt),),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinOpenCode(to_name, expression, emit, context):
    arg_desc = (
        ("open_filename", expression.subnode_filename),
        ("open_mode", expression.subnode_mode),
        ("open_buffering", expression.subnode_buffering),
    )

    if python_version >= 0x300:
        arg_desc += (
            ("open_encoding", expression.subnode_encoding),
            ("open_errors", expression.subnode_errors),
            ("open_newline", expression.subnode_newline),
            ("open_closefd", expression.subnode_closefd),
            ("open_opener", expression.subnode_opener),
        )

    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_OPEN",
        tstate=True,
        arg_desc=arg_desc,
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinSum1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_SUM1",
        tstate=True,
        arg_desc=(("sum_sequence", expression.subnode_sequence),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinSum2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_SUM2",
        tstate=True,
        arg_desc=(
            ("sum_sequence", expression.subnode_sequence),
            ("sum_start", expression.subnode_start),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinRange1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_RANGE",
        tstate=True,
        arg_desc=(("range_arg", expression.subnode_low),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinRange2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_RANGE2",
        tstate=True,
        arg_desc=(
            ("range2_low", expression.subnode_low),
            ("range2_high", expression.subnode_high),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinRange3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_RANGE3",
        tstate=True,
        arg_desc=(
            ("range3_low", expression.subnode_low),
            ("range3_high", expression.subnode_high),
            ("range3_step", expression.subnode_step),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinXrange1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_XRANGE1",
        tstate=True,
        arg_desc=(("xrange_low", expression.subnode_low),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
        none_null=True,
    )


def generateBuiltinXrange2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_XRANGE2",
        tstate=True,
        arg_desc=(
            ("xrange_low", expression.subnode_low),
            ("xrange_high", expression.subnode_high),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
        none_null=True,
    )


def generateBuiltinXrange3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_XRANGE3",
        tstate=True,
        arg_desc=(
            ("xrange_low", expression.subnode_low),
            ("xrange_high", expression.subnode_high),
            ("xrange_step", expression.subnode_step),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
        none_null=True,
    )


def generateBuiltinFloatCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="TO_FLOAT",
        tstate=False,
        arg_desc=(("float_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinComplex1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_COMPLEX1",
        tstate=True,
        arg_desc=(("real_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinComplex2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_COMPLEX2",
        tstate=True,
        arg_desc=(
            ("real_arg", expression.subnode_real),
            ("imag_arg", expression.subnode_imag),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinBoolCode(to_name, expression, emit, context):
    (arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("%s = CHECK_IF_TRUE(%s);" % (res_name, arg_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_name=arg_name,
        needs_check=expression.subnode_value.mayRaiseExceptionBool(BaseException),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s != 0" % res_name, emit=emit
    )


def generateBuiltinBinCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BIN",
        tstate=False,
        arg_desc=(("bin_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinOctCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_OCT",
        tstate=True,
        arg_desc=(("oct_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinHexCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_HEX",
        tstate=True,
        arg_desc=(("hex_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinBytearray1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BYTEARRAY1",
        tstate=False,
        arg_desc=(("bytearray_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinBytearray3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_BYTEARRAY3",
        tstate=True,
        arg_desc=(
            ("bytearray_string", expression.subnode_string),
            ("bytearray_encoding", expression.subnode_encoding),
            ("bytearray_errors", expression.subnode_errors),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinStaticmethodCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_STATICMETHOD",
        tstate=True,
        arg_desc=(("staticmethod_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinClassmethodCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_CLASSMETHOD",
        tstate=True,
        arg_desc=(("classmethod_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def getBuiltinCallViaSpecCode(spec, to_name, called_name, expression, emit, context):
    arg_value_names = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "%s_result" % spec.name.replace(".", "_"), expression, emit, context
    ) as value_name:
        emit(
            """\
{
    PyObject *args[] = {%(arg_value_names)s};
    char const *arg_names[] = {%(arg_names)s};

    %(to_name)s = CALL_BUILTIN_KW_ARGS(
        tstate,
        %(called_name)s,
        args,
        arg_names,
        sizeof(args) / sizeof(PyObject *),
        %(kw_only_count)d
    );
}
"""
            % {
                "to_name": value_name,
                "called_name": called_name,
                "arg_names": ",".join(
                    '"%s"' % arg_name for arg_name in spec.getArgumentNames()
                ),
                "arg_value_names": ",".join(
                    (str(arg_value_name) if arg_value_name else "NULL")
                    for arg_value_name in arg_value_names
                ),
                "kw_only_count": spec.getKwOnlyParameterCount(),
            }
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=[called_name] + list(arg_value_names),
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
