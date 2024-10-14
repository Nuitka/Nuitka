#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Exception handling.

"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitCode
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
    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_caught_type", expression, emit, context
    ) as value_name:
        if keeper_exception_state_name is None:
            emit("%s = EXC_TYPE(tstate);" % (value_name,))
        else:
            if python_version < 0x3C0:
                emit(
                    "%s = %s.exception_type;"
                    % (value_name, keeper_exception_state_name)
                )
            else:
                emit(
                    "%s = %s.exception_value;"
                    % (value_name, keeper_exception_state_name)
                )


def generateExceptionCaughtValueCode(to_name, expression, emit, context):
    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_caught_value", expression, emit, context
    ) as value_name:
        if keeper_exception_state_name is None:
            emit("%s = EXC_VALUE(tstate);" % value_name)
        elif python_version >= 0x270:
            emit("%s = %s.exception_value;" % (value_name, keeper_exception_state_name))
        else:
            # For Python2.6, value can be NULL.
            emit(
                "%s = %s.exception_value ? %s.exception_value : Py_None;"
                % (
                    value_name,
                    keeper_exception_state_name,
                    keeper_exception_state_name,
                )
            )

        emit("CHECK_OBJECT(%s); " % value_name)


def generateExceptionCaughtTracebackCode(to_name, expression, emit, context):
    (
        keeper_exception_state_name,
        keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    with withObjectCodeTemporaryAssignment(
        to_name, "exception_caught_tb", expression, emit, context
    ) as value_name:
        if keeper_exception_state_name is None:
            if python_version < 0x3B0:
                emit("%s = (PyObject *)EXC_TRACEBACK(tstate);" % (value_name,))
            else:
                emit(
                    """\
%(value_name)s = (PyObject *)GET_EXCEPTION_TRACEBACK(EXC_VALUE(tstate));
if (%(value_name)s == NULL) {
    %(value_name)s = Py_None;
}"""
                    % {"value_name": value_name}
                )

        else:
            emit(
                """\
if (%(keeper_exception_state_name)s.exception_tb != NULL) {
    %(to_name)s = (PyObject *)%(keeper_exception_state_name)s.exception_tb;
    Py_INCREF(%(to_name)s);
} else {
    %(to_name)s = (PyObject *)%(tb_making)s;
}
"""
                % {
                    "to_name": value_name,
                    "keeper_exception_state_name": keeper_exception_state_name,
                    "tb_making": getTracebackMakingIdentifier(
                        context=context, lineno_name=keeper_lineno
                    ),
                }
            )

            context.addCleanupTempName(value_name)


def getExceptionUnpublishedReleaseCode(emit, context):
    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    if keeper_exception_state_name is not None:
        emit("RELEASE_ERROR_OCCURRED_STATE(&%s);" % keeper_exception_state_name)


def generateExceptionPublishCode(statement, emit, context):
    # This statement has no attributes really, pylint: disable=unused-argument

    # Current variables cannot be used anymore now.
    (
        keeper_exception_state_name,
        keeper_lineno,
    ) = context.setExceptionKeeperVariables((None, None))

    emit(
        template_publish_exception_to_handler
        % {
            "tb_making": getTracebackMakingIdentifier(
                context=context, lineno_name=keeper_lineno
            ),
            "keeper_exception_state_name": keeper_exception_state_name,
            "keeper_lineno": keeper_lineno,
            "frame_identifier": context.getFrameHandle(),
        }
    )

    # TODO: Make this one thing for performance with thread state shared, also for less code,
    # then we should not make it in header anymore. Might be more scalable too.
    emit("PUBLISH_CURRENT_EXCEPTION(tstate, &%s);" % keeper_exception_state_name)


def _attachExceptionAttributeCode(
    to_name,
    attribute_expression,
    c_type_name,
    c_attribute_name,
    base_name_str,
    emit,
    context,
):
    if attribute_expression is not None:
        from .PythonAPICodes import getReferenceExportCode

        exception_attribute_name = context.allocateTempName(
            base_name_str + "_" + c_attribute_name
        )

        generateExpressionCode(
            to_name=exception_attribute_name,
            expression=attribute_expression,
            emit=emit,
            context=context,
            allow_none=True,
        )

        getReferenceExportCode(exception_attribute_name, emit, context)
        if context.needsCleanup(exception_attribute_name):
            context.removeCleanupTempName(exception_attribute_name)

        emit(
            "((%s *)%s)->%s = %s;"
            % (c_type_name, to_name, c_attribute_name, exception_attribute_name)
        )


def _generateBuiltinMakeExceptionCode(to_name, expression, for_raise, emit, context):
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
        exception_name = getExceptionIdentifier(exception_type)

        if len(exception_arg_names) == 1 and for_raise:
            emit(
                "%s = MAKE_EXCEPTION_WITH_VALUE(tstate, %s, %s);"
                % (value_name, exception_name, exception_arg_names[0])
            )

            getErrorExitCode(
                check_name=value_name,
                release_names=exception_arg_names,
                needs_check=expression.mayRaiseExceptionOperation(),
                emit=emit,
                context=context,
            )

            context.addCleanupTempName(value_name)
        elif exception_arg_names:
            getCallCodePosArgsQuick(
                to_name=value_name,
                called_name=exception_name,
                expression=expression,
                arg_names=exception_arg_names,
                emit=emit,
                context=context,
            )

        else:
            getCallCodeNoArgs(
                to_name=value_name,
                called_name=exception_name,
                expression=expression,
                emit=emit,
                context=context,
            )

        if (
            expression.isExpressionBuiltinMakeExceptionImportError()
            or expression.isExpressionBuiltinMakeExceptionModuleNotFoundError()
        ):
            _attachExceptionAttributeCode(
                to_name=to_name,
                attribute_expression=expression.subnode_name,
                base_name_str="exception_import_error",
                c_type_name="PyImportErrorObject",
                c_attribute_name="name",
                emit=emit,
                context=context,
            )

            _attachExceptionAttributeCode(
                to_name=to_name,
                attribute_expression=expression.subnode_path,
                base_name_str="exception_import_error",
                c_type_name="PyImportErrorObject",
                c_attribute_name="path",
                emit=emit,
                context=context,
            )

        elif expression.isExpressionBuiltinMakeExceptionAttributeError():
            _attachExceptionAttributeCode(
                to_name=to_name,
                attribute_expression=expression.subnode_name,
                base_name_str="exception_import_error",
                c_type_name="PyAttributeErrorObject",
                c_attribute_name="name",
                emit=emit,
                context=context,
            )

            _attachExceptionAttributeCode(
                to_name=to_name,
                attribute_expression=expression.subnode_obj,
                base_name_str="exception_import_error",
                c_type_name="PyAttributeErrorObject",
                c_attribute_name="obj",
                emit=emit,
                context=context,
            )


def generateBuiltinMakeExceptionCode(to_name, expression, emit, context):
    _generateBuiltinMakeExceptionCode(
        to_name=to_name,
        expression=expression,
        for_raise=expression.for_raise,
        emit=emit,
        context=context,
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
