//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_COMPILED_ASYNCGEN_H__
#define __NUITKA_COMPILED_ASYNCGEN_H__

#if PYTHON_VERSION >= 0x360

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

struct Nuitka_AsyncgenObject {
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

#if PYTHON_VERSION >= 0x380
    int m_running_async;
#endif

    void *m_code;

    struct Nuitka_FrameObject *m_frame;

    PyCodeObject *m_code_object;

    // Active caller frame saved across yields and restored when resuming.
    Nuitka_ThreadStateFrameType *m_resume_frame;

    Generator_Status m_status;

#if PYTHON_VERSION >= 0x370
    struct Nuitka_ExceptionStackItem m_exc_state;
#endif

    // The label index to resume after yield.
    int m_yield_return_index;

    PyObject *m_finalizer;
    bool m_hooks_init_done;
    bool m_closed;

    // Unique per-instance identifier used in comparisons.
    long m_counter;

    void *m_heap_storage;

    // Trailing flexible array allocated with space for m_closure_given cells plus heap storage.
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Asyncgen_Type;

typedef PyObject *(*asyncgen_code)(PyThreadState *tstate, struct Nuitka_AsyncgenObject *, PyObject *);

extern PyObject *Nuitka_Asyncgen_New(asyncgen_code code, PyObject *module, PyObject *name, PyObject *qualname,
                                     PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                     Py_ssize_t closure_given, Py_ssize_t heap_storage_size);

static inline bool Nuitka_Asyncgen_Check(PyObject *obj) { return Py_TYPE(obj) == &Nuitka_Asyncgen_Type; }

static inline void SAVE_ASYNCGEN_EXCEPTION(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
    /* Before Python3.7: When yielding from an exception handler in Python3,
     * the exception preserved to the frame is restored, while the current one
     * is put as there.
     *
     * Python3.7: The exception is preserved in the asyncgen object itself,
     * which is made the current exception state while the asyncgen runs.
     */
#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SAVE_ASYNCGEN_EXCEPTION: Enter\n");
    PRINT_PUBLISHED_EXCEPTION();
#endif

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

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SAVE_ASYNCGEN_EXCEPTION: Leave\n");
    PRINT_PUBLISHED_EXCEPTION();
#endif

    tstate->frame->f_exc_type = saved_exception_type;
    tstate->frame->f_exc_value = saved_exception_value;
    tstate->frame->f_exc_traceback = (PyObject *)saved_exception_traceback;
#else
    assert(asyncgen->m_exc_state.previous_item == NULL);

    asyncgen->m_exc_state.previous_item = tstate->exc_info;
    tstate->exc_info = (_PyErr_StackItem *)&asyncgen->m_exc_state;
#endif
}

static inline void RESTORE_ASYNCGEN_EXCEPTION(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ASYNCGEN_EXCEPTION: Enter\n");
#endif

#if PYTHON_VERSION < 0x370
#if PYTHON_VERSION < 0x3b0
    PyObject *saved_exception_type = EXC_TYPE(tstate);
#endif
    PyObject *saved_exception_value = EXC_VALUE(tstate);
#if PYTHON_VERSION < 0x3b0
    PyTracebackObject *saved_exception_traceback = EXC_TRACEBACK(tstate);
#endif

#if _DEBUG_EXCEPTIONS
#if PYTHON_VERSION < 0x3b0
    PRINT_EXCEPTION(saved_exception_type, saved_exception_value, saved_exception_traceback);
#else
    _PRINT_EXCEPTION1(saved_exception_value);
#endif
#endif

    EXC_TYPE(tstate) = tstate->frame->f_exc_type;
    EXC_VALUE(tstate) = tstate->frame->f_exc_value;
    SET_EXC_TRACEBACK(tstate, tstate->frame->f_exc_traceback);

    tstate->frame->f_exc_type = saved_exception_type;
    tstate->frame->f_exc_value = saved_exception_value;
    tstate->frame->f_exc_traceback = (PyObject *)saved_exception_traceback;
#else
    assert(asyncgen->m_exc_state.previous_item != NULL);

    tstate->exc_info = asyncgen->m_exc_state.previous_item;
    asyncgen->m_exc_state.previous_item = NULL;
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ASYNCGEN_EXCEPTION: Leave\n");
    PRINT_PUBLISHED_EXCEPTION();
#endif

#if PYTHON_VERSION < 0x3b0
    CHECK_OBJECT_X(EXC_TYPE(tstate));
#endif
    CHECK_OBJECT_X(EXC_VALUE(tstate));
#if PYTHON_VERSION < 0x3b0
    CHECK_OBJECT_X(EXC_TRACEBACK(tstate));
#endif
}

#if 0x300 <= PYTHON_VERSION && PYTHON_VERSION < 0x370
static inline void SAVE_ASYNCGEN_EXCEPTION_FROM_THREAD(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
    PyObject *old_type = EXC_TYPE_F(asyncgen);
    PyObject *old_value = EXC_VALUE_F(asyncgen);
    PyObject *old_tb = EXC_TRACEBACK_F(asyncgen);

    EXC_TYPE_F(asyncgen) = EXC_TYPE(tstate);
    Py_XINCREF(EXC_TYPE_F(asyncgen));
    EXC_VALUE_F(asyncgen) = EXC_VALUE(tstate);
    Py_XINCREF(EXC_VALUE_F(asyncgen));
    ASSIGN_EXC_TRACEBACK_F(asyncgen, EXC_TRACEBACK(tstate));
    Py_XINCREF(EXC_TRACEBACK_F(asyncgen));

    Py_XDECREF(old_type);
    Py_XDECREF(old_value);
    Py_XDECREF(old_tb);
}

static inline void RESUME_ASYNCGEN_EXCEPTION(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen,
                                             bool throw_flag) {
    if (throw_flag || EXC_TYPE_F(asyncgen) == NULL || EXC_TYPE_F(asyncgen) == Py_None) {
        SAVE_ASYNCGEN_EXCEPTION_FROM_THREAD(tstate, asyncgen);
    } else {
        SAVE_ASYNCGEN_EXCEPTION(tstate, asyncgen);
    }
}

static inline void RESTORE_AND_CLEAR_ASYNCGEN_EXCEPTION(PyThreadState *tstate, struct Nuitka_AsyncgenObject *asyncgen) {
    assert(asyncgen->m_frame != NULL);

    struct Nuitka_ExceptionStackItem exc_state;

    exc_state.exception_type = EXC_TYPE_F(asyncgen);
    exc_state.exception_value = EXC_VALUE_F(asyncgen);
    exc_state.exception_tb = (PyTracebackObject *)EXC_TRACEBACK_F(asyncgen);

    SET_CURRENT_EXCEPTION(tstate, &exc_state);

    EXC_TYPE_F(asyncgen) = NULL;
    EXC_VALUE_F(asyncgen) = NULL;
    EXC_TRACEBACK_F(asyncgen) = NULL;
}
#endif

NUITKA_MAY_BE_UNUSED static void STORE_ASYNCGEN_EXCEPTION(PyThreadState *tstate,
                                                          struct Nuitka_AsyncgenObject *asyncgen) {
#if 0x300 <= PYTHON_VERSION && PYTHON_VERSION < 0x370
    SAVE_ASYNCGEN_EXCEPTION_FROM_THREAD(tstate, asyncgen);
#else
#if PYTHON_VERSION < 0x3b0
    EXC_TYPE_F(asyncgen) = EXC_TYPE(tstate);
    if (EXC_TYPE_F(asyncgen) == Py_None) {
        EXC_TYPE_F(asyncgen) = NULL;
    }
    Py_XINCREF(EXC_TYPE_F(asyncgen));
#endif
    EXC_VALUE_F(asyncgen) = EXC_VALUE(tstate);
    Py_XINCREF(EXC_VALUE_F(asyncgen));
#if PYTHON_VERSION < 0x3b0
    ASSIGN_EXC_TRACEBACK_F(asyncgen, EXC_TRACEBACK(tstate));
    Py_XINCREF(EXC_TRACEBACK_F(asyncgen));
#endif
#endif
}
NUITKA_MAY_BE_UNUSED static void DROP_ASYNCGEN_EXCEPTION(struct Nuitka_AsyncgenObject *asyncgen) {
#if PYTHON_VERSION < 0x3b0
    Py_CLEAR(EXC_TYPE_F(asyncgen));
#endif
    Py_CLEAR(EXC_VALUE_F(asyncgen));
#if PYTHON_VERSION < 0x3b0
    Py_CLEAR(EXC_TRACEBACK_F(asyncgen));
#endif
#if PYTHON_VERSION >= 0x370
    asyncgen->m_exc_state.previous_item = NULL;
#endif
}

#if _DEBUG_REFCOUNTS
extern int count_active_Nuitka_Asyncgen_Type;
extern int count_allocated_Nuitka_Asyncgen_Type;
extern int count_released_Nuitka_Asyncgen_Type;

extern int count_active_Nuitka_AsyncgenValueWrapper_Type;
extern int count_allocated_Nuitka_AsyncgenValueWrapper_Type;
extern int count_released_Nuitka_AsyncgenValueWrapper_Type;

extern int count_active_Nuitka_AsyncgenAsend_Type;
extern int count_allocated_Nuitka_AsyncgenAsend_Type;
extern int count_released_Nuitka_AsyncgenAsend_Type;

extern int count_active_Nuitka_AsyncgenAthrow_Type;
extern int count_allocated_Nuitka_AsyncgenAthrow_Type;
extern int count_released_Nuitka_AsyncgenAthrow_Type;

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
