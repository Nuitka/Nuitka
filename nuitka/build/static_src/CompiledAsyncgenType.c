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
#include "nuitka/prelude.h"

#include "nuitka/freelists.h"

static PyObject *Nuitka_Asyncgen_get_name(struct Nuitka_AsyncgenObject *asyncgen) {
    Py_INCREF(asyncgen->m_name);
    return asyncgen->m_name;
}

static int Nuitka_Asyncgen_set_name(struct Nuitka_AsyncgenObject *asyncgen, PyObject *value) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyErr_Format(PyExc_TypeError, "__name__ must be set to a string object");

        return -1;
    }

    PyObject *tmp = asyncgen->m_name;
    Py_INCREF(value);
    asyncgen->m_name = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Asyncgen_get_qualname(struct Nuitka_AsyncgenObject *asyncgen) {
    Py_INCREF(asyncgen->m_qualname);
    return asyncgen->m_qualname;
}

static int Nuitka_Asyncgen_set_qualname(struct Nuitka_AsyncgenObject *asyncgen, PyObject *value) {
    // Cannot be deleted, not be non-unicode value.
    if (unlikely((value == NULL) || !PyUnicode_Check(value))) {
        PyErr_Format(PyExc_TypeError, "__qualname__ must be set to a string object");

        return -1;
    }

    PyObject *tmp = asyncgen->m_qualname;
    Py_INCREF(value);
    asyncgen->m_qualname = value;
    Py_DECREF(tmp);

    return 0;
}

static PyObject *Nuitka_Asyncgen_get_ag_await(struct Nuitka_AsyncgenObject *asyncgen) {
    if (asyncgen->m_yieldfrom) {
        Py_INCREF(asyncgen->m_yieldfrom);
        return asyncgen->m_yieldfrom;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

static PyObject *Nuitka_Asyncgen_get_code(struct Nuitka_AsyncgenObject *asyncgen) {
    Py_INCREF(asyncgen->m_code_object);
    return (PyObject *)asyncgen->m_code_object;
}

static int Nuitka_Asyncgen_set_code(struct Nuitka_AsyncgenObject *asyncgen, PyObject *value) {
    PyErr_Format(PyExc_RuntimeError, "ag_code is not writable in Nuitka");
    return -1;
}

static void Nuitka_Asyncgen_release_closure(struct Nuitka_AsyncgenObject *asyncgen) {
    for (Py_ssize_t i = 0; i < asyncgen->m_closure_given; i++) {
        CHECK_OBJECT(asyncgen->m_closure[i]);
        Py_DECREF(asyncgen->m_closure[i]);
    }

    asyncgen->m_closure_given = 0;
}

extern PyObject *ERROR_GET_STOP_ITERATION_VALUE();

extern PyObject *_Nuitka_YieldFromCore(PyObject *yieldfrom, PyObject *send_value, PyObject **returned_value, bool mode);

static PyObject *Nuitka_YieldFromAsyncgenCore(struct Nuitka_AsyncgenObject *asyncgen, PyObject *send_value, bool mode) {
    PyObject *yieldfrom = asyncgen->m_yieldfrom;
    assert(yieldfrom);

    // Need to make it unaccessible while using it.
    asyncgen->m_yieldfrom = NULL;
    PyObject *returned_value;
    PyObject *yielded = _Nuitka_YieldFromCore(yieldfrom, send_value, &returned_value, mode);

    if (yielded == NULL) {
        Py_DECREF(yieldfrom);

        yielded = ((asyncgen_code)asyncgen->m_code)(asyncgen, returned_value);
    } else {
        asyncgen->m_yieldfrom = yieldfrom;
    }

    return yielded;
}

static PyObject *Nuitka_YieldFromAsyncgenInitial(struct Nuitka_AsyncgenObject *asyncgen) {
    return Nuitka_YieldFromAsyncgenCore(asyncgen, Py_None, true);
}

static PyObject *Nuitka_YieldFromAsyncgenNext(struct Nuitka_AsyncgenObject *asyncgen, PyObject *send_value) {
    return Nuitka_YieldFromAsyncgenCore(asyncgen, send_value, false);
}

static PyObject *Nuitka_AsyncGenValueWrapperNew(PyObject *value);

static PyObject *_Nuitka_Asyncgen_send(struct Nuitka_AsyncgenObject *asyncgen, PyObject *value, bool closing,
                                       PyObject *exception_type, PyObject *exception_value,
                                       PyTracebackObject *exception_tb) {
    CHECK_OBJECT(asyncgen);
    CHECK_OBJECT_X(value);
    CHECK_OBJECT_X(exception_type);
    CHECK_OBJECT_X(exception_value);
    CHECK_OBJECT_X(exception_tb);

#if _DEBUG_ASYNCGEN
    PRINT_STRING("_Nuitka_Asyncgen_send: Enter asyncgen:");
    PRINT_ITEM((PyObject *)asyncgen);
    PRINT_NEW_LINE();
    PRINT_STRING("_Nuitka_Asyncgen_send: value:");
    PRINT_ITEM((PyObject *)value);
    PRINT_NEW_LINE();
    PRINT_STRING("_Nuitka_Asyncgen_send: exception:");
    PRINT_EXCEPTION(exception_type, exception_value, (PyObject *)exception_tb);
    PRINT_NEW_LINE();
#endif

    if (asyncgen->m_status == status_Unused && value != NULL && value != Py_None) {
        PyErr_Format(PyExc_TypeError, "can't send non-None value to a just-started async generator");
        return NULL;
    }

    if (asyncgen->m_status != status_Finished) {
        PyThreadState *thread_state = PyThreadState_GET();

        if (asyncgen->m_running) {
            PyErr_Format(PyExc_ValueError, "async generator already executing");
            return NULL;
        }

        if (asyncgen->m_status == status_Unused) {
            asyncgen->m_status = status_Running;
        }

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = thread_state->frame;
#ifndef __NUITKA_NO_ASSERT__
        if (return_frame) {
            assertFrameObject((struct Nuitka_FrameObject *)return_frame);
        }
#endif

        if (asyncgen->m_resume_frame) {
            // It would be nice if our frame were still alive. Nobody had the
            // right to release it.
            assertFrameObject(asyncgen->m_resume_frame);

            // It's not supposed to be on the top right now.
            assert(return_frame != &asyncgen->m_resume_frame->m_frame);

            thread_state->frame = &asyncgen->m_frame->m_frame;
            asyncgen->m_resume_frame = NULL;
        }

        // Continue the yielder function while preventing recursion.
        asyncgen->m_running = true;

        // Check for thrown exception, and publish it.
        if (unlikely(exception_type != NULL)) {
            assert(value == NULL);

            Py_INCREF(exception_type);
            Py_XINCREF(exception_value);
            Py_XINCREF(exception_tb);
            RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
        }

        if (asyncgen->m_frame) {
            Nuitka_Frame_MarkAsExecuting(asyncgen->m_frame);
        }

        PyObject *yielded;

        if (asyncgen->m_yieldfrom == NULL) {
            yielded = ((asyncgen_code)asyncgen->m_code)(asyncgen, value);
        } else {
            yielded = Nuitka_YieldFromAsyncgenNext(asyncgen, value);
        }

        // If the asyncgen returns with m_yieldfrom set, it wants us to yield
        // from that value from now on.
        while (yielded == NULL && asyncgen->m_yieldfrom != NULL) {
            yielded = Nuitka_YieldFromAsyncgenInitial(asyncgen);
        }

        if (asyncgen->m_frame) {
            Nuitka_Frame_MarkAsNotExecuting(asyncgen->m_frame);
        }

        asyncgen->m_running = false;

        thread_state = PyThreadState_GET();

        // Remove the back frame from asyncgen if it's there.
        if (asyncgen->m_frame) {
            assertFrameObject(asyncgen->m_frame);

            Py_CLEAR(asyncgen->m_frame->m_frame.f_back);

            // Remember where to resume from.
            asyncgen->m_resume_frame = (struct Nuitka_FrameObject *)thread_state->frame;
        }

        thread_state->frame = return_frame;

#ifndef __NUITKA_NO_ASSERT__
        if (return_frame) {
            assertFrameObject((struct Nuitka_FrameObject *)return_frame);
        }
#endif

        // Generator return does set this.
        if (yielded == NULL) {
            asyncgen->m_status = status_Finished;

            if (asyncgen->m_frame != NULL) {
                asyncgen->m_frame->m_frame.f_gen = NULL;
                Py_DECREF(asyncgen->m_frame);
                asyncgen->m_frame = NULL;
            }

            Nuitka_Asyncgen_release_closure(asyncgen);

            PyObject *error_occurred = GET_ERROR_OCCURRED();

            if (error_occurred == PyExc_StopIteration || error_occurred == PyExc_StopAsyncIteration) {
                PyObject *saved_exception_type, *saved_exception_value;
                PyTracebackObject *saved_exception_tb;

                FETCH_ERROR_OCCURRED(&saved_exception_type, &saved_exception_value, &saved_exception_tb);
                NORMALIZE_EXCEPTION(&saved_exception_type, &saved_exception_value, &saved_exception_tb);

                if (error_occurred == PyExc_StopIteration) {
                    PyErr_Format(PyExc_RuntimeError, "async generator raised StopIteration");
                } else {
                    PyErr_Format(PyExc_RuntimeError, "async generator raised StopAsyncIteration");
                }

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

            return NULL;
        } else {
            // For normal yield, wrap the result value before returning.
            if (asyncgen->m_yieldfrom == NULL) {
                // TODO: Why not transfer ownership to constructor.
                PyObject *wrapped = Nuitka_AsyncGenValueWrapperNew(yielded);
                Py_DECREF(yielded);

                yielded = wrapped;

                assert(yielded != NULL);
            }

            return yielded;
        }
    } else {
        PyErr_SetObject(PyExc_StopAsyncIteration, NULL);

        return NULL;
    }
}

PyObject *Nuitka_Asyncgen_close(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    if (asyncgen->m_status == status_Running) {
        PyObject *result = _Nuitka_Asyncgen_send(asyncgen, NULL, true, PyExc_GeneratorExit, NULL, NULL);

        if (unlikely(result)) {
            Py_DECREF(result);

            PyErr_Format(PyExc_RuntimeError, "async generator ignored GeneratorExit");
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

/* Shared from coroutines. */
extern bool Nuitka_gen_close_iter(PyObject *yieldfrom);

extern PyObject *const_str_plain_throw;

extern PyObject *Nuitka_UncompiledGenerator_throw(PyGenObject *gen, int close_on_genexit, PyObject *typ, PyObject *val,
                                                  PyObject *tb);

static PyObject *_Nuitka_Asyncgen_throw2(struct Nuitka_AsyncgenObject *asyncgen, bool close_on_genexit,
                                         PyObject *exception_type, PyObject *exception_value,
                                         PyTracebackObject *exception_tb) {
#if _DEBUG_ASYNCGEN
    PRINT_STRING("_Nuitka_Asyncgen_throw2: Enter\n");
#endif

    if (asyncgen->m_yieldfrom != NULL) {
        if (close_on_genexit) {
            if (PyErr_GivenExceptionMatches(exception_type, PyExc_GeneratorExit)) {
                // Asynchronous generators need to close the yield_from.
                asyncgen->m_running = 1;
                bool res = Nuitka_gen_close_iter(asyncgen->m_yieldfrom);
                asyncgen->m_running = 0;

                if (res == true) {
                    return _Nuitka_Asyncgen_send(asyncgen, NULL, false, exception_type, exception_value, exception_tb);
                }

                goto throw_here;
            }
        }

        PyObject *ret;

        if (PyGen_CheckExact(asyncgen->m_yieldfrom) || PyCoro_CheckExact(asyncgen->m_yieldfrom)) {
            PyGenObject *gen = (PyGenObject *)asyncgen->m_yieldfrom;

            ret = Nuitka_UncompiledGenerator_throw(gen, 1, exception_type, exception_value, (PyObject *)exception_tb);
        } else {
            PyObject *meth = PyObject_GetAttr(asyncgen->m_yieldfrom, const_str_plain_throw);
            if (unlikely(meth == NULL)) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    return NULL;
                }
                CLEAR_ERROR_OCCURRED();

                goto throw_here;
            }

            asyncgen->m_running = 1;
            ret = PyObject_CallFunctionObjArgs(meth, exception_type, exception_value, exception_tb, NULL);
            asyncgen->m_running = 0;

            Py_DECREF(meth);
        }

        if (unlikely(ret == NULL)) {
#if _DEBUG_ASYNCGEN
            PRINT_STRING("_Nuitka_Asyncgen_throw2: Extract value from exception\n");
#endif
            PyObject *val;

            if (_PyGen_FetchStopIterationValue(&val) == 0) {
                CHECK_OBJECT(val);

#if _DEBUG_ASYNCGEN
                PRINT_STRING("_Nuitka_Asyncgen_throw2: Value to send is");
                PRINT_ITEM(val);
                PRINT_NEW_LINE();
#endif
                ret = _Nuitka_Asyncgen_send(asyncgen, val, false, NULL, NULL, NULL);
                Py_DECREF(val);
            } else {
#if _DEBUG_ASYNCGEN
                PRINT_STRING("_Nuitka_Asyncgen_throw2: No value to send\n");
#endif
                ret = _Nuitka_Asyncgen_send(asyncgen, NULL, false, exception_type, exception_value, exception_tb);
            }
        }

#if _DEBUG_ASYNCGEN
        PRINT_STRING("_Nuitka_Asyncgen_throw2: Yieldfrom path taken\n");
#endif

        return ret;
    }

#if _DEBUG_ASYNCGEN
    PRINT_STRING("_Nuitka_Asyncgen_throw2: Throwing for real.");
#endif
throw_here:

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

    if (asyncgen->m_status == status_Running) {
        PyObject *result = _Nuitka_Asyncgen_send(asyncgen, NULL, false, exception_type, exception_value, exception_tb);
        return result;
    } else if (asyncgen->m_status == status_Finished) {
        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
        return NULL;
    } else {
        if (exception_tb == NULL) {
            // TODO: Our compiled objects really need a way to store common
            // stuff in a "shared" part across all instances, and outside of
            // run time, so we could reuse this.
            struct Nuitka_FrameObject *frame = MAKE_FUNCTION_FRAME(asyncgen->m_code_object, asyncgen->m_module, 0);

            exception_tb = MAKE_TRACEBACK(frame, asyncgen->m_code_object->co_firstlineno);

            Py_DECREF(frame);
        }

        RESTORE_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

        asyncgen->m_status = status_Finished;

        return NULL;
    }
}

static PyObject *Nuitka_Asyncgen_throw(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    PyObject *exception_type;
    PyObject *exception_value = NULL;
    PyTracebackObject *exception_tb = NULL;

    // This takes no references, that is for us to do.
    int res = PyArg_UnpackTuple(args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb);

    if (unlikely(res == 0)) {
        return NULL;
    }

    return _Nuitka_Asyncgen_throw2(asyncgen, true, exception_type, exception_value, exception_tb);
}

static int Nuitka_Asyncgen_init_hooks(struct Nuitka_AsyncgenObject *asyncgen) {
    /* Just do this once per async generator object. */
    if (asyncgen->m_hooks_init_done) {
        return 0;
    }
    asyncgen->m_hooks_init_done = 1;

    PyThreadState *tstate = PyThreadState_GET();

    /* Attach the finalizer if any. */
    PyObject *finalizer = tstate->async_gen_finalizer;
    if (finalizer) {
        Py_INCREF(finalizer);
        asyncgen->m_finalizer = finalizer;
    }

    /* Call the "firstiter" hook for async generator. */
    PyObject *firstiter = tstate->async_gen_firstiter;
    if (firstiter) {
        Py_INCREF(firstiter);

        PyObject *res = CALL_FUNCTION_WITH_SINGLE_ARG(firstiter, (PyObject *)asyncgen);

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
    if (Nuitka_Asyncgen_init_hooks(asyncgen)) {
        return NULL;
    }

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_Asyncgen_anext: Making Nuitka_AsyncgenAsend object.");
    PRINT_NEW_LINE();
#endif

    return Nuitka_AsyncgenAsend_New(asyncgen, Py_None);
}

static PyObject *Nuitka_Asyncgen_asend(struct Nuitka_AsyncgenObject *asyncgen, PyObject *value) {
    if (Nuitka_Asyncgen_init_hooks(asyncgen)) {
        return NULL;
    }

    return Nuitka_AsyncgenAsend_New(asyncgen, value);
}

static PyObject *Nuitka_Asyncgen_aclose(struct Nuitka_AsyncgenObject *asyncgen, PyObject *arg) {
    if (Nuitka_Asyncgen_init_hooks(asyncgen)) {
        return NULL;
    }

    return Nuitka_AsyncgenAthrow_New(asyncgen, NULL);
}

static PyObject *Nuitka_Asyncgen_athrow(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    if (Nuitka_Asyncgen_init_hooks(asyncgen)) {
        return NULL;
    }

    return Nuitka_AsyncgenAthrow_New(asyncgen, args);
}

#define MAX_ASYNCGEN_FREE_LIST_COUNT 100
static struct Nuitka_AsyncgenObject *free_list_asyncgens = NULL;
static int free_list_asyncgens_count = 0;

// TODO: This might have to be finalize actually.
static void Nuitka_Asyncgen_tp_dealloc(struct Nuitka_AsyncgenObject *asyncgen) {
    // Revive temporarily.
    assert(Py_REFCNT(asyncgen) == 0);
    Py_REFCNT(asyncgen) = 1;

    // Save the current exception, if any, we must preserve it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;

    PyObject *finalizer = asyncgen->m_finalizer;
    if (finalizer && asyncgen->m_closed == false) {
        /* Save the current exception, if any. */
        FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

        PyObject *res = CALL_FUNCTION_WITH_SINGLE_ARG(finalizer, (PyObject *)asyncgen);

        if (unlikely(res == NULL)) {
            PyErr_WriteUnraisable((PyObject *)asyncgen);
        } else {
            Py_DECREF(res);
        }

        RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
        return;
    }

    FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);

    PyObject *close_result = Nuitka_Asyncgen_close(asyncgen, NULL);

    if (unlikely(close_result == NULL)) {
        PyErr_WriteUnraisable((PyObject *)asyncgen);
    } else {
        Py_DECREF(close_result);
    }

    Nuitka_Asyncgen_release_closure(asyncgen);

    if (asyncgen->m_frame) {
        asyncgen->m_frame->m_frame.f_gen = NULL;
        Py_DECREF(asyncgen->m_frame);
        asyncgen->m_frame = NULL;
    }

    assert(Py_REFCNT(asyncgen) == 1);
    Py_REFCNT(asyncgen) = 0;

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack(asyncgen);

    Py_XDECREF(asyncgen->m_finalizer);

    if (asyncgen->m_weakrefs != NULL) {
        PyObject_ClearWeakRefs((PyObject *)asyncgen);
        assert(!ERROR_OCCURRED());
    }

    Py_DECREF(asyncgen->m_name);
    Py_DECREF(asyncgen->m_qualname);

    /* Put the object into freelist or release to GC */
    releaseToFreeList(free_list_asyncgens, asyncgen, MAX_ASYNCGEN_FREE_LIST_COUNT);

    RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
}

static PyObject *Nuitka_Asyncgen_tp_repr(struct Nuitka_AsyncgenObject *asyncgen) {
    return PyUnicode_FromFormat("<compiled_async_generator object %s at %p>",
                                Nuitka_String_AsString(asyncgen->m_qualname), asyncgen);
}

static int Nuitka_Asyncgen_tp_traverse(struct Nuitka_AsyncgenObject *asyncgen, visitproc visit, void *arg) {
    Py_VISIT(asyncgen->m_finalizer);

    // TODO: Identify the impact of not visiting owned objects and/or if it
    // could be NULL instead. The "methodobject" visits its self and module. I
    // understand this is probably so that back references of this function to
    // its upper do not make it stay in the memory. A specific test if that
    // works might be needed.
    return 0;
}

#include <structmember.h>

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyMethodDef Nuitka_Asyncgen_methods[] = {{"asend", (PyCFunction)Nuitka_Asyncgen_asend, METH_O, NULL},
                                                {"athrow", (PyCFunction)Nuitka_Asyncgen_athrow, METH_VARARGS, NULL},
                                                {"aclose", (PyCFunction)Nuitka_Asyncgen_aclose, METH_NOARGS, NULL},
                                                {NULL}};

static PyAsyncMethods Nuitka_Asyncgen_as_async = {
    0,                               /* am_await */
    PyObject_SelfIter,               /* am_aiter */
    (unaryfunc)Nuitka_Asyncgen_anext /* am_anext */
};

// TODO: Set "__doc__" automatically for method clones of compiled types from
// the documentation of built-in original type.
static PyGetSetDef Nuitka_Asyncgen_getsetlist[] = {
    {(char *)"__name__", (getter)Nuitka_Asyncgen_get_name, (setter)Nuitka_Asyncgen_set_name, NULL},
    {(char *)"__qualname__", (getter)Nuitka_Asyncgen_get_qualname, (setter)Nuitka_Asyncgen_set_qualname, NULL},
    {(char *)"ag_await", (getter)Nuitka_Asyncgen_get_ag_await, (setter)NULL, NULL},
    {(char *)"ag_code", (getter)Nuitka_Asyncgen_get_code, (setter)Nuitka_Asyncgen_set_code, NULL},

    {NULL}};

static PyMemberDef Nuitka_Asyncgen_members[] = {
    {(char *)"ag_frame", T_OBJECT, offsetof(struct Nuitka_AsyncgenObject, m_frame), READONLY},
    {(char *)"ag_running", T_BOOL, offsetof(struct Nuitka_AsyncgenObject, m_running), READONLY},
    {NULL}};

PyTypeObject Nuitka_Asyncgen_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator",          /* tp_name */
    sizeof(struct Nuitka_AsyncgenObject),                               /* tp_basicsize */
    sizeof(struct Nuitka_CellObject *),                                 /* tp_itemsize */
    (destructor)Nuitka_Asyncgen_tp_dealloc,                             /* tp_dealloc */
    0,                                                                  /* tp_print */
    0,                                                                  /* tp_getattr */
    0,                                                                  /* tp_setattr */
    &Nuitka_Asyncgen_as_async,                                          /* tp_as_async */
    (reprfunc)Nuitka_Asyncgen_tp_repr,                                  /* tp_repr */
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
    (traverseproc)Nuitka_Asyncgen_tp_traverse,                          /* tp_traverse */
    0,                                                                  /* tp_clear */
    0,                                                                  /* tp_richcompare */
    offsetof(struct Nuitka_AsyncgenObject, m_weakrefs),                 /* tp_weaklistoffset */
    0,                                                                  /* tp_iter */
    0,                                                                  /* tp_iternext */
    Nuitka_Asyncgen_methods,                                            /* tp_methods */
    Nuitka_Asyncgen_members,                                            /* tp_members */
    Nuitka_Asyncgen_getsetlist,                                         /* tp_getset */
    0,                                                                  /* tp_base */
    0,                                                                  /* tp_dict */
    0,                                                                  /* tp_descr_get */
    0,                                                                  /* tp_descr_set */
    0,                                                                  /* tp_dictoffset */
    0,                                                                  /* tp_init */
    0,                                                                  /* tp_alloc */
    0,                                                                  /* tp_new */
    0,                                                                  /* tp_free */
};

PyObject *Nuitka_Asyncgen_New(asyncgen_code code, PyObject *module, PyObject *name, PyObject *qualname,
                              PyCodeObject *code_object, Py_ssize_t closure_given, Py_ssize_t heap_storage_size) {
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

    // TODO: Makes no sense with asyncgens maybe?
    result->m_yieldfrom = NULL;

    // The m_closure is set from the outside.
    result->m_closure_given = closure_given;

    result->m_weakrefs = NULL;

    result->m_status = status_Unused;
    result->m_running = false;
    result->m_awaiting = false;

    result->m_yield_return_index = 0;

    result->m_frame = NULL;
    result->m_code_object = code_object;

    result->m_resume_frame = NULL;

    result->m_finalizer = NULL;
    result->m_hooks_init_done = false;
    result->m_closed = false;

#if PYTHON_VERSION >= 370
    result->m_exc_state.exc_type = NULL;
    result->m_exc_state.exc_value = NULL;
    result->m_exc_state.exc_traceback = NULL;
#endif

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

struct Nuitka_AsyncgenWrappedValueObject {
    /* Python object folklore: */
    PyObject_HEAD;

    PyObject *m_value;
};

static struct Nuitka_AsyncgenWrappedValueObject *free_list_asyncgen_value_wrappers = NULL;
static int free_list_asyncgen_value_wrappers_count = 0;

static void asyncgen_value_wrapper_tp_dealloc(struct Nuitka_AsyncgenWrappedValueObject *asyncgen_value_wrapper) {
    Nuitka_GC_UnTrack((PyObject *)asyncgen_value_wrapper);

    Py_DECREF(asyncgen_value_wrapper->m_value);

    releaseToFreeList(free_list_asyncgen_value_wrappers, asyncgen_value_wrapper, MAX_ASYNCGEN_FREE_LIST_COUNT);
}

static int asyncgen_value_wrapper_tp_traverse(struct Nuitka_AsyncgenWrappedValueObject *asyncgen_value_wrapper,
                                              visitproc visit, void *arg) {
    Py_VISIT(asyncgen_value_wrapper->m_value);

    return 0;
}

static PyTypeObject Nuitka_AsyncgenValueWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator_wrapped_value", /* tp_name */
    sizeof(struct Nuitka_AsyncgenWrappedValueObject),                        /* tp_basicsize */
    0,                                                                       /* tp_itemsize */
    (destructor)asyncgen_value_wrapper_tp_dealloc,                           /* tp_dealloc */
    0,                                                                       /* tp_print */
    0,                                                                       /* tp_getattr */
    0,                                                                       /* tp_setattr */
    0,                                                                       /* tp_as_async */
    0,                                                                       /* tp_repr */
    0,                                                                       /* tp_as_number */
    0,                                                                       /* tp_as_sequence */
    0,                                                                       /* tp_as_mapping */
    0,                                                                       /* tp_hash */
    0,                                                                       /* tp_call */
    0,                                                                       /* tp_str */
    PyObject_GenericGetAttr,                                                 /* tp_getattro */
    0,                                                                       /* tp_setattro */
    0,                                                                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                                 /* tp_flags */
    0,                                                                       /* tp_doc */
    (traverseproc)asyncgen_value_wrapper_tp_traverse,                        /* tp_traverse */
    0,                                                                       /* tp_clear */
    0,                                                                       /* tp_richcompare */
    0,                                                                       /* tp_weaklistoffset */
    0,                                                                       /* tp_iter */
    0,                                                                       /* tp_iternext */
    0,                                                                       /* tp_methods */
    0,                                                                       /* tp_members */
    0,                                                                       /* tp_getset */
    0,                                                                       /* tp_base */
    0,                                                                       /* tp_dict */
    0,                                                                       /* tp_descr_get */
    0,                                                                       /* tp_descr_set */
    0,                                                                       /* tp_dictoffset */
    0,                                                                       /* tp_init */
    0,                                                                       /* tp_alloc */
    0,                                                                       /* tp_new */
};

static PyObject *Nuitka_AsyncGenValueWrapperNew(PyObject *value) {
    CHECK_OBJECT(value);
    struct Nuitka_AsyncgenWrappedValueObject *result;

    allocateFromFreeListFixed(free_list_asyncgen_value_wrappers, struct Nuitka_AsyncgenWrappedValueObject,
                              Nuitka_AsyncgenValueWrapper_Type);

    result->m_value = value;

    Py_INCREF(value);

    Nuitka_GC_Track(result);

    return (PyObject *)result;
}

#define Nuitka_AsyncgenWrappedValue_CheckExact(o) (Py_TYPE(o) == &Nuitka_AsyncgenValueWrapper_Type)

// TODO: We could change all generators to use that kind of enum, if
// it's properly supported.
typedef enum {
    AWAITABLE_STATE_INIT = 0,   /* Has not yet been iterated. */
    AWAITABLE_STATE_ITER = 1,   /* Being iterated currently. */
    AWAITABLE_STATE_CLOSED = 2, /* Closed, no more. */
} AwaitableState;

struct Nuitka_AsyncgenAsendObject {
    /* Python object folklore: */
    PyObject_HEAD;

    struct Nuitka_AsyncgenObject *m_gen;
    PyObject *m_sendval;

    AwaitableState m_state;
};

/* For debug outputs only. */
char const *getAwaitableStateStr(AwaitableState state) {
    switch (state) {
    case AWAITABLE_STATE_INIT:
        return "AWAITABLE_STATE_INIT";
    case AWAITABLE_STATE_ITER:
        return "AWAITABLE_STATE_ITER";
    case AWAITABLE_STATE_CLOSED:
        return "AWAITABLE_STATE_CLOSED";
    default:
        return "AWAITABLE_STATE_ILLEGAL";
    }
}

/**
 * These can be created by byte code loop, and we don't now its internals,
 * yet we have to unwrap ourselves too. These could break in future updates,
 * and ideally we would have checks to cover those.
 */
typedef struct {
    /* Python object folklore: */
    PyObject_HEAD;

    PyObject *agw_val;
} _PyAsyncGenWrappedValue;

#define _PyAsyncGenWrappedValue_CheckExact(o) (Py_TYPE(o) == &_PyAsyncGenWrappedValue_Type)

static PyObject *Nuitka_Asyncgen_unwrap_value(struct Nuitka_AsyncgenObject *asyncgen, PyObject *result) {
    if (result == NULL) {
        if (!ERROR_OCCURRED()) {
            PyErr_SetNone(PyExc_StopAsyncIteration);
            asyncgen->m_closed = true;
        } else if (PyErr_ExceptionMatches(PyExc_StopAsyncIteration) || PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
            asyncgen->m_closed = true;
        }

        return NULL;
    }

    if (_PyAsyncGenWrappedValue_CheckExact(result)) {
        /* async yield */
        _PyGen_SetStopIterationValue(((_PyAsyncGenWrappedValue *)result)->agw_val);

        Py_DECREF(result);

        return NULL;
    } else if (Nuitka_AsyncgenWrappedValue_CheckExact(result)) {
        /* async yield */
        _PyGen_SetStopIterationValue(((struct Nuitka_AsyncgenWrappedValueObject *)result)->m_value);

        Py_DECREF(result);

        return NULL;
    }

    return result;
}

static struct Nuitka_AsyncgenAsendObject *free_list_asyncgen_asends = NULL;
static int free_list_asyncgen_asends_count = 0;

static void Nuitka_AsyncgenAsend_tp_dealloc(struct Nuitka_AsyncgenAsendObject *asyncgen_asend) {
    Nuitka_GC_UnTrack(asyncgen_asend);

    Py_DECREF(asyncgen_asend->m_gen);
    Py_DECREF(asyncgen_asend->m_sendval);

    releaseToFreeList(free_list_asyncgen_asends, asyncgen_asend, MAX_ASYNCGEN_FREE_LIST_COUNT);
}

static int Nuitka_AsyncgenAsend_tp_traverse(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, visitproc visit,
                                            void *arg) {
    Py_VISIT(asyncgen_asend->m_gen);
    Py_VISIT(asyncgen_asend->m_sendval);

    return 0;
}

static PyObject *Nuitka_AsyncgenAsend_send(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *arg) {
#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_send: Enter with state:\nasyncgen_asend:");
    PRINT_ITEM((PyObject *)asyncgen_asend);
    PRINT_NEW_LINE();
    PRINT_FORMAT("State on entry is asyncgen_send->m_state = %d (%s)\n", asyncgen_asend->m_state,
                 getAwaitableStateStr(asyncgen_asend->m_state));
    PRINT_STRING("Nuitka_AsyncgenAsend_send: arg:");
    PRINT_ITEM(arg);
    PRINT_NEW_LINE();
#endif

    PyObject *result;

    if (asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    } else if (asyncgen_asend->m_state == AWAITABLE_STATE_INIT) {
        if (arg == NULL || arg == Py_None) {
            arg = asyncgen_asend->m_sendval;
        }

        asyncgen_asend->m_state = AWAITABLE_STATE_ITER;
    }

    result = _Nuitka_Asyncgen_send(asyncgen_asend->m_gen, arg, false, NULL, NULL, NULL);
    result = Nuitka_Asyncgen_unwrap_value(asyncgen_asend->m_gen, result);

    if (result == NULL) {
        asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;
    }

#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_send: Result ");
    PRINT_ITEM(result);
    PRINT_NEW_LINE();
#endif

    return result;
}

static PyObject *Nuitka_AsyncgenAsend_tp_iternext(struct Nuitka_AsyncgenAsendObject *asyncgen_asend) {
#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_tp_iternext: refer to Nuitka_AsyncgenAsend_send");
    PRINT_NEW_LINE();
#endif

    return Nuitka_AsyncgenAsend_send(asyncgen_asend, Py_None);
}

static PyObject *Nuitka_AsyncgenAsend_throw(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *args) {
#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: Enter with state:\nasyncgen_asend:");
    PRINT_ITEM((PyObject *)asyncgen_asend);
    PRINT_NEW_LINE();
    PRINT_FORMAT("State on entry is asyncgen_send->m_state = %d (%s)\n", asyncgen_asend->m_state,
                 getAwaitableStateStr(asyncgen_asend->m_state));
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: args:");
    PRINT_ITEM(args);
    PRINT_NEW_LINE();
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: On entry: ");
    PRINT_CURRENT_EXCEPTION();
#endif

    PyObject *result;

    if (asyncgen_asend->m_state == AWAITABLE_STATE_CLOSED) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    result = Nuitka_Asyncgen_throw(asyncgen_asend->m_gen, args);
#if _DEBUG_ASYNCGEN
    PRINT_STRING("Nuitka_AsyncgenAsend_throw: Async throw result:");
    PRINT_ITEM(result);
    PRINT_STRING(" exception: ");
    PRINT_CURRENT_EXCEPTION();
#endif

    result = Nuitka_Asyncgen_unwrap_value(asyncgen_asend->m_gen, result);

    if (asyncgen_asend == NULL) {
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

    return result;
}

static PyObject *Nuitka_AsyncgenAsend_close(struct Nuitka_AsyncgenAsendObject *asyncgen_asend, PyObject *args) {
    asyncgen_asend->m_state = AWAITABLE_STATE_CLOSED;

    Py_INCREF(Py_None);
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
    PyObject_SelfIter, /* am_await */
    0,                 /* am_aiter */
    0                  /* am_anext */
};

static PyTypeObject Nuitka_AsyncgenAsend_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator_asend", /* tp_name */
    sizeof(struct Nuitka_AsyncgenAsendObject),                       /* tp_basicsize */
    0,                                                               /* tp_itemsize */
    (destructor)Nuitka_AsyncgenAsend_tp_dealloc,                     /* tp_dealloc */
    0,                                                               /* tp_print */
    0,                                                               /* tp_getattr */
    0,                                                               /* tp_setattr */
    &Nuitka_AsyncgenAsend_as_async,                                  /* tp_as_async */
    (reprfunc)Nuitka_AsyncgenAsend_tp_repr,                          /* tp_repr */
    0,                                                               /* tp_as_number */
    0,                                                               /* tp_as_sequence */
    0,                                                               /* tp_as_mapping */
    0,                                                               /* tp_hash */
    0,                                                               /* tp_call */
    0,                                                               /* tp_str */
    PyObject_GenericGetAttr,                                         /* tp_getattro */
    0,                                                               /* tp_setattro */
    0,                                                               /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                         /* tp_flags */
    0,                                                               /* tp_doc */
    (traverseproc)Nuitka_AsyncgenAsend_tp_traverse,                  /* tp_traverse */
    0,                                                               /* tp_clear */
    0,                                                               /* tp_richcompare */
    0,                                                               /* tp_weaklistoffset */
    PyObject_SelfIter,                                               /* tp_iter */
    (iternextfunc)Nuitka_AsyncgenAsend_tp_iternext,                  /* tp_iternext */
    Nuitka_AsyncgenAsend_methods,                                    /* tp_methods */
    0,                                                               /* tp_members */
    0,                                                               /* tp_getset */
    0,                                                               /* tp_base */
    0,                                                               /* tp_dict */
    0,                                                               /* tp_descr_get */
    0,                                                               /* tp_descr_set */
    0,                                                               /* tp_dictoffset */
    0,                                                               /* tp_init */
    0,                                                               /* tp_alloc */
    0,                                                               /* tp_new */
};

static PyObject *Nuitka_AsyncgenAsend_New(struct Nuitka_AsyncgenObject *asyncgen, PyObject *sendval) {
    struct Nuitka_AsyncgenAsendObject *result;

    allocateFromFreeListFixed(free_list_asyncgen_asends, struct Nuitka_AsyncgenAsendObject, Nuitka_AsyncgenAsend_Type)

        Py_INCREF(asyncgen);
    result->m_gen = asyncgen;

    // TODO: We could make the user do that.
    Py_INCREF(sendval);
    result->m_sendval = sendval;

    result->m_state = AWAITABLE_STATE_INIT;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

struct Nuitka_AsyncgenAthrowObject {
    /* Python object folklore: */
    PyObject_HEAD;

    // The asyncgen we are working for.
    struct Nuitka_AsyncgenObject *m_gen;
    // Arguments, NULL in case of close, otherwise throw arguments.
    PyObject *m_args;

    AwaitableState m_state;
};

static struct Nuitka_AsyncgenAthrowObject *free_list_asyncgen_athrows = NULL;
static int free_list_asyncgen_athrows_count = 0;

static void Nuitka_AsyncgenAthrow_dealloc(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow) {
    Nuitka_GC_UnTrack(asyncgen_athrow);

    Py_DECREF(asyncgen_athrow->m_gen);
    Py_XDECREF(asyncgen_athrow->m_args);

    releaseToFreeList(free_list_asyncgen_athrows, asyncgen_athrow, MAX_ASYNCGEN_FREE_LIST_COUNT);
}

static int Nuitka_AsyncgenAthrow_traverse(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, visitproc visit,
                                          void *arg) {
    Py_VISIT(asyncgen_athrow->m_gen);
    Py_VISIT(asyncgen_athrow->m_args);

    return 0;
}

static PyObject *Nuitka_AsyncgenAthrow_send(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *arg) {
    struct Nuitka_AsyncgenObject *asyncgen = asyncgen_athrow->m_gen;

    // If finished, just report StopIteration.
    if (asyncgen->m_status == status_Finished || asyncgen_athrow->m_state == AWAITABLE_STATE_CLOSED) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    PyObject *retval;

    if (asyncgen_athrow->m_state == AWAITABLE_STATE_INIT) {
        // Can also close only once.
        if (asyncgen->m_closed) {
            PyErr_SetNone(PyExc_StopIteration);
            return NULL;
        }

        // Starting accepts only "None" as input value.
        if (arg != Py_None) {
            PyErr_Format(PyExc_RuntimeError, "can't send non-None value to a just-started coroutine");

            return NULL;
        }

        asyncgen_athrow->m_state = AWAITABLE_STATE_ITER;

        if (asyncgen_athrow->m_args == NULL) {
            asyncgen->m_closed = true;

            retval =
                _Nuitka_Asyncgen_throw2(asyncgen, 1, /* Do not close generator when PyExc_GeneratorExit is passed */
                                        PyExc_GeneratorExit, NULL, NULL);

            if (retval) {
                if (_PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval)) {
                    Py_DECREF(retval);

                    PyErr_Format(PyExc_RuntimeError, "async generator ignored GeneratorExit");

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

            retval =
                _Nuitka_Asyncgen_throw2(asyncgen, 0, /* Do not close generator when PyExc_GeneratorExit is passed */
                                        exception_type, exception_value, exception_tb);

            retval = Nuitka_Asyncgen_unwrap_value(asyncgen, retval);
        }

        if (retval == NULL) {
            goto check_error;
        }

        return retval;
    }

    assert(asyncgen_athrow->m_state == AWAITABLE_STATE_ITER);

    retval = _Nuitka_Asyncgen_send(asyncgen, arg, false, NULL, NULL, NULL);

    if (asyncgen_athrow->m_args) {
        return Nuitka_Asyncgen_unwrap_value(asyncgen, retval);
    } else {
        /* We are here to close if no args. */
        if (retval) {
            if (_PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval)) {
                Py_DECREF(retval);

                PyErr_Format(PyExc_RuntimeError, "async generator ignored GeneratorExit");

                return NULL;
            }

            return retval;
        }
    }

check_error:

    if (PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
        asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

        if (asyncgen_athrow->m_args == NULL) {
            CLEAR_ERROR_OCCURRED();
            PyErr_SetNone(PyExc_StopIteration);
        }
    } else if (PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
        asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

        CLEAR_ERROR_OCCURRED();
        PyErr_SetNone(PyExc_StopIteration);
    }

    return NULL;
}

static PyObject *Nuitka_AsyncgenAthrow_throw(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *args) {
    PyObject *retval;

#if PYTHON_VERSION < 375
    if (asyncgen_athrow->m_state == AWAITABLE_STATE_INIT) {
        PyErr_Format(PyExc_RuntimeError, "can't send non-None value to a just-started coroutine");

        return NULL;
    }
#endif

    if (asyncgen_athrow->m_state == AWAITABLE_STATE_CLOSED) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    retval = Nuitka_Asyncgen_throw(asyncgen_athrow->m_gen, args);

    if (asyncgen_athrow->m_args) {
        return Nuitka_Asyncgen_unwrap_value(asyncgen_athrow->m_gen, retval);
    } else {
        if (retval) {
            if (_PyAsyncGenWrappedValue_CheckExact(retval) || Nuitka_AsyncgenWrappedValue_CheckExact(retval)) {
                Py_DECREF(retval);

                PyErr_Format(PyExc_RuntimeError, "async generator ignored GeneratorExit");

                return NULL;
            }
        }

        return retval;
    }
}

static PyObject *Nuitka_AsyncgenAthrow_tp_iternext(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow) {
    return Nuitka_AsyncgenAthrow_send(asyncgen_athrow, Py_None);
}

static PyObject *Nuitka_AsyncgenAthrow_close(struct Nuitka_AsyncgenAthrowObject *asyncgen_athrow, PyObject *args) {
    asyncgen_athrow->m_state = AWAITABLE_STATE_CLOSED;

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef Nuitka_AsyncgenAthrow_methods[] = {
    {"send", (PyCFunction)Nuitka_AsyncgenAthrow_send, METH_O, NULL},
    {"throw", (PyCFunction)Nuitka_AsyncgenAthrow_throw, METH_VARARGS, NULL},
    {"close", (PyCFunction)Nuitka_AsyncgenAthrow_close, METH_NOARGS, NULL},
    {NULL}};

static PyAsyncMethods Nuitka_AsyncgenAthrow_as_async = {
    PyObject_SelfIter, /* am_await */
    0,                 /* am_aiter */
    0                  /* am_anext */
};

static PyTypeObject Nuitka_AsyncgenAthrow_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_async_generator_athrow", /* tp_name */
    sizeof(struct Nuitka_AsyncgenAthrowObject),                       /* tp_basicsize */
    0,                                                                /* tp_itemsize */
    (destructor)Nuitka_AsyncgenAthrow_dealloc,                        /* tp_dealloc */
    0,                                                                /* tp_print */
    0,                                                                /* tp_getattr */
    0,                                                                /* tp_setattr */
    &Nuitka_AsyncgenAthrow_as_async,                                  /* tp_as_async */
    0,                                                                /* tp_repr */
    0,                                                                /* tp_as_number */
    0,                                                                /* tp_as_sequence */
    0,                                                                /* tp_as_mapping */
    0,                                                                /* tp_hash */
    0,                                                                /* tp_call */
    0,                                                                /* tp_str */
    PyObject_GenericGetAttr,                                          /* tp_getattro */
    0,                                                                /* tp_setattro */
    0,                                                                /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                          /* tp_flags */
    0,                                                                /* tp_doc */
    (traverseproc)Nuitka_AsyncgenAthrow_traverse,                     /* tp_traverse */
    0,                                                                /* tp_clear */
    0,                                                                /* tp_richcompare */
    0,                                                                /* tp_weaklistoffset */
    PyObject_SelfIter,                                                /* tp_iter */
    (iternextfunc)Nuitka_AsyncgenAthrow_tp_iternext,                  /* tp_iternext */
    Nuitka_AsyncgenAthrow_methods,                                    /* tp_methods */
    0,                                                                /* tp_members */
    0,                                                                /* tp_getset */
    0,                                                                /* tp_base */
    0,                                                                /* tp_dict */
    0,                                                                /* tp_descr_get */
    0,                                                                /* tp_descr_set */
    0,                                                                /* tp_dictoffset */
    0,                                                                /* tp_init */
    0,                                                                /* tp_alloc */
    0,                                                                /* tp_new */
};

static PyObject *Nuitka_AsyncgenAthrow_New(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args) {
    struct Nuitka_AsyncgenAthrowObject *result;

    allocateFromFreeListFixed(free_list_asyncgen_athrows, struct Nuitka_AsyncgenAthrowObject,
                              Nuitka_AsyncgenAthrow_Type)

        Py_INCREF(asyncgen);
    result->m_gen = asyncgen;

    Py_XINCREF(args);
    result->m_args = args;

    result->m_state = AWAITABLE_STATE_INIT;

    Nuitka_GC_Track(result);
    return (PyObject *)result;
}

extern PyObject *Nuitka_AIterWrapper_New(PyObject *aiter);

void _initCompiledAsyncgenTypes(void) {
    PyType_Ready(&Nuitka_Asyncgen_Type);
    PyType_Ready(&Nuitka_AsyncgenAsend_Type);
    PyType_Ready(&Nuitka_AsyncgenAthrow_Type);
    PyType_Ready(&Nuitka_AsyncgenValueWrapper_Type);
}
