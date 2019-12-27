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


from nuitka.containers.oset import OrderedSet

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

    emit("%s = CHECK_IF_TRUE(%s);" % (res_name, arg_name))

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


# Note: These are ordered, so we can define the order they are created in
# the code generation of specialized helpers, as this set is used for input
# there too.
specialized_add_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_ADD_OBJECT_INT",
        "BINARY_OPERATION_ADD_INT_OBJECT",
        "BINARY_OPERATION_ADD_INT_INT",
        "BINARY_OPERATION_ADD_OBJECT_STR",
        "BINARY_OPERATION_ADD_STR_OBJECT",
        "BINARY_OPERATION_ADD_STR_STR",
        "BINARY_OPERATION_ADD_OBJECT_UNICODE",
        "BINARY_OPERATION_ADD_UNICODE_OBJECT",
        "BINARY_OPERATION_ADD_UNICODE_UNICODE",
        "BINARY_OPERATION_ADD_OBJECT_FLOAT",
        "BINARY_OPERATION_ADD_FLOAT_OBJECT",
        "BINARY_OPERATION_ADD_FLOAT_FLOAT",
        "BINARY_OPERATION_ADD_OBJECT_TUPLE",
        "BINARY_OPERATION_ADD_TUPLE_OBJECT",
        "BINARY_OPERATION_ADD_TUPLE_TUPLE",
        "BINARY_OPERATION_ADD_OBJECT_LIST",
        "BINARY_OPERATION_ADD_LIST_OBJECT",
        "BINARY_OPERATION_ADD_LIST_LIST",
        "BINARY_OPERATION_ADD_OBJECT_BYTES",
        "BINARY_OPERATION_ADD_BYTES_OBJECT",
        "BINARY_OPERATION_ADD_BYTES_BYTES",
        "BINARY_OPERATION_ADD_OBJECT_LONG",
        "BINARY_OPERATION_ADD_LONG_OBJECT",
        "BINARY_OPERATION_ADD_LONG_LONG",
        # These are friends naturally, they all add with another
        "BINARY_OPERATION_ADD_FLOAT_LONG",
        "BINARY_OPERATION_ADD_LONG_FLOAT",
        "BINARY_OPERATION_ADD_FLOAT_INT",
        "BINARY_OPERATION_ADD_INT_FLOAT",
        "BINARY_OPERATION_ADD_LONG_INT",
        "BINARY_OPERATION_ADD_INT_LONG",
        # These are friends too.
        "BINARY_OPERATION_ADD_UNICODE_STR",
        "BINARY_OPERATION_ADD_STR_UNICODE",
        # Default implementation.
        "BINARY_OPERATION_ADD_OBJECT_OBJECT",
    )
)

nonspecialized_add_helpers_set = set()

specialized_sub_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_SUB_OBJECT_INT",
        "BINARY_OPERATION_SUB_INT_OBJECT",
        "BINARY_OPERATION_SUB_INT_INT",
        "BINARY_OPERATION_SUB_OBJECT_FLOAT",
        "BINARY_OPERATION_SUB_FLOAT_OBJECT",
        "BINARY_OPERATION_SUB_FLOAT_FLOAT",
        "BINARY_OPERATION_SUB_OBJECT_LONG",
        "BINARY_OPERATION_SUB_LONG_OBJECT",
        "BINARY_OPERATION_SUB_LONG_LONG",
        # These are friends naturally, they all sub with another
        "BINARY_OPERATION_SUB_FLOAT_LONG",
        "BINARY_OPERATION_SUB_LONG_FLOAT",
        "BINARY_OPERATION_SUB_FLOAT_INT",
        "BINARY_OPERATION_SUB_INT_FLOAT",
        "BINARY_OPERATION_SUB_LONG_INT",
        "BINARY_OPERATION_SUB_INT_LONG",
        # Default implementation.
        "BINARY_OPERATION_SUB_OBJECT_OBJECT",
    )
)
# These made no sense to specialize for, nothing to gain.
nonspecialized_sub_helpers_set = set(
    ("BINARY_OPERATION_SUB_OBJECT_LIST", "BINARY_OPERATION_SUB_OBJECT_TUPLE")
)

