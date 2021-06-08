//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

// For reporting about reference counts per type.
#if _DEBUG_REFCOUNTS
int count_active_Nuitka_Frame_Type = 0;
int count_allocated_Nuitka_Frame_Type = 0;
int count_released_Nuitka_Frame_Type = 0;
#endif

// For reporting about frame cache usage
#if _DEBUG_REFCOUNTS
int count_active_frame_cache_instances = 0;
int count_allocated_frame_cache_instances = 0;
int count_released_frame_cache_instances = 0;
int count_hit_frame_cache_instances = 0;
#endif

#define OFF(x) offsetof(PyFrameObject, x)

static PyMemberDef Nuitka_Frame_memberlist[] = {
    {(char *)"f_back", T_OBJECT, OFF(f_back), READONLY | RESTRICTED},
    {(char *)"f_code", T_OBJECT, OFF(f_code), READONLY | RESTRICTED},
    {(char *)"f_builtins", T_OBJECT, OFF(f_builtins), READONLY | RESTRICTED},
    {(char *)"f_globals", T_OBJECT, OFF(f_globals), READONLY | RESTRICTED},
    {(char *)"f_lasti", T_INT, OFF(f_lasti), READONLY | RESTRICTED},
    {NULL}};

#if PYTHON_VERSION < 0x300

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
                CHECK_OBJECT_X(value);

                if (value != NULL) {
                    PyDict_SetItem(result, *varnames, value);
                }

                t += sizeof(PyObject *);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *value = *(struct Nuitka_CellObject **)t;
                assert(Nuitka_Cell_Check((PyObject *)value));
                CHECK_OBJECT(value);

                if (value->ob_ref != NULL) {
                    PyDict_SetItem(result, *varnames, value->ob_ref);
                }

                t += sizeof(struct Nuitka_CellObject *);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_NULL: {
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
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "f_trace is not writable in Nuitka");
    return -1;
}

#if PYTHON_VERSION >= 0x370
static PyObject *Nuitka_Frame_gettracelines(PyFrameObject *frame, void *closure) {
    PyObject *result = Py_False;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_settracelines(PyFrameObject *frame, PyObject *v, void *closure) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "f_trace_lines is not writable in Nuitka");
    return -1;
}

static PyObject *Nuitka_Frame_gettraceopcodes(PyFrameObject *frame, void *closure) {
    PyObject *result = Py_False;
    Py_INCREF(result);
    return result;
}

static int Nuitka_Frame_settraceopcodes(PyFrameObject *frame, PyObject *v, void *closure) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "f_trace_opcodes is not writable in Nuitka");
    return -1;
}

#endif

static PyGetSetDef Nuitka_Frame_getsetlist[] = {
    {(char *)"f_locals", (getter)Nuitka_Frame_getlocals, NULL, NULL},
    {(char *)"f_lineno", (getter)Nuitka_Frame_getlineno, NULL, NULL},
    {(char *)"f_trace", (getter)Nuitka_Frame_gettrace, (setter)Nuitka_Frame_settrace, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"f_restricted", (getter)Nuitka_Frame_get_restricted, NULL, NULL},
    {(char *)"f_exc_traceback", (getter)Nuitka_Frame_get_exc_traceback, (setter)Nuitka_Frame_set_exc_traceback, NULL},
    {(char *)"f_exc_type", (getter)Nuitka_Frame_get_exc_type, (setter)Nuitka_Frame_set_exc_type, NULL},
    {(char *)"f_exc_value", (getter)Nuitka_Frame_get_exc_value, (setter)Nuitka_Frame_set_exc_value, NULL},
#endif
#if PYTHON_VERSION >= 0x370
    {(char *)"f_trace_lines", (getter)Nuitka_Frame_gettracelines, (setter)Nuitka_Frame_settracelines, NULL},
    {(char *)"f_trace_opcodes", (getter)Nuitka_Frame_gettraceopcodes, (setter)Nuitka_Frame_settraceopcodes, NULL},
#endif
    {NULL}};

// tp_repr slot, decide how a function shall be output
static PyObject *Nuitka_Frame_tp_repr(struct Nuitka_FrameObject *nuitka_frame) {
#if PYTHON_VERSION < 0x300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
#if PYTHON_VERSION >= 0x370
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
                CHECK_OBJECT_X(value);

                Py_XDECREF(value);

                t += sizeof(PyObject *);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *value = *(struct Nuitka_CellObject **)t;
                assert(Nuitka_Cell_Check((PyObject *)value));
                CHECK_OBJECT(value);

                Py_DECREF(value);

                t += sizeof(struct Nuitka_CellObject *);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_NULL: {
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

#define MAX_FRAME_FREE_LIST_COUNT 100
static struct Nuitka_FrameObject *free_list_frames = NULL;
static int free_list_frames_count = 0;

static void Nuitka_Frame_tp_dealloc(struct Nuitka_FrameObject *nuitka_frame) {
#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Frame_Type -= 1;
    count_released_Nuitka_Frame_Type += 1;
#endif

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

#if PYTHON_VERSION < 0x370
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
    // Py_VISIT(frame->f_code);
    Py_VISIT(frame->m_frame.f_builtins);
    Py_VISIT(frame->m_frame.f_globals);
    // Py_VISIT(frame->f_locals);

#if PYTHON_VERSION < 0x370
    Py_VISIT(frame->m_frame.f_exc_type);
    Py_VISIT(frame->m_frame.f_exc_value);
    Py_VISIT(frame->m_frame.f_exc_traceback);
#endif

    // Traverse attached locals too.
    char const *w = frame->m_type_description;
    char const *t = frame->m_locals_storage;

    while (w != NULL && *w != 0) {
        switch (*w) {
        case NUITKA_TYPE_DESCRIPTION_OBJECT:
        case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
            PyObject *value = *(PyObject **)t;
            CHECK_OBJECT_X(value);

            Py_VISIT(value);
            t += sizeof(PyObject *);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_CELL: {
            struct Nuitka_CellObject *value = *(struct Nuitka_CellObject **)t;
            assert(Nuitka_Cell_Check((PyObject *)value));
            CHECK_OBJECT(value);

            Py_VISIT(value);

            t += sizeof(struct Nuitka_CellObject *);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_NULL: {
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

    return 0;
}

#if PYTHON_VERSION >= 0x340

static PyObject *Nuitka_Frame_clear(struct Nuitka_FrameObject *frame) {
    if (frame->m_frame.f_executing) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_RuntimeError, "cannot clear an executing frame");

        return NULL;
    }

#if PYTHON_VERSION >= 0x340
    // For frames that are closed, we also need to close the generator.
    if (frame->m_frame.f_gen != NULL) {
        Py_INCREF(frame);

        CHECK_OBJECT(frame->m_frame.f_gen);
        PyObject *f_gen = frame->m_frame.f_gen;

        bool close_exception;

        if (Nuitka_Generator_Check(frame->m_frame.f_gen)) {
            struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)frame->m_frame.f_gen;
            frame->m_frame.f_gen = NULL;

            close_exception = !_Nuitka_Generator_close(generator);
        }
#if PYTHON_VERSION >= 0x350
        else if (Nuitka_Coroutine_Check(frame->m_frame.f_gen)) {
            struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)frame->m_frame.f_gen;
            frame->m_frame.f_gen = NULL;

            close_exception = !_Nuitka_Coroutine_close(coroutine);
        }
#endif
#if PYTHON_VERSION >= 0x360
        else if (Nuitka_Asyncgen_Check(frame->m_frame.f_gen)) {
            struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)frame->m_frame.f_gen;
            frame->m_frame.f_gen = NULL;

            close_exception = !_Nuitka_Asyncgen_close(asyncgen);
        }
#endif
        else {
            // Compiled frames should only have our types, so this ought to not happen.
            assert(false);

            frame->m_frame.f_gen = NULL;
            close_exception = false;
        }

        if (unlikely(close_exception)) {
            PyErr_WriteUnraisable(f_gen);
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
#if PYTHON_VERSION >= 0x340
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

static struct Nuitka_FrameObject *MAKE_FRAME(PyCodeObject *code, PyObject *module, bool is_module,
                                             Py_ssize_t locals_size) {
    assertCodeObject(code);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Frame_Type += 1;
    count_allocated_Nuitka_Frame_Type += 1;
#endif

    PyObject *globals = ((PyModuleObject *)module)->md_dict;
    assert(PyDict_Check(globals));

    struct Nuitka_FrameObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_frames, struct Nuitka_FrameObject, Nuitka_Frame_Type, locals_size);

    result->m_type_description = NULL;

    PyFrameObject *frame = &result->m_frame;

    frame->f_code = code;

    frame->f_trace = Py_None;

#if PYTHON_VERSION < 0x370
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

        PyDict_SetItem(frame->f_locals, const_str_plain___module__, MODULE_NAME0(module));
    }

#if PYTHON_VERSION < 0x340
    frame->f_tstate = PyThreadState_GET();
#endif

    frame->f_lasti = -1;
    frame->f_lineno = code->co_firstlineno;
    frame->f_iblock = 0;

#if PYTHON_VERSION >= 0x340
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

// This is the backend of MAKE_CODEOBJ macro.
PyCodeObject *makeCodeObject(PyObject *filename, int line, int flags, PyObject *function_name, PyObject *argnames,
                             PyObject *freevars, int arg_count
#if PYTHON_VERSION >= 0x300
                             ,
                             int kw_only_count
#endif
#if PYTHON_VERSION >= 0x380
                             ,
                             int pos_only_count
#endif
) {
    CHECK_OBJECT(filename);
    assert(Nuitka_String_CheckExact(filename));
    CHECK_OBJECT(function_name);
    assert(Nuitka_String_CheckExact(function_name));

    if (argnames == NULL) {
        argnames = const_tuple_empty;
    }
    CHECK_OBJECT(argnames);
    assert(PyTuple_Check(argnames));

    if (freevars == NULL) {
        freevars = const_tuple_empty;
    }
    CHECK_OBJECT(freevars);
    assert(PyTuple_Check(freevars));

    // The PyCode_New has funny code that interns, mutating the tuple that owns
    // it. Really serious non-immutable shit. We have triggered that changes
    // behind our back in the past.
#ifndef __NUITKA_NO_ASSERT__
    Py_hash_t hash = DEEP_HASH(argnames);
#endif

#if PYTHON_VERSION < 0x300
    PyObject *code = const_str_empty;
    PyObject *lnotab = const_str_empty;
#else
    PyObject *code = const_bytes_empty;
    PyObject *lnotab = const_bytes_empty;
#endif

    // Not using PyCode_NewEmpty, it doesn't given us much beyond this
    // and is not available for Python2.
#if PYTHON_VERSION >= 0x380
    PyCodeObject *result = PyCode_NewWithPosOnlyArgs(arg_count, // argcount
#else
    PyCodeObject *result = PyCode_New(arg_count, // argcount
#endif
#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION >= 0x380
                                                     pos_only_count, // kw-only count
#endif
                                                     kw_only_count, // kw-only count
#endif
                                                     0,                 // nlocals
                                                     0,                 // stacksize
                                                     flags,             // flags
                                                     code,              // code (bytecode)
                                                     const_tuple_empty, // consts (we are not going to be compatible)
                                                     const_tuple_empty, // names (we are not going to be compatible)
                                                     argnames,          // varnames (we are not going to be compatible)
                                                     freevars,          // freevars
                                                     const_tuple_empty, // cellvars (we are not going to be compatible)
                                                     filename,          // filename
                                                     function_name,     // name
                                                     line,              // firstlineno (offset of the code object)
                                                     lnotab             // lnotab (table to translate code object)
    );

    assert(DEEP_HASH(argnames) == hash);

    CHECK_OBJECT(result);
    return result;
}

void Nuitka_Frame_AttachLocals(struct Nuitka_FrameObject *frame, char const *type_description, ...) {
    assert(frame->m_type_description == NULL);

    // TODO: Do not call this if there is nothing to do. Instead make all the
    // places handle NULL pointer and recognize that there is nothing to do.
    // assert(type_description != NULL && assert(strlen(type_description)>0));
    if (type_description == NULL) {
        type_description = "";
    }

    frame->m_type_description = type_description;

    char const *w = type_description;
    char *t = frame->m_locals_storage;

    va_list(ap);
    va_start(ap, type_description);

    while (*w != 0) {
        switch (*w) {
        case NUITKA_TYPE_DESCRIPTION_OBJECT: {
            PyObject *value = va_arg(ap, PyObject *);
            memcpy(t, &value, sizeof(PyObject *));
            Py_XINCREF(value);
            t += sizeof(PyObject *);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
            /* Note: We store the pointed object only, so this is only
               a shortcut for the calling side. */
            PyObject **value = va_arg(ap, PyObject **);
            CHECK_OBJECT_X(*value);

            memcpy(t, value, sizeof(PyObject *));

            Py_XINCREF(*value);
            t += sizeof(PyObject *);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_CELL: {
            struct Nuitka_CellObject *value = va_arg(ap, struct Nuitka_CellObject *);
            assert(Nuitka_Cell_Check((PyObject *)value));
            CHECK_OBJECT(value);
            CHECK_OBJECT_X(value->ob_ref);

            memcpy(t, &value, sizeof(struct Nuitka_CellObject *));
            Py_INCREF(value);

            t += sizeof(struct Nuitka_CellObject *);

            break;
        }
        case NUITKA_TYPE_DESCRIPTION_NULL: {
            NUITKA_MAY_BE_UNUSED void *value = va_arg(ap, struct Nuitka_CellObject *);

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

// Make a dump of the active frame stack. For debugging purposes only.
void dumpFrameStack(void) {
    PyObject *saved_exception_type, *saved_exception_value;
    PyTracebackObject *saved_exception_tb;

    FETCH_ERROR_OCCURRED(&saved_exception_type, &saved_exception_value, &saved_exception_tb);

    PyFrameObject *current = PyThreadState_GET()->frame;
    int total = 0;

    while (current) {
        total++;
        current = current->f_back;
    }

    current = PyThreadState_GET()->frame;

    PRINT_STRING(">--------->\n");

    while (current) {
        PyObject *current_repr = PyObject_Str((PyObject *)current);
        PyObject *code_repr = PyObject_Str((PyObject *)current->f_code);

        PRINT_FORMAT("Frame stack %d: %s %d %s\n", total--, Nuitka_String_AsString(current_repr), Py_REFCNT(current),
                     Nuitka_String_AsString(code_repr));

        Py_DECREF(current_repr);
        Py_DECREF(code_repr);

        current = current->f_back;
    }

    PRINT_STRING(">---------<\n");

    RESTORE_ERROR_OCCURRED(saved_exception_type, saved_exception_value, saved_exception_tb);
}
