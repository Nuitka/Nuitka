#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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


def _makeTypeSemiOps(op_code, type_name, result_types):
    for result_type in result_types or (None,):
        if result_type is None:
            yield "INPLACE_OPERATION_%s_%s_OBJECT" % (op_code, type_name)
        else:
            yield "BINARY_OPERATION_%s_%s_OBJECT_%s" % (op_code, result_type, type_name)
            yield "BINARY_OPERATION_%s_%s_%s_OBJECT" % (op_code, result_type, type_name)


def _makeTypeOps(op_code, type_name, result_types):
    if result_types is None:
        # Inplace has no result type.
        yield "INPLACE_OPERATION_%s_%s_%s" % (op_code, type_name, type_name)
        yield "INPLACE_OPERATION_%s_OBJECT_%s" % (op_code, type_name)
        yield "INPLACE_OPERATION_%s_%s_OBJECT" % (op_code, type_name)
    else:
        for result_type in result_types:
            yield "BINARY_OPERATION_%s_%s_%s_%s" % (
                op_code,
                result_type,
                type_name,
                type_name,
            )
            yield "BINARY_OPERATION_%s_%s_OBJECT_%s" % (op_code, result_type, type_name)
            yield "BINARY_OPERATION_%s_%s_%s_OBJECT" % (op_code, result_type, type_name)


def _makeTypeOpsNbool(op_code, type_name):
    return _makeTypeOps(op_code=op_code, type_name=type_name, result_types=("NBOOL",))


def isCommutativeOperation(op_code):
    return op_code in ("ADD", "MULT", "BITOR", "BITAND", "BITXOR")


def isCommutativeType(type_name):
    return type_name in ("INT", "LONG", "FLOAT", "CLONG", "DIGIT", "CFLOAT", "NILONG")


