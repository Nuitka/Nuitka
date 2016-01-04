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
""" Subscript related code generation.

There is special handling for integer indexes, which can be dealt with
much faster than general subscript lookups.
"""

from nuitka import Options
from nuitka.Constants import isIndexConstant

from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes
from .Helpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    generateExpressionsCode
)


def generateAssignmentSubscriptCode(statement, emit, context):
    subscribed      = statement.getSubscribed()
    subscript       = statement.getSubscript()
    value           = statement.getAssignSource()

    integer_subscript = False
    if subscript.isExpressionConstantRef():
        constant = subscript.getConstant()

        if isIndexConstant(constant):
            constant_value = int(constant)

            if abs(constant_value) < 2**31:
                integer_subscript = True

    value_name = context.allocateTempName("ass_subvalue")

    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    subscribed_name = context.allocateTempName("ass_subscribed")
    generateExpressionCode(
        to_name    = subscribed_name,
        expression = subscribed,
        emit       = emit,
        context    = context
    )


    subscript_name = context.allocateTempName("ass_subscript")

    generateExpressionCode(
        to_name    = subscript_name,
        expression = subscript,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        value.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    if integer_subscript:
        getIntegerSubscriptAssignmentCode(
            subscribed_name = subscribed_name,
            subscript_name  = subscript_name,
            subscript_value = constant_value,
            value_name      = value_name,
            emit            = emit,
            context         = context
        )
    else:
        getSubscriptAssignmentCode(
            target_name    = subscribed_name,
            subscript_name = subscript_name,
            value_name     = value_name,
            emit           = emit,
            context        = context
        )
    context.setCurrentSourceCodeReference(old_source_ref)


def generateDelSubscriptCode(statement, emit, context):
    subscribed = statement.getSubscribed()
    subscript  = statement.getSubscript()

    target_name, subscript_name = generateExpressionsCode(
        expressions = (subscribed, subscript),
        names       = ("delsubscr_target", "delsubscr_subscript"),
        emit        = emit,
        context     = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        subscript.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    getSubscriptDelCode(
        target_name    = target_name,
        subscript_name = subscript_name,
        emit           = emit,
        context        = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateSubscriptLookupCode(to_name, expression, emit, context):
    subscribed_name, subscript_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    return getSubscriptLookupCode(
        to_name         = to_name,
        subscribed_name = subscribed_name,
        subscript_name  = subscript_name,
        emit            = emit,
        context         = context
    )


def getIntegerSubscriptLookupCode(to_name, target_name, subscript_name,
                                  subscript_value, emit, context):
    emit(
        "%s = LOOKUP_SUBSCRIPT_CONST( %s, %s, %s );" % (
            to_name,
            target_name,
            subscript_name,
            subscript_value
        )
    )

    getReleaseCodes(
        release_names = (target_name, subscript_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getSubscriptLookupCode(to_name, subscript_name, subscribed_name, emit,
                           context):
    emit(
        "%s = LOOKUP_SUBSCRIPT( %s, %s );" % (
            to_name,
            subscribed_name,
            subscript_name,
        )
    )

    getReleaseCodes(
        release_names = (subscribed_name, subscript_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getIntegerSubscriptAssignmentCode(subscribed_name, subscript_name,
                                      subscript_value, value_name, emit,
                                      context):
    assert abs(subscript_value) < 2**31

    res_name = context.allocateTempName("ass_subscript_res", "int")

    emit(
        "%s = SET_SUBSCRIPT_CONST( %s, %s, %s, %s );" % (
            res_name,
            subscribed_name,
            subscript_name,
            subscript_value,
            value_name,
        )
    )

    getReleaseCodes(
        release_names = (subscribed_name, value_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )


def getSubscriptAssignmentCode(target_name, subscript_name, value_name,
                               emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_SUBSCRIPT( %s, %s, %s );" % (
            res_name,
            target_name,
            subscript_name,
            value_name,
        )
    )

    getReleaseCodes(
        release_names = (target_name, subscript_name, value_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )


def getSubscriptDelCode(target_name, subscript_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = DEL_SUBSCRIPT( %s, %s );" % (
            res_name,
            target_name,
            subscript_name,
        )
    )

    getReleaseCodes(
        release_names = (target_name, subscript_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )
