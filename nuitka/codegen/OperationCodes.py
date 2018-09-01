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
""" Codes for operations.

There are unary and binary operations. Many of them have specializations and
of course types could play into it. Then there is also the added difficulty of
in-place assignments, which have other operation variants.
"""

from . import OperatorCodes
from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode


def generateOperationBinaryCode(to_name, expression, emit, context):
    left_arg_name, right_arg_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # TODO: Decide and use one single spelling, inplace or in_place
    inplace = expression.isInplaceSuspect()

    assert not inplace or not expression.getLeft().isCompileTimeConstant(),  \
        expression

    getOperationCode(
        to_name          = to_name,
        operator         = expression.getOperator(),
        arg_names        = (left_arg_name, right_arg_name),
        in_place         = inplace,
        needs_check      = expression.mayRaiseException(BaseException),
        conversion_check = decideConversionCheckNeeded(to_name, expression),
        emit             = emit,
        context          = context
    )


def generateOperationNotCode(to_name, expression, emit, context):
    arg_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    res_name = context.getIntResName()

    emit(
         "%s = CHECK_IF_TRUE( %s );" % (
            res_name,
            arg_name
        )
    )

    getErrorExitBoolCode(
        condition    = "%s == -1" % res_name,
        release_name = arg_name,
        needs_check  = expression.getOperand().mayRaiseExceptionBool(BaseException),
        emit         = emit,
        context      = context
    )

    emit(
        to_name.getCType().getAssignmentCodeFromBoolCondition(
            to_name   = to_name,
            condition = "%s == 0" % res_name
        )
    )


def generateOperationUnaryCode(to_name, expression, emit, context):
    arg_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    getOperationCode(
        to_name          = to_name,
        operator         = expression.getOperator(),
        arg_names        = (arg_name,),
        in_place         = False,
        needs_check      = expression.mayRaiseException(BaseException),
        conversion_check = decideConversionCheckNeeded(to_name, expression),
        emit             = emit,
        context          = context
    )


def getOperationCode(to_name, operator, arg_names, in_place, needs_check,
                     conversion_check, emit, context):
    # This needs to have one case per operation of Python, and there are many
    # of these, pylint: disable=too-many-branches,too-many-statements

    # TODO: Use "needs_check" too.

    prefix_args = ()
    ref_count = 1

    if operator == "Pow":
        helper = "POWER_OPERATION"
    elif operator == "IPow" and in_place:
        helper = "POWER_OPERATION_INPLACE"
    elif operator == "IPow":
        helper = "POWER_OPERATION2"
    elif operator == "Add":
        helper = "BINARY_OPERATION_ADD"
    elif operator == "IAdd" and in_place:
        helper = "BINARY_OPERATION_ADD_INPLACE"
    elif operator == "IMult" and in_place:
        helper = "BINARY_OPERATION_MUL_INPLACE"
    elif operator == "Sub":
        helper = "BINARY_OPERATION_SUB"
    elif operator == "Div":
        helper = "BINARY_OPERATION_DIV"
    elif operator == "FloorDiv":
        helper = "BINARY_OPERATION_FLOORDIV"
    elif operator == "TrueDiv":
        helper = "BINARY_OPERATION_TRUEDIV"
    elif operator == "Mult":
        helper = "BINARY_OPERATION_MUL"
    elif operator == "Mod":
        helper = "BINARY_OPERATION_REMAINDER"
    elif operator == "Divmod":
        helper = "BUILTIN_DIVMOD"
    elif len(arg_names) == 2:
        helper = "BINARY_OPERATION"
        prefix_args = (
            OperatorCodes.binary_operator_codes[ operator ],
        )
    elif len(arg_names) == 1:
        impl_helper, ref_count = OperatorCodes.unary_operator_codes[ operator ]

        helper = "UNARY_OPERATION"
        prefix_args = (
            impl_helper,
        )
    else:
        assert False, operator

    # We must assume to write to a variable is "in_place" is active, not e.g.
    # a constant reference. That was asserted before calling us.
    if in_place:
        res_name = context.getBoolResName()

        # We may have not specialized this one yet, so lets use generic in-place
        # code, or the helper specified.
        if helper == "BINARY_OPERATION":
            emit(
                "%s = BINARY_OPERATION_INPLACE( %s, &%s, %s );" % (
                    res_name,
                    OperatorCodes.binary_operator_codes[ operator ],
                    arg_names[0],
                    arg_names[1],
                )
            )
        else:
            emit(
                "%s = %s( &%s, %s );" % (
                    res_name,
                    helper,
                    arg_names[0],
                    arg_names[1],
                )
            )

            ref_count = 0

        emit(
            "%s = %s;" % (
                to_name,
                arg_names[0]
            )
        )

        getErrorExitBoolCode(
            condition     = "%s == false" % res_name,
            release_names = arg_names,
            emit          = emit,
            context       = context
        )

        if ref_count:
            context.addCleanupTempName(to_name)

    else:
        if to_name.c_type != "PyObject *":
            value_name = context.allocateTempName("op_%s_res" % operator.lower())
        else:
            value_name = to_name

        emit(
            "%s = %s( %s );" % (
                value_name,
                helper,
                ", ".join(
                    str(arg_name)
                    for arg_name in
                    prefix_args + arg_names
                )
            )
        )

        getErrorExitCode(
            check_name    = value_name,
            release_names = arg_names,
            emit          = emit,
            context       = context
        )

        if value_name is not to_name:
            to_name.getCType().emitAssignConversionCode(
                to_name     = to_name,
                value_name  = value_name,
                needs_check = conversion_check,
                emit        = emit,
                context     = context
            )
        else:
            if ref_count:
                context.addCleanupTempName(to_name)
