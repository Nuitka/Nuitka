//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_COMPILED_COROUTINE_H__
#define __NUITKA_COMPILED_COROUTINE_H__

#if PYTHON_VERSION >= 0x350

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#ifdef __cplusplus
enum Await_Kind {
    await_normal, // user "await"
    await_enter,  // "async with" __aenter__
    await_exit    // "async with" __aexit__
};
#else
typedef int Await_Kind;
static const int await_normal = 0;
static const int await_enter = 1;
static const int await_exit = 2;
#endif

struct Nuitka_CoroutineObject {
    PyObject_VAR_HEAD

        PyObject *m_name;

    // TODO: Only to make traceback for non-started throw
    PyObject *m_module;

    PyObject *m_qualname;
    PyObject *m_yield_from;

#if 0x300 <= PYTHON_VERSION && PYTHON_VERSION < 0x370
    bool m_yield_from_exception_preserving;
#endif

    PyObject *m_weakrefs;

    int m_running;
    int m_awaiting;

    void *m_code;

    struct Nuitka_FrameObject *m_frame;

    PyCodeObject *m_code_object;

    // Active caller frame saved across yields and restored when resuming.
    Nuitka_ThreadStateFrameType *m_resume_frame;

    Generator_Status m_status;

#if PYTHON_VERSION == 0x3c0
    // CPython 3.12.0 fails to clear the frame of a coroutine that is closed
    // before it started, and therefore reports it as created, and we mimic
    // that for compatibility.
    int m_closed_before_start;
#endif

#if PYTHON_VERSION >= 0x370
    struct Nuitka_ExceptionStackItem m_exc_state;
    PyObject *m_origin;
#endif

    // The label index to resume after yield.
    int m_yield_return_index;

    // Return value when coroutine finishes (yielded value is NULL); NULL while yielding.
    PyObject *m_returned;

    // Unique per-instance identifier used in comparisons.
    long m_counter;

    void *m_heap_storage;

    // Trailing flexible array allocated with space for m_closure_given cells plus heap storage.
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Coroutine_Type;

typedef PyObject *(*coroutine_code)(PyThreadState *tstate, struct Nuitka_CoroutineObject *, PyObject *);

extern PyObject *Nuitka_Coroutine_New(PyThreadState *tstate, coroutine_code code, PyObject *module, PyObject *name,
                                      PyObject *qualname, PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                      Py_ssize_t closure_given, Py_ssize_t heap_storage_size);

static inline bool Nuitka_Coroutine_Check(PyObject *obj) { return Py_TYPE(obj) == &Nuitka_Coroutine_Type; }

struct Nuitka_CoroutineWrapperObject {
    PyObject_HEAD

        struct Nuitka_CoroutineObject *m_coroutine;
};

extern PyTypeObject Nuitka_CoroutineWrapper_Type;

static inline bool Nuitka_CoroutineWrapper_Check(PyObject *obj) {
    return Py_TYPE(obj) == &Nuitka_CoroutineWrapper_Type;
}

static inline void SAVE_COROUTINE_EXCEPTION(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine) {
    /* Before Python3.7: When yielding from an exception handler in Python3,
     * the exception preserved to the frame is restored, while the current one
     * is put as there.
     *
     * Python3.7: The exception is preserved in the coroutine object itself,
     * which is made the current exception state while the coroutine runs.
     */

#if PYTHON_VERSION < 0x370
#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(tstate);
#endif
    PyObject *saved_exception_value = EXC_VALUE(tstate);
#if PYTHON_VERSION < 0x3b0
    PyTracebackObject *saved_exception_traceback = EXC_TRACEBACK(tstate);
#endif

    EXC_TYPE(tstate) = tstate->frame->f_exc_type;
    EXC_VALUE(tstate) = tstate->frame->f_exc_value;
    SET_EXC_TRACEBACK(tstate, tstate->frame->f_exc_traceback);

    tstate->frame->f_exc_type = saved_exception_type;
    tstate->frame->f_exc_value = saved_exception_value;
    tstate->frame->f_exc_traceback = (PyObject *)saved_exception_traceback;
#else
    assert(coroutine->m_exc_state.previous_item == NULL);

    coroutine->m_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = (_PyErr_StackItem *)&coroutine->m_exc_state;
#endif
}

static inline void RESTORE_COROUTINE_EXCEPTION(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine) {
    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.

#if PYTHON_VERSION < 0x370
#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(tstate);
#endif
    PyObject *saved_exception_value = EXC_VALUE(tstate);
#if PYTHON_VERSION < 0x3b0
    PyTracebackObject *saved_exception_traceback = EXC_TRACEBACK(tstate);
#endif

    EXC_TYPE(tstate) = tstate->frame->f_exc_type;
    EXC_VALUE(tstate) = tstate->frame->f_exc_value;
    SET_EXC_TRACEBACK(tstate, tstate->frame->f_exc_traceback);

    tstate->frame->f_exc_type = saved_exception_type;
    tstate->frame->f_exc_value = saved_exception_value;
    tstate->frame->f_exc_traceback = (PyObject *)saved_exception_traceback;
#else
    assert(coroutine->m_exc_state.previous_item != NULL);

    tstate->exc_info = coroutine->m_exc_state.previous_item;
    coroutine->m_exc_state.previous_item = NULL;
#endif
}

#if 0x300 <= PYTHON_VERSION && PYTHON_VERSION < 0x370
static inline void SAVE_COROUTINE_EXCEPTION_FROM_THREAD(PyThreadState *tstate,
                                                        struct Nuitka_CoroutineObject *coroutine) {
    PyObject *old_type = EXC_TYPE_F(coroutine);
    PyObject *old_value = EXC_VALUE_F(coroutine);
    PyObject *old_tb = EXC_TRACEBACK_F(coroutine);

