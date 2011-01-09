#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Python operator tables

These are mostly used to look up the Python C/API from operations or a wrapper used and to
resolve the operator in the module operator.

"""

from .Utils import getPythonVersion

import operator

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

if getPythonVersion() >= 300:
    operator.div = operator.truediv

binary_operator_functions = {
    "Add"      : operator.add,
    "Sub"      : operator.sub,
    "Pow"      : operator.pow,
    "Mult"     : operator.mul,
    "Div"      : operator.div,
    "FloorDiv" : operator.floordiv,
    "TrueDiv"  : operator.truediv,
    "Mod"      : operator.mod,
    "LShift"   : operator.lshift,
    "RShift"   : operator.rshift,
    "BitAnd"   : operator.and_,
    "BitOr"    : operator.or_,
    "BitXor"   : operator.xor,
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

if getPythonVersion() >= 300:
    operator.idiv = operator.itruediv

inplace_operator_functions = {
    "Add"      : operator.iadd,
    "Sub"      : operator.isub,
    "Pow"      : operator.ipow,
    "Mult"     : operator.imul,
    "Div"      : operator.idiv,
    "FloorDiv" : operator.ifloordiv,
    "TrueDiv"  : operator.itruediv,
    "Mod"      : operator.imod,
    "LShift"   : operator.ilshift,
    "RShift"   : operator.irshift,
    "BitAnd"   : operator.iand,
    "BitOr"    : operator.ior,
    "BitXor"   : operator.ixor,
}


assert inplace_operator_codes.keys() == binary_operator_codes.keys()

unary_operator_codes = {
    "UAdd"   : "PyNumber_Positive",
    "USub"   : "PyNumber_Negative",
    "Invert" : "PyNumber_Invert",
    "Repr"   : "PyObject_Repr",
}

unary_operator_functions = {
    "UAdd"   : operator.pos,
    "USub"   : operator.neg,
    "Invert" : operator.invert,
    "Repr"   : "PyObject_Repr",
}

normal_comparison_operators = {
    "In"    : "SEQUENCE_CONTAINS",
    "NotIn" : "SEQUENCE_CONTAINS_NOT"
}

rich_comparison_functions = {
    "Lt"    : operator.lt,
    "LtE"   : operator.le,
    "Eq"    : operator.eq,
    "NotEq" : operator.ne,
    "Gt"    : operator.gt,
    "GtE"   : operator.ge
}

rich_comparison_codes = {
    "Lt"    : "Py_LT",
    "LtE"   : "Py_LE",
    "Eq"    : "Py_EQ",
    "NotEq" : "Py_NE",
    "Gt"    : "Py_GT",
    "GtE"   : "Py_GE"
}
