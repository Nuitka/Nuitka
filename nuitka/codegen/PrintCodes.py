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


from .ErrorCodes import getErrorExitBoolCode, getReleaseCode, getReleaseCodes


def getPrintValueCode(dest_name, value_name, emit, context):
    if dest_name is not None:
        print_code = "PRINT_ITEM_TO( %s, %s ) == false" % (
            dest_name,
            value_name
        )
    else:
        print_code = "PRINT_ITEM( %s ) == false" % (
            value_name,
        )

    getErrorExitBoolCode(
        condition = print_code,
        emit      = emit,
        context   = context
    )

    getReleaseCodes(
        release_names = (dest_name, value_name),
        emit          = emit,
        context       = context
    )


def getPrintNewlineCode(dest_name, emit, context):
    if dest_name is not None:
        print_code = "PRINT_NEW_LINE_TO( %s ) == false" % (
            dest_name,
        )
    else:
        print_code = "PRINT_NEW_LINE() == false"

    getErrorExitBoolCode(
        condition = print_code,
        emit      = emit,
        context   = context
    )

    getReleaseCode(
        release_name = dest_name,
        emit         = emit,
        context      = context
    )