specialized_mul_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_MUL_OBJECT_INT",
        "BINARY_OPERATION_MUL_INT_OBJECT",
        "BINARY_OPERATION_MUL_INT_INT",
        "BINARY_OPERATION_MUL_OBJECT_LONG",
        "BINARY_OPERATION_MUL_CLONG_CLONG",
        "BINARY_OPERATION_MUL_INT_CLONG",
        "BINARY_OPERATION_MUL_CLONG_INT",
        "BINARY_OPERATION_MUL_LONG_OBJECT",
        "BINARY_OPERATION_MUL_LONG_LONG",
        "BINARY_OPERATION_MUL_OBJECT_STR",
        "BINARY_OPERATION_MUL_STR_OBJECT",
        "BINARY_OPERATION_MUL_INT_STR",
        "BINARY_OPERATION_MUL_STR_INT",
        "BINARY_OPERATION_MUL_LONG_STR",
        "BINARY_OPERATION_MUL_STR_LONG",
        # Should not occur.
        # "BINARY_OPERATION_MUL_STR_STR",
        "BINARY_OPERATION_MUL_OBJECT_UNICODE",
        "BINARY_OPERATION_MUL_UNICODE_OBJECT",
        "BINARY_OPERATION_MUL_INT_UNICODE",
        "BINARY_OPERATION_MUL_UNICODE_INT",
        "BINARY_OPERATION_MUL_LONG_UNICODE",
        "BINARY_OPERATION_MUL_UNICODE_LONG",
        # Should not occur.
        # "BINARY_OPERATION_MUL_UNICODE_UNICODE",
        "BINARY_OPERATION_MUL_OBJECT_FLOAT",
        "BINARY_OPERATION_MUL_FLOAT_OBJECT",
        "BINARY_OPERATION_MUL_FLOAT_FLOAT",
        "BINARY_OPERATION_MUL_OBJECT_TUPLE",
        "BINARY_OPERATION_MUL_TUPLE_OBJECT",
        "BINARY_OPERATION_MUL_INT_TUPLE",
        "BINARY_OPERATION_MUL_TUPLE_INT",
        "BINARY_OPERATION_MUL_LONG_TUPLE",
        "BINARY_OPERATION_MUL_TUPLE_LONG",
        # Should not occur.
        # "BINARY_OPERATION_MUL_TUPLE_TUPLE",
        "BINARY_OPERATION_MUL_OBJECT_LIST",
        "BINARY_OPERATION_MUL_LIST_OBJECT",
        "BINARY_OPERATION_MUL_INT_LIST",
        "BINARY_OPERATION_MUL_LIST_INT",
        "BINARY_OPERATION_MUL_LONG_LIST",
        "BINARY_OPERATION_MUL_LIST_LONG",
        # Should not occur.
        # "BINARY_OPERATION_MUL_LIST_LIST",
        "BINARY_OPERATION_MUL_OBJECT_BYTES",
        "BINARY_OPERATION_MUL_BYTES_OBJECT",
        "BINARY_OPERATION_MUL_LONG_BYTES",
        "BINARY_OPERATION_MUL_BYTES_LONG",
        # Should not occur.
        # "BINARY_OPERATION_MUL_BYTES_BYTES",
        # These are friends naturally, they all mul with another
        "BINARY_OPERATION_MUL_FLOAT_LONG",
        "BINARY_OPERATION_MUL_LONG_FLOAT",
        "BINARY_OPERATION_MUL_FLOAT_INT",
        "BINARY_OPERATION_MUL_INT_FLOAT",
        "BINARY_OPERATION_MUL_LONG_INT",
        "BINARY_OPERATION_MUL_INT_LONG",
        # Default implementation.
        "BINARY_OPERATION_MUL_OBJECT_OBJECT",
    )
)

nonspecialized_mul_helpers_set = set()

