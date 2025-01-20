#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" CType classes for C "float" (double), (used in conjunction with PyFloatObject *)

"""

from math import copysign, isinf, isnan

from .CTypeBases import CTypeBase


class CTypeCFloat(CTypeBase):
    c_type = "double"

    helper_code = "CFLOAT"

    @classmethod
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        # No context needed, pylint: disable=unused-argument
        if constant == 0.0:
            if copysign(1, constant) == 1:
                c_constant = "0.0"
            else:
                c_constant = "-0.0"
        elif isnan(constant):
            if copysign(1, constant) == 1:
                c_constant = "NAN"
            else:
                c_constant = "-NAN"
        elif isinf(constant):
            if copysign(1, constant) == 1:
                c_constant = "HUGE_VAL"
            else:
                c_constant = "-HUGE_VAL"
        else:
            c_constant = constant

        emit("%s = %s;" % (to_name, c_constant))


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
