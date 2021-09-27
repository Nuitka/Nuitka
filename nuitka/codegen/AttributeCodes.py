#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Attribute related codes.

Attribute lookup, setting.
"""

from nuitka import Options

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCode
from .PythonAPICodes import generateCAPIObjectCode, generateCAPIObjectCode0


def generateAssignmentAttributeCode(statement, emit, context):
    lookup_source = statement.subnode_expression
    attribute_name = statement.getAttributeName()
    value = statement.subnode_source

    value_name = context.allocateTempName("assattr_value")
    generateExpressionCode(
        to_name=value_name, expression=value, emit=emit, context=context
    )

    target_name = context.allocateTempName("assattr_target")
    generateExpressionCode(
        to_name=target_name, expression=lookup_source, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(
        value.getSourceReference()
        if Options.is_fullcompat
        else statement.getSourceReference()
    ):
        if attribute_name == "__dict__":
            getAttributeAssignmentDictSlotCode(
                target_name=target_name,
                value_name=value_name,
                emit=emit,
                context=context,
            )
        elif attribute_name == "__class__":
            getAttributeAssignmentClassSlotCode(
                target_name=target_name,
                value_name=value_name,
                emit=emit,
                context=context,
            )
        else:
            getAttributeAssignmentCode(
                target_name=target_name,
                value_name=value_name,
                attribute_name=context.getConstantCode(constant=attribute_name),
                emit=emit,
                context=context,
            )


def generateDelAttributeCode(statement, emit, context):
    target_name = context.allocateTempName("attrdel_target")

    generateExpressionCode(
        to_name=target_name,
        expression=statement.subnode_expression,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(
        statement.subnode_expression.getSourceReference()
        if Options.is_fullcompat
        else statement.getSourceReference()
    ):
        getAttributeDelCode(
            target_name=target_name,
            attribute_name=context.getConstantCode(
                constant=statement.getAttributeName()
            ),
            emit=emit,
            context=context,
        )


def generateAttributeLookupCode(to_name, expression, emit, context):
    (source_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    attribute_name = expression.getAttributeName()

    needs_check = expression.subnode_expression.mayRaiseExceptionAttributeLookup(
        exception_type=BaseException, attribute_name=attribute_name
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "attribute_value", expression, emit, context
    ) as value_name:
        if attribute_name == "__dict__":
            emit("%s = LOOKUP_ATTRIBUTE_DICT_SLOT(%s);" % (value_name, source_name))
        elif attribute_name == "__class__":
            emit("%s = LOOKUP_ATTRIBUTE_CLASS_SLOT(%s);" % (value_name, source_name))
        else:
            emit(
                "%s = LOOKUP_ATTRIBUTE(%s, %s);"
                % (value_name, source_name, context.getConstantCode(attribute_name))
            )

        getErrorExitCode(
            check_name=value_name,
            release_name=source_name,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def getAttributeAssignmentCode(target_name, attribute_name, value_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_ATTRIBUTE(%s, %s, %s);"
        % (res_name, target_name, attribute_name, value_name)
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(value_name, target_name, attribute_name),
        emit=emit,
        context=context,
    )


def getAttributeAssignmentDictSlotCode(target_name, value_name, emit, context):
    """Code for special case target.__dict__ = value"""

    res_name = context.getBoolResName()

    emit("%s = SET_ATTRIBUTE_DICT_SLOT(%s, %s);" % (res_name, target_name, value_name))

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def getAttributeAssignmentClassSlotCode(target_name, value_name, emit, context):
    """Get code for special case target.__class__ = value"""

    res_name = context.getBoolResName()

    emit("%s = SET_ATTRIBUTE_CLASS_SLOT(%s, %s);" % (res_name, target_name, value_name))

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def getAttributeDelCode(target_name, attribute_name, emit, context):
    res_name = context.getIntResName()

    emit("%s = PyObject_DelAttr(%s, %s);" % (res_name, target_name, attribute_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(target_name, attribute_name),
        emit=emit,
        context=context,
    )


def generateAttributeLookupSpecialCode(to_name, expression, emit, context):
    (source_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    attribute_name = expression.getAttributeName()

    getAttributeLookupSpecialCode(
        to_name=to_name,
        source_name=source_name,
        attr_name=context.getConstantCode(constant=attribute_name),
        needs_check=expression.subnode_expression.mayRaiseExceptionAttributeLookupSpecial(
            exception_type=BaseException, attribute_name=attribute_name
        ),
        emit=emit,
        context=context,
    )


def getAttributeLookupSpecialCode(
    to_name, source_name, attr_name, needs_check, emit, context
):
    emit("%s = LOOKUP_SPECIAL(%s, %s);" % (to_name, source_name, attr_name))

    getErrorExitCode(
        check_name=to_name,
        release_names=(source_name, attr_name),
        emit=emit,
        needs_check=needs_check,
        context=context,
    )

    context.addCleanupTempName(to_name)


def generateBuiltinHasattrCode(to_name, expression, emit, context):
    source_name, attr_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("%s = BUILTIN_HASATTR_BOOL(%s, %s);" % (res_name, source_name, attr_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(source_name, attr_name),
        needs_check=expression.mayRaiseException(BaseException),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s != 0" % res_name, emit=emit
    )


def generateAttributeCheckCode(to_name, expression, emit, context):
    (source_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getBoolResName()

    emit(
        "%s = HAS_ATTR_BOOL(%s, %s);"
        % (
            res_name,
            source_name,
            context.getConstantCode(constant=expression.getAttributeName()),
        )
    )

    getReleaseCode(release_name=source_name, emit=emit, context=context)

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition=res_name, emit=emit
    )


def generateBuiltinGetattrCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_GETATTR",
        arg_desc=(
            ("getattr_target", expression.subnode_expression),
            ("getattr_attr", expression.subnode_name),
            ("getattr_default", expression.subnode_default),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinSetattrCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=to_name,
        capi="BUILTIN_SETATTR",
        arg_desc=(
            ("setattr_target", expression.subnode_expression),
            ("setattr_attr", expression.subnode_attribute),
            ("setattr_value", expression.subnode_value),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )
