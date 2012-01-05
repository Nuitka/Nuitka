#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at a later time to
#     the PSF. With this version of Nuitka, using it for a Closed Source and
#     distributing the binary only is not allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Operator code tables

These are mostly used to look up the Python C/API from operations or a wrapper used.

"""

binary_operator_codes = {
    "Add"      : "PyNumber_Add",
    "Sub"      : "PyNumber_Subtract",
    "Pow"      : "PyNumber_Power",
    "Mult"     : "PyNumber_Multiply",
    "Div"      : "PyNumber_Divide",
    "FloorDiv" : "PyNumber_FloorDivide",
    "TrueDiv"  : "PyNumber_TrueDivide",
    "Mod"      : "PyNumber_Remainder",
    "LShift"   : "PyNumber_Lshift",
    "RShift"   : "PyNumber_Rshift",
    "BitAnd"   : "PyNumber_And",
    "BitOr"    : "PyNumber_Or",
    "BitXor"   : "PyNumber_Xor",
}

inplace_operator_codes = {
    "Add"      : "PyNumber_InPlaceAdd",
    "Sub"      : "PyNumber_InPlaceSubtract",
    "Pow"      : "PyNumber_InPlacePower",
    "Mult"     : "PyNumber_InPlaceMultiply",
    "Div"      : "PyNumber_InPlaceDivide",
    "FloorDiv" : "PyNumber_InPlaceFloorDivide",
    "TrueDiv"  : "PyNumber_InPlaceTrueDivide",
    "Mod"      : "PyNumber_InPlaceRemainder",
    "LShift"   : "PyNumber_InPlaceLshift",
    "RShift"   : "PyNumber_InPlaceRshift",
    "BitAnd"   : "PyNumber_InPlaceAnd",
    "BitOr"    : "PyNumber_InPlaceOr",
    "BitXor"   : "PyNumber_InPlaceXor",
}

assert inplace_operator_codes.keys() == binary_operator_codes.keys()

unary_operator_codes = {
    "UAdd"   : "PyNumber_Positive",
    "USub"   : "PyNumber_Negative",
    "Invert" : "PyNumber_Invert",
    "Repr"   : "PyObject_Repr",
}

rich_comparison_codes = {
    "Lt"    : "LT",
    "LtE"   : "LE",
    "Eq"    : "EQ",
    "NotEq" : "NE",
    "Gt"    : "GT",
    "GtE"   : "GE"
}

normal_comparison_codes = {
    "In"    : "SEQUENCE_CONTAINS",
    "NotIn" : "SEQUENCE_CONTAINS_NOT"
}
