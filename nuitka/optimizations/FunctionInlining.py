#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" In-lining of functions.

Done by assigning the argument values to variables, and producing an outline
from the in-lined function.
"""

from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.tree.Extractions import updateVariableUsage
from nuitka.tree.TreeHelpers import makeStatementsSequence


def convertFunctionCallToOutline(provider, function_ref, values):
    # This has got to have pretty man details, pylint: disable=too-many-locals
    function_body = function_ref.getFunctionBody()

    call_source_ref = function_ref.getSourceReference()
    function_source_ref = function_body.getSourceReference()

    outline_body = ExpressionOutlineBody(
        provider   = provider,
        name       = "inline",
        source_ref = function_source_ref
    )

    clone = function_body.getBody().makeClone()

    temp_scope = outline_body.getOutlineTempScope()

    translation = {}

    for variable in function_body.getLocalVariables():
        # TODO: Later we should be able to do that too.
        assert variable.isSharedTechnically() is False

        new_variable = outline_body.allocateTempVariable(
            temp_scope = temp_scope,
            name       = variable.getName()
        )

        # TODO: Lets update all at once maybe, it would take less visits.
        updateVariableUsage(
            clone,
            old_variable = variable,
            new_variable = new_variable
        )

        translation[variable.getName()] = new_variable

    statements = []

    if function_body.isExpressionClassBody():
        argument_names = ()
    else:
        argument_names = function_body.getParameters().getParameterNames()

    assert len(argument_names) == len(values), (argument_names, values)

    for argument_name, value in zip(argument_names, values):
        statements.append(
            StatementAssignmentVariable(
                variable   = translation[argument_name],
                source     = value,
                source_ref = call_source_ref,
            )
        )

    body = makeStatementsSequence(
        statements = (statements, clone),
        allow_none = False,
        source_ref = function_source_ref
    )
    outline_body.setBody(body)

    return outline_body
