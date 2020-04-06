#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.PythonVersions import python_version

from .ExceptionCodes import getExceptionIdentifier
from .Indentation import getCommentCode, indented
from .LineNumberCodes import getErrorLineNumberUpdateCode
from .templates.CodeTemplatesExceptions import (
    template_error_catch_exception,
    template_error_catch_quick_exception,
    template_error_format_string_exception,
)


def getErrorExitReleaseCode(context):
    temp_release = "\n".join(
        "Py_DECREF(%s);" % tmp_name for tmp_name in context.getCleanupTempnames()
    )

    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[0] is not None:
        temp_release += "\nPy_DECREF(%s);" % keeper_variables[0]
        temp_release += "\nPy_XDECREF(%s);" % keeper_variables[1]
        temp_release += "\nPy_XDECREF(%s);" % keeper_variables[2]

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
    needs_check=True,
    quick_exception=None,
):
    assert not condition.endswith(";")

    if release_names:
        getReleaseCodes(release_names, emit, context)
        assert not release_name

    if release_name is not None:
        getReleaseCode(release_name, emit, context)
        assert not release_names

    if not needs_check:
        getAssertionCode("!(%s)" % condition, emit)
        return

    exception_type, exception_value, exception_tb, _exception_lineno = (
        context.variable_storage.getExceptionVariableDescriptions()
    )

    if quick_exception:
        emit(
            indented(
                template_error_catch_quick_exception
                % {
                    "condition": condition,
                    "exception_type": exception_type,
                    "exception_value": exception_value,
                    "exception_tb": exception_tb,
                    "exception_exit": context.getExceptionEscape(),
                    "quick_exception": getExceptionIdentifier(quick_exception),
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
                    "exception_type": exception_type,
                    "exception_value": exception_value,
                    "exception_tb": exception_tb,
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
    quick_exception=None,
    needs_check=True,
):
    getErrorExitBoolCode(
        condition=check_name.getCType().getExceptionCheckCondition(check_name),
        release_names=release_names,
        release_name=release_name,
        needs_check=needs_check,
        quick_exception=quick_exception,
        emit=emit,
        context=context,
    )


def getErrorFormatExitBoolCode(condition, exception, args, emit, context):
    assert not condition.endswith(";")

    exception_type, exception_value, exception_tb, _exception_lineno = (
        context.variable_storage.getExceptionVariableDescriptions()
    )

    if len(args) == 1 and type(args[0]) is str:
        from .ConstantCodes import getModuleConstantCode

        set_exception = [
            "%s = %s;" % (exception_type, exception),
            "Py_INCREF(%s);" % exception_type,
            "%s = %s;" % (exception_value, getModuleConstantCode(constant=args[0])),
            "%s = NULL;" % exception_tb,
        ]
    else:
        set_exception = [
            "%s = %s;" % (exception_type, exception),
            "Py_INCREF(%s);" % exception_type,
            "%s = Py%s_FromFormat(%s);"
            % (
                exception_value,
                "String" if python_version < 300 else "Unicode",
                ", ".join('"%s"' % arg for arg in args),
            ),
            "%s = NULL;" % exception_tb,
        ]

    if python_version >= 300:
        keeper_vars = context.getExceptionKeeperVariables()

        if keeper_vars[0] is not None:
            set_exception.append(
                "ADD_EXCEPTION_CONTEXT(&%s, &%s);" % (keeper_vars[0], keeper_vars[1])
            )
        else:
            set_exception.append(
                "NORMALIZE_EXCEPTION(&%s, &%s, &%s);"
                % (exception_type, exception_value, exception_tb)
            )
            set_exception.append("CHAIN_EXCEPTION(%s);" % exception_value)

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


def getTakeReferenceCode(value_name, emit):
    # TODO: This should be done via the C type
    if value_name.c_type == "PyObject *":
        emit("Py_INCREF(%s);" % value_name)
    elif value_name.c_type == "nuitka_bool":
        pass
    elif value_name.c_type == "nuitka_void":
        pass
    else:
        assert False, repr(value_name)


def getReleaseCode(release_name, emit, context):
    if context.needsCleanup(release_name):
        # TODO: This should be done via the C type and its getReleaseCode() method, but this
        # one does too much for object, in that it always assigns NULL to the object for no
        # good reason in non-debug mode.
        if release_name.c_type == "PyObject *":
            emit("Py_DECREF(%s);" % release_name)
        elif release_name.c_type == "nuitka_bool":
            pass
        elif release_name.c_type == "nuitka_void":
            pass
        else:
            assert False, repr(release_name)

        context.removeCleanupTempName(release_name)


def getReleaseCodes(release_names, emit, context):
    for release_name in release_names:
        getReleaseCode(release_name=release_name, emit=emit, context=context)


def getMustNotGetHereCode(reason, context, emit):
    getCommentCode(reason, emit)

    provider = context.getEntryPoint()

    emit(
        "NUITKA_CANNOT_GET_HERE(%(function_identifier)s);"
        % {"function_identifier": provider.getCodeName()}
    )
    emit("return NULL;")


def getAssertionCode(check, emit):
    emit("assert(%s);" % check)


def getCheckObjectCode(check_name, emit):
    emit("CHECK_OBJECT(%s);" % check_name)


def getLocalVariableReferenceErrorCode(variable, condition, emit, context):
    if variable.getOwner() is not context.getOwner():
        getErrorFormatExitBoolCode(
            condition=condition,
            exception="PyExc_NameError",
            args=(
                """\
free variable '%s' referenced before assignment in enclosing scope""",
                variable.getName(),
            ),
            emit=emit,
            context=context,
        )
    else:
        getErrorFormatExitBoolCode(
            condition=condition,
            exception="PyExc_UnboundLocalError",
            args=(
                """\
local variable '%s' referenced before assignment""",
                variable.getName(),
            ),
            emit=emit,
            context=context,
        )


def getNameReferenceErrorCode(variable_name, condition, emit, context):
    if python_version < 340:
        owner = context.getOwner()

        if not owner.isCompiledPythonModule() and not owner.isExpressionClassBody():
            error_message = "global name '%s' is not defined"
        else:
            error_message = "name '%s' is not defined"
    else:
        error_message = "name '%s' is not defined"

    error_message = error_message % variable_name

    getErrorFormatExitBoolCode(
        condition=condition,
        exception="PyExc_NameError",
        args=(error_message,),
        emit=emit,
        context=context,
    )
