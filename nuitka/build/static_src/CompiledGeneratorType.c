//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** Compiled Generators.
 *
 * Unlike in CPython, we have one type for just generators, this doesn't do coroutines
 * nor asyncgen.
 *
 * It strives to be full replacement for normal generators, while providing also an
 * interface for quick iteration from compiled code.
 *
 */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#include <structmember.h>
#endif

#if _DEBUG_REFCOUNTS
int count_active_Nuitka_Generator_Type;
int count_allocated_Nuitka_Generator_Type;
int count_released_Nuitka_Generator_Type;
#endif

// In a separate file, code to interact with uncompiled generators, that does
// all the quirks necessary to get those working.
#include "CompiledGeneratorTypeUncompiledIntegration.c"

// Debugging output tools
#if _DEBUG_GENERATOR
NUITKA_MAY_BE_UNUSED static void _PRINT_GENERATOR_STATUS(char const *descriptor, char const *context,
                                                         struct Nuitka_GeneratorObject *generator) {
    char const *status;

    switch (generator->m_status) {
    case status_Finished:
        status = "(finished)";
        break;
    case status_Running:
        status = "(running)";
        break;
    case status_Unused:
        status = "(unused)";
        break;
    default:
        status = "(ILLEGAL)";
        break;
    }

    PRINT_STRING(descriptor);
    PRINT_STRING(" : ");
    PRINT_STRING(context);
    PRINT_STRING(" ");
    PRINT_ITEM((PyObject *)generator);
    PRINT_STRING(" ");
    PRINT_STRING(status);
    PRINT_STRING(" ");
    PRINT_REFCOUNT((PyObject *)generator);
    PRINT_NEW_LINE();
}

#define PRINT_GENERATOR_STATUS(context, generator) _PRINT_GENERATOR_STATUS(__FUNCTION__, context, generator)

#endif

#if _DEBUG_GENERATOR || _DEBUG_COROUTINE || _DEBUG_ASYNCGEN

NUITKA_MAY_BE_UNUSED static void PRINT_COROUTINE_VALUE(char const *name, PyObject *value) {
    PRINT_STRING(name);
    PRINT_STRING("=");
    PRINT_ITEM(value);
    if (value) {
        PRINT_REFCOUNT(value);
    }
    PRINT_NEW_LINE();
}

NUITKA_MAY_BE_UNUSED static void PRINT_COROUTINE_STRING(char const *name, char const *value) {
    PRINT_STRING(name);
    PRINT_STRING("=");
    PRINT_STRING(value);
    PRINT_NEW_LINE();
}
#endif

static void Nuitka_MarkGeneratorAsFinished(struct Nuitka_GeneratorObject *generator) {
    generator->m_status = status_Finished;

#if PYTHON_VERSION >= 0x3b0
    if (generator->m_frame) {
        generator->m_frame->m_frame_state = FRAME_COMPLETED;
    }
#endif
}

static void Nuitka_MarkGeneratorAsRunning(struct Nuitka_GeneratorObject *generator) {
    generator->m_running = 1;

    if (generator->m_frame) {
        Nuitka_Frame_MarkAsExecuting(generator->m_frame);
    }
}

static void Nuitka_MarkGeneratorAsNotRunning(struct Nuitka_GeneratorObject *generator) {
    generator->m_running = 0;

    if (generator->m_frame) {
        Nuitka_Frame_MarkAsNotExecuting(generator->m_frame);
    }
}

static PyObject *Nuitka_Generator_tp_repr(struct Nuitka_GeneratorObject *generator) {
#if PYTHON_VERSION < 0x300
    return Nuitka_String_FromFormat("<compiled_generator object %s at %p>", Nuitka_String_AsString(generator->m_name),
                                    generator);
#elif PYTHON_VERSION < 0x350
    return Nuitka_String_FromFormat("<compiled_generator object %U at %p>", generator->m_name, generator);

#else
    return Nuitka_String_FromFormat("<compiled_generator object %U at %p>", generator->m_qualname, generator);
#endif
}

static long Nuitka_Generator_tp_traverse(struct Nuitka_GeneratorObject *generator, visitproc visit, void *arg) {
    CHECK_OBJECT(generator);

    // TODO: Identify the impact of not visiting owned objects like module.
#if PYTHON_VERSION >= 0x300
    Py_VISIT(generator->m_yield_from);
#endif

    for (Py_ssize_t i = 0; i < generator->m_closure_given; i++) {
        Py_VISIT(generator->m_closure[i]);
    }

    Py_VISIT(generator->m_frame);

    return 0;
}

static void Nuitka_Generator_release_closure(struct Nuitka_GeneratorObject *generator) {
    for (Py_ssize_t i = 0; i < generator->m_closure_given; i++) {
        CHECK_OBJECT(generator->m_closure[i]);
        Py_DECREF(generator->m_closure[i]);
    }

    generator->m_closure_given = 0;
}

static PyObject *_Nuitka_CallGeneratorCodeC(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                            PyObject *send_value) {

#if PYTHON_VERSION < 0x300
    return ((generator_code)generator->m_code)(tstate, generator, send_value);
#else
    struct Nuitka_ExceptionStackItem enter_exception = GET_CURRENT_EXCEPTION(tstate);

#if PYTHON_VERSION < 0x3b0
    if (generator->m_resume_exception.exception_type != NULL) {
        SET_CURRENT_EXCEPTION(tstate, &generator->m_resume_exception);
    }
#else
    if (generator->m_resume_exception.exception_value != NULL) {
        SET_CURRENT_EXCEPTION(tstate, &generator->m_resume_exception);
    }
#endif

    PyObject *result = ((generator_code)generator->m_code)(tstate, generator, send_value);

#if PYTHON_VERSION < 0x3b0
    if (enter_exception.exception_type != NULL) {
        if (enter_exception.exception_type != Py_None) {
            if (EXC_TYPE(tstate) != enter_exception.exception_type ||
                EXC_VALUE(tstate) != enter_exception.exception_value) {
                generator->m_resume_exception = GET_CURRENT_EXCEPTION(tstate);

                SET_CURRENT_EXCEPTION(tstate, &enter_exception);
            } else {
                Py_DECREF(enter_exception.exception_type);
                Py_XDECREF(enter_exception.exception_value);
                Py_XDECREF(enter_exception.exception_tb);
            }
        } else {
            Py_DECREF(enter_exception.exception_type);
            Py_XDECREF(enter_exception.exception_value);
            Py_XDECREF(enter_exception.exception_tb);
        }
    }
#else
    if (enter_exception.exception_value != NULL) {
        if (enter_exception.exception_value != Py_None) {
            if (EXC_VALUE(tstate) != enter_exception.exception_value) {
                generator->m_resume_exception = GET_CURRENT_EXCEPTION(tstate);

                SET_CURRENT_EXCEPTION(tstate, &enter_exception);
            } else {
                Py_DECREF(enter_exception.exception_value);
            }
        } else {
            Py_DECREF_IMMORTAL(Py_None);
        }
    }
#endif

    return result;
#endif
}

#if PYTHON_VERSION >= 0x300

// Note: Shared with coroutines and asyncgen code.
static PyObject *ERROR_GET_STOP_ITERATION_VALUE(PyThreadState *tstate) {
    assert(PyErr_ExceptionMatches(PyExc_StopIteration));

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

#if PYTHON_VERSION < 0x3c0
    Py_DECREF(saved_exception_state.exception_type);
    Py_XDECREF(saved_exception_state.exception_tb);
#endif

    // We own a reference, and we mean to return it.
    PyObject *exception_value = saved_exception_state.exception_value;

    PyObject *value = NULL;

    if (exception_value != NULL) {
        if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, exception_value, PyExc_StopIteration)) {
            value = ((PyStopIterationObject *)exception_value)->value;
            Py_XINCREF(value);
            Py_DECREF(exception_value);
        } else {
            value = exception_value;
        }
    }

    if (value == NULL) {
        Py_INCREF_IMMORTAL(Py_None);
        value = Py_None;
    }

    return value;
}

static PyObject *Nuitka_CallGeneratorThrowMethod(PyObject *throw_method,
                                                 struct Nuitka_ExceptionPreservationItem *exception_state) {

    // TODO: Faster call code should be used.

#if PYTHON_VERSION < 0x3c0
    PyObject *result =
        PyObject_CallFunctionObjArgs(throw_method, exception_state->exception_type, exception_state->exception_value,
                                     exception_state->exception_tb, NULL);

    return result;
#else
    // For Python 3.12 or higher, we don't create the type and tb args, code was
    // always supposed to handle single argument forms and is now.
    PyObject *result = PyObject_CallFunctionObjArgs(throw_method, exception_state->exception_value, NULL);

    return result;
#endif
}

static PyObject *_Nuitka_Generator_throw2(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);
#if PYTHON_VERSION >= 0x350
static PyObject *_Nuitka_Coroutine_throw2(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine, bool closing,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);
#endif

static PyObject *_Nuitka_YieldFromPassExceptionTo(PyThreadState *tstate, PyObject *value,
                                                  struct Nuitka_ExceptionPreservationItem *exception_state) {
    // The yielding generator is being closed, but we also are tasked to
    // immediately close the currently running sub-generator.
    if (EXCEPTION_STATE_MATCH_BOOL_SINGLE(tstate, exception_state, PyExc_GeneratorExit)) {
        PyObject *close_method = PyObject_GetAttr(value, const_str_plain_close);

        if (close_method) {
            PyObject *close_value = PyObject_Call(close_method, const_tuple_empty, NULL);
            Py_DECREF(close_method);

            if (unlikely(close_value == NULL)) {
                // Release exception, we are done with it, raising the one from close instead.
                RELEASE_ERROR_OCCURRED_STATE(exception_state);

                return NULL;
            }

            Py_DECREF(close_value);
        } else {
            PyObject *error = GET_ERROR_OCCURRED(tstate);

            if (error != NULL && !EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_AttributeError)) {
                PyErr_WriteUnraisable((PyObject *)value);
            }
        }

        // Transfer exception ownership to published.
        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

        return NULL;
    }

#if NUITKA_UNCOMPILED_THROW_INTEGRATION
    if (PyGen_CheckExact(value)
#if PYTHON_VERSION >= 0x350
        || PyCoro_CheckExact(value)
#endif
    ) {
        PyGenObject *gen = (PyGenObject *)value;

        // Handing exception ownership over.
        PyObject *result = Nuitka_UncompiledGenerator_throw(tstate, gen, 1, exception_state);

        return result;
    }
#endif

    if (Nuitka_Generator_Check(value)) {
        struct Nuitka_GeneratorObject *gen = ((struct Nuitka_GeneratorObject *)value);

        return _Nuitka_Generator_throw2(tstate, gen, exception_state);
    }

#if PYTHON_VERSION >= 0x350
    if (Nuitka_Coroutine_Check(value)) {
        struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineObject *)value);
        // Handing exception ownership over.
        return _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
    }

    if (Nuitka_CoroutineWrapper_Check(value)) {
        struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineWrapperObject *)value)->m_coroutine;
        // Handing exception ownership over.
        return _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
    }
#endif

    PyObject *throw_method = PyObject_GetAttr(value, const_str_plain_throw);

    if (throw_method != NULL) {
        PyObject *result = Nuitka_CallGeneratorThrowMethod(throw_method, exception_state);
        Py_DECREF(throw_method);

        // Releasing exception we own.
        RELEASE_ERROR_OCCURRED_STATE(exception_state);

        return result;
    } else {
        assert(HAS_ERROR_OCCURRED(tstate));

        if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, GET_ERROR_OCCURRED(tstate), PyExc_AttributeError)) {
            // Restoring the exception we own, to be released when handling it.
            RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);
        } else {
            // Releasing exception we own.
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
        }

        return NULL;
    }
}

static PyObject *_Nuitka_YieldFromGeneratorCore(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                                PyObject *yield_from, PyObject *send_value) {
    // Send iteration value to the sub-generator, which may be a CPython
    // generator object, something with an iterator next, or a send method,
    // where the later is only required if values other than "None" need to
    // be passed in.
    CHECK_OBJECT(yield_from);
    assert(send_value != NULL || HAS_ERROR_OCCURRED(tstate));

    PyObject *retval;

#if 0
    PRINT_STRING("YIELD CORE:");
    PRINT_ITEM( value );
    PRINT_ITEM( send_value );

    PRINT_NEW_LINE();
#endif

    struct Nuitka_ExceptionPreservationItem exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &exception_state);

    // Exception, was thrown into us, need to send that to sub-generator.
    if (HAS_EXCEPTION_STATE(&exception_state)) {
        // Passing ownership of exception fetch to it.
        retval = _Nuitka_YieldFromPassExceptionTo(tstate, yield_from, &exception_state);

        // TODO: This wants to look at retval most definitely, send_value is going to be NULL.
        if (unlikely(send_value == NULL)) {
            PyObject *error = GET_ERROR_OCCURRED(tstate);

            if (error != NULL && EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopIteration)) {
                generator->m_returned = ERROR_GET_STOP_ITERATION_VALUE(tstate);
                assert(!HAS_ERROR_OCCURRED(tstate));

                return NULL;
            }
        }
    } else if (PyGen_CheckExact(yield_from)) {
        retval = Nuitka_PyGen_Send(tstate, (PyGenObject *)yield_from, Py_None);
    }
#if PYTHON_VERSION >= 0x350
    else if (PyCoro_CheckExact(yield_from)) {
        retval = Nuitka_PyGen_Send(tstate, (PyGenObject *)yield_from, Py_None);
    }
#endif
    else if (send_value == Py_None && Py_TYPE(yield_from)->tp_iternext != NULL) {
        retval = Py_TYPE(yield_from)->tp_iternext(yield_from);
    } else {
        // Bug compatibility here, before Python3 tuples were unrolled in calls, which is what
        // PyObject_CallMethod does.
#if PYTHON_VERSION >= 0x300
        retval = PyObject_CallMethodObjArgs(yield_from, const_str_plain_send, send_value, NULL);
#else
        retval = PyObject_CallMethod(yield_from, (char *)"send", (char *)"O", send_value);
#endif
    }

    // Check the sub-generator result
    if (retval == NULL) {
        PyObject *error = GET_ERROR_OCCURRED(tstate);

        if (error == NULL) {
            Py_INCREF_IMMORTAL(Py_None);
            generator->m_returned = Py_None;
        } else if (likely(EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopIteration))) {
            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            generator->m_returned = ERROR_GET_STOP_ITERATION_VALUE(tstate);
            assert(!HAS_ERROR_OCCURRED(tstate));
        }

        return NULL;
    } else {
        return retval;
    }
}

static PyObject *Nuitka_YieldFromGeneratorCore(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                               PyObject *send_value) {
    CHECK_OBJECT(generator);
    CHECK_OBJECT_X(send_value);

    PyObject *yield_from = generator->m_yield_from;
    CHECK_OBJECT(yield_from);

    // Need to make it unaccessible while using it.
    generator->m_yield_from = NULL;
    PyObject *yielded = _Nuitka_YieldFromGeneratorCore(tstate, generator, yield_from, send_value);

    if (yielded == NULL) {
        Py_DECREF(yield_from);

        if (generator->m_returned != NULL) {
            PyObject *yield_from_result = generator->m_returned;
            generator->m_returned = NULL;

            yielded = _Nuitka_CallGeneratorCodeC(tstate, generator, yield_from_result);
        } else {
            assert(HAS_ERROR_OCCURRED(tstate));
            yielded = _Nuitka_CallGeneratorCodeC(tstate, generator, NULL);
        }

    } else {
        generator->m_yield_from = yield_from;
    }

    return yielded;
}

static PyObject *Nuitka_YieldFromGeneratorNext(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator) {
    CHECK_OBJECT(generator);

    // Coroutines are already perfect for yielding from.
#if PYTHON_VERSION >= 0x350
    if (PyCoro_CheckExact(generator->m_yield_from) || Nuitka_Coroutine_Check(generator->m_yield_from)) {
        if (unlikely((generator->m_code_object->co_flags & CO_ITERABLE_COROUTINE) == 0)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                            "cannot 'yield from' a coroutine object in a non-coroutine generator");
        }
    } else
