//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** Compiled Coroutines.
 *
 * Unlike in CPython, we have one type for just coroutines, this doesn't do generators
 * nor asyncgen.
 *
 * It strives to be full replacement for normal coroutines.
 *
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/freelists.h"
#include "nuitka/prelude.h"
#include <structmember.h>
#endif

// For reporting about reference counts per type.
#if _DEBUG_REFCOUNTS
int count_active_Nuitka_Coroutine_Type = 0;
int count_allocated_Nuitka_Coroutine_Type = 0;
int count_released_Nuitka_Coroutine_Type = 0;
int count_active_Nuitka_CoroutineWrapper_Type = 0;
int count_allocated_Nuitka_CoroutineWrapper_Type = 0;
int count_released_Nuitka_CoroutineWrapper_Type = 0;
int count_active_Nuitka_AIterWrapper_Type = 0;
int count_allocated_Nuitka_AIterWrapper_Type = 0;
int count_released_Nuitka_AIterWrapper_Type = 0;
#endif

static void Nuitka_MarkCoroutineAsFinished(struct Nuitka_CoroutineObject *coroutine) {
    coroutine->m_status = status_Finished;

#if PYTHON_VERSION >= 0x3b0
    if (coroutine->m_frame) {
        coroutine->m_frame->m_frame_state = FRAME_COMPLETED;
    }
#endif
}

static void Nuitka_MarkCoroutineAsRunning(struct Nuitka_CoroutineObject *coroutine) {
    coroutine->m_running = 1;

    if (coroutine->m_frame) {
        Nuitka_Frame_MarkAsExecuting(coroutine->m_frame);
    }
}

static void Nuitka_MarkCoroutineAsNotRunning(struct Nuitka_CoroutineObject *coroutine) {
    coroutine->m_running = 0;

    if (coroutine->m_frame) {
        Nuitka_Frame_MarkAsNotExecuting(coroutine->m_frame);
    }
}

static PyObject *_Nuitka_Coroutine_send(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine,
                                        PyObject *value, bool closing,
                                        struct Nuitka_ExceptionPreservationItem *exception_state);

static long Nuitka_Coroutine_tp_hash(struct Nuitka_CoroutineObject *coroutine) { return coroutine->m_counter; }

static PyObject *Nuitka_Coroutine_get_name(PyObject *self, void *data) {
    CHECK_OBJECT(self);

    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    Py_INCREF(coroutine->m_name);
    return coroutine->m_name;
}

static int Nuitka_Coroutine_set_name(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(value);

    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must be set to a string object");
        return -1;
    }

    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    PyObject *tmp = coroutine->m_name;
    Py_INCREF(value);
    coroutine->m_name = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Coroutine_get_qualname(PyObject *self, void *data) {
    CHECK_OBJECT(self);

    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    Py_INCREF(coroutine->m_qualname);
    return coroutine->m_qualname;
}

