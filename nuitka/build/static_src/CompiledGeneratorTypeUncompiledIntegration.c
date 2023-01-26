//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
/** Uncompiled generator integration
 *
 * This is for use in compiled generator, coroutine, async types. The file in
 * included for compiled generator, and in part exports functions as necessary.
 *
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#ifdef PY_NOGIL
#define Py_BUILD_CORE
#include "internal/pycore_generator.h"
#undef Py_BUILD_CORE
#endif

// This function takes no reference to value, and publishes a StopIteration
// exception with it.
#if PYTHON_VERSION >= 0x300
static void Nuitka_SetStopIterationValue(PyObject *value) {
    CHECK_OBJECT(value);

#if PYTHON_VERSION <= 0x352
    PyObject *stop_value = CALL_FUNCTION_WITH_SINGLE_ARG(PyExc_StopIteration, value);

    if (unlikely(stop_value == NULL)) {
        return;
    }

    Py_INCREF(PyExc_StopIteration);
    RESTORE_ERROR_OCCURRED(PyExc_StopIteration, stop_value, NULL);
#else
    if (likely(!PyTuple_Check(value) && !PyExceptionInstance_Check(value))) {
        Py_INCREF(PyExc_StopIteration);
        Py_INCREF(value);

        RESTORE_ERROR_OCCURRED(PyExc_StopIteration, value, NULL);
    } else {
        PyObject *stop_value = CALL_FUNCTION_WITH_SINGLE_ARG(PyExc_StopIteration, value);

        if (unlikely(stop_value == NULL)) {
            return;
        }

        Py_INCREF(PyExc_StopIteration);

        RESTORE_ERROR_OCCURRED(PyExc_StopIteration, stop_value, NULL);
    }
#endif
}
#endif

#if PYTHON_VERSION >= 0x370
static inline void Nuitka_PyGen_exc_state_clear(_PyErr_StackItem *exc_state) {
#if PYTHON_VERSION < 0x3b0
    PyObject *t = exc_state->exc_type;
#endif
    PyObject *v = exc_state->exc_value;
#if PYTHON_VERSION < 0x3b0
    PyObject *tb = exc_state->exc_traceback;
#endif

#if PYTHON_VERSION < 0x3b0
    exc_state->exc_type = NULL;
#endif
    exc_state->exc_value = NULL;
#if PYTHON_VERSION < 0x3b0
    exc_state->exc_traceback = NULL;
#endif

#if PYTHON_VERSION < 0x3b0
    Py_XDECREF(t);
#endif
    Py_XDECREF(v);
#if PYTHON_VERSION < 0x3b0
    Py_XDECREF(tb);
#endif
}
#endif

#if PYTHON_VERSION >= 0x300

#if PYTHON_VERSION < 0x3b0
static inline bool Nuitka_PyFrameHasCompleted(PyFrameObject *const frame) {
#if PYTHON_VERSION < 0x3a0
    return frame->f_stacktop == NULL;
#else
    return frame->f_state > FRAME_EXECUTING;
#endif
}
#endif

// This is for CPython iterator objects, the respective code is not exported as
// API, so we need to redo it. This is an re-implementation that closely follows
// what it does. It's unrelated to compiled generators, and used from coroutines
// and asyncgen to interact with them.
static PyObject *Nuitka_PyGen_Send(PyGenObject *gen, PyObject *arg) {
#if defined(PY_NOGIL)
    PyObject *res;

    if (gen->status == GEN_CREATED) {
        if (unlikely(arg != Py_None)) {
            char const *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }

            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
            return NULL;
        }
        arg = NULL;
    }

    res = PyEval2_EvalGen(gen, arg);

    if (likely(res != NULL)) {
        assert(gen->status == GEN_SUSPENDED);
        return res;
    }

    if (likely(gen->return_value == Py_None)) {
        gen->return_value = NULL;
        PyErr_SetNone(PyAsyncGen_CheckExact(gen) ? PyExc_StopAsyncIteration : PyExc_StopIteration);
        return NULL;
    } else if (gen->return_value != NULL) {
        Nuitka_SetStopIterationValue(gen->return_value);
        return NULL;
    } else {
        return gen_wrap_exception(gen);
    }
#elif PYTHON_VERSION >= 0x3a0
    PyObject *result;

    PySendResult res = PyIter_Send((PyObject *)gen, arg, &result);

    switch (res) {
    case PYGEN_RETURN:
        if (result == NULL) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        } else {
            if (result != Py_None) {
                Nuitka_SetStopIterationValue(result);
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
#else

    PyFrameObject *f = gen->gi_frame;

#if PYTHON_VERSION >= 0x3b0
    if (gen->gi_frame_state == FRAME_EXECUTING) {
#elif PYTHON_VERSION >= 0x3a0
    if (f != NULL && _PyFrame_IsExecuting(f)) {
#else
    if (unlikely(gen->gi_running)) {
#endif
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, "generator already executing");
        return NULL;
    }

#if PYTHON_VERSION < 0x3b0
    if (f == NULL || Nuitka_PyFrameHasCompleted(f)) {
#else
    if (gen->gi_frame_state >= FRAME_COMPLETED) {
#endif
        // Set exception if called from send()
        if (arg != NULL) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        }

        return NULL;
    }

#if PYTHON_VERSION < 0x3a0
    if (f->f_lasti == -1) {
        if (unlikely(arg && arg != Py_None)) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "can't send non-None value to a just-started generator");

            return NULL;
        }
    } else {
        // Put arg on top of the value stack
        PyObject *tmp = arg ? arg : Py_None;

        Py_INCREF(tmp);
        *(f->f_stacktop++) = tmp;
    }
#else
    // CPython assertions, check them
    assert(_PyFrame_IsRunnable(f));
    assert(f->f_lasti >= 0 || ((unsigned char *)PyBytes_AS_STRING(f->f_code->co_code))[0] == 129);

    PyObject *gen_result = arg ? arg : Py_None;
    Py_INCREF(gen_result);
    gen->gi_frame->f_valuestack[gen->gi_frame->f_stackdepth] = gen_result;
    gen->gi_frame->f_stackdepth++;
#endif

    // Generators always return to their most recent caller, not necessarily
    // their creator.
    PyThreadState *tstate = PyThreadState_GET();
    Py_XINCREF(tstate->frame);

    f->f_back = tstate->frame;

#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 1;
#endif
#if PYTHON_VERSION >= 0x370
    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;
#endif

#if PYTHON_VERSION < 0x390
    PyObject *result = PyEval_EvalFrameEx(f, 0);
#else
    PyObject *result = _PyEval_EvalFrame(tstate, f, 0);
#endif

#if PYTHON_VERSION >= 0x370
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;
#endif
#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 0;
#endif

    // Don't keep the reference to f_back any longer than necessary.  It
    // may keep a chain of frames alive or it could create a reference
    // cycle.
    Py_CLEAR(f->f_back);

    // If the generator just returned (as opposed to yielding), signal that the
    // generator is exhausted.
#if PYTHON_VERSION < 0x3a0
    if (result && f->f_stacktop == NULL) {
        if (result == Py_None) {
            SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
        } else {
            PyObject *e = PyObject_CallFunctionObjArgs(PyExc_StopIteration, result, NULL);

            if (e != NULL) {
                SET_CURRENT_EXCEPTION_TYPE0_VALUE1(PyExc_StopIteration, e);
            }
        }

        Py_CLEAR(result);
    }

    if (result == NULL || f->f_stacktop == NULL) {
#if PYTHON_VERSION < 0x370
        // Generator is finished, remove exception from frame before releasing
        // it.
        PyObject *type = f->f_exc_type;
        PyObject *value = f->f_exc_value;
        PyObject *traceback = f->f_exc_traceback;
        f->f_exc_type = NULL;
        f->f_exc_value = NULL;
        f->f_exc_traceback = NULL;
        Py_XDECREF(type);
        Py_XDECREF(value);
        Py_XDECREF(traceback);
#else
        Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);
#endif

        // Now release frame.
#if PYTHON_VERSION >= 0x340
        gen->gi_frame->f_gen = NULL;
#endif
        gen->gi_frame = NULL;
        Py_DECREF(f);
    }
#else
    if (result) {
        if (!_PyFrameHasCompleted(f)) {
            return result;
        }
        assert(result == Py_None || !PyAsyncGen_CheckExact(gen));

        if (result == Py_None && !PyAsyncGen_CheckExact(gen)) {
            Py_DECREF(result);
            result = NULL;
        }
    } else {
        if (PyErr_ExceptionMatches(PyExc_StopIteration)) {
            const char *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        } else if (PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
            /* code in `gen` raised a StopAsyncIteration error:
               raise a RuntimeError.
            */
            const char *msg = "async generator raised StopAsyncIteration";
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        }

        result = NULL;
    }

    /* generator can't be rerun, so release the frame */
    /* first clean reference cycle through stored exception traceback */
    Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);
    gen->gi_frame->f_gen = NULL;
    gen->gi_frame = NULL;
    Py_DECREF(f);

