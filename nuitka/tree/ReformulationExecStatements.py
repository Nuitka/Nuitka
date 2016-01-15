#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.BuiltinRefNodes import (
    ExpressionBuiltinAnonymousRef,
    ExpressionBuiltinExceptionRef
)
from nuitka.nodes.CallNodes import ExpressionCallEmpty
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    StatementConditional
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ExceptionNodes import StatementRaiseException
from nuitka.nodes.ExecEvalNodes import StatementExec, StatementLocalsDictSync
from nuitka.nodes.GlobalsLocalsNodes import (
    ExpressionBuiltinGlobals,
    ExpressionBuiltinLocals
)
from nuitka.nodes.TypeNodes import ExpressionBuiltinIsinstance

from .Helpers import (
    buildNode,
    getKind,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements
)
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def _getLocalsClassNode(provider):
    if provider.isCompiledPythonModule():
        return ExpressionBuiltinGlobals
    else:
        return ExpressionBuiltinLocals


def wrapEvalGlobalsAndLocals(provider, globals_node, locals_node,
                             temp_scope, source_ref):
    """ Wrap the locals and globals arguments for "eval".

        This is called from the outside, and when the node tree
        already exists.
    """

    globals_keeper_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "globals"
    )

    locals_keeper_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "locals"
    )

    if locals_node is None:
        locals_node = ExpressionConstantRef(
            constant   = None,
            source_ref = source_ref
        )

    if globals_node is None:
        globals_node = ExpressionConstantRef(
            constant   = None,
            source_ref = source_ref
        )

    post_statements = []

    if provider.isExpressionClassBody():
        post_statements.append(
            StatementLocalsDictSync(
                locals_arg = ExpressionTempVariableRef(
                    variable   = locals_keeper_variable,
                    source_ref = source_ref,
                ),
                source_ref = source_ref.atInternal()
            )
        )

    post_statements += [
        StatementReleaseVariable(
            variable   = globals_keeper_variable,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = locals_keeper_variable,
            source_ref = source_ref
        )
    ]

    # The locals default is dependent on exec_mode, globals or locals.
    locals_default = ExpressionConditional(
        condition      = ExpressionComparisonIs(
            left       = ExpressionTempVariableRef(
                variable   = globals_keeper_variable,
                source_ref = source_ref
            ),
            right      = ExpressionConstantRef(
                constant   = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        expression_no  = ExpressionTempVariableRef(
            variable   = globals_keeper_variable,
            source_ref = source_ref
        ),
        expression_yes = _getLocalsClassNode(provider)(
            source_ref = source_ref
        ),
        source_ref     = source_ref
    )

    pre_statements = [
        # First assign globals and locals temporary the values given.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = globals_keeper_variable,
                source_ref = source_ref
            ),
            source       = globals_node,
            source_ref   = source_ref,
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = locals_keeper_variable,
                source_ref = source_ref
            ),
            source       = locals_node,
            source_ref   = source_ref,
        ),
        StatementConditional(
            condition  = ExpressionComparisonIs(
                left       = ExpressionTempVariableRef(
                    variable   = locals_keeper_variable,
                    source_ref = source_ref
                ),
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = makeStatementsSequenceFromStatement(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = locals_keeper_variable,
                        source_ref = source_ref
                    ),
                    source       = locals_default,
                    source_ref   = source_ref,
                )
            ),
            no_branch  = None,
            source_ref = source_ref
        ),
        StatementConditional(
            condition  = ExpressionComparisonIs(
                left       = ExpressionTempVariableRef(
                    variable   = globals_keeper_variable,
                    source_ref = source_ref
                ),
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = makeStatementsSequenceFromStatement(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = globals_keeper_variable,
                        source_ref = source_ref
                    ),
                    source       = ExpressionBuiltinGlobals(
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref,
                )
            ),
            no_branch  = None,
            source_ref = source_ref
        )
    ]

    return (
        ExpressionTempVariableRef(
            variable   = globals_keeper_variable,
            source_ref = source_ref
              if globals_node is None else
            globals_node.getSourceReference()

        ),
        ExpressionTempVariableRef(
            variable   = locals_keeper_variable,
            source_ref = source_ref
              if locals_node is None else
            locals_node.getSourceReference()
        ),
        makeStatementsSequence(pre_statements, False, source_ref),
        makeStatementsSequence(post_statements, False, source_ref)
    )


