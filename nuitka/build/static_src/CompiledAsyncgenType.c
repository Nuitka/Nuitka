//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** Compiled Asyncgen.
 *
 * Unlike in CPython, we have one type for just asyncgen, this doesn't do
 * generators nor coroutines.
 *
 * It strives to be full replacement for normal asyncgen.
 *
 * spellchecker: ignore Asend,Athrow
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
int count_active_Nuitka_Asyncgen_Type = 0;
int count_allocated_Nuitka_Asyncgen_Type = 0;
int count_released_Nuitka_Asyncgen_Type = 0;
int count_active_Nuitka_AsyncgenValueWrapper_Type = 0;
int count_allocated_Nuitka_AsyncgenValueWrapper_Type = 0;
int count_released_Nuitka_AsyncgenValueWrapper_Type = 0;
int count_active_Nuitka_AsyncgenAsend_Type = 0;
int count_allocated_Nuitka_AsyncgenAsend_Type = 0;
int count_released_Nuitka_AsyncgenAsend_Type = 0;
int count_active_Nuitka_AsyncgenAthrow_Type = 0;
int count_allocated_Nuitka_AsyncgenAthrow_Type = 0;
int count_released_Nuitka_AsyncgenAthrow_Type = 0;
#endif

static void Nuitka_MarkAsyncgenAsFinished(struct Nuitka_AsyncgenObject *asyncgen) {
    asyncgen->m_status = status_Finished;

#if PYTHON_VERSION >= 0x3b0
    if (asyncgen->m_frame) {
        asyncgen->m_frame->m_frame_state = FRAME_COMPLETED;
    }
#endif
}

static void Nuitka_MarkAsyncgenAsRunning(struct Nuitka_AsyncgenObject *asyncgen) {
    asyncgen->m_running = 1;

    if (asyncgen->m_frame) {
        Nuitka_Frame_MarkAsExecuting(asyncgen->m_frame);
    }
}

static void Nuitka_MarkAsyncgenAsNotRunning(struct Nuitka_AsyncgenObject *asyncgen) {
    asyncgen->m_running = 0;

    if (asyncgen->m_frame) {
        Nuitka_Frame_MarkAsNotExecuting(asyncgen->m_frame);
    }
}

static long Nuitka_Asyncgen_tp_hash(struct Nuitka_AsyncgenObject *asyncgen) { return asyncgen->m_counter; }

static PyObject *Nuitka_Asyncgen_get_name(PyObject *self, void *data) {
    CHECK_OBJECT(self);

    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    Py_INCREF(asyncgen->m_name);
    return asyncgen->m_name;
}

static int Nuitka_Asyncgen_set_name(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(value);

    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__name__ must be set to a string object");
        return -1;
    }

    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    PyObject *tmp = asyncgen->m_name;
    Py_INCREF(value);
    asyncgen->m_name = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Asyncgen_get_qualname(PyObject *self, void *data) {
    CHECK_OBJECT(self);

    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    Py_INCREF(asyncgen->m_qualname);
    return asyncgen->m_qualname;
}

static int Nuitka_Asyncgen_set_qualname(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(value);

    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "__qualname__ must be set to a string object");
        return -1;
    }

    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    PyObject *tmp = asyncgen->m_qualname;
    Py_INCREF(value);
    asyncgen->m_qualname = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Asyncgen_get_ag_await(PyObject *self, void *data) {
    CHECK_OBJECT(self);

    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    if (asyncgen->m_yield_from) {
        Py_INCREF(asyncgen->m_yield_from);
        return asyncgen->m_yield_from;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

static PyObject *Nuitka_Asyncgen_get_code(PyObject *self, void *data) {
    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT(asyncgen->m_code_object);

    Py_INCREF(asyncgen->m_code_object);
    return (PyObject *)asyncgen->m_code_object;
}

static int Nuitka_Asyncgen_set_code(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "ag_code is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Asyncgen_get_frame(PyObject *self, void *data) {
    struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)self;
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_X(asyncgen->m_frame);

    if (asyncgen->m_frame) {
        Py_INCREF(asyncgen->m_frame);
        return (PyObject *)asyncgen->m_frame;
    } else {
        Py_INCREF_IMMORTAL(Py_None);
        return Py_None;
    }
}

static int Nuitka_Asyncgen_set_frame(PyObject *self, PyObject *value, void *data) {
    CHECK_OBJECT(self);
    CHECK_OBJECT_X(value);

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "ag_frame is not writable in Nuitka");
    return -1;
}

static void Nuitka_Asyncgen_release_closure(struct Nuitka_AsyncgenObject *asyncgen) {
    CHECK_OBJECT(asyncgen);

    for (Py_ssize_t i = 0; i < asyncgen->m_closure_given; i++) {
        CHECK_OBJECT(asyncgen->m_closure[i]);
        Py_DECREF(asyncgen->m_closure[i]);
    }

    asyncgen->m_closure_given = 0;
}

static PyObject *Nuitka_YieldFromAsyncgenCore(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen,
                                              PyObject *send_value, bool mode) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_X(send_value);

    PyObject *yield_from = asyncgen->m_yield_from;
    CHECK_OBJECT(yield_from);

    // Need to make it unaccessible while using it.
    asyncgen->m_yield_from = NULL;

    PyObject *returned_value;
    PyObject *yielded = _Nuitka_YieldFromCore(tstate, yield_from, send_value, &returned_value, mode);

    if (yielded == NULL) {
        assert(asyncgen->m_yield_from == NULL);
        Py_DECREF(yield_from);

        yielded = ((asyncgen_code)asyncgen->m_code)(tstate, asyncgen, returned_value);
    } else {
        assert(asyncgen->m_yield_from == NULL);
        asyncgen->m_yield_from = yield_from;
    }

    return yielded;
}

#if _DEBUG_ASYNCGEN
NUITKA_MAY_BE_UNUSED static void _PRINT_ASYNCGEN_STATUS(char const *descriptor, char const *context,
                                                        struct Nuitka_AsyncgenObject *asyncgen) {
    char const *status;

    switch (asyncgen->m_status) {
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
    PRINT_ITEM((PyObject *)asyncgen);
    PRINT_STRING(" ");
    PRINT_STRING(status);
    PRINT_NEW_LINE();
}

#define PRINT_ASYNCGEN_STATUS(context, asyncgen) _PRINT_ASYNCGEN_STATUS(__FUNCTION__, context, asyncgen)

#endif

static PyObject *Nuitka_YieldFromAsyncgenNext(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
    CHECK_OBJECT(asyncgen);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
    PRINT_NEW_LINE();
#endif
    PyObject *result = Nuitka_YieldFromAsyncgenCore(tstate, asyncgen, Py_None, true);
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Leave", asyncgen);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_YieldFromAsyncgenInitial(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen,
                                                 PyObject *send_value) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_X(send_value);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
    PRINT_NEW_LINE();
#endif
    PyObject *result = Nuitka_YieldFromAsyncgenCore(tstate, asyncgen, send_value, false);
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Leave", asyncgen);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_AsyncgenValueWrapper_New(PyObject *value);

static PySendResult _Nuitka_Asyncgen_sendR(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen,
                                           PyObject *value, bool closing,
                                           struct Nuitka_ExceptionPreservationItem *exception_state,
                                           PyObject **result) {
    CHECK_OBJECT(asyncgen);
    assert(Nuitka_Asyncgen_Check((PyObject *)asyncgen));
    CHECK_OBJECT_X(value);
    CHECK_EXCEPTION_STATE_X(exception_state);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
    PRINT_COROUTINE_VALUE("value", value);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    if (value != NULL) {
        ASSERT_EMPTY_EXCEPTION_STATE(exception_state);
    }

    if (asyncgen->m_status == status_Unused && value != NULL && value != Py_None) {
        // No exception if value is given.
        Py_XDECREF(value);

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "can't send non-None value to a just-started async generator");
        return PYGEN_ERROR;
    }

    if (asyncgen->m_status != status_Finished) {
        if (asyncgen->m_running) {
            Py_XDECREF(value);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "async generator already executing");
            return PYGEN_ERROR;
        }
        // Put the asyncgen back on the frame stack.
        Nuitka_ThreadStateFrameType *return_frame = _Nuitka_GetThreadStateFrame(tstate);

        // Consider it as running.
        if (asyncgen->m_status == status_Unused) {
            asyncgen->m_status = status_Running;
            assert(asyncgen->m_resume_frame == NULL);

            // Value will not be used, can only be Py_None or NULL.
            Py_XDECREF(value);
            value = NULL;
        } else {
            assert(asyncgen->m_resume_frame);
            pushFrameStackGenerator(tstate, asyncgen->m_resume_frame);

            asyncgen->m_resume_frame = NULL;
        }

        // Continue the yielder function while preventing recursion.
        asyncgen->m_running = true;

        // Check for thrown exception, and publish it.
        if (unlikely(HAS_EXCEPTION_STATE(exception_state))) {
            assert(value == NULL);

            // Transfer exception ownership to published.
            RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);
        }

        if (asyncgen->m_frame) {
            Nuitka_Frame_MarkAsExecuting(asyncgen->m_frame);
        }

