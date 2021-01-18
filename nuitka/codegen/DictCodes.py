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

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    withCleanupFinally,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode


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

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

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

    old_source_ref = context.setCurrentSourceCodeReference(old_source_ref)


def generateDictOperationGetCode(to_name, expression, emit, context):
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


def generateDictOperationInCode(to_name, expression, emit, context):
    inverted = expression.isExpressionDictOperationNotIn()

    dict_name, key_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

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

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.subnode_key.getSourceReference()
        if Options.is_fullcompat
        else statement.getSourceReference()
    )

    res_name = context.getBoolResName()

    emit("%s = DICT_REMOVE_ITEM(%s, %s);" % (res_name, dict_arg_name, key_arg_name))

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(dict_arg_name, key_arg_name),
        needs_check=statement.mayRaiseException(BaseException),
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)
