#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for 'yield', 'yield from', and 'await' expressions."""

from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .DeferredReleaseCodes import checkDeferredReleaseUse
from .ErrorCodes import getErrorExitCode
from .PythonAPICodes import getReferenceExportCode
from .VariableDeclarations import VariableDeclaration


def _checkDeferredReleaseYield(value_name, expression, context):
    checkDeferredReleaseUse(
        usage="yield",
        tmp_name=value_name,
        context=context,
        detail=expression.getSourceReference().getAsString(),
    )


def _getYieldPreserveCode(
    to_name, value_name, preserve_exception, yield_code, resume_code, emit, context
):
    yield_return_label = context.allocateLabel("yield_return")
    yield_return_index = yield_return_label.split("_")[-1]

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

    if to_name in locals_preserved:
        locals_preserved.remove(to_name)

    if locals_preserved:
        yield_temps = context.variable_storage.getYieldTempsDeclaration()

        yield_tmp_storage = yield_temps.addSizeExpression(
            " + ".join(
                "sizeof(%s)" % local_preserved.c_type
                for local_preserved in locals_preserved
            )
        )

        emit(
            "NUITKA_PRESERVE_HEAP(%s, sizeof(%s), %s, NULL);"
            % (
                yield_tmp_storage,
                yield_tmp_storage,
                ", ".join(
                    "&%s, sizeof(%s)" % (local_preserved, local_preserved.c_type)
                    for local_preserved in locals_preserved
                ),
            )
        )

    if preserve_exception:
        # Python 3.7+ keeps the handled exception in the generator object
        # itself, only older versions need to swap it at the yield.
        # Expands to SAVE_GENERATOR_EXCEPTION,SAVE_COROUTINE_EXCEPTION,SAVE_ASYNCGEN_EXCEPTION
        emit(
            "SAVE_%s_EXCEPTION(tstate, %s);"
            % (context.getContextObjectName().upper(), context.getContextObjectName())
        )
    elif 0x300 <= python_version < 0x370:
        # Python 3 before 3.7 restores the caller exception and clears the
        # frame state when yielding outside of an exception handler.
        # Expands to RESTORE_AND_CLEAR_GENERATOR_EXCEPTION, etc.
        emit(
            "RESTORE_AND_CLEAR_%s_EXCEPTION(tstate, %s);"
            % (context.getContextObjectName().upper(), context.getContextObjectName())
        )

    emit(
        """\
%(context_object_name)s->m_yield_return_index = %(yield_return_index)s;"""
        % {
            "context_object_name": context.getContextObjectName(),
            "yield_return_index": yield_return_index,
        }
    )

    emit(yield_code)

    emit("%(yield_return_label)s:" % {"yield_return_label": yield_return_label})

    if preserve_exception and not 0x300 <= python_version < 0x370:
        # Expands to RESTORE_GENERATOR_EXCEPTION,RESTORE_COROUTINE_EXCEPTION,RESTORE_ASYNCGEN_EXCEPTION
        emit(
            "RESTORE_%s_EXCEPTION(tstate, %s);"
            % (context.getContextObjectName().upper(), context.getContextObjectName())
        )

    if locals_preserved:
        emit(
            "NUITKA_RESTORE_HEAP(%s, sizeof(%s), %s, NULL);"
            % (
                yield_tmp_storage,
                yield_tmp_storage,
                ", ".join(
                    "&%s, sizeof(%s)" % (local_preserved, local_preserved.c_type)
                    for local_preserved in locals_preserved
                ),
            )
        )

    if resume_code:
        emit(resume_code)

    yield_return_name = VariableDeclaration(
        c_type="PyObject *",
        code_name="yield_return_value",
        init_value=None,
        heap_name=None,
        struct_name=None,
    )

    getErrorExitCode(check_name=yield_return_name, emit=emit, context=context)

    emit("%s = %s;" % (to_name, yield_return_name))
    context.addCleanupTempName(to_name)


