//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_COMPILED_COROUTINE_H__
#define __NUITKA_COMPILED_COROUTINE_H__

// Compiled coroutine type.

// Another cornerstone of the integration into CPython. Try to behave as well as
// normal coroutine objects do or even better.

#if PYTHON_VERSION >= 0x350

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// The Nuitka_CoroutineObject is the storage associated with a compiled
// coroutine object instance of which there can be many for each code.
struct Nuitka_CoroutineObject {
    /* Python object folklore: */
    PyObject_VAR_HEAD

        PyObject *m_name;

    // TODO: Only to make traceback for non-started throw
    PyObject *m_module;

    PyObject *m_qualname;
    PyObject *m_yield_from;

    // Weak references are supported for coroutine objects in CPython.
    PyObject *m_weakrefs;

    int m_running;

    // When a coroutine is awaiting, this flag is set.
    int m_awaiting;

    void *m_code;

    // The parent frame of the coroutine, if created.
    struct Nuitka_FrameObject *m_frame;

    PyCodeObject *m_code_object;

    // While yielding, this was the frame currently active, restore when
    // resuming.
    Nuitka_ThreadStateFrameType *m_resume_frame;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

#if PYTHON_VERSION >= 0x370
    struct Nuitka_ExceptionStackItem m_exc_state;

    // The cr_origin attribute.
    PyObject *m_origin;
#endif

    // The label index to resume after yield.
    int m_yield_return_index;

    // Returned value if yielded value is NULL, is
    // NULL if not a return
    PyObject *m_returned;

    // A kind of uuid for the coroutine object, used in comparisons.
    long m_counter;

    /* The heap of coroutine objects at run time. */
    void *m_heap_storage;

    /* Closure variables given, if any, we reference cells here. The last
     * part is dynamically allocated, the array size differs per coroutine
     * and includes the heap storage.
     */
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Coroutine_Type;

typedef PyObject *(*coroutine_code)(PyThreadState *tstate, struct Nuitka_CoroutineObject *, PyObject *);

extern PyObject *Nuitka_Coroutine_New(PyThreadState *tstate, coroutine_code code, PyObject *module, PyObject *name,
                                      PyObject *qualname, PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                      Py_ssize_t closure_given, Py_ssize_t heap_storage_size);

static inline bool Nuitka_Coroutine_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_Coroutine_Type; }

struct Nuitka_CoroutineWrapperObject {
    /* Python object folklore: */
    PyObject_HEAD

        struct Nuitka_CoroutineObject *m_coroutine;
};

extern PyTypeObject Nuitka_CoroutineWrapper_Type;

static inline bool Nuitka_CoroutineWrapper_Check(PyObject *object) {
    return Py_TYPE(object) == &Nuitka_CoroutineWrapper_Type;
}

static inline void SAVE_COROUTINE_EXCEPTION(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine) {
    /* Before Python3.7: When yielding from an exception handler in Python3,
     * the exception preserved to the frame is restored, while the current one
     * is put as there.
     *
     * Python3.7: The exception is preserved in the coroutine object itself
     * which has a new "m_exc_state" structure just for that.
     */

#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(tstate);
#endif
    PyObject *saved_exception_value = EXC_VALUE(tstate);
#if PYTHON_VERSION < 0x3b0
    PyTracebackObject *saved_exception_traceback = EXC_TRACEBACK(tstate);
#endif

#if PYTHON_VERSION < 0x370
    EXC_TYPE(tstate) = tstate->frame->f_exc_type;
    EXC_VALUE(tstate) = tstate->frame->f_exc_value;
    SET_EXC_TRACEBACK(tstate, tstate->frame->f_exc_traceback);
#else
#if PYTHON_VERSION < 0x3b0
    EXC_TYPE(tstate) = coroutine->m_exc_state.exception_type;
#endif
    EXC_VALUE(tstate) = coroutine->m_exc_state.exception_value;
#if PYTHON_VERSION < 0x3b0
    SET_EXC_TRACEBACK(tstate, coroutine->m_exc_state.exception_tb);
#endif
#endif

#if PYTHON_VERSION < 0x370
    tstate->frame->f_exc_type = saved_exception_type;
    tstate->frame->f_exc_value = saved_exception_value;
    tstate->frame->f_exc_traceback = (PyObject *)saved_exception_traceback;
#else
#if PYTHON_VERSION < 0x3b0
    coroutine->m_exc_state.exception_type = saved_exception_type;
#endif
    coroutine->m_exc_state.exception_value = saved_exception_value;
#if PYTHON_VERSION < 0x3b0
    coroutine->m_exc_state.exception_tb = (PyTracebackObject *)saved_exception_traceback;
#endif
#endif
}

static inline void RESTORE_COROUTINE_EXCEPTION(PyThreadState *tstate, struct Nuitka_CoroutineObject *coroutine) {
    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.

#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(tstate);
#endif
    PyObject *saved_exception_value = EXC_VALUE(tstate);
#if PYTHON_VERSION < 0x3b0
    PyTracebackObject *saved_exception_traceback = EXC_TRACEBACK(tstate);
#endif

#if PYTHON_VERSION < 0x370
    EXC_TYPE(tstate) = tstate->frame->f_exc_type;
    EXC_VALUE(tstate) = tstate->frame->f_exc_value;
    SET_EXC_TRACEBACK(tstate, tstate->frame->f_exc_traceback);

    tstate->frame->f_exc_type = saved_exception_type;
    tstate->frame->f_exc_value = saved_exception_value;
    tstate->frame->f_exc_traceback = (PyObject *)saved_exception_traceback;
#else
#if PYTHON_VERSION < 0x3b0
    EXC_TYPE(tstate) = coroutine->m_exc_state.exception_type;
#endif
    EXC_VALUE(tstate) = coroutine->m_exc_state.exception_value;
#if PYTHON_VERSION < 0x3b0
    SET_EXC_TRACEBACK(tstate, coroutine->m_exc_state.exception_tb);
#endif

#if PYTHON_VERSION < 0x3b0
    coroutine->m_exc_state.exception_type = saved_exception_type;
#endif
    coroutine->m_exc_state.exception_value = saved_exception_value;
#if PYTHON_VERSION < 0x3b0
    coroutine->m_exc_state.exception_tb = (PyTracebackObject *)saved_exception_traceback;
#endif
#endif
}

#ifdef __cplusplus
enum Await_Kind {
    await_normal, // user provided "await"
    await_enter,  // async with statement "__enter__"
    await_exit    // async with statement "__enter__"
};
#else
typedef int Generator_Status;
static const int await_normal = 0;
static const int await_enter = 1;
static const int await_exit = 2;
#endif

// Create the object to await for async for "iter".
extern PyObject *ASYNC_MAKE_ITERATOR(PyThreadState *tstate, PyObject *value);

// Create the object to await for async for "next".
extern PyObject *ASYNC_ITERATOR_NEXT(PyThreadState *tstate, PyObject *value);

// Create the object for plain "await".
extern PyObject *ASYNC_AWAIT(PyThreadState *tstate, PyObject *awaitable, int await_kind);

NUITKA_MAY_BE_UNUSED static void STORE_COROUTINE_EXCEPTION(PyThreadState *tstate,
                                                           struct Nuitka_CoroutineObject *coroutine) {
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
}

NUITKA_MAY_BE_UNUSED static void DROP_COROUTINE_EXCEPTION(struct Nuitka_CoroutineObject *coroutine) {
#if PYTHON_VERSION < 0x3b0
    Py_CLEAR(EXC_TYPE_F(coroutine));
#endif
    Py_CLEAR(EXC_VALUE_F(coroutine));
#if PYTHON_VERSION < 0x3b0
    Py_CLEAR(EXC_TRACEBACK_F(coroutine));
#endif
}

// For reference count debugging.
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
