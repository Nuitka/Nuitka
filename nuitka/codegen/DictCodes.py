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

Right now only the creation and a few operations on dictionaries are done here.
"""

from nuitka.PythonVersions import python_version

from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes
from .Helpers import generateChildExpressionsCode


def generateDictionaryCreationCode(to_name, pairs, emit, context):
    emit(
        "%s = _PyDict_NewPresized( %d );" % (
            to_name,
            len(pairs)
        )
    )

    context.addCleanupTempName(to_name)

    from .CodeGeneration import generateExpressionCode

    def generateValueCode(dict_value_name, pair):
        generateExpressionCode(
            to_name    = dict_value_name,
            expression = pair.getValue(),
            emit       = emit,
            context    = context
        )

    def generateKeyCode(dict_key_name, pair):
        generateExpressionCode(
            to_name    = dict_key_name,
            expression = pair.getKey(),
            emit       = emit,
            context    = context
        )


    # Strange as it is, CPython evaluates the key/value pairs strictly in order,
    # but for each pair, the value first.
    for pair in pairs:
        dict_key_name = context.allocateTempName("dict_key")
        dict_value_name = context.allocateTempName("dict_value")

        if python_version < 350:
            generateValueCode(dict_value_name, pair)
            generateKeyCode(dict_key_name, pair)
        else:
            generateKeyCode(dict_key_name, pair)
            generateValueCode(dict_value_name, pair)

        if pair.getKey().isKnownToBeHashable():
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


def generateDictOperationUpdateCode(to_name, expression, emit, context):
    res_name = context.getIntResName()

    dict_arg_name, value_arg_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit("assert( PyDict_Check( %s ) );" % dict_arg_name)
    emit(
        "%s = PyDict_Update( %s, %s );" % (
            res_name,
            dict_arg_name,
            value_arg_name
        )
    )

    getReleaseCodes(
        release_names = (dict_arg_name, value_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
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