#endif
    {
        PyObject *new_iterator = MAKE_ITERATOR(tstate, generator->m_yield_from);
        if (new_iterator != NULL) {
            Py_DECREF(generator->m_yield_from);
            generator->m_yield_from = new_iterator;
        }
    }

    return Nuitka_YieldFromGeneratorCore(tstate, generator, Py_None);
}

static PyObject *Nuitka_YieldFromGeneratorInitial(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                                  PyObject *send_value) {
    PyObject *result = Nuitka_YieldFromGeneratorCore(tstate, generator, send_value);

#if 0
    PRINT_STRING("RES:");
    PRINT_ITEM( result );
    PRINT_NEW_LINE();
#endif

    return result;
}

#endif

static void _Nuitka_GeneratorPopFrame(PyThreadState *tstate, Nuitka_ThreadStateFrameType *return_frame) {
#if PYTHON_VERSION < 0x3b0
    tstate->frame = return_frame;
#else
    CURRENT_TSTATE_INTERPRETER_FRAME(tstate) = return_frame;
#endif

    PRINT_TOP_FRAME("Generator pop exit gives top frame:");
}

#if PYTHON_VERSION >= 0x350
static void RAISE_RUNTIME_ERROR_RAISED_STOP_ITERATION(PyThreadState *tstate, char const *message) {

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

#if PYTHON_VERSION < 0x3c0
    NORMALIZE_EXCEPTION_STATE(tstate, &saved_exception_state);
#endif

    struct Nuitka_ExceptionPreservationItem new_exception_state;
    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, &new_exception_state, PyExc_RuntimeError, message);

#if PYTHON_VERSION < 0x3c0
    NORMALIZE_EXCEPTION_STATE(tstate, &new_exception_state);
#endif

    Py_INCREF(saved_exception_state.exception_value);
    RAISE_EXCEPTION_WITH_CAUSE(tstate, &new_exception_state, saved_exception_state.exception_value);

    Nuitka_Exception_SetContext(new_exception_state.exception_value, saved_exception_state.exception_value);

    RELEASE_ERROR_OCCURRED_STATE_X(&saved_exception_state);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &new_exception_state);
}
#endif

static PyObject *_Nuitka_Generator_send(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                        PyObject *value, struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT(generator);
    assert(Nuitka_Generator_Check((PyObject *)generator));
    CHECK_EXCEPTION_STATE_X(exception_state);
    CHECK_OBJECT_X(value);

#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
    PRINT_COROUTINE_VALUE("value", value);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    if (value != NULL) {
        ASSERT_EMPTY_EXCEPTION_STATE(exception_state);
    }

    if (generator->m_status != status_Finished) {
        if (generator->m_running) {
            Py_XDECREF(value);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "generator already executing");
            return NULL;
        }

#if PYTHON_VERSION < 0x300
        PyObject *saved_exception_type = tstate->exc_type;
        PyObject *saved_exception_value = NULL;
        PyTracebackObject *saved_exception_traceback = NULL;

        if (saved_exception_type != Py_None && saved_exception_type != NULL) {
            saved_exception_value = tstate->exc_value;
            Py_INCREF(saved_exception_type);
            Py_XINCREF(saved_exception_value);
            saved_exception_traceback = (PyTracebackObject *)tstate->exc_traceback;
            Py_XINCREF(saved_exception_traceback);
        }
#endif

        // Put the generator back on the frame stack.
        Nuitka_ThreadStateFrameType *return_frame = _Nuitka_GetThreadStateFrame(tstate);

        if (generator->m_status == status_Unused) {
            generator->m_status = status_Running;

            Py_XDECREF(value);
            value = NULL;
        } else {
            // Put the generator back on the frame stack.
            pushFrameStackGeneratorCompiledFrame(tstate, generator->m_frame);
        }

        // Continue the yielder function while preventing recursion.
        Nuitka_MarkGeneratorAsRunning(generator);

        // Check for thrown exception, publish it to the generator code.
        if (unlikely(HAS_EXCEPTION_STATE(exception_state))) {
            // TODO: Original value is meant here probably.
            assert(value == NULL);

            // Transfer exception ownership to published.
            RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);
        }

#if _DEBUG_GENERATOR
        PRINT_GENERATOR_STATUS("Switching to generator", generator);
        PRINT_COROUTINE_VALUE("value", value);
        PRINT_CURRENT_EXCEPTION();
        PRINT_NEW_LINE();
        // dumpFrameStack();
#endif

        PyObject *yielded;

#if PYTHON_VERSION >= 0x300
        if (generator->m_yield_from == NULL) {
            yielded = _Nuitka_CallGeneratorCodeC(tstate, generator, value);
        } else {
            // This does not release the value if any, so we need to do it afterwards.
            yielded = Nuitka_YieldFromGeneratorInitial(tstate, generator, value);
            Py_XDECREF(value);
        }
#else
        yielded = _Nuitka_CallGeneratorCodeC(tstate, generator, value);
#endif

#if PYTHON_VERSION >= 0x300
        // If the generator returns with m_yield_from set, it wants us to yield
        // from that value from now on.
        while (yielded == NULL && generator->m_yield_from != NULL) {
            yielded = Nuitka_YieldFromGeneratorNext(tstate, generator);
        }
#endif
        Nuitka_MarkGeneratorAsNotRunning(generator);

        // Remove the generator from the frame stack.
        if (generator->m_frame) {
            // assert(tstate->frame == &generator->m_frame->m_frame);
            assertFrameObject(generator->m_frame);

            if (generator->m_frame->m_frame.f_back) {
                Py_CLEAR(generator->m_frame->m_frame.f_back);
            }
        }

        // Return back to the frame that called us.
        _Nuitka_GeneratorPopFrame(tstate, return_frame);

#if _DEBUG_GENERATOR
        PRINT_GENERATOR_STATUS("Returned from generator", generator);
        // dumpFrameStack();
#endif

        if (yielded == NULL) {
#if _DEBUG_GENERATOR
            PRINT_GENERATOR_STATUS("finishing from yield", generator);
            PRINT_STRING("-> finishing generator sets status_Finished\n");
            PRINT_COROUTINE_VALUE("return_value", generator->m_returned);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
            Nuitka_MarkGeneratorAsFinished(generator);

            if (generator->m_frame != NULL) {
#if PYTHON_VERSION >= 0x300
                Nuitka_SetFrameGenerator(generator->m_frame, NULL);
#endif
                Py_DECREF(generator->m_frame);
                generator->m_frame = NULL;
            }

            Nuitka_Generator_release_closure(generator);

#if PYTHON_VERSION < 0x300
            if (saved_exception_type != NULL && saved_exception_type != Py_None) {
                Py_DECREF(saved_exception_type);
                Py_XDECREF(saved_exception_value);
                Py_XDECREF(saved_exception_traceback);
            }
#endif

#if PYTHON_VERSION >= 0x350
            if (
#if PYTHON_VERSION < 0x370
                generator->m_code_object->co_flags & CO_FUTURE_GENERATOR_STOP &&
#endif
                GET_ERROR_OCCURRED(tstate) == PyExc_StopIteration) {
                RAISE_RUNTIME_ERROR_RAISED_STOP_ITERATION(tstate, "generator raised StopIteration");

                return NULL;
            }
#endif

            // Create StopIteration if necessary, i.e. return value that is not "None" was
            // given. TODO: Push this further down the user line, we might be able to avoid
            // it for some uses, e.g. quick iteration entirely.
#if PYTHON_VERSION >= 0x300
            if (generator->m_returned) {
                if (generator->m_returned != Py_None) {
                    Nuitka_SetStopIterationValue(tstate, generator->m_returned);
                }

                Py_DECREF(generator->m_returned);
                generator->m_returned = NULL;

#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Return value to exception set", generator);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif
            }
#endif

            return NULL;
        } else {
#if _NUITKA_MAINTAIN_SYS_EXC_VARS
            PyObject *old_type = tstate->exc_type;
            PyObject *old_value = tstate->exc_value;
            PyTracebackObject *old_tb = (PyTracebackObject *)tstate->exc_traceback;

            // Set sys attributes in the fastest possible way, spell-checker: ignore sysdict
            PyObject *sys_dict = tstate->interp->sysdict;
            CHECK_OBJECT(sys_dict);

            if (saved_exception_type != NULL && saved_exception_type != Py_None) {
                tstate->exc_type = saved_exception_type;
                tstate->exc_value = saved_exception_value;
                tstate->exc_traceback = (PyObject *)saved_exception_traceback;

                Py_XDECREF(old_type);
                Py_XDECREF(old_value);
                Py_XDECREF(old_tb);

                if (old_type != saved_exception_type) {
                    DICT_SET_ITEM(sys_dict, const_str_plain_exc_type, saved_exception_type);
                }
                if (saved_exception_value != old_value) {
                    DICT_SET_ITEM(sys_dict, const_str_plain_exc_value,
                                  saved_exception_value ? saved_exception_value : Py_None);
                }
                if (saved_exception_traceback != old_tb) {
                    DICT_SET_ITEM(sys_dict, const_str_plain_exc_traceback,
                                  saved_exception_traceback ? (PyObject *)saved_exception_traceback : Py_None);
                }
            } else {
                tstate->exc_type = Py_None;
                tstate->exc_value = Py_None;
                tstate->exc_traceback = (PyObject *)Py_None;

                Py_INCREF_IMMORTAL(Py_None);
                Py_INCREF_IMMORTAL(Py_None);
                Py_INCREF_IMMORTAL(Py_None);

                Py_XDECREF(old_type);
                Py_XDECREF(old_value);
                Py_XDECREF(old_tb);

                if (old_type != Py_None) {
                    DICT_SET_ITEM(sys_dict, const_str_plain_exc_type, Py_None);
                }
                if (old_value != Py_None) {
                    DICT_SET_ITEM(sys_dict, const_str_plain_exc_value, Py_None);
                }
                if (old_tb != (PyTracebackObject *)Py_None) {
                    DICT_SET_ITEM(sys_dict, const_str_plain_exc_traceback, Py_None);
                }
            }
#endif

            return yielded;
        }
    } else {
        Py_XDECREF(value);

        // Release exception if any, we are finished with it and will raise another.
        RELEASE_ERROR_OCCURRED_STATE_X(exception_state);

        return NULL;
    }
}

static PyObject *Nuitka_Generator_send(struct Nuitka_GeneratorObject *generator, PyObject *value) {
    CHECK_OBJECT(value);

    PyThreadState *tstate = PyThreadState_GET();

    if (generator->m_status == status_Unused && value != Py_None) {
        // Buggy CPython 3.10 refuses to allow later usage.
#if PYTHON_VERSION >= 0x3a0 && PYTHON_VERSION < 0x3a2
        Nuitka_MarkGeneratorAsFinished(generator);
#endif

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "can't send non-None value to a just-started generator");
        return NULL;
    }

    // We need to transfer ownership of the sent value.
    Py_INCREF(value);

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    PyObject *result = _Nuitka_Generator_send(tstate, generator, value, &exception_state);

    if (result == NULL) {
        if (HAS_ERROR_OCCURRED(tstate) == false) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }
    }

    return result;
}

static PyObject *Nuitka_Generator_tp_iternext(struct Nuitka_GeneratorObject *generator) {
#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    Py_INCREF_IMMORTAL(Py_None);

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    return _Nuitka_Generator_send(tstate, generator, Py_None, &exception_state);
}

/* Our own qiter interface, which is for quicker simple loop style iteration,
   that does not send anything in. */
PyObject *Nuitka_Generator_qiter(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator, bool *finished) {
    Py_INCREF_IMMORTAL(Py_None);

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    PyObject *result = _Nuitka_Generator_send(tstate, generator, Py_None, &exception_state);

    if (result == NULL) {
        if (unlikely(!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate))) {
            *finished = false;
            return NULL;
        }

        *finished = true;
        return NULL;
    }

    *finished = false;
    return result;
}

static bool DROP_ERROR_OCCURRED_GENERATOR_EXIT_OR_STOP_ITERATION(PyThreadState *tstate) {
    PyObject *error = GET_ERROR_OCCURRED(tstate);

    if (EXCEPTION_MATCH_GENERATOR(tstate, error)) {
        CLEAR_ERROR_OCCURRED(tstate);

        return true;
    }

    return false;
}

// Note: Used by compiled frames.
static bool _Nuitka_Generator_close(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator) {
#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
#endif
    CHECK_OBJECT(generator);

    if (generator->m_status == status_Running) {
        struct Nuitka_ExceptionPreservationItem exception_state;
        SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, &exception_state, PyExc_GeneratorExit, NULL, NULL);

        PyObject *result = _Nuitka_Generator_send(tstate, generator, NULL, &exception_state);

        if (unlikely(result)) {
            Py_DECREF(result);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "generator ignored GeneratorExit");
            return false;
        } else {
            PyObject *error = GET_ERROR_OCCURRED(tstate);

            // StopIteration as exception.
            if (error == NULL) {
                return true;
            }

            // Maybe another acceptable exception for generator exit.
            return DROP_ERROR_OCCURRED_GENERATOR_EXIT_OR_STOP_ITERATION(tstate);
        }
    }

    return true;
}

static PyObject *Nuitka_Generator_close(struct Nuitka_GeneratorObject *generator, PyObject *unused) {
    PyThreadState *tstate = PyThreadState_GET();

    bool r = _Nuitka_Generator_close(tstate, generator);

    if (unlikely(r == false)) {
        return NULL;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

#if PYTHON_VERSION >= 0x3c0
static bool _Nuitka_Generator_check_throw_args(PyThreadState *tstate, PyObject **exception_type,
                                               PyObject **exception_value, PyTracebackObject **exception_tb) {
    if (*exception_tb == (PyTracebackObject *)Py_None) {
        *exception_tb = NULL;
    } else if (*exception_tb != NULL && !PyTraceBack_Check(*exception_tb)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "throw() third argument must be a traceback object");
        goto failed_throw;
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(tstate, exception_type, exception_value, exception_tb);
    } else if (PyExceptionInstance_Check(*exception_type)) {
        if (*exception_value != NULL && *exception_value != Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                            "instance exception may not have a separate value");
            goto failed_throw;
        }

        // Release old None value and replace it with the object, then set the exception type
        // from the class. The "None" is known immortal here and needs no refcount correction.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);
    } else {
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "exceptions must be classes, or instances, not %s",
                     Py_TYPE(*exception_type)->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "exceptions must be classes or instances deriving from BaseException, not %s",
                     Py_TYPE(*exception_type)->tp_name);
#endif

        goto failed_throw;
    }

    return true;

failed_throw:

    return false;
}
#endif

static bool _Nuitka_Generator_make_throw_exception_state(PyThreadState *tstate,
                                                         struct Nuitka_ExceptionPreservationItem *exception_state,
                                                         PyObject *exception_type, PyObject *exception_value,
                                                         PyTracebackObject *exception_tb) {

#if PYTHON_VERSION >= 0x3c0
    Py_INCREF(exception_type);
    Py_XINCREF(exception_value);
    Py_XINCREF(exception_tb);

    if (_Nuitka_Generator_check_throw_args(tstate, &exception_type, &exception_value, &exception_tb) == false) {
        Py_DECREF(exception_type);
        Py_XDECREF(exception_value);
        Py_XDECREF(exception_tb);

        return false;
    }
#endif

    SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, exception_state, exception_type, exception_value, exception_tb);

#if PYTHON_VERSION >= 0x3c0
    Py_DECREF(exception_type);
    Py_XDECREF(exception_value);
    Py_XDECREF(exception_tb);
#endif

    return true;
}

