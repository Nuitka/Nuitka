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

These are mostly used to resolve the operator in the module operator and to know the list
of operations allowed.

"""

from .Utils import getPythonVersion

import operator

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


unary_operator_functions = {
    "UAdd"   : operator.pos,
    "USub"   : operator.neg,
    "Invert" : operator.invert,
    "Repr"   : repr,
}


rich_comparison_functions = {
    "Lt"    : operator.lt,
    "LtE"   : operator.le,
    "Eq"    : operator.eq,
    "NotEq" : operator.ne,
    "Gt"    : operator.gt,
    "GtE"   : operator.ge
}

other_comparison_functions = {
    "Is"    : operator.is_,
    "IsNot" : operator.is_not,
    "In"    : lambda value1, value2: value1 in value2,
    "NotIn" : lambda value1, value2: value1 not in value2
}


all_comparison_functions = dict( rich_comparison_functions)
all_comparison_functions.update( other_comparison_functions )
