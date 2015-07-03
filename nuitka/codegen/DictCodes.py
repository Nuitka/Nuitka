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
""" Code generation for dicts.

Right now only the creation is done here. But more should be added later on.
"""

from nuitka import Options
from nuitka.PythonVersions import python_version

from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes


def generateDictionaryCreationCode(to_name, pairs, emit, context):
    if Options.isFullCompat() and python_version >= 340:
        return _generateDictionaryCreationCode340(
            to_name = to_name,
            pairs   = pairs,
            emit    = emit,
            context = context
        )
    else:
        return _generateDictionaryCreationCode(
            to_name = to_name,
            pairs   = pairs,
            emit    = emit,
            context = context
        )


def _generateDictionaryCreationCode340(to_name, pairs, emit, context):

    # Note: This is only for Python3.4 full compatibility, it's worse than for
    # the other versions, and only to be used if that level of compatibility is
    # requested. It is to avoid changes in dictionary items order that are
    # normal with random hashing.

    emit(
        "%s = _PyDict_NewPresized( %d );" % (
            to_name,
            len(pairs)
        )
    )

    context.addCleanupTempName(to_name)

    from .CodeGeneration import generateExpressionCode

    dict_key_names = []
    dict_value_names = []
    keys = []

    # Strange as it is, CPython evaluates the key/value pairs strictly in order,
    # but for each pair, the value first.
    for pair in pairs:
        dict_key_name = context.allocateTempName("dict_key")
        dict_value_name = context.allocateTempName("dict_value")

        if python_version < 350:
            generateExpressionCode(
                to_name    = dict_value_name,
                expression = pair.getValue(),
                emit       = emit,
                context    = context
            )

            generateExpressionCode(
                to_name    = dict_key_name,
                expression = pair.getKey(),
                emit       = emit,
                context    = context
            )
        else:
            generateExpressionCode(
                to_name    = dict_key_name,
                expression = pair.getKey(),
                emit       = emit,
                context    = context
            )

            generateExpressionCode(
                to_name    = dict_value_name,
                expression = pair.getValue(),
                emit       = emit,
                context    = context
            )


        dict_key_names.append(dict_key_name)
        dict_value_names.append(dict_value_name)

        keys.append(pair.getKey())

    for key, dict_key_name, dict_value_name in \
      zip(reversed(keys), reversed(dict_key_names), reversed(dict_value_names)):
        if key.isKnownToBeHashable():
            emit(
                "PyDict_SetItem( %s, %s, %s );" % (
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )
        else:
            res_name = context.getIntResName()

            emit(
                "%s = PyDict_SetItem( %s, %s, %s );" % (
                    res_name,
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )

            getErrorExitBoolCode(
                condition = "%s != 0" % res_name,
                emit      = emit,
                context   = context
            )

        if context.needsCleanup(dict_value_name):
            emit("Py_DECREF( %s );" % dict_value_name)
            context.removeCleanupTempName(dict_value_name)

        if context.needsCleanup(dict_key_name):
            emit("Py_DECREF( %s );" % dict_key_name)
            context.removeCleanupTempName(dict_key_name)


def _generateDictionaryCreationCode(to_name, pairs, emit, context):
    emit(
        "%s = _PyDict_NewPresized( %d );" % (
            to_name,
            len(pairs)
        )
    )

    context.addCleanupTempName(to_name)

    from .CodeGeneration import generateExpressionCode

    # Strange as it is, CPython evaluates the key/value pairs strictly in order,
    # but for each pair, the value first.
    for pair in pairs:
        dict_key_name = context.allocateTempName("dict_key")
        dict_value_name = context.allocateTempName("dict_value")

        generateExpressionCode(
            to_name    = dict_value_name,
            expression = pair.getValue(),
            emit       = emit,
            context    = context
        )

        key = pair.getKey()

        generateExpressionCode(
            to_name    = dict_key_name,
            expression = key,
            emit       = emit,
            context    = context
        )


        if key.isKnownToBeHashable():
            emit(
                "PyDict_SetItem( %s, %s, %s );" % (
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )
        else:
            res_name = context.getIntResName()

            emit(
                "%s = PyDict_SetItem( %s, %s, %s );" % (
                    res_name,
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )

            getErrorExitBoolCode(
                condition = "%s != 0" % res_name,
                emit      = emit,
                context   = context
            )

        if context.needsCleanup(dict_value_name):
            emit("Py_DECREF( %s );" % dict_value_name)
            context.removeCleanupTempName(dict_value_name)

        if context.needsCleanup(dict_key_name):
            emit("Py_DECREF( %s );" % dict_key_name)
            context.removeCleanupTempName(dict_key_name)



def getDictOperationGetCode(to_name, dict_name, key_name, emit, context):
    emit(
        "%s = DICT_GET_ITEM( %s, %s );" % (
            to_name,
            dict_name,
            key_name
        )
    )

    getReleaseCodes(
        release_names = (dict_name, key_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getBuiltinDict2Code(to_name, seq_name, dict_name, emit, context):
    # Seq not available must have been optimized way already.
    assert seq_name is not None

    emit(
        "%s = TO_DICT( %s, %s );" % (
            to_name,
            seq_name,
            "NULL" if dict_name is None else dict_name
        )
    )

    getReleaseCodes(
        release_names = (seq_name, dict_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getDictOperationRemoveCode(dict_name, key_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = DICT_REMOVE_ITEM( %s, %s );" % (
            res_name,
            dict_name,
            key_name
        )
    )

    getReleaseCodes(
        release_names = (dict_name, key_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )


def getDictOperationSetCode(to_name, dict_name, key_name, value_name, emit,
                            context):
    res_name = context.getIntResName()

    emit(
        "%s = PyDict_SetItem( %s, %s, %s );" % (
            res_name,
            dict_name,
            key_name,
            value_name
        )
    )

    getReleaseCodes(
        release_names = (dict_name, key_name, value_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s != 0" % res_name,
        emit      = emit,
        context   = context
    )

    # Only assign if necessary.
    if context.isUsed(to_name):
        emit(
            "%s = Py_None;" % to_name
        )
    else:
        context.forgetTempName(to_name)
