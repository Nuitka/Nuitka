#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
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
    "UAdd"   : ( "PyNumber_Positive", 1 ),
    "USub"   : ( "PyNumber_Negative", 1 ),
    "Invert" : ( "PyNumber_Invert", 1 ),
    "Repr"   : ( "PyObject_Repr", 1 ),
    "Not"    : ( "UNARY_NOT", 0 )
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
