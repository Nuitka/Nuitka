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
""" Code generation for calls.

The different kinds of calls get dedicated code. Most notable, calls with
only positional arguments, are attempted through helpers that might be
able to execute them without creating the argument dictionary at all.

"""

from . import CodeTemplates
from .ErrorCodes import getErrorExitCode, getReleaseCode, getReleaseCodes
from .ExceptionCodes import getExceptionIdentifier
from .LineNumberCodes import emitLineNumberUpdateCode


def getCallCodeNoArgs(to_name, called_name, emit, context):
    emitLineNumberUpdateCode(context, emit)

    emit(
        "%s = CALL_FUNCTION_NO_ARGS( %s );" % (
            to_name,
            called_name
        )
    )

    getReleaseCode(
        release_name = called_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name  = to_name,
        emit        = emit,
        context     = context
    )

    context.addCleanupTempName(to_name)



# Outside helper code relies on some quick call to be present.
quick_calls_used = set( [ 1, 2, 3 ] )

def getCallCodePosArgsQuick(to_name, called_name, arg_names, emit, context):

    arg_size = len(arg_names)
    quick_calls_used.add(arg_size)

    # For 0 arguments, NOARGS is supposed to be used.
    assert arg_size > 0

    emitLineNumberUpdateCode(context, emit)

    emit(
        "%s = CALL_FUNCTION_WITH_ARGS%d( %s, %s );" % (
            to_name,
            arg_size,
            called_name,
            ", ".join(arg_names)
        )
    )

    getReleaseCodes(
        release_names = [called_name] + arg_names,
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getCallCodePosArgs(to_name, called_name, args_name, emit, context):
    emitLineNumberUpdateCode(context, emit)

    emit(
        "%s = CALL_FUNCTION_WITH_POSARGS( %s, %s );" % (
            to_name,
            called_name,
            args_name
        )
    )

    getReleaseCodes(
        release_names = (called_name, args_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getCallCodeKeywordArgs(to_name, called_name, call_kw_name, emit, context):
    emitLineNumberUpdateCode(context, emit)

    emit(
        "%s = CALL_FUNCTION_WITH_KEYARGS( %s, %s );" % (
            to_name,
            called_name,
            call_kw_name
        )
    )

    getReleaseCodes(
        release_names = (called_name, call_kw_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getCallCodePosKeywordArgs(to_name, called_name, call_args_name,
                              call_kw_name, emit, context):
    emitLineNumberUpdateCode(context, emit)

    emit(
        "%s = CALL_FUNCTION( %s, %s, %s );" % (
            to_name,
            called_name,
            call_args_name,
            call_kw_name
        )
    )

    getReleaseCodes(
        release_names = (called_name, call_args_name, call_kw_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getCallsDecls():
    result = []

    for quick_call_used in sorted(quick_calls_used):
        args_decl = [
            "PyObject *arg%d" % d
            for d in range(quick_call_used)
        ]

        result.append(
            CodeTemplates.template_call_function_with_args_decl % {
                "args_decl"  : ", ".join(args_decl),
                "args_count" : quick_call_used
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_CALLS_H__",
        "header_body"       : "\n".join(result)
    }


def getCallsCode():
    result = []

    result.append(
        CodeTemplates.template_helper_impl_decl % {}
    )

    result.append(
        CodeTemplates.template_call_cpython_function_fast_impl % {}
    )

    for quick_call_used in sorted( quick_calls_used ):
        args_decl = [
            "PyObject *arg%d" % d
            for d in range(1, quick_call_used + 1)
        ]
        args_list = [
            "arg%d" % d
            for d in range(1, quick_call_used + 1)
        ]

        result.append(
            CodeTemplates.template_call_function_with_args_impl % {
                "args_decl"  : ", ".join(args_decl),
                "args_list"  : ", ".join(args_list),
                "args_count" : quick_call_used
            }
        )

    return "\n".join(result)


def getMakeBuiltinExceptionCode(to_name, exception_type, arg_names, emit,
                                context):
    if arg_names:
        getCallCodePosArgsQuick(
            to_name     = to_name,
            called_name = getExceptionIdentifier(exception_type),
            arg_names   = arg_names,
            emit        = emit,
            context     = context
        )

    else:
        getCallCodeNoArgs(
            to_name     = to_name,
            called_name = getExceptionIdentifier(exception_type),
            emit        = emit,
            context     = context
        )
