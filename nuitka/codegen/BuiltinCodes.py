#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

This is code generation for built-in references, and some built-ins like range,
bin, etc.
"""
from nuitka import Builtins

from .ConstantCodes import getConstantCode
from .ErrorCodes import getAssertionCode, getErrorExitCode, getReleaseCodes
from .Helpers import generateChildExpressionsCode
from .PythonAPICodes import generateCAPIObjectCode, generateCAPIObjectCode0


def generateBuiltinRefCode(to_name, expression, emit, context):
    builtin_name = expression.getBuiltinName()

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


def generateBuiltinAnonymousRefCode(to_name, expression, emit, context):
    # Functions used for generation all accept context, but this one does
    # not use it. pylint: disable=W0613
    builtin_name = expression.getBuiltinName()

    emit(
        "%s = (PyObject *)%s;" % (
            to_name,
            Builtins.builtin_anon_codes[builtin_name]
        )
    )


def generateBuiltinType1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_TYPE1",
        arg_desc   = (
            ("type_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinType3Code(to_name, expression, emit, context):
    type_name, bases_name, dict_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

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


def generateBuiltinOpenCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_OPEN",
        arg_desc   = (
            ("open_filename", expression.getFilename()),
            ("open_mode", expression.getMode()),
            ("open_buffering", expression.getBuffering()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        none_null  = True,
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinRange1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_RANGE",
        arg_desc   = (
            ("range_arg", expression.getLow()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinRange2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_RANGE2",
        arg_desc   = (
            ("range2_low", expression.getLow()),
            ("range2_high", expression.getHigh()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinRange3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_RANGE3",
        arg_desc   = (
            ("range3_low", expression.getLow()),
            ("range3_high", expression.getHigh()),
            ("range3_step", expression.getStep()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinXrangeCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_XRANGE",
        arg_desc   = (
            ("xrange_low", expression.getLow()),
            ("xrange_high", expression.getHigh()),
            ("xrange_step", expression.getStep()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context,
        none_null  = True,
    )


def generateBuiltinFloatCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "TO_FLOAT",
        arg_desc   = (
            ("float_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinComplexCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "TO_COMPLEX",
        arg_desc   = (
            ("real_arg", expression.getReal()),
            ("imag_arg", expression.getImag())
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        none_null  = True,
        emit       = emit,
        context    = context
    )


def generateBuiltinBoolCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name    = to_name,
        capi       = "TO_BOOL",
        arg_desc   = (
            ("bool_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinBinCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_BIN",
        arg_desc   = (
            ("bin_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinOctCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_OCT",
        arg_desc   = (
            ("oct_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinHexCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_HEX",
        arg_desc   = (
            ("hex_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinBytearrayCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_BYTEARRAY",
        arg_desc   = (
            ("bytearray_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )
