#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Subscript related code generation.

There is special handling for integer indexes, which can be dealt with
much faster than general subscript lookups.
"""

from nuitka.States import states

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    generateExpressionsCode,
    promoteBorrowedValue,
    withBorrowedValueScope,
)
from .PythonAPICodes import (
    CArg,
    generateCAPIBoolCode,
    generateCAPIObjectCode,
    getCAPIErrorCode,
    makeArgDescFromExpression,
)


def generateAssignmentSubscriptCode(statement, emit, context):
    with withBorrowedValueScope(context):
        _generateAssignmentSubscriptCode(
            statement=statement, emit=emit, context=context
        )


def _generateAssignmentSubscriptCode(statement, emit, context):
    subscribed = statement.subnode_subscribed
    subscript = statement.subnode_subscript
    value = statement.subnode_source

    integer_subscript = subscript.isExpressionIntegerSubscript()

    value_name = context.allocateTempName("ass_subvalue")

    generateExpressionCode(
        to_name=value_name, expression=value, emit=emit, context=context
    )
    promoteBorrowedValue(
        value_name=value_name,
        later_expressions=(subscribed, subscript),
        emit=emit,
        context=context,
    )

    subscribed_name = context.allocateTempName("ass_subscribed")
    generateExpressionCode(
        to_name=subscribed_name, expression=subscribed, emit=emit, context=context
    )
    promoteBorrowedValue(
        value_name=subscribed_name,
        later_expressions=(subscript,),
        emit=emit,
        context=context,
    )

    subscript_name = context.allocateTempName("ass_subscript")
    generateExpressionCode(
        to_name=subscript_name, expression=subscript, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(
        value.getSourceReference()
        if states.is_full_compat
        else statement.getSourceReference()
    ):
        if integer_subscript:
            _getIntegerSubscriptAssignmentCode(
                subscribed_name=subscribed_name,
                subscript_name=subscript_name,
                subscript_value=subscript.getIndexValue(),
                value_name=value_name,
                emit=emit,
                context=context,
            )
        else:
            _getSubscriptAssignmentCode(
                target_name=subscribed_name,
                subscript_name=subscript_name,
                value_name=value_name,
                emit=emit,
                context=context,
            )


def generateDelSubscriptCode(statement, emit, context):
    with withBorrowedValueScope(context):
        _generateDelSubscriptCode(statement=statement, emit=emit, context=context)


def _generateDelSubscriptCode(statement, emit, context):
    subscribed = statement.subnode_subscribed
    subscript = statement.subnode_subscript

    target_name, subscript_name = generateExpressionsCode(
        expressions=(subscribed, subscript),
        names=("delsubscr_target", "delsubscr_subscript"),
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(
        subscript.getSourceReference()
        if states.is_full_compat
        else statement.getSourceReference()
    ):
        _getSubscriptDelCode(
            target_name=target_name,
            subscript_name=subscript_name,
            emit=emit,
            context=context,
        )


def generateSubscriptLookupCode(to_name, expression, emit, context):
    subscript = expression.subnode_subscript

    if subscript.isExpressionIntegerSubscript():
        capi = "LOOKUP_SUBSCRIPT_CONST"
        arg_desc = makeArgDescFromExpression(expression) + (
            CArg(subscript.getIndexValue()),
        )
    else:
        capi = "LOOKUP_SUBSCRIPT"
        arg_desc = makeArgDescFromExpression(expression)

    generateCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        tstate=True,
        arg_desc=arg_desc,
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateSubscriptLookupForUnpackCode(to_name, expression, emit, context):
    subscript = expression.subnode_subscript
    assert subscript.isExpressionIntegerSubscript(), subscript

    generateCAPIObjectCode(
        to_name=to_name,
        capi="LOOKUP_SUBSCRIPT_CONST_FOR_UNPACK",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression)
        + (
            CArg(subscript.getIndexValue()),
            CArg(expression.expected),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        fetched_exception=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateMatchSubscriptCheckCode(to_name, expression, emit, context):
    generateCAPIBoolCode(
        to_name=to_name,
        capi="MATCH_MAPPING_KEY",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        res_type="bool",
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def _getIntegerSubscriptAssignmentCode(
    subscribed_name, subscript_name, subscript_value, value_name, emit, context
):
    assert abs(subscript_value) < 2**31

    getCAPIErrorCode(
        capi="SET_SUBSCRIPT_CONST",
        arg_names=(
            "tstate",
            subscribed_name,
            subscript_name,
            subscript_value,
            value_name,
        ),
        may_raise=True,
        release_names=(subscribed_name, value_name),
        emit=emit,
        context=context,
    )


def _getSubscriptAssignmentCode(target_name, subscript_name, value_name, emit, context):
    getCAPIErrorCode(
        capi="SET_SUBSCRIPT",
        arg_names=("tstate", target_name, subscript_name, value_name),
        may_raise=True,
        release_names=(target_name, subscript_name, value_name),
        emit=emit,
        context=context,
    )


def _getSubscriptDelCode(target_name, subscript_name, emit, context):
    getCAPIErrorCode(
        capi="DEL_SUBSCRIPT",
        arg_names=(target_name, subscript_name),
        may_raise=True,
        release_names=(target_name, subscript_name),
        emit=emit,
        context=context,
    )


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
