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
#ifndef __NUITKA_COMPILED_COROUTINE_H__
#define __NUITKA_COMPILED_COROUTINE_H__

// Compiled coroutine type.

// Another cornerstone of the integration into CPython. Try to behave as well as
// normal coroutine objects do or even better.

#if PYTHON_VERSION >= 350

// The Nuitka_CoroutineObject is the storage associated with a compiled
// coroutine object instance of which there can be many for each code.
struct Nuitka_CoroutineObject {
    PyObject_VAR_HEAD

    PyObject *m_name;

    PyObject *m_qualname;
    PyObject *m_yieldfrom;

    Fiber m_yielder_context;
    Fiber m_caller_context;

    // Weak references are supported for coroutine objects in CPython.
    PyObject *m_weakrefs;

    int m_running;
    int m_awaiting;

    void *m_code;

    PyObject *m_yielded;
    PyObject *m_returned;

    PyObject *m_exception_type, *m_exception_value;
    PyTracebackObject *m_exception_tb;

    struct Nuitka_FrameObject *m_frame;
    PyCodeObject *m_code_object;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

#if PYTHON_VERSION >= 370
    _PyErr_StackItem m_exc_state;
#endif

    // Closure variables given, if any, we reference cells here.
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Coroutine_Type;

typedef void (*coroutine_code)( struct Nuitka_CoroutineObject * );

extern PyObject *Nuitka_Coroutine_New( coroutine_code code, PyObject *name, PyObject *qualname, PyCodeObject *code_object, Py_ssize_t closure_given );

static inline bool Nuitka_Coroutine_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Coroutine_Type;
}

struct Nuitka_CoroutineWrapperObject {
    PyObject_HEAD
    struct Nuitka_CoroutineObject *m_coroutine;
};

extern PyTypeObject Nuitka_CoroutineWrapper_Type;

extern PyObject *COROUTINE_AWAIT( struct Nuitka_CoroutineObject *coroutine, PyObject *awaitable );
extern PyObject *COROUTINE_AWAIT_IN_HANDLER( struct Nuitka_CoroutineObject *coroutine, PyObject *awaitable );

extern PyObject *COROUTINE_ASYNC_MAKE_ITERATOR( struct Nuitka_CoroutineObject *coroutine, PyObject *value );
extern PyObject *COROUTINE_ASYNC_ITERATOR_NEXT( struct Nuitka_CoroutineObject *coroutine, PyObject *value );

static inline PyObject *COROUTINE_YIELD( struct Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    CHECK_OBJECT( value );

    coroutine->m_yielded = value;

    Nuitka_Frame_MarkAsNotExecuting( coroutine->m_frame );

    // Return to the calling context.
    swapFiber( &coroutine->m_yielder_context, &coroutine->m_caller_context );

    Nuitka_Frame_MarkAsExecuting( coroutine->m_frame );

    // Check for thrown exception.
    if (unlikely( coroutine->m_exception_type ))
    {
        RESTORE_ERROR_OCCURRED(
            coroutine->m_exception_type,
            coroutine->m_exception_value,
            coroutine->m_exception_tb
        );

        coroutine->m_exception_type = NULL;
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        return NULL;
    }

    CHECK_OBJECT( coroutine->m_yielded );
    return coroutine->m_yielded;
}

static inline PyObject *COROUTINE_YIELD_IN_HANDLER( struct Nuitka_CoroutineObject *coroutine, PyObject *value )
{
    CHECK_OBJECT( value );

    coroutine->m_yielded = value;

    /* Before Python3.7: When yielding from an exception handler in Python3,
     * the exception preserved to the frame is restored, while the current one
     * is put as there.
     *
     * Python3.7: The exception is preserved in the generator object itself
     * which has a new "m_exc_state" structure just for that.
     */
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *saved_exception_type = EXC_TYPE(thread_state);
    PyObject *saved_exception_value = EXC_VALUE(thread_state);
    PyObject *saved_exception_traceback = EXC_TRACEBACK(thread_state);

#if PYTHON_VERSION < 370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;
#else
    EXC_TYPE(thread_state) = coroutine->m_exc_state.exc_type;
    EXC_VALUE(thread_state) = coroutine->m_exc_state.exc_value;
    EXC_TRACEBACK(thread_state) = coroutine->m_exc_state.exc_traceback;
#endif

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD exit:\n");
    PRINT_EXCEPTION( thread_state->exc_type, thread_state->exc_value, (PyObject *)thread_state->exc_traceback );
#endif

#if PYTHON_VERSION < 370
    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
    coroutine->m_exc_state.exc_type = saved_exception_type;
    coroutine->m_exc_state.exc_value = saved_exception_value;;
    coroutine->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

    Nuitka_Frame_MarkAsNotExecuting( coroutine->m_frame );

    // Return to the calling context.
    swapFiber( &coroutine->m_yielder_context, &coroutine->m_caller_context );

    Nuitka_Frame_MarkAsExecuting( coroutine->m_frame );

    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.
    thread_state = PyThreadState_GET();

    saved_exception_type = EXC_TYPE(thread_state);
    saved_exception_value = EXC_VALUE(thread_state);
    saved_exception_traceback = EXC_TRACEBACK(thread_state);

#if _DEBUG_EXCEPTIONS
    PRINT_STRING("YIELD return:\n");
    PRINT_EXCEPTION( thread_state->exc_type, thread_state->exc_value, (PyObject *)thread_state->exc_traceback );
#endif

#if PYTHON_VERSION < 370
    EXC_TYPE(thread_state) = thread_state->frame->f_exc_type;
    EXC_VALUE(thread_state) = thread_state->frame->f_exc_value;
    EXC_TRACEBACK(thread_state) = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;
#else
    EXC_TYPE(thread_state) = coroutine->m_exc_state.exc_type;
    EXC_VALUE(thread_state) = coroutine->m_exc_state.exc_value;
    EXC_TRACEBACK(thread_state) = coroutine->m_exc_state.exc_traceback;

    coroutine->m_exc_state.exc_type = saved_exception_type;
    coroutine->m_exc_state.exc_value = saved_exception_value;
    coroutine->m_exc_state.exc_traceback = saved_exception_traceback;
#endif

    // Check for thrown exception.
    if (unlikely( coroutine->m_exception_type ))
    {
        RESTORE_ERROR_OCCURRED(
            coroutine->m_exception_type,
            coroutine->m_exception_value,
            coroutine->m_exception_tb
        );

        coroutine->m_exception_type = NULL;
        coroutine->m_exception_value = NULL;
        coroutine->m_exception_tb = NULL;

        return NULL;
    }

    return coroutine->m_yielded;
}

#if PYTHON_VERSION >= 360
extern PyObject *PyCoro_GetAwaitableIter( PyObject *value );
#endif

#endif

#endif
