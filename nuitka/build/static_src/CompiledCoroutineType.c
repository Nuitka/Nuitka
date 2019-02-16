//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
//
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
//
/** Compiled Coroutines.
 *
 * Unlike in CPython, we have one type for just coroutines, this doesn't do generators
 * nor asyncgen.
 *
 * It strives to be full replacement for normal coroutines.
 *
 */

#include "nuitka/prelude.h"

#include "nuitka/freelists.h"

static PyObject *Nuitka_Coroutine_get_name(struct Nuitka_CoroutineObject *coroutine) {
    Py_INCREF(coroutine->m_name);
    return coroutine->m_name;
}

static int Nuitka_Coroutine_set_name(struct Nuitka_CoroutineObject *coroutine, PyObject *value) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyErr_Format(PyExc_TypeError, "__name__ must be set to a string object");

        return -1;
    }

    PyObject *tmp = coroutine->m_name;
    Py_INCREF(value);
    coroutine->m_name = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Coroutine_get_qualname(struct Nuitka_CoroutineObject *coroutine) {
    Py_INCREF(coroutine->m_qualname);
    return coroutine->m_qualname;
}

static int Nuitka_Coroutine_set_qualname(struct Nuitka_CoroutineObject *coroutine, PyObject *value) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyErr_Format(PyExc_TypeError, "__qualname__ must be set to a string object");

        return -1;
    }

    PyObject *tmp = coroutine->m_qualname;
    Py_INCREF(value);
    coroutine->m_qualname = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Coroutine_get_cr_await(struct Nuitka_CoroutineObject *coroutine) {
    if (coroutine->m_yieldfrom) {
        Py_INCREF(coroutine->m_yieldfrom);
        return coroutine->m_yieldfrom;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

static PyObject *Nuitka_Coroutine_get_code(struct Nuitka_CoroutineObject *coroutine) {
    Py_INCREF(coroutine->m_code_object);
    return (PyObject *)coroutine->m_code_object;
}

static int Nuitka_Coroutine_set_code(struct Nuitka_CoroutineObject *coroutine, PyObject *value) {
    PyErr_Format(PyExc_RuntimeError, "cr_code is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Coroutine_get_frame(struct Nuitka_CoroutineObject *coroutine) {
    if (coroutine->m_frame) {
        Py_INCREF(coroutine->m_frame);
        return (PyObject *)coroutine->m_frame;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

static int Nuitka_Coroutine_set_frame(struct Nuitka_CoroutineObject *coroutine, PyObject *value) {
    PyErr_Format(PyExc_RuntimeError, "gi_frame is not writable in Nuitka");
    return -1;
}

static void Nuitka_Coroutine_release_closure(struct Nuitka_CoroutineObject *coroutine) {
    for (Py_ssize_t i = 0; i < coroutine->m_closure_given; i++) {
        CHECK_OBJECT(coroutine->m_closure[i]);
        Py_DECREF(coroutine->m_closure[i]);
    }

    coroutine->m_closure_given = 0;
}

extern PyObject *Nuitka_UncompiledGenerator_throw(PyGenObject *gen, int close_on_genexit, PyObject *typ, PyObject *val,
                                                  PyObject *tb);

extern PyObject *ERROR_GET_STOP_ITERATION_VALUE();

extern PyObject *PyGen_Send(PyGenObject *gen, PyObject *arg);

extern PyObject *const_str_plain_send, *const_str_plain_throw, *const_str_plain_close;

extern PyObject *_Nuitka_YieldFromPassExceptionTo(PyObject *value, PyObject *exception_type, PyObject *exception_value,
                                                  PyTracebackObject *exception_tb);

PyObject *_Nuitka_YieldFromCore(PyObject *yieldfrom, PyObject *send_value, PyObject **returned_value) {
    // Send iteration value to the sub-generator, which may be a CPython
    // generator object, something with an iterator next, or a send method,
    // where the later is only required if values other than "None" need to
    // be passed in.
    CHECK_OBJECT(yieldfrom);
    assert(send_value != NULL || ERROR_OCCURRED());

    PyObject *retval;

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;
    FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);

    // Exception, was thrown into us, need to send that to sub-generator.
    if (exception_type) {
        retval = _Nuitka_YieldFromPassExceptionTo(yieldfrom, exception_type, exception_value, exception_tb);

        if (unlikely(send_value == NULL)) {
            PyObject *error = GET_ERROR_OCCURRED();

            if (error != NULL && EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_StopIteration)) {
                *returned_value = ERROR_GET_STOP_ITERATION_VALUE();

                assert(!ERROR_OCCURRED());
                return NULL;
            }
        }
    } else if (PyGen_CheckExact(yieldfrom) || PyCoro_CheckExact(yieldfrom)) {
        retval = PyGen_Send((PyGenObject *)yieldfrom, Py_None);
    } else if (send_value == Py_None && Py_TYPE(yieldfrom)->tp_iternext != NULL) {
        retval = Py_TYPE(yieldfrom)->tp_iternext(yieldfrom);
    } else {
        retval = PyObject_CallMethodObjArgs(yieldfrom, const_str_plain_send, send_value, NULL);
    }

    // Check the sub-generator result
    if (retval == NULL) {
        PyObject *error = GET_ERROR_OCCURRED();

        if (error == NULL) {
            Py_INCREF(Py_None);
            *returned_value = Py_None;
        } else if (likely(EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_StopIteration))) {
            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            *returned_value = ERROR_GET_STOP_ITERATION_VALUE();
            assert(*returned_value != NULL);
            assert(!ERROR_OCCURRED());
        } else {
            *returned_value = NULL;
        }

        return NULL;
    } else {
        assert(!ERROR_OCCURRED());
        return retval;
    }
}

static PyObject *Nuitka_YieldFromCoroutineCore(struct Nuitka_CoroutineObject *coroutine, PyObject *send_value) {
    PyObject *yieldfrom = coroutine->m_yieldfrom;
    assert(yieldfrom);

    // Need to make it unaccessible while using it.
    coroutine->m_yieldfrom = NULL;

    PyObject *returned_value;
    PyObject *yielded = _Nuitka_YieldFromCore(yieldfrom, send_value, &returned_value);

    if (yielded == NULL) {
        Py_DECREF(yieldfrom);

        yielded = ((coroutine_code)coroutine->m_code)(coroutine, returned_value);
    } else {
        coroutine->m_yieldfrom = yieldfrom;
    }

    return yielded;
}

static PyObject *Nuitka_YieldFromCoroutineInitial(struct Nuitka_CoroutineObject *coroutine) {
    return Nuitka_YieldFromCoroutineCore(coroutine, Py_None);
}

static PyObject *Nuitka_YieldFromCoroutineNext(struct Nuitka_CoroutineObject *coroutine, PyObject *send_value) {
    return Nuitka_YieldFromCoroutineCore(coroutine, send_value);
}

extern void Nuitka_SetStopIterationValue(PyObject *value);

static PyObject *_Nuitka_Coroutine_send(struct Nuitka_CoroutineObject *coroutine, PyObject *value, bool closing,
                                        PyObject *exception_type, PyObject *exception_value,
                                        PyTracebackObject *exception_tb) {
#if _DEBUG_COROUTINE
    PRINT_STRING("_Nuitka_Coroutine_send: ");
    if (coroutine->m_status == status_Finished)
        PRINT_STRING("(finished) ");
    if (coroutine->m_status == status_Running)
        PRINT_STRING("(running) ");
    if (coroutine->m_status == status_Unused)
        PRINT_STRING("(unused) ");
    PRINT_STRING(closing ? "(closing) " : "(not closing) ");
    PRINT_ITEM((PyObject *)coroutine);
    PRINT_NEW_LINE();
    PRINT_STRING("_Nuitka_Coroutine_send: value ");
    PRINT_ITEM(value);
    PRINT_NEW_LINE();
#endif

    if (coroutine->m_status == status_Unused && value != NULL && value != Py_None) {
        PyErr_Format(PyExc_TypeError, "can't send non-None value to a just-started coroutine");
        return NULL;
    }

    if (coroutine->m_status != status_Finished) {
        PyThreadState *thread_state = PyThreadState_GET();

        if (coroutine->m_running) {
            PyErr_Format(PyExc_ValueError, "coroutine already executing");
            return NULL;
        }

        if (coroutine->m_status == status_Unused) {
            coroutine->m_status = status_Running;
        }

        // Put the coroutine back on the frame stack.
        PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
        if (return_frame) {
            assertFrameObject((struct Nuitka_FrameObject *)return_frame);
        }
#endif

        if (coroutine->m_resume_frame) {
            // It would be nice if our frame were still alive. Nobody had the
            // right to release it.
            assertFrameObject(coroutine->m_resume_frame);

            // It's not supposed to be on the top right now.
            assert(return_frame != &coroutine->m_resume_frame->m_frame);

            thread_state->frame = &coroutine->m_resume_frame->m_frame;
            coroutine->m_resume_frame = NULL;
        }

        // Continue the yielder function while preventing recursion.
        coroutine->m_running = true;

        // Check for thrown exception.
        if (unlikely(exception_type)) {
            assert(value == NULL);

            RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
        }

        if (coroutine->m_frame) {
            Nuitka_Frame_MarkAsExecuting(coroutine->m_frame);
        }

        PyObject *yielded;

        if (coroutine->m_yieldfrom == NULL) {
            yielded = ((coroutine_code)coroutine->m_code)(coroutine, value);
        } else {
            yielded = Nuitka_YieldFromCoroutineNext(coroutine, value);
        }

        // If the coroutine returns with m_yieldfrom set, it wants us to yield
        // from that value from now on.
        while (yielded == NULL && coroutine->m_yieldfrom != NULL) {
            yielded = Nuitka_YieldFromCoroutineInitial(coroutine);
        }

        if (coroutine->m_frame) {
            Nuitka_Frame_MarkAsNotExecuting(coroutine->m_frame);
        }

        coroutine->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the back frame from coroutine if it's there.
        if (coroutine->m_frame) {
            assertFrameObject(coroutine->m_frame);

            Py_CLEAR(coroutine->m_frame->m_frame.f_back);

            // Remember where to resume from.
            coroutine->m_resume_frame = (struct Nuitka_FrameObject *)thread_state->frame;
        }

        thread_state->frame = return_frame;

#ifndef __NUITKA_NO_ASSERT__
        if (return_frame) {
            assertFrameObject((struct Nuitka_FrameObject *)return_frame);
        }
#endif

        if (yielded == NULL) {
            coroutine->m_status = status_Finished;

            if (coroutine->m_frame != NULL) {
                coroutine->m_frame->m_frame.f_gen = NULL;
                Py_DECREF(coroutine->m_frame);
                coroutine->m_frame = NULL;
            }

            Nuitka_Coroutine_release_closure(coroutine);

            // Create StopIteration if necessary, i.e. return value that is not "None" was
            // given. TODO: Push this further down the user line, we might be able to avoid
            // it for some uses, e.g. quick iteration entirely.
            if (coroutine->m_returned) {
                Nuitka_SetStopIterationValue(coroutine->m_returned);

                Py_DECREF(coroutine->m_returned);
                coroutine->m_returned = NULL;
            } else {
                PyObject *error = GET_ERROR_OCCURRED();

                if (error == NULL) {
                    PyErr_SetObject(PyExc_StopIteration, Py_None);
                } else if (error == PyExc_StopIteration) {
                    PyObject *saved_exception_type, *saved_exception_value;
                    PyTracebackObject *saved_exception_tb;

                    FETCH_ERROR_OCCURRED(&saved_exception_type, &saved_exception_value, &saved_exception_tb);
                    NORMALIZE_EXCEPTION(&saved_exception_type, &saved_exception_value, &saved_exception_tb);

                    PyErr_Format(PyExc_RuntimeError, "coroutine raised StopIteration");

                    FETCH_ERROR_OCCURRED(&exception_type, &exception_value, &exception_tb);

                    RAISE_EXCEPTION_WITH_CAUSE(&exception_type, &exception_value, &exception_tb, saved_exception_value);

                    CHECK_OBJECT(exception_value);
                    CHECK_OBJECT(saved_exception_value);

                    Py_INCREF(saved_exception_value);
                    PyException_SetContext(exception_value, saved_exception_value);

                    Py_DECREF(saved_exception_type);
                    Py_XDECREF(saved_exception_tb);

                    RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
                }
            }

            assert(ERROR_OCCURRED());

            return NULL;
        } else {
            return yielded;
        }
    } else {
#if PYTHON_VERSION >= 352 || !defined(_NUITKA_FULL_COMPAT)
        /* This check got added in Python 3.5.2 only. It's good to do it, but
         * not fully compatible, therefore guard it.
         */
        if (closing == false) {
#if _DEBUG_COROUTINE
            PRINT_STRING("Finished coroutine sent into, but not for closing it -> RuntimeError\n");
#endif

            PyErr_Format(PyExc_RuntimeError,
#if !defined(_NUITKA_FULL_COMPAT)
                         "cannot reuse already awaited compiled_coroutine"
#else
                         "cannot reuse already awaited coroutine"
#endif
            );
        } else
#endif
        {
            PyErr_SetObject(PyExc_StopIteration, NULL);
        }

        return NULL;
    }
}

static PyObject *Nuitka_Coroutine_send(struct Nuitka_CoroutineObject *coroutine, PyObject *value) {
    PyObject *result = _Nuitka_Coroutine_send(coroutine, value, false, NULL, NULL, NULL);

    // Make sure to not misbehave
    assert(result != NULL || ERROR_OCCURRED());
    return result;
}

PyObject *Nuitka_Coroutine_close(struct Nuitka_CoroutineObject *coroutine, PyObject *args) {
    if (coroutine->m_status == status_Running) {
        Py_INCREF(PyExc_GeneratorExit);

        PyObject *result = _Nuitka_Coroutine_send(coroutine, NULL, true, PyExc_GeneratorExit, NULL, NULL);

        if (unlikely(result)) {
            Py_DECREF(result);

            PyErr_Format(PyExc_RuntimeError, "coroutine ignored GeneratorExit");
            return NULL;
        } else {
            PyObject *error = GET_ERROR_OCCURRED();
            assert(error != NULL);

            if (EXCEPTION_MATCH_GENERATOR(error)) {
                CLEAR_ERROR_OCCURRED();

                Py_INCREF(Py_None);
                return Py_None;
            }

            return NULL;
        }
    }

    Py_INCREF(Py_None);
    return Py_None;
}

extern PyObject *const_str_plain_close;

/* Also used for asyncgen. */
#if PYTHON_VERSION < 360
static
#endif
    bool
    Nuitka_gen_close_iter(PyObject *yieldfrom) {
    PyObject *meth = PyObject_GetAttr(yieldfrom, const_str_plain_close);

    if (unlikely(meth == NULL)) {
        if (unlikely(!PyErr_ExceptionMatches(PyExc_AttributeError))) {
            PyErr_WriteUnraisable(yieldfrom);
        }

        CLEAR_ERROR_OCCURRED();

        return true;
    } else {
        PyObject *retval = CALL_FUNCTION_NO_ARGS(meth);
        Py_DECREF(meth);

        if (unlikely(retval == NULL)) {
            return false;
        }

        Py_DECREF(retval);

        return true;
    }
}

extern PyObject *const_str_plain_throw;

PyObject *_Nuitka_Coroutine_throw2(struct Nuitka_CoroutineObject *coroutine, bool closing, PyObject *exception_type,
                                   PyObject *exception_value, PyTracebackObject *exception_tb) {
    assert(Nuitka_Coroutine_Check((PyObject *)coroutine));

#if _DEBUG_COROUTINE
    PRINT_STRING("_Nuitka_Coroutine_throw2: ");
    if (coroutine->m_status == status_Finished)
        PRINT_STRING("(finished) ");
    if (coroutine->m_status == status_Running)
        PRINT_STRING("(running) ");
    if (coroutine->m_status == status_Unused)
        PRINT_STRING("(unused) ");
    PRINT_STRING(closing ? "(closing) " : "(not closing) ");
    PRINT_ITEM((PyObject *)coroutine);
    PRINT_NEW_LINE();
    PRINT_STRING("_Nuitka_Coroutine_throw2: yielding from: ");
    PRINT_ITEM(coroutine->m_yieldfrom);
    PRINT_NEW_LINE();
#endif

    CHECK_OBJECT(exception_type);

    if (coroutine->m_yieldfrom != NULL) {
        if (PyErr_GivenExceptionMatches(exception_type, PyExc_GeneratorExit)) {
            // Coroutines need to close the yield_from.
            coroutine->m_running = 1;
            bool res = Nuitka_gen_close_iter(coroutine->m_yieldfrom);
            coroutine->m_running = 0;

            if (res == true) {
                Py_INCREF(exception_type);
                Py_XINCREF(exception_value);
                Py_XINCREF(exception_tb);

                return _Nuitka_Coroutine_send(coroutine, NULL, false, exception_type, exception_value, exception_tb);
            }

            goto throw_here;
        }

        PyObject *ret;

        if (PyGen_CheckExact(coroutine->m_yieldfrom) || PyCoro_CheckExact(coroutine->m_yieldfrom)) {
            PyGenObject *gen = (PyGenObject *)coroutine->m_yieldfrom;

            ret = Nuitka_UncompiledGenerator_throw(gen, 1, exception_type, exception_value, (PyObject *)exception_tb);
        } else {
            PyObject *meth = PyObject_GetAttr(coroutine->m_yieldfrom, const_str_plain_throw);
            if (unlikely(meth == NULL)) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    return NULL;
                }

                CLEAR_ERROR_OCCURRED();
                goto throw_here;
            }

            coroutine->m_running = 1;
            CHECK_OBJECT(exception_type);

            ret = PyObject_CallFunctionObjArgs(meth, exception_type, exception_value, exception_tb, NULL);
            coroutine->m_running = 0;

            Py_DECREF(meth);
        }

        if (unlikely(ret == NULL)) {
            PyObject *val;

#if _DEBUG_COROUTINE
            PRINT_STRING("_Nuitka_Coroutine_throw2: Sending exception value into ourselves:");
            if (coroutine->m_status == status_Finished)
                PRINT_STRING("(finished)");
            if (coroutine->m_status == status_Running)
                PRINT_STRING("(running)");
            if (coroutine->m_status == status_Unused)
                PRINT_STRING("(unused)");
            PRINT_ITEM((PyObject *)coroutine);
            PRINT_NEW_LINE();
#endif

            if (_PyGen_FetchStopIterationValue(&val) == 0) {
                ret = _Nuitka_Coroutine_send(coroutine, val, false, NULL, NULL, NULL);

                Py_DECREF(val);
            } else {
                ret = _Nuitka_Coroutine_send(coroutine, NULL, false, NULL, NULL, NULL);
            }
#if _DEBUG_COROUTINE
            PRINT_STRING("_Nuitka_Coroutine_throw2: Returned from send into ourselves:");
            if (coroutine->m_status == status_Finished)
                PRINT_STRING("(finished)");
            if (coroutine->m_status == status_Running)
                PRINT_STRING("(running)");
            if (coroutine->m_status == status_Unused)
                PRINT_STRING("(unused)");
            PRINT_ITEM((PyObject *)coroutine);
            PRINT_NEW_LINE();
#endif
        }

        assert(ret != NULL || ERROR_OCCURRED());
        return ret;
    }

throw_here:

    CHECK_OBJECT(exception_type);

    if ((PyObject *)exception_tb == Py_None) {
        exception_tb = NULL;
    } else if (exception_tb != NULL && !PyTraceBack_Check(exception_tb)) {
        PyErr_Format(PyExc_TypeError, "throw() third argument must be a traceback object");
        return NULL;
    }

    if (PyExceptionClass_Check(exception_type)) {
        Py_INCREF(exception_type);
        Py_XINCREF(exception_value);
        Py_XINCREF(exception_tb);

        NORMALIZE_EXCEPTION(&exception_type, &exception_value, &exception_tb);
    } else if (PyExceptionInstance_Check(exception_type)) {
        if (exception_value != NULL && exception_value != Py_None) {
            PyErr_Format(PyExc_TypeError, "instance exception may not have a separate value");
            return NULL;
        }

        exception_value = exception_type;
        Py_INCREF(exception_value);
        exception_type = PyExceptionInstance_Class(exception_type);
        Py_INCREF(exception_type);
        Py_XINCREF(exception_tb);
    } else {
        PyErr_Format(PyExc_TypeError, "exceptions must be classes or instances deriving from BaseException, not %s",
                     Py_TYPE(exception_type)->tp_name);

        return NULL;
    }

    if ((exception_tb != NULL) && ((PyObject *)exception_tb != Py_None) && (!PyTraceBack_Check(exception_tb))) {
        PyErr_Format(PyExc_TypeError, "throw() third argument must be a traceback object");
        return NULL;
    }

    if (coroutine->m_status == status_Running) {
        PyObject *result =
            _Nuitka_Coroutine_send(coroutine, NULL, false, exception_type, exception_value, exception_tb);
        return result;
    } else if (coroutine->m_status == status_Finished) {
        /* This seems wasteful to do it like this, but it's a corner case. */
        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        /* This check got added in Python 3.5.2 only. It's good to do it, but
         * not fully compatible, therefore guard it.
         */
#if PYTHON_VERSION >= 352 || !defined(_NUITKA_FULL_COMPAT)
        if (closing) {
#if _DEBUG_COROUTINE
            PRINT_STRING("Finished coroutine thrown into -> RuntimeError\n");
            PRINT_ITEM(coroutine->m_qualname);
            PRINT_NEW_LINE();
#endif
            PyErr_Format(PyExc_RuntimeError,
#if !defined(_NUITKA_FULL_COMPAT)
                         "cannot reuse already awaited compiled_coroutine"
#else
                         "cannot reuse already awaited coroutine"
#endif
            );
        }
#endif

        return NULL;
    } else {
        if (exception_tb == NULL) {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame = MAKE_FUNCTION_FRAME(coroutine->m_code_object, coroutine->m_module, 0);

            exception_tb = MAKE_TRACEBACK(frame, coroutine->m_code_object->co_firstlineno);

            Py_DECREF(frame);
        }

        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        coroutine->m_status = status_Finished;

        return NULL;
    }
}

static PyObject *Nuitka_Coroutine_throw(struct Nuitka_CoroutineObject *coroutine, PyObject *args) {
    PyObject *exception_type;
    PyObject *exception_value = NULL;
    PyTracebackObject *exception_tb = NULL;

    // This takes no references, that is for us to do.
    int res = PyArg_UnpackTuple(args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb);

    if (unlikely(res == 0)) {
        return NULL;
    }

#if _DEBUG_COROUTINE
    PRINT_STRING("Nuitka_Coroutine_throw: Enter\n");

    if (exception_type) {
        PRINT_STRING("TYPE:");
        PRINT_ITEM((PyObject *)Py_TYPE(exception_type));
    }
    PRINT_ITEM(exception_type);
    PRINT_STRING("-");
    PRINT_ITEM(exception_value);
    PRINT_STRING("-");
    PRINT_ITEM((PyObject *)exception_tb);
    PRINT_NEW_LINE();
#endif

    PyObject *result = _Nuitka_Coroutine_throw2(coroutine, true, exception_type, exception_value, exception_tb);

#if _DEBUG_COROUTINE
    PRINT_STRING("Nuitka_Coroutine_throw: Leave\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    // Make sure to not misbehave
    assert(result != NULL || ERROR_OCCURRED());
    return result;
}

static void Nuitka_Coroutine_tp_del(struct Nuitka_CoroutineObject *coroutine) {
    if (coroutine->m_status != status_Running) {
        return;
    }

    PyObject *error_type, *error_value;
    PyTracebackObject *error_traceback;

    FETCH_ERROR_OCCURRED(&error_type, &error_value, &error_traceback);

    PyObject *close_result = Nuitka_Coroutine_close(coroutine, NULL);

    if (unlikely(close_result == NULL)) {
        PyErr_WriteUnraisable((PyObject *)coroutine);
    } else {
        Py_DECREF(close_result);
    }

    /* Restore the saved exception if any. */
    RESTORE_ERROR_OCCURRED(error_type, error_value, error_traceback);
}

static PyObject *Nuitka_Coroutine_tp_repr(struct Nuitka_CoroutineObject *coroutine) {
    return PyUnicode_FromFormat("<compiled_coroutine object %s at %p>", Nuitka_String_AsString(coroutine->m_qualname),
                                coroutine);
}

static long Nuitka_Coroutine_tp_traverse(PyObject *coroutine, visitproc visit, void *arg) {
    // TODO: Identify the impact of not visiting owned objects and/or if it
    // could be NULL instead. The "methodobject" visits its self and module. I
    // understand this is probably so that back references of this function to
    // its upper do not make it stay in the memory. A specific test if that
    // works might be needed.
    return 0;
}

static struct Nuitka_CoroutineWrapperObject *free_list_coro_wrappers = NULL;
static int free_list_coro_wrappers_count = 0;

static PyObject *Nuitka_Coroutine_await(struct Nuitka_CoroutineObject *coroutine) {
#if _DEBUG_COROUTINE
    PRINT_STRING("Nuitka_Coroutine_await enter");
    PRINT_NEW_LINE();
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

#define MAX_COROUTINE_FREE_LIST_COUNT 100
static struct Nuitka_CoroutineObject *free_list_coros = NULL;
static int free_list_coros_count = 0;

static void Nuitka_Coroutine_tp_dealloc(struct Nuitka_CoroutineObject *coroutine) {
    // Revive temporarily.
    assert(Py_REFCNT(coroutine) == 0);
    Py_REFCNT(coroutine) = 1;

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

    PyObject *close_result = Nuitka_Coroutine_close(coroutine, NULL);

    if (unlikely(close_result == NULL)) {
        PyErr_WriteUnraisable((PyObject *)coroutine);
    } else {
        Py_DECREF(close_result);
    }

    Nuitka_Coroutine_release_closure(coroutine);

    Py_XDECREF(coroutine->m_frame);

    assert(Py_REFCNT(coroutine) == 1);
    Py_REFCNT(coroutine) = 0;

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack(coroutine);

    if (coroutine->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)coroutine);
        assert(!ERROR_OCCURRED());
    }

    Py_DECREF(coroutine->m_name);
    Py_DECREF(coroutine->m_qualname);

    /* Put the object into freelist or release to GC */
    releaseToFreeList(free_list_coros, coroutine, MAX_COROUTINE_FREE_LIST_COUNT);

    RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
}

#include <structmember.h>

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyMethodDef Nuitka_Coroutine_methods[] = {{"send", (PyCFunction)Nuitka_Coroutine_send, METH_O, NULL},
                                                 {"throw", (PyCFunction)Nuitka_Coroutine_throw, METH_VARARGS, NULL},
                                                 {"close", (PyCFunction)Nuitka_Coroutine_close, METH_NOARGS, NULL},
                                                 {NULL}};

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyGetSetDef Nuitka_Coroutine_getsetlist[] = {
    {(char *)"__name__", (getter)Nuitka_Coroutine_get_name, (setter)Nuitka_Coroutine_set_name, NULL},
    {(char *)"__qualname__", (getter)Nuitka_Coroutine_get_qualname, (setter)Nuitka_Coroutine_set_qualname, NULL},
    {(char *)"cr_await", (getter)Nuitka_Coroutine_get_cr_await, (setter)NULL, NULL},
    {(char *)"cr_code", (getter)Nuitka_Coroutine_get_code, (setter)Nuitka_Coroutine_set_code, NULL},
    {(char *)"cr_frame", (getter)Nuitka_Coroutine_get_frame, (setter)Nuitka_Coroutine_set_frame, NULL},

    {NULL}};

static PyMemberDef Nuitka_Coroutine_members[] = {
    {(char *)"cr_running", T_BOOL, offsetof(struct Nuitka_CoroutineObject, m_running), READONLY},
#if PYTHON_VERSION >= 370
    {(char *)"cr_origin", T_OBJECT, offsetof(struct Nuitka_CoroutineObject, m_origin), READONLY},

#endif
    {NULL}};

static PyAsyncMethods Nuitka_Coroutine_as_async = {
    (unaryfunc)Nuitka_Coroutine_await, /* am_await */
    0,                                 /* am_aiter */
    0                                  /* am_anext */
};

PyTypeObject Nuitka_Coroutine_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_coroutine",                /* tp_name */
    sizeof(struct Nuitka_CoroutineObject),                              /* tp_basicsize */
    sizeof(struct Nuitka_CellObject *),                                 /* tp_itemsize */
    (destructor)Nuitka_Coroutine_tp_dealloc,                            /* tp_dealloc */
    0,                                                                  /* tp_print */
    0,                                                                  /* tp_getattr */
    0,                                                                  /* tp_setattr */
    &Nuitka_Coroutine_as_async,                                         /* tp_as_async */
    (reprfunc)Nuitka_Coroutine_tp_repr,                                 /* tp_repr */
    0,                                                                  /* tp_as_number */
    0,                                                                  /* tp_as_sequence */
    0,                                                                  /* tp_as_mapping */
    0,                                                                  /* tp_hash */
    0,                                                                  /* tp_call */
    0,                                                                  /* tp_str */
    PyObject_GenericGetAttr,                                            /* tp_getattro */
    0,                                                                  /* tp_setattro */
    0,                                                                  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_FINALIZE, /* tp_flags */
    0,                                                                  /* tp_doc */
    (traverseproc)Nuitka_Coroutine_tp_traverse,                         /* tp_traverse */
    0,                                                                  /* tp_clear */
    0,                                                                  /* tp_richcompare */
    offsetof(struct Nuitka_CoroutineObject, m_weakrefs),                /* tp_weaklistoffset */
    0,                                                                  /* tp_iter */
    0,                                                                  /* tp_iternext */
    Nuitka_Coroutine_methods,                                           /* tp_methods */
    Nuitka_Coroutine_members,                                           /* tp_members */
    Nuitka_Coroutine_getsetlist,                                        /* tp_getset */
    0,                                                                  /* tp_base */
    0,                                                                  /* tp_dict */
    0,                                                                  /* tp_descr_get */
    0,                                                                  /* tp_descr_set */
    0,                                                                  /* tp_dictoffset */
    0,                                                                  /* tp_init */
    0,                                                                  /* tp_alloc */
    0,                                                                  /* tp_new */
    0,                                                                  /* tp_free */
    0,                                                                  /* tp_is_gc */
    0,                                                                  /* tp_bases */
    0,                                                                  /* tp_mro */
    0,                                                                  /* tp_cache */
    0,                                                                  /* tp_subclasses */
    0,                                                                  /* tp_weaklist */
    0,                                                                  /* tp_del */
    0,                                                                  /* tp_version_tag */
    (destructor)Nuitka_Coroutine_tp_del,                                /* tp_finalize */
};

static void Nuitka_CoroutineWrapper_tp_dealloc(struct Nuitka_CoroutineWrapperObject *cw) {
    Nuitka_GC_UnTrack((PyObject *)cw);

    Py_DECREF(cw->m_coroutine);
    cw->m_coroutine = NULL;

    releaseToFreeList(free_list_coro_wrappers, cw, MAX_COROUTINE_FREE_LIST_COUNT);
}

static PyObject *Nuitka_CoroutineWrapper_tp_iternext(struct Nuitka_CoroutineWrapperObject *cw) {
    return Nuitka_Coroutine_send(cw->m_coroutine, Py_None);
}

static int Nuitka_CoroutineWrapper_tp_traverse(struct Nuitka_CoroutineWrapperObject *cw, visitproc visit, void *arg) {
    Py_VISIT((PyObject *)cw->m_coroutine);
    return 0;
}

static PyObject *Nuitka_CoroutineWrapper_send(struct Nuitka_CoroutineWrapperObject *cw, PyObject *arg) {
    return Nuitka_Coroutine_send(cw->m_coroutine, arg);
}

static PyObject *Nuitka_CoroutineWrapper_throw(struct Nuitka_CoroutineWrapperObject *cw, PyObject *args) {
    return Nuitka_Coroutine_throw(cw->m_coroutine, args);
}

