#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Print related codes.

This is broken down to to level on printing one individual item, and
a new line potentially. The heavy lifting for 'softspace', etc. is
happening in the C helper functions.

"""

from .CodeHelpers import generateExpressionCode
from .ErrorCodes import getErrorExitBoolCode


def generatePrintValueCode(statement, emit, context):
    destination = statement.getDestination()
    value = statement.getValue()

    if destination is not None:
        dest_name = context.allocateTempName("print_dest", unique=True)

        generateExpressionCode(
            expression=destination, to_name=dest_name, emit=emit, context=context
        )
    else:
        dest_name = None

    value_name = context.allocateTempName("print_value", unique=True)

    generateExpressionCode(
        expression=value, to_name=value_name, emit=emit, context=context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    res_name = context.getBoolResName()

    if dest_name is not None:
        print_code = "%s = PRINT_ITEM_TO( %s, %s );" % (res_name, dest_name, value_name)
    else:
        print_code = "%s = PRINT_ITEM( %s );" % (res_name, value_name)

    emit(print_code)

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(dest_name, value_name),
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generatePrintNewlineCode(statement, emit, context):
    destination = statement.getDestination()

    if destination is not None:
        dest_name = context.allocateTempName("print_dest", unique=True)

        generateExpressionCode(
            expression=destination, to_name=dest_name, emit=emit, context=context
        )
    else:
        dest_name = None

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    if dest_name is not None:
        print_code = "PRINT_NEW_LINE_TO( %s ) == false" % (dest_name,)
    else:
        print_code = "PRINT_NEW_LINE() == false"

    getErrorExitBoolCode(
        condition=print_code, release_name=dest_name, emit=emit, context=context
    )

    context.setCurrentSourceCodeReference(old_source_ref)
