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
""" Codes for operations.

There are unary and binary operations. Many of them have specializations and
of course types could play into it. Then there is also the added difficulty of
in-place assignments, which have other operation variants.
"""


from . import OperatorCodes
from .CodeHelpers import (
    generateChildExpressionsCode,
    pickCodeHelper,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode


def generateOperationBinaryCode(to_name, expression, emit, context):
    left_arg_name, right_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # TODO: Decide and use one single spelling, inplace or in_place
    inplace = expression.isInplaceSuspect()

    assert not inplace or not expression.getLeft().isCompileTimeConstant(), expression

    _getBinaryOperationCode(
        to_name=to_name,
        expression=expression,
        operator=expression.getOperator(),
        arg_names=(left_arg_name, right_arg_name),
        in_place=inplace,
        emit=emit,
        context=context,
    )


def generateOperationNotCode(to_name, expression, emit, context):
    arg_name, = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("%s = CHECK_IF_TRUE( %s );" % (res_name, arg_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_name=arg_name,
        needs_check=expression.getOperand().mayRaiseExceptionBool(BaseException),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s == 0" % res_name, emit=emit
    )


def generateOperationUnaryCode(to_name, expression, emit, context):
    arg_name, = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    _getUnaryOperationCode(
        to_name=to_name,
        expression=expression,
        operator=expression.getOperator(),
        arg_name=arg_name,
        needs_check=expression.mayRaiseException(BaseException),
        emit=emit,
        context=context,
    )


_add_helpers_set = set(
    (
        "BINARY_OPERATION_ADD_OBJECT_OBJECT",
        "BINARY_OPERATION_ADD_OBJECT_INT",
        "BINARY_OPERATION_ADD_OBJECT_LONG",
        "BINARY_OPERATION_ADD_OBJECT_STR",
        "BINARY_OPERATION_ADD_OBJECT_FLOAT",
        "BINARY_OPERATION_ADD_OBJECT_UNICODE",
        "BINARY_OPERATION_ADD_OBJECT_TUPLE",
        "BINARY_OPERATION_ADD_OBJECT_LIST",
        "BINARY_OPERATION_ADD_OBJECT_BYTES",
        "BINARY_OPERATION_ADD_INT_OBJECT",
        "BINARY_OPERATION_ADD_LONG_OBJECT",
        "BINARY_OPERATION_ADD_STR_OBJECT",
        "BINARY_OPERATION_ADD_FLOAT_OBJECT",
        "BINARY_OPERATION_ADD_UNICODE_OBJECT",
        "BINARY_OPERATION_ADD_TUPLE_OBJECT",
        "BINARY_OPERATION_ADD_LIST_OBJECT",
        "BINARY_OPERATION_ADD_BYTES_OBJECT",
        "BINARY_OPERATION_ADD_INT_INT",
        "BINARY_OPERATION_ADD_LONG_LONG",
        "BINARY_OPERATION_ADD_STR_STR",
        "BINARY_OPERATION_ADD_FLOAT_FLOAT",
        "BINARY_OPERATION_ADD_UNICODE_UNICODE",
        "BINARY_OPERATION_ADD_TUPLE_TUPLE",
        "BINARY_OPERATION_ADD_LIST_LIST",
        "BINARY_OPERATION_ADD_BYTES_BYTES",
        "BINARY_OPERATION_ADD_LONG_FLOAT",
        "BINARY_OPERATION_ADD_FLOAT_LONG",
    )
)

_iadd_helpers_set = set(
    (
        "BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_STR_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_INT_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE",
        "BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_STR_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_INT_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_LIST_LIST_INPLACE",
        "BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE",
        "BINARY_OPERATION_ADD_STR_STR_INPLACE",
        "BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE",
        "BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE",
        "BINARY_OPERATION_ADD_INT_INT_INPLACE",
        "BINARY_OPERATION_ADD_LONG_LONG_INPLACE",
        "BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE",
    )
)


def _getBinaryOperationCode(
    to_name, expression, operator, arg_names, in_place, emit, context
):
    # This needs to have one case per operation of Python, and there are many
    # of these, pylint: disable=too-many-branches,too-many-statements
    left = expression.getLeft()

    prefix_args = ()
    ref_count = 1

    needs_check = expression.mayRaiseExceptionOperation()

    if operator == "Pow":
        helper = "POWER_OPERATION"
    elif operator == "IPow" and in_place:
        helper = "POWER_OPERATION_INPLACE"
    elif operator == "IPow":
        helper = "POWER_OPERATION2"
    elif operator == "Add":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_ADD",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=_add_helpers_set,
        )
    elif operator == "IAdd" and in_place:
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_ADD",
            suffix="_INPLACE",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=_iadd_helpers_set,
        )
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
        prefix_args = (OperatorCodes.binary_operator_codes[operator],)
    else:
        assert False, operator

    # We must assume to write to a variable is "in_place" is active, not e.g.
    # a constant reference. That was asserted before calling us.
    if in_place:
        res_name = context.getBoolResName()

        # For module variable C type to reference later.
        if left.getVariable().isModuleVariable():
            emit("%s = %s;" % (context.getInplaceLeftName(), arg_names[0]))

        # We may have not specialized this one yet, so lets use generic in-place
        # code, or the helper specified.
        if helper == "BINARY_OPERATION":
            emit(
                "%s = BINARY_OPERATION_INPLACE( %s, &%s, %s );"
                % (
                    res_name,
                    OperatorCodes.binary_operator_codes[operator],
                    arg_names[0],
                    arg_names[1],
                )
            )
        else:
            emit("%s = %s( &%s, %s );" % (res_name, helper, arg_names[0], arg_names[1]))

            ref_count = 0

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            release_names=arg_names,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        emit("%s = %s;" % (to_name, arg_names[0]))

        if ref_count:
            context.addCleanupTempName(to_name)

    else:
        with withObjectCodeTemporaryAssignment(
            to_name, "op_%s_res" % operator.lower(), expression, emit, context
        ) as value_name:

            emit(
                "%s = %s( %s );"
                % (
                    value_name,
                    helper,
                    ", ".join(str(arg_name) for arg_name in prefix_args + arg_names),
                )
            )

            getErrorExitCode(
                check_name=value_name,
                release_names=arg_names,
                needs_check=needs_check,
                emit=emit,
                context=context,
            )

            if ref_count:
                context.addCleanupTempName(value_name)


def _getUnaryOperationCode(
    to_name, expression, operator, arg_name, needs_check, emit, context
):
    impl_helper, ref_count = OperatorCodes.unary_operator_codes[operator]

    helper = "UNARY_OPERATION"
    prefix_args = (impl_helper,)

    with withObjectCodeTemporaryAssignment(
        to_name, "op_%s_res" % operator.lower(), expression, emit, context
    ) as value_name:

        emit(
            "%s = %s( %s );"
            % (
                value_name,
                helper,
                ", ".join(str(arg_name) for arg_name in prefix_args + (arg_name,)),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_name=arg_name,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        if ref_count:
            context.addCleanupTempName(value_name)
