#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for match statement helpers.

"""

from .CodeHelpers import (
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitCode


def generateMatchArgsCode(to_name, expression, emit, context):
    (matched_value_name, match_type_name) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # TODO: Prefer "PyObject **" of course once we have that.
    keywords = expression.getKeywordArgs()

    if keywords:
        keywords_name = context.getConstantCode(constant=keywords)
        keywords_name = "&PyTuple_GET_ITEM(%s, 0)" % keywords_name
    else:
        keywords_name = "NULL"

    with withObjectCodeTemporaryAssignment(
        to_name, "match_args_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = MATCH_CLASS_ARGS(tstate, %s, %s, %d, %s, %d);"
            % (
                value_name,
                matched_value_name,
                match_type_name,
                expression.getPositionalArgsCount(),
                keywords_name,
                len(keywords),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(matched_value_name, match_type_name),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


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
