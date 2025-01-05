#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for index values.

This is not for actual subscripts (see SubscriptCodes), but to convert
generic values to indexes. Also the maximum and minimum index values
are abstracted here.

"""

from .ErrorCodes import getErrorExitBoolCode


def getMaxIndexCode(to_name, emit):
    emit("%s = PY_SSIZE_T_MAX;" % to_name)


def getMinIndexCode(to_name, emit):
    emit("%s = 0;" % to_name)


def getIndexCode(to_name, value_name, emit, context):
    emit("%s = CONVERT_TO_INDEX(tstate, %s);" % (to_name, value_name))

    getErrorExitBoolCode(
        condition="%s == -1 && HAS_ERROR_OCCURRED(tstate)" % to_name,
        emit=emit,
        context=context,
    )


def getIndexValueCode(to_name, value, emit):
    emit("%s = %d;" % (to_name, value))


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
