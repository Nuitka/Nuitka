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
#ifndef __NUITKA_COMPILED_GENERATOR_H__
#define __NUITKA_COMPILED_GENERATOR_H__

#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"

// Compiled generator function type.

// Another cornerstone of the integration into CPython. Try to behave as well as
// normal generator objects do or even better.

#include "fibers.h"

// Status of the generator object.
#ifdef __cplusplus
enum Generator_Status {
    status_Unused,  // Not used so far
    status_Running, // Running, used but didn't stop yet
    status_Finished // Stopped, no more values to come
};
#else
typedef int Generator_Status;
static const int status_Unused = 0;
static const int status_Running = 1;
static const int status_Finished = 2;
#endif

// The Nuitka_GeneratorObject is the storage associated with a compiled
// generator object instance of which there can be many for each code.
struct Nuitka_GeneratorObject {
    PyObject_VAR_HEAD

    PyObject *m_name;

    PyObject *m_module;

#if PYTHON_VERSION >= 350
    PyObject *m_qualname;
    PyObject *m_yieldfrom;
#endif

    Fiber m_yielder_context;
    Fiber m_caller_context;

    // Weak references are supported for generator objects in CPython.
    PyObject *m_weakrefs;

    int m_running;

    void *m_code;

    PyObject *m_yielded;
    PyObject *m_exception_type, *m_exception_value;
    PyTracebackObject *m_exception_tb;

    struct Nuitka_FrameObject *m_frame;
    PyCodeObject *m_code_object;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

    /* Closure variables given, if any, we reference cells here. The last
     * part is dynamically allocated, the array size differs per generator.
     */
    Py_ssize_t m_closure_given;
    struct Nuitka_CellObject *m_closure[1];
};

extern PyTypeObject Nuitka_Generator_Type;

typedef void (*generator_code)( struct Nuitka_GeneratorObject * );

#if PYTHON_VERSION < 350
extern PyObject *Nuitka_Generator_New( generator_code code, PyObject *module, PyObject *name, PyCodeObject *code_object, Py_ssize_t closure_given );
#else
extern PyObject *Nuitka_Generator_New( generator_code code, PyObject *module, PyObject *name, PyObject *qualname, PyCodeObject *code_object, Py_ssize_t closure_given );
#endif

extern PyObject *Nuitka_Generator_qiter( struct Nuitka_GeneratorObject *generator, bool *finished );

static inline bool Nuitka_Generator_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Generator_Type;
}

static inline PyObject *Nuitka_Generator_GetName( PyObject *object )
{
    return ((struct Nuitka_GeneratorObject *)object)->m_name;
}


static inline PyObject *GENERATOR_YIELD( struct Nuitka_GeneratorObject *generator, PyObject *value )
{
    CHECK_OBJECT( value );

    generator->m_yielded = value;

    Nuitka_Frame_MarkAsNotExecuting( generator->m_frame );

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

    Nuitka_Frame_MarkAsExecuting( generator->m_frame );

    // Check for thrown exception.
    if (unlikely( generator->m_exception_type ))
    {
        RESTORE_ERROR_OCCURRED(
            generator->m_exception_type,
            generator->m_exception_value,
            generator->m_exception_tb
        );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }

    CHECK_OBJECT( generator->m_yielded );
    return generator->m_yielded;
}

#if PYTHON_VERSION >= 300
static inline PyObject *GENERATOR_YIELD_IN_HANDLER( struct Nuitka_GeneratorObject *generator, PyObject *value )
{
    CHECK_OBJECT( value );

    generator->m_yielded = value;

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

    Nuitka_Frame_MarkAsNotExecuting( generator->m_frame );

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

    Nuitka_Frame_MarkAsExecuting( generator->m_frame );

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
    if (unlikely( generator->m_exception_type ))
    {
        RESTORE_ERROR_OCCURRED(
            generator->m_exception_type,
            generator->m_exception_value,
            generator->m_exception_tb
        );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }

    return generator->m_yielded;
}
#endif

#if PYTHON_VERSION >= 330
extern PyObject *GENERATOR_YIELD_FROM( struct Nuitka_GeneratorObject *generator, PyObject *target );
extern PyObject *GENERATOR_YIELD_FROM_IN_HANDLER( struct Nuitka_GeneratorObject *generator, PyObject *target );
#endif

#endif