def buildExecNode(provider, node, source_ref):
    # "exec" statements, should only occur with Python2.

    # This is using many variables, due to the many details this is
    # dealing with. The locals and globals need to be dealt with in
    # temporary variables, and we need handling of indicators, so
    # that is just the complexity, pylint: disable=R0914

    exec_globals = node.globals
    exec_locals = node.locals
    body = node.body

    orig_globals = exec_globals

    # Handle exec(a,b,c) to be same as exec a, b, c
    if exec_locals is None and exec_globals is None and \
       getKind(body) == "Tuple":
        parts = body.elts
        body  = parts[0]

        if len(parts) > 1:
            exec_globals = parts[1]

            if len(parts) > 2:
                exec_locals = parts[2]
        else:
            return StatementRaiseException(
                exception_type  = ExpressionBuiltinExceptionRef(
                    exception_name = "TypeError",
                    source_ref     = source_ref
                ),
                exception_value = ExpressionConstantRef(
                    constant   = """\
exec: arg 1 must be a string, file, or code object""",
                    source_ref = source_ref
                ),
                exception_trace = None,
                exception_cause = None,
                source_ref      = source_ref
            )

    if not provider.isCompiledPythonModule():
        provider.markAsExecContaining()

        if orig_globals is None:
            provider.markAsUnqualifiedExecContaining(source_ref)

    temp_scope = provider.allocateTempScope("exec")

    locals_value  = buildNode(provider, exec_locals, source_ref, True)

    if locals_value is None:
        locals_value = ExpressionConstantRef(
            constant   = None,
            source_ref = source_ref
        )

    globals_value = buildNode(provider, exec_globals, source_ref, True)

    if globals_value is None:
        globals_value = ExpressionConstantRef(
            constant   = None,
            source_ref = source_ref
        )

    source_code = buildNode(provider, body, source_ref)

    source_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "exec_source"
    )

    globals_keeper_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "globals"
    )

    locals_keeper_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "locals"
    )

    plain_indicator_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "plain"
    )

    tried = (
        # First evaluate the source code expressions.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = source_variable,
                source_ref = source_ref
            ),
            source       = source_code,
            source_ref   = source_ref
        ),
        # Assign globals and locals temporary the values given, then fix it
        # up, taking note in the "plain" temporary variable, if it was an
        # "exec" statement with None arguments, in which case the copy back
        # will be necessary.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = globals_keeper_variable,
                source_ref = source_ref
            ),
            source       = globals_value,
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = locals_keeper_variable,
                source_ref = source_ref
            ),
            source       = locals_value,
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = plain_indicator_variable,
                source_ref = source_ref
            ),
            source       = ExpressionConstantRef(
                constant   = False,
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementConditional(
            condition  = ExpressionComparisonIs(
                left       = ExpressionTempVariableRef(
                    variable   = globals_keeper_variable,
                    source_ref = source_ref
                ),
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = makeStatementsSequenceFromStatements(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = globals_keeper_variable,
                        source_ref = source_ref
                    ),
                    source       = ExpressionBuiltinGlobals(
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref,
                ),
                StatementConditional(
                    condition  = ExpressionComparisonIs(
                        left       = ExpressionTempVariableRef(
                            variable   = locals_keeper_variable,
                            source_ref = source_ref
                        ),
                        right      = ExpressionConstantRef(
                            constant   = None,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_branch = makeStatementsSequenceFromStatements(
                        StatementAssignmentVariable(
                            variable_ref = ExpressionTargetTempVariableRef(
                                variable   = locals_keeper_variable,
                                source_ref = source_ref
                            ),
                            source       = _getLocalsClassNode(provider)(
                                source_ref = source_ref
                            ),
                            source_ref   = source_ref,
                        ),
                        StatementAssignmentVariable(
                            variable_ref = ExpressionTargetTempVariableRef(
                                variable   = plain_indicator_variable,
                                source_ref = source_ref
                            ),
                            source       = ExpressionConstantRef(
                                constant   = True,
                                source_ref = source_ref
                            ),
                            source_ref   = source_ref,
                        )
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                ),
            ),
            no_branch  = makeStatementsSequenceFromStatements(
                StatementConditional(
                    condition  = ExpressionComparisonIs(
                        left       = ExpressionTempVariableRef(
                            variable   = locals_keeper_variable,
                            source_ref = source_ref
                        ),
                        right      = ExpressionConstantRef(
                            constant   = None,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_branch = makeStatementsSequenceFromStatement(
                        statement = StatementAssignmentVariable(
                            variable_ref = ExpressionTargetTempVariableRef(
                                variable   = locals_keeper_variable,
                                source_ref = source_ref
                            ),
                            source       = ExpressionTempVariableRef(
                                variable   = globals_keeper_variable,
                                source_ref = source_ref
                            ),
                            source_ref   = source_ref,
                        )
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            ),
            source_ref = source_ref
        ),
        # Source needs some special treatment for not done for "eval", if it's a
        # file object, then  must be read.
        StatementConditional(
            condition  = ExpressionBuiltinIsinstance(
                instance   = ExpressionTempVariableRef(
                    variable   = source_variable,
                    source_ref = source_ref
                ),
                classes    = ExpressionBuiltinAnonymousRef(
                    builtin_name = "file",
                    source_ref   = source_ref,
                ),
                source_ref = source_ref
            ),
            yes_branch = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = source_variable,
                        source_ref = source_ref
                    ),
                    source       = ExpressionCallEmpty(
                        called     = ExpressionAttributeLookup(
                            source         = ExpressionTempVariableRef(
                                variable   = source_variable,
                                source_ref = source_ref
                            ),
                            attribute_name = "read",
                            source_ref     = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref
                )
            ),
            no_branch  = None,
            source_ref = source_ref
        ),
        makeTryFinallyStatement(
            provider   = provider,
            tried      = StatementExec(
                source_code = ExpressionTempVariableRef(
                    variable   = source_variable,
                    source_ref = source_ref
                ),
                globals_arg = ExpressionTempVariableRef(
                    variable   = globals_keeper_variable,
                    source_ref = source_ref
                ),
                locals_arg  = ExpressionTempVariableRef(
                    variable   = locals_keeper_variable,
                    source_ref = source_ref
                ),
                source_ref  = source_ref
            ),
            final      = StatementConditional(
                condition  = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = plain_indicator_variable,
                        source_ref = source_ref
                    ),
                    right      = ExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = makeStatementsSequenceFromStatement(
                    statement = StatementLocalsDictSync(
                        locals_arg = ExpressionTempVariableRef(
                            variable   = locals_keeper_variable,
                            source_ref = source_ref,
                        ),
                        source_ref = source_ref.atInternal()
                    )
                ),
                no_branch  = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    final = (
        StatementReleaseVariable(
            variable   = source_variable,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = globals_keeper_variable,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = locals_keeper_variable,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = plain_indicator_variable,
            source_ref = source_ref
        ),
    )

    return makeTryFinallyStatement(
        provider   = provider,
        tried      = tried,
        final      = final,
        source_ref = source_ref
    )

# This is here, to make sure it can register, pylint: disable=W0611
import nuitka.optimizations.OptimizeBuiltinCalls # isort:skip @UnusedImport
