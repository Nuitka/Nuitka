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
""" Codes for operations.

There are unary and binary operations. Many of them have specializations and
of course types could play into it. Then there is also the added difficulty of
in-place assignments, which have other operation variants.
"""

from . import OperatorCodes
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCode
from .Helpers import generateChildExpressionsCode


def generateOperationBinaryCode(to_name, expression, emit, context):
    left_arg_name, right_arg_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    getOperationCode(
        to_name   = to_name,
        operator  = expression.getOperator(),
        arg_names = (left_arg_name, right_arg_name),
        in_place  = expression.isInplaceSuspect(),
        emit      = emit,
        context   = context
    )


def generateOperationUnaryCode(to_name, expression, emit, context):
    arg_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    getOperationCode(
        to_name   = to_name,
        operator  = expression.getOperator(),
        arg_names = (arg_name,),
        in_place  = expression.isInplaceSuspect(),
        emit      = emit,
        context   = context
    )


def getOperationCode(to_name, operator, arg_names, in_place, emit, context):
    # This needs to have one case per operation of Python, and there are many
    # of these, # pylint: disable=R0912

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
    elif operator == "Sub":
        helper = "BINARY_OPERATION_SUB"
    elif operator == "Div":
        helper = "BINARY_OPERATION_DIV"
    elif operator == "Mult":
        helper = "BINARY_OPERATION_MUL"
    elif operator == "Mod":
        helper = "BINARY_OPERATION_REMAINDER"
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

    # This is not working, as we do assertions that are broken.
    if in_place:
        res_name = context.getBoolResName()

        # We may have not specialized this one yet, so lets use generic in-place
        # code, or the helper specificed.
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

        for arg_name in arg_names:
            getReleaseCode(
                arg_name,
                emit,
                context
            )

        getErrorExitBoolCode(
            condition = "%s == false" % res_name,
            emit      = emit,
            context   = context
        )

        if ref_count:
            context.addCleanupTempName(to_name)

    else:
        emit(
            "%s = %s( %s );" % (
                to_name,
                helper,
                ", ".join(prefix_args + arg_names)
            )
        )

        for arg_name in arg_names:
            getReleaseCode(
                arg_name,
                emit,
                context
            )

        getErrorExitCode(
            check_name = to_name,
            emit       = emit,
            context    = context
        )

        if ref_count:
            context.addCleanupTempName(to_name)
