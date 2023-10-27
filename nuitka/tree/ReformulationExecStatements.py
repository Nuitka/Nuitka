#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of "exec" statements

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    makeStatementConditional,
)
from nuitka.nodes.ConstantRefNodes import (
    ExpressionConstantNoneRef,
    makeConstantRefNode,
)
from nuitka.nodes.ExceptionNodes import StatementRaiseException
from nuitka.nodes.ExecEvalNodes import StatementExec, StatementLocalsDictSync
from nuitka.nodes.GlobalsLocalsNodes import ExpressionBuiltinGlobals
from nuitka.nodes.NodeMakingHelpers import makeExpressionBuiltinLocals
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.nodes.VariableReleaseNodes import makeStatementsReleaseVariables

from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import (
    buildNode,
    getKind,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
)


def wrapEvalGlobalsAndLocals(
    provider, globals_node, locals_node, temp_scope, source_ref
):
    """Wrap the locals and globals arguments for "eval".

    This is called from the outside, and when the node tree
    already exists.
    """

    locals_scope = provider.getLocalsScope()

    globals_keeper_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="globals", temp_type="object"
    )

    locals_keeper_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="locals", temp_type="object"
    )

    if locals_node is None:
        locals_node = ExpressionConstantNoneRef(source_ref=source_ref)

    if globals_node is None:
        globals_node = ExpressionConstantNoneRef(source_ref=source_ref)

    post_statements = []

    if provider.isExpressionClassBodyBase():
        post_statements.append(
            StatementLocalsDictSync(
                locals_scope=locals_scope,
                locals_arg=ExpressionTempVariableRef(
                    variable=locals_keeper_variable, source_ref=source_ref
                ),
                source_ref=source_ref.atInternal(),
            )
        )

    post_statements += makeStatementsReleaseVariables(
        variables=(globals_keeper_variable, locals_keeper_variable),
        source_ref=source_ref,
    )

    # The locals default is dependent on exec_mode, globals or locals.
    locals_default = ExpressionConditional(
        condition=ExpressionComparisonIs(
            left=ExpressionTempVariableRef(
                variable=globals_keeper_variable, source_ref=source_ref
            ),
            right=ExpressionConstantNoneRef(source_ref=source_ref),
            source_ref=source_ref,
        ),
        expression_no=ExpressionTempVariableRef(
            variable=globals_keeper_variable, source_ref=source_ref
        ),
        expression_yes=makeExpressionBuiltinLocals(
            locals_scope=locals_scope, source_ref=source_ref
        ),
        source_ref=source_ref,
    )

    pre_statements = [
        # First assign globals and locals temporary the values given.
        makeStatementAssignmentVariable(
            variable=globals_keeper_variable, source=globals_node, source_ref=source_ref
        ),
        makeStatementAssignmentVariable(
            variable=locals_keeper_variable, source=locals_node, source_ref=source_ref
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIs(
                left=ExpressionTempVariableRef(
                    variable=locals_keeper_variable, source_ref=source_ref
                ),
                right=ExpressionConstantNoneRef(source_ref=source_ref),
                source_ref=source_ref,
            ),
            yes_branch=makeStatementAssignmentVariable(
                variable=locals_keeper_variable,
                source=locals_default,
                source_ref=source_ref,
            ),
            no_branch=None,
            source_ref=source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIs(
                left=ExpressionTempVariableRef(
                    variable=globals_keeper_variable, source_ref=source_ref
                ),
                right=ExpressionConstantNoneRef(source_ref=source_ref),
                source_ref=source_ref,
            ),
            yes_branch=makeStatementAssignmentVariable(
                variable=globals_keeper_variable,
                source=ExpressionBuiltinGlobals(source_ref=source_ref),
                source_ref=source_ref,
            ),
            no_branch=None,
            source_ref=source_ref,
        ),
    ]

    return (
        ExpressionTempVariableRef(
            variable=globals_keeper_variable,
            source_ref=source_ref
            if globals_node is None
            else globals_node.getSourceReference(),
        ),
        ExpressionTempVariableRef(
            variable=locals_keeper_variable,
            source_ref=source_ref
            if locals_node is None
            else locals_node.getSourceReference(),
        ),
        makeStatementsSequence(pre_statements, False, source_ref),
        makeStatementsSequence(post_statements, False, source_ref),
    )


