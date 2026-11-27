//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_EXCEPTIONS_H__
#define __NUITKA_EXCEPTIONS_H__

#ifdef __IDE_ONLY__
#include "nuitka/cpython_api_compat.h"
#include "nuitka/defines.h"
#include "nuitka/helper/tuples.h"
#include "nuitka/string_functions.h"
#endif

// Fundamental, because we use it for print style debugging in everything.
#include "nuitka/checkers.h"
#include "nuitka/constants.h"
#include "nuitka/printing.h"

// Declared here because this header is included before the dictionary helpers.
extern void DICT_SET_ITEM_INFALLIBLE(PyThreadState *tstate, PyObject *dict, PyObject *key, PyObject *value);

// Write unraisable exceptions, unless disabled at compile time. CPython
// internal writes still need the "sys.unraisablehook" workaround.
#if PYTHON_NO_UNRAISABLE
#define Nuitka_WriteUnraisable(tstate, object) CLEAR_ERROR_OCCURRED(tstate)
#define Nuitka_WriteUnraisableMsg(tstate, message, object) CLEAR_ERROR_OCCURRED(tstate)
#else
#define Nuitka_WriteUnraisable(tstate, object) PyErr_WriteUnraisable(object)

#if PYTHON_VERSION >= 0x3d0
#define Nuitka_WriteUnraisableMsg(tstate, message, object) PyErr_FormatUnraisable("Exception ignored %s", message)
#else
#define Nuitka_WriteUnraisableMsg(tstate, message, object) _PyErr_WriteUnraisableMsg(message, object)
#endif
#endif

NUITKA_MAY_BE_UNUSED static inline bool HAS_ERROR_OCCURRED(PyThreadState const *tstate) {
#if PYTHON_VERSION < 0x3c0
    return tstate->curexc_type != NULL;
#else
    return tstate->current_exception != NULL;
#endif
}

// Get the error type occurred, no reference given.
NUITKA_MAY_BE_UNUSED static inline PyObject *GET_ERROR_OCCURRED(PyThreadState const *const tstate) {
#if PYTHON_VERSION < 0x3c0
    return tstate->curexc_type;
#else
    return tstate->current_exception ? (PyObject *)PyExceptionInstance_Class(tstate->current_exception) : NULL;
#endif
}

NUITKA_MAY_BE_UNUSED static inline void ASSERT_NORMALIZED_EXCEPTION_VALUE_X(PyObject const *const exception_value) {
    CHECK_OBJECT_X(exception_value);
    assert(exception_value == NULL || PyExceptionInstance_Check(exception_value));
}

NUITKA_MAY_BE_UNUSED static inline void ASSERT_NORMALIZED_EXCEPTION_VALUE(PyObject *exception_value) {
    CHECK_OBJECT(exception_value);
    assert(PyExceptionInstance_Check(exception_value));
}

// Clear error, which likely set, similar to "_PyErr_Clear(tstate)" and "PyErr_Clear"
NUITKA_MAY_BE_UNUSED static inline void CLEAR_ERROR_OCCURRED(PyThreadState *tstate) {
#if PYTHON_VERSION < 0x3c0
    PyObject *old_type = tstate->curexc_type;
    PyObject *old_value = tstate->curexc_value;
    PyObject *old_tb = tstate->curexc_traceback;

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;

    Py_XDECREF(old_type);
    Py_XDECREF(old_value);
    Py_XDECREF(old_tb);
#else
    PyObject *old_exception_value = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(old_exception_value);

    tstate->current_exception = NULL;

    Py_XDECREF(old_exception_value);
#endif
}

// Clear error, which is not likely set, use "CLEAR_ERROR_OCCURRED" if not sure there is an error.
NUITKA_MAY_BE_UNUSED static inline bool DROP_ERROR_OCCURRED(PyThreadState *tstate) {

#if PYTHON_VERSION < 0x3c0
    if (unlikely(tstate->curexc_type != NULL)) {
        PyObject *old_type = tstate->curexc_type;
        PyObject *old_value = tstate->curexc_value;
        PyObject *old_tb = tstate->curexc_traceback;

        tstate->curexc_type = NULL;
        tstate->curexc_value = NULL;
        tstate->curexc_traceback = NULL;

        Py_DECREF(old_type);
        Py_XDECREF(old_value);
        Py_XDECREF(old_tb);

        return true;
    }
#else
    if (unlikely(tstate->current_exception != NULL)) {
        PyObject *old_exception_value = tstate->current_exception;
        ASSERT_NORMALIZED_EXCEPTION_VALUE(old_exception_value);

        tstate->current_exception = NULL;

        Py_DECREF(old_exception_value);

        return true;
    }
#endif
    return false;
}

#if PYTHON_VERSION < 0x3c0
// Fetch the current error into object variables, transfers reference coming from tstate ownership
NUITKA_MAY_BE_UNUSED static void FETCH_ERROR_OCCURRED(PyThreadState *tstate, PyObject **exception_type,
                                                      PyObject **exception_value,
                                                      PyTracebackObject **exception_traceback) {
    *exception_type = tstate->curexc_type;
    *exception_value = tstate->curexc_value;
    *exception_traceback = (PyTracebackObject *)tstate->curexc_traceback;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("FETCH_ERROR_OCCURRED:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;
}

NUITKA_MAY_BE_UNUSED static void FETCH_ERROR_OCCURRED_UNTRACED(PyThreadState *tstate, PyObject **exception_type,
                                                               PyObject **exception_value,
                                                               PyTracebackObject **exception_traceback) {
    *exception_type = tstate->curexc_type;
    *exception_value = tstate->curexc_value;
    *exception_traceback = (PyTracebackObject *)tstate->curexc_traceback;

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;
}

NUITKA_MAY_BE_UNUSED static void RESTORE_ERROR_OCCURRED(PyThreadState *tstate, PyObject *exception_type,
                                                        PyObject *exception_value,
                                                        PyTracebackObject *exception_traceback) {
    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    tstate->curexc_value = exception_value;
    tstate->curexc_traceback = (PyObject *)exception_traceback;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ERROR_OCCURRED:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
}

NUITKA_MAY_BE_UNUSED static void RESTORE_ERROR_OCCURRED_UNTRACED(PyThreadState *tstate, PyObject *exception_type,
                                                                 PyObject *exception_value,
                                                                 PyTracebackObject *exception_traceback) {
    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    tstate->curexc_value = exception_value;
    tstate->curexc_traceback = (PyObject *)exception_traceback;

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
}
#endif

struct Nuitka_FrameObject;

extern PyTracebackObject *MAKE_TRACEBACK(struct Nuitka_FrameObject *frame, int lineno);

NUITKA_MAY_BE_UNUSED static PyTracebackObject *ADD_TRACEBACK(PyTracebackObject *exception_tb,
                                                             struct Nuitka_FrameObject *frame, int lineno) {
    CHECK_OBJECT(exception_tb);
    CHECK_OBJECT(frame);

    PyTracebackObject *traceback_new = MAKE_TRACEBACK(frame, lineno);
    traceback_new->tb_next = exception_tb;
    Py_INCREF(exception_tb);
    return traceback_new;
}

// Need some wrapper functions for accessing exception type, value, and traceback
// due to changes in Python 3.7

#if PYTHON_VERSION >= 0x370
// Python 3.7+ keeps the handled exception state of generators, coroutines and
// async generators in an item that may be made the current thread state one
// while they run, with the previous item chained to it.
#define EXC_STATE(x) ((struct Nuitka_ExceptionStackItem *)(x)->exc_info)
#endif

#if PYTHON_VERSION < 0x370
#define EXC_TYPE(x) (x->exc_type)
#define EXC_VALUE(x) (x->exc_value)
#define EXC_TRACEBACK(x) ((PyTracebackObject *)(x->exc_traceback))
#define EXC_TRACEBACK_PTR(x) ((PyTracebackObject **)(&x->exc_traceback))
#define SET_EXC_TRACEBACK(x, tb) x->exc_traceback = (PyObject *)tb
#elif PYTHON_VERSION < 0x3b0
#define EXC_TYPE(x) (EXC_STATE(x)->exception_type)
#define EXC_VALUE(x) (EXC_STATE(x)->exception_value)
#define EXC_TRACEBACK(x) ((PyTracebackObject *)(EXC_STATE(x)->exception_tb))
#define EXC_TRACEBACK_PTR(x) ((PyTracebackObject **)(&EXC_STATE(x)->exception_tb))
#define SET_EXC_TRACEBACK(x, tb) EXC_STATE(x)->exception_tb = (PyTracebackObject *)(tb)
#else
#define EXC_TYPE(x) ((PyObject *)Py_TYPE(EXC_STATE(x)->exception_value))
#define EXC_VALUE(x) (EXC_STATE(x)->exception_value)
#endif

#if PYTHON_VERSION < 0x370
#define EXC_TYPE_F(x) (x->m_frame->m_frame.f_exc_type)
#define EXC_VALUE_F(x) (x->m_frame->m_frame.f_exc_value)
#define EXC_TRACEBACK_F(x) (x->m_frame->m_frame.f_exc_traceback)
#define ASSIGN_EXC_TRACEBACK_F(x, tb) x->m_frame->m_frame.f_exc_traceback = (PyObject *)(tb)
#elif PYTHON_VERSION < 0x3b0
#define EXC_TYPE_F(x) (x->m_exc_state.exception_type)
#define EXC_VALUE_F(x) (x->m_exc_state.exception_value)
#define EXC_TRACEBACK_F(x) (x->m_exc_state.exception_tb)
#define ASSIGN_EXC_TRACEBACK_F(x, tb) x->m_exc_state.exception_tb = (PyTracebackObject *)(tb)
#else
#define EXC_VALUE_F(x) (x->m_exc_state.exception_value)
#endif

#if PYTHON_VERSION < 0x3b0
struct Nuitka_ExceptionStackItem {
    PyObject *exception_type;
    PyObject *exception_value;
    PyTracebackObject *exception_tb;
#if PYTHON_VERSION >= 0x370
    _PyErr_StackItem *previous_item;
#endif
};

#if defined(__cplusplus)
#if PYTHON_VERSION >= 0x370
static const struct Nuitka_ExceptionStackItem Nuitka_ExceptionStackItem_Empty = {NULL, NULL, NULL, NULL};
#else
static const struct Nuitka_ExceptionStackItem Nuitka_ExceptionStackItem_Empty = {NULL, NULL, NULL};
#endif
#else
#if PYTHON_VERSION >= 0x370
#define Nuitka_ExceptionStackItem_Empty                                                                                \
    (struct Nuitka_ExceptionStackItem) {                                                                               \
        .exception_type = NULL, .exception_value = NULL, .exception_tb = NULL, .previous_item = NULL                   \
    }
#else
#define Nuitka_ExceptionStackItem_Empty                                                                                \
    (struct Nuitka_ExceptionStackItem) { .exception_type = NULL, .exception_value = NULL, .exception_tb = NULL }
#endif
#endif
#else
struct Nuitka_ExceptionStackItem {
    PyObject *exception_value;
#if PYTHON_VERSION >= 0x370
    _PyErr_StackItem *previous_item;
#endif
};

#if defined(__cplusplus)
static const struct Nuitka_ExceptionStackItem Nuitka_ExceptionStackItem_Empty = {NULL, NULL};
#else
#define Nuitka_ExceptionStackItem_Empty                                                                                \
    (struct Nuitka_ExceptionStackItem) { .exception_value = NULL, .previous_item = NULL }
#endif

#endif

#if PYTHON_VERSION >= 0x370
STATIC_ASSERT(sizeof(struct Nuitka_ExceptionStackItem) == sizeof(_PyErr_StackItem),
              "Exception stack item must match CPython layout");
STATIC_ASSERT(offsetof(struct Nuitka_ExceptionStackItem, exception_value) == offsetof(_PyErr_StackItem, exc_value),
              "Exception stack item value must match CPython layout");
#if PYTHON_VERSION < 0x3b0
STATIC_ASSERT(offsetof(struct Nuitka_ExceptionStackItem, exception_type) == offsetof(_PyErr_StackItem, exc_type),
              "Exception stack item type must match CPython layout");
STATIC_ASSERT(offsetof(struct Nuitka_ExceptionStackItem, exception_tb) == offsetof(_PyErr_StackItem, exc_traceback),
              "Exception stack item traceback must match CPython layout");
#endif
STATIC_ASSERT(offsetof(struct Nuitka_ExceptionStackItem, previous_item) == offsetof(_PyErr_StackItem, previous_item),
              "Exception stack item previous item must match CPython layout");
#endif

// Helper that gets the current thread exception, for use in exception handlers
NUITKA_MAY_BE_UNUSED inline static struct Nuitka_ExceptionStackItem GET_CURRENT_EXCEPTION(PyThreadState *tstate) {
    struct Nuitka_ExceptionStackItem result;
#if PYTHON_VERSION < 0x3b0
    result.exception_type = EXC_TYPE(tstate);
    Py_XINCREF(result.exception_type);
#endif
    result.exception_value = EXC_VALUE(tstate);
    Py_XINCREF(result.exception_value);
#if PYTHON_VERSION < 0x3b0
    result.exception_tb = (PyTracebackObject *)EXC_TRACEBACK(tstate);
    Py_XINCREF(result.exception_tb);
#endif
#if PYTHON_VERSION >= 0x370
    result.previous_item = NULL;
#endif

    return result;
};

#if PYTHON_VERSION < 0x300 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_SYS_EXC_VARS)
#define _NUITKA_MAINTAIN_SYS_EXC_VARS 1
#endif

// Set the published thread exception, transferring ownership from exc_state and
// releasing the previous one.
NUITKA_MAY_BE_UNUSED inline static void SET_CURRENT_EXCEPTION(PyThreadState *tstate,
                                                              struct Nuitka_ExceptionStackItem *exc_state) {
#if PYTHON_VERSION < 0x3b0
    CHECK_OBJECT_X(exc_state->exception_type);
#endif
    CHECK_OBJECT_X(exc_state->exception_value);
#if PYTHON_VERSION < 0x3b0
    CHECK_OBJECT_X(exc_state->exception_tb);
#endif

#if PYTHON_VERSION < 0x3b0
    PyObject *old_type = EXC_TYPE(tstate);
#endif
    PyObject *old_value = EXC_VALUE(tstate);
#if PYTHON_VERSION < 0x3b0
    PyTracebackObject *old_tb = EXC_TRACEBACK(tstate);
#endif

#if PYTHON_VERSION < 0x3b0
    CHECK_OBJECT_X(old_type);
#endif
    CHECK_OBJECT_X(old_value);
#if PYTHON_VERSION < 0x3b0
    CHECK_OBJECT_X(old_tb);
#endif

#if PYTHON_VERSION < 0x3b0
    EXC_TYPE(tstate) = exc_state->exception_type;
#endif
    EXC_VALUE(tstate) = exc_state->exception_value;
#if PYTHON_VERSION < 0x3b0
    SET_EXC_TRACEBACK(tstate, exc_state->exception_tb);
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION:\n");
    PRINT_PUBLISHED_EXCEPTION();
#endif

#if PYTHON_VERSION < 0x3b0
    Py_XDECREF(old_type);
#endif
    Py_XDECREF(old_value);
#if PYTHON_VERSION < 0x3b0
    Py_XDECREF(old_tb);
#endif

#if _NUITKA_MAINTAIN_SYS_EXC_VARS
    // Set sys attributes in the fastest possible way, spell-checker: ignore sysdict
    PyObject *sys_dict = tstate->interp->sysdict;
    CHECK_OBJECT(sys_dict);

    DICT_SET_ITEM_INFALLIBLE(tstate, sys_dict, const_str_plain_exc_type,
                             exc_state->exception_type ? exc_state->exception_type : Py_None);
    DICT_SET_ITEM_INFALLIBLE(tstate, sys_dict, const_str_plain_exc_value,
                             exc_state->exception_value ? exc_state->exception_value : Py_None);
    DICT_SET_ITEM_INFALLIBLE(tstate, sys_dict, const_str_plain_exc_traceback,
                             exc_state->exception_tb ? (PyObject *)exc_state->exception_tb : Py_None);

    if (exc_state->exception_type) {
        assert(Py_REFCNT(exc_state->exception_type) >= 2);
    }
    if (exc_state->exception_value) {
        assert(Py_REFCNT(exc_state->exception_value) >= 2);
    }
    if (exc_state->exception_tb) {
        assert(Py_REFCNT(exc_state->exception_tb) >= 2);
    }
#endif
}

#if PYTHON_VERSION >= 0x3b0
// Helper that sets the current thread exception to a value, for use in the
// "except*" handling, where the match of a clause is published.
NUITKA_MAY_BE_UNUSED static inline void PUBLISH_CURRENT_EXCEPTION_VALUE(PyThreadState *tstate, PyObject *value) {
    CHECK_OBJECT(value);

    Py_INCREF(value);
    struct Nuitka_ExceptionStackItem exc_state = {value};

    SET_CURRENT_EXCEPTION(tstate, &exc_state);
}
#endif

#if PYTHON_VERSION >= 0x370
// Find the stack item that CPython uses for the handled exception visible to
// "sys.exception" and implicit exception chaining, which is the current item
// unless it has no exception, in which case the previous items are searched.
NUITKA_MAY_BE_UNUSED static inline struct Nuitka_ExceptionStackItem *
GET_TOP_MOST_CURRENT_EXCEPTION_STATE(PyThreadState *tstate) {
    struct Nuitka_ExceptionStackItem *exc_state = EXC_STATE(tstate);

    while ((exc_state->exception_value == NULL || exc_state->exception_value == Py_None) &&
           exc_state->previous_item != NULL) {
        exc_state = (struct Nuitka_ExceptionStackItem *)exc_state->previous_item;
    }

    return exc_state;
}
#endif

// Normalize an exception, may release old values and replace them, expects
// references passed and returns them.
NUITKA_MAY_BE_UNUSED static inline void NORMALIZE_EXCEPTION(PyThreadState *tstate, PyObject **exception_type,
                                                            PyObject **exception_value,
                                                            PyTracebackObject **exception_tb);

extern PyObject *NORMALIZE_EXCEPTION_VALUE_FOR_RAISE(PyThreadState *tstate, PyObject *exception_type);

// Helper that sets the current thread exception, and has no reference passed.
// Similar to "PyErr_SetNone".
NUITKA_MAY_BE_UNUSED inline static void SET_CURRENT_EXCEPTION_TYPE0(PyThreadState *tstate, PyObject *exception_type) {
    CHECK_OBJECT(exception_type);

#if PYTHON_VERSION < 0x3c0
    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    Py_INCREF(exception_type);
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION_TYPE0:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
#else
    PyObject *old_exception = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(old_exception);

    // TODO: Make the call, exception creation on the outside somehow.
    PyObject *exception_value = NORMALIZE_EXCEPTION_VALUE_FOR_RAISE(tstate, exception_type);
    ASSERT_NORMALIZED_EXCEPTION_VALUE(exception_value);
    tstate->current_exception = exception_value;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION_TYPE0:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception);
#endif
}

// Same as "PyErr_SetObject" CPython API, use this instead.
NUITKA_MAY_BE_UNUSED inline static void
SET_CURRENT_EXCEPTION_TYPE0_VALUE0(PyThreadState *tstate, PyObject *exception_type, PyObject *exception_value) {
    CHECK_OBJECT(exception_type);
    CHECK_OBJECT(exception_value);

#if PYTHON_VERSION < 0x3c0
    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    Py_INCREF(exception_type);
    tstate->curexc_value = exception_value;
    Py_INCREF(exception_value);
    tstate->curexc_traceback = NULL;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION_TYPE0_VALUE0:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
#else
    PyObject *old_exception_value = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(old_exception_value);

    // TODO: Make the call on the outside.
    NORMALIZE_EXCEPTION(tstate, &exception_type, &exception_value, NULL);
    ASSERT_NORMALIZED_EXCEPTION_VALUE(exception_value);
    tstate->current_exception = exception_value;
    Py_INCREF(exception_value);

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION_TYPE_0_VALUE0:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_value);
#endif
}

// TODO: For Python3.12 it would be nice to know it's normalized already, so we
// can avoid the call to "NORMALIZE_EXCEPTION".
NUITKA_MAY_BE_UNUSED inline static void
SET_CURRENT_EXCEPTION_TYPE0_VALUE1(PyThreadState *tstate, PyObject *exception_type, PyObject *exception_value) {
    CHECK_OBJECT(exception_type);
    CHECK_OBJECT(exception_value);

#if PYTHON_VERSION < 0x3c0
    PyObject *old_exception_type = tstate->curexc_type;
    PyObject *old_exception_value = tstate->curexc_value;
    PyObject *old_exception_traceback = tstate->curexc_traceback;

    tstate->curexc_type = exception_type;
    Py_INCREF(exception_type);
    tstate->curexc_value = exception_value;
    tstate->curexc_traceback = NULL;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION_TYPE0_VALUE1:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_type);
    Py_XDECREF(old_exception_value);
    Py_XDECREF(old_exception_traceback);
#else
    PyObject *old_exception_value = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(old_exception_value);

    // TODO: Make the call, exception creation on the outside somehow.
    NORMALIZE_EXCEPTION(tstate, &exception_type, &exception_value, NULL);
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_value);
    tstate->current_exception = exception_value;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SET_CURRENT_EXCEPTION_TYPE0_VALUE1:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_value);
#endif
}

// Helper that sets the current thread exception, and has no reference passed.
// Same as CPython API PyErr_SetString

NUITKA_MAY_BE_UNUSED inline static void SET_CURRENT_EXCEPTION_TYPE0_STR(PyThreadState *tstate, PyObject *exception_type,
                                                                        char const *value) {
    PyObject *exception_value = Nuitka_String_FromString(value);

    SET_CURRENT_EXCEPTION_TYPE0_VALUE1(tstate, exception_type, exception_value);
}

extern void SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyObject *exception_type, char const *format, char const *value);
extern void SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyObject *exception_type, char const *format, char const *value1,
                                                char const *value2);
extern void SET_CURRENT_EXCEPTION_TYPE0_FORMAT3(PyObject *exception_type, char const *format, char const *value1,
                                                char const *value2, char const *value3);

extern void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(char const *format, PyObject *mistyped);
extern void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_QUALIFIED(char const *format, PyObject *mistyped);
extern void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_QUALIFIED2(char const *format, PyObject *mistyped1,
                                                            PyObject *mistyped2);
extern void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE(char const *format, PyObject *mistyped);

#if PYTHON_VERSION < 0x300

NUITKA_MAY_BE_UNUSED static inline void PRESERVE_FRAME_EXCEPTION(PyThreadState *tstate,
                                                                 struct Nuitka_FrameObject *frame_object) {
    PyFrameObject *frame = (PyFrameObject *)frame_object;

    if (frame->f_exc_type == NULL) {
        if (tstate->exc_type != NULL && tstate->exc_type != Py_None) {
#if _DEBUG_EXCEPTIONS
            PRINT_STRING("PRESERVE_FRAME_EXCEPTION: preserve thread exception\n");
#endif
            frame->f_exc_type = tstate->exc_type;
            Py_INCREF(frame->f_exc_type);
            frame->f_exc_value = tstate->exc_value;
            Py_XINCREF(frame->f_exc_value);
            frame->f_exc_traceback = tstate->exc_traceback;
            Py_XINCREF(frame->f_exc_traceback);
        } else {
#if _DEBUG_EXCEPTIONS
            PRINT_STRING("PRESERVE_FRAME_EXCEPTION: no exception to preserve\n");
#endif
            frame->f_exc_type = Py_None;
            Py_INCREF_IMMORTAL(frame->f_exc_type);
            frame->f_exc_value = NULL;
            frame->f_exc_traceback = NULL;
        }
    }
#if _DEBUG_EXCEPTIONS
    else {
        PRINT_STRING("PRESERVE_FRAME_EXCEPTION: already preserving\n");
    }

    PRINT_ITEM((PyObject *)frame_object);
    PRINT_NEW_LINE();
    PRINT_EXCEPTION(frame->f_exc_type, frame->f_exc_value, (PyTracebackObject *)frame->f_exc_traceback);
#endif
}

NUITKA_MAY_BE_UNUSED static inline void RESTORE_FRAME_EXCEPTION(PyThreadState *tstate,
                                                                struct Nuitka_FrameObject *frame_object) {
    PyFrameObject *frame = (PyFrameObject *)frame_object;

    if (frame->f_exc_type) {
#if _DEBUG_EXCEPTIONS
        PRINT_STRING("RESTORE_FRAME_EXCEPTION: restoring preserved\n");
        PRINT_ITEM((PyObject *)frame_object);
        PRINT_NEW_LINE();
#endif

        struct Nuitka_ExceptionStackItem exc_state;

        exc_state.exception_type = frame->f_exc_type;
        exc_state.exception_value = frame->f_exc_value;
        exc_state.exception_tb = (PyTracebackObject *)frame->f_exc_traceback;

        SET_CURRENT_EXCEPTION(tstate, &exc_state);

        frame->f_exc_type = NULL;
        frame->f_exc_value = NULL;
        frame->f_exc_traceback = NULL;
    }
#if _DEBUG_EXCEPTIONS
    else {
        PRINT_STRING("RESTORE_FRAME_EXCEPTION: nothing to restore\n");
        PRINT_ITEM((PyObject *)frame_object);
        PRINT_NEW_LINE();
    }
#endif
}

#endif

// Similar to "PyException_SetTraceback", only done for Python3.
#if PYTHON_VERSION < 0x300
#define ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(exception_value, exception_tb) ;
#else
NUITKA_MAY_BE_UNUSED static inline void ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(PyObject *exception_value,
                                                                            PyTracebackObject *exception_tb) {
    CHECK_OBJECT(exception_value);
    CHECK_OBJECT_X(exception_tb);

    if (exception_tb == (PyTracebackObject *)Py_None) {
        exception_tb = NULL;
    }

    assert(PyExceptionInstance_Check(exception_value));
    assert(exception_tb == NULL || PyTraceBack_Check(exception_tb));

    PyBaseExceptionObject *e = (PyBaseExceptionObject *)exception_value;

    PyObject *old = e->traceback;
    Py_XINCREF(exception_tb);
    e->traceback = (PyObject *)exception_tb;
    Py_XDECREF(old);
}

// Much like "PyException_GetTraceback", but does not give a reference.
NUITKA_MAY_BE_UNUSED static inline PyTracebackObject *GET_EXCEPTION_TRACEBACK(PyObject *exception_value) {
    CHECK_OBJECT(exception_value);
    assert(PyExceptionInstance_Check(exception_value));

    PyBaseExceptionObject *exc_object = (PyBaseExceptionObject *)(exception_value);
    return (PyTracebackObject *)exc_object->traceback;
}

#endif

// Match an exception value or class against a single exception class, similar to
// "PyErr_GivenExceptionMatches(exception_value, exception_checked)" without tuple support.
// Returns true on a match, false otherwise, and preserves the current exception state.
NUITKA_MAY_BE_UNUSED static bool EXCEPTION_MATCH_BOOL_SINGLE(PyThreadState *tstate, PyObject *exception_value,
                                                             PyObject *exception_checked);

// Clear exception_type if matched, similar to "if (PyErr_ExceptionMatches(exception_type)) PyErr_Clear()".
// Returns true if no exception remains set, false if another exception is active.
NUITKA_MAY_BE_UNUSED static bool _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(PyThreadState *tstate, PyObject *exception_type) {
#if PYTHON_VERSION < 0x3c0
    PyObject *exception_current = tstate->curexc_type;
#else
    PyObject *exception_current = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_current);
#endif
    if (exception_current == NULL) {
        return true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, exception_current, exception_type)) {
        CHECK_OBJECT(exception_current);

#if PYTHON_VERSION < 0x3c0
        // Clear the exception first, we believe we know it doesn't have side effects.
        Py_DECREF(exception_current);
        tstate->curexc_type = NULL;

        PyObject *old_value = tstate->curexc_value;
        PyObject *old_tb = tstate->curexc_traceback;

        tstate->curexc_value = NULL;
        tstate->curexc_traceback = NULL;

        Py_XDECREF(old_value);
        Py_XDECREF(old_tb);
#else
        tstate->current_exception = NULL;
        Py_DECREF(exception_current);
#endif

        return true;
    } else {
        return false;
    }
}

NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(PyThreadState *tstate) {
    return _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_StopIteration);
}

#if PYTHON_VERSION >= 0x350
NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_STOP_ASYNC_ITERATION_OCCURRED(PyThreadState *tstate) {
    return _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_StopAsyncIteration);
}
#endif

NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_GENERATOR_EXIT_OCCURRED(PyThreadState *tstate) {
    return _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_GeneratorExit);
}

NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_KEY_ERROR_OCCURRED(PyThreadState *tstate) {
    return _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_KeyError);
}

NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(PyThreadState *tstate) {
    return _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_AttributeError);
}

NUITKA_MAY_BE_UNUSED static bool CHECK_AND_CLEAR_TYPE_ERROR_OCCURRED(PyThreadState *tstate) {
    return _CHECK_AND_CLEAR_EXCEPTION_OCCURRED(tstate, PyExc_TypeError);
}

#if PYTHON_VERSION >= 0x3c0
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE1(PyThreadState *tstate, PyObject *element1);

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_EXCEPTION_FROM_TYPE_ARG0(PyThreadState *tstate, PyObject *type,
                                                                    PyObject *arg) {
    PyBaseExceptionObject *self;

    PyTypeObject *type_object = (PyTypeObject *)type;

    self = (PyBaseExceptionObject *)(type_object->tp_alloc(type_object, 0));

    self->dict = NULL;
    self->notes = NULL;
    self->traceback = self->cause = self->context = NULL;
    self->suppress_context = 0;

    assert(arg != NULL);

    if (!PyTuple_Check(arg)) {
        self->args = MAKE_TUPLE1(tstate, arg);
    } else {
        self->args = Py_NewRef(arg);
    }

    return (PyObject *)self;
}
#else

extern PyObject *CALL_FUNCTION_WITH_SINGLE_ARG(PyThreadState *tstate, PyObject *called, PyObject *arg);

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_EXCEPTION_FROM_TYPE_ARG0(PyThreadState *tstate, PyObject *type,
                                                                    PyObject *arg) {
    return CALL_FUNCTION_WITH_SINGLE_ARG(tstate, type, arg);
}

#endif

#if PYTHON_VERSION < 0x3c0
struct Nuitka_ExceptionPreservationItem {
    PyObject *exception_type;
    PyObject *exception_value;
    PyTracebackObject *exception_tb;
};

static const struct Nuitka_ExceptionPreservationItem Empty_Nuitka_ExceptionPreservationItem = {0};

// Fetch the current exception into state, transfers reference coming from tstate ownership. Old values are overwritten.
NUITKA_MAY_BE_UNUSED static void FETCH_ERROR_OCCURRED_STATE(PyThreadState *tstate,
                                                            struct Nuitka_ExceptionPreservationItem *exception_state) {
    FETCH_ERROR_OCCURRED(tstate, &exception_state->exception_type, &exception_state->exception_value,
                         &exception_state->exception_tb);
}

// Restore the current exception from state, transfers reference from state to tstate ownership.
NUITKA_MAY_BE_UNUSED static void
RESTORE_ERROR_OCCURRED_STATE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    RESTORE_ERROR_OCCURRED(tstate, exception_state->exception_type, exception_state->exception_value,
                           exception_state->exception_tb);
}

NUITKA_MAY_BE_UNUSED static void
FETCH_ERROR_OCCURRED_STATE_UNTRACED(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    FETCH_ERROR_OCCURRED_UNTRACED(tstate, &exception_state->exception_type, &exception_state->exception_value,
                                  &exception_state->exception_tb);
}

NUITKA_MAY_BE_UNUSED static void
RESTORE_ERROR_OCCURRED_STATE_UNTRACED(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    RESTORE_ERROR_OCCURRED_UNTRACED(tstate, exception_state->exception_type, exception_state->exception_value,
                                    exception_state->exception_tb);
}

NUITKA_MAY_BE_UNUSED static void
ASSERT_SAME_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state1,
                            struct Nuitka_ExceptionPreservationItem const *exception_state2) {
    assert(exception_state1->exception_type == exception_state2->exception_type);
    assert(exception_state1->exception_value == exception_state2->exception_value);
    assert(exception_state1->exception_tb == exception_state2->exception_tb);
}

NUITKA_MAY_BE_UNUSED static void
ASSERT_EMPTY_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    assert(exception_state->exception_type == NULL);
    assert(exception_state->exception_value == NULL);
    assert(exception_state->exception_tb == NULL);
}

NUITKA_MAY_BE_UNUSED static void INIT_ERROR_OCCURRED_STATE(struct Nuitka_ExceptionPreservationItem *exception_state) {
    exception_state->exception_type = NULL;
    exception_state->exception_value = NULL;
    exception_state->exception_tb = NULL;
}

NUITKA_MAY_BE_UNUSED static void
RELEASE_ERROR_OCCURRED_STATE(struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT(exception_state->exception_type);
    CHECK_OBJECT_X(exception_state->exception_value);
    CHECK_OBJECT_X(exception_state->exception_tb);
    Py_DECREF(exception_state->exception_type);
    Py_XDECREF(exception_state->exception_value);
    Py_XDECREF(exception_state->exception_tb);
}

NUITKA_MAY_BE_UNUSED static void
RELEASE_ERROR_OCCURRED_STATE_X(struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT_X(exception_state->exception_type);
    CHECK_OBJECT_X(exception_state->exception_value);
    CHECK_OBJECT_X(exception_state->exception_tb);

    Py_XDECREF(exception_state->exception_type);
    Py_XDECREF(exception_state->exception_value);
    Py_XDECREF(exception_state->exception_tb);
}

NUITKA_MAY_BE_UNUSED static void SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(
    PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state, PyObject *exception_type,
    PyObject *exception_value, PyTracebackObject *exception_tb) {
    Py_INCREF(exception_type);
    Py_XINCREF(exception_value);
    Py_XINCREF(exception_tb);

    exception_state->exception_type = exception_type;
    exception_state->exception_value = exception_value;
    exception_state->exception_tb = exception_tb;
}

NUITKA_MAY_BE_UNUSED static void
ASSIGN_ARGS_FROM_EXCEPTION_PRESERVATION_STATE(struct Nuitka_ExceptionPreservationItem *exception_state,
                                              PyObject **exception_type, PyObject **exception_value,
                                              PyTracebackObject **exception_tb) {

    *exception_type = exception_state->exception_type;
    Py_INCREF(*exception_type);
    *exception_value = exception_state->exception_value;
    Py_XINCREF(*exception_value);
    *exception_tb = exception_state->exception_tb;
    Py_XINCREF(*exception_tb);
}

NUITKA_MAY_BE_UNUSED static PyTracebackObject *
GET_EXCEPTION_STATE_TRACEBACK(struct Nuitka_ExceptionPreservationItem *exception_state) {
    return exception_state->exception_tb;
}

// Transfer ownership of the traceback to the exception state.
NUITKA_MAY_BE_UNUSED static void SET_EXCEPTION_STATE_TRACEBACK(struct Nuitka_ExceptionPreservationItem *exception_state,
                                                               PyTracebackObject *exception_tb) {
    CHECK_OBJECT_X(exception_state->exception_tb);
    CHECK_OBJECT_X(exception_tb);

    Py_XDECREF(exception_state->exception_tb);
    exception_state->exception_tb = exception_tb;
}

NUITKA_MAY_BE_UNUSED static bool HAS_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    return exception_state->exception_type != NULL;
}

NUITKA_MAY_BE_UNUSED static bool
EXCEPTION_STATE_MATCH_BOOL_SINGLE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                  PyObject *exception_checked) {
    return EXCEPTION_MATCH_BOOL_SINGLE(tstate, exception_state->exception_type, exception_checked);
}

NUITKA_MAY_BE_UNUSED inline static void
CHECK_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    CHECK_OBJECT(exception_state->exception_type);
    CHECK_OBJECT_X(exception_state->exception_value);
    CHECK_OBJECT_X(exception_state->exception_tb);
}

NUITKA_MAY_BE_UNUSED inline static void
CHECK_EXCEPTION_STATE_X(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    CHECK_OBJECT_X(exception_state->exception_type);
    CHECK_OBJECT_X(exception_state->exception_value);
    CHECK_OBJECT_X(exception_state->exception_tb);
}

#else
struct Nuitka_ExceptionPreservationItem {
    PyObject *exception_value;
};

static const struct Nuitka_ExceptionPreservationItem Empty_Nuitka_ExceptionPreservationItem = {0};

// Fetch the current exception into state, transfers reference coming from tstate ownership. Old value is overwritten.
NUITKA_MAY_BE_UNUSED static void FETCH_ERROR_OCCURRED_STATE(PyThreadState *tstate,
                                                            struct Nuitka_ExceptionPreservationItem *exception_state) {
    exception_state->exception_value = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_state->exception_value);

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("FETCH_ERROR_OCCURRED_STATE:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    tstate->current_exception = NULL;
}

NUITKA_MAY_BE_UNUSED static void
FETCH_ERROR_OCCURRED_STATE_UNTRACED(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    exception_state->exception_value = tstate->current_exception;
    tstate->current_exception = NULL;

    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_state->exception_value);
}

NUITKA_MAY_BE_UNUSED static void
RESTORE_ERROR_OCCURRED_STATE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    PyObject *old_exception_value = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(old_exception_value);

    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_state->exception_value);
    tstate->current_exception = exception_state->exception_value;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ERROR_OCCURRED_STATE:\n");
    PRINT_CURRENT_EXCEPTION();
#endif

    Py_XDECREF(old_exception_value);
}

NUITKA_MAY_BE_UNUSED static void
RESTORE_ERROR_OCCURRED_STATE_UNTRACED(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    PyObject *old_exception_value = tstate->current_exception;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(old_exception_value);

    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_state->exception_value);
    tstate->current_exception = exception_state->exception_value;

    Py_XDECREF(old_exception_value);
}

NUITKA_MAY_BE_UNUSED static void
ASSERT_SAME_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem *exception_state1,
                            struct Nuitka_ExceptionPreservationItem *exception_state2) {
    assert(exception_state1->exception_value == exception_state2->exception_value);
}

NUITKA_MAY_BE_UNUSED static void
ASSERT_EMPTY_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    assert(exception_state->exception_value == NULL);
}

NUITKA_MAY_BE_UNUSED static void INIT_ERROR_OCCURRED_STATE(struct Nuitka_ExceptionPreservationItem *exception_state) {
    exception_state->exception_value = NULL;
}

NUITKA_MAY_BE_UNUSED static void
RELEASE_ERROR_OCCURRED_STATE(struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT(exception_state->exception_value);
    Py_DECREF(exception_state->exception_value);
}

NUITKA_MAY_BE_UNUSED static void
RELEASE_ERROR_OCCURRED_STATE_X(struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_OBJECT_X(exception_state->exception_value);
    Py_XDECREF(exception_state->exception_value);
}

NUITKA_MAY_BE_UNUSED static void SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(
    PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state, PyObject *exception_type,
    PyObject *exception_value, PyTracebackObject *exception_tb) {

    Py_XINCREF(exception_type);
    Py_XINCREF(exception_value);
    Py_XINCREF(exception_tb);

    NORMALIZE_EXCEPTION(tstate, &exception_type, &exception_value, &exception_tb);
    ASSERT_NORMALIZED_EXCEPTION_VALUE(exception_value);

    exception_state->exception_value = exception_value;
    Py_INCREF(exception_value);

    ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(exception_value, exception_tb);

    Py_XDECREF(exception_type);
    Py_XDECREF(exception_value);
    Py_XDECREF(exception_tb);
}

NUITKA_MAY_BE_UNUSED static void
ASSIGN_ARGS_FROM_EXCEPTION_PRESERVATION_STATE(struct Nuitka_ExceptionPreservationItem *exception_state,
                                              PyObject **exception_type, PyObject **exception_value,
                                              PyTracebackObject **exception_tb) {

    *exception_value = exception_state->exception_value;

    if (*exception_value) {
        Py_INCREF(*exception_value);

        *exception_type = (PyObject *)PyExceptionInstance_Class(*exception_value);
        Py_INCREF(*exception_type);
        *exception_tb = GET_EXCEPTION_TRACEBACK(*exception_value);
        Py_XINCREF(*exception_tb);
    } else {
        *exception_type = NULL;
        *exception_tb = NULL;
    }
}

NUITKA_MAY_BE_UNUSED static PyTracebackObject *
GET_EXCEPTION_STATE_TRACEBACK(struct Nuitka_ExceptionPreservationItem *exception_state) {
    return GET_EXCEPTION_TRACEBACK(exception_state->exception_value);
}

// Transfer ownership of the traceback to the exception state.
NUITKA_MAY_BE_UNUSED static void SET_EXCEPTION_STATE_TRACEBACK(struct Nuitka_ExceptionPreservationItem *exception_state,
                                                               PyTracebackObject *exception_tb) {
    ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(exception_state->exception_value, exception_tb);
    Py_XDECREF(exception_tb);
    CHECK_OBJECT_X(exception_tb);
}

NUITKA_MAY_BE_UNUSED static bool HAS_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    return exception_state->exception_value != NULL;
}

NUITKA_MAY_BE_UNUSED static bool
EXCEPTION_STATE_MATCH_BOOL_SINGLE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem const *exception_state,
                                  PyObject *exception_checked) {
    return EXCEPTION_MATCH_BOOL_SINGLE(tstate, exception_state->exception_value, exception_checked);
}

NUITKA_MAY_BE_UNUSED inline static void
CHECK_EXCEPTION_STATE(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    ASSERT_NORMALIZED_EXCEPTION_VALUE(exception_state->exception_value);
}

NUITKA_MAY_BE_UNUSED inline static void
CHECK_EXCEPTION_STATE_X(struct Nuitka_ExceptionPreservationItem const *exception_state) {
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_state->exception_value);
}

#endif

NUITKA_MAY_BE_UNUSED inline static void SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0(
    PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state, PyObject *exception_type) {

    SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, exception_state, exception_type, NULL, NULL);
}

extern PyObject *CALL_FUNCTION_WITH_SINGLE_ARG(PyThreadState *tstate, PyObject *called, PyObject *arg);

NUITKA_MAY_BE_UNUSED inline static void
SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(PyThreadState *tstate,
                                                   struct Nuitka_ExceptionPreservationItem *exception_state,
                                                   PyObject *exception_type, PyObject *exception_value) {
#if PYTHON_VERSION < 0x3c0
    Py_INCREF(exception_type);

    exception_state->exception_type = exception_type;
    exception_state->exception_value = exception_value;
    exception_state->exception_tb = NULL;
#else
    PyObject *exc = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, exception_type, exception_value);
    exception_state->exception_value = exc;
    Py_DECREF(exception_value);
#endif
}

NUITKA_MAY_BE_UNUSED inline static void
SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1_NORMALIZED(PyThreadState *tstate,
                                                              struct Nuitka_ExceptionPreservationItem *exception_state,
                                                              PyObject *exception_type, PyObject *exception_value) {
#if PYTHON_VERSION < 0x3c0
    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, exception_type, exception_value);
#else
    exception_state->exception_value = exception_value;
#endif
}

NUITKA_MAY_BE_UNUSED inline static void
SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE0(PyThreadState *tstate,
                                                   struct Nuitka_ExceptionPreservationItem *exception_state,
                                                   PyObject *exception_type, PyObject *exception_value) {
    // TODO: Add variants for normalized values only.
    SET_EXCEPTION_PRESERVATION_STATE_FROM_ARGS(tstate, exception_state, exception_type, exception_value, NULL);
}

NUITKA_MAY_BE_UNUSED inline static void
SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(PyThreadState *tstate,
                                                struct Nuitka_ExceptionPreservationItem *exception_state,
                                                PyObject *exception_type, char const *value) {
    PyObject *exception_value = Nuitka_String_FromString(value);

    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, exception_type, exception_value);
}