#if _DEBUG_ASYNCGEN
        PRINT_ASYNCGEN_STATUS("Switching to asyncgen", asyncgen);
        PRINT_COROUTINE_VALUE("value", value);
        PRINT_CURRENT_EXCEPTION();
        PRINT_NEW_LINE();
        // dumpFrameStack();
#endif

        PyObject *yielded;

        if (asyncgen->m_yield_from == NULL) {
            yielded = ((asyncgen_code)asyncgen->m_code)(tstate, asyncgen, value);
        } else {
            // This does not release the value if any, so we need to do it afterwards.
            yielded = Nuitka_YieldFromAsyncgenInitial(tstate, asyncgen, value);
            Py_XDECREF(value);
        }

        // If the asyncgen returns with m_yield_from set, it wants us to yield
        // from that value from now on.
        while (yielded == NULL && asyncgen->m_yield_from != NULL) {
            yielded = Nuitka_YieldFromAsyncgenNext(tstate, asyncgen);
        }

        Nuitka_MarkAsyncgenAsNotRunning(asyncgen);

        // Remove the back frame from asyncgen if it's there.
        if (asyncgen->m_frame) {
            // assert(tstate->frame == &asyncgen->m_frame->m_frame);
            assertFrameObject(asyncgen->m_frame);

            Py_CLEAR(asyncgen->m_frame->m_frame.f_back);

            // Remember where to resume from.
            asyncgen->m_resume_frame = _Nuitka_GetThreadStateFrame(tstate);
        }

        // Return back to the frame that called us.
        _Nuitka_GeneratorPopFrame(tstate, return_frame);

#if _DEBUG_ASYNCGEN
        PRINT_ASYNCGEN_STATUS("Returned from coroutine", asyncgen);
        // dumpFrameStack();
#endif

#ifndef __NUITKA_NO_ASSERT__
        if (return_frame) {
            assertThreadFrameObject(return_frame);
        }
#endif

        if (yielded == NULL) {
#if _DEBUG_ASYNCGEN
            PRINT_ASYNCGEN_STATUS("finishing from yield", asyncgen);
            PRINT_CURRENT_EXCEPTION();
            PRINT_STRING("-> finishing asyncgen with exception sets status_Finished\n");
            PRINT_NEW_LINE();
#endif
            Nuitka_MarkAsyncgenAsFinished(asyncgen);

            if (asyncgen->m_frame != NULL) {
                Nuitka_SetFrameGenerator(asyncgen->m_frame, NULL);
                Py_DECREF(asyncgen->m_frame);
                asyncgen->m_frame = NULL;
            }

            Nuitka_Asyncgen_release_closure(asyncgen);

            PyObject *error_occurred = GET_ERROR_OCCURRED(tstate);

            if (error_occurred == PyExc_StopIteration || error_occurred == PyExc_StopAsyncIteration) {
                char const *message;
                if (error_occurred == PyExc_StopIteration) {
                    message = "async generator raised StopIteration";
                } else {
                    message = "async generator raised StopAsyncIteration";
                }

                RAISE_RUNTIME_ERROR_RAISED_STOP_ITERATION(tstate, message);
                return PYGEN_ERROR;
            }

            return PYGEN_ERROR;
        } else {
            // For normal yield, wrap the result value before returning.
            if (asyncgen->m_yield_from == NULL) {
                // Transferred ownership to constructor of Nuitka_AsyncgenValueWrapper
                PyObject *wrapped = Nuitka_AsyncgenValueWrapper_New(yielded);
                yielded = wrapped;

                assert(yielded != NULL);
            }

            *result = yielded;
            return PYGEN_NEXT;
        }
    } else {
        Py_XDECREF(value);

        // Release exception if any, we are finished with it and will raise another.
        RELEASE_ERROR_OCCURRED_STATE_X(exception_state);

        return PYGEN_RETURN;
    }
}

static PyObject *_Nuitka_Asyncgen_send(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen, PyObject *value,
                                       bool closing, struct Nuitka_ExceptionPreservationItem *exception_state) {

    PyObject *result;
    PySendResult res = _Nuitka_Asyncgen_sendR(tstate, asyncgen, value, closing, exception_state, &result);

    switch (res) {
    case PYGEN_RETURN:
        SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
        return NULL;
    case PYGEN_NEXT:
        return result;
    case PYGEN_ERROR:
        return NULL;
    default:
        NUITKA_CANNOT_GET_HERE("invalid PYGEN_ result");
    }
}

// Note: Used by compiled frames.
static bool _Nuitka_Asyncgen_close(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
#endif
    CHECK_OBJECT(asyncgen);

    if (asyncgen->m_status == status_Running) {
        struct Nuitka_ExceptionPreservationItem exception_state;
        SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, &exception_state, PyExc_GeneratorExit, NULL, NULL);

        PyObject *result = _Nuitka_Asyncgen_send(tstate, asyncgen, NULL, true, &exception_state);

        if (unlikely(result)) {
            Py_DECREF(result);

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "async generator ignored GeneratorExit");
            return false;
        } else {
            return DROP_ERROR_OCCURRED_GENERATOR_EXIT_OR_STOP_ITERATION(tstate);
        }
    }

    return true;
}

static bool _Nuitka_Generator_check_throw(PyThreadState *tstate,
                                          struct Nuitka_ExceptionPreservationItem *exception_state);

