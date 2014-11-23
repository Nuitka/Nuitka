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
""" Exception handling.

"""

from nuitka import Utils


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


def getTracebackMakingIdentifier(context):
    frame_handle = context.getFrameHandle()
    assert frame_handle is not None

    return "MAKE_TRACEBACK( INCREASE_REFCOUNT( %s ) )" % (
        frame_handle
    )


def getExceptionCaughtTypeCode(to_name, emit, context):
    if context.isExceptionPublished():
        emit(
            "%s = PyThreadState_GET()->exc_type;" % (
                to_name,
            )
        )
    else:
        emit(
            "%s = exception_type;" % (
                to_name,
            )
        )


def getExceptionCaughtValueCode(to_name, emit, context):
    if context.isExceptionPublished():
        emit(
            "%s = PyThreadState_GET()->exc_value;" % (
                to_name,
            )
        )
    else:
        if Utils.python_version >= 270:
            emit(
                "%s = exception_value;" % (
                    to_name,
                )
            )
        else:
            emit(
                "%s = exception_value ? exception_value : Py_None;" % (
                    to_name,
                )
            )


def getExceptionCaughtTracebackCode(to_name, emit, context):
    if context.isExceptionPublished():
        emit(
            "%s = PyThreadState_GET()->exc_traceback;" % (
                to_name,
            )
        )
    else:
        emit(
            "%s = exception_tb ? INCREASE_REFCOUNT( (PyObject *)exception_tb ) : (PyObject *)%s;" % (
                to_name,
                getTracebackMakingIdentifier(context)
            )
        )

        context.addCleanupTempName(to_name)


def getExceptionUnpublishedReleaseCode(emit, context):
    if not context.isExceptionPublished():
        emit("Py_DECREF( exception_type );")
        emit("Py_XDECREF( exception_value );")
        emit("Py_XDECREF( exception_tb );")
