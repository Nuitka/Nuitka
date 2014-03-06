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
""" Reformulation of assert statements.

Consult the developmer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""
from nuitka import Utils

from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ExceptionNodes import (
    ExpressionBuiltinMakeException,
    StatementRaiseException
)
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.OperatorNodes import ExpressionOperationNOT
from nuitka.nodes.ConditionalNodes import StatementConditional

from .Helpers import buildNode

def buildAssertNode(provider, node, source_ref):
    # Build assert statements. These are re-formulated as described in the
    # developer manual too. They end up as conditional statement with raises of
    # AssertionError exceptions.

    # Underlying assumption:
    #
    # Assert x, y is the same as:
    # if not x:
    #     raise AssertionError, y

    # Therefore assert statements are really just conditional statements with a
    # static raise contained.
    #
    # Starting with CPython2.7, it is, which means the creation of the exception
    # object is no more delayed:
    # if not x:
    #     raise AssertionError( y )

    if Utils.python_version < 270 or node.msg is None:
        raise_statement = StatementRaiseException(
            exception_type  = ExpressionBuiltinExceptionRef(
                exception_name = "AssertionError",
                source_ref     = source_ref
                ),
            exception_value = buildNode( provider, node.msg, source_ref, True ),
            exception_trace = None,
            exception_cause = None,
            source_ref      = source_ref
        )
    else:
        raise_statement = StatementRaiseException(
            exception_type  =  ExpressionBuiltinMakeException(
                exception_name = "AssertionError",
                args           = (
                    buildNode( provider, node.msg, source_ref, True ),
                ),
                source_ref     = source_ref
            ),
            exception_value = None,
            exception_trace = None,
            exception_cause = None,
            source_ref      = source_ref
        )

    return StatementConditional(
        condition  = ExpressionOperationNOT(
            operand    = buildNode( provider, node.test, source_ref ),
            source_ref = source_ref
        ),
        yes_branch = StatementsSequence(
            statements = (
                raise_statement,
            ),
            source_ref = source_ref
        ),
        no_branch  = None,
        source_ref = source_ref
    )
