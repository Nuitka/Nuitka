#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""In-lining of functions.

Done by assigning the argument values to variables, and producing an outline
from the in-lined function.
"""

from nuitka.nodes.FunctionNodes import updateFunctionBodyReferences
from nuitka.nodes.OutlineNodes import ExpressionOutlineFunction
from nuitka.nodes.ReturnNodes import StatementReturnNone
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.tree.Extractions import updateVariableUsage
from nuitka.tree.ReformulationTryFinallyStatements import (
    makeTryFinallyReleaseStatement,
)
from nuitka.tree.TreeHelpers import (
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
)
from nuitka.Variables import LocalVariable


def convertFunctionCallToOutline(provider, function_body, values, call_source_ref):
    # Many details to translate for the inlined scope, pylint: disable=too-many-locals
    function_source_ref = function_body.getSourceReference()

    outline_body = ExpressionOutlineFunction(
        provider=provider, name="inline", source_ref=call_source_ref
    )

    if function_body.subnode_body is None:
        clone = makeStatementsSequenceFromStatement(
            statement=StatementReturnNone(source_ref=function_source_ref)
        )
    else:
        clone = function_body.subnode_body.makeClone()

    parameter_variables = function_body.getParameters().getAllVariables()
    assert len(parameter_variables) == len(values), (parameter_variables, values)

    # Parameters of the called function become ordinary local variables of the
    # outline, assigned from the call argument expressions below.
    variable_translations = {}
    for parameter_variable in parameter_variables:
        variable_translations[parameter_variable] = LocalVariable(
            owner=outline_body, variable_name=parameter_variable.getName()
        )

    outline_body.locals_scope, variable_translations = (
        function_body.locals_scope.makeCloneWithVariableTranslations(
            new_owner=outline_body,
            variable_translations=variable_translations,
        )
    )

    for parameter_variable in parameter_variables:
        outline_body.locals_scope.local_variables[parameter_variable.getName()] = (
            variable_translations[parameter_variable]
        )

    for temp_variable in function_body.getTempVariables(None):
        variable_translations[temp_variable] = outline_body.allocateTempVariable(
            temp_scope=None,
            name=temp_variable.getName(),
            temp_type=temp_variable.getVariableType(),
            late=True,
        )

    for taken_variable in function_body.taken:
        outline_body.taken.add(
            variable_translations.get(taken_variable, taken_variable)
        )

    updateVariableUsage(
        provider=clone,
        old_locals_scope=function_body.locals_scope,
        new_locals_scope=outline_body.locals_scope,
        variable_translations=variable_translations,
    )

    updateFunctionBodyReferences(
        provider=clone,
        old_provider=function_body,
        variable_translations=variable_translations,
        code_name_translations={
            function_body.getCodeName(): outline_body.getCodeName()
        },
    )

    statements = []

    for parameter_variable, value in zip(parameter_variables, values):
        statements.append(
            makeStatementAssignmentVariable(
                variable=variable_translations[parameter_variable],
                source=value,
                source_ref=call_source_ref,
            )
        )

    body = makeStatementsSequence(
        statements=(statements, clone), source_ref=function_source_ref
    )

    auto_releases = function_body.getFunctionVariablesWithAutoReleases()

    if auto_releases:
        body = makeStatementsSequenceFromStatement(
            statement=makeTryFinallyReleaseStatement(
                provider=outline_body,
                tried=body,
                variables=tuple(
                    variable_translations[variable] for variable in auto_releases
                ),
                source_ref=function_source_ref,
            )
        )

    outline_body.setChildBody(body)

    return outline_body


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