static int Nuitka_Coroutine_set_qualname(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(value);

    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__qualname__ must be set to a string object");
        return -1;
    }

    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    PyObject *tmp = coroutine->m_qualname;
    Py_INCREF(value);
    coroutine->m_qualname = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Coroutine_get_cr_await(PyObject *self, void *data) {
    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT_X(coroutine->m_yield_from);

    if (coroutine->m_yield_from) {
        Py_INCREF(coroutine->m_yield_from);
        return coroutine->m_yield_from;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

static PyObject *Nuitka_Coroutine_get_code(PyObject *self, void *data) {
    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT(coroutine->m_code_object);

    Py_INCREF(coroutine->m_code_object);
    return (PyObject *)coroutine->m_code_object;
}

static int Nuitka_Coroutine_set_code(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cr_code is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Coroutine_get_frame(PyObject *self, void *data) {
    struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)self;
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT_X(coroutine->m_frame);

    if (coroutine->m_frame) {
        Py_INCREF(coroutine->m_frame);
        return (PyObject *)coroutine->m_frame;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

static int Nuitka_Coroutine_set_frame(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(value);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "gi_frame is not writable in Nuitka");
    return -1;
}

static void Nuitka_Coroutine_release_closure(struct Nuitka_CoroutineObject *coroutine) {
    CHECK_OBJECT(coroutine);

    for (Py_ssize_t i = 0; i < coroutine->m_closure_given; i++) {
        CHECK_OBJECT(coroutine->m_closure[i]);
        Py_DECREF(coroutine->m_closure[i]);
    }

    coroutine->m_closure_given = 0;
}

// Note: Shared with asyncgen.
static PyObject *_Nuitka_YieldFromCore(PyThreadState *tstate, PyObject *yield_from, PyObject *send_value,
                                       PyObject **returned_value, bool mode) {
    // Send iteration value to the sub-generator, which may be a CPython
    // generator object, something with an iterator next, or a send method,
    // where the later is only required if values other than "None" need to
    // be passed in.
    CHECK_OBJECT(yield_from);
    CHECK_OBJECT_X(send_value);

    assert(send_value != NULL || HAS_ERROR_OCCURRED(tstate));

    PyObject *retval;

    struct Nuitka_ExceptionPreservationItem exception_state;

    FETCH_ERROR_OCCURRED_STATE(tstate, &exception_state);

    if (HAS_EXCEPTION_STATE(&exception_state)) {
        // Exception, was thrown into us, need to send that to sub-generator.
        // We acquired ownership of the published exception and need to release it potentially.

        // Transfer exception owner this.
        retval = _Nuitka_YieldFromPassExceptionTo(tstate, yield_from, &exception_state);

        // TODO: This wants to look at retval most definitely, send_value is going to be NULL.
        if (unlikely(send_value == NULL)) {
            PyObject *error = GET_ERROR_OCCURRED(tstate);

            if (error != NULL && EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopIteration)) {
                *returned_value = ERROR_GET_STOP_ITERATION_VALUE(tstate);
                assert(!HAS_ERROR_OCCURRED(tstate));

                return NULL;
            }
        }
    } else if (PyGen_CheckExact(yield_from) || PyCoro_CheckExact(yield_from)) {
        retval = Nuitka_PyGen_Send(tstate, (PyGenObject *)yield_from, Py_None);
    } else if (send_value == Py_None && Nuitka_CoroutineWrapper_Check(yield_from)) {
        struct Nuitka_CoroutineObject *yieldfrom_coroutine =
            ((struct Nuitka_CoroutineWrapperObject *)yield_from)->m_coroutine;

        Py_INCREF_IMMORTAL(Py_None);

        struct Nuitka_ExceptionPreservationItem no_exception_state;
        INIT_ERROR_OCCURRED_STATE(&no_exception_state);

        retval = _Nuitka_Coroutine_send(tstate, yieldfrom_coroutine, Py_None, mode ? false : true, &no_exception_state);
    } else if (send_value == Py_None && Py_TYPE(yield_from)->tp_iternext != NULL) {
        retval = Py_TYPE(yield_from)->tp_iternext(yield_from);
    } else {
#if 0
        // TODO: Add slow mode traces.
        PRINT_ITEM(yield_from);
        PRINT_NEW_LINE();
#endif

        retval = PyObject_CallMethodObjArgs(yield_from, const_str_plain_send, send_value, NULL);
    }

    // Check the sub-generator result
    if (retval == NULL) {
        PyObject *error = GET_ERROR_OCCURRED(tstate);

        if (error == NULL) {
            Py_INCREF_IMMORTAL(Py_None);
            *returned_value = Py_None;
        } else if (likely(EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopIteration))) {
            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            *returned_value = ERROR_GET_STOP_ITERATION_VALUE(tstate);
            assert(!HAS_ERROR_OCCURRED(tstate));

            assert(*returned_value != NULL);
        } else {
            *returned_value = NULL;
        }

        return NULL;
    } else {
        assert(!HAS_ERROR_OCCURRED(tstate));
        return retval;
    }
}

static PyObject *_Nuitka_YieldFromCoroutineCore(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine,
                                                PyObject *send_value, bool mode) {
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT_X(send_value);

    PyObject *yield_from = coroutine->m_yield_from;
    CHECK_OBJECT(yield_from);

    // Need to make it unaccessible while using it.
    coroutine->m_yield_from = NULL;

    PyObject *returned_value;
    PyObject *yielded = _Nuitka_YieldFromCore(tstate, yield_from, send_value, &returned_value, mode);

    if (yielded == NULL) {
        assert(coroutine->m_yield_from == NULL);
        Py_DECREF(yield_from);

        yielded = ((coroutine_code)coroutine->m_code)(tstate, coroutine, returned_value);
    } else {
        assert(coroutine->m_yield_from == NULL);
        coroutine->m_yield_from = yield_from;
    }

    return yielded;
}

#if _DEBUG_COROUTINE
NUITKA_MAY_BE_UNUSED static void _PRINT_COROUTINE_STATUS(char const *descriptor, char const *context,
                                                         struct Nuitka_CoroutineObject *coroutine) {
    char const *status;

    switch (coroutine->m_status) {
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
    PRINT_ITEM((PyObject *)coroutine);
    PRINT_STRING(" ");
    PRINT_REFCOUNT((PyObject *)coroutine);
    PRINT_STRING(status);
    PRINT_NEW_LINE();
}

#define PRINT_COROUTINE_STATUS(context, coroutine) _PRINT_COROUTINE_STATUS(__FUNCTION__, context, coroutine)

#endif

static PyObject *Nuitka_YieldFromCoroutineNext(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine) {
    CHECK_OBJECT(coroutine);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_NEW_LINE();
#endif
    PyObject *result = _Nuitka_YieldFromCoroutineCore(tstate, coroutine, Py_None, true);
#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Leave", coroutine);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif
    return result;
}

static PyObject *Nuitka_YieldFromCoroutineInitial(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine,
                                                  PyObject *send_value) {
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT_X(send_value);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_NEW_LINE();
#endif
    PyObject *result = _Nuitka_YieldFromCoroutineCore(tstate, coroutine, send_value, false);
#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Leave", coroutine);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif
    return result;
}

static void Nuitka_SetStopIterationValue(PyThreadState *tstate, PyObject *value);

// This function is called when sending a value or exception to be handled in the coroutine
// Note:
//   Exception arguments are passed for ownership and must be released before returning. The
//   value of exception_type may be NULL, and the actual exception will not necessarily
//   be normalized.

static PySendResult _Nuitka_Coroutine_sendR(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine,
                                            PyObject *value, bool closing,
                                            struct Nuitka_ExceptionPreservationItem *exception_state,
                                            PyObject **result) {
    CHECK_OBJECT(coroutine);
    assert(Nuitka_Coroutine_Check((PyObject *)coroutine));
    CHECK_EXCEPTION_STATE_X(exception_state);
    CHECK_OBJECT_X(value);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_COROUTINE_STRING("closing", closing ? "(closing) " : "(not closing) ");
    PRINT_COROUTINE_VALUE("value", value);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    // Not both a value and an exception please.
    if (value != NULL) {
        ASSERT_EMPTY_EXCEPTION_STATE(exception_state);
    }

    if (coroutine->m_status == status_Unused && value != NULL && value != Py_None) {
        // No exception if value is given.
        Py_XDECREF(value);

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "can't send non-None value to a just-started coroutine");
        return PYGEN_ERROR;
    }

    if (coroutine->m_status != status_Finished) {
        if (coroutine->m_running) {
            Py_XDECREF(value);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "coroutine already executing");
            return PYGEN_ERROR;
        }

        // Put the coroutine back on the frame stack.
        Nuitka_ThreadStateFrameType *return_frame = _Nuitka_GetThreadStateFrame(tstate);

        // Consider it as running.
        if (coroutine->m_status == status_Unused) {
            coroutine->m_status = status_Running;
            assert(coroutine->m_resume_frame == NULL);

            // Value will not be used, can only be Py_None or NULL.
            Py_XDECREF(value);
            value = NULL;
        } else {
            assert(coroutine->m_resume_frame);
            pushFrameStackGenerator(tstate, coroutine->m_resume_frame);

            coroutine->m_resume_frame = NULL;
        }

        // Continue the yielder function while preventing recursion.
        Nuitka_MarkCoroutineAsRunning(coroutine);

        // Check for thrown exception, publish it to the coroutine code.
        if (unlikely(HAS_EXCEPTION_STATE(exception_state))) {
            assert(value == NULL);

            // Transfer exception ownership to published.
            RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);
        }

#if _DEBUG_COROUTINE
        PRINT_COROUTINE_STATUS("Switching to coroutine", coroutine);
        PRINT_COROUTINE_VALUE("value", value);
        PRINT_CURRENT_EXCEPTION();
        PRINT_NEW_LINE();
        // dumpFrameStack();
#endif

        PyObject *yielded;

        if (coroutine->m_yield_from == NULL) {
            yielded = ((coroutine_code)coroutine->m_code)(tstate, coroutine, value);
        } else {
            // This does not release the value if any, so we need to do it afterwards.
            yielded = Nuitka_YieldFromCoroutineInitial(tstate, coroutine, value);
            Py_XDECREF(value);
        }

        // If the coroutine returns with m_yield_from set, it wants us to yield
        // from that value from now on.
        while (yielded == NULL && coroutine->m_yield_from != NULL) {
            yielded = Nuitka_YieldFromCoroutineNext(tstate, coroutine);
        }

        Nuitka_MarkCoroutineAsNotRunning(coroutine);

        // Remove the back frame from coroutine if it's there.
        if (coroutine->m_frame) {
            // assert(tstate->frame == &coroutine->m_frame->m_frame);
            assertFrameObject(coroutine->m_frame);

            Py_CLEAR(coroutine->m_frame->m_frame.f_back);

            // Remember where to resume from.
            coroutine->m_resume_frame = _Nuitka_GetThreadStateFrame(tstate);
        }

        // Return back to the frame that called us.
        _Nuitka_GeneratorPopFrame(tstate, return_frame);

#if _DEBUG_COROUTINE
        PRINT_COROUTINE_STATUS("Returned from coroutine", coroutine);
        // dumpFrameStack();
#endif

#ifndef __NUITKA_NO_ASSERT__
        if (return_frame) {
            assertThreadFrameObject(return_frame);
        }
#endif

        if (yielded == NULL) {
#if _DEBUG_COROUTINE
            PRINT_COROUTINE_STATUS("finishing from yield", coroutine);
            PRINT_COROUTINE_STRING("closing", closing ? "(closing) " : "(not closing) ");
            PRINT_STRING("-> finishing coroutine sets status_Finished\n");
            PRINT_COROUTINE_VALUE("return_value", coroutine->m_returned);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
            Nuitka_MarkCoroutineAsFinished(coroutine);

            if (coroutine->m_frame != NULL) {
                Nuitka_SetFrameGenerator(coroutine->m_frame, NULL);
                Py_DECREF(coroutine->m_frame);
                coroutine->m_frame = NULL;
            }

            Nuitka_Coroutine_release_closure(coroutine);

            // Create StopIteration if necessary, i.e. return value that is not "None" was
            // given. TODO: Push this further down the user line, we might be able to avoid
            // it for some uses, e.g. quick iteration entirely.
            if (coroutine->m_returned) {
                *result = coroutine->m_returned;

                coroutine->m_returned = NULL;

#if _DEBUG_COROUTINE
                PRINT_COROUTINE_STATUS("Return value to exception set", coroutine);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif
                return PYGEN_RETURN;
            } else {
                PyObject *error = GET_ERROR_OCCURRED(tstate);

                if (error == NULL) {
                    *result = NULL;

                    return PYGEN_RETURN;
                } else if (error == PyExc_StopIteration) {
                    RAISE_RUNTIME_ERROR_RAISED_STOP_ITERATION(tstate, "coroutine raised StopIteration");

#if _DEBUG_COROUTINE
                    PRINT_COROUTINE_STATUS("Leave with exception set", coroutine);
                    PRINT_CURRENT_EXCEPTION();
                    PRINT_NEW_LINE();
#endif
                }

                return PYGEN_ERROR;
            }
        } else {
            *result = yielded;
            return PYGEN_NEXT;
        }
    } else {
        Py_XDECREF(value);

        // Release exception if any, we are finished with it and will raise another.
        RELEASE_ERROR_OCCURRED_STATE_X(exception_state);

        /* This is for status_Finished */
        assert(coroutine->m_status == status_Finished);
        /* This check got added in Python 3.5.2 only. It's good to do it, but
         * not fully compatible, therefore guard it.
         */
#if PYTHON_VERSION >= 0x352 || !defined(_NUITKA_FULL_COMPAT)
        if (closing == false) {
#if _DEBUG_COROUTINE
            PRINT_COROUTINE_STATUS("Finished coroutine sent into -> RuntimeError", coroutine);
            PRINT_NEW_LINE();
#endif
            PyErr_Format(PyExc_RuntimeError,
#if !defined(_NUITKA_FULL_COMPAT)
                         "cannot reuse already awaited compiled_coroutine %S", coroutine->m_qualname
#else
                         "cannot reuse already awaited coroutine"
#endif
            );

            return PYGEN_ERROR;
        } else
#endif
        {
            *result = NULL;
            return PYGEN_RETURN;
        }
    }
}