    EXC_TYPE_F(coroutine) = EXC_TYPE(tstate);
    Py_XINCREF(EXC_TYPE_F(coroutine));
    EXC_VALUE_F(coroutine) = EXC_VALUE(tstate);
    Py_XINCREF(EXC_VALUE_F(coroutine));
    ASSIGN_EXC_TRACEBACK_F(coroutine, EXC_TRACEBACK(tstate));
    Py_XINCREF(EXC_TRACEBACK_F(coroutine));

    Py_XDECREF(old_type);
    Py_XDECREF(old_value);
    Py_XDECREF(old_tb);
}

static inline void RESUME_COROUTINE_EXCEPTION(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine,
                                              bool throw_flag) {
    if (throw_flag || EXC_TYPE_F(coroutine) == NULL || EXC_TYPE_F(coroutine) == Py_None) {
        SAVE_COROUTINE_EXCEPTION_FROM_THREAD(tstate, coroutine);
    } else {
        SAVE_COROUTINE_EXCEPTION(tstate, coroutine);
    }
}

static inline void RESTORE_AND_CLEAR_COROUTINE_EXCEPTION(PyThreadState *tstate,
                                                         struct Nuitka_CoroutineObject *coroutine) {
    assert(coroutine->m_frame != NULL);

    struct Nuitka_ExceptionStackItem exc_state;

    exc_state.exception_type = EXC_TYPE_F(coroutine);
    exc_state.exception_value = EXC_VALUE_F(coroutine);
    exc_state.exception_tb = (PyTracebackObject *)EXC_TRACEBACK_F(coroutine);

    SET_CURRENT_EXCEPTION(tstate, &exc_state);

    EXC_TYPE_F(coroutine) = NULL;
    EXC_VALUE_F(coroutine) = NULL;
    EXC_TRACEBACK_F(coroutine) = NULL;
}
#endif

extern PyObject *ASYNC_MAKE_ITERATOR(PyThreadState *tstate, PyObject *value);

extern PyObject *ASYNC_ITERATOR_NEXT(PyThreadState *tstate, PyObject *value);

extern PyObject *ASYNC_AWAIT(PyThreadState *tstate, PyObject *awaitable, Await_Kind await_kind);

NUITKA_MAY_BE_UNUSED static void STORE_COROUTINE_EXCEPTION(PyThreadState *tstate,
                                                           struct Nuitka_CoroutineObject *coroutine) {
#if 0x300 <= PYTHON_VERSION && PYTHON_VERSION < 0x370
    SAVE_COROUTINE_EXCEPTION_FROM_THREAD(tstate, coroutine);
#else
#if PYTHON_VERSION < 0x3b0
    EXC_TYPE_F(coroutine) = EXC_TYPE(tstate);
    if (EXC_TYPE_F(coroutine) == Py_None) {
        EXC_TYPE_F(coroutine) = NULL;
    }
    Py_XINCREF(EXC_TYPE_F(coroutine));
#endif
    EXC_VALUE_F(coroutine) = EXC_VALUE(tstate);
    Py_XINCREF(EXC_VALUE_F(coroutine));
#if PYTHON_VERSION < 0x3b0
    ASSIGN_EXC_TRACEBACK_F(coroutine, EXC_TRACEBACK(tstate));
    Py_XINCREF(EXC_TRACEBACK_F(coroutine));
#endif
#endif
}
NUITKA_MAY_BE_UNUSED static void DROP_COROUTINE_EXCEPTION(struct Nuitka_CoroutineObject *coroutine) {
#if PYTHON_VERSION < 0x3b0
    Py_CLEAR(EXC_TYPE_F(coroutine));
#endif
    Py_CLEAR(EXC_VALUE_F(coroutine));
#if PYTHON_VERSION < 0x3b0
    Py_CLEAR(EXC_TRACEBACK_F(coroutine));
#endif
#if PYTHON_VERSION >= 0x370
    coroutine->m_exc_state.previous_item = NULL;
#endif
}

#if _DEBUG_REFCOUNTS
extern int count_active_Nuitka_Coroutine_Type;
extern int count_allocated_Nuitka_Coroutine_Type;
extern int count_released_Nuitka_Coroutine_Type;

extern int count_active_Nuitka_CoroutineWrapper_Type;
extern int count_allocated_Nuitka_CoroutineWrapper_Type;
extern int count_released_Nuitka_CoroutineWrapper_Type;

extern int count_active_Nuitka_AIterWrapper_Type;
extern int count_allocated_Nuitka_AIterWrapper_Type;
extern int count_released_Nuitka_AIterWrapper_Type;
#endif

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
