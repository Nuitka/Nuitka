#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Error codes

These are the helper functions that will emit the error exit codes. They
can abstractly check conditions or values directly. The release of statement
temporaries from context is automatic.

Also formatting errors is done here, avoiding PyErr_Format as much as
possible.

And releasing of values, as this is what the error case commonly does.

"""

from nuitka.PythonVersions import python_version

from .DeferredReleaseCodes import getDeferredReleaseErrorCode
from .Indentation import indented
from .LineNumberCodes import getErrorLineNumberUpdateCode
from .templates.CodeTemplatesExceptions import (
    template_error_catch_exception,
    template_error_catch_fetched_exception,
    template_error_format_name_error_exception,
    template_error_format_string_exception,
)


def getErrorExitReleaseCode(context):
    temp_release = []

    for tmp_name in context.getCleanupTempNames():
        # Drop the owning reference.
        temp_release.append("Py_DECREF(%s);" % tmp_name)

        if context.isDeferredReleaseName(tmp_name):
            # Release the deferred reference only when nothing else
            # references the value.
            deferred_code = getDeferredReleaseErrorCode(
                context=context,
                tmp_name=tmp_name,
                release_info=context.getDeferredReleaseNames()[tmp_name],
            )

            if deferred_code is not None:
                temp_release.append(deferred_code)

    temp_release = "\n".join(temp_release)

    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    if keeper_exception_state_name is not None:
        temp_release += (
            "\nRELEASE_ERROR_OCCURRED_STATE(&%s);" % keeper_exception_state_name
        )

    return temp_release


def getErrorExitBoolCode(
    condition,
    emit,
    context,
    release_names=(),
    release_name=None,
    fetched_exception=False,
    needs_check=True,
):
    """Emit error exit code based on a condition.

    Args:
        condition: C boolean expression checking for error.
        emit: Function to emit code.
        context: Code generation context.
        release_names: Tuple/list of variable names to release, None entries are allowed.
        release_name: Single variable name to release.
        fetched_exception: Whether exception is already fetched.
        needs_check: Whether validation of condition is needed.

    Notes:
        `release_name` and `release_names` are mutually exclusive.
        Use `release_name` for a single variable, `release_names` for multiple.
    """
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
    ) = context.getExceptionVariableDescriptions()

    if fetched_exception:
        emit(
            template_error_catch_fetched_exception
            % {
                "condition": condition,
                "exception_state_name": exception_state_name,
                "exception_exit": context.getExceptionEscape(),
                "release_temps": indented(getErrorExitReleaseCode(context)),
                "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
            }
        )
    else:
        emit(
            template_error_catch_exception
            % {
                "condition": condition,
                "exception_state_name": exception_state_name,
                "exception_exit": context.getExceptionEscape(),
                "release_temps": indented(getErrorExitReleaseCode(context)),
                "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
            }
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
    """Emit error exit code by checking a variable.

    Args:
        check_name: Variable to check for error condition.
        emit: Function to emit code.
        context: Code generation context.
        release_names: Tuple/list of variable names to release.
        release_name: Single variable name to release.
        fetched_exception: Whether exception is already fetched.
        needs_check: Whether validation of condition is needed.

    Notes:
        `release_name` and `release_names` are mutually exclusive.
        Use `release_name` for a single variable, `release_names` for multiple.
    """
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
    ) = context.getExceptionVariableDescriptions()

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
        # Note: Deferred release values additionally keep a pinned reference
        # that is released at the end of the statement.
        release_name.getCType().getReleaseCode(
            value_name=release_name, needs_check=False, emit=emit
        )

        context.removeCleanupTempName(release_name)


def getReleaseCodes(release_names, emit, context):
    for release_name in release_names:
        getReleaseCode(release_name=release_name, emit=emit, context=context)


def getMustNotGetHereCode(reason, emit):
    emit("""\
NUITKA_CANNOT_GET_HERE("%s");
return NULL;""" % reason)


def getAssertionCode(check, emit):
    emit("assert(%s);" % check)


def _getFrameVariableErrorCode(
    variable,
    exception_state_name,
    keeper_exception_state_code,
    frame_identifier,
    context,
):
    """Get the exception setting for a variable with a frame, or None.

    The variable name is resolved from the frame's code object, using the
    local variable index or the closure variable index, depending on where
    the variable is found, so no string constant is needed.

    Args:
        variable: Variable that is accessed.
        exception_state_name: Name of the exception state variable.
        keeper_exception_state_code: Code for the keeper exception state, or "NULL".
        frame_identifier: Variable declaration of the frame object, or None.
        context: Code generation context.

    Returns:
        Code that sets the exception, or None if unavailable.
    """
    owner = variable.getOwner()

    if owner.isExpressionOutlineFunctionBase():
        owner = owner.getEntryPoint()

    user = context.getOwner().getEntryPoint()

    if owner is not user:
        closure_variables = user.getClosureVariables()

        assert frame_identifier is not None
        assert variable in closure_variables, (variable, closure_variables)

        return "Nuitka_Frame_FormatUnboundClosureError(tstate, &%s, %s, %s, %d);" % (
            exception_state_name,
            keeper_exception_state_code,
            frame_identifier,
            closure_variables.index(variable),
        )

    if frame_identifier is not None:
        frame_variables = context.getFrameVariables()

        if variable in frame_variables:
            return "Nuitka_Frame_FormatUnboundLocalError(tstate, &%s, %s, %s, %d);" % (
                exception_state_name,
                keeper_exception_state_code,
                frame_identifier,
                frame_variables.index(variable),
            )

    return None


def getLocalVariableReferenceErrorCode(variable, condition, emit, context):
    variable_name = variable.getName()

    (
        exception_state_name,
        _exception_lineno,
    ) = context.getExceptionVariableDescriptions()

    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    if keeper_exception_state_name is not None:
        keeper_exception_state_code = "&%s" % keeper_exception_state_name
    else:
        keeper_exception_state_code = "NULL"

    frame_identifier = context.getFrameHandle()

    frame_error_code = _getFrameVariableErrorCode(
        variable=variable,
        exception_state_name=exception_state_name,
        keeper_exception_state_code=keeper_exception_state_code,
        frame_identifier=frame_identifier,
        context=context,
    )

    if frame_error_code is not None:
        set_exception = [frame_error_code]
    else:
        # Without a frame or frame variables, only the spurious local variable
        # checks that should not exist can occur. Closures always have a frame.
        set_exception = [
            "FORMAT_UNBOUND_LOCAL_ERROR(tstate, &%s, %s);"
            % (
                exception_state_name,
                context.getConstantCode(variable_name),
            ),
        ]

        if python_version >= 0x300:
            set_exception.extend(_getExceptionChainingCode(context))

    emit(
        template_error_format_string_exception
        % {
            "condition": condition,
            "exception_exit": context.getExceptionEscape(),
            "set_exception": indented(set_exception),
            "release_temps": indented(getErrorExitReleaseCode(context)),
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
    ) = context.getExceptionVariableDescriptions()

    emit(
        template_error_format_name_error_exception
        % {
            "condition": condition,
            "exception_exit": context.getExceptionEscape(),
            "raise_name_error_helper": helper_code,
            "variable_name": context.getConstantCode(variable_name),
            "release_temps": indented(getErrorExitReleaseCode(context)),
            "line_number_code": indented(getErrorLineNumberUpdateCode(context)),
            "exception_state_name": exception_state_name,
        }
    )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