static PyObject *_Nuitka_Coroutine_send(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine,
                                        PyObject *value, bool closing,
                                        struct Nuitka_ExceptionPreservationItem *exception_state) {

    PyObject *result;
    PySendResult res = _Nuitka_Coroutine_sendR(tstate, coroutine, value, closing, exception_state, &result);

    switch (res) {
    case PYGEN_RETURN:
        if (result != NULL) {
            if (result != Py_None) {
                Nuitka_SetStopIterationValue(tstate, result);
            }

            Py_DECREF(result);
        }

        return NULL;
    case PYGEN_NEXT:
        return result;
    case PYGEN_ERROR:
        return NULL;
    default:
        NUITKA_CANNOT_GET_HERE("invalid PYGEN_ result");
    }
}

static PyObject *Nuitka_Coroutine_send(struct Nuitka_CoroutineObject *coroutine, PyObject *value) {
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT(value);

    // We need to transfer ownership of the sent value.
    Py_INCREF(value);

    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    PyObject *result = _Nuitka_Coroutine_send(tstate, coroutine, value, false, &exception_state);

    if (result == NULL) {
        if (HAS_ERROR_OCCURRED(tstate) == false) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }
    }

    return result;
}

// Note: Used by compiled frames.
static bool _Nuitka_Coroutine_close(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine) {
#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
#endif
    CHECK_OBJECT(coroutine);

    if (coroutine->m_status == status_Running) {
        struct Nuitka_ExceptionPreservationItem exception_state;
        SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, &exception_state, PyExc_GeneratorExit, NULL, NULL);

        PyObject *result = _Nuitka_Coroutine_send(tstate, coroutine, NULL, true, &exception_state);

        if (unlikely(result)) {
            Py_DECREF(result);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "coroutine ignored GeneratorExit");
            return false;
        } else {
            return DROP_ERROR_OCCURRED_GENERATOR_EXIT_OR_STOP_ITERATION(tstate);
        }
    }

    return true;
}

static PyObject *Nuitka_Coroutine_close(struct Nuitka_CoroutineObject *coroutine) {
    PyThreadState *tstate = PyThreadState_GET();

    bool r = _Nuitka_Coroutine_close(tstate, coroutine);

    if (unlikely(r == false)) {
        return NULL;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

#if PYTHON_VERSION >= 0x360
static bool Nuitka_AsyncgenAsend_Check(PyObject *object);
struct Nuitka_AsyncgenAsendObject;
static PyObject *_Nuitka_AsyncgenAsend_throw2(PyThreadState *tstate, struct Nuitka_AsyncgenAsendObject *asyncgen_asend,
                                              struct Nuitka_ExceptionPreservationItem *exception_state);
#endif

static bool _Nuitka_Generator_check_throw(PyThreadState *tstate,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);

// This function is called when yielding to a coroutine through "_Nuitka_YieldFromPassExceptionTo"
// and potentially wrapper objects used by generators, or by the throw method itself.
// Note:
//   Exception arguments are passed for ownership and must be released before returning. The
//   value of exception_type will not be NULL, but the actual exception will not necessarily
//   be normalized.
static PyObject *_Nuitka_Coroutine_throw2(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine, bool closing,
                                          struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT(coroutine);
    assert(Nuitka_Coroutine_Check((PyObject *)coroutine));
    CHECK_EXCEPTION_STATE(exception_state);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_COROUTINE_STRING("closing", closing ? "(closing) " : "(not closing) ");
    PRINT_COROUTINE_VALUE("yield_from", coroutine->m_yield_from);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_NEW_LINE();
#endif

    if (coroutine->m_yield_from != NULL) {
        if (EXCEPTION_STATE_MATCH_BOOL_SINGLE(tstate, exception_state, PyExc_GeneratorExit)) {
            // Coroutines need to close the yield_from.
            Nuitka_MarkCoroutineAsRunning(coroutine);
            bool res = Nuitka_gen_close_iter(tstate, coroutine->m_yield_from);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);

            if (res == false) {
                // Release exception, we are done with it now and pick up the new one.
                RELEASE_ERROR_OCCURRED_STATE(exception_state);

                FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);
            }

            // Transferred exception ownership to "_Nuitka_Coroutine_send".
            return _Nuitka_Coroutine_send(tstate, coroutine, NULL, false, exception_state);
        }

        PyObject *ret;

#if _DEBUG_COROUTINE
        PRINT_COROUTINE_STATUS("Passing to yielded from", coroutine);
        PRINT_COROUTINE_VALUE("m_yield_from", coroutine->m_yield_from);
        PRINT_NEW_LINE();
#endif

        if (Nuitka_Generator_Check(coroutine->m_yield_from)) {
            struct Nuitka_GeneratorObject *gen = ((struct Nuitka_GeneratorObject *)coroutine->m_yield_from);
            // Transferred exception ownership to "_Nuitka_Generator_throw2".
            Nuitka_MarkCoroutineAsRunning(coroutine);
            ret = _Nuitka_Generator_throw2(tstate, gen, exception_state);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);
        } else if (Nuitka_Coroutine_Check(coroutine->m_yield_from)) {
            struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineObject *)coroutine->m_yield_from);
            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            Nuitka_MarkCoroutineAsRunning(coroutine);
            ret = _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);
#if NUITKA_UNCOMPILED_THROW_INTEGRATION
        } else if (PyGen_CheckExact(coroutine->m_yield_from) || PyCoro_CheckExact(coroutine->m_yield_from)) {
            PyGenObject *gen = (PyGenObject *)coroutine->m_yield_from;

            // Transferred exception ownership to "Nuitka_UncompiledGenerator_throw".
            Nuitka_MarkCoroutineAsRunning(coroutine);
            ret = Nuitka_UncompiledGenerator_throw(tstate, gen, 1, exception_state);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);
#endif
        } else if (Nuitka_CoroutineWrapper_Check(coroutine->m_yield_from)) {
            struct Nuitka_CoroutineObject *coro =
                ((struct Nuitka_CoroutineWrapperObject *)coroutine->m_yield_from)->m_coroutine;

            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            Nuitka_MarkCoroutineAsRunning(coroutine);
            ret = _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);
#if PYTHON_VERSION >= 0x360
        } else if (Nuitka_AsyncgenAsend_Check(coroutine->m_yield_from)) {
            struct Nuitka_AsyncgenAsendObject *asyncgen_asend =
                ((struct Nuitka_AsyncgenAsendObject *)coroutine->m_yield_from);

            // Transferred exception ownership to "_Nuitka_AsyncgenAsend_throw2".
            Nuitka_MarkCoroutineAsRunning(coroutine);
            ret = _Nuitka_AsyncgenAsend_throw2(tstate, asyncgen_asend, exception_state);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);
#endif
        } else {
            PyObject *meth = PyObject_GetAttr(coroutine->m_yield_from, const_str_plain_throw);
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
            Nuitka_MarkCoroutineAsRunning(coroutine);
            ret = Nuitka_CallGeneratorThrowMethod(meth, exception_state);
            Nuitka_MarkCoroutineAsNotRunning(coroutine);

            Py_DECREF(meth);

            // Release exception, we are done with it now.
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
        }

        if (unlikely(ret == NULL)) {
            // Return value or exception, not to continue with yielding from.
            if (coroutine->m_yield_from != NULL) {
                CHECK_OBJECT(coroutine->m_yield_from);
#if _DEBUG_COROUTINE
                PRINT_COROUTINE_STATUS("Null return, yield from removal:", coroutine);
                PRINT_COROUTINE_VALUE("yield_from", coroutine->m_yield_from);
#endif
                Py_DECREF(coroutine->m_yield_from);
                coroutine->m_yield_from = NULL;
            }

            PyObject *val;
            if (Nuitka_PyGen_FetchStopIterationValue(tstate, &val)) {
                CHECK_OBJECT(val);

#if _DEBUG_COROUTINE
                PRINT_COROUTINE_STATUS("Sending return value into ourselves", coroutine);
                PRINT_COROUTINE_VALUE("value", val);
                PRINT_NEW_LINE();
#endif

                struct Nuitka_ExceptionPreservationItem no_exception_state;
                INIT_ERROR_OCCURRED_STATE(&no_exception_state);

                // The ownership of val is transferred.
                ret = _Nuitka_Coroutine_send(tstate, coroutine, val, false, &no_exception_state);
            } else {
#if _DEBUG_COROUTINE
                PRINT_COROUTINE_STATUS("Sending exception value into ourselves", coroutine);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif

                struct Nuitka_ExceptionPreservationItem no_exception_state;
                INIT_ERROR_OCCURRED_STATE(&no_exception_state);

                ret = _Nuitka_Coroutine_send(tstate, coroutine, NULL, false, &no_exception_state);
            }

#if _DEBUG_COROUTINE
            PRINT_COROUTINE_STATUS("Leave with value/exception from sending into ourselves:", coroutine);
            PRINT_COROUTINE_STRING("closing", closing ? "(closing) " : "(not closing) ");
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        } else {
#if _DEBUG_COROUTINE
            PRINT_COROUTINE_STATUS("Leave with return value:", coroutine);
            PRINT_COROUTINE_STRING("closing", closing ? "(closing) " : "(not closing) ");
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        }

        return ret;
    }

throw_here:
    // We continue to have exception ownership here.

    if (unlikely(_Nuitka_Generator_check_throw(tstate, exception_state) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw already.
        return NULL;
    }

    if (coroutine->m_status == status_Running) {
        // Transferred exception ownership to "_Nuitka_Coroutine_send".
        PyObject *result = _Nuitka_Coroutine_send(tstate, coroutine, NULL, false, exception_state);
        return result;
    } else if (coroutine->m_status == status_Finished) {

        /* This check got added in Python 3.5.2 only. It's good to do it, but
         * not fully compatible, therefore guard it.
         */
#if PYTHON_VERSION >= 0x352 || !defined(_NUITKA_FULL_COMPAT)
        if (closing == false) {
#if _DEBUG_COROUTINE
            PRINT_STRING("Finished coroutine thrown into -> RuntimeError\n");
            PRINT_ITEM(coroutine->m_qualname);
            PRINT_NEW_LINE();
#endif
            PyErr_Format(PyExc_RuntimeError,
#if !defined(_NUITKA_FULL_COMPAT)
                         "cannot reuse already awaited compiled_coroutine %S", coroutine->m_qualname
#else
                         "cannot reuse already awaited coroutine"
#endif
            );

            RELEASE_ERROR_OCCURRED_STATE(exception_state);

            return NULL;
        }
#endif
        // Passing exception to publication.
        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

        return NULL;
    } else {
        PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(exception_state);

        if (exception_tb == NULL) {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame =
                MAKE_FUNCTION_FRAME(tstate, coroutine->m_code_object, coroutine->m_module, 0);
            SET_EXCEPTION_STATE_TRACEBACK(exception_state,
                                          MAKE_TRACEBACK(frame, coroutine->m_code_object->co_firstlineno));
            Py_DECREF(frame);
        }

        // Passing exception to publication.
        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

#if _DEBUG_COROUTINE
        PRINT_COROUTINE_STATUS("Finishing from exception", coroutine);
        PRINT_NEW_LINE();
#endif

        Nuitka_MarkCoroutineAsFinished(coroutine);

        return NULL;
    }
}

static PyObject *Nuitka_Coroutine_throw(struct Nuitka_CoroutineObject *coroutine, PyObject *args) {
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT_DEEP(args);

    PyObject *exception_type;
    PyObject *exception_value = NULL;
    PyTracebackObject *exception_tb = NULL;

    // This takes no references, that is for us to do.
    int res = PyArg_UnpackTuple(args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb);

    if (unlikely(res == 0)) {
        return NULL;
    }

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_NEW_LINE();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    // Handing ownership of exception over, we need not release it ourselves
    struct Nuitka_ExceptionPreservationItem exception_state;
    if (_Nuitka_Generator_make_throw_exception_state(tstate, &exception_state, exception_type, exception_value,
                                                     exception_tb) == false) {
        return NULL;
    }

    PyObject *result = _Nuitka_Coroutine_throw2(tstate, coroutine, false, &exception_state);

    if (result == NULL) {
        if (HAS_ERROR_OCCURRED(tstate) == false) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }
    }

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Leave", coroutine);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_COROUTINE_VALUE("return value", result);
    PRINT_CURRENT_EXCEPTION();
#endif

    return result;
}

static PyObject *Nuitka_Coroutine_tp_repr(struct Nuitka_CoroutineObject *coroutine) {
    CHECK_OBJECT(coroutine);
    CHECK_OBJECT(coroutine->m_qualname);

    return PyUnicode_FromFormat("<compiled_coroutine object %s at %p>", Nuitka_String_AsString(coroutine->m_qualname),
                                coroutine);
}

static long Nuitka_Coroutine_tp_traverse(struct Nuitka_CoroutineObject *coroutine, visitproc visit, void *arg) {
    CHECK_OBJECT(coroutine);

    // TODO: Identify the impact of not visiting owned objects like module
    Py_VISIT(coroutine->m_yield_from);

    for (Py_ssize_t i = 0; i < coroutine->m_closure_given; i++) {
        Py_VISIT(coroutine->m_closure[i]);
    }

    Py_VISIT(coroutine->m_frame);

    return 0;
}

static struct Nuitka_CoroutineWrapperObject *free_list_coro_wrappers = NULL;
static int free_list_coro_wrappers_count = 0;

static PyObject *Nuitka_Coroutine_await(struct Nuitka_CoroutineObject *coroutine) {
    CHECK_OBJECT(coroutine);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_NEW_LINE();
#endif

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_CoroutineWrapper_Type += 1;
    count_allocated_Nuitka_CoroutineWrapper_Type += 1;
#endif

    struct Nuitka_CoroutineWrapperObject *result;

    allocateFromFreeListFixed(free_list_coro_wrappers, struct Nuitka_CoroutineWrapperObject,
                              Nuitka_CoroutineWrapper_Type);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    result->m_coroutine = coroutine;
    Py_INCREF(result->m_coroutine);

    Nuitka_GC_Track(result);

    return (PyObject *)result;
}

#if PYTHON_VERSION >= 0x3a0
static PySendResult _Nuitka_Coroutine_am_send(struct Nuitka_CoroutineObject *coroutine, PyObject *arg,
                                              PyObject **result) {
#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
#endif
    PyThreadState *tstate = PyThreadState_GET();

    // We need to transfer ownership of the sent value.
    Py_INCREF(arg);

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    PySendResult res = _Nuitka_Coroutine_sendR(tstate, coroutine, arg, false, &exception_state, result);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Leave", coroutine);
    PRINT_COROUTINE_VALUE("result", *result);
    PRINT_NEW_LINE();
#endif
    return res;
}
#endif

static void Nuitka_Coroutine_tp_finalize(struct Nuitka_CoroutineObject *coroutine) {
    if (coroutine->m_status != status_Running) {
        return;
    }

    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    bool close_result = _Nuitka_Coroutine_close(tstate, coroutine);

    if (unlikely(close_result == false)) {
        PyErr_WriteUnraisable((PyObject *)coroutine);
    }

    /* Restore the saved exception if any. */
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}

