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

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    ShapeTypeBytes,
    ShapeTypeFloat,
    ShapeTypeInt,
    ShapeTypeList,
    ShapeTypeLong,
    ShapeTypeStr,
    ShapeTypeTuple,
    ShapeTypeUnicode
)
from nuitka.PythonVersions import python_version

from . import OperatorCodes
from .CodeHelpers import (
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode
from .Reports import onMissingHelper


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

    _getOperationCode(
        to_name     = to_name,
        expression  = expression,
        operator    = expression.getOperator(),
        arg_names   = (left_arg_name, right_arg_name),
        in_place    = inplace,
        needs_check = expression.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
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

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name   = to_name,
        condition = "%s == 0" % res_name,
        emit      = emit
    )


def generateOperationUnaryCode(to_name, expression, emit, context):
    arg_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    _getOperationCode(
        to_name     = to_name,
        expression  = expression,
        operator    = expression.getOperator(),
        arg_names   = (arg_name,),
        in_place    = False,
        needs_check = expression.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
    )

# TODO: Have these for even more types, esp. long values, construct from the
# list of keys the helper name automatically.
_shape_to_helper_code = {
    ShapeTypeList    : "LIST",
    ShapeTypeFloat   : "FLOAT",
    ShapeTypeTuple   : "TUPLE",
    ShapeTypeUnicode : "UNICODE",
}

if python_version < 300:
    _shape_to_helper_code[ShapeTypeInt] = "INT"
    _shape_to_helper_code[ShapeTypeStr] = "STR"
else:
    _shape_to_helper_code[ShapeTypeLong] = "LONG"
    _shape_to_helper_code[ShapeTypeBytes] = "BYTES"

_iadd_helpers_set = set(
    [
        "BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE",

        "BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_INT_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_STR_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE",
        "BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE",

        "BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_INT_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_STR_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE",
        "BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE",

        "BINARY_OPERATION_ADD_LIST_LIST_INPLACE",
    ]
)

def _getOperationCode(to_name, expression, operator, arg_names, in_place,
                      needs_check, emit, context):
    # This needs to have one case per operation of Python, and there are many
    # of these, pylint: disable=too-many-branches,too-many-locals,too-many-statements

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
        left_shape = expression.getLeft().getTypeShape()
        right_shape = expression.getRight().getTypeShape()

        left_part = _shape_to_helper_code.get(left_shape, "OBJECT")
        right_part = _shape_to_helper_code.get(right_shape, "OBJECT")

        ideal_helper = "BINARY_OPERATION_ADD_%s_%s_INPLACE" % (
            left_part,
            right_part
        )

        if ideal_helper not in _iadd_helpers_set:
            onMissingHelper(ideal_helper)

            helper = "BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE"
        else:
            helper = ideal_helper
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
            needs_check   = needs_check,
            emit          = emit,
            context       = context
        )

        if ref_count:
            context.addCleanupTempName(to_name)

    else:
        with withObjectCodeTemporaryAssignment(to_name, "op_%s_res" % operator.lower(), expression, emit, context) \
          as value_name:

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
                needs_check   = needs_check,
                emit          = emit,
                context       = context
            )

            if ref_count:
                context.addCleanupTempName(value_name)
