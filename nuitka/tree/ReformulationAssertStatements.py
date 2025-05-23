#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of assert statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ContainerMakingNodes import makeExpressionMakeTuple
from nuitka.nodes.ExceptionNodes import (
    StatementRaiseException,
    makeBuiltinMakeExceptionNode,
)
from nuitka.nodes.OperatorNodesUnary import ExpressionOperationNot
from nuitka.Options import hasPythonFlagNoAsserts
from nuitka.PythonVersions import python_version

from .TreeHelpers import buildNode


def buildAssertNode(provider, node, source_ref):
    # Build assert statements. These are re-formulated as described in the
    # Developer Manual too. They end up as conditional statement with raises of
    # AssertionError exceptions.

    # Underlying assumption:
    #
    # Assert x, y is the same as:
    # if not x:
    #     raise AssertionError, y

    # Therefore assert statements are really just conditional statements with a
    # static raise contained.
    #

    asserted_value_expression = buildNode(provider, node.test, source_ref)

    exception_value = buildNode(provider, node.msg, source_ref, True)

    if hasPythonFlagNoAsserts():
        return None

    if python_version < 0x3C0:
        if exception_value is not None and python_version >= 0x272:
            exception_value = makeExpressionMakeTuple(
                elements=(exception_value,), source_ref=source_ref
            )

        raise_statement = StatementRaiseException(
            exception_type=ExpressionBuiltinExceptionRef(
                exception_name="AssertionError", source_ref=source_ref
            ),
            exception_value=exception_value,
            exception_trace=None,
            exception_cause=None,
            source_ref=source_ref,
        )
    else:
        raise_statement = StatementRaiseException(
            exception_type=makeBuiltinMakeExceptionNode(
                exception_name="AssertionError",
                args=(exception_value,) if exception_value else (),
                for_raise=False,
                source_ref=source_ref,
            ),
            exception_value=None,
            exception_cause=None,
            exception_trace=None,
            source_ref=source_ref,
        )

    # May not need a condition.
    if asserted_value_expression.isCompileTimeConstant():
        asserted_value = asserted_value_expression.getCompileTimeConstant()

        if not asserted_value:
            return raise_statement

    return makeStatementConditional(
        condition=ExpressionOperationNot(
            operand=asserted_value_expression,
            source_ref=source_ref,
        ),
        yes_branch=raise_statement,
        no_branch=None,
        source_ref=source_ref,
    )


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