// Shared code for checking a thrown exception, coroutines, asyncgen, uncompiled
// ones do this too. For pre-3.12, the checking needs to be done late, for 3.12
// early, so it's a separate function.
static bool _Nuitka_Generator_check_throw(PyThreadState *tstate,
                                          struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_EXCEPTION_STATE(exception_state);

#if PYTHON_VERSION < 0x3c0
    if (exception_state->exception_tb == (PyTracebackObject *)Py_None) {
        Py_DECREF(exception_state->exception_tb);
        exception_state->exception_tb = NULL;
    } else if (exception_state->exception_tb != NULL && !PyTraceBack_Check(exception_state->exception_tb)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "throw() third argument must be a traceback object");
        goto failed_throw;
    }

    if (PyExceptionClass_Check(exception_state->exception_type)) {
        // TODO: Must not / need not normalize here?
        NORMALIZE_EXCEPTION_STATE(tstate, exception_state);
    } else if (PyExceptionInstance_Check(exception_state->exception_type)) {
        if (exception_state->exception_value != NULL && exception_state->exception_value != Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                            "instance exception may not have a separate value");
            goto failed_throw;
        }

        // Release old None value and replace it with the object, then set the exception type
        // from the class.
        Py_XDECREF(exception_state->exception_value);
        exception_state->exception_value = exception_state->exception_type;

        exception_state->exception_type = PyExceptionInstance_Class(exception_state->exception_type);
        Py_INCREF(exception_state->exception_type);
    } else {
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "exceptions must be classes, or instances, not %s",
                     Py_TYPE(exception_state->exception_type)->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "exceptions must be classes or instances deriving from BaseException, not %s",
                     Py_TYPE(exception_state->exception_type)->tp_name);
#endif

        goto failed_throw;
    }

#endif
    return true;

#if PYTHON_VERSION < 0x3c0
failed_throw:
#endif
    // Release exception, we are done with it now.
    RELEASE_ERROR_OCCURRED_STATE(exception_state);

    return false;
}

#if PYTHON_VERSION >= 0x300

static bool _Nuitka_Generator_close(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator);
#if PYTHON_VERSION >= 0x350
static bool _Nuitka_Coroutine_close(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine);
#if PYTHON_VERSION >= 0x360
static bool _Nuitka_Asyncgen_close(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen);
#endif
#endif

// Note: This is also used for coroutines and asyncgen
static bool Nuitka_gen_close_iter(PyThreadState *tstate, PyObject *yield_from) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_gen_close_iter: Enter\n");
#endif

    CHECK_OBJECT(yield_from);

    // TODO: Could specialize depending in yield_from type for performance. Many
    // times these will be our own ones, or known ones like uncompiled
    // generators.
    if (Nuitka_Generator_Check(yield_from)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Defer to _Nuitka_Generator_close\n");
#endif
        return _Nuitka_Generator_close(tstate, (struct Nuitka_GeneratorObject *)yield_from);
    }

#if PYTHON_VERSION >= 0x350
    if (Nuitka_Coroutine_Check(yield_from)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Defer to _Nuitka_Coroutine_close\n");
#endif
        return _Nuitka_Coroutine_close(tstate, (struct Nuitka_CoroutineObject *)yield_from);
    }
#endif

#if PYTHON_VERSION >= 0x360
    if (Nuitka_Asyncgen_Check(yield_from)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Defer to _Nuitka_Asyncgen_close\n");
#endif
        return _Nuitka_Asyncgen_close(tstate, (struct Nuitka_AsyncgenObject *)yield_from);
    }
#endif

    PyObject *meth = PyObject_GetAttr(yield_from, const_str_plain_close);

    if (unlikely(meth == NULL)) {
        if (unlikely(!PyErr_ExceptionMatches(PyExc_AttributeError))) {
#if _DEBUG_GENERATOR
            PRINT_STRING("Nuitka_gen_close_iter: Strange error while looking up close method.\n");
#endif
            PyErr_WriteUnraisable(yield_from);
        }

        CLEAR_ERROR_OCCURRED(tstate);

#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Leave, has no close method.\n");
#endif
        return true;
    }

    PyObject *retval = CALL_FUNCTION_NO_ARGS(tstate, meth);
    Py_DECREF(meth);

    if (unlikely(retval == NULL)) {
#if _DEBUG_GENERATOR
        PRINT_STRING("Nuitka_gen_close_iter: Leave, exception from close.\n");
#endif
        return false;
    }

    CHECK_OBJECT(retval);
    Py_DECREF(retval);

#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_gen_close_iter: Leave, closed.\n");
#endif

    return true;
}
#endif

#if PYTHON_VERSION >= 0x360
static bool Nuitka_AsyncgenAsend_Check(PyObject *object);
struct Nuitka_AsyncgenAsendObject;
static PyObject *_Nuitka_AsyncgenAsend_throw2(PyThreadState *tstate, struct Nuitka_AsyncgenAsendObject *asyncgen_asend,
                                              struct Nuitka_ExceptionPreservationItem *exception_state);
#endif

static PyObject *_Nuitka_Generator_throw2(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                          struct Nuitka_ExceptionPreservationItem *exception_state) {
#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Enter", generator);
    PRINT_COROUTINE_VALUE("yield_from", generator->m_yield_from);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_NEW_LINE();
#endif

    CHECK_OBJECT(generator);
    assert(Nuitka_Generator_Check((PyObject *)generator));
    CHECK_EXCEPTION_STATE(exception_state);

#if PYTHON_VERSION >= 0x300
    if (generator->m_yield_from != NULL) {
        if (EXCEPTION_STATE_MATCH_BOOL_SINGLE(tstate, exception_state, PyExc_GeneratorExit)) {
            // Generators need to close the yield_from.
            Nuitka_MarkGeneratorAsRunning(generator);
            bool res = Nuitka_gen_close_iter(tstate, generator->m_yield_from);
            Nuitka_MarkGeneratorAsNotRunning(generator);

            if (res == false) {
                // Release exception, we are done with it now and pick up the new one.
                RELEASE_ERROR_OCCURRED_STATE(exception_state);

                FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);
            }

            // Transferred exception ownership to "_Nuitka_Generator_send".
            return _Nuitka_Generator_send(tstate, generator, NULL, exception_state);
        }

        PyObject *ret;

#if _DEBUG_GENERATOR
        PRINT_GENERATOR_STATUS("Passing to yielded from", generator);
        PRINT_COROUTINE_VALUE("m_yield_from", generator->m_yield_from);
        PRINT_NEW_LINE();
#endif

        if (Nuitka_Generator_Check(generator->m_yield_from)) {
            struct Nuitka_GeneratorObject *gen = ((struct Nuitka_GeneratorObject *)generator->m_yield_from);
            // Transferred exception ownership to "_Nuitka_Generator_throw2".
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = _Nuitka_Generator_throw2(tstate, gen, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);
#if NUITKA_UNCOMPILED_THROW_INTEGRATION
        } else if (PyGen_CheckExact(generator->m_yield_from)) {
            PyGenObject *gen = (PyGenObject *)generator->m_yield_from;

            // Transferred exception ownership to "Nuitka_UncompiledGenerator_throw".
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = Nuitka_UncompiledGenerator_throw(tstate, gen, 1, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);
#endif
#if PYTHON_VERSION >= 0x350
        } else if (Nuitka_Coroutine_Check(generator->m_yield_from)) {
            struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineObject *)generator->m_yield_from);
            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);
        } else if (Nuitka_CoroutineWrapper_Check(generator->m_yield_from)) {
            struct Nuitka_CoroutineObject *coro =
                ((struct Nuitka_CoroutineWrapperObject *)generator->m_yield_from)->m_coroutine;

            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);
#if NUITKA_UNCOMPILED_THROW_INTEGRATION
        } else if (PyCoro_CheckExact(generator->m_yield_from)) {
            PyGenObject *gen = (PyGenObject *)generator->m_yield_from;

            // Transferred exception ownership to "Nuitka_UncompiledGenerator_throw".
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = Nuitka_UncompiledGenerator_throw(tstate, gen, 1, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);
#endif
#if PYTHON_VERSION >= 0x360
        } else if (Nuitka_AsyncgenAsend_Check(generator->m_yield_from)) {
            struct Nuitka_AsyncgenAsendObject *asyncgen_asend =
                ((struct Nuitka_AsyncgenAsendObject *)generator->m_yield_from);

            // Transferred exception ownership to "_Nuitka_AsyncgenAsend_throw2".
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = _Nuitka_AsyncgenAsend_throw2(tstate, asyncgen_asend, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);
#endif
#endif
        } else {
            PyObject *meth = PyObject_GetAttr(generator->m_yield_from, const_str_plain_throw);
            if (unlikely(meth == NULL)) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    // Release exception, we are done with it now.
                    RELEASE_ERROR_OCCURRED_STATE(exception_state);

                    return NULL;
                }

                CLEAR_ERROR_OCCURRED(tstate);

                // Passing exception ownership to that code.
                goto throw_here;
            }

            CHECK_EXCEPTION_STATE(exception_state);

