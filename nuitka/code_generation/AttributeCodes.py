#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Attribute lookup, assignment, and deletion code generation."""

from nuitka.States import states

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    promoteBorrowedValue,
)
from .PythonAPICodes import (
    ConstantArg,
    generateCAPIBoolCode,
    generateCAPIObjectCode,
    generateCAPIObjectCode0,
    getCAPIErrorCode,
    getCAPIObjectCode,
    makeArgDescFromExpression,
)


def generateAssignmentAttributeCode(statement, emit, context):
    lookup_source = statement.subnode_expression
    attribute_name = statement.getAttributeName()
    value = statement.subnode_source

    value_name = context.allocateTempName("ass_attr_value")
    generateExpressionCode(
        to_name=value_name, expression=value, emit=emit, context=context
    )
    promoteBorrowedValue(
        value_name=value_name,
        later_expressions=(lookup_source,),
        emit=emit,
        context=context,
    )

    target_name = context.allocateTempName("ass_attr_target")
    generateExpressionCode(
        to_name=target_name, expression=lookup_source, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(
        value.getSourceReference()
        if states.is_full_compat
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
    target_name = context.allocateTempName("attr_del_target")

    generateExpressionCode(
        to_name=target_name,
        expression=statement.subnode_expression,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(
        statement.subnode_expression.getSourceReference()
        if states.is_full_compat
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


def getAttributeLookupCode(
    to_name, source_name, attribute_name, needs_check, emit, context
):
    if attribute_name == "__dict__":
        capi = "LOOKUP_ATTRIBUTE_DICT_SLOT"
        arg_names = ("tstate", source_name)
    elif attribute_name == "__class__":
        capi = "LOOKUP_ATTRIBUTE_CLASS_SLOT"
        arg_names = ("tstate", source_name)
    else:
        capi = "LOOKUP_ATTRIBUTE"
        arg_names = ("tstate", source_name, context.getConstantCode(attribute_name))

    getCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        arg_names=arg_names,
        may_raise=needs_check,
        conversion_check=False,
        ref_count=1,
        release_names=(source_name,),
        emit=emit,
        context=context,
    )


def generateAttributeLookupCode(to_name, expression, emit, context):
    attribute_name = expression.getAttributeName()

    if attribute_name == "__dict__":
        capi = "LOOKUP_ATTRIBUTE_DICT_SLOT"
        arg_desc = makeArgDescFromExpression(expression)
    elif attribute_name == "__class__":
        capi = "LOOKUP_ATTRIBUTE_CLASS_SLOT"
        arg_desc = makeArgDescFromExpression(expression)
    else:
        capi = "LOOKUP_ATTRIBUTE"
        arg_desc = makeArgDescFromExpression(expression) + (
            ConstantArg(attribute_name),
        )

    generateCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        tstate=True,
        arg_desc=arg_desc,
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getSourceReference(),
        emit=emit,
        context=context,
    )


def getAttributeAssignmentCode(target_name, attribute_name, value_name, emit, context):
    getCAPIErrorCode(
        capi="SET_ATTRIBUTE",
        arg_names=("tstate", target_name, attribute_name, value_name),
        may_raise=True,
        release_names=(value_name, target_name, attribute_name),
        emit=emit,
        context=context,
    )


def getAttributeAssignmentDictSlotCode(target_name, value_name, emit, context):
    getCAPIErrorCode(
        capi="SET_ATTRIBUTE_DICT_SLOT",
        arg_names=("tstate", target_name, value_name),
        may_raise=True,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def getAttributeAssignmentClassSlotCode(target_name, value_name, emit, context):
    getCAPIErrorCode(
        capi="SET_ATTRIBUTE_CLASS_SLOT",
        arg_names=("tstate", target_name, value_name),
        may_raise=True,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def getAttributeDelCode(target_name, attribute_name, emit, context):
    getCAPIErrorCode(
        capi="PyObject_DelAttr",
        arg_names=(target_name, attribute_name),
        may_raise=True,
        release_names=(target_name, attribute_name),
        res_type="int_neg1",
        emit=emit,
        context=context,
    )


def generateAttributeLookupSpecialCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LOOKUP_SPECIAL",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression)
        + (ConstantArg(expression.getAttributeName()),),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def getAttributeLookupSpecialCode(
    to_name, source_name, attr_name, needs_check, emit, context
):
    getCAPIObjectCode(
        to_name=to_name,
        capi="LOOKUP_SPECIAL",
        arg_names=("tstate", source_name, attr_name),
        may_raise=needs_check,
        conversion_check=False,
        ref_count=1,
        release_names=(source_name, attr_name),
        emit=emit,
        context=context,
    )


def generateBuiltinHasattrCode(to_name, expression, emit, context):
    generateCAPIBoolCode(
        to_name=to_name,
        capi="BUILTIN_HASATTR_BOOL",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateAttributeCheckCode(to_name, expression, emit, context):
    may_raise = expression.mayRaiseExceptionOperation()

    generateCAPIBoolCode(
        to_name=to_name,
        capi="HAS_ATTR_BOOL2" if may_raise else "HAS_ATTR_BOOL",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression)
        + (ConstantArg(expression.getAttributeName()),),
        may_raise=may_raise,
        res_type="tristate" if may_raise else "bool",
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinGetattrCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_GETATTR",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
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
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinDelattrCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=to_name,
        capi="BUILTIN_DELATTR",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
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
