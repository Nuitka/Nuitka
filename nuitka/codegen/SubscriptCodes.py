#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Subscript related code generation.

There is special handling for integer indexes, which can be dealt with
much faster than general subscript lookups.
"""

from nuitka import Options

from .CodeHelpers import (
    generateChildExpressionCode,
    generateExpressionCode,
    generateExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes


def _decideIntegerSubscript(subscript):
    if subscript.isExpressionConstantRef():
        if subscript.isIndexConstant():
            constant_value = subscript.getIndexValue()

            if abs(constant_value) < 2**31:
                return constant_value, True

    return None, False


def generateAssignmentSubscriptCode(statement, emit, context):
    subscribed = statement.subnode_subscribed
    subscript = statement.subnode_subscript
    value = statement.subnode_source

    subscript_constant, integer_subscript = _decideIntegerSubscript(subscript)

    value_name = context.allocateTempName("ass_subvalue")

    generateExpressionCode(
        to_name=value_name, expression=value, emit=emit, context=context
    )

    subscribed_name = context.allocateTempName("ass_subscribed")
    generateExpressionCode(
        to_name=subscribed_name, expression=subscribed, emit=emit, context=context
    )

    subscript_name = context.allocateTempName("ass_subscript")
    generateExpressionCode(
        to_name=subscript_name, expression=subscript, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(
        value.getSourceReference()
        if Options.is_full_compat
        else statement.getSourceReference()
    ):
        if integer_subscript:
            _getIntegerSubscriptAssignmentCode(
                subscribed_name=subscribed_name,
                subscript_name=subscript_name,
                subscript_value=subscript_constant,
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
        if Options.is_full_compat
        else statement.getSourceReference()
    ):
        _getSubscriptDelCode(
            target_name=target_name,
            subscript_name=subscript_name,
            emit=emit,
            context=context,
        )


def generateSubscriptLookupCode(to_name, expression, emit, context):
    subscribed = expression.subnode_expression
    subscript = expression.subnode_subscript

    subscribed_name = generateChildExpressionCode(
        expression=subscribed, emit=emit, context=context
    )

    subscript_name = generateChildExpressionCode(
        expression=subscript, emit=emit, context=context
    )

    subscript_constant, integer_subscript = _decideIntegerSubscript(subscript)

    with withObjectCodeTemporaryAssignment(
        to_name, "subscript_result", expression, emit, context
    ) as value_name:

        if integer_subscript:
            _getIntegerSubscriptLookupCode(
                to_name=value_name,
                subscribed_name=subscribed_name,
                subscript_name=subscript_name,
                subscript_value=subscript_constant,
                emit=emit,
                context=context,
            )
        else:
            _getSubscriptLookupCode(
                to_name=value_name,
                subscribed_name=subscribed_name,
                subscript_name=subscript_name,
                emit=emit,
                context=context,
            )


def generateSubscriptCheckCode(to_name, expression, emit, context):
    subscribed = expression.subnode_expression
    subscript = expression.subnode_subscript

    subscribed_name = generateChildExpressionCode(
        expression=subscribed, emit=emit, context=context
    )

    subscript_name = generateChildExpressionCode(
        expression=subscript, emit=emit, context=context
    )

    subscript_constant, integer_subscript = _decideIntegerSubscript(subscript)

    res_name = context.getBoolResName()

    if integer_subscript:
        emit(
            "%s = HAS_SUBSCRIPT_CONST(%s, %s, %s);"
            % (res_name, subscribed_name, subscript_name, subscript_constant)
        )
    else:
        emit(
            "%s = HAS_SUBSCRIPT(%s, %s);" % (res_name, subscribed_name, subscript_name)
        )

    getReleaseCodes((subscript_name, subscribed_name), emit, context)

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name,
        condition=res_name,
        emit=emit,
    )


def _getIntegerSubscriptLookupCode(
    to_name, subscribed_name, subscript_name, subscript_value, emit, context
):
    emit(
        "%s = LOOKUP_SUBSCRIPT_CONST(%s, %s, %s);"
        % (to_name, subscribed_name, subscript_name, subscript_value)
    )

    getErrorExitCode(
        check_name=to_name,
        release_names=(subscribed_name, subscript_name),
        emit=emit,
        context=context,
    )

    context.addCleanupTempName(to_name)


def _getSubscriptLookupCode(to_name, subscript_name, subscribed_name, emit, context):
    emit("%s = LOOKUP_SUBSCRIPT(%s, %s);" % (to_name, subscribed_name, subscript_name))

    getErrorExitCode(
        check_name=to_name,
        release_names=(subscribed_name, subscript_name),
        emit=emit,
        context=context,
    )

    context.addCleanupTempName(to_name)


def _getIntegerSubscriptAssignmentCode(
    subscribed_name, subscript_name, subscript_value, value_name, emit, context
):
    assert abs(subscript_value) < 2**31

    res_name = context.allocateTempName("ass_subscript_res", "int")

    emit(
        "%s = SET_SUBSCRIPT_CONST(%s, %s, %s, %s);"
        % (res_name, subscribed_name, subscript_name, subscript_value, value_name)
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(subscribed_name, value_name),
        emit=emit,
        context=context,
    )


def _getSubscriptAssignmentCode(target_name, subscript_name, value_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_SUBSCRIPT(%s, %s, %s);"
        % (res_name, target_name, subscript_name, value_name)
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(target_name, subscript_name, value_name),
        emit=emit,
        context=context,
    )


def _getSubscriptDelCode(target_name, subscript_name, emit, context):
    res_name = context.getBoolResName()

    emit("%s = DEL_SUBSCRIPT(%s, %s);" % (res_name, target_name, subscript_name))

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(target_name, subscript_name),
        emit=emit,
        context=context,
    )