static PyObject *Nuitka_CoroutineWrapper_close(struct Nuitka_CoroutineWrapperObject *cw, PyObject *args) {
    return Nuitka_Coroutine_close(cw->m_coroutine, args);
}

static PyObject *Nuitka_CoroutineWrapper_tp_repr(struct Nuitka_CoroutineWrapperObject *cw) {
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
    sizeof(struct Nuitka_CoroutineWrapperObject),      /* tp_basicsize */
    0,                                                 /* tp_itemsize */
    (destructor)Nuitka_CoroutineWrapper_tp_dealloc,    /* tp_dealloc */
    0,                                                 /* tp_print */
    0,                                                 /* tp_getattr */
    0,                                                 /* tp_setattr */
    0,                                                 /* tp_as_async */
    (reprfunc)Nuitka_CoroutineWrapper_tp_repr,         /* tp_repr */
    0,                                                 /* tp_as_number */
    0,                                                 /* tp_as_sequence */
    0,                                                 /* tp_as_mapping */
    0,                                                 /* tp_hash */
    0,                                                 /* tp_call */
    0,                                                 /* tp_str */
    PyObject_GenericGetAttr,                           /* tp_getattro */
    0,                                                 /* tp_setattro */
    0,                                                 /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,           /* tp_flags */
    0,                                                 /* tp_doc */
    (traverseproc)Nuitka_CoroutineWrapper_tp_traverse, /* tp_traverse */
    0,                                                 /* tp_clear */
    0,                                                 /* tp_richcompare */
    0,                                                 /* tp_weaklistoffset */
    PyObject_SelfIter,                                 /* tp_iter */
    (iternextfunc)Nuitka_CoroutineWrapper_tp_iternext, /* tp_iternext */
    Nuitka_CoroutineWrapper_methods,                   /* tp_methods */
    0,                                                 /* tp_members */
    0,                                                 /* tp_getset */
    0,                                                 /* tp_base */
    0,                                                 /* tp_dict */
    0,                                                 /* tp_descr_get */
    0,                                                 /* tp_descr_set */
    0,                                                 /* tp_dictoffset */
    0,                                                 /* tp_init */
    0,                                                 /* tp_alloc */
    0,                                                 /* tp_new */
    0,                                                 /* tp_free */
};

#if PYTHON_VERSION >= 370
static PyObject *computeCoroutineOrigin(int origin_depth) {
    PyFrameObject *frame = PyEval_GetFrame();

    int frame_count = 0;

    while (frame != NULL && frame_count < origin_depth) {
        frame = frame->f_back;
        frame_count += 1;
    }

    PyObject *cr_origin = PyTuple_New(frame_count);

    frame = PyEval_GetFrame();

    for (int i = 0; i < frame_count; i++) {
        PyObject *frameinfo =
            Py_BuildValue("OiO", frame->f_code->co_filename, PyFrame_GetLineNumber(frame), frame->f_code->co_name);

        assert(frameinfo);

        PyTuple_SET_ITEM(cr_origin, i, frameinfo);

        frame = frame->f_back;
    }

    return cr_origin;
}
#endif

PyObject *Nuitka_Coroutine_New(coroutine_code code, PyObject *module, PyObject *name, PyObject *qualname,
                               PyCodeObject *code_object, Py_ssize_t closure_given, Py_ssize_t heap_storage_size) {
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

    result->m_yieldfrom = NULL;

    // The m_closure is set from the outside.
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;
    result->m_awaiting = false;

    result->m_exception_type = NULL;
    result->m_exception_value = NULL;
    result->m_exception_tb = NULL;

    result->m_yield_return_index = 0;

    result->m_returned = NULL;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    result->m_resume_frame = NULL;

#if PYTHON_VERSION >= 370
    PyThreadState *tstate = PyThreadState_GET();
    int origin_depth = tstate->coroutine_origin_tracking_depth;

    if (origin_depth == 0) {
        result->m_origin = NULL;
    } else {
        result->m_origin = computeCoroutineOrigin(origin_depth);
    }
#endif

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

extern PyObject *PyGen_Send(PyGenObject *gen, PyObject *arg);
extern PyObject *const_str_plain_send;

static int gen_is_coroutine(PyObject *object) {
    if (PyGen_CheckExact(object)) {
        PyCodeObject *code = (PyCodeObject *)((PyGenObject *)object)->gi_code;

        if (code->co_flags & CO_ITERABLE_COROUTINE) {
            return 1;
        }
    }

    return 0;
}

static PyObject *Nuitka_GetAwaitableIter(PyObject *value) {
#if _DEBUG_COROUTINE
    PRINT_STRING("Nuitka_GetAwaitableIter:");
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

                PyErr_Format(PyExc_TypeError, "__await__() returned a coroutine");

                return NULL;
            }

            if (unlikely(!HAS_ITERNEXT(result))) {
                PyErr_Format(PyExc_TypeError, "__await__() returned non-iterator of type '%s'",
                             Py_TYPE(result)->tp_name);

                Py_DECREF(result);

                return NULL;
            }
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "object %s can't be used in 'await' expression", Py_TYPE(value)->tp_name);

    return NULL;
}

#if PYTHON_VERSION >= 366
static void FORMAT_AWAIT_ERROR(PyObject *value, int await_kind) {
    if (await_kind == await_enter) {
        PyErr_Format(PyExc_TypeError,
                     "'async with' received an object from __aenter__ that does not implement __await__: %s",
                     Py_TYPE(value)->tp_name);
    } else if (await_kind == await_exit) {
        PyErr_Format(PyExc_TypeError,
                     "'async with' received an object from __aexit__ that does not implement __await__: %s",
                     Py_TYPE(value)->tp_name);
    }

    assert(ERROR_OCCURRED());
}
#endif

PyObject *ASYNC_AWAIT(PyObject *awaitable, int await_kind) {
    PyObject *awaitable_iter = Nuitka_GetAwaitableIter(awaitable);

    if (unlikely(awaitable_iter == NULL)) {
#if PYTHON_VERSION >= 366
        FORMAT_AWAIT_ERROR(awaitable, await_kind);
#endif
        return NULL;
    }

#if PYTHON_VERSION >= 366
    if (await_kind != await_normal && Py_TYPE(awaitable_iter) != &Nuitka_CoroutineWrapper_Type) {
        if (unlikely(Py_TYPE(awaitable_iter)->tp_as_async == NULL ||
                     Py_TYPE(awaitable_iter)->tp_as_async->am_await == NULL)) {
            FORMAT_AWAIT_ERROR(awaitable_iter, await_kind);
            return NULL;
        }
    }
#endif

#if PYTHON_VERSION >= 352 || !defined(_NUITKA_FULL_COMPAT)
    /* This check got added in Python 3.5.2 only. It's good to do it, but
     * not fully compatible, therefore guard it.
     */

    if (Nuitka_Coroutine_Check(awaitable)) {
        struct Nuitka_CoroutineObject *awaited_coroutine = (struct Nuitka_CoroutineObject *)awaitable;

        if (awaited_coroutine->m_awaiting) {
            Py_DECREF(awaitable_iter);

            PyErr_Format(PyExc_RuntimeError, "coroutine is being awaited already");

            return NULL;
        }
    }
#endif

    return awaitable_iter;
}

#if PYTHON_VERSION >= 352

/* Our "aiter" wrapper clone */
struct Nuitka_AIterWrapper {
    PyObject_HEAD PyObject *aw_aiter;
};

static PyObject *Nuitka_AIterWrapper_tp_repr(struct Nuitka_AIterWrapper *aw) {
    return PyUnicode_FromFormat("<compiled_aiter_wrapper object of %R at %p>", aw->aw_aiter, aw);
}

