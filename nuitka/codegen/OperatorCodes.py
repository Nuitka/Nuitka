#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

unary_operator_codes = {
    "UAdd": ("PyNumber_Positive", 1),
    "USub": ("PyNumber_Negative", 1),
    "Invert": ("PyNumber_Invert", 1),
    "Repr": ("PyObject_Repr", 1),
    "Not": ("UNARY_NOT", 0),
}

rich_comparison_codes = {
    "Lt": "LT",
    "LtE": "LE",
    "Eq": "EQ",
    "NotEq": "NE",
    "Gt": "GT",
    "GtE": "GE",
}

containing_comparison_codes = ("In", "NotIn")