#define SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_FORMAT1(tstate, exception_state, exception_type, message, arg1)    \
    {                                                                                                                  \
        PyObject *exception_value = Nuitka_String_FromFormat(message, arg1);                                           \
        CHECK_OBJECT(exception_value);                                                                                 \
        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, exception_type, exception_value);  \
    }

#define SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_FORMAT2(tstate, exception_state, exception_type, message, arg1,    \
                                                            arg2)                                                      \
    {                                                                                                                  \
        PyObject *exception_value = Nuitka_String_FromFormat(message, arg1, arg2);                                     \
        CHECK_OBJECT(exception_value);                                                                                 \
        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, exception_type, exception_value);  \
    }

NUITKA_MAY_BE_UNUSED static bool EXCEPTION_MATCH_GENERATOR(PyThreadState *tstate, PyObject *exception_value) {
    CHECK_OBJECT(exception_value);

    // TODO: For Python3.12 this must be done differently to be a lot better.

    if (PyExceptionInstance_Check(exception_value)) {
        exception_value = PyExceptionInstance_Class(exception_value);
    }

    if (exception_value == PyExc_GeneratorExit || exception_value == PyExc_StopIteration) {
        return true;
    }

    if (PyExceptionClass_Check(exception_value)) {
#if PYTHON_VERSION < 0x300
        struct Nuitka_ExceptionPreservationItem saved_exception_state;
        FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        int res = Nuitka_Object_IsSubclass(tstate, exception_value, PyExc_GeneratorExit);

        if (unlikely(res == -1)) {
            Nuitka_WriteUnraisable(tstate, exception_value);
        }

        if (res != 1) {
            res = Nuitka_Object_IsSubclass(tstate, exception_value, PyExc_StopIteration);

            if (unlikely(res == -1)) {
                Nuitka_WriteUnraisable(tstate, exception_value);
            }
        }

        RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        return res == 1;
#else
        return Nuitka_Type_IsSubtype((PyTypeObject *)exception_value, (PyTypeObject *)PyExc_GeneratorExit) ||
               Nuitka_Type_IsSubtype((PyTypeObject *)exception_value, (PyTypeObject *)PyExc_StopIteration);
#endif
    }

    return false;
}

NUITKA_MAY_BE_UNUSED static bool
EXCEPTION_STATE_MATCH_GENERATOR(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
#if PYTHON_VERSION < 0x3c0
    return EXCEPTION_MATCH_GENERATOR(tstate, exception_state->exception_type);
#else
    return EXCEPTION_MATCH_GENERATOR(tstate, exception_state->exception_value);
#endif
}

NUITKA_MAY_BE_UNUSED static bool EXCEPTION_MATCH_BOOL_SINGLE(PyThreadState *tstate, PyObject *exception_value,
                                                             PyObject *exception_checked) {
    CHECK_OBJECT(exception_value);
    CHECK_OBJECT(exception_checked);

    if (PyExceptionInstance_Check(exception_value)) {
        exception_value = PyExceptionInstance_Class(exception_value);
    }

    if (exception_value == exception_checked) {
        return true;
    }

    if (PyExceptionClass_Check(exception_value)) {
#if PYTHON_VERSION < 0x300
        struct Nuitka_ExceptionPreservationItem saved_exception_state;
        FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        // Python 2 old-style class exceptions require Nuitka_Object_IsSubclass;
        // Python 3 BaseException subclasses use Nuitka_Type_IsSubtype directly.
        int res = Nuitka_Object_IsSubclass(tstate, exception_value, exception_checked);

        if (unlikely(res == -1)) {
            Nuitka_WriteUnraisable(tstate, exception_value);
        }

        RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        return res == 1;
#else
        int res = Nuitka_Type_IsSubtype((PyTypeObject *)exception_value, (PyTypeObject *)exception_checked);
        return res == 1;
#endif
    }

    return false;
}

NUITKA_MAY_BE_UNUSED static inline int _EXCEPTION_MATCH_BOOL(PyThreadState *tstate, PyObject *exception_value,
                                                             PyObject *exception_checked) {
    CHECK_OBJECT(exception_value);
    CHECK_OBJECT(exception_checked);

    // TODO: Can this not be an instance from called code?!
    PyObject *exception_class;
    if (PyExceptionInstance_Check(exception_value)) {
        exception_class = PyExceptionInstance_Class(exception_value);
    } else {
        exception_class = exception_value;
    }

#if PYTHON_VERSION < 0x300
    if (PyExceptionClass_Check(exception_class) && PyExceptionClass_Check(exception_checked)) {
        struct Nuitka_ExceptionPreservationItem saved_exception_state;
        FETCH_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        // Avoid recursion limit being exceeded just then
        int recursion_limit = Py_GetRecursionLimit();
        if (recursion_limit < (1 << 30)) {
            Py_SetRecursionLimit(recursion_limit + 5);
        }

        int res = Nuitka_Object_IsSubclass(tstate, exception_class, exception_checked);

        Py_SetRecursionLimit(recursion_limit);

        if (unlikely(res == -1)) {
            Nuitka_WriteUnraisable(tstate, exception_value);
            res = 0;
        }

        RESTORE_ERROR_OCCURRED_STATE(tstate, &saved_exception_state);

        return res;
    } else {
        return exception_class == exception_checked;
    }
#else
    if (PyExceptionClass_Check(exception_class) && PyExceptionClass_Check(exception_checked)) {
        return Nuitka_Type_IsSubtype((PyTypeObject *)exception_class, (PyTypeObject *)exception_checked);
    } else {
        return exception_class == exception_checked;
    }
#endif
}

// This is for the actual comparison operation that is being done in the
// node tree, no other code should use it. TODO: Then it's probably not
// properly located here.
NUITKA_MAY_BE_UNUSED static inline int EXCEPTION_MATCH_BOOL(PyThreadState *tstate, PyObject *exception_value,
                                                            PyObject *exception_checked) {
    CHECK_OBJECT(exception_value);
    CHECK_OBJECT(exception_checked);

#if PYTHON_VERSION >= 0x300
    // Validate all tuple elements inherit from BaseException before matching
    // earlier elements, matching Python 3 semantics.
    if (PyTuple_Check(exception_checked)) {
        Py_ssize_t length = PyTuple_GET_SIZE(exception_checked);

        for (Py_ssize_t i = 0; i < length; i += 1) {
            PyObject *element = PyTuple_GET_ITEM(exception_checked, i);

            if (unlikely(!PyExceptionClass_Check(element))) {
                SET_CURRENT_EXCEPTION_TYPE0_STR(
                    tstate, PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed");
                return -1;
            }
        }
    } else if (unlikely(!PyExceptionClass_Check(exception_checked))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "catching classes that do not inherit from BaseException is not allowed");
        return -1;
    }
#endif

    if (PyTuple_Check(exception_checked)) {
        Py_ssize_t length = PyTuple_GET_SIZE(exception_checked);

        for (Py_ssize_t i = 0; i < length; i += 1) {
            PyObject *element = PyTuple_GET_ITEM(exception_checked, i);

            int res = EXCEPTION_MATCH_BOOL(tstate, exception_value, element);

            if (res != 0) {
                return res;
            }
        }

        return 0;
    } else {
        return _EXCEPTION_MATCH_BOOL(tstate, exception_value, exception_checked);
    }
}

extern void Nuitka_Err_NormalizeException(PyThreadState *tstate, PyObject **exc, PyObject **val,
                                          PyTracebackObject **tb);