_type_order = (
    "CLONG",
    "INT",
    "DIGIT",
    "NILONG",
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


def _makeFriendOps(op_code, friend_type_names, result_types):
    friend_type_names = tuple(
        sorted(friend_type_names, key=lambda type_name: -_type_order.index(type_name))
    )

    for type_name1 in friend_type_names:
        for type_name2 in friend_type_names[friend_type_names.index(type_name1) + 1 :]:
            for result_type in result_types or (None,):
                # These should be used with reversed arguments, and only have the
                # dominant type as the first argument.
                arg_swap = (
                    isCommutativeOperation(op_code)
                    and result_type is not None
                    and isCommutativeType(type_name1)
                    and isCommutativeType(type_name2)
                )

                if result_type is None:
                    if type_name1 not in _no_inplace_target_types:
                        yield "INPLACE_OPERATION_%s_%s_%s" % (
                            op_code,
                            type_name1,
                            type_name2,
                        )
                else:
                    yield "BINARY_OPERATION_%s_%s_%s_%s" % (
                        op_code,
                        result_type,
                        type_name1,
                        type_name2,
                    )

                if not arg_swap:
                    if result_type is None:
                        if type_name2 not in _no_inplace_target_types:
                            yield "INPLACE_OPERATION_%s_%s_%s" % (
                                op_code,
                                type_name2,
                                type_name1,
                            )
                    else:
                        yield "BINARY_OPERATION_%s_%s_%s_%s" % (
                            op_code,
                            result_type,
                            type_name2,
                            type_name1,
                        )


def _makeDefaultOps(op_code, result_types):
    for result_type in result_types or (None,):
        if result_type is None:
            yield "INPLACE_OPERATION_%s_OBJECT_OBJECT" % op_code
        else:
            yield "BINARY_OPERATION_%s_%s_OBJECT_OBJECT" % (op_code, result_type)


def _makeNonContainerMathOps(op_code):
    for type_name in "TUPLE", "LIST", "DICT", "SET", "FROZENSET":
        if "BIT" in op_code and type_name == "SET":
            continue
        if "SUB" in op_code and type_name == "SET":
            continue

        for value in _makeTypeOps(
            op_code, type_name, result_types=standard_result_types
        ):
            yield value


def _makeNumberOps(op_code, result_types):
    return buildOrderedSet(
        _makeTypeOps(op_code=op_code, type_name="INT", result_types=result_types),
        _makeTypeOps(op_code=op_code, type_name="LONG", result_types=result_types),
        _makeTypeOps(op_code=op_code, type_name="FLOAT", result_types=result_types),
        # These are friends naturally, they all add with another.
        _makeFriendOps(
            op_code=op_code,
            friend_type_names=("INT", "LONG", "FLOAT"),
            result_types=result_types,
        ),
        # Special operations, currently used with constant values mostly.
        _makeFriendOps(
            op_code, friend_type_names=("INT", "CLONG"), result_types=result_types
        ),
        (
            _makeFriendOps(
                op_code, friend_type_names=("LONG", "DIGIT"), result_types=result_types
            )
            if op_code in ("ADD", "SUB")  # TODO: Add more
            else ()
        ),
        (
            _makeFriendOps(
                op_code, friend_type_names=("LONG", "CLONG"), result_types=result_types
            )
            if op_code in ("ADD", "SUB")  # TODO: Add more
            else ()
        ),
        _makeFriendOps(
            op_code, friend_type_names=("FLOAT", "CFLOAT"), result_types=result_types
        ),
        (
            _makeFriendOps(
                op_code,
                friend_type_names=("NILONG", "NILONG", "DIGIT"),
                result_types=("NILONG",),
            )
            if op_code in ("ADD", "SUB") and result_types is not None
            else ()
        ),
    )


def _makeAddOps(in_place):
    return buildOrderedSet(
        _makeNumberOps("ADD", result_types=None if in_place else standard_result_types),
        _makeTypeOps("ADD", "STR", result_types=None if in_place else ("OBJECT",)),
        _makeTypeOps("ADD", "UNICODE", result_types=None if in_place else ("OBJECT",)),
        _makeTypeOps("ADD", "BYTES", result_types=None if in_place else ("OBJECT",)),
        _makeTypeOps("ADD", "TUPLE", result_types=None if in_place else ("OBJECT",)),
        _makeTypeOps(
            "ADD", "LIST", result_types=None if in_place else standard_result_types
        ),
        # These are friends too.
        _makeFriendOps(
            "ADD",
            friend_type_names=("STR", "UNICODE"),
            result_types=None if in_place else standard_result_types,
        ),
        # Default implementation.
        _makeDefaultOps(
            "ADD", result_types=None if in_place else standard_result_types
        ),
    )


standard_result_types = ("OBJECT", "NBOOL")

specialized_add_helpers_set = _makeAddOps(in_place=False)

nonspecialized_add_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("ADD", "STR"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "UNICODE"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "BYTES"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "TUPLE"),  # Not really likely to be used.
)


def makeSubOps(result_types):
    return buildOrderedSet(
        _makeNumberOps("SUB", result_types=result_types),
        _makeDefaultOps("SUB", result_types=result_types),
    )


specialized_sub_helpers_set = makeSubOps(result_types=("OBJECT",))

# These made no sense to specialize for, nothing to gain.
nonspecialized_sub_helpers_set = buildOrderedSet(
    _makeTypeOps("SUB", "STR", result_types=standard_result_types),
    _makeTypeOps("SUB", "UNICODE", result_types=standard_result_types),
    _makeTypeOps("SUB", "BYTES", result_types=standard_result_types),
    _makeNonContainerMathOps("SUB"),
)