#define MAX_COROUTINE_FREE_LIST_COUNT 100
static struct Nuitka_CoroutineObject *free_list_coros = NULL;
static int free_list_coros_count = 0;

static void Nuitka_Coroutine_tp_dealloc(struct Nuitka_CoroutineObject *coroutine) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Coroutine_Type -= 1;
    count_released_Nuitka_Coroutine_Type += 1;
#endif

    // Revive temporarily.
    assert(Py_REFCNT(coroutine) == 0);
    Py_SET_REFCNT(coroutine, 1);

    PyThreadState *tstate = PyThreadState_GET();

    // Save the current exception, if any, we must preserve it.
    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

#if _DEBUG_COROUTINE
    PRINT_COROUTINE_STATUS("Enter", coroutine);
    PRINT_NEW_LINE();
#endif

    bool close_result = _Nuitka_Coroutine_close(tstate, coroutine);

    if (unlikely(close_result == false)) {
        PyErr_WriteUnraisable((PyObject *)coroutine);
    }

    Nuitka_Coroutine_release_closure(coroutine);

    // Allow for above code to resurrect the coroutine.
    Py_SET_REFCNT(coroutine, Py_REFCNT(coroutine) - 1);
    if (Py_REFCNT(coroutine) >= 1) {
        RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
        return;
    }

    if (coroutine->m_frame) {
        Nuitka_SetFrameGenerator(coroutine->m_frame, NULL);
        Py_DECREF(coroutine->m_frame);
        coroutine->m_frame = NULL;
    }

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack(coroutine);

    if (coroutine->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)coroutine);
        assert(!HAS_ERROR_OCCURRED(tstate));
    }

    Py_DECREF(coroutine->m_name);
    Py_DECREF(coroutine->m_qualname);

#if PYTHON_VERSION >= 0x370
    Py_XDECREF(coroutine->m_origin);
#endif

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_coros, coroutine, MAX_COROUTINE_FREE_LIST_COUNT);

    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyMethodDef Nuitka_Coroutine_methods[] = {{"send", (PyCFunction)Nuitka_Coroutine_send, METH_O, NULL},
                                                 {"throw", (PyCFunction)Nuitka_Coroutine_throw, METH_VARARGS, NULL},
                                                 {"close", (PyCFunction)Nuitka_Coroutine_close, METH_NOARGS, NULL},
                                                 {NULL}};

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyGetSetDef Nuitka_Coroutine_tp_getset[] = {
    {(char *)"__name__", Nuitka_Coroutine_get_name, Nuitka_Coroutine_set_name, NULL},
    {(char *)"__qualname__", Nuitka_Coroutine_get_qualname, Nuitka_Coroutine_set_qualname, NULL},
    {(char *)"cr_await", Nuitka_Coroutine_get_cr_await, NULL, NULL},
    {(char *)"cr_code", Nuitka_Coroutine_get_code, Nuitka_Coroutine_set_code, NULL},
    {(char *)"cr_frame", Nuitka_Coroutine_get_frame, Nuitka_Coroutine_set_frame, NULL},

    {NULL}};

static PyMemberDef Nuitka_Coroutine_members[] = {
    {(char *)"cr_running", T_BOOL, offsetof(struct Nuitka_CoroutineObject, m_running), READONLY},
#if PYTHON_VERSION >= 0x370
    {(char *)"cr_origin", T_OBJECT, offsetof(struct Nuitka_CoroutineObject, m_origin), READONLY},

#endif
    {NULL}};

static PyAsyncMethods Nuitka_Coroutine_as_async = {
    (unaryfunc)Nuitka_Coroutine_await, // am_await
    0,                                 // am_aiter
    0                                  // am_anext
#if PYTHON_VERSION >= 0x3a0
    ,
    (sendfunc)_Nuitka_Coroutine_am_send // am_send
#endif

};

PyTypeObject Nuitka_Coroutine_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_coroutine",                // tp_name
    sizeof(struct Nuitka_CoroutineObject),                              // tp_basicsize
    sizeof(struct Nuitka_CellObject *),                                 // tp_itemsize
    (destructor)Nuitka_Coroutine_tp_dealloc,                            // tp_dealloc
    0,                                                                  // tp_print
    0,                                                                  // tp_getattr
    0,                                                                  // tp_setattr
    &Nuitka_Coroutine_as_async,                                         // tp_as_async
    (reprfunc)Nuitka_Coroutine_tp_repr,                                 // tp_repr
    0,                                                                  // tp_as_number
    0,                                                                  // tp_as_sequence
    0,                                                                  // tp_as_mapping
    (hashfunc)Nuitka_Coroutine_tp_hash,                                 // tp_hash
    0,                                                                  // tp_call
    0,                                                                  // tp_str
    0,                                                                  // tp_getattro (PyObject_GenericGetAttr)
    0,                                                                  // tp_setattro
    0,                                                                  // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE, // tp_flags
    0,                                                                  // tp_doc
    (traverseproc)Nuitka_Coroutine_tp_traverse,                         // tp_traverse
    0,                                                                  // tp_clear
    0,                                                                  // tp_richcompare
    offsetof(struct Nuitka_CoroutineObject, m_weakrefs),                // tp_weaklistoffset
    0,                                                                  // tp_iter
    0,                                                                  // tp_iternext
    Nuitka_Coroutine_methods,                                           // tp_methods
    Nuitka_Coroutine_members,                                           // tp_members
    Nuitka_Coroutine_tp_getset,                                         // tp_getset
    0,                                                                  // tp_base
    0,                                                                  // tp_dict
    0,                                                                  // tp_descr_get
    0,                                                                  // tp_descr_set
    0,                                                                  // tp_dictoffset
    0,                                                                  // tp_init
    0,                                                                  // tp_alloc
    0,                                                                  // tp_new
    0,                                                                  // tp_free
    0,                                                                  // tp_is_gc
    0,                                                                  // tp_bases
    0,                                                                  // tp_mro
    0,                                                                  // tp_cache
    0,                                                                  // tp_subclasses
    0,                                                                  // tp_weaklist
    0,                                                                  // tp_del
    0,                                                                  // tp_version_tag
    (destructor)Nuitka_Coroutine_tp_finalize,                           // tp_finalize
};

static void Nuitka_CoroutineWrapper_tp_dealloc(struct Nuitka_CoroutineWrapperObject *cw) {
    Nuitka_GC_UnTrack((PyObject *)cw);

    assert(Py_REFCNT(cw) == 0);
    Py_SET_REFCNT(cw, 1);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_CoroutineWrapper_Type -= 1;
    count_released_Nuitka_CoroutineWrapper_Type += 1;
#endif
    CHECK_OBJECT(cw->m_coroutine);

    Py_DECREF(cw->m_coroutine);
    cw->m_coroutine = NULL;

    assert(Py_REFCNT(cw) == 1);
    Py_SET_REFCNT(cw, 0);

    releaseToFreeList(free_list_coro_wrappers, cw, MAX_COROUTINE_FREE_LIST_COUNT);
}

static PyObject *Nuitka_CoroutineWrapper_tp_iternext(struct Nuitka_CoroutineWrapperObject *cw) {
    CHECK_OBJECT(cw);

    return Nuitka_Coroutine_send(cw->m_coroutine, Py_None);
}

static int Nuitka_CoroutineWrapper_tp_traverse(struct Nuitka_CoroutineWrapperObject *cw, visitproc visit, void *arg) {
    CHECK_OBJECT(cw);

    Py_VISIT((PyObject *)cw->m_coroutine);
    return 0;
}

static PyObject *Nuitka_CoroutineWrapper_send(struct Nuitka_CoroutineWrapperObject *cw, PyObject *arg) {
    CHECK_OBJECT(cw);
    CHECK_OBJECT(arg);

    return Nuitka_Coroutine_send(cw->m_coroutine, arg);
}

static PyObject *Nuitka_CoroutineWrapper_throw(struct Nuitka_CoroutineWrapperObject *cw, PyObject *args) {
    CHECK_OBJECT(cw);
    CHECK_OBJECT_DEEP(args);

    return Nuitka_Coroutine_throw(cw->m_coroutine, args);
}

static PyObject *Nuitka_CoroutineWrapper_close(struct Nuitka_CoroutineWrapperObject *cw) {
    CHECK_OBJECT(cw);

    return Nuitka_Coroutine_close(cw->m_coroutine);
}