#if 0
            // TODO: Add slow mode traces.
            PRINT_ITEM(coroutine->m_yield_from);
            PRINT_NEW_LINE();
#endif
            Nuitka_MarkGeneratorAsRunning(generator);
            ret = Nuitka_CallGeneratorThrowMethod(meth, exception_state);
            Nuitka_MarkGeneratorAsNotRunning(generator);

            Py_DECREF(meth);

            // Release exception, we are done with it now.
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
        }

        if (unlikely(ret == NULL)) {
            // Return value or exception, not to continue with yielding from.
            if (generator->m_yield_from != NULL) {
                CHECK_OBJECT(generator->m_yield_from);
#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Null return, yield from removal:", generator);
                PRINT_COROUTINE_VALUE("yield_from", generator->m_yield_from);
#endif
                Py_DECREF(generator->m_yield_from);
                generator->m_yield_from = NULL;
            }

            PyObject *val;
            if (Nuitka_PyGen_FetchStopIterationValue(tstate, &val)) {
                CHECK_OBJECT(val);

#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Sending return value into ourselves", generator);
                PRINT_COROUTINE_VALUE("value", val);
                PRINT_NEW_LINE();
#endif

                struct Nuitka_ExceptionPreservationItem no_exception_state;
                INIT_ERROR_OCCURRED_STATE(&no_exception_state);

                ret = _Nuitka_Generator_send(tstate, generator, val, &no_exception_state);
            } else {
#if _DEBUG_GENERATOR
                PRINT_GENERATOR_STATUS("Sending exception value into ourselves", generator);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif

                struct Nuitka_ExceptionPreservationItem no_exception_state;
                INIT_ERROR_OCCURRED_STATE(&no_exception_state);

                ret = _Nuitka_Generator_send(tstate, generator, NULL, &no_exception_state);
            }

#if _DEBUG_GENERATOR
            PRINT_GENERATOR_STATUS("Leave with value/exception from sending into ourselves:", generator);
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        } else {
#if _DEBUG_GENERATOR
            PRINT_GENERATOR_STATUS("Leave with return value:", generator);
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        }

        return ret;
    }

throw_here:
#endif

    // We continue to have exception ownership here.

    if (unlikely(_Nuitka_Generator_check_throw(tstate, exception_state) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw already.
        return NULL;
    }

    if (generator->m_status == status_Running) {
        // Passing exception ownership to _Nuitka_Generator_send
        PyObject *result = _Nuitka_Generator_send(tstate, generator, NULL, exception_state);

        if (result == NULL) {
            if (HAS_ERROR_OCCURRED(tstate) == false) {
                SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
            }
        }

        return result;
    } else if (generator->m_status == status_Finished) {
        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

        return NULL;
    } else {
        PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(exception_state);

        if (exception_tb == NULL) {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame =
                MAKE_FUNCTION_FRAME(tstate, generator->m_code_object, generator->m_module, 0);
            SET_EXCEPTION_STATE_TRACEBACK(exception_state,
                                          MAKE_TRACEBACK(frame, generator->m_code_object->co_firstlineno));
            Py_DECREF(frame);
        }

        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

        Nuitka_MarkGeneratorAsFinished(generator);

        return NULL;
    }
}

static PyObject *Nuitka_Generator_throw(struct Nuitka_GeneratorObject *generator, PyObject *args) {
    PyObject *exception_type;
    PyObject *exception_value = NULL;
    PyTracebackObject *exception_tb = NULL;

    // This takes no references, that is for us to do.
    int res = PyArg_UnpackTuple(args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb);

    if (unlikely(res == 0)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();

    // Handing ownership of exception over, we need not release it ourselves
    struct Nuitka_ExceptionPreservationItem exception_state;
    if (_Nuitka_Generator_make_throw_exception_state(tstate, &exception_state, exception_type, exception_value,
                                                     exception_tb) == false) {
        return NULL;
    }

    PyObject *result = _Nuitka_Generator_throw2(tstate, generator, &exception_state);

    if (result == NULL) {
        if (HAS_ERROR_OCCURRED(tstate) == false) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }
    }

#if _DEBUG_GENERATOR
    PRINT_GENERATOR_STATUS("Leave", generator);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_COROUTINE_VALUE("return value", result);
    PRINT_CURRENT_EXCEPTION();
#endif

    return result;
}

#if PYTHON_VERSION >= 0x300

// Need to integrate with garbage collector to undo finalization.
#if PYTHON_VERSION >= 0x300

#if PYTHON_VERSION < 0x380
#define _PyGC_CLEAR_FINALIZED(o) _PyGC_SET_FINALIZED(o, 0)
#elif PYTHON_VERSION < 0x3d0
#define _PyGCHead_SET_UNFINALIZED(g) ((g)->_gc_prev &= (~_PyGC_PREV_MASK_FINALIZED))
#define _PyGC_CLEAR_FINALIZED(o) _PyGCHead_SET_UNFINALIZED(_Py_AS_GC(o))
#endif
#endif

#if !defined(_PyGC_FINALIZED) && PYTHON_VERSION < 0x3d0
#define _PyGC_FINALIZED(o) _PyGCHead_FINALIZED(_Py_AS_GC(o))
#endif
#if !defined(_PyType_IS_GC) && PYTHON_VERSION < 0x3d0
#define _PyType_IS_GC(t) PyType_HasFeature((t), Py_TPFLAGS_HAVE_GC)
#endif

// Replacement for PyObject_CallFinalizer
static void Nuitka_CallFinalizer(PyObject *self) {
    PyTypeObject *type = Py_TYPE(self);

    // Do not call this otherwise.
    assert(type->tp_finalize != NULL);

    assert(_PyType_IS_GC(type));
    if (_PyGC_FINALIZED(self)) {
        return;
    }

    type->tp_finalize(self);

#if PYTHON_VERSION >= 0x380
    _PyGC_SET_FINALIZED(self);
#else
    _PyGC_SET_FINALIZED(self, 1);
#endif
}

// Replacement for PyObject_CallFinalizerFromDealloc
static bool Nuitka_CallFinalizerFromDealloc(PyObject *self) {
    assert(Py_REFCNT(self) == 0);

    // Temporarily resurrect the object, so it can be worked with.
    Py_SET_REFCNT(self, 1);

    Nuitka_CallFinalizer(self);

    assert(Py_REFCNT(self) > 0);

    // Undo the temporary resurrection
    Py_SET_REFCNT(self, Py_REFCNT(self) - 1);
    if (Py_REFCNT(self) == 0) {
        return true;
    } else {
        assert((!_PyType_IS_GC(Py_TYPE(self)) || _PyObject_GC_IS_TRACKED(self)));

        return false;
    }
}

static void Nuitka_Generator_tp_finalizer(struct Nuitka_GeneratorObject *generator) {
    if (generator->m_status != status_Running) {
        return;
    }

    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    bool close_result = _Nuitka_Generator_close(tstate, generator);

    if (unlikely(close_result == false)) {
        PyErr_WriteUnraisable((PyObject *)generator);
    }

    // Restore the saved exception if any.
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}
#endif

// Freelist setup
#define MAX_GENERATOR_FREE_LIST_COUNT 100
static struct Nuitka_GeneratorObject *free_list_generators = NULL;
static int free_list_generators_count = 0;

static void Nuitka_Generator_tp_dealloc(struct Nuitka_GeneratorObject *generator) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Generator_Type -= 1;
    count_released_Nuitka_Generator_Type += 1;
#endif

    if (generator->m_weakrefs != NULL) {
        Nuitka_GC_UnTrack(generator);

        // TODO: Avoid API call and make this our own function to reuse the
        // pattern of temporarily untracking the value or maybe even to avoid
        // the need to do it. It may also be a lot of work to do that though
        // and maybe having weakrefs is uncommon.
        PyObject_ClearWeakRefs((PyObject *)generator);

        Nuitka_GC_Track(generator);
    }

