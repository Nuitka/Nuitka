#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Shared definitions of what binary operation helpers are available.

These are functions to work with helper names, as well as sets of functions to
generate specialized code variants for.

Note: These are ordered, so we can define the order they are created in the
code generation of specialized helpers, as this set is used for input there
too.

"""

from nuitka.containers.OrderedSets import OrderedSet, buildOrderedSet

# spell-checker: ignore clong


def parseTypesFromHelper(helper_name):
    """Function to parse helper names."""

    if helper_name.startswith("INPLACE_"):
        target_code = None
        left_code = helper_name.split("_")[3]
        right_code = helper_name.split("_")[4]
    else:
        target_code = helper_name.split("_")[3]
        left_code = helper_name.split("_")[4]
        right_code = helper_name.split("_")[5]

    return target_code, left_code, right_code


def deriveInplaceFromBinaryOperations(operations_set):
    """Derive the in-place operations from the binary ones.

    These can largely be the same, or should be, and keeping them inline is easier when
    generating them. Obviously the templates might both need changes to optimize equally
    well for all variants.
    """

    if not operations_set:
        return None

    operation = next(iter(operations_set)).split("_")[2]

    return OrderedSet(
        helper_name.replace(operation + "_OBJECT", operation).replace(
            "BINARY_", "INPLACE_"
        )
        for helper_name in operations_set
        if parseTypesFromHelper(helper_name)[0] == "OBJECT"
    )


def _makeTypeSemiOps(op_code, type_name, in_place=False):
    if in_place:
        yield "INPLACE_OPERATION_%s_%s_OBJECT" % (op_code, type_name)
    else:
        yield "BINARY_OPERATION_%s_OBJECT_OBJECT_%s" % (op_code, type_name)
        yield "BINARY_OPERATION_%s_OBJECT_%s_OBJECT" % (op_code, type_name)


def _makeTypeOps(op_code, type_name, include_nbool, in_place=False):
    if in_place:
        yield "INPLACE_OPERATION_%s_%s_%s" % (op_code, type_name, type_name)
        yield "INPLACE_OPERATION_%s_OBJECT_%s" % (op_code, type_name)
        yield "INPLACE_OPERATION_%s_%s_OBJECT" % (op_code, type_name)
    else:
        yield "BINARY_OPERATION_%s_OBJECT_%s_%s" % (op_code, type_name, type_name)
        yield "BINARY_OPERATION_%s_OBJECT_OBJECT_%s" % (op_code, type_name)
        yield "BINARY_OPERATION_%s_OBJECT_%s_OBJECT" % (op_code, type_name)

    if include_nbool and not in_place:
        for helper in _makeTypeOpsNbool(op_code, type_name):
            yield helper


def _makeTypeOpsNbool(op_code, type_name):
    yield "BINARY_OPERATION_%s_NBOOL_%s_%s" % (op_code, type_name, type_name)
    yield "BINARY_OPERATION_%s_NBOOL_OBJECT_%s" % (op_code, type_name)
    yield "BINARY_OPERATION_%s_NBOOL_%s_OBJECT" % (op_code, type_name)


def _isCommutativeOperation(op_code):
    return op_code in ("ADD", "MULT", "BITOR", "BITAND", "BITXOR")


def _isCommutativeType(type_name):
    return type_name in ("INT", "LONG", "FLOAT", "CLONG", "DIGIT", "CFLOAT")


_type_order = (
    "CLONG",
    "INT",
    "DIGIT",
    "CFLOAT",
    "LONG",
    "FLOAT",
    "STR",
    "UNICODE",
    "BYTES",
    "TUPLE",
    "LIST",
)

_no_inplace_target_types = ("CLONG", "DIGIT", "CFLOAT")


def _makeFriendOps(op_code, include_nbool, in_place, *type_names):
    assert len(type_names) == len(set(type_names)), type_names

    type_names = tuple(
        sorted(type_names, key=lambda type_name: -_type_order.index(type_name))
    )

    for type_name1 in type_names:

        for type_name2 in type_names[type_names.index(type_name1) + 1 :]:
            # These should be used with reversed arguments, and only have the
            # dominant type as the first argument.
            arg_swap = (
                _isCommutativeOperation(op_code)
                and not in_place
                and _isCommutativeType(type_name1)
                and _isCommutativeType(type_name2)
            )

            if in_place:
                if type_name1 not in _no_inplace_target_types:
                    yield "INPLACE_OPERATION_%s_%s_%s" % (
                        op_code,
                        type_name1,
                        type_name2,
                    )
            else:
                yield "BINARY_OPERATION_%s_OBJECT_%s_%s" % (
                    op_code,
                    type_name1,
                    type_name2,
                )

            if not arg_swap:
                if in_place:
                    if type_name2 not in _no_inplace_target_types:
                        yield "INPLACE_OPERATION_%s_%s_%s" % (
                            op_code,
                            type_name2,
                            type_name1,
                        )
                else:
                    yield "BINARY_OPERATION_%s_OBJECT_%s_%s" % (
                        op_code,
                        type_name2,
                        type_name1,
                    )

            if include_nbool and not in_place:
                yield "BINARY_OPERATION_%s_NBOOL_%s_%s" % (
                    op_code,
                    type_name1,
                    type_name2,
                )

                if not arg_swap:
                    yield "BINARY_OPERATION_%s_NBOOL_%s_%s" % (
                        op_code,
                        type_name2,
                        type_name1,
                    )


def _makeDefaultOps(op_code, include_nbool, in_place=False):

    if in_place:
        yield "INPLACE_OPERATION_%s_OBJECT_OBJECT" % op_code
    else:
        yield "BINARY_OPERATION_%s_OBJECT_OBJECT_OBJECT" % op_code

    if include_nbool and not in_place:
        yield "BINARY_OPERATION_%s_NBOOL_OBJECT_OBJECT" % op_code


def _makeNonContainerMathOps(op_code):
    for type_name in "TUPLE", "LIST", "DICT", "SET", "FROZENSET":
        if "BIT" in op_code and type_name == "SET":
            continue
        if "SUB" in op_code and type_name == "SET":
            continue

        for value in _makeTypeOps(op_code, type_name, include_nbool=True):
            yield value


def _makeNumberOps(op_code, include_nbool, in_place):
    return buildOrderedSet(
        _makeTypeOps(op_code, "INT", include_nbool=include_nbool, in_place=in_place),
        _makeTypeOps(op_code, "LONG", include_nbool=include_nbool, in_place=in_place),
        _makeTypeOps(op_code, "FLOAT", include_nbool=include_nbool, in_place=in_place),
        # These are friends naturally, they all add with another.
        _makeFriendOps(op_code, include_nbool, in_place, "INT", "LONG", "FLOAT"),
        # Special operations, currently used with constant values mostly.
        _makeFriendOps(op_code, include_nbool, in_place, "INT", "CLONG"),
        _makeFriendOps(op_code, include_nbool, in_place, "LONG", "DIGIT")
        if op_code in ("ADD", "SUB")  # TODO: Add more
        else (),
        _makeFriendOps(op_code, include_nbool, in_place, "FLOAT", "CFLOAT"),
    )


def _makeAddOps(in_place):
    return buildOrderedSet(
        _makeNumberOps("ADD", include_nbool=True, in_place=in_place),
        _makeTypeOps("ADD", "STR", include_nbool=False, in_place=in_place),
        _makeTypeOps("ADD", "UNICODE", include_nbool=False, in_place=in_place),
        _makeTypeOps("ADD", "BYTES", include_nbool=False, in_place=in_place),
        _makeTypeOps("ADD", "TUPLE", include_nbool=False, in_place=in_place),
        _makeTypeOps("ADD", "LIST", include_nbool=True, in_place=in_place),
        # These are friends too.
        _makeFriendOps("ADD", True, in_place, "STR", "UNICODE"),
        # Default implementation.
        _makeDefaultOps("ADD", include_nbool=True, in_place=in_place),
    )


specialized_add_helpers_set = _makeAddOps(in_place=False)

nonspecialized_add_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("ADD", "STR"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "UNICODE"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "BYTES"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "TUPLE"),  # Not really likely to be used.
)


def makeSubOps(in_place):
    return buildOrderedSet(
        _makeNumberOps("SUB", include_nbool=False, in_place=in_place),
        _makeDefaultOps("SUB", include_nbool=False, in_place=in_place),
    )


specialized_sub_helpers_set = makeSubOps(in_place=False)

# These made no sense to specialize for, nothing to gain.
nonspecialized_sub_helpers_set = buildOrderedSet(
    _makeTypeOps("SUB", "STR", include_nbool=True),
    _makeTypeOps("SUB", "UNICODE", include_nbool=True),
    _makeTypeOps("SUB", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("SUB"),
)


def _makeMultOps(in_place):
    return buildOrderedSet(
        _makeNumberOps("MULT", include_nbool=True, in_place=in_place),
        _makeFriendOps("MULT", False, in_place, "INT", "STR"),
        _makeFriendOps("MULT", False, in_place, "INT", "UNICODE"),
        _makeFriendOps("MULT", False, in_place, "INT", "TUPLE"),
        _makeFriendOps("MULT", False, in_place, "INT", "LIST"),
        _makeFriendOps("MULT", False, in_place, "LONG", "UNICODE"),
        _makeFriendOps("MULT", False, in_place, "LONG", "BYTES"),
        _makeFriendOps("MULT", False, in_place, "LONG", "TUPLE"),
        _makeFriendOps("MULT", False, in_place, "LONG", "LIST"),
        _makeTypeSemiOps("MULT", "STR", in_place=in_place),
        _makeTypeSemiOps("MULT", "UNICODE", in_place=in_place),
        _makeTypeSemiOps("MULT", "BYTES", in_place=in_place),
        _makeTypeSemiOps("MULT", "TUPLE", in_place=in_place),
        _makeTypeSemiOps("MULT", "LIST", in_place=in_place),
        # These are friends naturally, they all mul with another
        _makeDefaultOps("MULT", include_nbool=True, in_place=in_place),
    )


specialized_mult_helpers_set = _makeMultOps(in_place=False)
# Using booleans, because multiplication might be used to test for zero result.

nonspecialized_mult_helpers_set = None


def _makeDivOps(op_code, in_place):
    return buildOrderedSet(
        _makeNumberOps(op_code, include_nbool=False, in_place=in_place),
        _makeDefaultOps(op_code, include_nbool=False, in_place=in_place),
    )


specialized_truediv_helpers_set = _makeDivOps("TRUEDIV", in_place=False)

nonspecialized_truediv_helpers_set = buildOrderedSet(
    _makeTypeOps("TRUEDIV", "UNICODE", include_nbool=True),
    _makeTypeOps("TRUEDIV", "STR", include_nbool=True),
    _makeTypeOps("TRUEDIV", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("TRUEDIV"),
)

specialized_olddiv_helpers_set = _makeDivOps("OLDDIV", in_place=False)

nonspecialized_olddiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "OLDDIV") for helper in nonspecialized_truediv_helpers_set
)

specialized_floordiv_helpers_set = _makeDivOps("FLOORDIV", in_place=False)

nonspecialized_floordiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "FLOORDIV")
    for helper in nonspecialized_truediv_helpers_set
)


def _makeModOps(in_place):
    def _makeFormatOps(str_type_name):
        for formatted_type_name in (
            "INT",
            "LONG",
            "FLOAT",
            "STR",
            "BYTES",
            "UNICODE",
            "TUPLE",
            "LIST",
            "DICT",
            "OBJECT",
        ):

            if str_type_name == "STR" and formatted_type_name == "BYTES":
                continue
            if str_type_name == "BYTES" and formatted_type_name in ("STR", "INT"):
                continue

            if in_place:
                yield "INPLACE_OPERATION_MOD_%s_%s" % (
                    str_type_name,
                    formatted_type_name,
                )
            else:
                yield "BINARY_OPERATION_MOD_OBJECT_%s_%s" % (
                    str_type_name,
                    formatted_type_name,
                )

    return buildOrderedSet(
        _makeNumberOps("MOD", include_nbool=True, in_place=in_place),
        # These are friends naturally, they mod with another
        _makeFriendOps("MOD", True, in_place, "INT", "LONG", "FLOAT"),
        # String interpolation:
        _makeFormatOps(str_type_name="STR"),
        _makeFormatOps(str_type_name="UNICODE"),
        _makeFormatOps(str_type_name="BYTES"),
        _makeDefaultOps("MOD", include_nbool=True, in_place=in_place),
    )


specialized_mod_helpers_set = _makeModOps(in_place=False)

nonspecialized_mod_helpers_set = buildOrderedSet(
    (
        "BINARY_OPERATION_MOD_OBJECT_TUPLE_OBJECT",
        "BINARY_OPERATION_MOD_OBJECT_LIST_OBJECT",
        # String formatting with STR:
        "BINARY_OPERATION_MOD_NBOOL_STR_INT",
        "BINARY_OPERATION_MOD_NBOOL_STR_LONG",
        "BINARY_OPERATION_MOD_NBOOL_STR_FLOAT",
        "BINARY_OPERATION_MOD_NBOOL_STR_STR",
        "BINARY_OPERATION_MOD_NBOOL_STR_UNICODE",
        "BINARY_OPERATION_MOD_NBOOL_STR_TUPLE",
        "BINARY_OPERATION_MOD_NBOOL_STR_LIST",
        "BINARY_OPERATION_MOD_NBOOL_STR_DICT",
        "BINARY_OPERATION_MOD_NBOOL_STR_OBJECT",
        # String formatting with UNICODE:
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_INT",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_LONG",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_FLOAT",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_STR",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_BYTES",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_UNICODE",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_TUPLE",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_LIST",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_DICT",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_OBJECT",
    )
)

specialized_imod_helpers_set = _makeModOps(in_place=True)

nonspecialized_imod_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_mod_helpers_set
)


def _makeBitOps(op_name, in_place):
    return buildOrderedSet(
        _makeTypeOps(op_name, "LONG", include_nbool=True, in_place=in_place),
        _makeTypeOps(op_name, "INT", include_nbool=True, in_place=in_place),
        _makeFriendOps(op_name, True, in_place, "INT", "CLONG"),
        _makeFriendOps(op_name, True, in_place, "INT", "LONG"),
        _makeTypeOps(op_name, "SET", include_nbool=False, in_place=in_place),
        _makeDefaultOps(op_name, include_nbool=True, in_place=in_place),
    )


specialized_bitor_helpers_set = _makeBitOps("BITOR", in_place=False)

nonspecialized_bitor_helpers_set = buildOrderedSet(
    _makeTypeOps("BITOR", "FLOAT", include_nbool=True),
    _makeNonContainerMathOps("BITOR"),
    _makeTypeOps("BITOR", "UNICODE", include_nbool=True),
    _makeTypeOps("BITOR", "STR", include_nbool=True),
    _makeTypeOps("BITOR", "BYTES", include_nbool=True),
)

specialized_bitand_helpers_set = _makeBitOps("BITAND", in_place=False)
nonspecialized_bitand_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITAND_") for helper in nonspecialized_bitor_helpers_set
)
specialized_bitxor_helpers_set = _makeBitOps("BITXOR", in_place=False)

nonspecialized_bitxor_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITXOR_") for helper in nonspecialized_bitor_helpers_set
)


def _makeShiftOps(op_name, in_place):
    return buildOrderedSet(
        _makeTypeOps(op_name, "LONG", include_nbool=True, in_place=in_place),
        _makeTypeOps(op_name, "INT", include_nbool=True, in_place=in_place),
        _makeFriendOps(op_name, True, in_place, "INT", "LONG"),
        _makeDefaultOps(op_name, include_nbool=True, in_place=in_place),
    )


specialized_lshift_helpers_set = _makeShiftOps("LSHIFT", in_place=False)

nonspecialized_lshift_helpers_set = buildOrderedSet(
    _makeTypeOps("LSHIFT", "FLOAT", include_nbool=True),
    _makeNonContainerMathOps("LSHIFT"),
)
specialized_rshift_helpers_set = _makeShiftOps("RSHIFT", in_place=False)

nonspecialized_rshift_helpers_set = OrderedSet(
    helper.replace("_LSHIFT_", "_RSHIFT_")
    for helper in nonspecialized_lshift_helpers_set
)


specialized_pow_helpers_set = buildOrderedSet(
    _makeTypeOps("POW", "FLOAT", include_nbool=False),
    _makeTypeOps("POW", "LONG", include_nbool=False),
    _makeTypeOps("POW", "INT", include_nbool=False),
    _makeFriendOps("POW", False, False, "INT", "LONG", "FLOAT"),
    _makeDefaultOps("POW", include_nbool=True),
    (
        # Float is used by other types for ** operations.
        # TODO: Enable these later.
        #        "BINARY_OPERATION_POW_OBJECT_LONG_FLOAT",
        #        "BINARY_OPERATION_POW_NBOOL_LONG_FLOAT",
    ),
)
nonspecialized_pow_helpers_set = buildOrderedSet(
    _makeTypeOps("POW", "STR", include_nbool=True),
    _makeTypeOps("POW", "UNICODE", include_nbool=True),
    _makeTypeOps("POW", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("POW"),
)


specialized_divmod_helpers_set = _makeDivOps("DIVMOD", in_place=False)

nonspecialized_divmod_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("DIVMOD", "INT"),
    _makeTypeOpsNbool("DIVMOD", "LONG"),
    _makeTypeOpsNbool("DIVMOD", "FLOAT"),
    _makeTypeOps("DIVMOD", "UNICODE", include_nbool=True),
    _makeTypeOps("DIVMOD", "STR", include_nbool=True),
    _makeTypeOps("DIVMOD", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("DIVMOD"),
)

specialized_matmult_helpers_set = buildOrderedSet(
    _makeTypeOps("MATMULT", "LONG", include_nbool=False),
    _makeTypeOps("MATMULT", "FLOAT", include_nbool=False),
    _makeDefaultOps("MATMULT", include_nbool=False),
)

nonspecialized_matmult_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("MATMULT", "LONG"),
    _makeTypeOpsNbool("MATMULT", "FLOAT"),
    _makeTypeOps("MATMULT", "TUPLE", include_nbool=True),
    _makeTypeOps("MATMULT", "LIST", include_nbool=True),
    _makeTypeOps("MATMULT", "DICT", include_nbool=True),
    _makeTypeOps("MATMULT", "BYTES", include_nbool=True),
    _makeTypeOps("MATMULT", "UNICODE", include_nbool=True),
)

specialized_iadd_helpers_set = buildOrderedSet(
    _makeAddOps(in_place=True),
    ("INPLACE_OPERATION_ADD_LIST_TUPLE",),
)
nonspecialized_iadd_helpers_set = buildOrderedSet(
    deriveInplaceFromBinaryOperations(nonspecialized_add_helpers_set),
    (
        "INPLACE_OPERATION_ADD_LIST_STR",
        "INPLACE_OPERATION_ADD_LIST_BYTES",
        "INPLACE_OPERATION_ADD_LIST_BYTEARRAY",
        "INPLACE_OPERATION_ADD_LIST_UNICODE",
        "INPLACE_OPERATION_ADD_LIST_SET",  # semi useful only
        "INPLACE_OPERATION_ADD_LIST_FROZENSET",
        "INPLACE_OPERATION_ADD_LIST_DICT",
    ),
)

specialized_isub_helpers_set = makeSubOps(in_place=True)

nonspecialized_isub_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_sub_helpers_set
)

specialized_imult_helpers_set = _makeMultOps(in_place=True)

nonspecialized_imult_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_mult_helpers_set
)

specialized_ibitor_helpers_set = _makeBitOps("BITOR", in_place=True)

nonspecialized_ibitor_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_bitor_helpers_set
)

specialized_ibitand_helpers_set = _makeBitOps("BITAND", in_place=True)

nonspecialized_ibitand_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_bitand_helpers_set
)

specialized_ibitxor_helpers_set = _makeBitOps("BITXOR", in_place=True)

nonspecialized_ibitxor_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_bitxor_helpers_set
)

specialized_ilshift_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_lshift_helpers_set
)

nonspecialized_ilshift_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_lshift_helpers_set
)

specialized_irshift_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_rshift_helpers_set
)

nonspecialized_irshift_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_rshift_helpers_set
)

specialized_ifloordiv_helpers_set = _makeDivOps("FLOORDIV", in_place=True)

nonspecialized_ifloordiv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_floordiv_helpers_set
)

specialized_itruediv_helpers_set = _makeDivOps("TRUEDIV", in_place=True)

nonspecialized_itruediv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_truediv_helpers_set
)

specialized_iolddiv_helpers_set = _makeDivOps("OLDDIV", in_place=True)

nonspecialized_iolddiv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_olddiv_helpers_set
)

specialized_ipow_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_pow_helpers_set
)

nonspecialized_ipow_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_pow_helpers_set
)

specialized_imatmult_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_matmult_helpers_set
)

nonspecialized_imatmult_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_matmult_helpers_set
)


def getSpecializedBinaryOperations(operator):
    return globals()["specialized_%s_helpers_set" % operator.lower()]


def getNonSpecializedBinaryOperations(operator):
    return globals()["nonspecialized_%s_helpers_set" % operator.lower()]


def getCodeNameForBinaryOperation(operator):
    return operator[1:].upper() if operator[0] == "I" else operator.upper()
