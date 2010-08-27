#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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

# TODO: No more needed maybe
multiple_arg_operators = {
    "Bitand"     : "NUMBER_AND",
    "Bitor"      : "NUMBER_OR",
    "Bitxor"     : "NUMBER_XOR",
}

binary_operators = {
    "Pow"        : "PyNumber_Power",
    "Mult"       : "PyNumber_Multiply",
    "Div"        : "PyNumber_Divide",
    "FloorDiv"   : "PyNumber_FloorDivide",
    "TrueDiv"    : "PyNumber_TrueDivide",
    "Mod"        : "PyNumber_Remainder",
    "Add"        : "PyNumber_Add",
    "Sub"        : "PyNumber_Subtract",
    "LShift"     : "PyNumber_Lshift",
    "RShift"     : "PyNumber_Rshift",
    "BitAnd"     : "PyNumber_And",
    "BitOr"      : "PyNumber_Or",
    "BitXor"     : "PyNumber_Xor",
}

inplace_operator_opcodes = {
    "Add"                  : "PyNumber_InPlaceAdd",
    "Sub"                  : "PyNumber_InPlaceSubtract",
    "Pow"                  : "PyNumber_InPlacePower",
    "Mult"                 : "PyNumber_InPlaceMultiply",
    "Div"                  : "PyNumber_InPlaceDivide",
    "FloorDiv"             : "PyNumber_InPlaceFloorDivide",
    "Mod"                  : "PyNumber_InPlaceRemainder",
    "LShift"               : "PyNumber_InPlaceLshift",
    "RShift"               : "PyNumber_InPlaceRshift",
    "BitAnd"               : "PyNumber_InPlaceAnd",
    "BitOr"                : "PyNumber_InPlaceOr",
    "BitXor"               : "PyNumber_InPlaceXor",
}

unary_operators = {
    "UAdd"       : "PyNumber_Positive",
    "USub"       : "PyNumber_Negative",
    "Invert"     : "PyNumber_Invert",
    "Repr"       : "PyObject_Repr",
}

normal_comparison_operators = {
    "In"    : "SEQUENCE_CONTAINS",
    "NotIn" : "SEQUENCE_CONTAINS_NOT"
}

rich_comparison_operators = {
    "Lt"    : "Py_LT",
    "LtE"   : "Py_LE",
    "Eq"    : "Py_EQ",
    "NotEq" : "Py_NE",
    "Gt"    : "Py_GT",
    "GtE"   : "Py_GE"
}
