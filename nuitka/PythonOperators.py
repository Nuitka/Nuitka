#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Python operator tables

These are mostly used to resolve the operator in the module operator and to know the list
of operations allowed.

"""

from .Utils import python_version

import operator

if python_version >= 300:
    operator.div = operator.truediv
    operator.idiv = operator.itruediv

binary_operator_functions = {
    "Add"       : operator.add,
    "Sub"       : operator.sub,
    "Pow"       : operator.pow,
    "Mult"      : operator.mul,
    "Div"       : operator.div,
    "FloorDiv"  : operator.floordiv,
    "TrueDiv"   : operator.truediv,
    "Mod"       : operator.mod,
    "LShift"    : operator.lshift,
    "RShift"    : operator.rshift,
    "BitAnd"    : operator.and_,
    "BitOr"     : operator.or_,
    "BitXor"    : operator.xor,
    "IAdd"      : operator.iadd,
    "ISub"      : operator.isub,
    "IPow"      : operator.ipow,
    "IMult"     : operator.imul,
    "IDiv"      : operator.idiv,
    "IFloorDiv" : operator.ifloordiv,
    "ITrueDiv"  : operator.itruediv,
    "IMod"      : operator.imod,
    "ILShift"   : operator.ilshift,
    "IRShift"   : operator.irshift,
    "IBitAnd"   : operator.iand,
    "IBitOr"    : operator.ior,
    "IBitXor"   : operator.ixor,
}

unary_operator_functions = {
    "UAdd"   : operator.pos,
    "USub"   : operator.neg,
    "Invert" : operator.invert,
    "Repr"   : repr,
    # Boolean not is treated an unary operator.
    "Not"    : operator.not_,
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

comparison_inversions = {
    "Is"    : "IsNot",
    "IsNot" : "Is",
    "In"    : "NotIn",
    "NotIn" : "In"
}

all_comparison_functions = dict( rich_comparison_functions)
all_comparison_functions.update( other_comparison_functions )
