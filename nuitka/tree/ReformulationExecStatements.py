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
""" Reformulation of exec statements

Consult the developmer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
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
from nuitka.nodes.ExecEvalNodes import StatementExec
from nuitka.nodes.GlobalsLocalsNodes import (
    ExpressionBuiltinGlobals,
    ExpressionBuiltinLocals
)
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.TryNodes import StatementTryFinally
from nuitka.nodes.TypeNodes import ExpressionBuiltinIsinstance
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)

from .Helpers import (
    buildNode,
    getKind,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement
)


def wrapEvalGlobalsAndLocals(provider, globals_node, locals_node,
                             temp_scope, source_ref):
    """ Wrap the locals and globals arguments for eval and exec.

        For eval, this is called from the outside, and when the node tree
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

    post_statements = [
        StatementDelVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = globals_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            tolerant     = False,
            source_ref   = source_ref
        ),
        StatementDelVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = locals_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            tolerant     = False,
            source_ref   = source_ref
        )
    ]

    # The locals default is dependant on exec_mode, globals or locals.
    locals_default = ExpressionConditional(
        condition = ExpressionComparisonIs(
            left       = ExpressionTempVariableRef(
                variable   = globals_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            right      = ExpressionConstantRef(
                constant   = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        no_expression  = ExpressionTempVariableRef(
            variable   = globals_keeper_variable.makeReference(
                provider
            ),
            source_ref = source_ref
        ),
        yes_expression = ExpressionBuiltinLocals(
            source_ref = source_ref
        ),
        source_ref     = source_ref
    )

    pre_statements = [
        # First assign globals and locals temporary the values given.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = globals_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            source       = globals_node,
            source_ref   = source_ref,
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = locals_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            source       = locals_node,
            source_ref   = source_ref,
        ),
        StatementConditional(
            condition      = ExpressionComparisonIs(
                left       = ExpressionTempVariableRef(
                    variable   = locals_keeper_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch     = makeStatementsSequenceFromStatement(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = locals_keeper_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    source       = locals_default,
                    source_ref   = source_ref,
                )
            ),
            no_branch      = None,
            source_ref     = source_ref
        ),
        StatementConditional(
            condition      = ExpressionComparisonIs(
                left       = ExpressionTempVariableRef(
                    variable   = globals_keeper_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch     = makeStatementsSequenceFromStatement(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = globals_keeper_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    source       = ExpressionBuiltinGlobals(
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref,
                )
            ),
            no_branch      = None,
            source_ref     = source_ref
        )
    ]

    return (
        ExpressionTempVariableRef(
            variable   = globals_keeper_variable.makeReference(
                provider
            ),
            source_ref = source_ref
              if globals_node is None else
            globals_node.getSourceReference()

        ),
        ExpressionTempVariableRef(
            variable   = locals_keeper_variable.makeReference(
                provider
            ),
            source_ref = source_ref
              if locals_node is None else
            locals_node.getSourceReference()
        ),
        makeStatementsSequence(pre_statements, False, source_ref),
        makeStatementsSequence(post_statements, False, source_ref)
    )

def buildExecNode(provider, node, source_ref):
    # "exec" statements, should only occur with Python2.

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
                exception_type = ExpressionBuiltinExceptionRef(
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

    if provider.isExpressionFunctionBody():
        provider.markAsExecContaining()

        if orig_globals is None:
            provider.markAsUnqualifiedExecContaining(source_ref)

    temp_scope = provider.allocateTempScope("exec")

    globals_ref, locals_ref, tried, final = wrapEvalGlobalsAndLocals(
        provider     = provider,
        globals_node = buildNode(provider, exec_globals, source_ref, True),
        locals_node  = buildNode(provider, exec_locals, source_ref, True),
        temp_scope   = temp_scope,
        source_ref   = source_ref
    )

    source_code = buildNode(provider, body, source_ref)

    source_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "source"
    )

    # Source needs some special treatment for eval, if it's a string, it
    # must be stripped.
    file_fixup = [
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = source_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            source = ExpressionCallEmpty(
                called = ExpressionAttributeLookup(
                    expression     = ExpressionTempVariableRef(
                        variable   = source_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    attribute_name = "read",
                    source_ref     = source_ref
                ),
                source_ref   = source_ref
            ),
            source_ref = source_ref
        )
    ]

    statements = (
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = source_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            source       = source_code,
            source_ref   = source_ref,
        ),
        StatementConditional(
            condition = ExpressionBuiltinIsinstance(
                cls = ExpressionBuiltinAnonymousRef(
                    builtin_name = "file",
                    source_ref   = source_ref,
                ),
                instance = ExpressionTempVariableRef(
                    variable   = source_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = StatementsSequence(
                statements = file_fixup,
                source_ref = source_ref
            ),
            no_branch  = None,
            source_ref = source_ref
        ),
        StatementExec(
            source_code = ExpressionTempVariableRef(
                variable   = source_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            globals_arg = globals_ref,
            locals_arg  = locals_ref,
            source_ref  = source_ref
        )
    )

    tried.setChild(
        "statements",
        tried.getStatements() + statements
    )

    final.setStatements(
        final.getStatements() + (
            StatementDelVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = source_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                tolerant     = True,
                source_ref   = source_ref
            ),
        )
    )

    return StatementTryFinally(
        tried      = tried,
        final      = final,
        public_exc = False,
        source_ref = source_ref
    )

# This is here, to make sure it can register, pylint: disable=W0611
import nuitka.optimizations.OptimizeBuiltinCalls # isort:skip
