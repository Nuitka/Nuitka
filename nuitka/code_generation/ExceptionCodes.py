#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Exception handling.

"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .templates.CodeTemplatesExceptions import (
    template_publish_exception_to_handler,
)


def getExceptionIdentifier(exception_type):
    assert "PyExc" not in exception_type, exception_type

    if exception_type == "NotImplemented":
        return "Py_NotImplemented"

    return "PyExc_%s" % exception_type


def generateExceptionRefCode(to_name, expression, emit, context):
    exception_type = expression.getExceptionName()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_name", expression, emit, context
    ) as value_name:

        emit("%s = %s;" % (value_name, getExceptionIdentifier(exception_type)))


def getTracebackMakingIdentifier(context, lineno_name):
    frame_handle = context.getFrameHandle()
    assert frame_handle is not None

    return "MAKE_TRACEBACK(%s, %s)" % (frame_handle, lineno_name)


def generateExceptionCaughtTypeCode(to_name, expression, emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_caught_type", expression, emit, context
    ) as value_name:

        if keeper_variables[0] is None:
            emit("%s = EXC_TYPE(PyThreadState_GET());" % (value_name,))
        else:
            emit("%s = %s;" % (value_name, keeper_variables[0]))


def generateExceptionCaughtValueCode(to_name, expression, emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_caught_value", expression, emit, context
    ) as value_name:

        if keeper_variables[1] is None:
            emit("%s = EXC_VALUE(PyThreadState_GET());" % (value_name,))
        else:
            if python_version >= 0x270:
                emit("%s = %s;" % (value_name, keeper_variables[1]))
            else:
                emit(
                    "%s = %s ? %s : Py_None;"
                    % (value_name, keeper_variables[1], keeper_variables[1])
                )


def generateExceptionCaughtTracebackCode(to_name, expression, emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_caught_tb", expression, emit, context
    ) as value_name:

        if keeper_variables[2] is None:
            emit("%s = EXC_TRACEBACK(PyThreadState_GET());" % (value_name,))
        else:
            emit(
                """\
if (%(keeper_tb)s != NULL) {
    %(to_name)s = (PyObject *)%(keeper_tb)s;
    Py_INCREF(%(to_name)s);
} else {
    %(to_name)s = (PyObject *)%(tb_making)s;
}
"""
                % {
                    "to_name": value_name,
                    "keeper_tb": keeper_variables[2],
                    "tb_making": getTracebackMakingIdentifier(
                        context=context, lineno_name=keeper_variables[3]
                    ),
                }
            )

            context.addCleanupTempName(value_name)


def getExceptionUnpublishedReleaseCode(emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[0] is not None:
        emit("Py_DECREF(%s);" % keeper_variables[0])
        emit("Py_XDECREF(%s);" % keeper_variables[1])
        emit("Py_XDECREF(%s);" % keeper_variables[2])


def generateExceptionPublishCode(statement, emit, context):
    # This statement has no attributes really, pylint: disable=unused-argument

    # Current variables cannot be used anymore now.
    (
        keeper_type,
        keeper_value,
        keeper_tb,
        keeper_lineno,
    ) = context.setExceptionKeeperVariables((None, None, None, None))

    emit(
        template_publish_exception_to_handler
        % {
            "tb_making": getTracebackMakingIdentifier(
                context=context, lineno_name=keeper_lineno
            ),
            "keeper_tb": keeper_tb,
            "keeper_lineno": keeper_lineno,
            "frame_identifier": context.getFrameHandle(),
        }
    )

    # TODO: Make this one thing for performance with thread state shared, also for less code,
    # then we should not make it in header anymore. Might be more scalable too.
    emit(
        "PUBLISH_CURRENT_EXCEPTION(&%s, &%s, &%s);"
        % (keeper_type, keeper_value, keeper_tb)
    )


def generateBuiltinMakeExceptionCode(to_name, expression, emit, context):
    # We try to make optimal code for various cases, pylint: disable=too-many-locals

    from .CallCodes import getCallCodeNoArgs, getCallCodePosArgsQuick

    exception_arg_names = []

    for exception_arg in expression.subnode_args:
        exception_arg_name = context.allocateTempName("make_exception_arg")

        generateExpressionCode(
            to_name=exception_arg_name,
            expression=exception_arg,
            emit=emit,
            context=context,
        )

        exception_arg_names.append(exception_arg_name)

    exception_type = expression.getExceptionName()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_made", expression, emit, context
    ) as value_name:

        if exception_arg_names:
            getCallCodePosArgsQuick(
                to_name=value_name,
                called_name=getExceptionIdentifier(exception_type),
                expression=expression,
                arg_names=exception_arg_names,
                needs_check=False,
                emit=emit,
                context=context,
            )

        else:
            getCallCodeNoArgs(
                to_name=value_name,
                called_name=getExceptionIdentifier(exception_type),
                expression=expression,
                needs_check=False,
                emit=emit,
                context=context,
            )

        if expression.getExceptionName() == "ImportError" and python_version >= 0x300:
            from .PythonAPICodes import getReferenceExportCode

            import_error_name_expression = expression.subnode_name

            if import_error_name_expression is not None:
                exception_importerror_name = context.allocateTempName(
                    "make_exception_importerror_name"
                )

                generateExpressionCode(
                    to_name=exception_importerror_name,
                    expression=import_error_name_expression,
                    emit=emit,
                    context=context,
                    allow_none=True,
                )

                getReferenceExportCode(exception_importerror_name, emit, context)
                if context.needsCleanup(exception_importerror_name):
                    context.removeCleanupTempName(exception_importerror_name)

                emit(
                    "((PyImportErrorObject *)%s)->name = %s;"
                    % (to_name, exception_importerror_name)
                )

            import_error_path_expression = expression.subnode_path

            if import_error_path_expression is not None:
                exception_importerror_path = context.allocateTempName(
                    "make_exception_importerror_path"
                )

                generateExpressionCode(
                    to_name=exception_importerror_path,
                    expression=import_error_path_expression,
                    emit=emit,
                    context=context,
                    allow_none=True,
                )

                getReferenceExportCode(exception_importerror_path, emit, context)
                if context.needsCleanup(exception_importerror_path):
                    context.removeCleanupTempName(exception_importerror_path)

                emit(
                    "((PyImportErrorObject *)%s)->path = %s;"
                    % (to_name, exception_importerror_path)
                )
