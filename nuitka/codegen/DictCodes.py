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
""" Code generation for dictionaries.

"""

from nuitka import Options
from nuitka.PythonVersions import python_version
from nuitka.utils.Jinja2 import renderTemplateFromString

from .CodeHelpers import (
    assignConstantNoneResult,
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withCleanupFinally,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes
from .PythonAPICodes import (
    generateCAPIObjectCode,
    generateCAPIObjectCode0,
    makeArgDescFromExpression,
)


def generateBuiltinDictCode(to_name, expression, emit, context):
    if expression.subnode_pos_arg:
        seq_name = context.allocateTempName("dict_seq")

        generateExpressionCode(
            to_name=seq_name,
            expression=expression.subnode_pos_arg,
            emit=emit,
            context=context,
            allow_none=True,
        )
    else:
        seq_name = None

    with withObjectCodeTemporaryAssignment(
        to_name, "dict_value", expression, emit, context
    ) as value_name:

        if expression.subnode_pairs:
            # If there is no sequence to mix in, then directly generate
            # into to_name.

            if seq_name is None:
                _getDictionaryCreationCode(
                    to_name=value_name,
                    pairs=expression.subnode_pairs,
                    emit=emit,
                    context=context,
                )

                dict_name = None
            else:
                dict_name = context.allocateTempName("dict_arg")

                _getDictionaryCreationCode(
                    to_name=dict_name,
                    pairs=expression.subnode_pairs,
                    emit=emit,
                    context=context,
                )
        else:
            dict_name = None

        if seq_name is not None:
            emit(
                "%s = TO_DICT(%s, %s);"
                % (value_name, seq_name, "NULL" if dict_name is None else dict_name)
            )

            getErrorExitCode(
                check_name=value_name,
                release_names=(seq_name, dict_name),
                emit=emit,
                context=context,
            )

            context.addCleanupTempName(value_name)


def generateDictionaryCreationCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "dict_result", expression, emit, context
    ) as value_name:
        _getDictionaryCreationCode(
            to_name=value_name,
            pairs=expression.subnode_pairs,
            emit=emit,
            context=context,
        )


def _getDictionaryCreationCode(to_name, pairs, emit, context):
    # Detailed, and verbose code, pylint: disable=too-many-locals

    pairs_count = len(pairs)

    # Empty dictionaries should not get to this function, but be constant value instead.
    assert pairs_count > 0

    # Unique per dictionary, they might be nested, but used for all of them.
    dict_key_name = context.allocateTempName("dict_key")
    dict_value_name = context.allocateTempName("dict_value")

    is_hashable_key = [pair.subnode_key.isKnownToBeHashable() for pair in pairs]

    # Does this dictionary build need an exception handling at all.
    if all(is_hashable_key):
        for pair in pairs[1:]:
            if pair.subnode_key.mayRaiseException(BaseException):
                needs_exception_exit = True
                break
            if pair.subnode_value.mayRaiseException(BaseException):
                needs_exception_exit = True
                break
        else:
            needs_exception_exit = False
    else:
        needs_exception_exit = True

    def generateValueCode(dict_value_name, pair):
        generateExpressionCode(
            to_name=dict_value_name,
            expression=pair.subnode_value,
            emit=emit,
            context=context,
        )

    def generateKeyCode(dict_key_name, pair):
        generateExpressionCode(
            to_name=dict_key_name,
            expression=pair.subnode_key,
            emit=emit,
            context=context,
        )

    def generatePairCode(pair):
        # Strange as it is, CPython 3.5 and before evaluated the key/value pairs
        # strictly in order, but for each pair, the value first.
        if python_version < 0x350:
            generateValueCode(dict_value_name, pair)
            generateKeyCode(dict_key_name, pair)
        else:
            generateKeyCode(dict_key_name, pair)
            generateValueCode(dict_value_name, pair)

        key_needs_release = context.needsCleanup(dict_key_name)
        if key_needs_release:
            context.removeCleanupTempName(dict_key_name)

        value_needs_release = context.needsCleanup(dict_value_name)
        if value_needs_release:
            context.removeCleanupTempName(dict_value_name)

        return key_needs_release, value_needs_release

    key_needs_release, value_needs_release = generatePairCode(pairs[0])

    # Create dictionary presized.
    emit("%s = _PyDict_NewPresized( %d );" % (to_name, pairs_count))

    with withCleanupFinally(
        "dict_build", to_name, needs_exception_exit, emit, context
    ) as guarded_emit:
        emit = guarded_emit.emit

        for count, pair in enumerate(pairs):
            if count > 0:
                key_needs_release, value_needs_release = generatePairCode(pair)

            needs_check = not is_hashable_key[count]
            res_name = context.getIntResName()

            emit(
                "%s = PyDict_SetItem(%s, %s, %s);"
                % (res_name, to_name, dict_key_name, dict_value_name)
            )

            if value_needs_release:
                emit("Py_DECREF(%s);" % dict_value_name)

            if key_needs_release:
                emit("Py_DECREF(%s);" % dict_key_name)

            getErrorExitBoolCode(
                condition="%s != 0" % res_name,
                needs_check=needs_check,
                emit=emit,
                context=context,
            )