#endif

    return result;
#endif
}

#endif

// TODO: Disabled for NOGIL until it becomes more ready.
// TODO: Disable for Python3.11 initially
#if PYTHON_VERSION >= 0x340 && !defined(PY_NOGIL) && PYTHON_VERSION < 0x3b0

// Clashes with our helper names.
#include <opcode.h>
#undef LIST_EXTEND
#undef CALL_FUNCTION
#undef IMPORT_NAME

// Not done for earlier versions yet, indicate usability for compiled generators.
#define NUITKA_UNCOMPILED_THROW_INTEGRATION 1

static PyObject *Nuitka_PyGen_gen_close(PyGenObject *gen, PyObject *args);

static PyObject *Nuitka_PyGen_yf(PyGenObject *gen) {
    PyFrameObject *f = gen->gi_frame;

#if PYTHON_VERSION < 0x3a0
    if (f && f->f_stacktop) {
#else
    if (f) {
#endif
        PyObject *bytecode = f->f_code->co_code;
        unsigned char *code = (unsigned char *)PyBytes_AS_STRING(bytecode);

        if (f->f_lasti < 0) {
            return NULL;
        }

#if PYTHON_VERSION < 0x360
        if (code[f->f_lasti + 1] != YIELD_FROM)
#elif PYTHON_VERSION < 0x3a0
        if (code[f->f_lasti + sizeof(_Py_CODEUNIT)] != YIELD_FROM)
#else
    if (code[(f->f_lasti + 1) * sizeof(_Py_CODEUNIT)] != YIELD_FROM)
#endif
        {
            return NULL;
        }

#if PYTHON_VERSION < 0x3a0
        PyObject *yf = f->f_stacktop[-1];
#else
        assert(f->f_stackdepth > 0);
        PyObject *yf = f->f_valuestack[f->f_stackdepth - 1];
#endif
        Py_INCREF(yf);
        return yf;
    } else {
        return NULL;
    }
}

static PyObject *Nuitka_PyGen_gen_send_ex(PyGenObject *gen, PyObject *arg, int exc, int closing) {
    PyThreadState *tstate = PyThreadState_GET();
    PyFrameObject *f = gen->gi_frame;
    PyObject *result;

#if PYTHON_VERSION >= 0x3a0
    if (f != NULL && unlikely(_PyFrame_IsExecuting(f))) {
#else
    if (unlikely(gen->gi_running)) {
#endif
        char const *msg = "generator already executing";

#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine already executing";
        }
#if PYTHON_VERSION >= 0x360
        else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator already executing";
        }
#endif
#endif
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError, msg);

        return NULL;
    }

    if (f == NULL || Nuitka_PyFrameHasCompleted(f)) {
#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen) && !closing) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "cannot reuse already awaited coroutine");
        } else
#endif
            if (arg && !exc) {
#if PYTHON_VERSION >= 0x360
            if (PyAsyncGen_CheckExact(gen)) {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopAsyncIteration);
            } else
#endif
            {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
            }
        }
        return NULL;
    }

#if PYTHON_VERSION < 0x3a0
    if (f->f_lasti == -1) {
        if (unlikely(arg != NULL && arg != Py_None)) {
            char const *msg = "can't send non-None value to a just-started generator";

#if PYTHON_VERSION >= 0x350
            if (PyCoro_CheckExact(gen)) {
                msg = "can't send non-None value to a just-started coroutine";
            }
#if PYTHON_VERSION >= 0x360
            else if (PyAsyncGen_CheckExact(gen)) {
                msg = "can't send non-None value to a just-started async generator";
            }
#endif
#endif

            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, msg);
            return NULL;
        }
    } else {
        result = arg ? arg : Py_None;
        Py_INCREF(result);
        *(f->f_stacktop++) = result;
    }
#else
    // CPython assertions, check them
    assert(_PyFrame_IsRunnable(f));
    assert(f->f_lasti >= 0 || ((unsigned char *)PyBytes_AS_STRING(f->f_code->co_code))[0] == GEN_START);

    result = arg ? arg : Py_None;
    Py_INCREF(result);
    gen->gi_frame->f_valuestack[gen->gi_frame->f_stackdepth] = result;
    gen->gi_frame->f_stackdepth++;
#endif

    Py_XINCREF(tstate->frame);
    f->f_back = tstate->frame;

#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 1;
#endif
#if PYTHON_VERSION >= 0x370
    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;
#endif
#if PYTHON_VERSION < 0x390
    result = PyEval_EvalFrameEx(f, exc);
#else
    result = _PyEval_EvalFrame(tstate, f, exc);
#endif
#if PYTHON_VERSION >= 0x370
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;
#endif
#if PYTHON_VERSION < 0x3a0
    gen->gi_running = 0;
#endif

    Py_CLEAR(f->f_back);

#if PYTHON_VERSION < 0x3a0
    if (result && f->f_stacktop == NULL) {
        if (result == Py_None) {
#if PYTHON_VERSION >= 0x360
            if (PyAsyncGen_CheckExact(gen)) {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopAsyncIteration);
            } else
#endif
            {
                SET_CURRENT_EXCEPTION_TYPE0(PyExc_StopIteration);
            }
        } else {
            Nuitka_SetStopIterationValue(result);
        }

        Py_CLEAR(result);
    }
#if PYTHON_VERSION >= 0x350
    else if (result == NULL && PyErr_ExceptionMatches(PyExc_StopIteration)) {
#if PYTHON_VERSION < 0x370
        const int check_stop_iter_error_flags = CO_FUTURE_GENERATOR_STOP | CO_COROUTINE |
#if PYTHON_VERSION >= 0x360
                                                CO_ASYNC_GENERATOR |
#endif
                                                CO_ITERABLE_COROUTINE;

        if (unlikely(gen->gi_code != NULL && ((PyCodeObject *)gen->gi_code)->co_flags & check_stop_iter_error_flags))
#endif
        {
            char const *msg = "generator raised StopIteration";

            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            }
#if PYTHON_VERSION >= 0x360
            else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
#endif

#if PYTHON_VERSION >= 0x360
            _PyErr_FormatFromCause(
#else
            PyErr_Format(
#endif
                PyExc_RuntimeError, "%s", msg);
        }
    }
#endif
#if PYTHON_VERSION >= 0x360
    else if (result == NULL && PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
        char const *msg = "async generator raised StopAsyncIteration";
        _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
    }
#endif

    if (!result || f->f_stacktop == NULL) {
#if PYTHON_VERSION < 0x370
        PyObject *t, *v, *tb;
        t = f->f_exc_type;
        v = f->f_exc_value;
        tb = f->f_exc_traceback;
        f->f_exc_type = NULL;
        f->f_exc_value = NULL;
        f->f_exc_traceback = NULL;
        Py_XDECREF(t);
        Py_XDECREF(v);
        Py_XDECREF(tb);
#else
        Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);
#endif
        gen->gi_frame->f_gen = NULL;
        gen->gi_frame = NULL;
        Py_DECREF(f);
    }
#else
    if (result) {
        if (!_PyFrameHasCompleted(f)) {
            return result;
        }
        assert(result == Py_None || !PyAsyncGen_CheckExact(gen));
        if (result == Py_None && !PyAsyncGen_CheckExact(gen) && !arg) {
            /* Return NULL if called by gen_iternext() */
            Py_CLEAR(result);
        }
    } else {
        if (PyErr_ExceptionMatches(PyExc_StopIteration)) {
            const char *msg = "generator raised StopIteration";
            if (PyCoro_CheckExact(gen)) {
                msg = "coroutine raised StopIteration";
            } else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        } else if (PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
            /* code in `gen` raised a StopAsyncIteration error:
               raise a RuntimeError.
            */
            const char *msg = "async generator raised StopAsyncIteration";
            _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
        }
    }

    /* generator can't be rerun, so release the frame */
    /* first clean reference cycle through stored exception traceback */
    Nuitka_PyGen_exc_state_clear(&gen->gi_exc_state);
    gen->gi_frame->f_gen = NULL;
    gen->gi_frame = NULL;
    Py_DECREF(f);
#endif
    return result;
}

static int Nuitka_PyGen_gen_close_iter(PyObject *yf) {
    PyObject *retval = NULL;

    if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 0x350
        || PyCoro_CheckExact(yf)
#endif
    ) {
        retval = Nuitka_PyGen_gen_close((PyGenObject *)yf, NULL);

        if (retval == NULL) {
            return -1;
        }
    } else {
        PyObject *meth = PyObject_GetAttr(yf, const_str_plain_close);

        if (meth == NULL) {
            if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                PyErr_WriteUnraisable(yf);
            }

            CLEAR_ERROR_OCCURRED();
        } else {
            retval = CALL_FUNCTION_NO_ARGS(meth);

            Py_DECREF(meth);

            if (retval == NULL) {
                return -1;
            }
        }
    }

    Py_XDECREF(retval);
    return 0;
}

static PyObject *Nuitka_PyGen_gen_close(PyGenObject *gen, PyObject *args) {
    PyObject *yf = Nuitka_PyGen_yf(gen);
    int err = 0;

    if (yf != NULL) {
#if PYTHON_VERSION >= 0x3a0
        PyFrameState state = gen->gi_frame->f_state;
        gen->gi_frame->f_state = FRAME_EXECUTING;
#else
        gen->gi_running = 1;
#endif
        err = Nuitka_PyGen_gen_close_iter(yf);

#if PYTHON_VERSION >= 0x3a0
        gen->gi_frame->f_state = state;
#else
        gen->gi_running = 0;
#endif
        Py_DECREF(yf);
    }

    if (err == 0) {
        SET_CURRENT_EXCEPTION_TYPE0(PyExc_GeneratorExit);
    }

    PyObject *retval = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);

    if (retval != NULL) {
        char const *msg = "generator ignored GeneratorExit";

#if PYTHON_VERSION >= 0x350
        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine ignored GeneratorExit";
        }
#if PYTHON_VERSION >= 0x360
        else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator ignored GeneratorExit";
        }
#endif
#endif
        Py_DECREF(retval);

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, msg);
        return NULL;
    }

    if (PyErr_ExceptionMatches(PyExc_StopIteration) || PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
        CLEAR_ERROR_OCCURRED();

        Py_INCREF(Py_None);
        return Py_None;
    }
    return NULL;
}

static bool _Nuitka_Generator_check_throw2(PyObject **exception_type, PyObject **exception_value,
                                           PyTracebackObject **exception_tb);

// This function is called when throwing to an uncompiled generator. Coroutines and generators
// do this in their yielding from.
// Note:
//   Exception arguments are passed for ownership and must be released before returning. The
//   value of exception_type will not be NULL, but the actual exception will not necessarily
//   be normalized.
static PyObject *Nuitka_UncompiledGenerator_throw(PyGenObject *gen, int close_on_genexit, PyObject *exception_type,
                                                  PyObject *exception_value, PyTracebackObject *exception_tb) {
#if _DEBUG_GENERATOR
    PRINT_STRING("Nuitka_UncompiledGenerator_throw: Enter ");
    PRINT_ITEM((PyObject *)gen);
    PRINT_EXCEPTION(exception_type, exception_value, exception_tb);
    PRINT_NEW_LINE();
#endif

    PyObject *yf = Nuitka_PyGen_yf(gen);

    if (yf != NULL) {
        if (close_on_genexit && EXCEPTION_MATCH_BOOL_SINGLE(exception_type, PyExc_GeneratorExit)) {
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif

            int err = Nuitka_PyGen_gen_close_iter(yf);
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif
            Py_DECREF(yf);

            if (err < 0) {
                // Releasing exception, we are done with it, raising instead the error just
                // occurred.
                Py_DECREF(exception_type);
                Py_XDECREF(exception_value);
                Py_XDECREF(exception_tb);

                return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }

            // Handing exception ownership to this code.
            goto throw_here;
        }

        PyObject *ret;

        if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 0x350
            || PyCoro_CheckExact(yf)
#endif
        ) {
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif

            // Handing exception ownership to "Nuitka_UncompiledGenerator_throw".
            ret = Nuitka_UncompiledGenerator_throw((PyGenObject *)yf, close_on_genexit, exception_type, exception_value,
                                                   exception_tb);

#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif
        } else {
#if 0
            // TODO: Add slow mode traces.
            PRINT_ITEM(yf);
            PRINT_NEW_LINE();
#endif

            PyObject *meth = PyObject_GetAttr(yf, const_str_plain_throw);

            if (meth == NULL) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    Py_DECREF(yf);

                    // Releasing exception, we are done with it.
                    Py_DECREF(exception_type);
                    Py_XDECREF(exception_value);
                    Py_XDECREF(exception_tb);

                    return NULL;
                }

                CLEAR_ERROR_OCCURRED();
                Py_DECREF(yf);

                // Handing exception ownership to this code.
                goto throw_here;
            }

#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 1;
#else
            PyFrameState state = gen->gi_frame->f_state;
            gen->gi_frame->f_state = FRAME_EXECUTING;
#endif
            ret = PyObject_CallFunctionObjArgs(meth, exception_type, exception_value, exception_tb, NULL);
#if PYTHON_VERSION < 0x3a0
            gen->gi_running = 0;
#else
            gen->gi_frame->f_state = state;
#endif

            // Releasing exception, we are done with it.
            Py_DECREF(exception_type);
            Py_XDECREF(exception_value);
            Py_XDECREF(exception_tb);

            Py_DECREF(meth);
        }

        Py_DECREF(yf);

        if (ret == NULL) {
#if PYTHON_VERSION < 0x3a0
            ret = *(--gen->gi_frame->f_stacktop);
#else
            assert(gen->gi_frame->f_stackdepth > 0);
            gen->gi_frame->f_stackdepth--;
            ret = gen->gi_frame->f_valuestack[gen->gi_frame->f_stackdepth];
#endif
            Py_DECREF(ret);

#if PYTHON_VERSION >= 0x360
            gen->gi_frame->f_lasti += sizeof(_Py_CODEUNIT);
#else
            gen->gi_frame->f_lasti += 1;
#endif

            if (_PyGen_FetchStopIterationValue(&exception_value) == 0) {
                ret = Nuitka_PyGen_gen_send_ex(gen, exception_value, 0, 0);

                Py_DECREF(exception_value);
            } else {
                ret = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }
        }
        return ret;
    }

throw_here:
    // We continue to have exception ownership here.
    if (unlikely(_Nuitka_Generator_check_throw2(&exception_type, &exception_value, &exception_tb) == false)) {
        // Exception was released by _Nuitka_Generator_check_throw2 already.
        return NULL;
    }

    // Transfer exception ownership to published exception.
    RESTORE_ERROR_OCCURRED(exception_type, exception_value, (PyTracebackObject *)exception_tb);

    return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);
}

#endif
