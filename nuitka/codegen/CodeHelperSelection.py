#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Select from code helpers.

This aims at being general, but right now is only used for comparison code helpers.
"""

from nuitka import Options

from .c_types.CTypeNuitkaBools import CTypeNuitkaBoolEnum
from .c_types.CTypePyObjectPtrs import CTypePyObjectPtr
from .c_types.CTypeVoids import CTypeVoid
from .Reports import onMissingHelper


def selectCodeHelper(
    prefix,
    specialized_helpers_set,
    nonspecialized,
    helper_type,
    left_shape,
    right_shape,
    left_c_type,
    right_c_type,
    source_ref,
):
    left_helper = (
        left_shape.helper_code
        if left_c_type is CTypePyObjectPtr
        else left_c_type.helper_code
    )
    right_helper = (
        right_shape.helper_code
        if right_c_type is CTypePyObjectPtr
        else right_c_type.helper_code
    )

    while 1:
        helper_function = "%s_%s_%s_%s" % (
            prefix,
            helper_type.helper_code,
            left_helper,
            right_helper,
        )
        if helper_function in specialized_helpers_set:
            break

        # Special hack for "void", use the "NBOOL" more automatically"
        if helper_type is CTypeVoid:
            helper_type = CTypeNuitkaBoolEnum
        else:
            if Options.is_report_missing and (
                not nonspecialized or helper_function not in nonspecialized
            ):
                onMissingHelper(helper_function, source_ref)

            return None, None

    return helper_type, helper_function
