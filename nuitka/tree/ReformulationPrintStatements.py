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
""" Reformulation of print statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
)
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinStr
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ImportNodes import ExpressionImportModuleHard
from nuitka.nodes.PrintNodes import StatementPrintNewline, StatementPrintValue
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)

from .Helpers import (
    buildNode,
    buildNodeList,
    makeStatementsSequenceFromStatement,
    makeTryFinallyStatement
)


def buildPrintNode(provider, node, source_ref):
    # "print" statements, should only occur with Python2.

    def wrapValue(value):
        if value.isExpressionConstantRef():
            str_value = value.getStrValue()

            if str_value is not None:
                return str_value

        return ExpressionBuiltinStr(
            value      = value,
            source_ref = value.getSourceReference()
        )

    if node.dest is not None:
        temp_scope = provider.allocateTempScope("print")

        tmp_target_variable = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "target"
        )

        target_default_statement = StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_target_variable,
                source_ref = source_ref
            ),
            source       = ExpressionImportModuleHard(
                module_name = "sys",
                import_name = "stdout",
                source_ref  = source_ref
            ),
            source_ref   = source_ref
        )

        statements = [
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_target_variable,
                    source_ref = source_ref
                ),
                source       = buildNode(
                    provider   = provider,
                    node       = node.dest,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            ),
            StatementConditional(
                condition  = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_target_variable,
                        source_ref = source_ref
                    ),
                    right      = ExpressionConstantRef(
                        constant   = None,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = makeStatementsSequenceFromStatement(
                    statement = target_default_statement
                ),
                no_branch  = None,
                source_ref = source_ref
            )
        ]

    values = buildNodeList(
        provider   = provider,
        nodes      = node.values,
        source_ref = source_ref
    )

    values = [
        wrapValue(value)
        for value in
        values
    ]

    if node.dest is not None:
        print_statements = [
            StatementPrintValue(
                dest       = ExpressionTempVariableRef(
                    variable   = tmp_target_variable,
                    source_ref = source_ref
                ),
                value      = value,
                source_ref = source_ref
            )
            for value in values
        ]

        if node.nl:
            print_statements.append(
                StatementPrintNewline(
                    dest       = ExpressionTempVariableRef(
                        variable   = tmp_target_variable,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            )

        statements.append(
            makeTryFinallyStatement(
                tried      = print_statements,
                final      = StatementDelVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_target_variable,
                        source_ref = source_ref
                    ),
                    tolerant     = False,
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            )
        )
    else:
        statements = [
            StatementPrintValue(
                dest       = None,
                value      = value,
                source_ref = source_ref
            )
            for value in values
        ]

        if node.nl:
            statements.append(
                StatementPrintNewline(
                    dest       = None,
                    source_ref = source_ref
                )
            )

    return StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )
