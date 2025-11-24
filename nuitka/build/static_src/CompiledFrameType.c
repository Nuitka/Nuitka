//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifdef __IDE_ONLY__
#include "nuitka/freelists.h"
#include "nuitka/prelude.h"
#include <structmember.h>
#endif

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

#if PYTHON_VERSION < 0x3b0
static PyMemberDef Nuitka_Frame_members[] = {
    {(char *)"f_back", T_OBJECT, offsetof(PyFrameObject, f_back), READONLY | RESTRICTED},
    {(char *)"f_code", T_OBJECT, offsetof(PyFrameObject, f_code), READONLY | RESTRICTED},
    {(char *)"f_builtins", T_OBJECT, offsetof(PyFrameObject, f_builtins), READONLY | RESTRICTED},
    {(char *)"f_globals", T_OBJECT, offsetof(PyFrameObject, f_globals), READONLY | RESTRICTED},
    {(char *)"f_lasti", T_INT, offsetof(PyFrameObject, f_lasti), READONLY | RESTRICTED},
    {NULL}};

#else
#define Nuitka_Frame_members 0
#endif

#if PYTHON_VERSION < 0x300

static PyObject *_Nuitka_Frame_get_exc_traceback(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;
    PyObject *result = frame->m_frame.f_exc_traceback;

    if (result == NULL) {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int _Nuitka_Frame_set_exc_traceback(PyObject *self, PyObject *traceback, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;
    Py_XDECREF(frame->m_frame.f_exc_traceback);

    if (traceback == Py_None) {
        traceback = NULL;
    }

    frame->m_frame.f_exc_traceback = traceback;
    Py_XINCREF(traceback);

    return 0;
}

static PyObject *_Nuitka_Frame_get_exc_type(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    PyObject *result;
    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;

    if (frame->m_frame.f_exc_type != NULL) {
        result = frame->m_frame.f_exc_type;
    } else {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int _Nuitka_Frame_set_exc_type(PyObject *self, PyObject *exception_type, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;
    PyObject *old = frame->m_frame.f_exc_type;

    if (exception_type == Py_None) {
        exception_type = NULL;
    }

    frame->m_frame.f_exc_type = exception_type;
    Py_XINCREF(frame->m_frame.f_exc_type);

    Py_XDECREF(old);

    return 0;
}

static PyObject *_Nuitka_Frame_get_exc_value(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    PyObject *result;
    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;

    if (frame->m_frame.f_exc_value != NULL) {
        result = frame->m_frame.f_exc_value;
    } else {
        result = Py_None;
    }

    Py_INCREF(result);
    return result;
}

static int _Nuitka_Frame_set_exc_value(PyObject *self, PyObject *exception_value, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;
    PyObject *old = frame->m_frame.f_exc_value;

    if (exception_value == Py_None) {
        exception_value = NULL;
    }

    frame->m_frame.f_exc_value = exception_value;
    Py_XINCREF(exception_value);
    Py_XDECREF(old);

    return 0;
}

static PyObject *_Nuitka_Frame_get_restricted(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    Py_INCREF_IMMORTAL(Py_False);
    return Py_False;
}

#endif

static PyObject *_Nuitka_Frame_get_locals(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    NUITKA_MAY_BE_UNUSED PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_FrameObject *nuitka_frame = (struct Nuitka_FrameObject *)self;
    if (nuitka_frame->m_type_description == NULL) {
#if PYTHON_VERSION < 0x3b0
        PyFrameObject *locals_owner = &nuitka_frame->m_frame;
#else
        _PyInterpreterFrame *locals_owner = &nuitka_frame->m_interpreter_frame;
#endif

        if (locals_owner->f_locals == NULL) {
            locals_owner->f_locals = MAKE_DICT_EMPTY(tstate);
        }

        Py_INCREF(locals_owner->f_locals);
        return locals_owner->f_locals;
    } else {
        PyObject *result = MAKE_DICT_EMPTY(tstate);
        PyObject **var_names = Nuitka_GetCodeVarNames(Nuitka_GetFrameCodeObject(nuitka_frame));

        char const *w = nuitka_frame->m_type_description;
        char const *t = nuitka_frame->m_locals_storage;

        while (*w != 0) {
            switch (*w) {
            case NUITKA_TYPE_DESCRIPTION_OBJECT:
            case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR: {
                PyObject *value = *(PyObject **)t;
                CHECK_OBJECT_X(value);

                if (value != NULL) {
                    DICT_SET_ITEM(result, *var_names, value);
                }

                t += sizeof(PyObject *);

                break;
            }
            case NUITKA_TYPE_DESCRIPTION_CELL: {
                struct Nuitka_CellObject *value = *(struct Nuitka_CellObject **)t;
                assert(Nuitka_Cell_Check((PyObject *)value));
                CHECK_OBJECT(value);

                if (value->ob_ref != NULL) {
                    DICT_SET_ITEM(result, *var_names, value->ob_ref);
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
                    DICT_SET_ITEM(result, *var_names, Py_True);
                    break;
                }
                case NUITKA_BOOL_FALSE: {
                    DICT_SET_ITEM(result, *var_names, Py_False);
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
            var_names += 1;
        }

        return result;
    }
}

static PyObject *_Nuitka_Frame_get_lineno(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;
    return Nuitka_PyInt_FromLong(frame->m_frame.f_lineno);
}

static PyObject *_Nuitka_Frame_get_trace(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    struct Nuitka_FrameObject *frame = (struct Nuitka_FrameObject *)self;
    PyObject *result = frame->m_frame.f_trace;
    Py_INCREF(result);
    return result;
}

static int _Nuitka_Frame_set_trace(PyObject *self, PyObject *value, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));
#if !defined(_NUITKA_DEPLOYMENT_MODE) && !defined(_NUITKA_NO_DEPLOYMENT_FRAME_USELESS_SET_TRACE)
    if (value == Py_None) {
        return 0;
    } else {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(
            tstate, PyExc_RuntimeError,
            "f_trace is not writable in Nuitka, ignore with '--no-deployment-flag=frame-useless-set-trace'");
        return -1;
    }
#else
    return 0;
#endif
}

#if PYTHON_VERSION >= 0x370
static PyObject *_Nuitka_Frame_get_trace_lines(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    PyObject *result = Py_False;
    Py_INCREF_IMMORTAL(result);
    return result;
}

static int _Nuitka_Frame_set_trace_lines(PyObject *self, PyObject *value, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "f_trace_lines is not writable in Nuitka");
    return -1;
}

static PyObject *_Nuitka_Frame_get_trace_opcodes(PyObject *self, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    PyObject *result = Py_False;
    Py_INCREF_IMMORTAL(result);
    return result;
}

static int _Nuitka_Frame_set_trace_opcodes(PyObject *self, PyObject *value, void *data) {
    assert(Nuitka_Frame_CheckExact(self));
    CHECK_OBJECT(self);
    assert(_PyObject_GC_IS_TRACKED(self));

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "f_trace_opcodes is not writable in Nuitka");
    return -1;
}
#endif

static PyGetSetDef Nuitka_Frame_tp_getset[] = {
    {(char *)"f_locals", _Nuitka_Frame_get_locals, NULL, NULL},
    {(char *)"f_lineno", _Nuitka_Frame_get_lineno, NULL, NULL},
    {(char *)"f_trace", _Nuitka_Frame_get_trace, _Nuitka_Frame_set_trace, NULL},
#if PYTHON_VERSION < 0x300
    {(char *)"f_restricted", _Nuitka_Frame_get_restricted, NULL, NULL},
    {(char *)"f_exc_traceback", _Nuitka_Frame_get_exc_traceback, _Nuitka_Frame_set_exc_traceback, NULL},
    {(char *)"f_exc_type", _Nuitka_Frame_get_exc_type, _Nuitka_Frame_set_exc_type, NULL},
    {(char *)"f_exc_value", _Nuitka_Frame_get_exc_value, _Nuitka_Frame_set_exc_value, NULL},
#endif
#if PYTHON_VERSION >= 0x370
    {(char *)"f_trace_lines", _Nuitka_Frame_get_trace_lines, _Nuitka_Frame_set_trace_lines, NULL},
    {(char *)"f_trace_opcodes", _Nuitka_Frame_get_trace_opcodes, _Nuitka_Frame_set_trace_opcodes, NULL},
#endif
    {NULL}};

// tp_repr slot, decide how a function shall be output
static PyObject *Nuitka_Frame_tp_repr(struct Nuitka_FrameObject *nuitka_frame) {
    assert(Nuitka_Frame_CheckExact((PyObject *)nuitka_frame));
    CHECK_OBJECT((PyObject *)nuitka_frame);
    assert(_PyObject_GC_IS_TRACKED(nuitka_frame));

#if PYTHON_VERSION >= 0x370
    PyCodeObject *code_object = Nuitka_GetFrameCodeObject(nuitka_frame);
    return Nuitka_String_FromFormat("<compiled_frame at %p, file %R, line %d, code %S>", nuitka_frame,
                                    code_object->co_filename, Nuitka_GetFrameLineNumber(nuitka_frame),
                                    code_object->co_name);
#elif _DEBUG_FRAME || _DEBUG_REFRAME || _DEBUG_EXCEPTIONS
    PyCodeObject *code_object = Nuitka_GetFrameCodeObject(nuitka_frame);
    return Nuitka_String_FromFormat("<compiled_frame object for %s at %p>",
                                    Nuitka_String_AsString(code_object->co_name), nuitka_frame);
#else
    return Nuitka_String_FromFormat("<compiled_frame object at %p>", nuitka_frame);
#endif
}

static void Nuitka_Frame_tp_clear(struct Nuitka_FrameObject *frame) {
    if (frame->m_type_description) {
        char const *w = frame->m_type_description;
        char const *t = frame->m_locals_storage;

        while (*w != 0) {
            switch (*w) {
            case NUITKA_TYPE_DESCRIPTION_OBJECT:
            case NUITKA_TYPE_DESCRIPTION_OBJECT_PTR:
            case NUITKA_TYPE_DESCRIPTION_NILONG: {
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

// Freelist setup
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
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state1;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state1);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state1);
#endif

    Nuitka_GC_UnTrack(nuitka_frame);

    PyFrameObject *frame = &nuitka_frame->m_frame;
#if PYTHON_VERSION < 0x3b0
    PyFrameObject *locals_owner = frame;
#else
    _PyInterpreterFrame *locals_owner = &nuitka_frame->m_interpreter_frame;
#endif

    assert(Nuitka_GC_IS_TRACKED_X((PyObject *)frame->f_back));
    Py_XDECREF(frame->f_back);
    Py_DECREF(locals_owner->f_builtins);
    Py_DECREF(locals_owner->f_globals);
    Py_XDECREF(locals_owner->f_locals);

#if PYTHON_VERSION < 0x370
    Py_XDECREF(frame->f_exc_type);
    Py_XDECREF(frame->f_exc_value);
    Py_XDECREF(frame->f_exc_traceback);
#endif

    Nuitka_Frame_tp_clear(nuitka_frame);

    if (Py_REFCNT(nuitka_frame) > 0) {
        Py_SET_REFCNT(nuitka_frame, Py_REFCNT(nuitka_frame) - 1);
        if (Py_REFCNT(nuitka_frame) >= 1) {
            // TODO: Allow this in debug mode, for now we would like to reproduce it.
            assert(false);
            return;
        }
    }

#if PYTHON_VERSION >= 0x3b0
    // Restore from backup, see header comment for the field "m_ob_size" to get
    // it.
    Py_SET_SIZE(nuitka_frame, nuitka_frame->m_ob_size);
#endif

    releaseToFreeList(free_list_frames, nuitka_frame, MAX_FRAME_FREE_LIST_COUNT);

#ifndef __NUITKA_NO_ASSERT__
    struct Nuitka_ExceptionPreservationItem saved_exception_state2;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state2);
    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state2);

    ASSERT_SAME_EXCEPTION_STATE(&saved_exception_state1, &saved_exception_state2);
#endif
}

static int Nuitka_Frame_tp_traverse(struct Nuitka_FrameObject *frame, visitproc visit, void *arg) {
    assert(Nuitka_Frame_CheckExact((PyObject *)frame));
    CHECK_OBJECT((PyObject *)frame);
    assert(_PyObject_GC_IS_TRACKED(frame));

    Py_VISIT(frame->m_frame.f_back);

#if PYTHON_VERSION < 0x3b0
    PyFrameObject *locals_owner = &frame->m_frame;
#else
    _PyInterpreterFrame *locals_owner = &frame->m_interpreter_frame;
#endif

    Py_VISIT(locals_owner->f_builtins);
    Py_VISIT(locals_owner->f_globals);
    // Py_VISIT(locals_owner->f_locals);

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
            NUITKA_CANNOT_GET_HERE("invalid type description");
            assert(false);
        }

        w += 1;
    }

    return 0;
}

#if PYTHON_VERSION >= 0x300

static PyObject *Nuitka_GetFrameGenerator(struct Nuitka_FrameObject *nuitka_frame) {
#if PYTHON_VERSION < 0x3b0
    return nuitka_frame->m_frame.f_gen;
#else
    return nuitka_frame->m_generator;
#endif
}

static PyObject *Nuitka_Frame_clear(struct Nuitka_FrameObject *frame, PyObject *unused) {
    assert(Nuitka_Frame_CheckExact((PyObject *)frame));
    CHECK_OBJECT((PyObject *)frame);
    assert(_PyObject_GC_IS_TRACKED(frame));

    PyThreadState *tstate = PyThreadState_GET();

    if (Nuitka_Frame_IsExecuting(frame)) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot clear an executing frame");

        return NULL;
    }

#if PYTHON_VERSION >= 0x3b0
    if (frame->m_frame_state == FRAME_COMPLETED) {
        Nuitka_Frame_tp_clear(frame);

        Py_RETURN_NONE;
    }

    if (frame->m_frame_state == FRAME_EXECUTING) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "cannot clear an executing frame");
        return NULL;
    }
#endif

#if PYTHON_VERSION >= 0x300
    // For frames that are closed, we also need to close the generator.
    PyObject *f_gen = Nuitka_GetFrameGenerator(frame);
    if (f_gen != NULL) {
        CHECK_OBJECT(f_gen);

        Py_INCREF(frame);

        bool close_exception;

        if (Nuitka_Generator_Check(f_gen)) {
            struct Nuitka_GeneratorObject *generator = (struct Nuitka_GeneratorObject *)f_gen;
            Nuitka_SetFrameGenerator(frame, NULL);

            close_exception = !_Nuitka_Generator_close(tstate, generator);
        }
#if PYTHON_VERSION >= 0x350
        else if (Nuitka_Coroutine_Check(f_gen)) {
            struct Nuitka_CoroutineObject *coroutine = (struct Nuitka_CoroutineObject *)f_gen;
            Nuitka_SetFrameGenerator(frame, NULL);

            close_exception = !_Nuitka_Coroutine_close(tstate, coroutine);
        }
#endif
#if PYTHON_VERSION >= 0x360
        else if (Nuitka_Asyncgen_Check(f_gen)) {
            struct Nuitka_AsyncgenObject *asyncgen = (struct Nuitka_AsyncgenObject *)f_gen;
            Nuitka_SetFrameGenerator(frame, NULL);

            close_exception = !_Nuitka_Asyncgen_close(tstate, asyncgen);
        }
#endif
        else {
            // Compiled frames should only have our types, so this ought to not happen.
            assert(false);

            Nuitka_SetFrameGenerator(frame, NULL);

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

static inline Py_ssize_t Nuitka_Frame_GetSize(struct Nuitka_FrameObject *frame) {
    assert(Nuitka_Frame_CheckExact((PyObject *)frame));
    CHECK_OBJECT((PyObject *)frame);
    assert(_PyObject_GC_IS_TRACKED(frame));

#if PYTHON_VERSION < 0x3b0
    return Py_SIZE(frame);
#else
    return frame->m_ob_size;
#endif
}

static PyObject *Nuitka_Frame_sizeof(struct Nuitka_FrameObject *frame, PyObject *unused) {
    assert(Nuitka_Frame_CheckExact((PyObject *)frame));
    CHECK_OBJECT((PyObject *)frame);
    assert(_PyObject_GC_IS_TRACKED(frame));

    return PyInt_FromSsize_t(sizeof(struct Nuitka_FrameObject) + Py_SIZE(frame));
}

static PyMethodDef Nuitka_Frame_methods[] = {
#if PYTHON_VERSION >= 0x300
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
    0,                                       // tp_getattro (PyObject_GenericGetAttr)
    0,                                       // tp_setattro (PyObject_GenericSetAttr)
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
    Nuitka_Frame_members,                    // tp_members
    Nuitka_Frame_tp_getset,                  // tp_getset
    0,                                       // tp_base
    0,                                       // tp_dict
};

void _initCompiledFrameType(void) {
    assert(Nuitka_Frame_Type.tp_doc != PyFrame_Type.tp_doc || PyFrame_Type.tp_doc == NULL);
    assert(Nuitka_Frame_Type.tp_traverse != PyFrame_Type.tp_traverse);
    assert(Nuitka_Frame_Type.tp_clear != PyFrame_Type.tp_clear || PyFrame_Type.tp_clear == NULL);
    assert(Nuitka_Frame_Type.tp_richcompare != PyFrame_Type.tp_richcompare || PyFrame_Type.tp_richcompare == NULL);
    assert(Nuitka_Frame_Type.tp_weaklistoffset != PyFrame_Type.tp_weaklistoffset ||
           PyFrame_Type.tp_weaklistoffset == 0);
    assert(Nuitka_Frame_Type.tp_iter != PyFrame_Type.tp_iter || PyFrame_Type.tp_iter == NULL);
    assert(Nuitka_Frame_Type.tp_iternext != PyFrame_Type.tp_iternext || PyFrame_Type.tp_iternext == NULL);
    assert(Nuitka_Frame_Type.tp_methods != PyFrame_Type.tp_methods);
    assert(Nuitka_Frame_Type.tp_members != PyFrame_Type.tp_members);
    assert(Nuitka_Frame_Type.tp_getset != PyFrame_Type.tp_getset);

    assert(Nuitka_Frame_Type.tp_descr_get != PyFrame_Type.tp_descr_get || PyFrame_Type.tp_descr_get == NULL);

    assert(Nuitka_Frame_Type.tp_descr_set != PyFrame_Type.tp_descr_set || PyFrame_Type.tp_descr_set == NULL);
    assert(Nuitka_Frame_Type.tp_dictoffset != PyFrame_Type.tp_dictoffset || PyFrame_Type.tp_dictoffset == 0);
    // TODO: These get changed and into the same thing, not sure what to compare against, project something
    // assert(Nuitka_Frame_Type.tp_dict != PyFrame_Type.tp_dict);
    // assert(Nuitka_Frame_Type.tp_init != PyFrame_Type.tp_init || PyFrame_Type.tp_init == NULL);
    // assert(Nuitka_Frame_Type.tp_alloc != PyFrame_Type.tp_alloc || PyFrame_Type.tp_alloc == NULL);
    // assert(Nuitka_Frame_Type.tp_new != PyFrame_Type.tp_new || PyFrame_Type.tp_new == NULL);
    // assert(Nuitka_Frame_Type.tp_free != PyFrame_Type.tp_free || PyFrame_Type.tp_free == NULL);
    // assert(Nuitka_Frame_Type.tp_weaklist != PyFrame_Type.tp_weaklist);
    assert(Nuitka_Frame_Type.tp_bases != PyFrame_Type.tp_bases);
    assert(Nuitka_Frame_Type.tp_mro != PyFrame_Type.tp_mro);
    assert(Nuitka_Frame_Type.tp_cache != PyFrame_Type.tp_cache || PyFrame_Type.tp_cache == NULL);
    assert(Nuitka_Frame_Type.tp_subclasses != PyFrame_Type.tp_subclasses || PyFrame_Type.tp_cache == NULL);
    assert(Nuitka_Frame_Type.tp_del != PyFrame_Type.tp_del || PyFrame_Type.tp_del == NULL);
#if PYTHON_VERSION >= 0x300
    assert(Nuitka_Frame_Type.tp_finalize != PyFrame_Type.tp_finalize || PyFrame_Type.tp_finalize == NULL);
#endif
    Nuitka_PyType_Ready(&Nuitka_Frame_Type, &PyFrame_Type, true, true, false, false, false);

    // These are to be used interchangeably. Make sure that's true.
    assert(offsetof(struct Nuitka_FrameObject, m_frame) == 0);
}

static struct Nuitka_FrameObject *_MAKE_COMPILED_FRAME(PyCodeObject *code, PyObject *module, PyObject *f_locals,
                                                       Py_ssize_t locals_size) {
    CHECK_CODE_OBJECT(code);
    CHECK_OBJECT(module);

#if _DEBUG_REFCOUNTS
    count_active_Nuitka_Frame_Type += 1;
    count_allocated_Nuitka_Frame_Type += 1;
#endif

    PyObject *globals = ((PyModuleObject *)module)->md_dict;
    CHECK_OBJECT(globals);

    assert(PyDict_Check(globals));

    struct Nuitka_FrameObject *result;

    // Macro to assign result memory from GC or free list.
    allocateFromFreeList(free_list_frames, struct Nuitka_FrameObject, Nuitka_Frame_Type, locals_size);

    result->m_type_description = NULL;

    PyFrameObject *frame = &result->m_frame;
    // Globals and locals are stored differently before Python 3.11
#if PYTHON_VERSION < 0x3b0
    PyFrameObject *locals_owner = frame;
#else
    _PyInterpreterFrame *locals_owner = &result->m_interpreter_frame;
#endif

#if PYTHON_VERSION < 0x3d0
    locals_owner->f_code = code;
#elif PYTHON_VERSION < 0x3e0
    locals_owner->f_executable = (PyObject *)code;
#else
    // TODO: Why is our code object not immortal?
    locals_owner->f_executable = _PyStackRef_FromPyObjectNew((PyObject *)code);
#endif

    frame->f_trace = Py_None;

#if PYTHON_VERSION < 0x370
    frame->f_exc_type = NULL;
    frame->f_exc_value = NULL;
    frame->f_exc_traceback = NULL;
#else
    frame->f_trace_lines = 0;
    frame->f_trace_opcodes = 0;
#endif

#if PYTHON_VERSION >= 0x3b0
    result->m_ob_size = Py_SIZE(result);
#endif
    frame->f_back = NULL;

    Py_INCREF(dict_builtin);
    locals_owner->f_builtins = (PyObject *)dict_builtin;

    Py_INCREF(globals);
    locals_owner->f_globals = globals;

    // Note: Reference taking happens in calling function.
    CHECK_OBJECT_X(f_locals);
    locals_owner->f_locals = f_locals;

#if PYTHON_VERSION < 0x300
    frame->f_tstate = PyThreadState_GET();
#endif

#if PYTHON_VERSION < 0x3b0
    frame->f_lasti = -1;
    frame->f_iblock = 0; // spell-checker: ignore iblock
#endif

    frame->f_lineno = code->co_firstlineno;

#if PYTHON_VERSION >= 0x300
    Nuitka_SetFrameGenerator(result, NULL);

    Nuitka_Frame_MarkAsNotExecuting(result);
#endif

#if PYTHON_VERSION >= 0x3b0
    result->m_interpreter_frame.frame_obj = &result->m_frame;
    result->m_interpreter_frame.owner = FRAME_OWNED_BY_GENERATOR;
#if PYTHON_VERSION >= 0x3e0
    result->m_interpreter_frame.f_funcobj = PyStackRef_NULL; // spell-checker: ignore funcobj
#elif PYTHON_VERSION >= 0x3c0
    result->m_interpreter_frame.f_funcobj = NULL; // spell-checker: ignore funcobj
#else
    result->m_interpreter_frame.f_func = NULL;
#endif
#if PYTHON_VERSION < 0x3d0
    result->m_interpreter_frame.prev_instr = _PyCode_CODE(code);
#else
    result->m_interpreter_frame.instr_ptr = _PyCode_CODE(code);
#endif
    result->m_frame.f_frame = &result->m_interpreter_frame;

    assert(!_PyFrame_IsIncomplete(&result->m_interpreter_frame));
#endif

    Nuitka_GC_Track(result);
    return result;
}

struct Nuitka_FrameObject *MAKE_MODULE_FRAME(PyCodeObject *code, PyObject *module) {
    PyObject *f_locals = ((PyModuleObject *)module)->md_dict;
    Py_INCREF(f_locals);

    return _MAKE_COMPILED_FRAME(code, module, f_locals, 0);
}

struct Nuitka_FrameObject *MAKE_FUNCTION_FRAME(PyThreadState *tstate, PyCodeObject *code, PyObject *module,
                                               Py_ssize_t locals_size) {
    PyObject *f_locals;

    if (likely((code->co_flags & CO_OPTIMIZED) == CO_OPTIMIZED)) {
        f_locals = NULL;
    } else {
        PyObject *kw_pairs[2] = {const_str_plain___module__, MODULE_NAME0(tstate, module)};
        f_locals = MAKE_DICT(kw_pairs, 1);
    }

    return _MAKE_COMPILED_FRAME(code, module, f_locals, locals_size);
}

struct Nuitka_FrameObject *MAKE_CLASS_FRAME(PyThreadState *tstate, PyCodeObject *code, PyObject *module,
                                            PyObject *f_locals, Py_ssize_t locals_size) {
    // The frame template sets f_locals on usage itself, need not create it that way.
    if (f_locals == NULL) {
        PyObject *kw_pairs[2] = {const_str_plain___module__, MODULE_NAME0(tstate, module)};
        f_locals = MAKE_DICT(kw_pairs, 1);
    } else {
        Py_INCREF(f_locals);
    }

    return _MAKE_COMPILED_FRAME(code, module, f_locals, locals_size);
}


#if PYTHON_VERSION >= 0x3e0

static int
Nuitka_PyCode_scan_varint(const uint8_t *ptr)
{
    unsigned int read = *ptr++;
    unsigned int val = read & 63;
    unsigned int shift = 0;
    while (read & 64) {
        read = *ptr++;
        shift += 6;
        val |= (read & 63) << shift;
    }
    return val;
}

static int
Nuitka_PyCode_scan_signed_varint(const uint8_t *ptr)
{
    unsigned int uval = Nuitka_PyCode_scan_varint(ptr);
    if (uval & 1) {
        return -(int)(uval >> 1);
    }
    else {
        return uval >> 1;
    }
}

static int
Nuitka_PyCode_get_line_delta(const uint8_t *ptr)
{
    int code = ((*ptr) >> 3) & 15;
    switch (code) {
        case PY_CODE_LOCATION_INFO_NONE:
            return 0;
        case PY_CODE_LOCATION_INFO_NO_COLUMNS:
        case PY_CODE_LOCATION_INFO_LONG:
            return Nuitka_PyCode_scan_signed_varint(ptr+1);
        case PY_CODE_LOCATION_INFO_ONE_LINE0:
            return 0;
        case PY_CODE_LOCATION_INFO_ONE_LINE1:
            return 1;
        case PY_CODE_LOCATION_INFO_ONE_LINE2:
            return 2;
        default:
            /* Same line */
            return 0;
    }
}

static PyObject *
Nuitka_PyCode_remove_column_info(PyObject *locations)
{
    Py_ssize_t offset = 0;
    const uint8_t *data = (const uint8_t *)PyBytes_AS_STRING(locations);
    PyObject *res = PyBytes_FromStringAndSize(NULL, 32);
    if (res == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    uint8_t *output = (uint8_t *)PyBytes_AS_STRING(res);
    while (offset < PyBytes_GET_SIZE(locations)) {
        Py_ssize_t write_offset = output - (uint8_t *)PyBytes_AS_STRING(res);
        if (write_offset + 16 >= PyBytes_GET_SIZE(res)) {
            if (_PyBytes_Resize(&res, PyBytes_GET_SIZE(res) * 2) < 0) {
                return NULL;
            }
            output = (uint8_t *)PyBytes_AS_STRING(res) + write_offset;
        }
        int code = (data[offset] >> 3) & 15;
        if (code == PY_CODE_LOCATION_INFO_NONE) {
            *output++ = data[offset];
        }
        else {
            int blength = (data[offset] & 7)+1;
            output += write_location_entry_start(
                output, PY_CODE_LOCATION_INFO_NO_COLUMNS, blength);
            int ldelta = Nuitka_PyCode_get_line_delta(&data[offset]);
            output += write_signed_varint(output, ldelta);
        }
        offset++;
        while (offset < PyBytes_GET_SIZE(locations) &&
            (data[offset] & 128) == 0) {
            offset++;
        }
    }
    Py_ssize_t write_offset = output - (uint8_t *)PyBytes_AS_STRING(res);
    if (_PyBytes_Resize(&res, write_offset)) {
        return NULL;
    }
    return res;
}

static int
Nuitka_PyCode_intern_strings(PyObject *tuple)
{
    PyInterpreterState *interp = _PyInterpreterState_GET();
    Py_ssize_t i;

    for (i = PyTuple_GET_SIZE(tuple); --i >= 0; ) {
        PyObject *v = PyTuple_GET_ITEM(tuple, i);
        if (v == NULL || !PyUnicode_CheckExact(v)) {
            PyErr_SetString(PyExc_SystemError,
                            "non-string found in code slot");
            return -1;
        }
        _PyUnicode_InternImmortal(interp, &_PyTuple_ITEMS(tuple)[i]);
    }
    return 0;
}

static int
Nuitka_PyCode_should_intern_string(PyObject *o)
{
#ifdef Py_GIL_DISABLED
    // The free-threaded build interns (and immortalizes) all string constants
    return 1;
#else
    // compute if s matches [a-zA-Z0-9_]
    const unsigned char *s, *e;

    if (!PyUnicode_IS_ASCII(o))
        return 0;

    s = PyUnicode_1BYTE_DATA(o);
    e = s + PyUnicode_GET_LENGTH(o);
    for (; s != e; s++) {
        if (!Py_ISALNUM(*s) && *s != '_')
            return 0;
    }
    return 1;
#endif
}

/* Intern constants. In the default build, this interns selected string
   constants. In the free-threaded build, this also interns non-string
   constants. */
static int
Nuitka_PyCode_intern_constants(PyObject *tuple, int *modified)
{
    PyInterpreterState *interp = _PyInterpreterState_GET();
    for (Py_ssize_t i = PyTuple_GET_SIZE(tuple); --i >= 0; ) {
        PyObject *v = PyTuple_GET_ITEM(tuple, i);
        if (PyUnicode_CheckExact(v)) {
            if (Nuitka_PyCode_should_intern_string(v)) {
                PyObject *w = v;
                _PyUnicode_InternMortal(interp, &v);
                if (w != v) {
                    PyTuple_SET_ITEM(tuple, i, v);
                    if (modified) {
                        *modified = 1;
                    }
                }
            }
        }
        else if (PyTuple_CheckExact(v)) {
            if (Nuitka_PyCode_intern_constants(v, NULL) < 0) {
                return -1;
            }
        }
        else if (PyFrozenSet_CheckExact(v)) {
            PyObject *w = v;
            PyObject *tmp = PySequence_Tuple(v);
            if (tmp == NULL) {
                return -1;
            }
            int tmp_modified = 0;
            if (Nuitka_PyCode_intern_constants(tmp, &tmp_modified) < 0) {
                Py_DECREF(tmp);
                return -1;
            }
            if (tmp_modified) {
                v = PyFrozenSet_New(tmp);
                if (v == NULL) {
                    Py_DECREF(tmp);
                    return -1;
                }

                PyTuple_SET_ITEM(tuple, i, v);
                Py_DECREF(w);
                if (modified) {
                    *modified = 1;
                }
            }
            Py_DECREF(tmp);
        }
#ifdef Py_GIL_DISABLED
        // Nuitka TODO: Fix some missing symbols here
        else if (PySlice_Check(v)) {
            PySliceObject *slice = (PySliceObject *)v;
            PyObject *tmp = PyTuple_New(3);
            if (tmp == NULL) {
                return -1;
            }
            PyTuple_SET_ITEM(tmp, 0, Py_NewRef(slice->start));
            PyTuple_SET_ITEM(tmp, 1, Py_NewRef(slice->stop));
            PyTuple_SET_ITEM(tmp, 2, Py_NewRef(slice->step));
            int tmp_modified = 0;
            if (intern_constants(tmp, &tmp_modified) < 0) {
                Py_DECREF(tmp);
                return -1;
            }
            if (tmp_modified) {
                v = PySlice_New(PyTuple_GET_ITEM(tmp, 0),
                                PyTuple_GET_ITEM(tmp, 1),
                                PyTuple_GET_ITEM(tmp, 2));
                if (v == NULL) {
                    Py_DECREF(tmp);
                    return -1;
                }
                PyTuple_SET_ITEM(tuple, i, v);
                Py_DECREF(slice);
                if (modified) {
                    *modified = 1;
                }
            }
            Py_DECREF(tmp);
        }

        // Intern non-string constants in the free-threaded build
        _PyThreadStateImpl *tstate = (_PyThreadStateImpl *)_PyThreadState_GET();
        if (!_Py_IsImmortal(v) && !PyUnicode_CheckExact(v) &&
            should_immortalize_constant(v) &&
            !tstate->suppress_co_const_immortalization)
        {
            PyObject *interned = intern_one_constant(v);
            if (interned == NULL) {
                return -1;
            }
            else if (interned != v) {
                PyTuple_SET_ITEM(tuple, i, interned);
                Py_SETREF(v, interned);
                if (modified) {
                    *modified = 1;
                }
            }
        }
#endif
    }
    return 0;
}

static int
Nuitka_PyCode_intern_code_constants(struct _PyCodeConstructor *con)
{
#ifdef Py_GIL_DISABLED
    PyInterpreterState *interp = _PyInterpreterState_GET();
    struct _py_code_state *state = &interp->code_state;
    PyMutex_Lock(&state->mutex);
#endif
    if (Nuitka_PyCode_intern_strings(con->names) < 0) {
        goto error;
    }
    if (Nuitka_PyCode_intern_constants(con->consts, NULL) < 0) {
        goto error;
    }
    if (Nuitka_PyCode_intern_strings(con->localsplusnames) < 0) {
        goto error;
    }
#ifdef Py_GIL_DISABLED
    PyMutex_Unlock(&state->mutex);
#endif
    return 0;

error:
#ifdef Py_GIL_DISABLED
    PyMutex_Unlock(&state->mutex);
#endif
    return -1;
}


static void
Nuitka_PyCode_get_localsplus_counts(PyObject *names, PyObject *kinds,
                      int *pnlocals, int *pncellvars,
                      int *pnfreevars)
{
    int nlocals = 0;
    int ncellvars = 0;
    int nfreevars = 0;
    Py_ssize_t nlocalsplus = PyTuple_GET_SIZE(names);
    for (int i = 0; i < nlocalsplus; i++) {
        _PyLocals_Kind kind = _PyLocals_GetKind(kinds, i);
        if (kind & CO_FAST_LOCAL) {
            nlocals += 1;
            if (kind & CO_FAST_CELL) {
                ncellvars += 1;
            }
        }
        else if (kind & CO_FAST_CELL) {
            ncellvars += 1;
        }
        else if (kind & CO_FAST_FREE) {
            nfreevars += 1;
        }
    }
    if (pnlocals != NULL) {
        *pnlocals = nlocals;
    }
    if (pncellvars != NULL) {
        *pncellvars = ncellvars;
    }
    if (pnfreevars != NULL) {
        *pnfreevars = nfreevars;
    }
}

static int
Nuitka_PyCode_init_code(PyCodeObject *co, struct _PyCodeConstructor *con)
{
    int nlocalsplus = (int)PyTuple_GET_SIZE(con->localsplusnames);
    int nlocals, ncellvars, nfreevars;
    Nuitka_PyCode_get_localsplus_counts(con->localsplusnames, con->localspluskinds,
                          &nlocals, &ncellvars, &nfreevars);
    if (con->stacksize == 0) {
        con->stacksize = 1;
    }

    PyInterpreterState *interp = _PyInterpreterState_GET();
    co->co_filename = Py_NewRef(con->filename);
    co->co_name = Py_NewRef(con->name);
    co->co_qualname = Py_NewRef(con->qualname);
    _PyUnicode_InternMortal(interp, &co->co_filename);
    _PyUnicode_InternMortal(interp, &co->co_name);
    _PyUnicode_InternMortal(interp, &co->co_qualname);
    co->co_flags = con->flags;

    co->co_firstlineno = con->firstlineno;
    co->co_linetable = Py_NewRef(con->linetable);

    co->co_consts = Py_NewRef(con->consts);
    co->co_names = Py_NewRef(con->names);

    co->co_localsplusnames = Py_NewRef(con->localsplusnames);
    co->co_localspluskinds = Py_NewRef(con->localspluskinds);

    co->co_argcount = con->argcount;
    co->co_posonlyargcount = con->posonlyargcount;
    co->co_kwonlyargcount = con->kwonlyargcount;

    co->co_stacksize = con->stacksize;

    co->co_exceptiontable = Py_NewRef(con->exceptiontable);

    /* derived values */
    co->co_nlocalsplus = nlocalsplus;
    co->co_nlocals = nlocals;
    co->co_framesize = nlocalsplus + con->stacksize + FRAME_SPECIALS_SIZE;
    co->co_ncellvars = ncellvars;
    co->co_nfreevars = nfreevars;
#ifdef Py_GIL_DISABLED
    PyMutex_Lock(&interp->func_state.mutex);
#endif
    co->co_version = interp->func_state.next_version;
    if (interp->func_state.next_version != 0) {
        interp->func_state.next_version++;
    }
#ifdef Py_GIL_DISABLED
    PyMutex_Unlock(&interp->func_state.mutex);
#endif
    co->_co_monitoring = NULL;
    co->_co_instrumentation_version = 0;
    /* not set */
    co->co_weakreflist = NULL;
    co->co_extra = NULL;
    co->_co_cached = NULL;
    co->co_executors = NULL;

    memcpy(_PyCode_CODE(co), PyBytes_AS_STRING(con->code),
           PyBytes_GET_SIZE(con->code));
#ifdef Py_GIL_DISABLED
    co->co_tlbc = _PyCodeArray_New(INITIAL_SPECIALIZED_CODE_SIZE);
    if (co->co_tlbc == NULL) {
        return -1;
    }
    co->co_tlbc->entries[0] = co->co_code_adaptive;
#endif
    int entry_point = 0;
    while (entry_point < Py_SIZE(co) &&
        _PyCode_CODE(co)[entry_point].op.code != RESUME) {
        entry_point++;
    }
    co->_co_firsttraceable = entry_point;
#ifdef Py_GIL_DISABLED
    //_PyCode_Quicken(_PyCode_CODE(co), Py_SIZE(co), interp->config.tlbc_enabled);
#else
    //_PyCode_Quicken(_PyCode_CODE(co), Py_SIZE(co), 1);
#endif
    // Nuitka shouldn't need any code watchers
    //notify_code_watchers(PY_CODE_EVENT_CREATE, co);
    return 0;
}

PyCodeObject *
Nuitka_PyCode_New(struct _PyCodeConstructor *con)
{
    if (Nuitka_PyCode_intern_code_constants(con) < 0) {
        return NULL;
    }

    PyObject *replacement_locations = NULL;
    // Compact the linetable if we are opted out of debug
    // ranges.
    /*if (!_Py_GetConfig()->code_debug_ranges) {
        replacement_locations = remove_column_info(con->linetable);
        if (replacement_locations == NULL) {
            return NULL;
        }
        con->linetable = replacement_locations;
    }*/

    Py_ssize_t size = PyBytes_GET_SIZE(con->code) / sizeof(_Py_CODEUNIT);
    PyCodeObject *co;
#ifdef Py_GIL_DISABLED
    co = PyObject_GC_NewVar(PyCodeObject, &PyCode_Type, size);
#else
    co = PyObject_NewVar(PyCodeObject, &PyCode_Type, size);
#endif
    if (co == NULL) {
        Py_XDECREF(replacement_locations);
        PyErr_NoMemory();
        return NULL;
    }

    if (Nuitka_PyCode_init_code(co, con) < 0) {
        Py_DECREF(co);
        return NULL;
    }

#ifdef Py_GIL_DISABLED
    co->_co_unique_id = _PyObject_AssignUniqueId((PyObject *)co);
    Nuitka_GC_Track(co);
#endif
    Py_XDECREF(replacement_locations);
    return co;
}
#endif


// This is the backend of MAKE_CODE_OBJECT macro.
PyCodeObject *makeCodeObject(PyObject *filename, int line, int flags, PyObject *function_name,
#if PYTHON_VERSION >= 0x3b0
                             PyObject *function_qualname,
#endif
                             PyObject *arg_names, PyObject *free_vars, int arg_count
#if PYTHON_VERSION >= 0x300
                             ,
                             int kw_only_count
#endif
#if PYTHON_VERSION >= 0x380
                             ,
                             int pos_only_count
#endif
) {

    if (filename == Py_None) {
        filename = const_str_empty;
    }

    // TODO: We don't do that anymore once new-code-objects
    // is the default, then we don't need to pass it, since
    // we create them incomplete anyway.
    CHECK_OBJECT(filename);
    assert(Nuitka_StringOrUnicode_CheckExact(filename));

    CHECK_OBJECT(function_name);
    assert(Nuitka_String_CheckExact(function_name));

#if PYTHON_VERSION >= 0x3b0
    if (function_qualname) {
        CHECK_OBJECT(function_qualname);
        PyUnicode_CheckExact(function_qualname);
    }
#endif

#if PYTHON_VERSION >= 0x300
    assert(kw_only_count >= 0);
#endif
#if PYTHON_VERSION >= 0x380
    assert(pos_only_count >= 0);
#endif
    assert(flags >= 0);
    assert(arg_count >= 0);

// TODO: On macOS with zig, libpython asserts against values failing, but only if
// debug mode is not on, these check without using the disabled assert.
#if 0
    if (pos_only_count < 0) abort();
    if (kw_only_count < 0) abort();
    if (flags < 0) abort();
    if (arg_count < 0) abort();
#endif

#if PYTHON_VERSION < 0x300
    PyObject *filename_str = NULL;

    // TODO: Memory leak of filename, it might be intended transferred to the
    // code object by using code.
    if (PyUnicode_CheckExact(filename)) {
        filename_str = PyUnicode_AsUTF8String(filename);
        filename = filename_str;
    } else {
        filename_str = filename;
        Py_INCREF(filename);
    }
#endif

    if (arg_names == NULL || arg_names == Py_None) {
        arg_names = const_tuple_empty;
    }
    CHECK_OBJECT(arg_names);
    assert(PyTuple_Check(arg_names));

    if (free_vars == NULL || free_vars == Py_None) {
        free_vars = const_tuple_empty;
    }
    CHECK_OBJECT(free_vars);
    assert(PyTuple_Check(free_vars));

    // The PyCode_New has funny code that interns, mutating the tuple that owns
    // it. Really serious non-immutable shit. We have triggered that changes
    // behind our back in the past.
#ifndef __NUITKA_NO_ASSERT__
    // TODO: Reactivate once code object creation becomes un-streaming driven
    // and we can pass the extra args with no worries.

    // Py_hash_t hash = DEEP_HASH(arg_names);
#endif

    // spell-checker: ignore lnotab
#if PYTHON_VERSION < 0x300
    PyObject *code = const_str_empty;
    PyObject *lnotab = const_str_empty;
    PyObject *consts = const_tuple_empty;
    PyObject *names = const_tuple_empty;
    int stacksize = 0;
#elif PYTHON_VERSION < 0x3b0
    PyObject *code = const_bytes_empty;
    PyObject *lnotab = const_bytes_empty;
    PyObject *consts = const_tuple_empty;
    PyObject *names = const_tuple_empty;
    int stacksize = 0;
#else
    // Our code object needs to be recognizable, and Python doesn't store the
    // length anymore, so we need a non-empty one.
    static PyObject *empty_code = NULL;
    static PyObject *lnotab = NULL;
    static PyObject *consts = NULL;
    static PyObject *names = NULL;
    // TODO: Seems removable.
    static PyObject *exception_table = NULL;
    static int stacksize = 0;

    if (empty_code == NULL) {
        // Only needed once here.
        PyThreadState *tstate = PyThreadState_GET();

        PyObject *empty_code_module_object = Py_CompileString(
            "def empty(): raise RuntimeError('Compiled function bytecode used')", "<exec>", Py_file_input);
        NUITKA_MAY_BE_UNUSED PyObject *module =
            PyImport_ExecCodeModule("nuitka_empty_function", empty_code_module_object);
        CHECK_OBJECT(module);

        PyObject *empty_function = PyObject_GetAttrString(module, "empty");
        CHECK_OBJECT(empty_function);
        PyObject *empty_code_object = PyObject_GetAttrString(empty_function, "__code__");
        CHECK_OBJECT(empty_code_object);

        NUITKA_MAY_BE_UNUSED bool bool_res = Nuitka_DelModuleString(tstate, "nuitka_empty_function");
        assert(bool_res != false);

        empty_code = PyObject_GetAttrString(empty_code_object, "co_code");
        CHECK_OBJECT(empty_code);
#if PYTHON_VERSION >= 0x3c0
        lnotab = ((PyCodeObject *)empty_code_object)->co_linetable; // spell-checker: ignore linetable
#else
        lnotab = PyObject_GetAttrString(empty_code_object, "co_lnotab");
        CHECK_OBJECT(lnotab);
#endif
        consts = PyObject_GetAttrString(empty_code_object, "co_consts");
        CHECK_OBJECT(consts);
        names = PyObject_GetAttrString(empty_code_object, "co_names");
        CHECK_OBJECT(names);
        exception_table = PyObject_GetAttrString(empty_code_object, "co_exceptiontable");
        CHECK_OBJECT(exception_table);

        stacksize = (int)PyLong_AsLong(PyObject_GetAttrString(empty_code_object, "co_stacksize"));
    }

    PyObject *code = empty_code;
    CHECK_OBJECT(empty_code);
    assert(PyBytes_Check(code));
    CHECK_OBJECT(lnotab);
    assert(PyBytes_Check(lnotab));
    CHECK_OBJECT(consts);
    assert(PyTuple_Check(consts));
    CHECK_OBJECT(names);
    assert(PyTuple_Check(names));
    CHECK_OBJECT(exception_table);
    assert(PyBytes_Check(exception_table));
    assert(stacksize >= 0);
#endif

    // For Python 3.11 this value is checked, even if not used.
#if PYTHON_VERSION >= 0x3b0
    int nlocals = (int)PyTuple_GET_SIZE(arg_names);
#else
    int nlocals = 0;
#endif

#if PYTHON_VERSION >= 0x3e0
    struct _PyCodeConstructor con = {
        .filename = filename,
        .name = names,
        .qualname = names,
        .flags = flags,

        .code = code,
        .firstlineno = line,
        .linetable = lnotab,

        .consts = consts,
        .names = names,

        .localsplusnames = const_tuple_empty,
        .localspluskinds = const_tuple_empty,

        .argcount = arg_count,
        .posonlyargcount = pos_only_count,
        .kwonlyargcount = kw_only_count,

        .stacksize = stacksize,

        .exceptiontable = exception_table,
    };
    PyCodeObject *result = Nuitka_PyCode_New(&con);
#else

    // Not using PyCode_NewEmpty, it doesn't given us much beyond this
    // and is not available for Python2.

#if PYTHON_VERSION >= 0x380
    PyCodeObject *result = PyCode_NewWithPosOnlyArgs(arg_count, // arg_count
#else
    PyCodeObject *result = PyCode_New(arg_count, // arg_count
#endif

#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION >= 0x380
                                                     pos_only_count, // pos-only count
#endif
                                                     kw_only_count, // kw-only count
#endif
                                                     nlocals,           // nlocals
                                                     stacksize,         // stacksize
                                                     flags,             // flags
                                                     code,              // code (bytecode)
                                                     consts,            // consts (we are not going to be compatible)
                                                     names,             // names (we are not going to be compatible)
                                                     arg_names,         // var_names (we are not going to be compatible)
                                                     free_vars,         // free_vars
                                                     const_tuple_empty, // cell_vars (we are not going to be compatible)
                                                     filename,          // filename
                                                     function_name,     // name
#if PYTHON_VERSION >= 0x3b0
                                                     function_qualname, // qualname
#endif
                                                     line,  // first_lineno (offset of the code object)
                                                     lnotab // lnotab (table to translate code object)
#if PYTHON_VERSION >= 0x3b0
                                                     ,
                                                     exception_table // exception_table
#endif
    );

    // assert(DEEP_HASH(tstate, arg_names) == hash);

#endif

#if PYTHON_VERSION < 0x300
    Py_DECREF(filename_str);
#endif

    if (result == NULL) {
        PyErr_PrintEx(0);
        NUITKA_CANNOT_GET_HERE("Failed to create code object");
    }

    return result;
}

PyCodeObject *USE_CODE_OBJECT(PyThreadState *tstate, PyObject *code_object, PyObject *module_filename_obj) {
    assert(PyCode_Check(code_object));
    CHECK_OBJECT(module_filename_obj);

    PyCodeObject *co = (PyCodeObject *)code_object;
    PyObject *old = co->co_filename;

    if (old == const_str_empty) {
        // Set the filename, ignore the loss of a reference to empty string,
        // that's our singleton and immortal at least practically.
        co->co_filename = Py_NewRef(module_filename_obj);

#if PYTHON_VERSION >= 0x3b0
        // Also, make sure the qualname is completed from the partial
        // name.
        if (co->co_qualname != co->co_name) {
            PyObject *w = UNICODE_CONCAT(tstate, co->co_qualname, const_str_dot);
            co->co_qualname = UNICODE_CONCAT(tstate, w, co->co_name);
            Py_DECREF(w);
        }
#endif
    }

    return co;
}

void Nuitka_Frame_AttachLocals(struct Nuitka_FrameObject *frame_object, char const *type_description, ...) {
    assert(Nuitka_Frame_CheckExact((PyObject *)frame_object));
    CHECK_OBJECT((PyObject *)frame_object);
    assert(_PyObject_GC_IS_TRACKED(frame_object));
    assertFrameObject(frame_object);

#if _DEBUG_FRAME
    PRINT_FORMAT("Attaching to frame 0x%lx %s\n", frame_object,
                 Nuitka_String_AsString(PyObject_Repr((PyObject *)Nuitka_Frame_GetCodeObject(&frame_object->m_frame))));
#endif

    assert(frame_object->m_type_description == NULL);

    // TODO: Do not call this if there is nothing to do. Instead make all the
    // places handle NULL pointer and recognize that there is nothing to do.
    // assert(type_description != NULL && assert(strlen(type_description)>0));
    if (type_description == NULL) {
        type_description = "";
    }

    frame_object->m_type_description = type_description;

    char const *w = type_description;
    char *t = frame_object->m_locals_storage;

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
            // TODO: Reference count must become wrong here, should
            // be forced to one probably, or we should simply not
            // store cells, but their values. Take a ref off "value"
            // is probably not needed.
            // Py_SET_REFCNT((struct Nuitka_CellObject *)t, 1);
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
        case NUITKA_TYPE_DESCRIPTION_NILONG: {
            nuitka_ilong value = va_arg(ap, nuitka_ilong);
            ENFORCE_NILONG_OBJECT_VALUE(&value);

            CHECK_OBJECT(value.python_value);
            memcpy(t, &value.python_value, sizeof(PyObject *));
            Py_XINCREF(value.python_value);
            t += sizeof(PyObject *);

            break;
        }
        default:
            NUITKA_CANNOT_GET_HERE("invalid type description");
            assert(false);
        }

        w += 1;
    }

    va_end(ap);

    assert(t - frame_object->m_locals_storage <= Nuitka_Frame_GetSize(frame_object));
}

// Make a dump of the active frame stack. For debugging purposes only.
#if _DEBUG_FRAME
void dumpFrameStack(void) {
    PyThreadState *tstate = PyThreadState_GET();

    struct Nuitka_ExceptionPreservationItem saved_exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

    int total = 0;

#if PYTHON_VERSION < 0x3b0
    PyFrameObject *current = PyThreadState_GET()->frame;
    while (current != NULL) {
        total++;
        current = current->f_back;
    }

    current = tstate->frame;
#else
    _PyCFrame *current = tstate->cframe;
    while (current != NULL) {
        total++;
        current = current->previous;
    }

    current = tstate->cframe;
#endif

    PRINT_STRING(">--------->\n");

    while (current) {
#if PYTHON_VERSION < 0x3b0
        PyObject *current_repr = PyObject_Str((PyObject *)current);
        PyObject *code_repr = PyObject_Str((PyObject *)current->f_code);
#else
        PyObject *current_repr = NULL;
        if (current->current_frame->frame_obj != NULL) {
            current_repr = PyObject_Str((PyObject *)current->current_frame->frame_obj);
        } else {
            current_repr = const_str_empty;
            Py_INCREF(const_str_empty);
        }
        PyObject *code_repr = PyObject_Str((PyObject *)Nuitka_InterpreterFrame_GetCodeObject(current->current_frame));
#endif

        PRINT_FORMAT("Frame stack %d: %s %d %s\n", total--, Nuitka_String_AsString(current_repr), Py_REFCNT(current),
                     Nuitka_String_AsString(code_repr));

        Py_DECREF(current_repr);
        Py_DECREF(code_repr);

#if PYTHON_VERSION < 0x3b0
        current = current->f_back;
#else
        current = current->previous;
#endif
    }

    PRINT_STRING(">---------<\n");

    RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);
}

static void PRINT_UNCOMPILED_FRAME(char const *prefix, PyFrameObject *frame) {
    PRINT_STRING(prefix);
    PRINT_STRING(" ");

    if (frame) {
        PyObject *frame_str = PyObject_Str((PyObject *)frame);
        PRINT_ITEM(frame_str);
        Py_DECREF(frame_str);

        PyObject *code_object_str = PyObject_Repr((PyObject *)Nuitka_Frame_GetCodeObject(frame));
        PRINT_ITEM(code_object_str);
        Py_DECREF(code_object_str);

        PRINT_REFCOUNT((PyObject *)frame);
    } else {
        PRINT_STRING("<NULL> no frame");
    }

    PRINT_NEW_LINE();
}

void PRINT_COMPILED_FRAME(char const *prefix, struct Nuitka_FrameObject *frame) {
    return PRINT_UNCOMPILED_FRAME(prefix, &frame->m_frame);
}

void PRINT_INTERPRETER_FRAME(char const *prefix, Nuitka_ThreadStateFrameType *frame) {
#if PYTHON_VERSION < 0x3b0
    PRINT_UNCOMPILED_FRAME(prefix, frame);
#else
    PRINT_STRING(prefix);
    PRINT_STRING(" ");

    if (frame) {
        PRINT_FORMAT("0x%lx ", frame);

        PyObject *code_object_str = PyObject_Repr((PyObject *)Nuitka_InterpreterFrame_GetCodeObject(frame));
        PRINT_ITEM(code_object_str);
        Py_DECREF(code_object_str);
    } else {
        PRINT_STRING("<NULL> no frame");
    }

    PRINT_NEW_LINE();
#endif
}

void PRINT_TOP_FRAME(char const *prefix) {
    PyThreadState *tstate = PyThreadState_GET();

#if PYTHON_VERSION < 0x3b0
    PRINT_UNCOMPILED_FRAME(prefix, tstate->frame);
#else
    PRINT_INTERPRETER_FRAME(prefix, CURRENT_TSTATE_INTERPRETER_FRAME(tstate));
#endif
}

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
