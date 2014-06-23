#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes


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
    # Both not available must have been optimized way.
    assert seq_name is not None or dict_name is not None

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
    else:
        # TODO: This could be avoided entirely, but it's only an alias, so we
        # leave it to the C++ compiler for now.
        emit(
            "%s = %s;" % (
                to_name,
                dict_name
            )
        )

        if context.needsCleanup(dict_name):
            context.addCleanupTempName(to_name)
            context.removeCleanupTempName(dict_name)


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