specialized_truediv_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_TRUEDIV_OBJECT_INT",
        "BINARY_OPERATION_TRUEDIV_INT_OBJECT",
        "BINARY_OPERATION_TRUEDIV_INT_INT",
        "BINARY_OPERATION_TRUEDIV_OBJECT_LONG",
        "BINARY_OPERATION_TRUEDIV_LONG_OBJECT",
        "BINARY_OPERATION_TRUEDIV_LONG_LONG",
        "BINARY_OPERATION_TRUEDIV_OBJECT_FLOAT",
        "BINARY_OPERATION_TRUEDIV_FLOAT_OBJECT",
        "BINARY_OPERATION_TRUEDIV_FLOAT_FLOAT",
        # These are friends naturally, they div mul with another
        "BINARY_OPERATION_TRUEDIV_FLOAT_LONG",
        "BINARY_OPERATION_TRUEDIV_LONG_FLOAT",
        "BINARY_OPERATION_TRUEDIV_FLOAT_INT",
        "BINARY_OPERATION_TRUEDIV_INT_FLOAT",
        "BINARY_OPERATION_TRUEDIV_LONG_INT",
        "BINARY_OPERATION_TRUEDIV_INT_LONG",
        # Default implementation.
        "BINARY_OPERATION_TRUEDIV_OBJECT_OBJECT",
    )
)

nonspecialized_truediv_helpers_set = set(
    (
        # e.g. pathlib defines objects that do this.
        "BINARY_OPERATION_TRUEDIV_OBJECT_UNICODE",
        "BINARY_OPERATION_TRUEDIV_UNICODE_OBJECT",
    )
)

specialized_olddiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "OLDDIV") for helper in specialized_truediv_helpers_set
)

nonspecialized_olddiv_helpers_set = set()


specialized_floordiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "FLOORDIV") for helper in specialized_truediv_helpers_set
)

nonspecialized_floordiv_helpers_set = set()

_iadd_helpers_set = OrderedSet(
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

specialized_mod_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_MOD_OBJECT_INT",
        "BINARY_OPERATION_MOD_INT_OBJECT",
        "BINARY_OPERATION_MOD_INT_INT",
        "BINARY_OPERATION_MOD_OBJECT_LONG",
        "BINARY_OPERATION_MOD_LONG_OBJECT",
        "BINARY_OPERATION_MOD_LONG_LONG",
        "BINARY_OPERATION_MOD_OBJECT_FLOAT",
        "BINARY_OPERATION_MOD_FLOAT_OBJECT",
        "BINARY_OPERATION_MOD_FLOAT_FLOAT",
        # These are friends naturally, they mod with another
        "BINARY_OPERATION_MOD_FLOAT_LONG",
        "BINARY_OPERATION_MOD_LONG_FLOAT",
        "BINARY_OPERATION_MOD_FLOAT_INT",
        "BINARY_OPERATION_MOD_INT_FLOAT",
        "BINARY_OPERATION_MOD_LONG_INT",
        "BINARY_OPERATION_MOD_INT_LONG",
        # String interpolation with STR:
        "BINARY_OPERATION_MOD_STR_INT",
        "BINARY_OPERATION_MOD_STR_LONG",
        "BINARY_OPERATION_MOD_STR_FLOAT",
        "BINARY_OPERATION_MOD_STR_STR",
        "BINARY_OPERATION_MOD_STR_BYTES",
        "BINARY_OPERATION_MOD_STR_UNICODE",
        "BINARY_OPERATION_MOD_STR_TUPLE",
        "BINARY_OPERATION_MOD_STR_LIST",
        "BINARY_OPERATION_MOD_STR_DICT",
        "BINARY_OPERATION_MOD_STR_OBJECT",
        # String formatting with UNICODE:
        "BINARY_OPERATION_MOD_UNICODE_INT",
        "BINARY_OPERATION_MOD_UNICODE_LONG",
        "BINARY_OPERATION_MOD_UNICODE_FLOAT",
        "BINARY_OPERATION_MOD_UNICODE_STR",
        "BINARY_OPERATION_MOD_UNICODE_BYTES",
        "BINARY_OPERATION_MOD_UNICODE_UNICODE",
        "BINARY_OPERATION_MOD_UNICODE_TUPLE",
        "BINARY_OPERATION_MOD_UNICODE_LIST",
        "BINARY_OPERATION_MOD_UNICODE_DICT",
        "BINARY_OPERATION_MOD_UNICODE_OBJECT",
        # String formatting with BYTES:
        "BINARY_OPERATION_MOD_BYTES_LONG",
        "BINARY_OPERATION_MOD_BYTES_FLOAT",
        "BINARY_OPERATION_MOD_BYTES_BYTES",
        "BINARY_OPERATION_MOD_BYTES_UNICODE",
        "BINARY_OPERATION_MOD_BYTES_TUPLE",
        "BINARY_OPERATION_MOD_BYTES_LIST",
        "BINARY_OPERATION_MOD_BYTES_DICT",
        "BINARY_OPERATION_MOD_BYTES_OBJECT",
        # String formatting with OBJECT:
        "BINARY_OPERATION_MOD_OBJECT_STR",
        "BINARY_OPERATION_MOD_OBJECT_BYTES",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE",
        "BINARY_OPERATION_MOD_OBJECT_TUPLE",
        "BINARY_OPERATION_MOD_OBJECT_LIST",
        "BINARY_OPERATION_MOD_OBJECT_DICT",
        # Default implementation.
        "BINARY_OPERATION_MOD_OBJECT_OBJECT",
    )
)

