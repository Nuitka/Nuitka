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
#ifndef __NUITKA_COMPILED_ASYNCGEN_H__
#define __NUITKA_COMPILED_ASYNCGEN_H__

// Compiled async generator type.

// Another cornerstone of the integration into CPython. Try to behave as well as
// normal asyncgen objects do or even better.

#if PYTHON_VERSION >= 0x360

// The Nuitka_AsyncgenObject is the storage associated with a compiled
// async generator object instance of which there can be many for each code.
struct Nuitka_AsyncgenObject {
    /* Python object folklore: */
    PyObject_VAR_HEAD;

    PyObject *m_name;

    // TODO: Only to make traceback for non-started throw
    PyObject *m_module;

    PyObject *m_qualname;
    PyObject *m_yieldfrom;

    // Weak references are supported for asyncgen objects in CPython.
    PyObject *m_weakrefs;

    int m_running;

    // When an asyncgen is awaiting, this flag is set.
    int m_awaiting;

#if PYTHON_VERSION >= 0x380
    // When an asyncgen is running, this is set
    int m_running_async;
#endif

    void *m_code;

    // The parent frame of the coroutine, if created.
    struct Nuitka_FrameObject *m_frame;

    PyCodeObject *m_code_object;

    // While yielding, this was the frame currently active, restore when
    // resuming.
    struct Nuitka_FrameObject *m_resume_frame;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

#if PYTHON_VERSION >= 0x370
    _PyErr_StackItem m_exc_state;
#endif

    // The label index to resume after yield.
    int m_yield_return_index;

    // The finalizer associated through a hook
    PyObject *m_finalizer;

    // The hooks were initialized
    bool m_hooks_init_done;

    // It is closed, and cannot be closed again.
    bool m_closed;

    /* The heap of generator objects at run time. */
    void *m_heap_storage;

    /* Closure variables given, if any, we reference cells here. The last
     * part is dynamically allocated, the array size differs per asyncgen
     * and includes the heap storage.
     */
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Asyncgen_Type;

typedef PyObject *(*asyncgen_code)(struct Nuitka_AsyncgenObject *, PyObject *);

extern PyObject *Nuitka_Asyncgen_New(asyncgen_code code, PyObject *module, PyObject *name, PyObject *qualname,
                                     PyCodeObject *code_object, struct Nuitka_CellObject **closure,
                                     Py_ssize_t closure_given, Py_ssize_t heap_storage_size);

static inline bool Nuitka_Asyncgen_Check(PyObject *object) { return Py_TYPE(object) == &Nuitka_Asyncgen_Type; }

static inline void SAVE_ASYNCGEN_EXCEPTION(struct Nuitka_AsyncgenObject *asyncgen) {
    /* Before Python3.7: When yielding from an exception handler in Python3,
     * the exception preserved to the frame is restored, while the current one
     * is put as there.
     *
     * Python3.7: The exception is preserved in the asyncgen object itself
     * which has a new "m_exc_state" structure just for that.
     */

    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *saved_exception_type = EXC_TYPE(thread_state);
    PyObject *saved_exception_value = EXC_VALUE(thread_state);
    PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SAVE_ASYNCGEN_EXCEPTION: Enter\n");
    PRINT_EXCEPTION(saved_exception_type, saved_exception_value, saved_exception_traceback);
#endif

    CHECK_OBJECT_X(saved_exception_type);
    CHECK_OBJECT_X(saved_exception_value);
    CHECK_OBJECT_X(saved_exception_traceback);

#if PYTHON_VERSION < 0x370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;
#else
    EXC_TYPE(thread_state) = asyncgen->m_exc_state.exc_type;
    EXC_VALUE(thread_state) = asyncgen->m_exc_state.exc_value;
    EXC_TRACEBACK(thread_state) = asyncgen->m_exc_state.exc_traceback;
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("SAVE_ASYNCGEN_EXCEPTION: Leave\n");
    PRINT_EXCEPTION(EXC_TYPE(thread_state), EXC_VALUE(thread_state), EXC_TRACEBACK(thread_state));
#endif

    CHECK_OBJECT_X(EXC_TYPE(thread_state));
    CHECK_OBJECT_X(EXC_VALUE(thread_state));
    CHECK_OBJECT_X(EXC_TRACEBACK(thread_state));

#if PYTHON_VERSION < 0x370
    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
    asyncgen->m_exc_state.exc_type = saved_exception_type;
    asyncgen->m_exc_state.exc_value = saved_exception_value;
    asyncgen->m_exc_state.exc_traceback = saved_exception_traceback;
#endif
}

static inline void RESTORE_ASYNCGEN_EXCEPTION(struct Nuitka_AsyncgenObject *asyncgen) {
    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *saved_exception_type = EXC_TYPE(thread_state);
    PyObject *saved_exception_value = EXC_VALUE(thread_state);
    PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ASYNCGEN_EXCEPTION: Enter\n");
    PRINT_EXCEPTION(saved_exception_type, saved_exception_value, saved_exception_traceback);
#endif

    CHECK_OBJECT_X(saved_exception_type);
    CHECK_OBJECT_X(saved_exception_value);
    CHECK_OBJECT_X(saved_exception_traceback);

#if PYTHON_VERSION < 0x370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
    EXC_TYPE(thread_state) = asyncgen->m_exc_state.exc_type;
    EXC_VALUE(thread_state) = asyncgen->m_exc_state.exc_value;
    EXC_TRACEBACK(thread_state) = asyncgen->m_exc_state.exc_traceback;

    asyncgen->m_exc_state.exc_type = saved_exception_type;
    asyncgen->m_exc_state.exc_value = saved_exception_value;
    asyncgen->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("RESTORE_ASYNCGEN_EXCEPTION: Leave\n");
    PRINT_EXCEPTION(EXC_TYPE(thread_state), EXC_VALUE(thread_state), EXC_TRACEBACK(thread_state));
#endif

    CHECK_OBJECT_X(EXC_TYPE(thread_state));
    CHECK_OBJECT_X(EXC_VALUE(thread_state));
    CHECK_OBJECT_X(EXC_TRACEBACK(thread_state));
}

#endif

// For reference count debugging.
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
