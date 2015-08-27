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
""" Exception handling.

"""

from nuitka.utils import Utils

from .templates. \
    CodeTemplatesExceptions import template_publish_exception_to_handler


def getExceptionIdentifier(exception_type):
    assert "PyExc" not in exception_type, exception_type

    if exception_type == "NotImplemented":
        return "Py_NotImplemented"

    return "PyExc_%s" % exception_type


def getExceptionRefCode(to_name, exception_type, emit, context):
    emit(
        "%s = %s;" % (
            to_name,
            getExceptionIdentifier(exception_type),
        )
    )

    # Lets have context in the API for consistency with everything else.
    assert context


def getTracebackMakingIdentifier(context, lineno_name):
    frame_handle = context.getFrameHandle()
    assert frame_handle is not None

    return "MAKE_TRACEBACK( %s, %s )" % (
        frame_handle,
        lineno_name
    )


def getExceptionCaughtTypeCode(to_name, emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[0] is None:
        emit(
            "%s = PyThreadState_GET()->exc_type;" % (
                to_name,
            )
        )
    else:
        emit(
            "%s = %s;" % (
                to_name,
                keeper_variables[0]
            )
        )


def getExceptionCaughtValueCode(to_name, emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[1] is None:
        emit(
            "%s = PyThreadState_GET()->exc_value;" % (
                to_name,
            )
        )
    else:
        if Utils.python_version >= 270:
            emit(
                "%s = %s;" % (
                    to_name,
                    keeper_variables[1]
                )
            )
        else:
            emit(
                "%s = %s ? %s : Py_None;" % (
                    to_name,
                    keeper_variables[1],
                    keeper_variables[1]
                )
            )


def getExceptionCaughtTracebackCode(to_name, emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[2] is None:
        emit(
            "%s = PyThreadState_GET()->exc_traceback;" % (
                to_name,
            )
        )
    else:
        emit(
            """\
if ( %(keeper_tb)s != NULL )
{
    %(to_name)s = (PyObject *)%(keeper_tb)s;
    Py_INCREF( %(to_name)s );
}
else
{
    %(to_name)s = (PyObject *)%(tb_making)s;
}
""" % {
                "to_name"   : to_name,
                "keeper_tb" : keeper_variables[2],
                "tb_making" : getTracebackMakingIdentifier(
                                 context     = context,
                                 lineno_name = keeper_variables[3]
                              )
            }
        )

        context.addCleanupTempName(to_name)


def getExceptionUnpublishedReleaseCode(emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[0] is not None:
        emit("Py_DECREF( %s );" % keeper_variables[0])
        emit("Py_XDECREF( %s );"  % keeper_variables[1])
        emit("Py_XDECREF( %s );"  % keeper_variables[2])


def generateExceptionPublishCode(statement, emit, context):
    # This statement has no attributes really, pylint: disable=W0613

    # TODO: Should this be necessary, something else would have required
    # them already, or it's wrong.
    context.markAsNeedsExceptionVariables()

    # Current variables cannot be used anymore now.
    keeper_type, keeper_value, keeper_tb, keeper_lineno = context.setExceptionKeeperVariables(
        (None, None, None, None)
    )

    emit(
        template_publish_exception_to_handler % {
            "tb_making"        : getTracebackMakingIdentifier(
                context     = context,
                lineno_name = keeper_lineno
            ),
            "keeper_tb"        : keeper_tb,
            "keeper_lineno"    : keeper_lineno,
            "frame_identifier" : context.getFrameHandle()
        }
    )

    emit(
        "NORMALIZE_EXCEPTION( &%s, &%s, &%s );" % (
            keeper_type,
            keeper_value,
            keeper_tb
        )
    )

    if Utils.python_version >= 300:
        emit(
            "PyException_SetTraceback( %s, (PyObject *)%s );" % (
                keeper_value,
                keeper_tb
            )
        )

    emit(
        "PUBLISH_EXCEPTION( &%s, &%s, &%s );" % (
            keeper_type,
            keeper_value,
            keeper_tb
        )
    )
