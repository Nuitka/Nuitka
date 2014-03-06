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

from nuitka.nodes.ExceptionNodes import StatementRaiseException
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ExecEvalNodes import StatementExec

from nuitka.nodes.ConditionalNodes import ExpressionConditional
from nuitka.nodes.KeeperNodes import (
    ExpressionAssignmentTempKeeper,
    ExpressionTempKeeperRef
)
from nuitka.nodes.GlobalsLocalsNodes import (
    ExpressionBuiltinGlobals,
    ExpressionBuiltinLocals,
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs

from .Helpers import (
    buildNode,
    getKind
)


def wrapEvalGlobalsAndLocals( provider, globals_node, locals_node, exec_mode,
                              source_ref ):
    """ Wrap the locals and globals arguments for eval and exec.

        For eval, this is called from the outside, and when the node tree
        already exists.
    """

    if globals_node is not None:
        global_keeper_variable = provider.allocateTempKeeperVariable()
        tmp_global_assign = ExpressionAssignmentTempKeeper(
            variable   = global_keeper_variable.makeReference( provider ),
            source     = globals_node,
            source_ref = source_ref
        )

        globals_wrap = ExpressionConditional(
            condition      = ExpressionComparisonIs(
                left       = tmp_global_assign,
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            no_expression  = ExpressionTempKeeperRef(
                variable   = global_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            yes_expression = ExpressionBuiltinGlobals(
                source_ref = source_ref
            ),
            source_ref     = source_ref
        )
    else:
        globals_wrap = ExpressionBuiltinGlobals(
            source_ref = source_ref
        )

    if locals_node is not None:
        local_keeper_variable = provider.allocateTempKeeperVariable()
        tmp_local_assign = ExpressionAssignmentTempKeeper(
            variable   = local_keeper_variable.makeReference( provider ),
            source     = locals_node,
            source_ref = source_ref
        )

        if exec_mode:
            locals_fallback = ExpressionBuiltinLocals(
                source_ref = source_ref
            )
        else:
            locals_fallback = ExpressionConditional(
            condition      = ExpressionComparisonIs(
                left       = ExpressionTempKeeperRef(
                    variable   = global_keeper_variable.makeReference(
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
            no_expression  = ExpressionTempKeeperRef(
                variable   = global_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            yes_expression = ExpressionBuiltinLocals(
                source_ref = source_ref
            ),
            source_ref     = source_ref
        )

        locals_wrap = ExpressionConditional(
            condition = ExpressionComparisonIs(
                left       = tmp_local_assign,
                right      = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            no_expression  = ExpressionTempKeeperRef(
                variable   = local_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            yes_expression = locals_fallback,
            source_ref     = source_ref
        )
    else:
        if globals_node is None:
            locals_wrap = ExpressionBuiltinLocals(
                source_ref = source_ref
            )
        else:
            locals_wrap = ExpressionTempKeeperRef(
                variable   = global_keeper_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            )

    return globals_wrap, locals_wrap

def buildExecNode(provider, node, source_ref):
    # "exec" statements, should only occur with Python2.

    exec_globals = node.globals
    exec_locals = node.locals
    body = node.body

    orig_globals = exec_globals

    # Handle exec(a,b,c) to be same as exec a, b, c
    if exec_locals is None and exec_globals is None and \
       getKind( body ) == "Tuple":
        parts = body.elts
        body  = parts[0]

        if len( parts ) > 1:
            exec_globals = parts[1]

            if len( parts ) > 2:
                exec_locals = parts[2]
        else:
            return StatementRaiseException(
                exception_type = ExpressionBuiltinExceptionRef(
                    exception_name = "TypeError",
                    source_ref     = source_ref
                ),
                exception_value = ExpressionConstantRef(
                    constant   = "exec: arg 1 must be a string, file, or code object",
                    source_ref = source_ref
                ),
                exception_trace = None,
                exception_cause = None,
                source_ref      = source_ref
            )

    if provider.isExpressionFunctionBody():
        provider.markAsExecContaining()

        if orig_globals is None:
            provider.markAsUnqualifiedExecContaining( source_ref )

    globals_wrap, locals_wrap = wrapEvalGlobalsAndLocals(
        provider     = provider,
        globals_node = buildNode( provider, exec_globals, source_ref, True ),
        locals_node  = buildNode( provider, exec_locals, source_ref, True ),
        exec_mode    = True,
        source_ref   = source_ref
    )

    return StatementExec(
        source_code = buildNode( provider, body, source_ref ),
        globals_arg = globals_wrap,
        locals_arg  = locals_wrap,
        source_ref  = source_ref
    )

# This is here, to make sure it can register, pylint: disable=W0611
import nuitka.optimizations.OptimizeBuiltinCalls
