#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Module for helpers to select types for operation arguments.

This is first used for comparisons and binary operations, but should see
general use too and expand beyond constant values, e.g. covering constant
values that are of behind conditions or variables.
"""
from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bytearray,
    tshape_bytes,
    tshape_float,
    tshape_int,
    tshape_long,
    tshape_str,
    tshape_unicode,
)
from nuitka.PythonVersions import (
    isPythonValidCLongValue,
    isPythonValidDigitValue,
    python_version,
)

from .c_types.CTypeCFloats import CTypeCFloat
from .c_types.CTypeCLongs import CTypeCLong, CTypeCLongDigit
from .c_types.CTypePyObjectPointers import CTypePyObjectPtr


def _pickIntFamilyType(expression):
    if expression.isCompileTimeConstant():
        # On Python2, "INT_CLONG" is very fast as "CLONG" is the internal representation
        # of it, for Python3, it should be avoided, it usually is around 2**30.
        if python_version < 0x300:
            c_type = CTypeCLong
        elif isPythonValidDigitValue(expression.getCompileTimeConstant()):
            c_type = CTypeCLongDigit
        elif isPythonValidCLongValue(expression.getCompileTimeConstant()):
            c_type = CTypeCLong
        else:
            c_type = CTypePyObjectPtr
    else:
        c_type = CTypePyObjectPtr

    return c_type


def _pickFloatFamilyType(expression):
    if expression.isCompileTimeConstant():
        c_type = CTypeCFloat
    else:
        c_type = CTypePyObjectPtr

    return c_type


def _pickStrFamilyType(expression):
    # TODO: No C types yet for these, pylint: disable=unused-argument
    return CTypePyObjectPtr


def _pickBytesFamilyType(expression):
    # TODO: No C types yet for these, pylint: disable=unused-argument
    return CTypePyObjectPtr


_int_types_family = (tshape_int, tshape_long)
_float_types_family = (tshape_int, tshape_long, tshape_float)
_str_types_family = (tshape_str, tshape_unicode)

# TODO: Bytearray should be there too.
_bytes_types_family = (tshape_bytes,)

_float_argument_normalization = {
    # The C float argument should be last.
    (CTypePyObjectPtr, CTypeCFloat): False,
    (CTypeCFloat, CTypePyObjectPtr): True,
}

_long_argument_normalization = {
    # The C long/digit arguments should be last.
    (CTypePyObjectPtr, CTypeCLong): False,
    (CTypeCLong, CTypePyObjectPtr): True,
    (CTypePyObjectPtr, CTypeCLongDigit): False,
    (CTypeCLongDigit, CTypePyObjectPtr): True,
}

_str_argument_normalization = {
    # The C str/unicode argument should be last, but does not exist yet.
}

_bytes_argument_normalization = {
    # The C str/unicode argument should be last, but does not exist yet.
}


def decideExpressionCTypes(left, right, may_swap_arguments):
    # Complex stuff with many cases, pylint: disable=too-many-branches

    left_shape = left.getTypeShape()
    right_shape = right.getTypeShape()

    if left_shape in _int_types_family and right_shape in _int_types_family:
        may_swap_arguments = may_swap_arguments in ("number", "always")

        left_c_type = _pickIntFamilyType(left)
        right_c_type = _pickIntFamilyType(right)

        needs_argument_swap = (
            may_swap_arguments
            and left_c_type is not right_c_type
            and _long_argument_normalization[(left_c_type, right_c_type)]
        )

        # TODO: The INT and LONG types, do not have distinct C types yet, and maybe
        # won't have it, so these are manual:
        if may_swap_arguments and not needs_argument_swap:
            if right_shape is tshape_long and left_shape is tshape_int:
                needs_argument_swap = True

        unknown_types = False
    elif left_shape in _float_types_family and right_shape in _float_types_family:
        may_swap_arguments = may_swap_arguments in ("number", "always")

        left_c_type = _pickFloatFamilyType(left)
        right_c_type = _pickFloatFamilyType(right)

        # Arguments might be swapped because of normalization.
        needs_argument_swap = (
            may_swap_arguments
            and left_c_type is not right_c_type
            and _float_argument_normalization[(left_c_type, right_c_type)]
        )

        # TODO: The INT and LONG types, do not have distinct C types yet, and maybe
        # won't have it, so these are manual:
        if may_swap_arguments and not needs_argument_swap:
            if right_shape is tshape_float and left_shape in (tshape_int, tshape_long):
                needs_argument_swap = True

        unknown_types = False
    elif left_shape in _str_types_family and right_shape in _str_types_family:
        may_swap_arguments = may_swap_arguments == "always"

        left_c_type = _pickStrFamilyType(left)
        right_c_type = _pickStrFamilyType(right)

        # Arguments might be swapped because of normalization.
        needs_argument_swap = (
            may_swap_arguments
            and left_c_type is not right_c_type
            and _str_argument_normalization[(left_c_type, right_c_type)]
        )

        # TODO: The STR and UNICODE types, do not have distinct C types yet, and maybe
        # won't have it, so these are manual:
        if may_swap_arguments and not needs_argument_swap and str is bytes:
            if right_shape is tshape_unicode and left_shape is tshape_str:
                needs_argument_swap = True

        unknown_types = False
    elif left_shape in _bytes_types_family and right_shape in _bytes_types_family:
        may_swap_arguments = may_swap_arguments == "always"

        left_c_type = _pickBytesFamilyType(left)
        right_c_type = _pickBytesFamilyType(right)

        # Arguments might be swapped because of normalization.
        needs_argument_swap = (
            may_swap_arguments
            and left_c_type is not right_c_type
            and _bytes_argument_normalization[(left_c_type, right_c_type)]
        )

        # TODO: The BYTES and BYTEARRAY types, do not have distinct C types yet, and maybe
        # won't have it, so these are manual:
        if may_swap_arguments and not needs_argument_swap:
            if right_shape is tshape_bytearray and left_shape is tshape_bytes:
                needs_argument_swap = True

        unknown_types = False
    else:
        left_c_type = right_c_type = CTypePyObjectPtr

        needs_argument_swap = False
        unknown_types = True

    return (
        unknown_types,
        needs_argument_swap,
        left_shape,
        right_shape,
        left_c_type,
        right_c_type,
    )