nonspecialized_mod_helpers_set = set(
    ("BINARY_OPERATION_MOD_TUPLE_OBJECT", "BINARY_OPERATION_MOD_LIST_OBJECT")
)

specialized_bitor_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_BITOR_OBJECT_INT",
        "BINARY_OPERATION_BITOR_INT_OBJECT",
        "BINARY_OPERATION_BITOR_INT_INT",
        "BINARY_OPERATION_BITOR_OBJECT_LONG",
        "BINARY_OPERATION_BITOR_LONG_OBJECT",
        "BINARY_OPERATION_BITOR_LONG_LONG",
        "BINARY_OPERATION_BITOR_LONG_INT",
        "BINARY_OPERATION_BITOR_INT_LONG",
        # Set containers can do this
        "BINARY_OPERATION_BITOR_OBJECT_SET",
        "BINARY_OPERATION_BITOR_SET_OBJECT",
        "BINARY_OPERATION_BITOR_SET_SET",
        "BINARY_OPERATION_BITOR_OBJECT_LIST",
        "BINARY_OPERATION_BITOR_LIST_OBJECT",
        "BINARY_OPERATION_BITOR_OBJECT_LIST",
        "BINARY_OPERATION_BITOR_LIST_OBJECT",
        "BINARY_OPERATION_BITOR_OBJECT_TUPLE",
        "BINARY_OPERATION_BITOR_TUPLE_OBJECT",
        # Default implementation.
        "BINARY_OPERATION_BITOR_OBJECT_OBJECT",
    )
)
nonspecialized_bitor_helpers_set = set()

specialized_bitand_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITAND_") for helper in specialized_bitor_helpers_set
)
nonspecialized_bitand_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITAND_") for helper in nonspecialized_bitor_helpers_set
)
specialized_bitxor_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITXOR_") for helper in specialized_bitor_helpers_set
)
nonspecialized_bitxor_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITXOR_") for helper in nonspecialized_bitor_helpers_set
)
specialized_lshift_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_LSHIFT_")
    for helper in specialized_bitor_helpers_set
    if "_SET" not in helper
    if "_TUPLE" not in helper
)
nonspecialized_lshift_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_LSHIFT_") for helper in nonspecialized_bitor_helpers_set
)
specialized_rshift_helpers_set = OrderedSet(
    helper.replace("_LSHIFT_", "_RSHIFT_") for helper in specialized_lshift_helpers_set
)
nonspecialized_rshift_helpers_set = OrderedSet(
    helper.replace("_LSHIFT_", "_RSHIFT_")
    for helper in nonspecialized_lshift_helpers_set
)
specialized_pow_helpers_set = OrderedSet(
    (
        "BINARY_OPERATION_POW_INT_INT",
        "BINARY_OPERATION_POW_OBJECT_INT",
        "BINARY_OPERATION_POW_INT_OBJECT",
        "BINARY_OPERATION_POW_OBJECT_LONG",
        "BINARY_OPERATION_POW_LONG_OBJECT",
        "BINARY_OPERATION_POW_LONG_LONG",
        "BINARY_OPERATION_POW_LONG_INT",
        "BINARY_OPERATION_POW_INT_LONG",
        "BINARY_OPERATION_POW_OBJECT_FLOAT",
        "BINARY_OPERATION_POW_FLOAT_OBJECT",
        "BINARY_OPERATION_POW_FLOAT_FLOAT",
        # Default implementation.
        "BINARY_OPERATION_POW_OBJECT_OBJECT",
    )
)
nonspecialized_pow_helpers_set = set()
specialized_matmult_helpers_set = OrderedSet(
    (
        # Default implementation.
        "BINARY_OPERATION_MATMULT_LONG_OBJECT",
        "BINARY_OPERATION_MATMULT_OBJECT_LONG",
        "BINARY_OPERATION_MATMULT_OBJECT_OBJECT",
    )
)
nonspecialized_matmult_helpers_set = set()