static PyObject *Nuitka_AIterWrapper_iternext(struct Nuitka_AIterWrapper *aw) {
#if PYTHON_VERSION < 360
    PyErr_SetObject(PyExc_StopIteration, aw->aw_aiter);
#else
    if (!PyTuple_Check(aw->aw_aiter) && !PyExceptionInstance_Check(aw->aw_aiter)) {
        PyErr_SetObject(PyExc_StopIteration, aw->aw_aiter);
    } else {
        PyObject *result = PyObject_CallFunctionObjArgs(PyExc_StopIteration, aw->aw_aiter, NULL);
        if (unlikely(result == NULL)) {
            return NULL;
        }
        PyErr_SetObject(PyExc_StopIteration, result);
        Py_DECREF(result);
    }
#endif

    return NULL;
}

static int Nuitka_AIterWrapper_traverse(struct Nuitka_AIterWrapper *aw, visitproc visit, void *arg) {
    Py_VISIT((PyObject *)aw->aw_aiter);
    return 0;
}

static struct Nuitka_AIterWrapper *free_list_coroutine_aiter_wrappers = NULL;
static int free_list_coroutine_aiter_wrappers_count = 0;

static void Nuitka_AIterWrapper_dealloc(struct Nuitka_AIterWrapper *aw) {
    Nuitka_GC_UnTrack((PyObject *)aw);

    Py_DECREF(aw->aw_aiter);

    /* Put the object into freelist or release to GC */
    releaseToFreeList(free_list_coroutine_aiter_wrappers, aw, MAX_COROUTINE_FREE_LIST_COUNT);
}

static PyAsyncMethods Nuitka_AIterWrapper_as_async = {
    PyObject_SelfIter, /* am_await */
    0,                 /* am_aiter */
    0                  /* am_anext */
};

PyTypeObject Nuitka_AIterWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_aiter_wrapper",
    sizeof(struct Nuitka_AIterWrapper),      /* tp_basicsize */
    0,                                       /* tp_itemsize */
    (destructor)Nuitka_AIterWrapper_dealloc, /* destructor tp_dealloc */
    0,                                       /* tp_print */
    0,                                       /* tp_getattr */
    0,                                       /* tp_setattr */
    &Nuitka_AIterWrapper_as_async,           /* tp_as_async */
    (reprfunc)Nuitka_AIterWrapper_tp_repr,   /* tp_repr */
    0,                                       /* tp_as_number */
    0,                                       /* tp_as_sequence */
    0,                                       /* tp_as_mapping */
    0,                                       /* tp_hash */
    0,                                       /* tp_call */
    0,                                       /* tp_str */
    PyObject_GenericGetAttr,                 /* tp_getattro */
    0,                                       /* tp_setattro */
    0,                                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, /* tp_flags */
    "A wrapper object for '__aiter__' backwards compatibility.",
    (traverseproc)Nuitka_AIterWrapper_traverse, /* tp_traverse */
    0,                                          /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    PyObject_SelfIter,                          /* tp_iter */
    (iternextfunc)Nuitka_AIterWrapper_iternext, /* tp_iternext */
    0,                                          /* tp_methods */
    0,                                          /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    0,                                          /* tp_descr_get */
    0,                                          /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    0,                                          /* tp_init */
    0,                                          /* tp_alloc */
    0,                                          /* tp_new */
    0,                                          /* tp_free */
};

PyObject *Nuitka_AIterWrapper_New(PyObject *aiter) {
    struct Nuitka_AIterWrapper *result;

    allocateFromFreeListFixed(free_list_coroutine_aiter_wrappers, struct Nuitka_AIterWrapper, Nuitka_AIterWrapper_Type);

    CHECK_OBJECT(aiter);

    Py_INCREF(aiter);
    result->aw_aiter = aiter;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

#endif

PyObject *ASYNC_MAKE_ITERATOR(PyObject *value) {
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

#if PYTHON_VERSION >= 370
    if (unlikely(Py_TYPE(iter)->tp_as_async == NULL || Py_TYPE(iter)->tp_as_async->am_anext == NULL)) {
        PyErr_Format(PyExc_TypeError,
                     "'async for' received an object from __aiter__ that does not implement __anext__: %s",
                     Py_TYPE(iter)->tp_name);

        Py_DECREF(iter);
        return NULL;
    }
#endif

#if PYTHON_VERSION >= 352
    /* Starting with Python 3.5.2 it is acceptable to return an async iterator
     * directly, instead of an awaitable.
     */
    if (Py_TYPE(iter)->tp_as_async != NULL && Py_TYPE(iter)->tp_as_async->am_anext != NULL) {
        PyObject *wrapper = Nuitka_AIterWrapper_New(iter);
        Py_DECREF(iter);

        iter = wrapper;
    }
#endif

    PyObject *awaitable_iter = Nuitka_GetAwaitableIter(iter);

    if (unlikely(awaitable_iter == NULL)) {
#if PYTHON_VERSION >= 360
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

PyObject *ASYNC_ITERATOR_NEXT(PyObject *value) {
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
        PyErr_Format(PyExc_TypeError, "'async for' requires an iterator with __anext__ method, got %s",
                     Py_TYPE(value)->tp_name);

        return NULL;
    }

    PyObject *next_value = (*getter)(value);

    if (unlikely(next_value == NULL)) {
        return NULL;
    }

    PyObject *awaitable_iter = Nuitka_GetAwaitableIter(next_value);

    if (unlikely(awaitable_iter == NULL)) {
#if PYTHON_VERSION >= 360
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

void _initCompiledCoroutineTypes(void) {
    PyType_Ready(&Nuitka_Coroutine_Type);
    PyType_Ready(&Nuitka_CoroutineWrapper_Type);

#if PYTHON_VERSION >= 352
    PyType_Ready(&Nuitka_AIterWrapper_Type);
#endif
}