static PyObject *Nuitka_CoroutineWrapper_tp_repr(struct Nuitka_CoroutineWrapperObject *cw) {
    CHECK_OBJECT(cw);
    CHECK_OBJECT(cw->m_coroutine);
    CHECK_OBJECT(cw->m_coroutine->m_qualname);

    return PyUnicode_FromFormat("<compiled_coroutine_wrapper object %s at %p>",
                                Nuitka_String_AsString(cw->m_coroutine->m_qualname), cw);
}

static PyMethodDef Nuitka_CoroutineWrapper_methods[] = {
    {"send", (PyCFunction)Nuitka_CoroutineWrapper_send, METH_O, NULL},
    {"throw", (PyCFunction)Nuitka_CoroutineWrapper_throw, METH_VARARGS, NULL},
    {"close", (PyCFunction)Nuitka_CoroutineWrapper_close, METH_NOARGS, NULL},
    {NULL}};

PyTypeObject Nuitka_CoroutineWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_coroutine_wrapper",
    sizeof(struct Nuitka_CoroutineWrapperObject),      // tp_basicsize
    0,                                                 // tp_itemsize
    (destructor)Nuitka_CoroutineWrapper_tp_dealloc,    // tp_dealloc
    0,                                                 // tp_print
    0,                                                 // tp_getattr
    0,                                                 // tp_setattr
    0,                                                 // tp_as_async
    (reprfunc)Nuitka_CoroutineWrapper_tp_repr,         // tp_repr
    0,                                                 // tp_as_number
    0,                                                 // tp_as_sequence
    0,                                                 // tp_as_mapping
    0,                                                 // tp_hash
    0,                                                 // tp_call
    0,                                                 // tp_str
    0,                                                 // tp_getattro (PyObject_GenericGetAttr)
    0,                                                 // tp_setattro
    0,                                                 // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,           // tp_flags
    0,                                                 // tp_doc
    (traverseproc)Nuitka_CoroutineWrapper_tp_traverse, // tp_traverse
    0,                                                 // tp_clear
    0,                                                 // tp_richcompare
    0,                                                 // tp_weaklistoffset
    0,                                                 // tp_iter (PyObject_SelfIter)
    (iternextfunc)Nuitka_CoroutineWrapper_tp_iternext, // tp_iternext
    Nuitka_CoroutineWrapper_methods,                   // tp_methods
    0,                                                 // tp_members
    0,                                                 // tp_getset
    0,                                                 // tp_base
    0,                                                 // tp_dict
    0,                                                 // tp_descr_get
    0,                                                 // tp_descr_set
    0,                                                 // tp_dictoffset
    0,                                                 // tp_init
    0,                                                 // tp_alloc
    0,                                                 // tp_new
    0,                                                 // tp_free
};

#if PYTHON_VERSION >= 0x3b0

// Not exported by the core library.
static int Nuitka_PyInterpreterFrame_GetLine(_PyInterpreterFrame *frame) {
    // TODO: For Nuitka frames there is a better way actually, since
    // we have the line number stored.

    int addr = _PyInterpreterFrame_LASTI(frame) * sizeof(_Py_CODEUNIT);
#if PYTHON_VERSION < 0x3d0
    return PyCode_Addr2Line(frame->f_code, addr);
#else
    return PyCode_Addr2Line((PyCodeObject *)frame->f_executable, addr);
#endif
}

static PyObject *computeCoroutineOrigin(PyThreadState *tstate, int origin_depth) {
    _PyInterpreterFrame *current_frame = CURRENT_TSTATE_INTERPRETER_FRAME(tstate);

    // Create result tuple with correct size.
    int frame_count = 0;
    _PyInterpreterFrame *frame = current_frame;
    while (frame != NULL && frame_count < origin_depth) {
        frame = frame->previous;
        frame_count += 1;
    }
    PyObject *cr_origin = MAKE_TUPLE_EMPTY_VAR(tstate, frame_count);

    frame = current_frame;
    for (int i = 0; i < frame_count; i++) {
        PyCodeObject *code = Nuitka_InterpreterFrame_GetCodeObject(frame);

        int line = Nuitka_PyInterpreterFrame_GetLine(frame);

        PyObject *frame_info = Py_BuildValue("OiO", code->co_filename, line, code->co_name);
        assert(frame_info);

        PyTuple_SET_ITEM(cr_origin, i, frame_info);
        frame = frame->previous;
    }

    return cr_origin;
}

#elif PYTHON_VERSION >= 0x370
static PyObject *computeCoroutineOrigin(PyThreadState *tstate, int origin_depth) {
    PyFrameObject *frame = PyEval_GetFrame();

    int frame_count = 0;

    while (frame != NULL && frame_count < origin_depth) {
        frame = frame->f_back;
        frame_count += 1;
    }

    PyObject *cr_origin = MAKE_TUPLE_EMPTY_VAR(tstate, frame_count);

    frame = PyEval_GetFrame();

    for (int i = 0; i < frame_count; i++) {
        PyObject *frame_info = Py_BuildValue("OiO", Nuitka_Frame_GetCodeObject(frame)->co_filename,
                                             PyFrame_GetLineNumber(frame), frame->f_code->co_name);

        assert(frame_info);

        PyTuple_SET_ITEM(cr_origin, i, frame_info);

        frame = frame->f_back;
    }

    return cr_origin;
}
#endif

PyObject *Nuitka_Coroutine_New(PyThreadState *tstate, coroutine_code code, PyObject *module, PyObject *name,
                               PyObject *qualname, PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                               Py_ssize_t closure_given, Py_ssize_t heap_storage_size) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Coroutine_Type += 1;
    count_allocated_Nuitka_Coroutine_Type += 1;
#endif

    struct Nuitka_CoroutineObject *result;

    // TODO: Change the var part of the type to 1 maybe
    Py_ssize_t full_size = closure_given + (heap_storage_size + sizeof(void *) - 1) / sizeof(void *);

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_coros, struct Nuitka_CoroutineObject, Nuitka_Coroutine_Type, full_size);

    // For quicker access of generator heap.
    result->m_heap_storage = &result->m_closure[closure_given];

    result->m_code = (void *)code;

    CHECK_OBJECT(module);
    result->m_module = module;

    CHECK_OBJECT(name);
    result->m_name = name;
    Py_INCREF(name);

    // The "qualname" defaults to NULL for most compact C code.
    if (qualname == NULL) {
        qualname = name;
    }
    CHECK_OBJECT(qualname);

    result->m_qualname = qualname;
    Py_INCREF(qualname);

    result->m_yield_from = NULL;

    memcpy(&result->m_closure[0], closure, closure_given * sizeof(struct Nuitka_CellObject *));
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = 0;
    result->m_awaiting = false;

    result->m_yield_return_index = 0;

    result->m_returned = NULL;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    result->m_resume_frame = NULL;

#if PYTHON_VERSION >= 0x370
    int origin_depth = tstate->coroutine_origin_tracking_depth;

    if (origin_depth == 0) {
        result->m_origin = NULL;
    } else {
        result->m_origin = computeCoroutineOrigin(tstate, origin_depth);
    }
#endif

#if PYTHON_VERSION >= 0x370
    result->m_exc_state = Nuitka_ExceptionStackItem_Empty;
#endif

    static long Nuitka_Coroutine_counter = 0;
    result->m_counter = Nuitka_Coroutine_counter++;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

static inline PyCodeObject *_Nuitka_PyGen_GetCode(PyGenObject *gen) {
#if PYTHON_VERSION < 0x3c0
    return (PyCodeObject *)gen->gi_code;
#elif PYTHON_VERSION < 0x3d0
    _PyInterpreterFrame *frame = (_PyInterpreterFrame *)(gen->gi_iframe);
    return frame->f_code;
#else
    _PyInterpreterFrame *frame = (_PyInterpreterFrame *)(gen->gi_iframe);
    return (PyCodeObject *)frame->f_executable;
#endif
}

static int gen_is_coroutine(PyObject *object) {
    if (PyGen_CheckExact(object)) {
        PyCodeObject *code = _Nuitka_PyGen_GetCode((PyGenObject *)object);

        if (code->co_flags & CO_ITERABLE_COROUTINE) {
            return 1;
        }
    }

    return 0;
}