// This function is called when yielding to a asyncgen through "_Nuitka_YieldFromPassExceptionTo"
// and potentially wrapper objects used by generators, or by the throw method itself.
// Note:
//   Exception arguments are passed for ownership and must be released before returning. The
//   value of exception_type will not be NULL, but the actual exception will not necessarily
//   be normalized.
static PyObject *_Nuitka_Asyncgen_throw2(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen,
                                         bool close_on_genexit,
                                         struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT(asyncgen);
    assert(Nuitka_Asyncgen_Check((PyObject *)asyncgen));
    CHECK_EXCEPTION_STATE(exception_state);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
    PRINT_COROUTINE_VALUE("yield_from", asyncgen->m_yield_from);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_NEW_LINE();
#endif

    if (asyncgen->m_yield_from != NULL) {
        // TODO: This check is not done for coroutines, correct?
        if (close_on_genexit) {
            if (EXCEPTION_STATE_MATCH_BOOL_SINGLE(tstate, exception_state, PyExc_GeneratorExit)) {
                // Asynchronous generators need to close the yield_from.
                Nuitka_MarkAsyncgenAsRunning(asyncgen);
                bool res = Nuitka_gen_close_iter(tstate, asyncgen->m_yield_from);
                Nuitka_MarkAsyncgenAsNotRunning(asyncgen);

                if (res == false) {
                    // Release exception, we are done with it now and pick up the new one.
                    RELEASE_ERROR_OCCURRED_STATE(exception_state);
                    FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);
                }

                return _Nuitka_Asyncgen_send(tstate, asyncgen, NULL, false, exception_state);
            }
        }

        PyObject *ret;

#if _DEBUG_ASYNCGEN
        PRINT_ASYNCGEN_STATUS("Passing to yielded from", asyncgen);
        PRINT_COROUTINE_VALUE("m_yield_from", asyncgen->m_yield_from);
        PRINT_NEW_LINE();
#endif

#if NUITKA_UNCOMPILED_THROW_INTEGRATION
        if (PyGen_CheckExact(asyncgen->m_yield_from) || PyCoro_CheckExact(asyncgen->m_yield_from)) {
            PyGenObject *gen = (PyGenObject *)asyncgen->m_yield_from;

            // Transferred exception ownership to "Nuitka_UncompiledGenerator_throw".
            Nuitka_MarkAsyncgenAsRunning(asyncgen);
            ret = Nuitka_UncompiledGenerator_throw(tstate, gen, 1, exception_state);
            Nuitka_MarkAsyncgenAsNotRunning(asyncgen);
        } else
#endif
            if (Nuitka_Generator_Check(asyncgen->m_yield_from)) {
            struct Nuitka_GeneratorObject *gen = ((struct Nuitka_GeneratorObject *)asyncgen->m_yield_from);
            // Transferred exception ownership to "_Nuitka_Generator_throw2".
            Nuitka_MarkAsyncgenAsRunning(asyncgen);
            ret = _Nuitka_Generator_throw2(tstate, gen, exception_state);
            Nuitka_MarkAsyncgenAsNotRunning(asyncgen);
        } else if (Nuitka_Coroutine_Check(asyncgen->m_yield_from)) {
            struct Nuitka_CoroutineObject *coro = ((struct Nuitka_CoroutineObject *)asyncgen->m_yield_from);
            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            Nuitka_MarkAsyncgenAsRunning(asyncgen);
            ret = _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
            Nuitka_MarkAsyncgenAsNotRunning(asyncgen);
        } else if (Nuitka_CoroutineWrapper_Check(asyncgen->m_yield_from)) {
            struct Nuitka_CoroutineObject *coro =
                ((struct Nuitka_CoroutineWrapperObject *)asyncgen->m_yield_from)->m_coroutine;

            // Transferred exception ownership to "_Nuitka_Coroutine_throw2".
            Nuitka_MarkAsyncgenAsRunning(asyncgen);
            ret = _Nuitka_Coroutine_throw2(tstate, coro, true, exception_state);
            Nuitka_MarkAsyncgenAsNotRunning(asyncgen);
        } else if (Nuitka_AsyncgenAsend_Check(asyncgen->m_yield_from)) {
            struct Nuitka_AsyncgenAsendObject *asyncgen_asend =
                ((struct Nuitka_AsyncgenAsendObject *)asyncgen->m_yield_from);

            // Transferred exception ownership to "_Nuitka_AsyncgenAsend_throw2".
            Nuitka_MarkAsyncgenAsRunning(asyncgen);
            ret = _Nuitka_AsyncgenAsend_throw2(tstate, asyncgen_asend, exception_state);
            Nuitka_MarkAsyncgenAsNotRunning(asyncgen);
        } else {
            PyObject *meth = PyObject_GetAttr(asyncgen->m_yield_from, const_str_plain_throw);

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

            Nuitka_MarkAsyncgenAsRunning(asyncgen);
            ret = Nuitka_CallGeneratorThrowMethod(meth, exception_state);
            Nuitka_MarkAsyncgenAsNotRunning(asyncgen);

            Py_DECREF(meth);

            // Release exception, we are done with it now.
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
        }

        if (unlikely(ret == NULL)) {
            PyObject *val;

            if (Nuitka_PyGen_FetchStopIterationValue(tstate, &val)) {
                CHECK_OBJECT(val);

                asyncgen->m_yield_from = NULL;

                // Return value, not to continue with yielding from.
                if (asyncgen->m_yield_from != NULL) {
                    CHECK_OBJECT(asyncgen->m_yield_from);
#if _DEBUG_ASYNCGEN
                    PRINT_ASYNCGEN_STATUS("Yield from removal:", asyncgen);
                    PRINT_COROUTINE_VALUE("yield_from", asyncgen->m_yield_from);
#endif
                    Py_DECREF(asyncgen->m_yield_from);
                    asyncgen->m_yield_from = NULL;
                }

#if _DEBUG_ASYNCGEN
                PRINT_ASYNCGEN_STATUS("Sending return value into ourselves", asyncgen);
                PRINT_COROUTINE_VALUE("value", val);
                PRINT_NEW_LINE();
#endif

                struct Nuitka_ExceptionPreservationItem no_exception_state;
                INIT_ERROR_OCCURRED_STATE(&no_exception_state);

                ret = _Nuitka_Asyncgen_send(tstate, asyncgen, val, false, &no_exception_state);
            } else {
#if _DEBUG_ASYNCGEN
                PRINT_ASYNCGEN_STATUS("Sending exception value into ourselves", asyncgen);
                PRINT_COROUTINE_VALUE("yield_from", asyncgen->m_yield_from);
                PRINT_CURRENT_EXCEPTION();
                PRINT_NEW_LINE();
#endif

                struct Nuitka_ExceptionPreservationItem no_exception_state;
                INIT_ERROR_OCCURRED_STATE(&no_exception_state);

                ret = _Nuitka_Asyncgen_send(tstate, asyncgen, NULL, false, &no_exception_state);
            }

#if _DEBUG_ASYNCGEN
            PRINT_ASYNCGEN_STATUS("Leave with value/exception from sending into ourselves:", asyncgen);
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        } else {
#if _DEBUG_ASYNCGEN
            PRINT_ASYNCGEN_STATUS("Leave with return value:", asyncgen);
            PRINT_COROUTINE_VALUE("return_value", ret);
            PRINT_CURRENT_EXCEPTION();
            PRINT_NEW_LINE();
#endif
        }

        return ret;
    }

throw_here:
    // We continue to have exception ownership here.
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Need to throw into itself", asyncgen);
#endif

    if (unlikely(_Nuitka_Generator_check_throw(tstate, exception_state) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw already.
        return NULL;
    }

    PyObject *result;

    if (asyncgen->m_status == status_Running) {
        result = _Nuitka_Asyncgen_send(tstate, asyncgen, NULL, false, exception_state);
    } else if (asyncgen->m_status == status_Finished) {
        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);
        result = NULL;
    } else {
        PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(exception_state);

        if (exception_tb == NULL) {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame =
                MAKE_FUNCTION_FRAME(tstate, asyncgen->m_code_object, asyncgen->m_module, 0);
            SET_EXCEPTION_STATE_TRACEBACK(exception_state,
                                          MAKE_TRACEBACK(frame, asyncgen->m_code_object->co_firstlineno));
            Py_DECREF(frame);
        }

        RESTORE_ERROR_OCCURRED_STATE(tstate, exception_state);

#if _DEBUG_ASYNCGEN
        PRINT_ASYNCGEN_STATUS("Finishing from exception", asyncgen);
        PRINT_NEW_LINE();
#endif

        Nuitka_MarkAsyncgenAsFinished(asyncgen);

        result = NULL;
    }

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Leave", asyncgen);
    PRINT_COROUTINE_VALUE("yield_from", asyncgen->m_yield_from);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_Asyncgen_throw(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_DEEP(args);

    PyObject *exception_type;
    PyObject *exception_value = NULL;
    PyTracebackObject *exception_tb = NULL;

    // This takes no references, that is for us to do.
    int res = PyArg_UnpackTuple(args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb);

    if (unlikely(res == 0)) {
        return NULL;
    }

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_NEW_LINE();
#endif

    // Handing ownership of exception over, we need not release it ourselves
    struct Nuitka_ExceptionPreservationItem exception_state;
    if (_Nuitka_Generator_make_throw_exception_state(tstate, &exception_state, exception_type, exception_value,
                                                     exception_tb) == false) {
        return NULL;
    }

    PyObject *result = _Nuitka_Asyncgen_throw2(tstate, asyncgen, false, &exception_state);

    if (result == NULL) {
        if (HAS_ERROR_OCCURRED(tstate) == false) {
            SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
        }
    }

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Leave", asyncgen);
    PRINT_COROUTINE_VALUE("return value", result);
    PRINT_CURRENT_EXCEPTION();
#endif

    CHECK_EXCEPTION_STATE(&exception_state);

    return result;
}

static int _Nuitka_Asyncgen_init_hooks(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
    /* Just do this once per async generator object. */
    if (asyncgen->m_hooks_init_done) {
        return 0;
    }
    asyncgen->m_hooks_init_done = 1;

    /* Attach the finalizer if any. */
    PyObject *finalizer = tstate->async_gen_finalizer;
    if (finalizer != NULL) {
        Py_INCREF(finalizer);
        asyncgen->m_finalizer = finalizer;
    }

    /* Call the "firstiter" hook for async generator. */
    PyObject *firstiter = tstate->async_gen_firstiter;
    if (firstiter != NULL) {
        Py_INCREF(firstiter);

        PyObject *res = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, firstiter, (PyObject *)asyncgen);

        Py_DECREF(firstiter);

        if (unlikely(res == NULL)) {
            return 1;
        }

        Py_DECREF(res);
    }

    return 0;
}

static PyObject *Nuitka_AsyncgenAsend_New(struct Nuitka_AsyncgenObject *asyncgen, PyObject *sendval);
static PyObject *Nuitka_AsyncgenAthrow_New(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args);

static PyObject *Nuitka_Asyncgen_anext(struct Nuitka_AsyncgenObject *asyncgen) {
    CHECK_OBJECT(asyncgen);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
    PRINT_NEW_LINE();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    if (_Nuitka_Asyncgen_init_hooks(tstate, asyncgen)) {
        return NULL;
    }

    PyObject *result = Nuitka_AsyncgenAsend_New(asyncgen, Py_None);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Leave", asyncgen);
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_Asyncgen_asend(struct Nuitka_AsyncgenObject *asyncgen, PyObject *value) {
    CHECK_OBJECT(asyncgen);

    PyThreadState *tstate = PyThreadState_GET();

    if (_Nuitka_Asyncgen_init_hooks(tstate, asyncgen)) {
        return NULL;
    }

    return Nuitka_AsyncgenAsend_New(asyncgen, value);
}

static PyObject *Nuitka_Asyncgen_aclose(struct Nuitka_AsyncgenObject *asyncgen) {
    CHECK_OBJECT(asyncgen);

    PyThreadState *tstate = PyThreadState_GET();

    if (_Nuitka_Asyncgen_init_hooks(tstate, asyncgen)) {
        return NULL;
    }

    return Nuitka_AsyncgenAthrow_New(asyncgen, NULL);
}

static PyObject *Nuitka_Asyncgen_athrow(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    CHECK_OBJECT(asyncgen);

    PyThreadState *tstate = PyThreadState_GET();

    if (_Nuitka_Asyncgen_init_hooks(tstate, asyncgen)) {
        return NULL;
    }

    return Nuitka_AsyncgenAthrow_New(asyncgen, args);
}

#if PYTHON_VERSION >= 0x3a0
static PySendResult _Nuitka_Asyncgen_am_send(struct Nuitka_AsyncgenObject *asyncgen, PyObject *arg, PyObject **result) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Enter", asyncgen);
#endif

    *result = NULL;
    Py_INCREF(arg);

    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    PySendResult res = _Nuitka_Asyncgen_sendR(tstate, asyncgen, arg, false, &exception_state, result);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGEN_STATUS("Leave", asyncgen);
    PRINT_COROUTINE_VALUE("result", *result);
    PRINT_NEW_LINE();
#endif
    return res;
}
#endif