def _makeMultOps(in_place):
    return buildOrderedSet(
        _makeNumberOps(
            "MULT", result_types=None if in_place else standard_result_types
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("INT", "STR"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("INT", "UNICODE"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("INT", "TUPLE"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("INT", "LIST"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("LONG", "UNICODE"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("LONG", "BYTES"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("LONG", "TUPLE"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeFriendOps(
            "MULT",
            friend_type_names=("LONG", "LIST"),
            result_types=None if in_place else ("OBJECT",),
        ),
        _makeTypeSemiOps("MULT", "STR", result_types=None if in_place else ("OBJECT",)),
        _makeTypeSemiOps(
            "MULT", "UNICODE", result_types=None if in_place else ("OBJECT",)
        ),
        _makeTypeSemiOps(
            "MULT", "BYTES", result_types=None if in_place else ("OBJECT",)
        ),
        _makeTypeSemiOps(
            "MULT", "TUPLE", result_types=None if in_place else ("OBJECT",)
        ),
        _makeTypeSemiOps(
            "MULT", "LIST", result_types=None if in_place else ("OBJECT",)
        ),
        # These are friends naturally, they all mul with another
        _makeDefaultOps(
            "MULT", result_types=None if in_place else standard_result_types
        ),
    )


specialized_mult_helpers_set = _makeMultOps(in_place=False)
# Using booleans, because multiplication might be used to test for zero result.

nonspecialized_mult_helpers_set = None


def _makeDivOps(op_code, result_types):
    return buildOrderedSet(
        _makeNumberOps(op_code, result_types=result_types),
        _makeDefaultOps(op_code, result_types=result_types),
    )


specialized_truediv_helpers_set = _makeDivOps("TRUEDIV", result_types=("OBJECT",))

nonspecialized_truediv_helpers_set = buildOrderedSet(
    _makeTypeOps("TRUEDIV", "UNICODE", result_types=standard_result_types),
    _makeTypeOps("TRUEDIV", "STR", result_types=standard_result_types),
    _makeTypeOps("TRUEDIV", "BYTES", result_types=standard_result_types),
    _makeNonContainerMathOps("TRUEDIV"),
)

specialized_olddiv_helpers_set = _makeDivOps("OLDDIV", result_types=("OBJECT",))

nonspecialized_olddiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "OLDDIV") for helper in nonspecialized_truediv_helpers_set
)

specialized_floordiv_helpers_set = _makeDivOps("FLOORDIV", result_types=("OBJECT",))

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
        _makeNumberOps("MOD", result_types=None if in_place else standard_result_types),
        # These are friends naturally, they mod with another
        _makeFriendOps(
            "MOD",
            friend_type_names=("INT", "LONG", "FLOAT"),
            result_types=None if in_place else standard_result_types,
        ),
        # String interpolation:
        _makeFormatOps(str_type_name="STR"),
        _makeFormatOps(str_type_name="UNICODE"),
        _makeFormatOps(str_type_name="BYTES"),
        _makeDefaultOps(
            "MOD", result_types=None if in_place else standard_result_types
        ),
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
        _makeTypeOps(
            op_name, "LONG", result_types=None if in_place else standard_result_types
        ),
        _makeTypeOps(
            op_name, "INT", result_types=None if in_place else standard_result_types
        ),
        _makeFriendOps(
            op_name,
            friend_type_names=("INT", "CLONG"),
            result_types=None if in_place else standard_result_types,
        ),
        _makeFriendOps(
            op_name,
            friend_type_names=("INT", "LONG"),
            result_types=None if in_place else standard_result_types,
        ),
        _makeTypeOps(op_name, "SET", result_types=None if in_place else ("OBJECT",)),
        _makeDefaultOps(
            op_name, result_types=None if in_place else standard_result_types
        ),
    )


specialized_bitor_helpers_set = _makeBitOps("BITOR", in_place=False)

nonspecialized_bitor_helpers_set = buildOrderedSet(
    _makeTypeOps("BITOR", "FLOAT", result_types=standard_result_types),
    _makeNonContainerMathOps("BITOR"),
    _makeTypeOps("BITOR", "UNICODE", result_types=standard_result_types),
    _makeTypeOps("BITOR", "STR", result_types=standard_result_types),
    _makeTypeOps("BITOR", "BYTES", result_types=standard_result_types),
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
        _makeTypeOps(
            op_name, "LONG", result_types=None if in_place else standard_result_types
        ),
        _makeTypeOps(
            op_name, "INT", result_types=None if in_place else standard_result_types
        ),
        _makeFriendOps(
            op_name,
            friend_type_names=("INT", "LONG"),
            result_types=None if in_place else standard_result_types,
        ),
        _makeDefaultOps(
            op_name, result_types=None if in_place else standard_result_types
        ),
    )


specialized_lshift_helpers_set = _makeShiftOps("LSHIFT", in_place=False)

nonspecialized_lshift_helpers_set = buildOrderedSet(
    _makeTypeOps("LSHIFT", "FLOAT", result_types=standard_result_types),
    _makeNonContainerMathOps("LSHIFT"),
)
specialized_rshift_helpers_set = _makeShiftOps("RSHIFT", in_place=False)

nonspecialized_rshift_helpers_set = OrderedSet(
    helper.replace("_LSHIFT_", "_RSHIFT_")
    for helper in nonspecialized_lshift_helpers_set
)


specialized_pow_helpers_set = buildOrderedSet(
    _makeTypeOps("POW", "FLOAT", result_types=("OBJECT",)),
    _makeTypeOps("POW", "LONG", result_types=("OBJECT",)),
    _makeTypeOps("POW", "INT", result_types=("OBJECT",)),
    _makeFriendOps(
        "POW", friend_type_names=("INT", "LONG", "FLOAT"), result_types=("OBJECT",)
    ),
    _makeDefaultOps("POW", result_types=standard_result_types),
    (
        # Float is used by other types for ** operations.
        # TODO: Enable these later.
        #        "BINARY_OPERATION_POW_OBJECT_LONG_FLOAT",
        #        "BINARY_OPERATION_POW_NBOOL_LONG_FLOAT",
    ),
)
nonspecialized_pow_helpers_set = buildOrderedSet(
    _makeTypeOps("POW", "STR", result_types=standard_result_types),
    _makeTypeOps("POW", "UNICODE", result_types=standard_result_types),
    _makeTypeOps("POW", "BYTES", result_types=standard_result_types),
    _makeNonContainerMathOps("POW"),
)


specialized_divmod_helpers_set = _makeDivOps("DIVMOD", result_types=("OBJECT",))

nonspecialized_divmod_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("DIVMOD", "INT"),
    _makeTypeOpsNbool("DIVMOD", "LONG"),
    _makeTypeOpsNbool("DIVMOD", "FLOAT"),
    _makeTypeOps("DIVMOD", "UNICODE", result_types=standard_result_types),
    _makeTypeOps("DIVMOD", "STR", result_types=standard_result_types),
    _makeTypeOps("DIVMOD", "BYTES", result_types=standard_result_types),
    _makeNonContainerMathOps("DIVMOD"),
)

specialized_matmult_helpers_set = buildOrderedSet(
    _makeTypeOps("MATMULT", "LONG", result_types=("OBJECT",)),
    _makeTypeOps("MATMULT", "FLOAT", result_types=("OBJECT",)),
    _makeDefaultOps("MATMULT", result_types=("OBJECT",)),
)

nonspecialized_matmult_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("MATMULT", "LONG"),
    _makeTypeOpsNbool("MATMULT", "FLOAT"),
    _makeTypeOps("MATMULT", "TUPLE", result_types=standard_result_types),
    _makeTypeOps("MATMULT", "LIST", result_types=standard_result_types),
    _makeTypeOps("MATMULT", "DICT", result_types=standard_result_types),
    _makeTypeOps("MATMULT", "BYTES", result_types=standard_result_types),
    _makeTypeOps("MATMULT", "UNICODE", result_types=standard_result_types),
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

specialized_isub_helpers_set = makeSubOps(result_types=None)

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

specialized_ifloordiv_helpers_set = _makeDivOps("FLOORDIV", result_types=None)

nonspecialized_ifloordiv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_floordiv_helpers_set
)

specialized_itruediv_helpers_set = _makeDivOps("TRUEDIV", result_types=None)

nonspecialized_itruediv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_truediv_helpers_set
)

specialized_iolddiv_helpers_set = _makeDivOps("OLDDIV", result_types=None)

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