// Normalize an exception, may release old values and replace them, expects
// references passed and returns them.
NUITKA_MAY_BE_UNUSED static inline void NORMALIZE_EXCEPTION(PyThreadState *tstate, PyObject **exception_type,
                                                            PyObject **exception_value,
                                                            PyTracebackObject **exception_tb) {
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("NORMALIZE_EXCEPTION: Enter\n");
    PRINT_EXCEPTION(*exception_type, *exception_value, *exception_tb);
#endif
    CHECK_OBJECT_X(*exception_type);
    CHECK_OBJECT_X(*exception_value);
    if (exception_tb) {
        CHECK_OBJECT_X(*exception_tb);
    }

    // TODO: Often we already know this to be true.
    if (*exception_type != Py_None && *exception_type != NULL) {
        Nuitka_Err_NormalizeException(tstate, exception_type, exception_value, exception_tb);
    }

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("NORMALIZE_EXCEPTION: Leave\n");
    PRINT_EXCEPTION(*exception_type, *exception_value, exception_tb ? *exception_tb : NULL);
#endif
}

#if PYTHON_VERSION < 0x3c0
static inline void NORMALIZE_EXCEPTION_STATE(PyThreadState *tstate,
                                             struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_EXCEPTION_STATE_X(exception_state);

    NORMALIZE_EXCEPTION(tstate, &exception_state->exception_type, &exception_state->exception_value,
                        &exception_state->exception_tb);
}
#endif

extern PyObject *CALL_FUNCTION_NO_ARGS(PyThreadState *tstate, PyObject *called);

// Publish an exception, erasing the values of the variables.
NUITKA_MAY_BE_UNUSED static inline void
PUBLISH_CURRENT_EXCEPTION(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("PUBLISH_CURRENT_EXCEPTION:\n");
    PRINT_EXCEPTION_STATE(exception_state);
#endif

#if PYTHON_VERSION < 0x3c0
    NORMALIZE_EXCEPTION_STATE(tstate, exception_state);
    ATTACH_TRACEBACK_TO_EXCEPTION_VALUE(exception_state->exception_value, exception_state->exception_tb);
#endif

    struct Nuitka_ExceptionStackItem exc_state;

#if PYTHON_VERSION < 0x3b0
    exc_state.exception_type = exception_state->exception_type;
#endif
    exc_state.exception_value = exception_state->exception_value;
#if PYTHON_VERSION < 0x3b0
    exc_state.exception_tb = exception_state->exception_tb;
#endif

    SET_CURRENT_EXCEPTION(tstate, &exc_state);

#if PYTHON_VERSION >= 0x3b0 && PYTHON_VERSION < 0x3c0
    // TODO: We shouldn't get these in the first place, we don't transfer the
    // type anymore and the exception tb could come in already attached.
    Py_DECREF(exception_state->exception_type);
    Py_XDECREF(exception_state->exception_tb);
#endif

    INIT_ERROR_OCCURRED_STATE(exception_state);
}

NUITKA_MAY_BE_UNUSED static bool
_CHECK_AND_CLEAR_EXCEPTION_STATE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                 PyObject *exception_type) {
#if PYTHON_VERSION < 0x3c0
    PyObject *exception_current = exception_state->exception_type;
#else
    PyObject *exception_current = exception_state->exception_value;
    ASSERT_NORMALIZED_EXCEPTION_VALUE_X(exception_current);
#endif
    if (exception_current == NULL) {
        return true;
    } else if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, exception_current, exception_type)) {
        CHECK_OBJECT(exception_current);

        RELEASE_ERROR_OCCURRED_STATE(exception_state);
        INIT_ERROR_OCCURRED_STATE(exception_state);

        return true;
    } else {
        return false;
    }
}

// TODO: Get rid of "CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED" and rename this to
// its name.
NUITKA_MAY_BE_UNUSED static bool
CHECK_AND_CLEAR_STOP_ITERATION_STATE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    return _CHECK_AND_CLEAR_EXCEPTION_STATE(tstate, exception_state, PyExc_StopIteration);
}

#if PYTHON_VERSION >= 0x300
static inline PyBaseExceptionObject *_Nuitka_PyBaseExceptionObject_cast(PyObject *exc) {
    CHECK_OBJECT(exc);
    assert(PyExceptionInstance_Check(exc));
    return (PyBaseExceptionObject *)exc;
}

// Exception context, replacement for "PyException_GetContext", it however gives no
// reference.
NUITKA_MAY_BE_UNUSED static inline PyObject *Nuitka_Exception_GetContext(PyObject *self) {
    return _Nuitka_PyBaseExceptionObject_cast(self)->context;
}

// Exception context, replacement for "PyException_SetContext" it however doesn't
// consume a reference.
NUITKA_MAY_BE_UNUSED static inline void Nuitka_Exception_SetContext(PyObject *self, PyObject *context) {
    CHECK_OBJECT(self);
    CHECK_OBJECT(context);

    Py_INCREF(context);
    Py_XSETREF(_Nuitka_PyBaseExceptionObject_cast(self)->context, context);
}

NUITKA_MAY_BE_UNUSED static inline void Nuitka_Exception_DeleteContext(PyObject *self) {
    Py_XSETREF(_Nuitka_PyBaseExceptionObject_cast(self)->context, NULL);
}

#if PYTHON_VERSION >= 0x370
// Set the context of the currently raised exception to the current handled
// exception, similar to CPython's "_PyErr_ChainStackItem".
NUITKA_MAY_BE_UNUSED static inline void CHAIN_EXCEPTION_STACK_ITEM(PyThreadState *tstate) {
    struct Nuitka_ExceptionStackItem *exc_state = EXC_STATE(tstate);
    PyObject *handled_exception = exc_state->exception_value;

    if (handled_exception == NULL || handled_exception == Py_None) {
        return;
    }

    struct Nuitka_ExceptionPreservationItem exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &exception_state);

#if PYTHON_VERSION < 0x3c0
    NORMALIZE_EXCEPTION_STATE(tstate, &exception_state);
#endif

    PyObject *current_exception = exception_state.exception_value;
    ASSERT_NORMALIZED_EXCEPTION_VALUE(current_exception);

    if (current_exception != handled_exception) {
        PyObject *chain_exception = handled_exception;

        while (true) {
            PyObject *context = Nuitka_Exception_GetContext(chain_exception);
            if (context == NULL) {
                break;
            }

            CHECK_OBJECT(context);

            if (context == current_exception) {
                Nuitka_Exception_DeleteContext(chain_exception);
                break;
            }

            chain_exception = context;
        }

        Nuitka_Exception_SetContext(current_exception, handled_exception);
    }

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
}
#endif

#if PYTHON_VERSION >= 0x300
NUITKA_MAY_BE_UNUSED static inline void
ADD_EXCEPTION_CONTEXT(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
#if PYTHON_VERSION >= 0x370
    PyObject *context = GET_TOP_MOST_CURRENT_EXCEPTION_STATE(tstate)->exception_value;
#else
    PyObject *context = EXC_VALUE(tstate);
#endif

    if (context != NULL && context != Py_None) {
#if PYTHON_VERSION < 0x3c0
        NORMALIZE_EXCEPTION_STATE(tstate, exception_state);
#endif
        Nuitka_Exception_SetContext(exception_state->exception_value, context);
    }
}
#endif

// Our replacement for "PyException_SetCause", consumes a reference.
NUITKA_MAY_BE_UNUSED static inline void Nuitka_Exception_SetCause(PyObject *self, PyObject *cause) {
    PyBaseExceptionObject *base_self = _Nuitka_PyBaseExceptionObject_cast(self);
    base_self->suppress_context = 1;
    Py_XSETREF(base_self->cause, cause);
}

#endif

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
