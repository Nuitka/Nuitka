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

from nuitka import Options

from .CodeHelpers import generateChildExpressionsCode
from .ErrorCodes import getErrorExitCode
from .PythonAPICodes import getReferenceExportCode


def generateYieldCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # In handlers, we must preserve/restore the exception.
    preserve_exception = expression.isExceptionPreserving()

    # This will produce GENERATOR_YIELD, COROUTINE_YIELD or ASYNCGEN_YIELD.
    getReferenceExportCode(value_name, emit, context)

    if Options.isExperimental("generator_goto"):
        yield_return_label = context.allocateLabel("yield_return")
        yield_return_index = yield_return_label.split('_')[-1]


        emit(
            """
%(context_object_name)s->m_yield_return_index = %(yield_return_index)s;
return %(yielded_value)s;
%(yield_return_label)s:
%(to_name)s = yield_return_value;
""" % {
                "context_object_name" : context.getContextObjectName(),
                "yield_return_index"  : yield_return_index,
                "yielded_value"       : value_name,
                "yield_return_label"  : yield_return_label,
                "to_name"             : to_name
    }
        )

    else:
        emit(
            "%s = %s_%s( %s, %s );" % (
                to_name,
                context.getContextObjectName().upper(),
                "YIELD"
                  if not preserve_exception else
                "YIELD_IN_HANDLER",
                context.getContextObjectName(),
                value_name
            )
        )

    if context.needsCleanup(value_name):
        context.removeCleanupTempName(value_name)

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    # Comes as only borrowed.
    # context.addCleanupTempName(to_name)


def generateYieldFromCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # In handlers, we must preserve/restore the exception.
    preserve_exception = expression.isExceptionPreserving()

    # This will produce GENERATOR_YIELD_FROM, COROUTINE_YIELD_FROM or
    # ASYNCGEN_YIELD_FROM.
    getReferenceExportCode(value_name, emit, context)

    emit(
        "%s = %s_%s( %s, %s );" % (
            to_name,
            context.getContextObjectName().upper(),
            "YIELD_FROM"
              if not preserve_exception else
            "YIELD_FROM_IN_HANDLER",
            context.getContextObjectName(),
            value_name
        )
    )

    if not context.needsCleanup(value_name):
        context.addCleanupTempName(value_name)

    getErrorExitCode(
        check_name   = to_name,
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    context.addCleanupTempName(to_name)