def _getBinaryOperationCode(
    to_name, expression, operator, arg_names, in_place, emit, context
):
    # This needs to have one case per operation of Python, and there are many
    # of these, pylint: disable=too-many-branches,too-many-statements
    left = expression.getLeft()

    prefix_args = ()
    ref_count = 1

    needs_check = expression.mayRaiseExceptionOperation()

    if operator == "IPow" and in_place:
        helper = "POWER_OPERATION_INPLACE"
    elif operator == "IPow":
        helper = "POWER_OPERATION2"
    elif operator == "Add":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_ADD",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_add_helpers_set,
            nonhelpers=nonspecialized_add_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "Sub":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_SUB",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_sub_helpers_set,
            nonhelpers=nonspecialized_sub_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "IAdd" and in_place:
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_ADD",
            suffix="_INPLACE",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=_iadd_helpers_set,
            # TODO: Add this once generated.
            nonhelpers=(),
            source_ref=False,
        )
    elif operator == "IMult" and in_place:
        helper = "BINARY_OPERATION_MUL_INPLACE"
    elif operator == "Div":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_OLDDIV",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_olddiv_helpers_set,
            nonhelpers=nonspecialized_olddiv_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "FloorDiv":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_FLOORDIV",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_floordiv_helpers_set,
            nonhelpers=nonspecialized_floordiv_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "TrueDiv":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_TRUEDIV",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_truediv_helpers_set,
            nonhelpers=nonspecialized_truediv_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "Mult":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_MUL",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_mul_helpers_set,
            nonhelpers=nonspecialized_mul_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "Mod":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_MOD",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_mod_helpers_set,
            nonhelpers=nonspecialized_mod_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "LShift":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_LSHIFT",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_lshift_helpers_set,
            nonhelpers=nonspecialized_lshift_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "RShift":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_RSHIFT",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_rshift_helpers_set,
            nonhelpers=nonspecialized_rshift_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "BitOr":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_BITOR",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_bitor_helpers_set,
            nonhelpers=nonspecialized_bitor_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "BitAnd":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_BITAND",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_bitand_helpers_set,
            nonhelpers=nonspecialized_bitand_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "BitXor":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_BITXOR",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_bitxor_helpers_set,
            nonhelpers=nonspecialized_bitxor_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "Pow":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_POW",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_pow_helpers_set,
            nonhelpers=nonspecialized_pow_helpers_set,
            source_ref=expression.source_ref,
        )
    elif operator == "MatMult":
        helper = pickCodeHelper(
            prefix="BINARY_OPERATION_MATMULT",
            suffix="",
            left_shape=left.getTypeShape(),
            right_shape=expression.getRight().getTypeShape(),
            helpers=specialized_matmult_helpers_set,
            nonhelpers=nonspecialized_matmult_helpers_set,
            source_ref=expression.source_ref,
        )
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
                "%s = BINARY_OPERATION_INPLACE(%s, &%s, %s);"
                % (
                    res_name,
                    OperatorCodes.binary_operator_codes[operator],
                    arg_names[0],
                    arg_names[1],
                )
            )
        else:
            emit("%s = %s(&%s, %s);" % (res_name, helper, arg_names[0], arg_names[1]))

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
                "%s = %s(%s);"
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
            "%s = %s(%s);"
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
