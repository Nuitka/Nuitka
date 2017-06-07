//     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

#if PYTHON_VERSION >= 360

// The Nuitka_AsyncgenObject is the storage associated with a compiled
// async generator object instance of which there can be many for each code.
struct Nuitka_AsyncgenObject {
    PyObject_VAR_HEAD

    PyObject *m_name;

    PyObject *m_qualname;
    PyObject *m_yieldfrom;

    Fiber m_yielder_context;
    Fiber m_caller_context;

    // Weak references are supported for async generator objects in CPython.
    PyObject *m_weakrefs;

    int m_running;
    int m_awaiting;

    void *m_code;

    PyObject *m_yielded;

    PyObject *m_exception_type, *m_exception_value;
    PyTracebackObject *m_exception_tb;

    struct Nuitka_FrameObject *m_frame;
    PyCodeObject *m_code_object;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

    // The finalizer associated
    PyObject *m_finalizer;

    // The hooks were initialized
    bool m_hooks_init_done;

    // It is closed.
    bool m_closed;

    // Closure variables given, if any, we reference cells here.
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Asyncgen_Type;

typedef void (*asyncgen_code)( struct Nuitka_AsyncgenObject * );

extern PyObject *Nuitka_Asyncgen_New( asyncgen_code code, PyObject *name, PyObject *qualname, PyCodeObject *code_object, Py_ssize_t closure_given );

static inline bool Nuitka_Asyncgen_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Asyncgen_Type;
}

extern PyObject *ASYNCGEN_AWAIT( struct Nuitka_AsyncgenObject *asyngen, PyObject *awaitable );
extern PyObject *ASYNCGEN_AWAIT_IN_HANDLER( struct Nuitka_AsyncgenObject *asyngen, PyObject *awaitable );

extern PyObject *Nuitka_AsyncGenValueWrapperNew( PyObject *value );

static inline PyObject *ASYNCGEN_YIELD( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
    CHECK_OBJECT( value );

    asyncgen->m_yielded = Nuitka_AsyncGenValueWrapperNew( value );
    Py_DECREF( value );

    Nuitka_Frame_MarkAsNotExecuting( asyncgen->m_frame );

    // Return to the calling context.
    swapFiber( &asyncgen->m_yielder_context, &asyncgen->m_caller_context );

    Nuitka_Frame_MarkAsExecuting( asyncgen->m_frame );

    // Check for thrown exception.
    if (unlikely( asyncgen->m_exception_type ))
    {
        RESTORE_ERROR_OCCURRED(
            asyncgen->m_exception_type,
            asyncgen->m_exception_value,
            asyncgen->m_exception_tb
        );

        asyncgen->m_exception_type = NULL;
        asyncgen->m_exception_value = NULL;
        asyncgen->m_exception_tb = NULL;

        return NULL;
    }

    CHECK_OBJECT( asyncgen->m_yielded );
    return asyncgen->m_yielded;
}

static inline PyObject *ASYNCGEN_YIELD_IN_HANDLER( struct Nuitka_AsyncgenObject *asyncgen, PyObject *value )
{
    CHECK_OBJECT( value );

    asyncgen->m_yielded = Nuitka_AsyncGenValueWrapperNew( value );
    Py_DECREF( value );

    /* When yielding from an exception handler in Python3, the exception
     * preserved to the frame is restore, while the current one is put there.
     */
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *saved_exception_type = thread_state->exc_type;
    PyObject *saved_exception_value = thread_state->exc_value;
    PyObject *saved_exception_traceback = thread_state->exc_traceback;

    thread_state->exc_type = thread_state->frame->f_exc_type;
    thread_state->exc_value = thread_state->frame->f_exc_value;
    thread_state->exc_traceback = thread_state->frame->f_exc_traceback;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD exit:\n");
    PRINT_EXCEPTION( thread_state->exc_type, thread_state->exc_value, (PyObject *)thread_state->exc_traceback );
#endif

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;

#if _DEBUG_ASYNCGEN
    PRINT_STRING("ASYNCGEN_YIELD_FROM_HANDLER:");
    PRINT_NEW_LINE();
#endif

    Nuitka_Frame_MarkAsNotExecuting( asyncgen->m_frame );

    // Return to the calling context.
    swapFiber( &asyncgen->m_yielder_context, &asyncgen->m_caller_context );

    Nuitka_Frame_MarkAsExecuting( asyncgen->m_frame );

    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.
    thread_state = PyThreadState_GET();

    saved_exception_type = thread_state->exc_type;
    saved_exception_value = thread_state->exc_value;
    saved_exception_traceback = thread_state->exc_traceback;

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD return:\n");
    PRINT_EXCEPTION( thread_state->exc_type, thread_state->exc_value, (PyObject *)thread_state->exc_traceback );
#endif

    thread_state->exc_type = thread_state->frame->f_exc_type;
    thread_state->exc_value = thread_state->frame->f_exc_value;
    thread_state->exc_traceback = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;

    // Check for thrown exception.
    if (unlikely( asyncgen->m_exception_type ))
    {
        RESTORE_ERROR_OCCURRED(
            asyncgen->m_exception_type,
            asyncgen->m_exception_value,
            asyncgen->m_exception_tb
        );

        asyncgen->m_exception_type = NULL;
        asyncgen->m_exception_value = NULL;
        asyncgen->m_exception_tb = NULL;

        return NULL;
    }

    assert( asyncgen->m_yielded != NULL );

    return asyncgen->m_yielded;
}

#endif

#endif
