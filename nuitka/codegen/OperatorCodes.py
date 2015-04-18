#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Operator code tables

These are mostly used to look up the Python C/API from operations or a wrapper used.

"""

binary_operator_codes = {
# Those commented out in this section have fully specialized variants already.

#    "Add"       : "PyNumber_Add",
#    "Sub"       : "PyNumber_Subtract",
#    "Div"       : "PyNumber_Divide",
#    "Mult"      : "PyNumber_Multiply",
#    "Mod"       : "PyNumber_Remainder",
# These have their own variants only to make sure the generic code is in-lined
# but the CPython code is not in-lined.

#    "Pow"       : "PyNumber_Power",
#    "IPow"      : "PyNumber_InPlacePower",

# The others are generic code and would be faster if they had a specialized variant too.
    "FloorDiv"  : "PyNumber_FloorDivide",
    "TrueDiv"   : "PyNumber_TrueDivide",
    "LShift"    : "PyNumber_Lshift",
    "RShift"    : "PyNumber_Rshift",
    "BitAnd"    : "PyNumber_And",
    "BitOr"     : "PyNumber_Or",
    "BitXor"    : "PyNumber_Xor",
    "IAdd"      : "PyNumber_InPlaceAdd",
    "ISub"      : "PyNumber_InPlaceSubtract",
    "IMult"     : "PyNumber_InPlaceMultiply",
    "IDiv"      : "PyNumber_InPlaceDivide",
    "IFloorDiv" : "PyNumber_InPlaceFloorDivide",
    "ITrueDiv"  : "PyNumber_InPlaceTrueDivide",
    "IMod"      : "PyNumber_InPlaceRemainder",
    "ILShift"   : "PyNumber_InPlaceLshift",
    "IRShift"   : "PyNumber_InPlaceRshift",
    "IBitAnd"   : "PyNumber_InPlaceAnd",
    "IBitOr"    : "PyNumber_InPlaceOr",
    "IBitXor"   : "PyNumber_InPlaceXor",
}

inplace_operator_codes = {
    "IAdd" : "BINARY_OPERATION_ADD_INPLACE"
}

unary_operator_codes = {
    "UAdd"   : ("PyNumber_Positive", 1),
    "USub"   : ("PyNumber_Negative", 1),
    "Invert" : ("PyNumber_Invert", 1),
    "Repr"   : ("PyObject_Repr", 1),
    "Not"    : ("UNARY_NOT", 0)
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
