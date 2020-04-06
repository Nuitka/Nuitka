#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

import operator

from nuitka.PythonVersions import python_version

binary_operator_functions = {
    "Add": operator.add,
    "Sub": operator.sub,
    "Pow": operator.pow,
    "Mult": operator.mul,
    "FloorDiv": operator.floordiv,
    "TrueDiv": operator.truediv,
    "Mod": operator.mod,
    "LShift": operator.lshift,
    "RShift": operator.rshift,
    "BitAnd": operator.and_,
    "BitOr": operator.or_,
    "BitXor": operator.xor,
    "Divmod": divmod,
    "IAdd": operator.iadd,
    "ISub": operator.isub,
    "IPow": operator.ipow,
    "IMult": operator.imul,
    "IFloorDiv": operator.ifloordiv,
    "ITrueDiv": operator.itruediv,
    "IMod": operator.imod,
    "ILShift": operator.ilshift,
    "IRShift": operator.irshift,
    "IBitAnd": operator.iand,
    "IBitOr": operator.ior,
    "IBitXor": operator.ixor,
}

# Python 2 only operator
if python_version < 300:
    binary_operator_functions["OldDiv"] = operator.div
    binary_operator_functions["IOldDiv"] = operator.idiv

# Python 3.5 only operator
if python_version >= 350:
    binary_operator_functions["MatMult"] = operator.matmul
    binary_operator_functions["IMatMult"] = operator.imatmul

unary_operator_functions = {
    "UAdd": operator.pos,
    "USub": operator.neg,
    "Invert": operator.invert,
    "Repr": repr,
    # Boolean not is treated an unary operator.
    "Not": operator.not_,
    "Abs": operator.abs,
}


rich_comparison_functions = {
    "Lt": operator.lt,
    "LtE": operator.le,
    "Eq": operator.eq,
    "NotEq": operator.ne,
    "Gt": operator.gt,
    "GtE": operator.ge,
}

other_comparison_functions = {
    "Is": operator.is_,
    "IsNot": operator.is_not,
    "In": lambda value1, value2: value1 in value2,
    "NotIn": lambda value1, value2: value1 not in value2,
}

comparison_inversions = {
    "Is": "IsNot",
    "IsNot": "Is",
    "In": "NotIn",
    "NotIn": "In",
    "Lt": "GtE",
    "GtE": "Lt",
    "Eq": "NotEq",
    "NotEq": "Eq",
    "Gt": "LtE",
    "LtE": "Gt",
}

all_comparison_functions = dict(rich_comparison_functions)
all_comparison_functions.update(other_comparison_functions)


def matchException(left, right):
    if python_version >= 300:
        if type(right) is tuple:
            for element in right:
                if not isinstance(BaseException, element):
                    raise TypeError(
                        "catching classes that do not inherit from BaseException is not allowed"
                    )
        elif not isinstance(BaseException, right):
            raise TypeError(
                "catching classes that do not inherit from BaseException is not allowed"
            )

    # This doesn't yet work, make it error exit. and silence PyLint for now.
    # pylint: disable=protected-access
    import os

    os._exit(16)

    assert False, left


all_comparison_functions["exception_match"] = matchException
