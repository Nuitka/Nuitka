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
""" Error codes

These are the helper functions that will emit the error exit codes. They
can abstractly check conditions or values directly. The release of statement
temporaries from context is automatic.

Also formatting errors is done here, avoiding PyErr_Format as much as
possible.

And releasing of values, as this is what the error case commonly does.

"""

from nuitka import Utils

from . import CodeTemplates
from .ExceptionCodes import getExceptionIdentifier
from .Indentation import indented
from .LineNumberCodes import getLineNumberUpdateCode


def getErrorExitReleaseCode(context):
    return '\n'.join(
        "Py_DECREF( %s );" % tmp_name
        for tmp_name in
        context.getCleanupTempnames()
    )



def getErrorExitBoolCode(condition, emit, context, quick_exception = None):
    assert not condition.endswith(';')

    context.markAsNeedsExceptionVariables()

    if quick_exception:
        emit(
            indented(
                CodeTemplates.template_error_catch_quick_exception % {
                    "condition"        : condition,
                    "exception_exit"   : context.getExceptionEscape(),
                    "quick_exception"  : getExceptionIdentifier(quick_exception),
                    "release_temps"    : indented(
                        getErrorExitReleaseCode(context)
                    ),
                    "line_number_code" : indented(
                        getLineNumberUpdateCode(context)
                    )
                },
                0
            )
        )
    else:
        emit(
            indented(
                CodeTemplates.template_error_catch_exception % {
                    "condition"        : condition,
                    "exception_exit"   : context.getExceptionEscape(),
                    "release_temps"    : indented(
                        getErrorExitReleaseCode(context)
                    ),
                    "line_number_code" : indented(
                        getLineNumberUpdateCode(context)
                    )
                },
                0
            )
        )


def getErrorExitCode(check_name, emit, context, quick_exception = None):
    getErrorExitBoolCode(
        condition       = "%s == NULL" % check_name,
        quick_exception = quick_exception,
        emit            = emit,
        context         = context
    )


def getErrorFormatExitBoolCode(condition, exception, args, emit, context):
    assert not condition.endswith(';')

    context.markAsNeedsExceptionVariables()

    if len(args) == 1:
        from .ConstantCodes import getModuleConstantCode

        set_exception = [
            "exception_type = %s;" % exception,
            "Py_INCREF( exception_type );",
            "exception_value = %s;" % getModuleConstantCode(
                constant = args[0],
            ),
            "exception_tb = NULL;"
        ]
    else:
        assert False, args


    if Utils.python_version >= 300 and context.isExceptionPublished():
        set_exception += [
            "ADD_EXCEPTION_CONTEXT( &exception_type, &exception_value );",
        ]

    emit(
        CodeTemplates.template_error_format_string_exception % {
            "condition"        : condition,
            "exception_exit"   : context.getExceptionEscape(),
            "set_exception"    : indented(set_exception),
            "release_temps"    : indented(
                getErrorExitReleaseCode(context)
            ),
            "line_number_code" : indented(
                getLineNumberUpdateCode(context)
            )
        }
    )


def getErrorFormatExitCode(check_name, exception, args, emit, context):
    getErrorFormatExitBoolCode(
        condition = "%s == NULL" % check_name,
        exception = exception,
        args      = args,
        emit      = emit,
        context   = context
    )


def getReleaseCode(release_name, emit, context):
    assert release_name is None or len(release_name) > 2

    if context.needsCleanup(release_name):
        emit("Py_DECREF( %s );" % release_name)
        context.removeCleanupTempName(release_name)


def getReleaseCodes(release_names, emit, context):
    for release_name in release_names:
        getReleaseCode(
            release_name = release_name,
            emit         = emit,
            context      = context
        )