def generateYieldCode(to_name, expression, emit, context):
    (value_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    _checkDeferredReleaseYield(value_name, expression, context)

    preserve_exception = expression.isExceptionPreserving() and python_version < 0x370

    getReferenceExportCode(value_name, emit, context)
    if context.needsCleanup(value_name):
        context.removeCleanupTempName(value_name)

    yield_code = "return %(yielded_value)s;" % {"yielded_value": value_name}

    # Mimic CPython's "RESUME" instruction handling of pending signals when a
    # generator is resumed, delivering a "KeyboardInterrupt" at the yield
    # expression rather than at a later point in the caller. A "throw" into the
    # generator is not handled this way in CPython, and it also already has an
    # exception set, so it is excluded.
    resume_code = """\
if (yield_return_value != NULL && unlikely(CONSIDER_THREADING(tstate) == false)) {
    Py_DECREF(yield_return_value);
    yield_return_value = NULL;
}"""

    with withObjectCodeTemporaryAssignment(
        to_name, "yield_result", expression, emit, context
    ) as result_name:
        _getYieldPreserveCode(
            to_name=result_name,
            value_name=value_name,
            yield_code=yield_code,
            resume_code=resume_code,
            preserve_exception=preserve_exception,
            emit=emit,
            context=context,
        )

        if to_name.c_type == "nuitka_void":
            result_name.maybe_unused = True


def generateYieldFromCode(to_name, expression, emit, context):
    (value_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    _checkDeferredReleaseYield(value_name, expression, context)

    preserve_exception = expression.isExceptionPreserving() and python_version < 0x370

    getReferenceExportCode(value_name, emit, context)
    if context.needsCleanup(value_name):
        context.removeCleanupTempName(value_name)

    if 0x300 <= python_version < 0x370:
        yield_code = """\
generator->m_yield_from_exception_preserving = %(preserve)d;
generator->m_yield_from = %(yield_from)s;
return NULL;
""" % {
            "preserve": preserve_exception,
            "yield_from": value_name,
        }
    else:
        yield_code = """\
generator->m_yield_from = %(yield_from)s;
return NULL;
""" % {"yield_from": value_name}

    with withObjectCodeTemporaryAssignment(
        to_name, "yieldfrom_result", expression, emit, context
    ) as result_name:
        _getYieldPreserveCode(
            to_name=result_name,
            value_name=value_name,
            yield_code=yield_code,
            resume_code=None,
            preserve_exception=preserve_exception,
            emit=emit,
            context=context,
        )


def generateYieldFromAwaitableCode(to_name, expression, emit, context):
    preserve_exception = expression.isExceptionPreserving() and python_version < 0x370

    (awaited_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    _checkDeferredReleaseYield(awaited_name, expression, context)

    if 0x300 <= python_version < 0x370:
        yield_code = """\
%(object_name)s->m_yield_from_exception_preserving = %(preserve)d;
%(object_name)s->m_yield_from = %(yield_from)s;
%(object_name)s->m_awaiting = true;
return NULL;
""" % {
            "object_name": context.getContextObjectName(),
            "preserve": preserve_exception,
            "yield_from": awaited_name,
        }
    else:
        yield_code = """\
%(object_name)s->m_yield_from = %(yield_from)s;
%(object_name)s->m_awaiting = true;
return NULL;
""" % {
            "object_name": context.getContextObjectName(),
            "yield_from": awaited_name,
        }

    resume_code = """\
%(object_name)s->m_awaiting = false;
""" % {"object_name": context.getContextObjectName()}

    getReferenceExportCode(awaited_name, emit, context)
    if context.needsCleanup(awaited_name):
        context.removeCleanupTempName(awaited_name)

    with withObjectCodeTemporaryAssignment(
        to_name, "await_result", expression, emit, context
    ) as result_name:
        _getYieldPreserveCode(
            to_name=result_name,
            value_name=awaited_name,
            yield_code=yield_code,
            resume_code=resume_code,
            preserve_exception=preserve_exception,
            emit=emit,
            context=context,
        )


def getYieldReturnDispatchCode(context):
    function_dispatch = [
        "case %(index)d: goto yield_return_%(index)d;" % {"index": yield_index}
        for yield_index in range(context.getLabelCount("yield_return"), 0, -1)
    ]

    if function_dispatch:
        function_dispatch.insert(
            0, "switch(%s->m_yield_return_index) {" % context.getContextObjectName()
        )
        function_dispatch.append("}")

    return function_dispatch


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
