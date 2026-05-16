#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Attribute related codes.

Attribute lookup, setting.
"""

from nuitka.PythonVersions import python_version
from nuitka.States import states

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCode
from .PythonAPICodes import (
    generateCAPIObjectCode,
    generateCAPIObjectCode0,
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
        emit("%s = LOOKUP_ATTRIBUTE_DICT_SLOT(tstate, %s);" % (to_name, source_name))
    elif attribute_name == "__class__":
        emit("%s = LOOKUP_ATTRIBUTE_CLASS_SLOT(tstate, %s);" % (to_name, source_name))
    else:
        const_code = context.getConstantCode(attribute_name)

        if python_version >= 0x3C0:
            # Per-call-site version-tag inline cache for Python 3.12+ (standard GIL builds).
            # Hot path: version-tag check + single array load, no hash probe.
            # Miss path: LOOKUP_ATTRIBUTE then Nuitka_Nitro_CacheFill fills the cache.
            emit("{")
            emit("#ifndef Py_GIL_DISABLED")
            emit("    static NitroAttrCache _nitro_cache = {0};")
            emit(
                "    PyObject *_nitro_hit = Nuitka_Nitro_CachedGetAttr(%s, &_nitro_cache);"
                % source_name
            )
            emit("    if (likely(_nitro_hit != NULL)) {")
            emit("        %s = _nitro_hit;" % to_name)
            emit("    } else {")
            emit(
                "        %s = LOOKUP_ATTRIBUTE(tstate, %s, %s);"
                % (to_name, source_name, const_code)
            )
            emit("        if (%s != NULL && _nitro_cache.type_ver == 0u) {" % to_name)
            emit(
                "            Nuitka_Nitro_CacheFill(%s, %s, &_nitro_cache);"
                % (source_name, to_name)
            )
            emit("        }")
            emit("    }")
            emit("#else")
            emit(
                "    %s = LOOKUP_ATTRIBUTE(tstate, %s, %s);"
                % (to_name, source_name, const_code)
            )
            emit("#endif")
            emit("}")
        else:
            emit(
                "%s = LOOKUP_ATTRIBUTE(tstate, %s, %s);"
                % (to_name, source_name, const_code)
            )

    getErrorExitCode(
        check_name=to_name,
        release_name=source_name,
        needs_check=needs_check,
        emit=emit,
        context=context,
    )

    context.addCleanupTempName(to_name)


def generateAttributeLookupCode(to_name, expression, emit, context):
    (source_name,) = generateChildExpressionsCode(
        expression=expression,
        emit=emit,
        context=context,
    )

    attribute_name = expression.getAttributeName()

    with withObjectCodeTemporaryAssignment(
        to_name, "attribute_value", expression, emit, context
    ) as value_name:
        with context.withCurrentSourceCodeReference(expression.getSourceReference()):

            getAttributeLookupCode(
                to_name=value_name,
                source_name=source_name,
                attribute_name=attribute_name,
                needs_check=expression.subnode_expression.mayRaiseExceptionAttributeLookup(
                    exception_type=BaseException, attribute_name=attribute_name
                ),
                emit=emit,
                context=context,
            )


def getAttributeAssignmentCode(target_name, attribute_name, value_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_ATTRIBUTE(tstate, %s, %s, %s);"
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

    emit(
        "%s = SET_ATTRIBUTE_DICT_SLOT(tstate, %s, %s);"
        % (res_name, target_name, value_name)
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def getAttributeAssignmentClassSlotCode(target_name, value_name, emit, context):
    """Get code for special case target.__class__ = value"""

    res_name = context.getBoolResName()

    emit(
        "%s = SET_ATTRIBUTE_CLASS_SLOT(tstate, %s, %s);"
        % (res_name, target_name, value_name)
    )

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
    emit("%s = LOOKUP_SPECIAL(tstate, %s, %s);" % (to_name, source_name, attr_name))

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

    if python_version >= 0x3C0:
        emit("{")
        emit("#ifndef Py_GIL_DISABLED")
        # BUILTIN_HASATTR_BOOL is often called with non-constants too, so we
        # check if attr_name is a constant we can use with our static cache.
        # But wait, BUILTIN_HASATTR_BOOL takes TWO expressions. If attr_name is
        # not a constant, we can't easily use a static NitroAttrCache.
        # However, if it IS a constant string, we can!
        if (
            expression.subnode_name.isCompileTimeConstant()
            and type(expression.subnode_name.getCompileTimeConstant()) is str
        ):
            const_code = context.getConstantCode(
                expression.subnode_name.getCompileTimeConstant()
            )
            emit("    static NitroAttrCache _nitro_cache = {0};")
            emit(
                "    int _nitro_hit = Nuitka_Nitro_CachedHasAttr(%s, &_nitro_cache);"
                % source_name
            )
            emit("    if (likely(_nitro_hit != -1)) {")
            emit("        %s = _nitro_hit;" % res_name)
            emit("    } else {")
            emit(
                "        %s = BUILTIN_HASATTR_BOOL(tstate, %s, %s);"
                % (res_name, source_name, attr_name)
            )
            emit("        if (%s != -1 && _nitro_cache.type_ver == 0u) {" % res_name)
            emit(
                "            PyObject *_nitro_val = LOOKUP_ATTRIBUTE(tstate, %s, %s);"
                % (source_name, const_code)
            )
            emit("            if (_nitro_val != NULL) {")
            emit(
                "                Nuitka_Nitro_CacheFill(%s, _nitro_val, &_nitro_cache);"
                % (source_name)
            )
            emit("                Py_DECREF(_nitro_val);")
            emit("            } else {")
            emit("                CLEAR_ERROR_OCCURRED(tstate);")
            emit("            }")
            emit("        }")
            emit("    }")
        else:
            emit(
                "%s = BUILTIN_HASATTR_BOOL(tstate, %s, %s);"
                % (res_name, source_name, attr_name)
            )
        emit("#else")
        emit(
            "%s = BUILTIN_HASATTR_BOOL(tstate, %s, %s);"
            % (res_name, source_name, attr_name)
        )
        emit("#endif")
        emit("}")
    else:
        emit(
            "%s = BUILTIN_HASATTR_BOOL(tstate, %s, %s);"
            % (res_name, source_name, attr_name)
        )

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


def _getAttributeCheckFallbackCode(
    to_name, source_name, const_code, may_raise, emit, context
):
    if may_raise:
        res_name = context.getIntResName()
        emit(
            "%s = HAS_ATTR_BOOL2(tstate, %s, %s);" % (res_name, source_name, const_code)
        )
        getErrorExitBoolCode(
            condition="%s == -1" % res_name,
            release_name=source_name,
            emit=emit,
            context=context,
        )
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s != 0" % res_name, emit=emit
        )
    else:
        res_name = context.getBoolResName()
        emit(
            "%s = HAS_ATTR_BOOL(tstate, %s, %s);" % (res_name, source_name, const_code)
        )
        getReleaseCode(release_name=source_name, emit=emit, context=context)
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition=res_name, emit=emit
        )


def generateAttributeCheckCode(to_name, expression, emit, context):
    (source_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    attribute_name = expression.getAttributeName()
    const_code = context.getConstantCode(constant=attribute_name)
    may_raise = expression.mayRaiseExceptionOperation()

    if python_version >= 0x3C0:
        emit("{")
        emit("#ifndef Py_GIL_DISABLED")
        emit("    static NitroAttrCache _nitro_cache = {0};")
        emit(
            "    int _nitro_hit = Nuitka_Nitro_CachedHasAttr(%s, &_nitro_cache);"
            % source_name
        )
        emit("    if (likely(_nitro_hit != -1)) {")
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="_nitro_hit != 0", emit=emit
        )
        emit("    } else {")
        _getAttributeCheckFallbackCode(
            to_name, source_name, const_code, may_raise, emit, context
        )

        emit("        if (_nitro_cache.type_ver == 0u) {")
        # For hasattr we need the value to fill the cache correctly (to verify it matches).
        # This is slightly slower on first miss but only happens once.
        emit(
            "            PyObject *_nitro_val = LOOKUP_ATTRIBUTE(tstate, %s, %s);"
            % (source_name, const_code)
        )
        emit("            if (_nitro_val != NULL) {")
        emit(
            "                Nuitka_Nitro_CacheFill(%s, _nitro_val, &_nitro_cache);"
            % (source_name)
        )
        emit("                Py_DECREF(_nitro_val);")
        emit("            } else {")
        emit("                CLEAR_ERROR_OCCURRED(tstate);")
        emit("            }")
        emit("        }")
        emit("    }")
        emit("#else")
        _getAttributeCheckFallbackCode(
            to_name, source_name, const_code, may_raise, emit, context
        )
        emit("#endif")
        emit("}")
    else:
        _getAttributeCheckFallbackCode(
            to_name, source_name, const_code, may_raise, emit, context
        )


def generateBuiltinGetattrCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_GETATTR",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
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
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseException(BaseException),
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
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