def buildExecNode(provider, node, source_ref):
    # "exec" statements, should only occur with Python2.

    # This is using many variables, due to the many details this is
    # dealing with. The locals and globals need to be dealt with in
    # temporary variables, and we need handling of indicators, so
    # that is just the complexity, pylint: disable=too-many-locals

    exec_globals = node.globals
    exec_locals = node.locals
    body = node.body

    # Handle exec(a,b,c) to be same as exec a, b, c
    if exec_locals is None and exec_globals is None and getKind(body) == "Tuple":
        parts = body.elts
        body = parts[0]

        if len(parts) > 1:
            exec_globals = parts[1]

            if len(parts) > 2:
                exec_locals = parts[2]
        else:
            return StatementRaiseException(
                exception_type=ExpressionBuiltinExceptionRef(
                    exception_name="TypeError", source_ref=source_ref
                ),
                exception_value=makeConstantRefNode(
                    constant="""\
exec: arg 1 must be a string, file, or code object""",
                    source_ref=source_ref,
                ),
                exception_trace=None,
                exception_cause=None,
                source_ref=source_ref,
            )

    temp_scope = provider.allocateTempScope("exec")

    locals_value = buildNode(provider, exec_locals, source_ref, True)

    if locals_value is None:
        locals_value = ExpressionConstantNoneRef(source_ref=source_ref)

    globals_value = buildNode(provider, exec_globals, source_ref, True)

    if globals_value is None:
        globals_value = ExpressionConstantNoneRef(source_ref=source_ref)

    source_code = buildNode(provider, body, source_ref)

    source_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="exec_source", temp_type="object"
    )

    globals_keeper_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="globals", temp_type="object"
    )

    locals_keeper_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="locals", temp_type="object"
    )

    plain_indicator_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="plain", temp_type="bool"
    )

    tried = (
        # First evaluate the source code expressions.
        makeStatementAssignmentVariable(
            variable=source_variable, source=source_code, source_ref=source_ref
        ),
        # Assign globals and locals temporary the values given, then fix it
        # up, taking note in the "plain" temporary variable, if it was an
        # "exec" statement with None arguments, in which case the copy back
        # will be necessary.
        makeStatementAssignmentVariable(
            variable=globals_keeper_variable,
            source=globals_value,
            source_ref=source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=locals_keeper_variable, source=locals_value, source_ref=source_ref
        ),
        makeStatementAssignmentVariable(
            variable=plain_indicator_variable,
            source=makeConstantRefNode(constant=False, source_ref=source_ref),
            source_ref=source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIs(
                left=ExpressionTempVariableRef(
                    variable=globals_keeper_variable, source_ref=source_ref
                ),
                right=ExpressionConstantNoneRef(source_ref=source_ref),
                source_ref=source_ref,
            ),
            yes_branch=makeStatementsSequenceFromStatements(
                makeStatementAssignmentVariable(
                    variable=globals_keeper_variable,
                    source=ExpressionBuiltinGlobals(source_ref=source_ref),
                    source_ref=source_ref,
                ),
                makeStatementConditional(
                    condition=ExpressionComparisonIs(
                        left=ExpressionTempVariableRef(
                            variable=locals_keeper_variable, source_ref=source_ref
                        ),
                        right=ExpressionConstantNoneRef(source_ref=source_ref),
                        source_ref=source_ref,
                    ),
                    yes_branch=makeStatementsSequenceFromStatements(
                        makeStatementAssignmentVariable(
                            variable=locals_keeper_variable,
                            source=makeExpressionBuiltinLocals(
                                locals_scope=provider.getLocalsScope(),
                                source_ref=source_ref,
                            ),
                            source_ref=source_ref,
                        ),
                        makeStatementAssignmentVariable(
                            variable=plain_indicator_variable,
                            source=makeConstantRefNode(
                                constant=True, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        ),
                    ),
                    no_branch=None,
                    source_ref=source_ref,
                ),
            ),
            no_branch=makeStatementsSequenceFromStatements(
                makeStatementConditional(
                    condition=ExpressionComparisonIs(
                        left=ExpressionTempVariableRef(
                            variable=locals_keeper_variable, source_ref=source_ref
                        ),
                        right=ExpressionConstantNoneRef(source_ref=source_ref),
                        source_ref=source_ref,
                    ),
                    yes_branch=makeStatementsSequenceFromStatement(
                        statement=makeStatementAssignmentVariable(
                            variable=locals_keeper_variable,
                            source=ExpressionTempVariableRef(
                                variable=globals_keeper_variable, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        )
                    ),
                    no_branch=None,
                    source_ref=source_ref,
                )
            ),
            source_ref=source_ref,
        ),
        makeTryFinallyStatement(
            provider=provider,
            tried=StatementExec(
                source_code=ExpressionTempVariableRef(
                    variable=source_variable, source_ref=source_ref
                ),
                globals_arg=ExpressionTempVariableRef(
                    variable=globals_keeper_variable, source_ref=source_ref
                ),
                locals_arg=ExpressionTempVariableRef(
                    variable=locals_keeper_variable, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            final=makeStatementConditional(
                condition=ExpressionComparisonIs(
                    left=ExpressionTempVariableRef(
                        variable=plain_indicator_variable, source_ref=source_ref
                    ),
                    right=makeConstantRefNode(constant=True, source_ref=source_ref),
                    source_ref=source_ref,
                ),
                yes_branch=StatementLocalsDictSync(
                    locals_scope=provider.getLocalsScope(),
                    locals_arg=ExpressionTempVariableRef(
                        variable=locals_keeper_variable, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                no_branch=None,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
    )

    return makeTryFinallyStatement(
        provider=provider,
        tried=tried,
        final=makeStatementsReleaseVariables(
            variables=(
                source_variable,
                globals_keeper_variable,
                locals_keeper_variable,
                plain_indicator_variable,
            ),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


# This is here, to make sure it can register, pylint: disable=W0611
import nuitka.optimizations.OptimizeBuiltinCalls  # isort:skip