static PyObject *Nuitka_GetAwaitableIter(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

#if _DEBUG_COROUTINE
    PRINT_STRING("Nuitka_GetAwaitableIter: Enter ");
    PRINT_ITEM(value);
    PRINT_NEW_LINE();
#endif

    unaryfunc getter = NULL;

    if (PyCoro_CheckExact(value) || gen_is_coroutine(value)) {
        Py_INCREF(value);
        return value;
    }

    if (Py_TYPE(value)->tp_as_async != NULL) {
        getter = Py_TYPE(value)->tp_as_async->am_await;
    }

    if (getter != NULL) {
        PyObject *result = (*getter)(value);

        if (result != NULL) {
            if (unlikely(PyCoro_CheckExact(result) || gen_is_coroutine(result) || Nuitka_Coroutine_Check(result))) {
                Py_DECREF(result);

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__await__() returned a coroutine");

                return NULL;
            }

            if (unlikely(!HAS_ITERNEXT(result))) {
                SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("__await__() returned non-iterator of type '%s'", result);

                Py_DECREF(result);

                return NULL;
            }
        }

        return result;
    }

    SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("object %s can't be used in 'await' expression", value);

    return NULL;
}

#if PYTHON_VERSION >= 0x366
static void FORMAT_AWAIT_ERROR(PyThreadState *tstate, PyObject *value, int await_kind) {
    CHECK_OBJECT(value);

    if (await_kind == await_enter) {
        PyErr_Format(PyExc_TypeError,
                     "'async with' received an object from __aenter__ that does not implement __await__: %s",
                     Py_TYPE(value)->tp_name);
    } else if (await_kind == await_exit) {
        PyErr_Format(PyExc_TypeError,
                     "'async with' received an object from __aexit__ that does not implement __await__: %s",
                     Py_TYPE(value)->tp_name);
    }

    assert(HAS_ERROR_OCCURRED(tstate));
}
#endif

PyObject *ASYNC_AWAIT(PyThreadState *tstate, PyObject *awaitable, int await_kind) {
    CHECK_OBJECT(awaitable);

#if _DEBUG_COROUTINE
    PRINT_STRING("ASYNC_AWAIT: Enter for awaitable ");
    PRINT_STRING(await_kind == await_enter ? "enter" : "exit");
    PRINT_STRING(" ");
    PRINT_ITEM(awaitable);
    PRINT_NEW_LINE();
#endif

    PyObject *awaitable_iter = Nuitka_GetAwaitableIter(tstate, awaitable);

    if (unlikely(awaitable_iter == NULL)) {
#if PYTHON_VERSION >= 0x366
        FORMAT_AWAIT_ERROR(tstate, awaitable, await_kind);
#endif
        return NULL;
    }

#if PYTHON_VERSION >= 0x352 || !defined(_NUITKA_FULL_COMPAT)
    /* This check got added in Python 3.5.2 only. It's good to do it, but
     * not fully compatible, therefore guard it.
     */

    if (Nuitka_Coroutine_Check(awaitable)) {
        struct Nuitka_CoroutineObject *awaited_coroutine = (struct Nuitka_CoroutineObject *)awaitable;

        if (awaited_coroutine->m_awaiting) {
            Py_DECREF(awaitable_iter);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "coroutine is being awaited already");

            return NULL;
        }
    }
#endif

#if _DEBUG_COROUTINE
    PRINT_STRING("ASYNC_AWAIT: Result ");
    PRINT_ITEM(awaitable);
    PRINT_NEW_LINE();
#endif

    return awaitable_iter;
}

#if PYTHON_VERSION >= 0x352

/* Our "aiter" wrapper clone */
struct Nuitka_AIterWrapper {
    /* Python object folklore: */
    PyObject_HEAD

        PyObject *aw_aiter;
};

static PyObject *Nuitka_AIterWrapper_tp_repr(struct Nuitka_AIterWrapper *aw) {
    return PyUnicode_FromFormat("<compiled_aiter_wrapper object of %R at %p>", aw->aw_aiter, aw);
}

static PyObject *Nuitka_AIterWrapper_iternext(struct Nuitka_AIterWrapper *aw) {
    CHECK_OBJECT(aw);

    PyThreadState *tstate = PyThreadState_GET();

#if PYTHON_VERSION < 0x360
    SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_StopIteration, aw->aw_aiter);
#elif PYTHON_VERSION < 0x3c0
    if (!PyTuple_Check(aw->aw_aiter) && !PyExceptionInstance_Check(aw->aw_aiter)) {
        SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_StopIteration, aw->aw_aiter);
    } else {
        PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, PyExc_StopIteration, aw->aw_aiter);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        struct Nuitka_ExceptionPreservationItem exception_state = {_Py_NewRef(PyExc_StopIteration), result, NULL};

        RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
    }
#else
    struct Nuitka_ExceptionPreservationItem exception_state = {Nuitka_CreateStopIteration(tstate, aw->aw_aiter)};

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
#endif

    return NULL;
}

static int Nuitka_AIterWrapper_traverse(struct Nuitka_AIterWrapper *aw, visitproc visit, void *arg) {
    CHECK_OBJECT(aw);

    Py_VISIT((PyObject *)aw->aw_aiter);
    return 0;
}

static struct Nuitka_AIterWrapper *free_list_coroutine_aiter_wrappers = NULL;
static int free_list_coroutine_aiter_wrappers_count = 0;

static void Nuitka_AIterWrapper_dealloc(struct Nuitka_AIterWrapper *aw) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AIterWrapper_Type -= 1;
    count_released_Nuitka_AIterWrapper_Type += 1;
#endif

    Nuitka_GC_UnTrack((PyObject *)aw);

    CHECK_OBJECT(aw->aw_aiter);
    Py_DECREF(aw->aw_aiter);

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_coroutine_aiter_wrappers, aw, MAX_COROUTINE_FREE_LIST_COUNT);
}

static PyAsyncMethods Nuitka_AIterWrapper_as_async = {
    0, // am_await (PyObject_SelfIter)
    0, // am_aiter
    0  // am_anext
};

PyTypeObject Nuitka_AIterWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_aiter_wrapper",
    sizeof(struct Nuitka_AIterWrapper),                          // tp_basicsize
    0,                                                           // tp_itemsize
    (destructor)Nuitka_AIterWrapper_dealloc,                     // tp_dealloc
    0,                                                           // tp_print
    0,                                                           // tp_getattr
    0,                                                           // tp_setattr
    &Nuitka_AIterWrapper_as_async,                               // tp_as_async
    (reprfunc)Nuitka_AIterWrapper_tp_repr,                       // tp_repr
    0,                                                           // tp_as_number
    0,                                                           // tp_as_sequence
    0,                                                           // tp_as_mapping
    0,                                                           // tp_hash
    0,                                                           // tp_call
    0,                                                           // tp_str
    0,                                                           // tp_getattro (PyObject_GenericGetAttr)
    0,                                                           // tp_setattro
    0,                                                           // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                     // tp_flags
    "A wrapper object for '__aiter__' backwards compatibility.", // tp_doc
    (traverseproc)Nuitka_AIterWrapper_traverse,                  // tp_traverse
    0,                                                           // tp_clear
    0,                                                           // tp_richcompare
    0,                                                           // tp_weaklistoffset
    0,                                                           // tp_iter (PyObject_SelfIter)
    (iternextfunc)Nuitka_AIterWrapper_iternext,                  // tp_iternext
    0,                                                           // tp_methods
    0,                                                           // tp_members
    0,                                                           // tp_getset
    0,                                                           // tp_base
    0,                                                           // tp_dict
    0,                                                           // tp_descr_get
    0,                                                           // tp_descr_set
    0,                                                           // tp_dictoffset
    0,                                                           // tp_init
    0,                                                           // tp_alloc
    0,                                                           // tp_new
    0,                                                           // tp_free
};