static void Nuitka_Asyncgen_tp_finalize(struct Nuitka_AsyncgenObject *asyncgen) {
    if (asyncgen->m_status != status_Running) {
        return;
    }

    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    bool close_result = _Nuitka_Asyncgen_close(tstate, asyncgen);

    if (unlikely(close_result == false)) {
        PyErr_WriteUnraisable((PyObject *)asyncgen);
    }

    /* Restore the saved exception if any. */
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}

#define MAX_ASYNCGEN_FREE_LIST_COUNT 100
static struct Nuitka_AsyncgenObject *free_list_asyncgens = NULL;
static int free_list_asyncgens_count = 0;

// TODO: This might have to be finalize actually.
static void Nuitka_Asyncgen_tp_dealloc(struct Nuitka_AsyncgenObject *asyncgen) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Asyncgen_Type -= 1;
    count_released_Nuitka_Asyncgen_Type += 1;
#endif

    // Revive temporarily.
    assert(Py_REFCNT(asyncgen) == 0);
    Py_SET_REFCNT(asyncgen, 1);

    PyThreadState *tstate = PyThreadState_GET();

    // Save the current exception, if any, we must preserve it.
    struct Nuitka_ExceptionPreservationItem saved_exception_state;

    PyObject *finalizer = asyncgen->m_finalizer;
    if (finalizer != NULL && asyncgen->m_closed == false) {
        // Save the current exception, if any.
        FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        PyObject *res = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, finalizer, (PyObject *)asyncgen);

        if (unlikely(res == NULL)) {
            PyErr_WriteUnraisable((PyObject *)asyncgen);
        } else {
            Py_DECREF(res);
        }

        RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
        return;
    }

    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    bool close_result = _Nuitka_Asyncgen_close(tstate, asyncgen);

    if (unlikely(close_result == false)) {
        PyErr_WriteUnraisable((PyObject *)asyncgen);
    }

    Nuitka_Asyncgen_release_closure(asyncgen);

    // Allow for above code to resurrect the coroutine, do not release the object
    // like Py_DECREF would.
    Py_SET_REFCNT(asyncgen, Py_REFCNT(asyncgen) - 1);
    if (Py_REFCNT(asyncgen) >= 1) {
        return;
    }

    if (asyncgen->m_frame) {
        Nuitka_SetFrameGenerator(asyncgen->m_frame, NULL);
        Py_DECREF(asyncgen->m_frame);
        asyncgen->m_frame = NULL;
    }

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack(asyncgen);

    Py_XDECREF(asyncgen->m_finalizer);

    if (asyncgen->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)asyncgen);
        assert(!HAS_ERROR_OCCURRED(tstate));
    }

    Py_DECREF(asyncgen->m_name);
    Py_DECREF(asyncgen->m_qualname);

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_asyncgens, asyncgen, MAX_ASYNCGEN_FREE_LIST_COUNT);

    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}

static PyObject *Nuitka_Asyncgen_tp_repr(struct Nuitka_AsyncgenObject *asyncgen) {
    CHECK_OBJECT(asyncgen);

    return PyUnicode_FromFormat("<compiled_async_generator object %s at %p>",
                                Nuitka_String_AsString(asyncgen->m_qualname), asyncgen);
}

static int Nuitka_Asyncgen_tp_traverse(struct Nuitka_AsyncgenObject *asyncgen, visitproc visit, void *arg) {
    CHECK_OBJECT(asyncgen);

    Py_VISIT(asyncgen->m_yield_from);

    for (Py_ssize_t i = 0; i < asyncgen->m_closure_given; i++) {
        Py_VISIT(asyncgen->m_closure[i]);
    }

    Py_VISIT(asyncgen->m_frame);

    Py_VISIT(asyncgen->m_finalizer);

    return 0;
}

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyMethodDef Nuitka_Asyncgen_methods[] = {{"asend", (PyCFunction)Nuitka_Asyncgen_asend, METH_O, NULL},
                                                {"athrow", (PyCFunction)Nuitka_Asyncgen_athrow, METH_VARARGS, NULL},
                                                {"aclose", (PyCFunction)Nuitka_Asyncgen_aclose, METH_NOARGS, NULL},
                                                {NULL}};

static PyAsyncMethods Nuitka_Asyncgen_as_async = {
    0,                               // am_await
    0,                               // am_aiter (PyObject_SelfIter)
    (unaryfunc)Nuitka_Asyncgen_anext // am_anext
#if PYTHON_VERSION >= 0x3a0
    ,
    (sendfunc)_Nuitka_Asyncgen_am_send // am_send
#endif
};

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyGetSetDef Nuitka_Asyncgen_tp_getset[] = {
    {(char *)"__name__", Nuitka_Asyncgen_get_name, Nuitka_Asyncgen_set_name, NULL},
    {(char *)"__qualname__", Nuitka_Asyncgen_get_qualname, Nuitka_Asyncgen_set_qualname, NULL},
    {(char *)"ag_await", Nuitka_Asyncgen_get_ag_await, NULL, NULL},
    {(char *)"ag_code", Nuitka_Asyncgen_get_code, Nuitka_Asyncgen_set_code, NULL},
    {(char *)"ag_frame", Nuitka_Asyncgen_get_frame, Nuitka_Asyncgen_set_frame, NULL},

    {NULL}};

static PyMemberDef Nuitka_Asyncgen_members[] = {
    {(char *)"ag_running", T_BOOL, offsetof(struct Nuitka_AsyncgenObject, m_running), READONLY},
#if PYTHON_VERSION >= 0x380
    {(char *)"ag_running", T_BOOL, offsetof(struct Nuitka_AsyncgenObject, m_running_async), READONLY},
#endif
    {NULL}};

PyTypeObject Nuitka_Asyncgen_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator",          // tp_name
    sizeof(struct Nuitka_AsyncgenObject),                               // tp_basicsize
    sizeof(struct Nuitka_CellObject *),                                 // tp_itemsize
    (destructor)Nuitka_Asyncgen_tp_dealloc,                             // tp_dealloc
    0,                                                                  // tp_print
    0,                                                                  // tp_getattr
    0,                                                                  // tp_setattr
    &Nuitka_Asyncgen_as_async,                                          // tp_as_async
    (reprfunc)Nuitka_Asyncgen_tp_repr,                                  // tp_repr
    0,                                                                  // tp_as_number
    0,                                                                  // tp_as_sequence
    0,                                                                  // tp_as_mapping
    (hashfunc)Nuitka_Asyncgen_tp_hash,                                  // tp_hash
    0,                                                                  // tp_call
    0,                                                                  // tp_str
    0,                                                                  // tp_getattro (PyObject_GenericGetAttr)
    0,                                                                  // tp_setattro
    0,                                                                  // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE, // tp_flags
    0,                                                                  // tp_doc
    (traverseproc)Nuitka_Asyncgen_tp_traverse,                          // tp_traverse
    0,                                                                  // tp_clear
    0,                                                                  // tp_richcompare
    offsetof(struct Nuitka_AsyncgenObject, m_weakrefs),                 // tp_weaklistoffset
    0,                                                                  // tp_iter
    0,                                                                  // tp_iternext
    Nuitka_Asyncgen_methods,                                            // tp_methods
    Nuitka_Asyncgen_members,                                            // tp_members
    Nuitka_Asyncgen_tp_getset,                                          // tp_getset
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
    (destructor)Nuitka_Asyncgen_tp_finalize,                            // tp_finalize

};

PyObject *Nuitka_Asyncgen_New(asyncgen_code code, PyObject *module, PyObject *name, PyObject *qualname,
                              PyCodeObject *code_object, struct Nuitka_CellObject **closure, Py_ssize_t closure_given,
                              Py_ssize_t heap_storage_size) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Asyncgen_Type += 1;
    count_allocated_Nuitka_Asyncgen_Type += 1;
#endif

    struct Nuitka_AsyncgenObject *result;

    // TODO: Change the var part of the type to 1 maybe
    Py_ssize_t full_size = closure_given + (heap_storage_size + sizeof(void *) - 1) / sizeof(void *);

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_asyncgens, struct Nuitka_AsyncgenObject, Nuitka_Asyncgen_Type, full_size);

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
    result->m_running = false;
    result->m_awaiting = false;
#if PYTHON_VERSION >= 0x380
    result->m_running_async = false;
#endif

    result->m_yield_return_index = 0;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    result->m_resume_frame = NULL;

    result->m_finalizer = NULL;
    result->m_hooks_init_done = false;
    result->m_closed = false;

#if PYTHON_VERSION >= 0x370
    result->m_exc_state = Nuitka_ExceptionStackItem_Empty;
#endif

    static long Nuitka_Asyncgen_counter = 0;
    result->m_counter = Nuitka_Asyncgen_counter++;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

struct Nuitka_AsyncgenWrappedValueObject {
    /* Python object folklore: */
    PyObject_HEAD

        PyObject *m_value;
};

static struct Nuitka_AsyncgenWrappedValueObject *free_list_asyncgen_value_wrappers = NULL;
static int free_list_asyncgen_value_wrappers_count = 0;

static void Nuitka_AsyncgenValueWrapper_tp_dealloc(struct Nuitka_AsyncgenWrappedValueObject *asyncgen_value_wrapper) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AsyncgenValueWrapper_Type -= 1;
    count_released_Nuitka_AsyncgenValueWrapper_Type += 1;
#endif

    Nuitka_GC_UnTrack((PyObject *)asyncgen_value_wrapper);

    CHECK_OBJECT(asyncgen_value_wrapper->m_value);
    Py_DECREF(asyncgen_value_wrapper->m_value);

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_asyncgen_value_wrappers, asyncgen_value_wrapper, MAX_ASYNCGEN_FREE_LIST_COUNT);
}

static int Nuitka_AsyncgenValueWrapper_tp_traverse(struct Nuitka_AsyncgenWrappedValueObject *asyncgen_value_wrapper,
                                                   visitproc visit, void *arg) {
    CHECK_OBJECT(asyncgen_value_wrapper);

    Py_VISIT(asyncgen_value_wrapper->m_value);

    return 0;
}

static PyTypeObject Nuitka_AsyncgenValueWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator_wrapped_value", // tp_name
    sizeof(struct Nuitka_AsyncgenWrappedValueObject),                        // tp_basicsize
    0,                                                                       // tp_itemsize
    (destructor)Nuitka_AsyncgenValueWrapper_tp_dealloc,                      // tp_dealloc
    0,                                                                       // tp_print
    0,                                                                       // tp_getattr
    0,                                                                       // tp_setattr
    0,                                                                       // tp_as_async
    0,                                                                       // tp_repr
    0,                                                                       // tp_as_number
    0,                                                                       // tp_as_sequence
    0,                                                                       // tp_as_mapping
    0,                                                                       // tp_hash
    0,                                                                       // tp_call
    0,                                                                       // tp_str
    0,                                                                       // tp_getattro (PyObject_GenericGetAttr)
    0,                                                                       // tp_setattro
    0,                                                                       // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE,      // tp_flags
    0,                                                                       // tp_doc
    (traverseproc)Nuitka_AsyncgenValueWrapper_tp_traverse,                   // tp_traverse
    0,                                                                       // tp_clear
    0,                                                                       // tp_richcompare
    0,                                                                       // tp_weaklistoffset
    0,                                                                       // tp_iter
    0,                                                                       // tp_iternext
    0,                                                                       // tp_methods
    0,                                                                       // tp_members
    0,                                                                       // tp_getset
    0,                                                                       // tp_base
    0,                                                                       // tp_dict
    0,                                                                       // tp_descr_get
    0,                                                                       // tp_descr_set
    0,                                                                       // tp_dictoffset
    0,                                                                       // tp_init
    0,                                                                       // tp_alloc
    0,                                                                       // tp_new
};

// Note: This expects a reference given in value, because that is the
// only way we use it.
static PyObject *Nuitka_AsyncgenValueWrapper_New(PyObject *value) {
    CHECK_OBJECT(value);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AsyncgenValueWrapper_Type += 1;
#endif

    struct Nuitka_AsyncgenWrappedValueObject *result;

    allocateFromFreeListFixed(free_list_asyncgen_value_wrappers, struct Nuitka_AsyncgenWrappedValueObject,
                              Nuitka_AsyncgenValueWrapper_Type);

    result->m_value = value;

    Nuitka_GC_Track(result);

    return (PyObject *)result;
}

#define Nuitka_AsyncgenWrappedValue_CheckExact(o) (Py_TYPE(o) == &Nuitka_AsyncgenValueWrapper_Type)

typedef enum {
    AWAITABLE_STATE_INIT = 0,   /* Has not yet been iterated. */
    AWAITABLE_STATE_ITER = 1,   /* Being iterated currently. */
    AWAITABLE_STATE_CLOSED = 2, /* Closed, no more. */
} AwaitableState;

struct Nuitka_AsyncgenAsendObject {
    /* Python object folklore: */
    PyObject_HEAD

        struct Nuitka_AsyncgenObject *m_gen;
    PyObject *m_sendval;

    AwaitableState m_state;
};

#if _DEBUG_ASYNCGEN

NUITKA_MAY_BE_UNUSED static void _PRINT_ASYNCGENASEND_STATUS(char const *descriptor, char const *context,
                                                             struct Nuitka_AsyncgenAsendObject *asyncgen_asend) {
    char const *status;

    switch (asyncgen_asend->m_state) {
    case AWAITABLE_STATE_INIT:
        status = "(init)";
        break;
    case AWAITABLE_STATE_ITER:
        status = "(iter)";
        break;
    case AWAITABLE_STATE_CLOSED:
        status = "(closed)";
        break;
    default:
        status = "(ILLEGAL)";
        break;
    }

    PRINT_STRING(descriptor);
    PRINT_STRING(" : ");
    PRINT_STRING(context);
    PRINT_STRING(" ");
    PRINT_ITEM((PyObject *)asyncgen_asend);
    PRINT_STRING(" ");
    PRINT_STRING(status);
    PRINT_NEW_LINE();
}

#define PRINT_ASYNCGENASEND_STATUS(context, asyncgen_asend)                                                            \
    _PRINT_ASYNCGENASEND_STATUS(__FUNCTION__, context, asyncgen_asend)

#endif

/**
 * These can be created by byte code loop, and we don't now its internals,
 * yet we have to unwrap ourselves too. These could break in future updates,
 * and ideally we would have checks to cover those.
 */

struct _PyAsyncGenWrappedValue {
    /* Python object folklore: */
    PyObject_HEAD

        PyObject *agw_val;
};

#if PYTHON_VERSION < 0x3d0
#define _PyAsyncGenWrappedValue_CheckExact(o) (Py_TYPE(o) == &_PyAsyncGenWrappedValue_Type)
#else
static PyTypeObject *Nuitka_PyAsyncGenWrappedValue_Type = NULL;

#define _PyAsyncGenWrappedValue_CheckExact(o) (Py_TYPE(o) == Nuitka_PyAsyncGenWrappedValue_Type)
#endif

static PyObject *_Nuitka_Asyncgen_unwrap_value(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen,
                                               PyObject *result) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_X(result);

    if (result == NULL) {
        PyObject *error = GET_ERROR_OCCURRED(tstate);

        if (error == NULL) {
            SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
            asyncgen->m_closed = true;
        } else if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_StopAsyncIteration) ||
                   EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_GeneratorExit)) {
            asyncgen->m_closed = true;
        }

#if PYTHON_VERSION >= 0x380
        asyncgen->m_running_async = false;
#endif
        return NULL;
    }

    if (_PyAsyncGenWrappedValue_CheckExact(result)) {
        /* async yield */
        Nuitka_SetStopIterationValue(tstate, ((struct _PyAsyncGenWrappedValue *)result)->agw_val);

        Py_DECREF(result);

#if PYTHON_VERSION >= 0x380
        asyncgen->m_running_async = false;
#endif
        return NULL;
    } else if (Nuitka_AsyncgenWrappedValue_CheckExact(result)) {
        /* async yield */
        Nuitka_SetStopIterationValue(tstate, ((struct Nuitka_AsyncgenWrappedValueObject *)result)->m_value);

        Py_DECREF(result);

#if PYTHON_VERSION >= 0x380
        asyncgen->m_running_async = false;
#endif
        return NULL;
    }

    return result;
}

static struct Nuitka_AsyncgenAsendObject *free_list_asyncgen_asends = NULL;
static int free_list_asyncgen_asends_count = 0;

static void Nuitka_AsyncgenAsend_tp_dealloc(struct Nuitka_AsyncgenAsendObject *asyncgen_asend) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AsyncgenAsend_Type -= 1;
    count_released_Nuitka_AsyncgenAsend_Type += 1;
#endif

    Nuitka_GC_UnTrack(asyncgen_asend);

    CHECK_OBJECT(asyncgen_asend->m_gen);
    Py_DECREF(asyncgen_asend->m_gen);

    CHECK_OBJECT(asyncgen_asend->m_sendval);
    Py_DECREF(asyncgen_asend->m_sendval);

    releaseToFreeList(free_list_asyncgen_asends, asyncgen_asend, MAX_ASYNCGEN_FREE_LIST_COUNT);
}

static int Nuitka_AsyncgenAsend_tp_traverse(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, visitproc visit,
                                            void *arg) {
    CHECK_OBJECT(asyncgen_asend);

    CHECK_OBJECT(asyncgen_asend->m_gen);
    CHECK_OBJECT(asyncgen_asend->m_sendval);

    Py_VISIT(asyncgen_asend->m_gen);
    Py_VISIT(asyncgen_asend->m_sendval);

    return 0;
}

static PyObject *Nuitka_AsyncgenAsend_send(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *arg) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Enter", asyncgen_asend);
    PRINT_COROUTINE_VALUE("arg", arg);
    PRINT_NEW_LINE();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    if (asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED) {
#if PYTHON_VERSION < 0x390
        SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
#else
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot reuse already awaited __anext__()/asend()");
#endif

#if _DEBUG_ASYNCGEN
        PRINT_ASYNCGENASEND_STATUS("Leave", asyncgen_asend);
        PRINT_STRING("Closed -> StopIteration\n");
        PRINT_CURRENT_EXCEPTION();
        PRINT_NEW_LINE();
#endif

        return NULL;
    } else if (asyncgen_asend->m_state == AWAITABLE_STATE_INIT) {
#if PYTHON_VERSION >= 0x380
        if (asyncgen_asend->m_gen->m_running_async) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                            "anext(): asynchronous generator is already running");
            return NULL;
        }
#endif
        if (arg == NULL || arg == Py_None) {
            arg = asyncgen_asend->m_sendval;
        }

        asyncgen_asend->m_state = AWAITABLE_STATE_ITER;

#if _DEBUG_ASYNCGEN
        PRINT_STRING("Init -> begin iteration\n");
        PRINT_COROUTINE_VALUE("computed arg from sendval", arg);
        PRINT_NEW_LINE();
#endif
    }

#if PYTHON_VERSION >= 0x380
    asyncgen_asend->m_gen->m_running_async = true;
#endif

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Deferring to _Nuitka_Asyncgen_send\n");
    PRINT_NEW_LINE();
#endif

    Py_INCREF(arg);

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    PyObject *result = _Nuitka_Asyncgen_send(tstate, asyncgen_asend->m_gen, arg, false, &exception_state);

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Returned from _Nuitka_Asyncgen_send\n");
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_CURRENT_EXCEPTION();
#endif

    result = _Nuitka_Asyncgen_unwrap_value(tstate, asyncgen_asend->m_gen, result);

#if _DEBUG_ASYNCGEN
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    if (result == NULL) {
        asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;
    }

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Leave", asyncgen_asend);
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_AsyncgenAsend_tp_iternext(struct Nuitka_AsyncgenAsendObject *asyncgen_asend) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Enter", asyncgen_asend);
    PRINT_STRING("Deferring to Nuitka_AsyncgenAsend_send(Py_None)\n");
    PRINT_NEW_LINE();
#endif

    PyObject *result = Nuitka_AsyncgenAsend_send(asyncgen_asend, Py_None);

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Leave", asyncgen_asend);
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_AsyncgenAsend_throw(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *args) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Enter", asyncgen_asend);
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: args:");
    PRINT_ITEM(args);
    PRINT_NEW_LINE();
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: On entry: ");
    PRINT_CURRENT_EXCEPTION();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    if (asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED) {
        SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        return NULL;
    }

    PyObject *result = Nuitka_Asyncgen_throw(tstate, asyncgen_asend->m_gen, args);

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: Async throw result:");
    PRINT_ITEM(result);
    PRINT_STRING(" exception: ");
    PRINT_CURRENT_EXCEPTION();
#endif

    result = _Nuitka_Asyncgen_unwrap_value(tstate, asyncgen_asend->m_gen, result);

    if (result == NULL) {
        asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;
    }

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: Leave with result: ");
    PRINT_ITEM(result);
    PRINT_NEW_LINE();
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: Leave with exception: ");
    PRINT_CURRENT_EXCEPTION();
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: Leave with exception: ");
    PRINT_PUBLISHED_EXCEPTION();
    PRINT_NEW_LINE();
#endif
    CHECK_OBJECT_DEEP(args);

    return result;
}

static PyObject *_Nuitka_AsyncgenAsend_throw2(PyThreadState *tstate, struct Nuitka_AsyncgenAsendObject *asyncgen_asend,
                                              struct Nuitka_ExceptionPreservationItem *exception_state) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Enter", asyncgen_asend);
    PRINT_EXCEPTION_STATE(exception_state);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif

    if (asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED) {
        SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        return NULL;
    }

    PyObject *result = _Nuitka_Asyncgen_throw2(tstate, asyncgen_asend->m_gen, false, exception_state);

    // TODO: This might not be all that necessary as this is not directly outside facing,
    // but there were tests failing when this was not the specific value.
    if (result == NULL) {
        if (HAS_ERROR_OCCURRED(tstate) == false) {
            SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
        }
    }

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Got result", asyncgen_asend);
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_CURRENT_EXCEPTION();
#endif

    result = _Nuitka_Asyncgen_unwrap_value(tstate, asyncgen_asend->m_gen, result);

#if _DEBUG_ASYNCGEN
    PRINT_COROUTINE_VALUE("unwrapped", result);
    PRINT_NEW_LINE();
#endif

    if (result == NULL) {
        asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;
    }

#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENASEND_STATUS("Leave", asyncgen_asend);
    PRINT_COROUTINE_VALUE("result", result);
    PRINT_CURRENT_EXCEPTION();
    PRINT_NEW_LINE();
#endif
    return result;
}

static PyObject *Nuitka_AsyncgenAsend_close(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *args) {
    asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;

    Py_INCREF_IMMORTAL(Py_None);
    return Py_None;
}

static PyObject *Nuitka_AsyncgenAsend_tp_repr(struct Nuitka_AsyncgenAsendObject *asyncgen_asend) {
    return PyUnicode_FromFormat("<compiled_async_generator_asend of %s at %p>",
                                Nuitka_String_AsString(asyncgen_asend->m_gen->m_qualname), asyncgen_asend);
}

static PyMethodDef Nuitka_AsyncgenAsend_methods[] = {
    {"send", (PyCFunction)Nuitka_AsyncgenAsend_send, METH_O, NULL},
    {"throw", (PyCFunction)Nuitka_AsyncgenAsend_throw, METH_VARARGS, NULL},
    {"close", (PyCFunction)Nuitka_AsyncgenAsend_close, METH_NOARGS, NULL},
    {NULL}};

static PyAsyncMethods Nuitka_AsyncgenAsend_as_async = {
    0, // am_await (PyObject_SelfIter)
    0, // am_aiter
    0  // am_anext
};

static PyTypeObject Nuitka_AsyncgenAsend_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator_asend", // tp_name
    sizeof(struct Nuitka_AsyncgenAsendObject),                       // tp_basicsize
    0,                                                               // tp_itemsize
    (destructor)Nuitka_AsyncgenAsend_tp_dealloc,                     // tp_dealloc
    0,                                                               // tp_print
    0,                                                               // tp_getattr
    0,                                                               // tp_setattr
    &Nuitka_AsyncgenAsend_as_async,                                  // tp_as_async
    (reprfunc)Nuitka_AsyncgenAsend_tp_repr,                          // tp_repr
    0,                                                               // tp_as_number
    0,                                                               // tp_as_sequence
    0,                                                               // tp_as_mapping
    0,                                                               // tp_hash
    0,                                                               // tp_call
    0,                                                               // tp_str
    0,                                                               // tp_getattro (PyObject_GenericGetAttr)
    0,                                                               // tp_setattro
    0,                                                               // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                         // tp_flags
    0,                                                               // tp_doc
    (traverseproc)Nuitka_AsyncgenAsend_tp_traverse,                  // tp_traverse
    0,                                                               // tp_clear
    0,                                                               // tp_richcompare
    0,                                                               // tp_weaklistoffset
    0,                                                               // tp_iter (PyObject_SelfIter)
    (iternextfunc)Nuitka_AsyncgenAsend_tp_iternext,                  // tp_iternext
    Nuitka_AsyncgenAsend_methods,                                    // tp_methods
    0,                                                               // tp_members
    0,                                                               // tp_getset
    0,                                                               // tp_base
    0,                                                               // tp_dict
    0,                                                               // tp_descr_get
    0,                                                               // tp_descr_set
    0,                                                               // tp_dictoffset
    0,                                                               // tp_init
    0,                                                               // tp_alloc
    0,                                                               // tp_new
};

static bool Nuitka_AsyncgenAsend_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_AsyncgenAsend_Type; }

static PyObject *Nuitka_AsyncgenAsend_New(struct Nuitka_AsyncgenObject *asyncgen, PyObject *send_value) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT(send_value);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AsyncgenAsend_Type += 1;
    count_allocated_Nuitka_AsyncgenAsend_Type += 1;
#endif

    struct Nuitka_AsyncgenAsendObject *result;

    allocateFromFreeListFixed(free_list_asyncgen_asends, struct Nuitka_AsyncgenAsendObject, Nuitka_AsyncgenAsend_Type);

    Py_INCREF(asyncgen);
    result->m_gen = asyncgen;

    Py_INCREF(send_value);
    result->m_sendval = send_value;

    result->m_state = AWAITABLE_STATE_INIT;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

struct Nuitka_AsyncgenAthrowObject {
    /* Python object folklore: */
    PyObject_HEAD

        // The asyncgen we are working for.
        struct Nuitka_AsyncgenObject *m_gen;
    // Arguments, NULL in case of close, otherwise throw arguments.
    PyObject *m_args;

    AwaitableState m_state;
};

#if _DEBUG_ASYNCGEN

NUITKA_MAY_BE_UNUSED static void _PRINT_ASYNCGENATHROW_STATUS(char const *descriptor, char const *context,
                                                              struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow) {
    char const *status;

    switch (asyncgen_athrow->m_state) {
    case AWAITABLE_STATE_INIT:
        status = "(init)";
        break;
    case AWAITABLE_STATE_ITER:
        status = "(iter)";
        break;
    case AWAITABLE_STATE_CLOSED:
        status = "(closed)";
        break;
    default:
        status = "(ILLEGAL)";
        break;
    }

    PRINT_STRING(descriptor);
    PRINT_STRING(" : ");
    PRINT_STRING(context);
    PRINT_STRING(" ");
    PRINT_ITEM((PyObject *)asyncgen_athrow);
    PRINT_STRING(" ");
    PRINT_STRING(status);
    PRINT_NEW_LINE();
}

#define PRINT_ASYNCGENATHROW_STATUS(context, coroutine)                                                                \
    _PRINT_ASYNCGENATHROW_STATUS(__FUNCTION__, context, asyncgen_athrow)

#endif

static struct Nuitka_AsyncgenAthrowObject *free_list_asyncgen_athrows = NULL;
static int free_list_asyncgen_athrows_count = 0;

static void Nuitka_AsyncgenAthrow_dealloc(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AsyncgenAthrow_Type -= 1;
    count_released_Nuitka_AsyncgenAthrow_Type += 1;
#endif

    Nuitka_GC_UnTrack(asyncgen_athrow);

    CHECK_OBJECT(asyncgen_athrow->m_gen);
    Py_DECREF(asyncgen_athrow->m_gen);

    CHECK_OBJECT_X(asyncgen_athrow->m_args);
    Py_XDECREF(asyncgen_athrow->m_args);

    /* Put the object into free list or release to GC */
    releaseToFreeList(free_list_asyncgen_athrows, asyncgen_athrow, MAX_ASYNCGEN_FREE_LIST_COUNT);
}

static int Nuitka_AsyncgenAthrow_traverse(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, visitproc visit,
                                          void *arg) {
    Py_VISIT(asyncgen_athrow->m_gen);
    Py_VISIT(asyncgen_athrow->m_args);

    return 0;
}

static PyObject *Nuitka_AsyncgenAthrow_send(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *arg) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENATHROW_STATUS("Enter", asyncgen_athrow);
    PRINT_COROUTINE_VALUE("arg", arg);
    PRINT_NEW_LINE();
#endif
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_AsyncgenObject *asyncgen = asyncgen_athrow->m_gen;

    // Closing twice is not allowed with 3.9 or higher.
    if (asyncgen_athrow->m_state == AWAITABLE_STATE_CLOSED) {
#if PYTHON_VERSION < 0x390
        SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
#else
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot reuse already awaited aclose()/athrow()");
#endif

        return NULL;
    }

    // If finished, just report StopIteration.
    if (asyncgen->m_status == status_Finished) {
        SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        return NULL;
    }

    PyObject *retval;

    if (asyncgen_athrow->m_state == AWAITABLE_STATE_INIT) {
#if PYTHON_VERSION >= 0x380
        if (asyncgen_athrow->m_gen->m_running_async) {
            if (asyncgen_athrow->m_args == NULL) {
                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                                "aclose(): asynchronous generator is already running");
            } else {
                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                                "athrow(): asynchronous generator is already running");
            }
            return NULL;
        }
#endif

        // Can also close only once.
        if (asyncgen->m_closed) {
#if PYTHON_VERSION >= 0x380
            asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;
            SET_CURRENT_EXCEPTION_STOP_ASYNC_ITERATION(tstate);
#else
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
#endif
            return NULL;
        }

        // Starting accepts only "None" as input value.
        if (arg != Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                            "can't send non-None value to a just-started coroutine");

            return NULL;
        }

#if PYTHON_VERSION >= 0x380
        asyncgen_athrow->m_gen->m_running_async = true;
#endif
        asyncgen_athrow->m_state = AWAITABLE_STATE_ITER;

        if (asyncgen_athrow->m_args == NULL) {
            asyncgen->m_closed = true;

            struct Nuitka_ExceptionPreservationItem exception_state;
            SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, &exception_state, PyExc_GeneratorExit, NULL, NULL);

            retval = _Nuitka_Asyncgen_throw2(tstate, asyncgen,
                                             1, /* Do not close generator when PyExc_GeneratorExit is passed */
                                             &exception_state);

            if (retval) {
                if (_PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval)) {
#if PYTHON_VERSION >= 0x380
                    asyncgen_athrow->m_gen->m_running_async = false;
#endif

                    Py_DECREF(retval);

                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                                    "async generator ignored GeneratorExit");

                    return NULL;
                }
            }
        } else {
            PyObject *exception_type;
            PyObject *exception_value = NULL;
            PyTracebackObject *exception_tb = NULL;

            if (unlikely(!PyArg_UnpackTuple(asyncgen_athrow->m_args, "athrow", 1, 3, &exception_type, &exception_value,
                                            &exception_tb))) {
                return NULL;
            }

            // Handing ownership of exception over, we need not release it ourselves
            struct Nuitka_ExceptionPreservationItem exception_state;
            if (_Nuitka_Generator_make_throw_exception_state(tstate, &exception_state, exception_type, exception_value,
                                                             exception_tb) == false) {
                return NULL;
            }

            retval = _Nuitka_Asyncgen_throw2(tstate, asyncgen,
                                             0, /* Do not close generator when PyExc_GeneratorExit is passed */
                                             &exception_state);

            retval = _Nuitka_Asyncgen_unwrap_value(tstate, asyncgen, retval);
        }

        if (retval == NULL) {
            goto check_error;
        }

        return retval;
    }

    assert(asyncgen_athrow->m_state == AWAITABLE_STATE_ITER);

    struct Nuitka_ExceptionPreservationItem exception_state;
    INIT_ERROR_OCCURRED_STATE(&exception_state);

    retval = _Nuitka_Asyncgen_send(tstate, asyncgen, arg, false, &exception_state);

    if (asyncgen_athrow->m_args) {
        return _Nuitka_Asyncgen_unwrap_value(tstate, asyncgen, retval);
    } else {
        /* We are here to close if no args. */
        if (retval) {
            if (_PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval)) {
#if PYTHON_VERSION >= 0x380
                asyncgen_athrow->m_gen->m_running_async = false;
#endif
                Py_DECREF(retval);

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "async generator ignored GeneratorExit");

                return NULL;
            }

            return retval;
        }
    }

check_error:
#if PYTHON_VERSION >= 0x380
    asyncgen_athrow->m_gen->m_running_async = false;
#endif

    if (PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
        asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

        if (asyncgen_athrow->m_args == NULL) {
            CLEAR_ERROR_OCCURRED(tstate);
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }
    } else if (PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
        asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

#if PYTHON_VERSION >= 0x380
        if (asyncgen_athrow->m_args == NULL) {
#endif
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
#if PYTHON_VERSION >= 0x380
        }
#endif
    }

    return NULL;
}

static PyObject *Nuitka_AsyncgenAthrow_throw(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *args) {
#if _DEBUG_ASYNCGEN
    PRINT_ASYNCGENATHROW_STATUS("Enter", asyncgen_athrow);
    PRINT_COROUTINE_VALUE("args", args);
    PRINT_NEW_LINE();
#endif

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *retval;

#if PYTHON_VERSION < 0x375
    if (asyncgen_athrow->m_state == AWAITABLE_STATE_INIT) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError,
                                        "can't send non-None value to a just-started coroutine");

        return NULL;
    }
#endif

    if (asyncgen_athrow->m_state == AWAITABLE_STATE_CLOSED) {
#if PYTHON_VERSION < 0x390
        SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
#else
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot reuse already awaited aclose()/athrow()");
#endif

        return NULL;
    }

    retval = Nuitka_Asyncgen_throw(tstate, asyncgen_athrow->m_gen, args);

    if (asyncgen_athrow->m_args) {
        return _Nuitka_Asyncgen_unwrap_value(tstate, asyncgen_athrow->m_gen, retval);
    } else {
        if (retval != NULL) {
            if (_PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval)) {
#if PYTHON_VERSION >= 0x380
                asyncgen_athrow->m_gen->m_running_async = false;
#endif
                Py_DECREF(retval);

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "async generator ignored GeneratorExit");

                return NULL;
            }
        }

#if PYTHON_VERSION >= 0x390
        if (PyErr_ExceptionMatches(PyExc_StopAsyncIteration) || PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
            SET_CURRENT_EXCEPTION_STOP_ITERATION_EMPTY(tstate);
        }
#endif

        return retval;
    }
}

static PyObject *Nuitka_AsyncgenAthrow_tp_iternext(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow) {
    return Nuitka_AsyncgenAthrow_send(asyncgen_athrow, Py_None);
}

static PyObject *Nuitka_AsyncgenAthrow_close(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow) {
    asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

    Py_INCREF_IMMORTAL(Py_None);
    return Py_None;
}

static PyMethodDef Nuitka_AsyncgenAthrow_methods[] = {
    {"send", (PyCFunction)Nuitka_AsyncgenAthrow_send, METH_O, NULL},
    {"throw", (PyCFunction)Nuitka_AsyncgenAthrow_throw, METH_VARARGS, NULL},
    {"close", (PyCFunction)Nuitka_AsyncgenAthrow_close, METH_NOARGS, NULL},
    {NULL}};

static PyAsyncMethods Nuitka_AsyncgenAthrow_as_async = {
    0, // am_await (PyObject_SelfIter)
    0, // am_aiter
    0  // am_anext
};

static PyTypeObject Nuitka_AsyncgenAthrow_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator_athrow", // tp_name
    sizeof(struct Nuitka_AsyncgenAthrowObject),                       // tp_basicsize
    0,                                                                // tp_itemsize
    (destructor)Nuitka_AsyncgenAthrow_dealloc,                        // tp_dealloc
    0,                                                                // tp_print
    0,                                                                // tp_getattr
    0,                                                                // tp_setattr
    &Nuitka_AsyncgenAthrow_as_async,                                  // tp_as_async
    0,                                                                // tp_repr
    0,                                                                // tp_as_number
    0,                                                                // tp_as_sequence
    0,                                                                // tp_as_mapping
    0,                                                                // tp_hash
    0,                                                                // tp_call
    0,                                                                // tp_str
    0,                                                                // tp_getattro (PyObject_GenericGetAttr)
    0,                                                                // tp_setattro
    0,                                                                // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                          // tp_flags
    0,                                                                // tp_doc
    (traverseproc)Nuitka_AsyncgenAthrow_traverse,                     // tp_traverse
    0,                                                                // tp_clear
    0,                                                                // tp_richcompare
    0,                                                                // tp_weaklistoffset
    0,                                                                // tp_iter (PyObject_SelfIter)
    (iternextfunc)Nuitka_AsyncgenAthrow_tp_iternext,                  // tp_iternext
    Nuitka_AsyncgenAthrow_methods,                                    // tp_methods
    0,                                                                // tp_members
    0,                                                                // tp_getset
    0,                                                                // tp_base
    0,                                                                // tp_dict
    0,                                                                // tp_descr_get
    0,                                                                // tp_descr_set
    0,                                                                // tp_dictoffset
    0,                                                                // tp_init
    0,                                                                // tp_alloc
    0,                                                                // tp_new
    0,                                                                // tp_free
    0,                                                                // tp_is_gc
    0,                                                                // tp_bases
    0,                                                                // tp_mro
    0,                                                                // tp_cache
    0,                                                                // tp_subclasses
    0,                                                                // tp_weaklist
    0,                                                                // tp_del
    0,                                                                // tp_version_tag
    0,                                                                // tp_finalize
};

static PyObject *Nuitka_AsyncgenAthrow_New(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_X(args);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_AsyncgenAthrow_Type += 1;
    count_allocated_Nuitka_AsyncgenAthrow_Type += 1;
#endif

    struct Nuitka_AsyncgenAthrowObject *result;

    allocateFromFreeListFixed(free_list_asyncgen_athrows, struct Nuitka_AsyncgenAthrowObject,
                              Nuitka_AsyncgenAthrow_Type);

    Py_INCREF(asyncgen);
    result->m_gen = asyncgen;

    Py_XINCREF(args);
    result->m_args = args;

    result->m_state = AWAITABLE_STATE_INIT;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

static void _initCompiledAsyncgenTypes(void) {

    Nuitka_PyType_Ready(&Nuitka_Asyncgen_Type, &PyAsyncGen_Type, true, false, false, false, true);

    // Be a paranoid subtype of uncompiled function, we want nothing shared.
    assert(Nuitka_Asyncgen_Type.tp_doc != PyAsyncGen_Type.tp_doc || PyAsyncGen_Type.tp_doc == NULL);
    assert(Nuitka_Asyncgen_Type.tp_traverse != PyAsyncGen_Type.tp_traverse);
    assert(Nuitka_Asyncgen_Type.tp_clear != PyAsyncGen_Type.tp_clear || PyAsyncGen_Type.tp_clear == NULL);
    assert(Nuitka_Asyncgen_Type.tp_richcompare != PyAsyncGen_Type.tp_richcompare ||
           PyAsyncGen_Type.tp_richcompare == NULL);
    assert(Nuitka_Asyncgen_Type.tp_weaklistoffset != PyAsyncGen_Type.tp_weaklistoffset);
    assert(Nuitka_Asyncgen_Type.tp_iter != PyAsyncGen_Type.tp_iter || PyAsyncGen_Type.tp_iter == NULL);
    assert(Nuitka_Asyncgen_Type.tp_iternext != PyAsyncGen_Type.tp_iternext || PyAsyncGen_Type.tp_iternext == NULL);
    assert(Nuitka_Asyncgen_Type.tp_as_async != PyAsyncGen_Type.tp_as_async || PyAsyncGen_Type.tp_as_async == NULL);
    assert(Nuitka_Asyncgen_Type.tp_methods != PyAsyncGen_Type.tp_methods);
    assert(Nuitka_Asyncgen_Type.tp_members != PyAsyncGen_Type.tp_members);
    assert(Nuitka_Asyncgen_Type.tp_getset != PyAsyncGen_Type.tp_getset);
    assert(Nuitka_Asyncgen_Type.tp_base != PyAsyncGen_Type.tp_base);
    assert(Nuitka_Asyncgen_Type.tp_dict != PyAsyncGen_Type.tp_dict);
    assert(Nuitka_Asyncgen_Type.tp_descr_get != PyAsyncGen_Type.tp_descr_get || PyAsyncGen_Type.tp_descr_get == NULL);

    assert(Nuitka_Asyncgen_Type.tp_descr_set != PyAsyncGen_Type.tp_descr_set || PyAsyncGen_Type.tp_descr_set == NULL);
    assert(Nuitka_Asyncgen_Type.tp_dictoffset != PyAsyncGen_Type.tp_dictoffset || PyAsyncGen_Type.tp_dictoffset == 0);
    // TODO: These get changed and into the same thing, not sure what to compare against, project something
    // assert(Nuitka_Asyncgen_Type.tp_init != PyAsyncGen_Type.tp_init || PyAsyncGen_Type.tp_init == NULL);
    // assert(Nuitka_Asyncgen_Type.tp_alloc != PyAsyncGen_Type.tp_alloc || PyAsyncGen_Type.tp_alloc == NULL);
    // assert(Nuitka_Asyncgen_Type.tp_new != PyAsyncGen_Type.tp_new || PyAsyncGen_Type.tp_new == NULL);
    // assert(Nuitka_Asyncgen_Type.tp_free != PyAsyncGen_Type.tp_free || PyAsyncGen_Type.tp_free == NULL);
    assert(Nuitka_Asyncgen_Type.tp_bases != PyAsyncGen_Type.tp_bases);
    assert(Nuitka_Asyncgen_Type.tp_mro != PyAsyncGen_Type.tp_mro);
    assert(Nuitka_Asyncgen_Type.tp_cache != PyAsyncGen_Type.tp_cache || PyAsyncGen_Type.tp_cache == NULL);
    assert(Nuitka_Asyncgen_Type.tp_subclasses != PyAsyncGen_Type.tp_subclasses || PyAsyncGen_Type.tp_cache == NULL);
    assert(Nuitka_Asyncgen_Type.tp_weaklist != PyAsyncGen_Type.tp_weaklist);
    assert(Nuitka_Asyncgen_Type.tp_del != PyAsyncGen_Type.tp_del || PyAsyncGen_Type.tp_del == NULL);
    assert(Nuitka_Asyncgen_Type.tp_finalize != PyAsyncGen_Type.tp_finalize || PyAsyncGen_Type.tp_finalize == NULL);

    Nuitka_PyType_Ready(&Nuitka_AsyncgenAsend_Type, NULL, true, false, true, true, false);
    Nuitka_PyType_Ready(&Nuitka_AsyncgenAthrow_Type, NULL, true, false, true, true, false);
    Nuitka_PyType_Ready(&Nuitka_AsyncgenValueWrapper_Type, NULL, false, false, false, false, false);

#if PYTHON_VERSION >= 0x3d0
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *asyncgen_wrapper_object = _PyIntrinsics_UnaryFunctions[INTRINSIC_ASYNC_GEN_WRAP].func(tstate, Py_None);
    Nuitka_PyAsyncGenWrappedValue_Type = Py_TYPE(asyncgen_wrapper_object);
    Py_DECREF(asyncgen_wrapper_object);
#endif
}

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