def generateDictOperationUpdateCode(statement, emit, context):
    value_arg_name = context.allocateTempName("dictupdate_value", unique=True)
    generateExpressionCode(
        to_name=value_arg_name,
        expression=statement.subnode_value,
        emit=emit,
        context=context,
    )

    dict_arg_name = context.allocateTempName("dictupdate_dict", unique=True)
    generateExpressionCode(
        to_name=dict_arg_name,
        expression=statement.subnode_dict_arg,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        res_name = context.getIntResName()

        emit("assert(PyDict_Check(%s));" % dict_arg_name)
        emit("%s = PyDict_Update(%s, %s);" % (res_name, dict_arg_name, value_arg_name))

        getErrorExitBoolCode(
            condition="%s != 0" % res_name,
            release_names=(dict_arg_name, value_arg_name),
            needs_check=statement.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )


def generateDictOperationItemCode(to_name, expression, emit, context):
    dict_name, key_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "dict_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = DICT_GET_ITEM_WITH_ERROR(%s, %s);" % (value_name, dict_name, key_name)
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(dict_name, key_name),
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateDictOperationGet2Code(to_name, expression, emit, context):
    dict_name, key_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "dict_value", expression, emit, context
    ) as value_name:
        emit(
            renderTemplateFromString(
                r"""
{% if expression.known_hashable_key %}
%(value_name)s = DICT_GET_ITEM0(%(dict_name)s, %(key_name)s);
if (%(value_name)s == NULL) {
{% else %}
%(value_name)s = DICT_GET_ITEM_WITH_HASH_ERROR0(%(dict_name)s, %(key_name)s);
if (%(value_name)s == NULL && !ERROR_OCCURRED()) {
{% endif %}
    %(value_name)s = Py_None;
}
""",
                expression=expression,
            )
            % {
                "value_name": value_name,
                "dict_name": dict_name,
                "key_name": key_name,
            }
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(dict_name, key_name),
            needs_check=not expression.known_hashable_key,
            emit=emit,
            context=context,
        )