static PyObject *Nuitka_AIterWrapper_New(PyObject *aiter) {
    CHECK_OBJECT(aiter);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AIterWrapper_Type += 1;
    count_allocated_Nuitka_AIterWrapper_Type += 1;
#endif
    struct Nuitka_AIterWrapper *result;

    allocateFromFreeListFixed(free_list_coroutine_aiter_wrappers, struct Nuitka_AIterWrapper, Nuitka_AIterWrapper_Type);

    CHECK_OBJECT(aiter);

    Py_INCREF(aiter);
    result->aw_aiter = aiter;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

#endif

PyObject *ASYNC_MAKE_ITERATOR(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

#if _DEBUG_COROUTINE
    PRINT_STRING("AITER entry:");
    PRINT_ITEM(value);

    PRINT_NEW_LINE();
#endif

    unaryfunc getter = NULL;

    if (Py_TYPE(value)->tp_as_async) {
        getter = Py_TYPE(value)->tp_as_async->am_aiter;
    }

    if (unlikely(getter == NULL)) {
        PyErr_Format(PyExc_TypeError, "'async for' requires an object with __aiter__ method, got %s",
                     Py_TYPE(value)->tp_name);

        return NULL;
    }

    PyObject *iter = (*getter)(value);

    if (unlikely(iter == NULL)) {
        return NULL;
    }

#if PYTHON_VERSION >= 0x370
    if (unlikely(Py_TYPE(iter)->tp_as_async == NULL || Py_TYPE(iter)->tp_as_async->am_anext == NULL)) {
        PyErr_Format(PyExc_TypeError,
                     "'async for' received an object from __aiter__ that does not implement __anext__: %s",
                     Py_TYPE(iter)->tp_name);

        Py_DECREF(iter);
        return NULL;
    }
#endif

#if PYTHON_VERSION >= 0x352
    /* Starting with Python 3.5.2 it is acceptable to return an async iterator
     * directly, instead of an awaitable.
     */
    if (Py_TYPE(iter)->tp_as_async != NULL && Py_TYPE(iter)->tp_as_async->am_anext != NULL) {
        PyObject *wrapper = Nuitka_AIterWrapper_New(iter);
        Py_DECREF(iter);

        iter = wrapper;
    }
#endif

    PyObject *awaitable_iter = Nuitka_GetAwaitableIter(tstate, iter);

    if (unlikely(awaitable_iter == NULL)) {
#if PYTHON_VERSION >= 0x360
        _PyErr_FormatFromCause(
#else
        PyErr_Format(
#endif
            PyExc_TypeError, "'async for' received an invalid object from __aiter__: %s", Py_TYPE(iter)->tp_name);

        Py_DECREF(iter);

        return NULL;
    }

    Py_DECREF(iter);

    return awaitable_iter;
}

PyObject *ASYNC_ITERATOR_NEXT(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

#if _DEBUG_COROUTINE
    PRINT_STRING("ANEXT entry:");
    PRINT_ITEM(value);

    PRINT_NEW_LINE();
#endif

    unaryfunc getter = NULL;

    if (Py_TYPE(value)->tp_as_async) {
        getter = Py_TYPE(value)->tp_as_async->am_anext;
    }

    if (unlikely(getter == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'async for' requires an iterator with __anext__ method, got %s", value);

        return NULL;
    }

    PyObject *next_value = (*getter)(value);

    if (unlikely(next_value == NULL)) {
        return NULL;
    }

    PyObject *awaitable_iter = Nuitka_GetAwaitableIter(tstate, next_value);

    if (unlikely(awaitable_iter == NULL)) {
#if PYTHON_VERSION >= 0x360
        _PyErr_FormatFromCause(
#else
        PyErr_Format(
#endif
            PyExc_TypeError, "'async for' received an invalid object from __anext__: %s", Py_TYPE(next_value)->tp_name);

        Py_DECREF(next_value);

        return NULL;
    }

    Py_DECREF(next_value);

    return awaitable_iter;
}

static void _initCompiledCoroutineTypes(void) {
    Nuitka_PyType_Ready(&Nuitka_Coroutine_Type, &PyCoro_Type, true, false, false, false, false);

    // Be a paranoid subtype of uncompiled function, we want nothing shared.
    assert(Nuitka_Coroutine_Type.tp_doc != PyCoro_Type.tp_doc || PyCoro_Type.tp_doc == NULL);
    assert(Nuitka_Coroutine_Type.tp_traverse != PyCoro_Type.tp_traverse);
    assert(Nuitka_Coroutine_Type.tp_clear != PyCoro_Type.tp_clear || PyCoro_Type.tp_clear == NULL);
    assert(Nuitka_Coroutine_Type.tp_richcompare != PyCoro_Type.tp_richcompare || PyCoro_Type.tp_richcompare == NULL);
    assert(Nuitka_Coroutine_Type.tp_weaklistoffset != PyCoro_Type.tp_weaklistoffset);
    assert(Nuitka_Coroutine_Type.tp_iter != PyCoro_Type.tp_iter || PyCoro_Type.tp_iter == NULL);
    assert(Nuitka_Coroutine_Type.tp_iternext != PyCoro_Type.tp_iternext || PyCoro_Type.tp_iternext == NULL);
    assert(Nuitka_Coroutine_Type.tp_as_async != PyCoro_Type.tp_as_async || PyCoro_Type.tp_as_async == NULL);
    assert(Nuitka_Coroutine_Type.tp_methods != PyCoro_Type.tp_methods);
    assert(Nuitka_Coroutine_Type.tp_members != PyCoro_Type.tp_members);
    assert(Nuitka_Coroutine_Type.tp_getset != PyCoro_Type.tp_getset);
    assert(Nuitka_Coroutine_Type.tp_dict != PyCoro_Type.tp_dict);
    assert(Nuitka_Coroutine_Type.tp_descr_get != PyCoro_Type.tp_descr_get || PyCoro_Type.tp_descr_get == NULL);

    assert(Nuitka_Coroutine_Type.tp_descr_set != PyCoro_Type.tp_descr_set || PyCoro_Type.tp_descr_set == NULL);
    assert(Nuitka_Coroutine_Type.tp_dictoffset != PyCoro_Type.tp_dictoffset || PyCoro_Type.tp_dictoffset == 0);
    // TODO: These get changed and into the same thing, not sure what to compare against, project something
    // assert(Nuitka_Coroutine_Type.tp_init != PyCoro_Type.tp_init || PyCoro_Type.tp_init == NULL);
    // assert(Nuitka_Coroutine_Type.tp_alloc != PyCoro_Type.tp_alloc || PyCoro_Type.tp_alloc == NULL);
    // assert(Nuitka_Coroutine_Type.tp_new != PyCoro_Type.tp_new || PyCoro_Type.tp_new == NULL);
    // assert(Nuitka_Coroutine_Type.tp_free != PyCoro_Type.tp_free || PyCoro_Type.tp_free == NULL);
    assert(Nuitka_Coroutine_Type.tp_bases != PyCoro_Type.tp_bases);
    assert(Nuitka_Coroutine_Type.tp_mro != PyCoro_Type.tp_mro);
    assert(Nuitka_Coroutine_Type.tp_cache != PyCoro_Type.tp_cache || PyCoro_Type.tp_cache == NULL);
    assert(Nuitka_Coroutine_Type.tp_subclasses != PyCoro_Type.tp_subclasses || PyCoro_Type.tp_cache == NULL);
    assert(Nuitka_Coroutine_Type.tp_weaklist != PyCoro_Type.tp_weaklist);
    assert(Nuitka_Coroutine_Type.tp_del != PyCoro_Type.tp_del || PyCoro_Type.tp_del == NULL);
    assert(Nuitka_Coroutine_Type.tp_finalize != PyCoro_Type.tp_finalize || PyCoro_Type.tp_finalize == NULL);

    Nuitka_PyType_Ready(&Nuitka_CoroutineWrapper_Type, NULL, true, false, true, false, false);

#if PYTHON_VERSION >= 0x352
    Nuitka_PyType_Ready(&Nuitka_AIterWrapper_Type, NULL, true, false, true, true, false);
#endif
}

// Chain asyncgen code to coroutine and generator code, as it uses same functions,
// and then we can have some things static if both are in the same compilation unit.

#if PYTHON_VERSION >= 0x360
#include "CompiledAsyncgenType.c"
#endif

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
