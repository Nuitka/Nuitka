#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import itertools


def calledRepeatedly(cond):
    if cond:
        # At function entry, before first assignment "NUITKA_ILONG_UNASSIGNED" which
        # means no C or object value is value.
        i = 0
        # When assigning from constants, we do NUITKA_ILONG_BOTH_VALID. Depending
        # on the type, we might not

        # Comparing to a CLONG, is easy. Actually for such small values, a DIGIT
        # type will be used, which is like a CLONG but smaller and known to work
        # well with "PyLongObject *" internals.
        while i < 20000:  # RICH_COMPARE_CBOOL_NILONG_CLONG(i, 9)
            # BINARY_OPERATION_ADD_NILONG_NILONG_CLONG(i, 1)
            i = i + 1
            # NUITKA_ILONG_CLONG_VALID

        # The flag NUITKA_INT_OBJECT_VALID is not set, need to create the object
        # pointer and return it.
        return i


for x in itertools.repeat(None, 50):
    # construct_begin
    calledRepeatedly(True)
    # construct_alternative
    calledRepeatedly(False)
    # construct_end

print("OK.")

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