#if PYTHON_VERSION >= 0x300
    if (Nuitka_CallFinalizerFromDealloc((PyObject *)generator) == false) {
        return;
    }
#else
    // Revive temporarily.
    assert(Py_REFCNT(generator) == 0);
    Py_SET_REFCNT(generator, 1);

    PyThreadState *tstate = PyThreadState_GET();

    // Save the current exception, if any, we must preserve it.
    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    if (generator->m_status == status_Running) {
        bool close_result = _Nuitka_Generator_close(tstate, generator);
        CHECK_OBJECT(generator);

        if (unlikely(close_result == false)) {
            PyErr_WriteUnraisable((PyObject *)generator);
        }
    }

    Nuitka_Generator_release_closure(generator);

    // Allow for above code to resurrect the generator.
    Py_SET_REFCNT(generator, Py_REFCNT(generator) - 1);
    if (Py_REFCNT(generator) >= 1) {
        return;
    }
#endif

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack(generator);

    Nuitka_Generator_release_closure(generator);

    if (generator->m_frame != NULL) {
#if PYTHON_VERSION >= 0x300
        Nuitka_SetFrameGenerator(generator->m_frame, NULL);
#endif
        Py_DECREF(generator->m_frame);
    }

    Py_DECREF(generator->m_name);

#if PYTHON_VERSION >= 0x350
    Py_DECREF(generator->m_qualname);
#endif

#if PYTHON_VERSION >= 0x300
    // TODO: Maybe push this into the freelist code and do
    // it on allocation.
    _PyGC_CLEAR_FINALIZED((PyObject *)generator);
#endif

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_generators, generator, MAX_GENERATOR_FREE_LIST_COUNT);

#if PYTHON_VERSION < 0x300
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
#endif
}

static long Nuitka_Generator_tp_hash(struct Nuitka_GeneratorObject *generator) { return generator->m_counter; }

static PyObject *Nuitka_Generator_get_name(PyObject *self, void *data) {
    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    PyObject *result = generator->m_name;
    Py_INCREF(result);
    return result;
}

