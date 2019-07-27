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
/** Uncompiled generator integration
 *
 * This is for use in compiled generator, coroutine, async types. The file in
 * included for compiled generator, and in part exports functions as necessary.
 *
 */

#if PYTHON_VERSION >= 300
#if PYTHON_VERSION < 350
static
#endif
    void
    Nuitka_SetStopIterationValue(PyObject *value) {
    CHECK_OBJECT(value);

#if PYTHON_VERSION <= 352
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

#if PYTHON_VERSION >= 370
static inline void Nuitka_PyGen_exc_state_clear(_PyErr_StackItem *exc_state) {
    PyObject *t = exc_state->exc_type;
    PyObject *v = exc_state->exc_value;
    PyObject *tb = exc_state->exc_traceback;

    exc_state->exc_type = NULL;
    exc_state->exc_value = NULL;
    exc_state->exc_traceback = NULL;

    Py_XDECREF(t);
    Py_XDECREF(v);
    Py_XDECREF(tb);
}
#endif

#if PYTHON_VERSION >= 300

// This is for CPython iterator objects, the respective code is not exported as
// API, so we need to redo it. This is an re-implementation that closely follows
// what it does. It's unrelated to compiled generators.
PyObject *PyGen_Send(PyGenObject *gen, PyObject *arg) {
    if (unlikely(gen->gi_running)) {
        PyErr_Format(PyExc_ValueError, "generator already executing");
        return NULL;
    }

    PyFrameObject *f = gen->gi_frame;

    if (f == NULL || f->f_stacktop == NULL) {
        // Set exception if called from send()
        if (arg != NULL) {
            PyErr_SetNone(PyExc_StopIteration);
        }

        return NULL;
    }

    if (f->f_lasti == -1) {
        if (unlikely(arg && arg != Py_None)) {
            PyErr_Format(PyExc_TypeError, "can't send non-None value to a just-started generator");

            return NULL;
        }
    } else {
        // Put arg on top of the value stack
        PyObject *tmp = arg ? arg : Py_None;

        Py_INCREF(tmp);
        *(f->f_stacktop++) = tmp;
    }

    // Generators always return to their most recent caller, not necessarily
    // their creator.
    PyThreadState *tstate = PyThreadState_GET();
    Py_XINCREF(tstate->frame);

    f->f_back = tstate->frame;

    gen->gi_running = 1;
#if PYTHON_VERSION >= 370
    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;
#endif
    PyObject *result = PyEval_EvalFrameEx(f, 0);
#if PYTHON_VERSION >= 370
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;
#endif
    gen->gi_running = 0;

    // Don't keep the reference to f_back any longer than necessary.  It
    // may keep a chain of frames alive or it could create a reference
    // cycle.
    Py_CLEAR(f->f_back);

    // If the generator just returned (as opposed to yielding), signal that the
    // generator is exhausted.
    if (result && f->f_stacktop == NULL) {
        if (result == Py_None) {
            PyErr_SetNone(PyExc_StopIteration);
        } else {
            PyObject *e = PyObject_CallFunctionObjArgs(PyExc_StopIteration, result, NULL);

            if (e != NULL) {
                PyErr_SetObject(PyExc_StopIteration, e);
                Py_DECREF(e);
            }
        }

        Py_CLEAR(result);
    }

    if (result == NULL || f->f_stacktop == NULL) {
#if PYTHON_VERSION < 370
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
#if PYTHON_VERSION >= 340
        gen->gi_frame->f_gen = NULL;
#endif
        gen->gi_frame = NULL;
        Py_DECREF(f);
    }

    return result;
}

#endif

#if PYTHON_VERSION >= 340

#include <opcode.h>

// Not done for earlier versions yet, indicate usability for compiled generators.
#define NUITKA_UNCOMPILED_THROW_INTEGRATION 1

extern PyObject *const_str_plain_throw, *const_str_plain_close;

static PyObject *Nuitka_PyGen_gen_close(PyGenObject *gen, PyObject *args);

static PyObject *Nuitka_PyGen_yf(PyGenObject *gen) {
    PyFrameObject *f = gen->gi_frame;

    if (f && f->f_stacktop) {
        PyObject *bytecode = f->f_code->co_code;
        unsigned char *code = (unsigned char *)PyBytes_AS_STRING(bytecode);

        if (f->f_lasti < 0) {
            return NULL;
        }

#if PYTHON_VERSION < 360
        if (code[f->f_lasti + 1] != YIELD_FROM)
#else
        if (code[f->f_lasti + sizeof(_Py_CODEUNIT)] != YIELD_FROM)
#endif
        {
            return NULL;
        }

        PyObject *yf = f->f_stacktop[-1];
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

    if (unlikely(gen->gi_running)) {
        char const *msg = "generator already executing";

#if PYTHON_VERSION >= 350
        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine already executing";
        }
#if PYTHON_VERSION >= 360
        else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator already executing";
        }
#endif
#endif
        PyErr_Format(PyExc_ValueError, msg);

        return NULL;
    }

    if (f == NULL || f->f_stacktop == NULL) {
#if PYTHON_VERSION >= 350
        if (PyCoro_CheckExact(gen) && !closing) {
            PyErr_Format(PyExc_RuntimeError, "cannot reuse already awaited coroutine");
        } else
#endif
            if (arg && !exc) {
#if PYTHON_VERSION >= 360
            if (PyAsyncGen_CheckExact(gen)) {
                PyErr_SetNone(PyExc_StopAsyncIteration);
            } else
#endif
            {
                PyErr_SetNone(PyExc_StopIteration);
            }
        }
        return NULL;
    }

    if (f->f_lasti == -1) {
        if (unlikely(arg != NULL && arg != Py_None)) {
            char const *msg = "can't send non-None value to a just-started generator";

#if PYTHON_VERSION >= 350
            if (PyCoro_CheckExact(gen)) {
                msg = "can't send non-None value to a just-started coroutine";
            }
#if PYTHON_VERSION >= 360
            else if (PyAsyncGen_CheckExact(gen)) {
                msg = "can't send non-None value to a just-started async generator";
            }
#endif
#endif

            PyErr_Format(PyExc_TypeError, msg);
            return NULL;
        }
    } else {
        result = arg ? arg : Py_None;
        Py_INCREF(result);
        *(f->f_stacktop++) = result;
    }

    Py_XINCREF(tstate->frame);
    f->f_back = tstate->frame;

    gen->gi_running = 1;
#if PYTHON_VERSION >= 370
    gen->gi_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = &gen->gi_exc_state;
#endif
    result = PyEval_EvalFrameEx(f, exc);
#if PYTHON_VERSION >= 370
    tstate->exc_info = gen->gi_exc_state.previous_item;
    gen->gi_exc_state.previous_item = NULL;
#endif
    gen->gi_running = 0;

    Py_CLEAR(f->f_back);

    if (result && f->f_stacktop == NULL) {
        if (result == Py_None) {
#if PYTHON_VERSION >= 360
            if (PyAsyncGen_CheckExact(gen)) {
                PyErr_SetNone(PyExc_StopAsyncIteration);
            } else
#endif
            {
                PyErr_SetNone(PyExc_StopIteration);
            }
        } else {
            Nuitka_SetStopIterationValue(result);
        }

        Py_CLEAR(result);
    }
#if PYTHON_VERSION >= 350
    else if (result == NULL && PyErr_ExceptionMatches(PyExc_StopIteration)) {
#if PYTHON_VERSION < 370
        const int check_stop_iter_error_flags = CO_FUTURE_GENERATOR_STOP | CO_COROUTINE |
#if PYTHON_VERSION >= 360
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
#if PYTHON_VERSION >= 360
            else if (PyAsyncGen_CheckExact(gen)) {
                msg = "async generator raised StopIteration";
            }
#endif

#if PYTHON_VERSION >= 360
            _PyErr_FormatFromCause(
#else
            PyErr_Format(
#endif
                PyExc_RuntimeError, "%s", msg);
        }
    }
#endif
#if PYTHON_VERSION >= 360
    else if (result == NULL && PyAsyncGen_CheckExact(gen) && PyErr_ExceptionMatches(PyExc_StopAsyncIteration)) {
        char const *msg = "async generator raised StopAsyncIteration";
        _PyErr_FormatFromCause(PyExc_RuntimeError, "%s", msg);
    }
#endif

    if (!result || f->f_stacktop == NULL) {
#if PYTHON_VERSION < 370
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

    return result;
}

static int Nuitka_PyGen_gen_close_iter(PyObject *yf) {
    PyObject *retval = NULL;

    if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 350
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
        gen->gi_running = 1;
        err = Nuitka_PyGen_gen_close_iter(yf);
        gen->gi_running = 0;

        Py_DECREF(yf);
    }

    if (err == 0) {
        PyErr_SetNone(PyExc_GeneratorExit);
    }

    PyObject *retval = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);

    if (retval != NULL) {
        char const *msg = "generator ignored GeneratorExit";

#if PYTHON_VERSION >= 350
        if (PyCoro_CheckExact(gen)) {
            msg = "coroutine ignored GeneratorExit";
        }
#if PYTHON_VERSION >= 360
        else if (PyAsyncGen_CheckExact(gen)) {
            msg = "async generator ignored GeneratorExit";
        }
#endif
#endif
        Py_DECREF(retval);

        PyErr_Format(PyExc_RuntimeError, msg);
        return NULL;
    }

    if (PyErr_ExceptionMatches(PyExc_StopIteration) || PyErr_ExceptionMatches(PyExc_GeneratorExit)) {
        CLEAR_ERROR_OCCURRED();

        Py_INCREF(Py_None);
        return Py_None;
    }
    return NULL;
}

PyObject *Nuitka_UncompiledGenerator_throw(PyGenObject *gen, int close_on_genexit, PyObject *typ, PyObject *val,
                                           PyObject *tb) {
    PyObject *yf = Nuitka_PyGen_yf(gen);

    if (yf != NULL) {
        if (PyErr_GivenExceptionMatches(typ, PyExc_GeneratorExit) && close_on_genexit) {
            gen->gi_running = 1;
            int err = Nuitka_PyGen_gen_close_iter(yf);
            gen->gi_running = 0;

            Py_DECREF(yf);

            if (err < 0) {
                return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }

            goto throw_here;
        }

        PyObject *ret;

        if (PyGen_CheckExact(yf)
#if PYTHON_VERSION >= 350
            || PyCoro_CheckExact(yf)
#endif
        ) {
            gen->gi_running = 1;

            ret = Nuitka_UncompiledGenerator_throw((PyGenObject *)yf, close_on_genexit, typ, val, tb);

            gen->gi_running = 0;
        } else {
            PyObject *meth = PyObject_GetAttr(yf, const_str_plain_throw);

            if (meth == NULL) {
                if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    Py_DECREF(yf);

                    return NULL;
                }

                CLEAR_ERROR_OCCURRED();
                Py_DECREF(yf);

                goto throw_here;
            }

            gen->gi_running = 1;
            ret = PyObject_CallFunctionObjArgs(meth, typ, val, tb, NULL);
            gen->gi_running = 0;

            Py_DECREF(meth);
        }

        Py_DECREF(yf);

        if (ret == NULL) {
            ret = *(--gen->gi_frame->f_stacktop);
            Py_DECREF(ret);

#if PYTHON_VERSION >= 360
            gen->gi_frame->f_lasti += sizeof(_Py_CODEUNIT);
#else
            gen->gi_frame->f_lasti += 1;
#endif

            if (_PyGen_FetchStopIterationValue(&val) == 0) {
                ret = Nuitka_PyGen_gen_send_ex(gen, val, 0, 0);

                Py_DECREF(val);
            } else {
                ret = Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 0);
            }
        }
        return ret;
    }

throw_here:

    if (tb == Py_None) {
        tb = NULL;
    } else if (tb != NULL && !PyTraceBack_Check(tb)) {
        PyErr_Format(PyExc_TypeError, "throw() third argument must be a traceback object");
        return NULL;
    }

    Py_INCREF(typ);
    Py_XINCREF(val);
    Py_XINCREF(tb);

    if (PyExceptionClass_Check(typ)) {
        NORMALIZE_EXCEPTION(&typ, &val, (PyTracebackObject **)&tb);
    }

    else if (PyExceptionInstance_Check(typ)) {
        if (unlikely(val && val != Py_None)) {
            PyErr_Format(PyExc_TypeError, "instance exception may not have a separate value");

            goto failed_throw;
        } else {
            Py_XDECREF(val);
            val = typ;
            typ = PyExceptionInstance_Class(typ);
            Py_INCREF(typ);

            if (tb == NULL) {
                tb = PyException_GetTraceback(val);
            }
        }
    } else {
        PyErr_Format(PyExc_TypeError, "exceptions must be classes or instances deriving from BaseException, not %s",
                     Py_TYPE(typ)->tp_name);

        goto failed_throw;
    }

    RESTORE_ERROR_OCCURRED(typ, val, (PyTracebackObject *)tb);

    return Nuitka_PyGen_gen_send_ex(gen, Py_None, 1, 1);

failed_throw:
    Py_DECREF(typ);
    Py_XDECREF(val);
    Py_XDECREF(tb);
    return NULL;
}

#endif
