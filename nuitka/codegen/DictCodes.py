#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .CodeHelpers import generateChildExpressionsCode, generateExpressionCode
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes


def generateBuiltinDictCode(to_name, expression, emit, context):
    if expression.getPositionalArgument():
        seq_name = context.allocateTempName("dict_seq")

        generateExpressionCode(
            to_name    = seq_name,
            expression = expression.getPositionalArgument(),
            emit       = emit,
            context    = context,
            allow_none = True
        )
    else:
        seq_name = None

    if expression.getNamedArgumentPairs():
        # If there is no sequence to mix in, then directly generate
        # into to_name.

        if seq_name is None:
            getDictionaryCreationCode(
                to_name = to_name,
                pairs   = expression.getNamedArgumentPairs(),
                emit    = emit,
                context = context
            )

            dict_name = None
        else:
            dict_name = context.allocateTempName("dict_arg")

            getDictionaryCreationCode(
                to_name = dict_name,
                pairs   = expression.getNamedArgumentPairs(),
                emit    = emit,
                context = context
            )
    else:
        dict_name = None

    if seq_name is not None:
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


def generateDictionaryCreationCode(to_name, expression, emit, context):
    getDictionaryCreationCode(
        to_name = to_name,
        pairs   = expression.getPairs(),
        emit    = emit,
        context = context
    )


def getDictionaryCreationCode(to_name, pairs, emit, context):

    emit(
        "%s = _PyDict_NewPresized( %d );" % (
            to_name,
            len(pairs)
        )
    )

    context.addCleanupTempName(to_name)

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

        needs_check = not pair.getKey().isKnownToBeHashable()

        res_name = context.getIntResName()

        emit(
            "%s = PyDict_SetItem( %s, %s, %s );" % (
                res_name,
                to_name,
                dict_key_name,
                dict_value_name
            )
        )

        if context.needsCleanup(dict_value_name):
            emit("Py_DECREF( %s );" % dict_value_name)
            context.removeCleanupTempName(dict_value_name)

        if context.needsCleanup(dict_key_name):
            emit("Py_DECREF( %s );" % dict_key_name)
            context.removeCleanupTempName(dict_key_name)

        getErrorExitBoolCode(
            condition   = "%s != 0" % res_name,
            needs_check = needs_check,
            emit        = emit,
            context     = context
        )



def generateDictOperationUpdateCode(statement, emit, context):
    value_arg_name = context.allocateTempName("dictupdate_value", unique = True)
    generateExpressionCode(
        to_name    = value_arg_name,
        expression = statement.getValue(),
        emit       = emit,
        context    = context
    )

    dict_arg_name = context.allocateTempName("dictupdate_dict", unique = True)
    generateExpressionCode(
        to_name    = dict_arg_name,
        expression = statement.getDict(),
        emit       = emit,
        context    = context
    )

    res_name = context.getIntResName()

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
        condition   = "%s != 0" % res_name,
        needs_check = statement.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
    )


def generateDictOperationGetCode(to_name, expression, emit, context):
    dict_name, key_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

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
        check_name  = to_name,
        needs_check = expression.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
    )

    context.addCleanupTempName(to_name)


def generateDictOperationInCode(to_name, expression, emit, context):
    inverted = expression.isExpressionDictOperationNOTIn()

    dict_name, key_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    res_name = context.getIntResName()

    emit(
        "%s = PyDict_Contains( %s, %s );" % (
            res_name,
            key_name,
            dict_name
        )
    )


    getReleaseCodes(
        release_names = (dict_name, key_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition   = "%s == -1" % res_name,
        needs_check = expression.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
    )

    emit(
        "%s = BOOL_FROM( %s == %s );" % (
            to_name,
            res_name,
            '1' if not inverted else '0'
        )
    )


def generateDictOperationSetCode(statement, emit, context):
    value_arg_name = context.allocateTempName("dictset_value", unique = True)
    generateExpressionCode(
        to_name    = value_arg_name,
        expression = statement.getValue(),
        emit       = emit,
        context    = context
    )

    dict_arg_name = context.allocateTempName("dictset_dict", unique = True)
    generateExpressionCode(
        to_name    = dict_arg_name,
        expression = statement.getDict(),
        emit       = emit,
        context    = context
    )

    key_arg_name = context.allocateTempName("dictset_key", unique = True)
    generateExpressionCode(
        to_name    = key_arg_name,
        expression = statement.getKey(),
        emit       = emit,
        context    = context
    )
    context.setCurrentSourceCodeReference(statement.getSourceReference())

    res_name = context.getIntResName()

    emit(
        "%s = PyDict_SetItem( %s, %s, %s );" % (
            res_name,
            dict_arg_name,
            key_arg_name,
            value_arg_name
        )
    )

    getReleaseCodes(
        release_names = (value_arg_name, dict_arg_name, key_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition   = "%s != 0" % res_name,
        emit        = emit,
        needs_check = not statement.getKey().isKnownToBeHashable(),
        context     = context
    )


def generateDictOperationRemoveCode(statement, emit, context):
    dict_arg_name = context.allocateTempName("dictdel_dict", unique = True)
    generateExpressionCode(
        to_name    = dict_arg_name,
        expression = statement.getDict(),
        emit       = emit,
        context    = context
    )

    key_arg_name = context.allocateTempName("dictdel_key", unique = True)
    generateExpressionCode(
        to_name    = key_arg_name,
        expression = statement.getKey(),
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getKey().getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    res_name = context.getBoolResName()

    emit(
        "%s = DICT_REMOVE_ITEM( %s, %s );" % (
            res_name,
            dict_arg_name,
            key_arg_name
        )
    )

    getReleaseCodes(
        release_names = (dict_arg_name, key_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition   = "%s == false" % res_name,
        needs_check = statement.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)
