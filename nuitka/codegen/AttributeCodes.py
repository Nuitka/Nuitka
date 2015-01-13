#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ComparisonCodes import getBranchingCode
from .ConstantCodes import getConstantCode
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)
from .Helpers import generateChildExpressionsCode


def generateAttributeLookupCode(to_name, expression, emit, context):
    source_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    getAttributeLookupCode(
        to_name        = to_name,
        source_name    = source_name,
        attribute_name = expression.getAttributeName(),
        emit           = emit,
        context        = context
    )


def getSpecialAttributeLookupCode(to_name, source_name, attr_name, emit,
                                  context):
    emit(
        "%s = LOOKUP_SPECIAL( %s, %s );" % (
            to_name,
            source_name,
            attr_name,
        )
    )

    getReleaseCodes(
        release_names = (source_name, attr_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getAttributeLookupCode(to_name, source_name, attribute_name, emit, context):
    if attribute_name == "__dict__":
        emit(
            "%s = LOOKUP_ATTRIBUTE_DICT_SLOT( %s );" % (
                to_name,
                source_name
            )
        )
    elif attribute_name == "__class__":
        emit(
            "%s = LOOKUP_ATTRIBUTE_CLASS_SLOT( %s );" % (
                to_name,
                source_name
            )
        )
    else:
        emit(
            "%s = LOOKUP_ATTRIBUTE( %s, %s );" % (
                to_name,
                source_name,
                getConstantCode(
                    context  = context,
                    constant = attribute_name
                )
            )
        )

    getReleaseCode(
        release_name = source_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getAttributeCheckBoolCode(source_name, attr_name, emit, context):
    res_name = context.getIntResName()

    emit(
        "%s = PyObject_HasAttr( %s, %s );" % (
            res_name,
            source_name,
            attr_name
        )
    )

    getReleaseCodes(
        release_names = (source_name, attr_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
        emit      = emit,
        context   = context
    )

    getBranchingCode("%s == 1" % res_name, emit, context)


def getAttributeAssignmentCode(target_name, attribute_name, value_name, emit,
                               context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_ATTRIBUTE( %s, %s, %s );" % (
            res_name,
            target_name,
            attribute_name,
            value_name
        )
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )

    getReleaseCodes(
        release_names = (value_name, target_name, attribute_name),
        emit          = emit,
        context       = context
    )



def getAttributeAssignmentDictSlotCode(target_name, value_name, emit, context):
    """ Code for special case target.__dict__ = value """

    res_name = context.getBoolResName()

    emit(
        "%s = SET_ATTRIBUTE_DICT_SLOT( %s, %s );" % (
            res_name,
            target_name,
            value_name
        )
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )

    getReleaseCodes(
        release_names = (value_name, target_name),
        emit          = emit,
        context       = context
    )


def getAttributeAssignmentClassSlotCode(target_name, value_name, emit, context):
    """ Get code for special case target.__class__ = value """

    res_name = context.getBoolResName()

    emit(
        "%s = SET_ATTRIBUTE_CLASS_SLOT( %s, %s );" % (
            res_name,
            target_name,
            value_name
        )
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )

    getReleaseCodes(
        release_names = (value_name, target_name),
        emit          = emit,
        context       = context
    )


def getAttributeDelCode(target_name, attribute_name, emit, context):
    res_name = context.getIntResName()

    emit(
        "%s = PyObject_DelAttr( %s, %s );" % (
            res_name,
            target_name,
            attribute_name
        )
    )

    getReleaseCodes(
        release_names = (target_name, attribute_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
        emit      = emit,
        context   = context
    )