def generateDictOperationGet3Code(to_name, expression, emit, context):
    dict_name, key_name, default_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # TODO: This code could actually make it dependent on default taking
    # a reference or not, and then use DICT_GET_ITEM0/DICT_GET_ITEM_WITH_HASH_ERROR0 if not.

    with withObjectCodeTemporaryAssignment(
        to_name, "dict_value", expression, emit, context
    ) as value_name:
        emit(
            renderTemplateFromString(
                r"""
{% if expression.known_hashable_key %}
%(value_name)s = DICT_GET_ITEM1(%(dict_name)s, %(key_name)s);
if (%(value_name)s == NULL) {
{% else %}
%(value_name)s = DICT_GET_ITEM_WITH_HASH_ERROR1(%(dict_name)s, %(key_name)s);
if (%(value_name)s == NULL && !ERROR_OCCURRED()) {
{% endif %}
    %(value_name)s = %(default_name)s;
    Py_INCREF(%(value_name)s);
}

""",
                expression=expression,
            )
            % {
                "value_name": value_name,
                "dict_name": dict_name,
                "key_name": key_name,
                "default_name": default_name,
            }
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(dict_name, key_name, default_name),
            needs_check=not expression.known_hashable_key,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateDictOperationSetdefault2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_SETDEFAULT2",
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=not expression.known_hashable_key,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationSetdefault3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_SETDEFAULT3",
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=not expression.known_hashable_key,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationPop2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_POP2",
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationPop3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_POP3",
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=not expression.known_hashable_key,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationUpdate2Code(to_name, expression, emit, context):
    dict_name, iterable_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("assert(PyDict_Check(%s));" % dict_name)
    emit("%s = PyDict_Update(%s, %s);" % (res_name, dict_name, iterable_name))

    getErrorExitBoolCode(
        condition="%s != 0" % res_name,
        release_names=(dict_name, iterable_name),
        needs_check=expression.mayRaiseException(BaseException),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateDictOperationUpdate3Code(to_name, expression, emit, context):
    dict_name, iterable_name, pair_names = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("assert(PyDict_Check(%s));" % dict_name)

    if expression.subnode_iterable is not None:
        emit(
            renderTemplateFromString(
                r"""
{% if has_keys_attribute == None %}
if (HAS_ATTR_BOOL(%(iterable_name)s, const_str_plain_keys)){
    %(res_name)s = PyDict_Merge(%(dict_name)s, %(iterable_name)s, 1);
} else {
    %(res_name)s = PyDict_MergeFromSeq2(%(dict_name)s, %(iterable_name)s, 1);
}
{% elif has_keys_attribute == True %}
    %(res_name)s = PyDict_Merge(%(dict_name)s, %(iterable_name)s, 1);
{% else %}
    %(res_name)s = PyDict_MergeFromSeq2(%(dict_name)s, %(iterable_name)s, 1);
{% endif %}
""",
                has_keys_attribute=expression.subnode_iterable.isKnownToHaveAttribute(
                    "keys"
                ),
            )
            % {
                "res_name": res_name,
                "dict_name": dict_name,
                "iterable_name": iterable_name,
            }
        )

        getErrorExitBoolCode(
            condition="%s != 0" % res_name,
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )

    for count, (pair_key_name, pair_key_value) in enumerate(pair_names):
        if python_version < 0x350:
            pair_key_name, pair_key_value = pair_key_value, pair_key_name

        emit(
            "%s = PyDict_SetItem(%s, %s, %s);"
            % (res_name, dict_name, pair_key_name, pair_key_value)
        )

        getErrorExitBoolCode(
            condition="%s != 0" % res_name,
            needs_check=not expression.subnode_pairs[count].isKnownToBeHashable(),
            emit=emit,
            context=context,
        )

    getReleaseCodes(
        release_names=(dict_name, iterable_name) + sum(pair_names, ()),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateDictOperationCopyCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_COPY",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationClearCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=None,
        capi="DICT_CLEAR",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )

    # None result if wanted.
    assignConstantNoneResult(to_name, emit, context)


def generateDictOperationItemsCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_ITEMS",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationIteritemsCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_ITERITEMS",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationViewitemsCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_VIEWITEMS",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationKeysCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_KEYS",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationIterkeysCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_ITERKEYS",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationViewkeysCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_VIEWKEYS",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationValuesCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_VALUES",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationItervaluesCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_ITERVALUES",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationViewvaluesCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="DICT_VIEWVALUES",
        arg_desc=(("dict_arg", expression.subnode_dict_arg),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateDictOperationInCode(to_name, expression, emit, context):
    inverted = expression.isExpressionDictOperationNotIn()

    dict_name, key_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # Reverse child order.
    if expression.isExpressionDictOperationHaskey():
        dict_name, key_name = key_name, dict_name

    res_name = context.getIntResName()

    emit("%s = DICT_HAS_ITEM(%s, %s);" % (res_name, key_name, dict_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(dict_name, key_name),
        needs_check=expression.known_hashable_key is not True,
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name,
        condition="%s %s 0" % (res_name, "==" if inverted else "!="),
        emit=emit,
    )


def generateDictOperationSetCode(statement, emit, context):
    value_arg_name = context.allocateTempName("dictset_value", unique=True)
    generateExpressionCode(
        to_name=value_arg_name,
        expression=statement.subnode_value,
        emit=emit,
        context=context,
    )

    dict_arg_name = context.allocateTempName("dictset_dict", unique=True)
    generateExpressionCode(
        to_name=dict_arg_name,
        expression=statement.subnode_dict_arg,
        emit=emit,
        context=context,
    )

    key_arg_name = context.allocateTempName("dictset_key", unique=True)
    generateExpressionCode(
        to_name=key_arg_name,
        expression=statement.subnode_key,
        emit=emit,
        context=context,
    )
    context.setCurrentSourceCodeReference(statement.getSourceReference())

    res_name = context.getIntResName()

    emit(
        "%s = PyDict_SetItem(%s, %s, %s);"
        % (res_name, dict_arg_name, key_arg_name, value_arg_name)
    )

    getErrorExitBoolCode(
        condition="%s != 0" % res_name,
        release_names=(value_arg_name, dict_arg_name, key_arg_name),
        emit=emit,
        needs_check=not statement.subnode_key.isKnownToBeHashable(),
        context=context,
    )


def generateDictOperationSetCodeKeyValue(statement, emit, context):
    key_arg_name = context.allocateTempName("dictset38_key")
    generateExpressionCode(
        to_name=key_arg_name,
        expression=statement.subnode_key,
        emit=emit,
        context=context,
    )

    value_arg_name = context.allocateTempName("dictset38_value")
    generateExpressionCode(
        to_name=value_arg_name,
        expression=statement.subnode_value,
        emit=emit,
        context=context,
    )

    dict_arg_name = context.allocateTempName("dictset38_dict")
    generateExpressionCode(
        to_name=dict_arg_name,
        expression=statement.subnode_dict_arg,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    res_name = context.getIntResName()

    emit(
        "%s = PyDict_SetItem(%s, %s, %s);"
        % (res_name, dict_arg_name, key_arg_name, value_arg_name)
    )

    getErrorExitBoolCode(
        condition="%s != 0" % res_name,
        release_names=(value_arg_name, dict_arg_name, key_arg_name),
        emit=emit,
        needs_check=not statement.subnode_key.isKnownToBeHashable(),
        context=context,
    )


def generateDictOperationRemoveCode(statement, emit, context):
    dict_arg_name = context.allocateTempName("dictdel_dict", unique=True)
    generateExpressionCode(
        to_name=dict_arg_name,
        expression=statement.subnode_dict_arg,
        emit=emit,
        context=context,
    )

    key_arg_name = context.allocateTempName("dictdel_key", unique=True)
    generateExpressionCode(
        to_name=key_arg_name,
        expression=statement.subnode_key,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(
        statement.subnode_key.getSourceReference()
        if Options.is_fullcompat
        else statement.getSourceReference()
    ):
        res_name = context.getBoolResName()

        emit("%s = DICT_REMOVE_ITEM(%s, %s);" % (res_name, dict_arg_name, key_arg_name))

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            release_names=(dict_arg_name, key_arg_name),
            needs_check=statement.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )
