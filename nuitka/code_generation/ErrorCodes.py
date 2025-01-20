#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Error codes

These are the helper functions that will emit the error exit codes. They
can abstractly check conditions or values directly. The release of statement
temporaries from context is automatic.

Also formatting errors is done here, avoiding PyErr_Format as much as
possible.

And releasing of values, as this is what the error case commonly does.

"""

from nuitka.PythonVersions import python_version

from .Indentation import indented
from .LineNumberCodes import getErrorLineNumberUpdateCode
from .templates.CodeTemplatesExceptions import (
    template_error_catch_exception,
    template_error_catch_fetched_exception,
    template_error_format_name_error_exception,
    template_error_format_string_exception,
)


def getErrorExitReleaseCode(context):
    temp_release = "\n".join(
        "Py_DECREF(%s);" % tmp_name for tmp_name in context.getCleanupTempNames()
    )

    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    if keeper_exception_state_name is not None:
        temp_release += (
            "\nRELEASE_ERROR_OCCURRED_STATE(&%s);" % keeper_exception_state_name
        )

    return temp_release


def getFrameVariableTypeDescriptionCode(context):
    type_description = context.getFrameVariableTypeDescription()

    if type_description:
        return '%s = "%s";' % (
            context.getFrameTypeDescriptionDeclaration(),
            type_description,
        )
    else:
        return ""


def getErrorExitBoolCode(
    condition,
    emit,
    context,
    release_names=(),
    release_name=None,
    fetched_exception=False,
    needs_check=True,
):
    assert not condition.endswith(";")

    if release_names:
        getReleaseCodes(release_names, emit, context)
        assert not release_name

    if release_name is not None:
        assert type(release_name) is not tuple
        getReleaseCode(release_name, emit, context)
        assert not release_names

    if not needs_check:
        getAssertionCode("!(%s)" % condition, emit)
        return

    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    if fetched_exception:
        emit(
            indented(
                template_error_catch_fetched_exception
                % {
                    "condition": condition,
                    "exception_state_name": exception_state_name,
                    "exception_exit": context.getExceptionEscape(),
                    "release_temps": indented(getErrorExitReleaseCode(context)),
                    "var_description_code": indented(
                        getFrameVariableTypeDescriptionCode(context)
                    ),
                    "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
                },
                0,
            )
        )
    else:
        emit(
            indented(
                template_error_catch_exception
                % {
                    "condition": condition,
                    "exception_state_name": exception_state_name,
                    "exception_exit": context.getExceptionEscape(),
                    "release_temps": indented(getErrorExitReleaseCode(context)),
                    "var_description_code": indented(
                        getFrameVariableTypeDescriptionCode(context)
                    ),
                    "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
                },
                0,
            )
        )


def getErrorExitCode(
    check_name,
    emit,
    context,
    release_names=(),
    release_name=None,
    fetched_exception=False,
    needs_check=True,
):
    getErrorExitBoolCode(
        condition=check_name.getCType().getExceptionCheckCondition(check_name),
        release_names=release_names,
        release_name=release_name,
        needs_check=needs_check,
        fetched_exception=fetched_exception,
        emit=emit,
        context=context,
    )


def _getExceptionChainingCode(context):
    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    if keeper_exception_state_name is not None:
        yield "ADD_EXCEPTION_CONTEXT(tstate, &%s);" % keeper_exception_state_name
    else:
        if python_version < 0x3C0:
            yield "NORMALIZE_EXCEPTION_STATE(tstate, &%s);" % exception_state_name

        yield "CHAIN_EXCEPTION(tstate, %s.exception_value);" % exception_state_name


def getTakeReferenceCode(value_name, emit):
    value_name.getCType().getTakeReferenceCode(value_name=value_name, emit=emit)


def getReleaseCode(release_name, emit, context):
    if context.needsCleanup(release_name):
        release_name.getCType().getReleaseCode(
            value_name=release_name, needs_check=False, emit=emit
        )

        context.removeCleanupTempName(release_name)


def getReleaseCodes(release_names, emit, context):
    for release_name in release_names:
        getReleaseCode(release_name=release_name, emit=emit, context=context)


def getMustNotGetHereCode(reason, emit):
    emit(
        """\
NUITKA_CANNOT_GET_HERE("%s");
return NULL;"""
        % reason
    )


def getAssertionCode(check, emit):
    emit("assert(%s);" % check)


def getLocalVariableReferenceErrorCode(variable, condition, emit, context):
    variable_name = variable.getName()

    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    if variable.getOwner() is not context.getOwner():
        helper_code = "FORMAT_UNBOUND_CLOSURE_ERROR"
    else:
        helper_code = "FORMAT_UNBOUND_LOCAL_ERROR"

    set_exception = [
        "%s(tstate, &%s, %s);"
        % (
            helper_code,
            exception_state_name,
            context.getConstantCode(variable_name),
        ),
    ]

    # TODO: Move this into the helper code.
    if python_version >= 0x300:
        set_exception.extend(_getExceptionChainingCode(context))

    emit(
        template_error_format_string_exception
        % {
            "condition": condition,
            "exception_exit": context.getExceptionEscape(),
            "set_exception": indented(set_exception),
            "release_temps": indented(getErrorExitReleaseCode(context)),
            "var_description_code": indented(
                getFrameVariableTypeDescriptionCode(context)
            ),
            "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
        }
    )


# TODO: Get rid of this function entirely.
def getNameReferenceErrorCode(variable_name, condition, emit, context):
    helper_code = "RAISE_CURRENT_EXCEPTION_NAME_ERROR"

    if python_version < 0x300:
        owner = context.getOwner()

        if not owner.isCompiledPythonModule() and not owner.isExpressionClassBodyBase():
            helper_code = "RAISE_CURRENT_EXCEPTION_GLOBAL_NAME_ERROR"

    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    emit(
        template_error_format_name_error_exception
        % {
            "condition": condition,
            "exception_exit": context.getExceptionEscape(),
            "raise_name_error_helper": helper_code,
            "variable_name": context.getConstantCode(variable_name),
            "release_temps": indented(getErrorExitReleaseCode(context)),
            "var_description_code": indented(
                getFrameVariableTypeDescriptionCode(context)
            ),
            "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
            "exception_state_name": exception_state_name,
        }
    )


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
