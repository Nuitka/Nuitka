#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Yield related codes.

The normal "yield", and the Python 3.3 or higher "yield from" variant.
"""

from .CodeHelpers import (
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment
)
from .ErrorCodes import getErrorExitCode
from .PythonAPICodes import getReferenceExportCode
from .VariableDeclarations import VariableDeclaration


def getYieldPreserveCode(to_name, value_name, preserve_exception, yield_code,
                          resume_code, emit, context):
    yield_return_label = context.allocateLabel("yield_return")
    yield_return_index = yield_return_label.split('_')[-1]

    locals_preserved = context.variable_storage.getLocalPreservationDeclarations()

    # Need not preserve it, if we are not going to use it for the purpose
    # of releasing it.
    if type(value_name) is tuple:
        value_names = value_name
    else:
        value_names = (value_name,)

    for name in value_names:
        if not context.needsCleanup(name):
            locals_preserved.remove(name)

    # Target name is not assigned, no need to preserve it.
    if to_name in locals_preserved:
        locals_preserved.remove(to_name)

    if locals_preserved:
        yield_tmp_storage = context.variable_storage.getVariableDeclarationTop("yield_tmps")

        if yield_tmp_storage is None:
            yield_tmp_storage = context.variable_storage.addVariableDeclarationTop(
                "char[1024]",
                "yield_tmps",
                None
            )

        emit(
            "Nuitka_PreserveHeap( %s, %s, NULL );" % (
                yield_tmp_storage,
                ", ".join(
                    "&%s, sizeof(%s)" % (
                        local_preserved,
                        local_preserved.c_type
                    )
                    for local_preserved in
                    locals_preserved

                )
            )
        )

    if preserve_exception:
        emit(
            "SAVE_%s_EXCEPTION( %s );" % (
                context.getContextObjectName().upper(),
                context.getContextObjectName()
            )
        )

    emit(
        """\
%(context_object_name)s->m_yield_return_index = %(yield_return_index)s;""" % {
                "context_object_name" : context.getContextObjectName(),
                "yield_return_index"  : yield_return_index,
        }
    )

    emit(yield_code)

    emit(
        "%(yield_return_label)s:" % {
            "yield_return_label"  : yield_return_label,
        }
    )

    if locals_preserved:
        emit(
            "Nuitka_RestoreHeap( %s, %s, NULL );" % (
                yield_tmp_storage,
                ", ".join(
                    "&%s, sizeof(%s)" % (
                        local_preserved,
                        local_preserved.c_type
                    )
                    for local_preserved in
                    locals_preserved

                )
            )
        )

    if resume_code:
        emit(resume_code)

    yield_return_name = VariableDeclaration(
        "PyObject *",
        "yield_return_value",
        None,
        None
    )

    getErrorExitCode(
        check_name = yield_return_name,
        emit       = emit,
        context    = context
    )

    # Called with object
    emit(
        "%s = %s;" % (
            to_name,
            yield_return_name
        )
    )

    if preserve_exception:
        emit(
            "RESTORE_%s_EXCEPTION( %s );" % (
                context.getContextObjectName().upper(),
                context.getContextObjectName()
            )
        )


def generateYieldCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # In handlers, we must preserve/restore the exception.
    preserve_exception = expression.isExceptionPreserving()

    getReferenceExportCode(value_name, emit, context)
    if context.needsCleanup(value_name):
        context.removeCleanupTempName(value_name)

    yield_code = "return %(yielded_value)s;" % {
        "yielded_value" : value_name,
    }

    with withObjectCodeTemporaryAssignment(to_name, "yield_result", expression, emit, context) \
      as result_name:

        getYieldPreserveCode(
            to_name            = result_name,
            value_name         = value_name,
            yield_code         = yield_code,
            resume_code        = None,
            preserve_exception = preserve_exception,
            emit               = emit,
            context            = context
        )

        # This conversion will not use it, and since it is borrowed, debug mode
        # would otherwise complain.
        if to_name.c_type == "void":
            result_name.maybe_unused = True

        # Comes as only borrowed.
        # context.addCleanupTempName(result_name)


def generateYieldFromCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # In handlers, we must preserve/restore the exception.
    preserve_exception = expression.isExceptionPreserving()

    getReferenceExportCode(value_name, emit, context)

    if context.needsCleanup(value_name):
        context.removeCleanupTempName(value_name)
    yield_code = """\
generator->m_yieldfrom = %(yield_from)s;
return NULL;
""" % {
        "yield_from"       : value_name,
    }

    with withObjectCodeTemporaryAssignment(to_name, "yieldfrom_result", expression, emit, context) \
      as result_name:

        getYieldPreserveCode(
            to_name            = result_name,
            value_name         = value_name,
            yield_code         = yield_code,
            resume_code        = None,
            preserve_exception = preserve_exception,
            emit               = emit,
            context            = context
        )

        context.addCleanupTempName(result_name)


def getYieldReturnDispatchCode(context):
    function_dispatch = [
        "case %(index)d: goto yield_return_%(index)d;" % {
            "index" : yield_index
        }
        for yield_index in
        range(context.getLabelCount("yield_return"), 0, -1)
    ]

    if function_dispatch:
        function_dispatch.insert(
            0,
            "switch(%s->m_yield_return_index) {" % context.getContextObjectName()
        )
        function_dispatch.append('}')

    return function_dispatch
