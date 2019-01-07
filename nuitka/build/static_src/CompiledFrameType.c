//     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "structmember.h"

#define OFF(x) offsetof(PyFrameObject, x)

static PyMemberDef Nuitka_Frame_memberlist[] = {
    {(char *)"f_back", T_OBJECT, OFF(f_back), READONLY | RESTRICTED},
    {(char *)"f_code", T_OBJECT, OFF(f_code), READONLY | RESTRICTED},
    {(char *)"f_builtins", T_OBJECT, OFF(f_builtins), READONLY | RESTRICTED},
    {(char *)"f_globals", T_OBJECT, OFF(f_globals), READONLY | RESTRICTED},
    {(char *)"f_lasti", T_INT, OFF(f_lasti), READONLY | RESTRICTED},
    {NULL}};

#if PYTHON_VERSION < 300

static PyObject *Nuitka_Frame_get_exc_traceback(struct Nuitka_FrameObject *frame) {
    PyObject *result = frame->m_frame.f_exc_traceback;

    if (result == NULL) {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_set_exc_traceback(struct Nuitka_FrameObject *frame, PyObject *traceback) {
    Py_XDECREF(frame->m_frame.f_exc_traceback);

    if (traceback == Py_None) {
        traceback = NULL;
    }

    frame->m_frame.f_exc_traceback = traceback;
    Py_XINCREF(traceback);

    return 0;
}

static PyObject *Nuitka_Frame_get_exc_type(struct Nuitka_FrameObject *frame) {
    PyObject *result;

    if (frame->m_frame.f_exc_type != NULL) {
        result = frame->m_frame.f_exc_type;
    } else {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_set_exc_type(struct Nuitka_FrameObject *frame, PyObject *exception_type) {
    PyObject *old = frame->m_frame.f_exc_type;

    if (exception_type == Py_None) {
        exception_type = NULL;
    }

    frame->m_frame.f_exc_type = exception_type;
    Py_XINCREF(frame->m_frame.f_exc_type);

    Py_XDECREF(old);

    return 0;
}

static PyObject *Nuitka_Frame_get_exc_value(struct Nuitka_FrameObject *frame) {
    PyObject *result;

    if (frame->m_frame.f_exc_value != NULL) {
        result = frame->m_frame.f_exc_value;
    } else {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_set_exc_value(struct Nuitka_FrameObject *frame, PyObject *exception_value) {
    PyObject *old = frame->m_frame.f_exc_value;

    if (exception_value == Py_None) {
        exception_value = NULL;
    }

    frame->m_frame.f_exc_value = exception_value;
    Py_XINCREF(exception_value);
    Py_XDECREF(old);

    return 0;
}

static PyObject *Nuitka_Frame_get_restricted(struct Nuitka_FrameObject *frame, void *closure) {
    Py_INCREF(Py_False);
    return Py_False;
}

#endif

static PyObject *Nuitka_Frame_getlocals(struct Nuitka_FrameObject *frame, void *closure) {
    if (frame->m_type_description == NULL) {
        if (frame->m_frame.f_locals == NULL) {
            frame->m_frame.f_locals = PyDict_New();
        }

        Py_INCREF(frame->m_frame.f_locals);
        return frame->m_frame.f_locals;
    } else {
        PyObject *result = PyDict_New();
        PyObject **varnames = &PyTuple_GET_ITEM(frame->m_frame.f_code->co_varnames, 0);

        char const *w = frame->m_type_description;
        char const *t = frame->m_locals_storage;

        while (*w != 0) {
            switch (*w) {
            case NUITKA_TYPE_DESCRIPTION_OBJECT:
            case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
                PyObject *value = *(PyObject **)t;

                if (value != NULL) {
                    PyDict_SetItem(result, *varnames, value);
                }

                t += sizeof(value);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *value = *(struct Nuitka_CellObject **)t;
                PyDict_SetItem(result, *varnames, value->ob_ref);
                t += sizeof(value);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_NULL: {
                t += sizeof(void *);
                break;
            }
            case NUITKA_TYPE_DESCRIPTION_BOOL: {
                int value = *(int *)t;
                t += sizeof(int);
                switch ((nuitka_bool)value) {
                case NUITKA_BOOL_TRUE: {
                    PyDict_SetItem(result, *varnames, Py_True);
                    break;
                }
                case NUITKA_BOOL_FALSE: {
                    PyDict_SetItem(result, *varnames, Py_False);
                    break;
                }
                default:
                    break;
                }
                break;
            }
            default:
                assert(false);
            }

            w += 1;
            varnames += 1;
        }

        return result;
    }
}

static PyObject *Nuitka_Frame_getlineno(PyFrameObject *frame, void *closure) { return PyInt_FromLong(frame->f_lineno); }

static PyObject *Nuitka_Frame_gettrace(PyFrameObject *frame, void *closure) {
    PyObject *result = frame->f_trace;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_settrace(PyFrameObject *frame, PyObject *v, void *closure) {
    PyErr_Format(PyExc_RuntimeError, "f_trace is not writable in Nuitka");
    return -1;
}

#if PYTHON_VERSION >= 370
static PyObject *Nuitka_Frame_gettracelines(PyFrameObject *frame, void *closure) {
    PyObject *result = Py_False;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_settracelines(PyFrameObject *frame, PyObject *v, void *closure) {
    PyErr_Format(PyExc_RuntimeError, "f_trace_lines is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Frame_gettraceopcodes(PyFrameObject *frame, void *closure) {
    PyObject *result = Py_False;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_settraceopcodes(PyFrameObject *frame, PyObject *v, void *closure) {
    PyErr_Format(PyExc_RuntimeError, "f_trace_opcodes is not writable in Nuitka");
    return -1;
}

#endif

static PyGetSetDef Nuitka_Frame_getsetlist[] = {
    {(char *)"f_locals", (getter)Nuitka_Frame_getlocals, NULL, NULL},
    {(char *)"f_lineno", (getter)Nuitka_Frame_getlineno, NULL, NULL},
    {(char *)"f_trace", (getter)Nuitka_Frame_gettrace, (setter)Nuitka_Frame_settrace, NULL},
#if PYTHON_VERSION < 300
    {(char *)"f_restricted", (getter)Nuitka_Frame_get_restricted, NULL, NULL},
    {(char *)"f_exc_traceback", (getter)Nuitka_Frame_get_exc_traceback, (setter)Nuitka_Frame_set_exc_traceback, NULL},
    {(char *)"f_exc_type", (getter)Nuitka_Frame_get_exc_type, (setter)Nuitka_Frame_set_exc_type, NULL},
    {(char *)"f_exc_value", (getter)Nuitka_Frame_get_exc_value, (setter)Nuitka_Frame_set_exc_value, NULL},
#endif
#if PYTHON_VERSION >= 370
    {(char *)"f_trace_lines", (getter)Nuitka_Frame_gettracelines, (setter)Nuitka_Frame_settracelines, NULL},
    {(char *)"f_trace_opcodes", (getter)Nuitka_Frame_gettraceopcodes, (setter)Nuitka_Frame_settraceopcodes, NULL},
#endif
    {NULL}};

// tp_repr slot, decide how a function shall be output
static PyObject *Nuitka_Frame_tp_repr(struct Nuitka_FrameObject *nuitka_frame) {
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
#if PYTHON_VERSION >= 370
        "<compiled_frame at %p, file %R, line %d, code %S>", nuitka_frame, nuitka_frame->m_frame.f_code->co_filename,
        nuitka_frame->m_frame.f_lineno, nuitka_frame->m_frame.f_code->co_name
#elif _DEBUG_FRAME || _DEBUG_REFRAME || _DEBUG_EXCEPTIONS
        "<compiled_frame object for %s at %p>", Nuitka_String_AsString(nuitka_frame->m_frame.f_code->co_name),
        nuitka_frame
#else
        "<compiled_frame object at %p>",
        nuitka_frame
#endif
    );
}

static void Nuitka_Frame_tp_clear(struct Nuitka_FrameObject *frame) {
    if (frame->m_type_description) {
        char const *w = frame->m_type_description;
        char const *t = frame->m_locals_storage;

        while (*w != 0) {
            switch (*w) {
            case NUITKA_TYPE_DESCRIPTION_OBJECT:
            case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
                PyObject *value = *(PyObject **)t;
                Py_XDECREF(value);

                t += sizeof(value);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *value = *(struct Nuitka_CellObject **)t;
                Py_DECREF(value);

                t += sizeof(value);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_NULL: {
                t += sizeof(void *);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_BOOL: {
                t += sizeof(int);

                break;
            }
            default:
                assert(false);
            }

            w += 1;
        }

        frame->m_type_description = NULL;
    }
}

void Nuitka_Frame_ReleaseLocals(struct Nuitka_FrameObject *frame) { Nuitka_Frame_tp_clear(frame); }

#define MAX_FRAME_FREE_LIST_COUNT 100
static struct Nuitka_FrameObject *free_list_frames = NULL;
static int free_list_frames_count = 0;

static void Nuitka_Frame_tp_dealloc(struct Nuitka_FrameObject *nuitka_frame) {
#ifndef __NUITKA_NO_ASSERT__
    // Save the current exception, if any, we must to not corrupt it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED(&save_exception_type, &save_exception_value, &save_exception_tb);
    RESTORE_ERROR_OCCURRED(save_exception_type, save_exception_value, save_exception_tb);
#endif

    Nuitka_GC_UnTrack(nuitka_frame);

    PyFrameObject *frame = &nuitka_frame->m_frame;

    Py_XDECREF(frame->f_back);
    Py_DECREF(frame->f_builtins);
    Py_DECREF(frame->f_globals);
    Py_XDECREF(frame->f_locals);

#if PYTHON_VERSION < 370
    Py_XDECREF(frame->f_exc_type);
    Py_XDECREF(frame->f_exc_value);
    Py_XDECREF(frame->f_exc_traceback);
#endif

    Nuitka_Frame_tp_clear(nuitka_frame);

    releaseToFreeList(free_list_frames, nuitka_frame, MAX_FRAME_FREE_LIST_COUNT);

#ifndef __NUITKA_NO_ASSERT__
    PyThreadState *tstate = PyThreadState_GET();

    assert(tstate->curexc_type == save_exception_type);
    assert(tstate->curexc_value == save_exception_value);
    assert((PyTracebackObject *)tstate->curexc_traceback == save_exception_tb);
#endif
}

static int Nuitka_Frame_tp_traverse(struct Nuitka_FrameObject *frame, visitproc visit, void *arg) {
    Py_VISIT(frame->m_frame.f_back);
    // Py_VISIT( frame->f_code );
    Py_VISIT(frame->m_frame.f_builtins);
    Py_VISIT(frame->m_frame.f_globals);
    // Py_VISIT( frame->f_locals );
    // TODO: Traverse attached locals too.

#if PYTHON_VERSION < 370
    Py_VISIT(frame->m_frame.f_exc_type);
    Py_VISIT(frame->m_frame.f_exc_value);
    Py_VISIT(frame->m_frame.f_exc_traceback);
#endif

    return 0;
}

#if PYTHON_VERSION >= 340

extern PyObject *Nuitka_Generator_close(struct Nuitka_GeneratorObject *generator, PyObject *args);
#if PYTHON_VERSION >= 350
extern PyObject *Nuitka_Coroutine_close(struct Nuitka_CoroutineObject *coroutine, PyObject *args);
#endif
#if PYTHON_VERSION >= 360
extern PyObject *Nuitka_Asyncgen_close(struct Nuitka_AsyncgenObject *asyncgen, PyObject *args);
#endif

static PyObject *Nuitka_Frame_clear(struct Nuitka_FrameObject *frame) {
    if (frame->m_frame.f_executing) {
        PyErr_Format(PyExc_RuntimeError, "cannot clear an executing frame");

        return NULL;
    }

#if PYTHON_VERSION >= 340
    // For frames that are closed, we also need to close the generator.
    if (frame->m_frame.f_gen != NULL) {
        Py_INCREF(frame);

        CHECK_OBJECT(frame->m_frame.f_gen);
        PyObject *f_gen = frame->m_frame.f_gen;

        PyObject *close_result;
        if (Nuitka_Generator_Check(frame->m_frame.f_gen)) {
            struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)frame->m_frame.f_gen;
            frame->m_frame.f_gen = NULL;

            close_result = Nuitka_Generator_close(generator, NULL);
        }
#if PYTHON_VERSION >= 350
        else if (Nuitka_Coroutine_Check(frame->m_frame.f_gen)) {
            struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)frame->m_frame.f_gen;
            frame->m_frame.f_gen = NULL;

            close_result = Nuitka_Coroutine_close(coroutine, NULL);
        }
#endif
#if PYTHON_VERSION >= 360
        else if (Nuitka_Asyncgen_Check(frame->m_frame.f_gen)) {
            struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)frame->m_frame.f_gen;
            frame->m_frame.f_gen = NULL;

            close_result = Nuitka_Asyncgen_close(asyncgen, NULL);
        }
#endif
        else {
            // Compiled frames should only have our types.
            assert(false);

            frame->m_frame.f_gen = NULL;

            close_result = Py_None;
            Py_INCREF(close_result);
        }

        if (unlikely(close_result == NULL)) {
            PyErr_WriteUnraisable(f_gen);
        } else {
            Py_DECREF(close_result);
        }

        Py_DECREF(frame);
    }
#endif

    Nuitka_Frame_tp_clear(frame);

    Py_RETURN_NONE;
}

#endif

static PyObject *Nuitka_Frame_sizeof(struct Nuitka_FrameObject *frame) {
    return PyInt_FromSsize_t(sizeof(struct Nuitka_FrameObject) + Py_SIZE(frame));
}

static PyMethodDef Nuitka_Frame_methods[] = {
#if PYTHON_VERSION >= 340
    {"clear", (PyCFunction)Nuitka_Frame_clear, METH_NOARGS, "F.clear(): clear most references held by the frame"},
#endif
    {"__sizeof__", (PyCFunction)Nuitka_Frame_sizeof, METH_NOARGS, "F.__sizeof__() -> size of F in memory, in bytes"},
    {NULL, NULL}};

PyTypeObject Nuitka_Frame_Type = {
    PyVarObject_HEAD_INIT(NULL, 0) "compiled_frame",
    sizeof(struct Nuitka_FrameObject),
    1,
    (destructor)Nuitka_Frame_tp_dealloc,     // tp_dealloc
    0,                                       // tp_print
    0,                                       // tp_getattr
    0,                                       // tp_setattr
    0,                                       // tp_compare
    (reprfunc)Nuitka_Frame_tp_repr,          // tp_repr
    0,                                       // tp_as_number
    0,                                       // tp_as_sequence
    0,                                       // tp_as_mapping
    0,                                       // tp_hash
    0,                                       // tp_call
    0,                                       // tp_str
    PyObject_GenericGetAttr,                 // tp_getattro
    PyObject_GenericSetAttr,                 // tp_setattro
    0,                                       // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, // tp_flags
    0,                                       // tp_doc
    (traverseproc)Nuitka_Frame_tp_traverse,  // tp_traverse
    (inquiry)Nuitka_Frame_tp_clear,          // tp_clear
    0,                                       // tp_richcompare
    0,                                       // tp_weaklistoffset
    0,                                       // tp_iter
    0,                                       // tp_iternext
    Nuitka_Frame_methods,                    // tp_methods
    Nuitka_Frame_memberlist,                 // tp_members
    Nuitka_Frame_getsetlist,                 // tp_getset
    0,                                       // tp_base
    0,                                       // tp_dict
};

void _initCompiledFrameType(void) {
    PyType_Ready(&Nuitka_Frame_Type);

    // These are to be used interchangeably. Make sure that's true.
    assert(offsetof(struct Nuitka_FrameObject, m_frame.f_localsplus) == offsetof(PyFrameObject, f_localsplus));
}

extern PyObject *const_str_plain___module__;

static struct Nuitka_FrameObject *MAKE_FRAME(PyCodeObject *code, PyObject *module, bool is_module,
                                             Py_ssize_t locals_size) {
    assertCodeObject(code);

    PyObject *globals = ((PyModuleObject *)module)->md_dict;
    assert(PyDict_Check(globals));

    struct Nuitka_FrameObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_frames, struct Nuitka_FrameObject, Nuitka_Frame_Type, locals_size);

    result->m_type_description = NULL;

    PyFrameObject *frame = &result->m_frame;

    frame->f_code = code;

    frame->f_trace = Py_None;

#if PYTHON_VERSION < 370
    frame->f_exc_type = NULL;
    frame->f_exc_value = NULL;
    frame->f_exc_traceback = NULL;
#else
    frame->f_trace_lines = 0;
    frame->f_trace_opcodes = 0;
#endif

    Py_INCREF(dict_builtin);
    frame->f_builtins = (PyObject *)dict_builtin;

    frame->f_back = NULL;

    Py_INCREF(globals);
    frame->f_globals = globals;

    if (likely((code->co_flags & CO_OPTIMIZED) == CO_OPTIMIZED)) {
        frame->f_locals = NULL;
    } else if (is_module) {
        Py_INCREF(globals);
        frame->f_locals = globals;
    } else {
        frame->f_locals = PyDict_New();

        if (unlikely(frame->f_locals == NULL)) {
            Py_DECREF(result);

            return NULL;
        }

        PyDict_SetItem(frame->f_locals, const_str_plain___module__, MODULE_NAME(module));
    }

#if PYTHON_VERSION < 340
    frame->f_tstate = PyThreadState_GET();
#endif

    frame->f_lasti = -1;
    frame->f_lineno = code->co_firstlineno;
    frame->f_iblock = 0;

#if PYTHON_VERSION >= 340
    frame->f_gen = NULL;
    frame->f_executing = 0;
#endif

    Nuitka_GC_Track(result);
    return result;
}

struct Nuitka_FrameObject *MAKE_MODULE_FRAME(PyCodeObject *code, PyObject *module) {
    return MAKE_FRAME(code, module, true, 0);
}

struct Nuitka_FrameObject *MAKE_FUNCTION_FRAME(PyCodeObject *code, PyObject *module, Py_ssize_t locals_size) {
    return MAKE_FRAME(code, module, false, locals_size);
}

extern PyObject *const_str_empty;
extern PyObject *const_bytes_empty;

#if PYTHON_VERSION < 300
PyCodeObject *MAKE_CODEOBJ(PyObject *filename, PyObject *function_name, int line, PyObject *argnames, int arg_count,
                           int flags)
#else
PyCodeObject *MAKE_CODEOBJ(PyObject *filename, PyObject *function_name, int line, PyObject *argnames, int arg_count,
                           int kw_only_count, int flags)
#endif
{
    CHECK_OBJECT(filename);
    assert(Nuitka_String_Check(filename));
    CHECK_OBJECT(function_name);
    assert(Nuitka_String_Check(function_name));
    CHECK_OBJECT(argnames);
    assert(PyTuple_Check(argnames));

    // The PyCode_New has funny code that interns, mutating the tuple that owns
    // it. Really serious non-immutable shit. We have triggered that changes
    // behind our back in the past.
#ifndef __NUITKA_NO_ASSERT__
    Py_hash_t hash = DEEP_HASH(argnames);
#endif

    // Not using PyCode_NewEmpty, it doesn't given us much beyond this
    // and is not available for Python2.
    PyCodeObject *result = PyCode_New(arg_count, // argcount
#if PYTHON_VERSION >= 300
                                      kw_only_count, // kw-only count
#endif
                                      0,     // nlocals
                                      0,     // stacksize
                                      flags, // flags
#if PYTHON_VERSION < 300
                                      const_str_empty, // code (bytecode)
#else
                                      const_bytes_empty, // code (bytecode)
#endif
                                      const_tuple_empty, // consts (we are not going to be compatible)
                                      const_tuple_empty, // names (we are not going to be compatible)
                                      argnames,          // varnames (we are not going to be compatible)
                                      const_tuple_empty, // freevars (we are not going to be compatible)
                                      const_tuple_empty, // cellvars (we are not going to be compatible)
                                      filename,          // filename
                                      function_name,     // name
                                      line,              // firstlineno (offset of the code object)
#if PYTHON_VERSION < 300
                                      const_str_empty // lnotab (table to translate code object)
#else
                                      const_bytes_empty  // lnotab (table to translate code object)
#endif
    );

    assert(DEEP_HASH(argnames) == hash);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

void Nuitka_Frame_AttachLocals(struct Nuitka_FrameObject *frame, char const *type_description, ...) {
    assert(frame->m_type_description == NULL);

    // TODO: Do not call this if there is nothing to do. Instead make all the
    // places handle NULL pointer.
    if (type_description == NULL)
        type_description = "";

    frame->m_type_description = type_description;

    char const *w = type_description;
    char *t = frame->m_locals_storage;

    va_list(ap);
    va_start(ap, type_description);

    while (*w != 0) {
        switch (*w) {
        case NUITKA_TYPE_DESCRIPTION_OBJECT: {
            PyObject *value = va_arg(ap, PyObject *);
            memcpy(t, &value, sizeof(value));
            Py_XINCREF(value);
            t += sizeof(value);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
            /* We store the pointed object only. */
            PyObject **value = va_arg(ap, PyObject **);
            memcpy(t, value, sizeof(PyObject *));
            Py_XINCREF(*value);
            t += sizeof(value);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_CELL: {
            struct Nuitka_CellObject *value = va_arg(ap, struct Nuitka_CellObject *);
            CHECK_OBJECT(value);

            memcpy(t, &value, sizeof(value));
            Py_INCREF(value);
            t += sizeof(value);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_NULL: {
            void *value = va_arg(ap, struct Nuitka_CellObject *);
            t += sizeof(value);
            break;
        }
        case NUITKA_TYPE_DESCRIPTION_BOOL: {
            int value = va_arg(ap, int);
            memcpy(t, &value, sizeof(int));
            t += sizeof(value);
            break;
        }
        default:
            assert(false);
        }

        w += 1;
    }

    va_end(ap);
    assert(t - frame->m_locals_storage <= Py_SIZE(frame));
}
