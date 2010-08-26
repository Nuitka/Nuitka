# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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
multiple_arg_operators = {
    "Bitand"     : "NUMBER_AND",
    "Bitor"      : "NUMBER_OR",
    "Bitxor"     : "NUMBER_XOR",
}

binary_operators = {
    "Power"      : "PyNumber_Power",
    "Mul"        : "PyNumber_Multiply",
    "Div"        : "PyNumber_Divide",
    "FloorDiv"   : "PyNumber_FloorDivide",
    "Mod"        : "PyNumber_Remainder",
    "Add"        : "PyNumber_Add",
    "Sub"        : "PyNumber_Subtract",
    "LeftShift"  : "PyNumber_Lshift",
    "RightShift" : "PyNumber_Rshift",
}

inplace_operator_opcodes = {
    "+="                   : "PyNumber_InPlaceAdd",
    "-="                   : "PyNumber_InPlaceSubtract",
    "**="                  : "PyNumber_InPlacePower",
    "*="                   : "PyNumber_InPlaceMultiply",
    "/="                   : "PyNumber_InPlaceDivide",
    "//="                  : "PyNumber_InPlaceFloorDivide",
    "%="                   : "PyNumber_InPlaceRemainder",
    "<<="                  : "PyNumber_InPlaceLshift",
    ">>="                  : "PyNumber_InPlaceRshift",
    "&="                   : "PyNumber_InPlaceAnd",
    "^="                   : "PyNumber_InPlaceXor",
    "|="                   : "PyNumber_InPlaceOr"
}

unary_operators = {
    "UnaryAdd"       : "PyNumber_Positive",
    "UnarySub"       : "PyNumber_Negative",
    "Invert"         : "PyNumber_Invert",
    "Backquote"      : "PyObject_Repr",
}

normal_comparison_operators = {
    "in"     : "SEQUENCE_CONTAINS",
    "not in" : "SEQUENCE_CONTAINS_NOT"
}

rich_comparison_operators = {
    "<"  : "Py_LT",
    "<=" : "Py_LE",
    "==" : "Py_EQ",
    "!=" : "Py_NE",
    ">"  : "Py_GT",
    ">=" : "Py_GE"
}
