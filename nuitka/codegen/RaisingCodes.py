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
""" Code generation for implicit and explict exception raises.

Exceptions from other operations are consider ErrorCodes domain.

"""

from .LineNumberCodes import getLineNumberUpdateCode
from .PythonAPICodes import getReferenceExportCode


def getReRaiseExceptionCode(emit, context):
    assert context.getExceptionEscape() is not None

    if context.isExceptionPublished():
        emit(
            """\
RERAISE_EXCEPTION( &exception_type, &exception_value, &exception_tb );"""
        )

        frame_handle = context.getFrameHandle()

        if frame_handle:
            emit(
                """\
    if (exception_tb && exception_tb->tb_frame == %(frame_identifier)s) \
    %(frame_identifier)s->f_lineno = exception_tb->tb_lineno;""" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )
    emit(
        "goto %s;" % context.getExceptionEscape()
    )


def getRaiseExceptionWithCauseCode(raise_type_name, raise_cause_name, emit,
                                   context):
    context.markAsNeedsExceptionVariables()

    emit(
        "exception_type = %s;" % (
            getReferenceExportCode(raise_type_name, context)
        )
    )

    emit(
        getLineNumberUpdateCode(context)
    )

    emit(
        """\
RAISE_EXCEPTION_WITH_CAUSE( &exception_type, &exception_value, &exception_tb, \
%s );""" % getReferenceExportCode(raise_cause_name, context)
    )

    emit(
        "goto %s;" % (
            context.getExceptionEscape()
        )
    )

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_cause_name):
        context.removeCleanupTempName(raise_cause_name)


def getRaiseExceptionWithTypeCode(raise_type_name, emit, context):
    context.markAsNeedsExceptionVariables()

    emit(
        "exception_type = %s;" % (
            getReferenceExportCode(raise_type_name, context)
        )
    )

    emit(
        getLineNumberUpdateCode(context)
    )

    emit(
        "RAISE_EXCEPTION_WITH_TYPE( &exception_type, &exception_value, &exception_tb );"
    )

    emit(
        "goto %s;" % (
            context.getExceptionEscape()
        )
    )

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)


def getRaiseExceptionWithValueCode(raise_type_name, raise_value_name, implicit,
                                   emit, context):
    emit(
        "exception_type = %s;" % (
            getReferenceExportCode(raise_type_name, context)
        )
    )
    emit(
        "exception_value = %s;" % (
            getReferenceExportCode(raise_value_name, context)
        )
    )

    emit(
        getLineNumberUpdateCode(context)
    )

    emit(
        "RAISE_EXCEPTION_%s( &exception_type, &exception_value, &exception_tb );" % (
            ("IMPLICIT" if implicit else "WITH_VALUE")
        )
    )

    emit(
        "goto %s;" % (
            context.getExceptionEscape()
        )
    )

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_value_name):
        context.removeCleanupTempName(raise_value_name)


def getRaiseExceptionWithTracebackCode(raise_type_name, raise_value_name,
                                       raise_tb_name, emit, context):
    emit(
        "exception_type = %s;" % (
            getReferenceExportCode(raise_type_name, context)
        )
    )
    emit(
        "exception_value = %s;" % (
            getReferenceExportCode(raise_value_name, context)
        )
    )
    emit(
        "exception_tb = (PyTracebackObject *)%s;" % (
            getReferenceExportCode(raise_tb_name, context)
        )
    )

    emit(
        getLineNumberUpdateCode(context)
    )

    emit(
        "RAISE_EXCEPTION_WITH_TRACEBACK( &exception_type, &exception_value, &exception_tb);"
    )

    emit(
        "goto %s;" % (
            context.getExceptionEscape()
        )
    )

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_value_name):
        context.removeCleanupTempName(raise_value_name)
    if context.needsCleanup(raise_tb_name):
        context.removeCleanupTempName(raise_tb_name)