#if PYTHON_VERSION >= 0x350
static int Nuitka_Generator_set_name(PyObject *self, PyObject *value, void *data) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must be set to a string object");
        return -1;
    }

    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    PyObject *tmp = generator->m_name;
    Py_INCREF(value);
    generator->m_name = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Generator_get_qualname(PyObject *self, void *data) {
    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    PyObject *result = generator->m_qualname;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Generator_set_qualname(PyObject *self, PyObject *value, void *data) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__qualname__ must be set to a string object");
        return -1;
    }

    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    PyObject *tmp = generator->m_qualname;
    Py_INCREF(value);
    generator->m_qualname = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Generator_get_yield_from(PyObject *self, void *data) {
    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    if (generator->m_yield_from) {
        Py_INCREF(generator->m_yield_from);
        return generator->m_yield_from;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

#endif

static PyObject *Nuitka_Generator_get_code(PyObject *self, void *data) {
    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    PyObject *result = (PyObject *)generator->m_code_object;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Generator_set_code(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "gi_code is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Generator_get_frame(PyObject *self, void *data) {
    PyObject *result;

    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
    if (generator->m_frame) {
        result = (PyObject *)generator->m_frame;
    } else {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Generator_set_frame(PyObject *self, PyObject *value, void *data) {
    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "gi_frame is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Generator_get_running(PyObject *self, void *data) {
    PyObject *result;

    struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)self;
/* The type of "gi_running" changed in Python3. */
#if PYTHON_VERSION < 0x300
    result = Nuitka_PyInt_FromLong(generator->m_running);
#else
    result = BOOL_FROM(generator->m_running != 0);
    Py_INCREF_IMMORTAL(result);
#endif
    return result;
}

static int Nuitka_Generator_set_running(PyObject *self, PyObject *value, void *data) {
#if PYTHON_VERSION < 0x300
    PyObject *exception_type = PyExc_TypeError;
#else
    PyObject *exception_type = PyExc_AttributeError;
#endif

    PyThreadState *tstate = PyThreadState_GET();

#if !defined(_NUITKA_FULL_COMPAT) || PYTHON_VERSION >= 0x3a0
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, exception_type,
                                    "attribute 'gi_running' of 'generator' objects is not writable");
#else
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, exception_type, "readonly attribute");
#endif
    return -1;
}

// spell-checker: ignore gi_yieldfrom

static PyGetSetDef Nuitka_Generator_tp_getset[] = {
#if PYTHON_VERSION < 0x350
    {(char *)"__name__", Nuitka_Generator_get_name, NULL, NULL},
#else
    {(char *)"__name__", Nuitka_Generator_get_name, Nuitka_Generator_set_name, NULL},
    {(char *)"__qualname__", Nuitka_Generator_get_qualname, Nuitka_Generator_set_qualname, NULL},
    {(char *)"gi_yieldfrom", Nuitka_Generator_get_yield_from, NULL, NULL},
#endif
    {(char *)"gi_code", Nuitka_Generator_get_code, Nuitka_Generator_set_code, NULL},
    {(char *)"gi_frame", Nuitka_Generator_get_frame, Nuitka_Generator_set_frame, NULL},
    {(char *)"gi_running", Nuitka_Generator_get_running, Nuitka_Generator_set_running, NULL},

    {NULL}};

static PyMethodDef Nuitka_Generator_methods[] = {{"send", (PyCFunction)Nuitka_Generator_send, METH_O, NULL},
                                                 {"throw", (PyCFunction)Nuitka_Generator_throw, METH_VARARGS, NULL},
                                                 {"close", (PyCFunction)Nuitka_Generator_close, METH_NOARGS, NULL},
                                                 {NULL}};

// This is only used.
#if PYTHON_VERSION >= 0x3a0
static PyAsyncMethods Nuitka_Generator_as_async = {
    NULL, /* am_await */
    NULL, /* am_aiter */
    NULL, /* am_anext */
    // TODO: have this too, (sendfunc)_Nuitka_Generator_am_send
    NULL /* am_send */
};
#endif

PyTypeObject Nuitka_Generator_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_generator", // tp_name
    sizeof(struct Nuitka_GeneratorObject),               // tp_basicsize
    sizeof(struct Nuitka_CellObject *),                  // tp_itemsize
    (destructor)Nuitka_Generator_tp_dealloc,             // tp_dealloc
    0,                                                   // tp_print
    0,                                                   // tp_getattr
    0,                                                   // tp_setattr
#if PYTHON_VERSION < 0x3a0
    0, // tp_as_async
#else
    &Nuitka_Generator_as_async, // tp_as_async
#endif
    (reprfunc)Nuitka_Generator_tp_repr, // tp_repr
    0,                                  // tp_as_number
    0,                                  // tp_as_sequence
    0,                                  // tp_as_mapping
    (hashfunc)Nuitka_Generator_tp_hash, // tp_hash
    0,                                  // tp_call
    0,                                  // tp_str
    0,                                  // tp_getattro (PyObject_GenericGetAttr)
    0,                                  // tp_setattro
    0,                                  // tp_as_buffer
#if PYTHON_VERSION < 0x300
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
#else
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE,
#endif
    // tp_flags
    0,                                                   // tp_doc
    (traverseproc)Nuitka_Generator_tp_traverse,          // tp_traverse
    0,                                                   // tp_clear
    0,                                                   // tp_richcompare
    offsetof(struct Nuitka_GeneratorObject, m_weakrefs), // tp_weaklistoffset
    0,                                                   // tp_iter (PyObject_SelfIter)
    (iternextfunc)Nuitka_Generator_tp_iternext,          // tp_iternext
    Nuitka_Generator_methods,                            // tp_methods
    NULL,                                                // tp_members
    Nuitka_Generator_tp_getset,                          // tp_getset
    0,                                                   // tp_base
    0,                                                   // tp_dict
    0,                                                   // tp_descr_get
    0,                                                   // tp_descr_set
    0,                                                   // tp_dictoffset
    0,                                                   // tp_init
    0,                                                   // tp_alloc
    0,                                                   // tp_new
    0,                                                   // tp_free
    0,                                                   // tp_is_gc
    0,                                                   // tp_bases
    0,                                                   // tp_mro
    0,                                                   // tp_cache
    0,                                                   // tp_subclasses
    0,                                                   // tp_weaklist
    0,                                                   // tp_del
    0                                                    // tp_version_tag
#if PYTHON_VERSION >= 0x300
    ,
    (destructor)Nuitka_Generator_tp_finalizer // tp_finalize
#endif
};

#if PYTHON_VERSION >= 0x350
static void _initCompiledCoroutineTypes();
#endif
#if PYTHON_VERSION >= 0x360
static void _initCompiledAsyncgenTypes();
#endif

void _initCompiledGeneratorType(void) {
    Nuitka_PyType_Ready(&Nuitka_Generator_Type, &PyGen_Type, true, false, true, false, false);

    // Be a paranoid subtype of uncompiled function, we want nothing shared.
    assert(Nuitka_Generator_Type.tp_doc != PyGen_Type.tp_doc || PyGen_Type.tp_doc == NULL);
    assert(Nuitka_Generator_Type.tp_traverse != PyGen_Type.tp_traverse);
    assert(Nuitka_Generator_Type.tp_clear != PyGen_Type.tp_clear || PyGen_Type.tp_clear == NULL);
    assert(Nuitka_Generator_Type.tp_richcompare != PyGen_Type.tp_richcompare || PyGen_Type.tp_richcompare == NULL);
    assert(Nuitka_Generator_Type.tp_iter != PyGen_Type.tp_iter || PyGen_Type.tp_iter == PyObject_SelfIter);
    assert(Nuitka_Generator_Type.tp_iternext != PyGen_Type.tp_iternext || PyGen_Type.tp_iternext == NULL);
#if PYTHON_VERSION >= 0x350
    assert(Nuitka_Generator_Type.tp_as_async != PyGen_Type.tp_as_async || PyGen_Type.tp_as_async == NULL);
#endif
    assert(Nuitka_Generator_Type.tp_methods != PyGen_Type.tp_methods);
    assert(Nuitka_Generator_Type.tp_members != PyGen_Type.tp_members);
    assert(Nuitka_Generator_Type.tp_getset != PyGen_Type.tp_getset);
    assert(Nuitka_Generator_Type.tp_base != PyGen_Type.tp_base);
    assert(Nuitka_Generator_Type.tp_dict != PyGen_Type.tp_dict);
    assert(Nuitka_Generator_Type.tp_descr_get != PyGen_Type.tp_descr_get || PyGen_Type.tp_descr_get == NULL);

    assert(Nuitka_Generator_Type.tp_descr_set != PyGen_Type.tp_descr_set || PyGen_Type.tp_descr_set == NULL);
    assert(Nuitka_Generator_Type.tp_dictoffset != PyGen_Type.tp_dictoffset || PyGen_Type.tp_dictoffset == 0);
    // TODO: These get changed and into the same thing, not sure what to compare against, project something
    // assert(Nuitka_Generator_Type.tp_init != PyGen_Type.tp_init || PyGen_Type.tp_init == NULL);
    // assert(Nuitka_Generator_Type.tp_alloc != PyGen_Type.tp_alloc || PyGen_Type.tp_alloc == NULL);
    // assert(Nuitka_Generator_Type.tp_new != PyGen_Type.tp_new || PyGen_Type.tp_new == NULL);
    // assert(Nuitka_Generator_Type.tp_free != PyGen_Type.tp_free || PyGen_Type.tp_free == NULL);
    assert(Nuitka_Generator_Type.tp_bases != PyGen_Type.tp_bases);
    assert(Nuitka_Generator_Type.tp_mro != PyGen_Type.tp_mro);
    assert(Nuitka_Generator_Type.tp_cache != PyGen_Type.tp_cache || PyGen_Type.tp_cache == NULL);
    assert(Nuitka_Generator_Type.tp_subclasses != PyGen_Type.tp_subclasses || PyGen_Type.tp_cache == NULL);
    assert(Nuitka_Generator_Type.tp_weaklist != PyGen_Type.tp_weaklist);
    assert(Nuitka_Generator_Type.tp_del != PyGen_Type.tp_del || PyGen_Type.tp_del == NULL);
#if PYTHON_VERSION >= 0x300
    assert(Nuitka_Generator_Type.tp_finalize != PyGen_Type.tp_finalize || PyGen_Type.tp_finalize == NULL);
#endif

#if PYTHON_VERSION >= 0x350
    // Also initialize coroutines if necessary
    _initCompiledCoroutineTypes();
#endif

#if PYTHON_VERSION >= 0x360
    // Also initialize asyncgen if necessary
    _initCompiledAsyncgenTypes();
#endif
}

PyObject *Nuitka_Generator_New(generator_code code, PyObject *module, PyObject *name,
#if PYTHON_VERSION >= 0x350
                               PyObject *qualname,
#endif
                               PyCodeObject *code_object, struct Nuitka_CellObject **closure, Py_ssize_t closure_given,
                               Py_ssize_t heap_storage_size) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Generator_Type += 1;
    count_allocated_Nuitka_Generator_Type += 1;
#endif

    struct Nuitka_GeneratorObject *result;

    // TODO: Change the var part of the type to 1 maybe
    Py_ssize_t full_size = closure_given + (heap_storage_size + sizeof(void *) - 1) / sizeof(void *);

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_generators, struct Nuitka_GeneratorObject, Nuitka_Generator_Type, full_size);

    // For quicker access of generator heap.
    result->m_heap_storage = &result->m_closure[closure_given];

    assert(result != NULL);
    CHECK_OBJECT(result);

    assert(Py_SIZE(result) >= closure_given);

    result->m_code = (void *)code;

    CHECK_OBJECT(module);
    result->m_module = module;

    CHECK_OBJECT(name);
    result->m_name = name;
    Py_INCREF(name);

#if PYTHON_VERSION >= 0x350
    // The "qualname" defaults to NULL for most compact C code.
    if (qualname == NULL) {
        qualname = name;
    }
    CHECK_OBJECT(qualname);

    result->m_qualname = qualname;
    Py_INCREF(qualname);
#endif

#if PYTHON_VERSION >= 0x300
    result->m_yield_from = NULL;
#endif

    memcpy(&result->m_closure[0], closure, closure_given * sizeof(struct Nuitka_CellObject *));
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = 0;

    result->m_yield_return_index = 0;

#if PYTHON_VERSION >= 0x300
    result->m_returned = NULL;
#endif

    result->m_frame = NULL;
    result->m_code_object = code_object;

#if PYTHON_VERSION >= 0x370
    result->m_exc_state = Nuitka_ExceptionStackItem_Empty;
#endif

#if PYTHON_VERSION >= 0x300
    result->m_resume_exception = Nuitka_ExceptionStackItem_Empty;
#endif

    static long Nuitka_Generator_counter = 0;
    result->m_counter = Nuitka_Generator_counter++;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

static PyObject *_EMPTY_GENERATOR_CONTEXT(PyThreadState *tstate, struct Nuitka_GeneratorObject *generator,
                                          PyObject *yield_return_value) {
    return NULL;
}

PyObject *Nuitka_Generator_NewEmpty(PyObject *module, PyObject *name,
#if PYTHON_VERSION >= 0x350
                                    PyObject *qualname,
#endif
                                    PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                    Py_ssize_t closure_given) {
    return Nuitka_Generator_New(_EMPTY_GENERATOR_CONTEXT, module, name,
#if PYTHON_VERSION >= 0x350
                                qualname,
#endif
                                code_object, closure, closure_given, 0);
}

// Chain coroutine code to generator code, as it uses same functions, and then we can
// have some things static if both are in the same compilation unit. This also loads
// the asyncgen for 3.6 and higher.
#if PYTHON_VERSION >= 0x350
#include "CompiledCoroutineType.c"
#endif

// Chain frames to generator and asyncgen code, as they need to close them with access
// to best functions.
#include "CompiledFrameType.c"

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
