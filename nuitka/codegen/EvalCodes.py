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
""" Eval/exec/execfile/compile built-in related codes. """

from nuitka.Utils import python_version

from .ConstantCodes import getConstantCode
from .ErrorCodes import getErrorExitCode, getReleaseCode, getReleaseCodes
from .GlobalsLocalsCodes import getStoreLocalsCode


def getCompileCode(to_name, source_name, filename_name, mode_name,
                   flags_name, dont_inherit_name, optimize_name, emit, context):

    if python_version < 300:
        args = (
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name
        )
    else:
        args = (
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name,
            optimize_name
        )

    emit(
        "%s = COMPILE_CODE( %s );" % (
            to_name,
            ", ".join(args)
        )
    )

    getReleaseCodes(
        release_names = (source_name, filename_name, mode_name, flags_name,
                         dont_inherit_name, optimize_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getEvalCode(to_name, source_name, filename_name, globals_name, locals_name,
                mode_name, emit, context):
    compiled_name = context.allocateTempName("eval_compiled")

    getCompileCode(
        to_name           = compiled_name,
        source_name       = source_name,
        filename_name     = filename_name,
        mode_name         = mode_name,
        flags_name        = "NULL",
        dont_inherit_name = "NULL",
        optimize_name     = "NULL",
        emit              = emit,
        context           = context
    )

    emit(
        "%s = EVAL_CODE( %s, %s, %s );" % (
            to_name,
            compiled_name,
            globals_name,
            locals_name
        )
    )

    getReleaseCodes(
        release_names = (compiled_name, globals_name, locals_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getExecCode(source_name, globals_name, filename_name, locals_name,
                emit, context):
    compiled_name = context.allocateTempName("exec_compiled")

    getCompileCode(
        to_name           = compiled_name,
        source_name       = source_name,
        filename_name     = filename_name,
        mode_name         = getConstantCode(
            constant = "exec",
            context  = context
        ),
        flags_name        = "NULL",
        dont_inherit_name = "NULL",
        optimize_name     = "NULL",
        emit              = emit,
        context           = context
    )

    to_name = context.allocateTempName("exec_result")

    emit(
        "%s = EVAL_CODE( %s, %s, %s );" % (
            to_name,
            compiled_name,
            globals_name,
            locals_name
        )
    )

    getReleaseCodes(
        release_names = (compiled_name, globals_name, locals_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    # Immediately release the exec result.
    context.addCleanupTempName(to_name)
    getReleaseCode(
        release_name = to_name,
        emit         = emit,
        context      = context
    )


def getLocalsDictSyncCode(locals_name, provider, emit, context):
    getStoreLocalsCode(
        locals_name = locals_name,
        provider    = provider,
        emit        = emit,
        context     = context
    )
