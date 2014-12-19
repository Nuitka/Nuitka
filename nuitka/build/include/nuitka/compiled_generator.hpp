//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
// normal generator function objects do or even better.


// *** Nuitka_Generator type begin

#include "fibers.hpp"

// Status of the generator object.
enum Generator_Status {
    status_Unused,  // Not used so far
    status_Running, // Running, used but didn't stop yet
    status_Finished // Stoped, no more values to come
};

// The Nuitka_GeneratorObject is the storage associated with a compiled
// generator object instance of which there can be many for each code.
typedef struct {
    PyObject_HEAD

    PyObject *m_name;

    Fiber m_yielder_context;
    Fiber m_caller_context;

    void *m_context;
    releaser m_cleanup;

    // Weakrefs are supported for generator objects in CPython.
    PyObject *m_weakrefs;

    int m_running;

    void *m_code;

    PyObject *m_yielded;
    PyObject *m_exception_type, *m_exception_value;
    PyTracebackObject *m_exception_tb;

    PyFrameObject *m_frame;
    PyCodeObject *m_code_object;

    // Was it ever used, is it still running, or already finished.
    Generator_Status m_status;

} Nuitka_GeneratorObject;

extern PyTypeObject Nuitka_Generator_Type;

// For the yielder func, we may need to follow what makecontext will support and
// that is only a list of ints, but we will need to push a pointer through it,
// and so it's two of them, which might be sufficient.
#ifdef _NUITKA_MAKECONTEXT_INTS
typedef void (*yielder_func)( int, int );
#else
typedef void (*yielder_func)( Nuitka_GeneratorObject * );
#endif

extern PyObject *Nuitka_Generator_New( yielder_func code, PyObject *name, PyCodeObject *code_object, void *context, releaser cleanup );
extern PyObject *Nuitka_Generator_New( yielder_func code, PyObject *name, PyCodeObject *code_object );

static inline bool Nuitka_Generator_Check( PyObject *object )
{
    return Py_TYPE( object ) == &Nuitka_Generator_Type;
}

static inline PyObject *Nuitka_Generator_GetName( PyObject *object )
{
    return ((Nuitka_GeneratorObject *)object)->m_name;
}


static inline PyObject *YIELD( Nuitka_GeneratorObject *generator, PyObject *value )
{
    assertObject( value );

    generator->m_yielded = value;

#if PYTHON_VERSION >= 340
    generator->m_frame->f_executing -= 1;
#endif

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

#if PYTHON_VERSION >= 340
    generator->m_frame->f_executing += 1;
#endif

    // Check for thrown exception.
    if (unlikely( generator->m_exception_type ))
    {
        PyErr_Restore(
            generator->m_exception_type,
            generator->m_exception_value,
            (PyObject *)generator->m_exception_tb
        );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        return NULL;
    }

    assertObject( generator->m_yielded );
    return generator->m_yielded;
}

#if PYTHON_VERSION >= 300
static inline PyObject *YIELD_IN_HANDLER( Nuitka_GeneratorObject *generator, PyObject *value )
{
    assertObject( value );

    generator->m_yielded = value;

    // When yielding from an exception handler in Python3, the exception
    // preserved to the frame is restore, while the current one is put there.
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *saved_exception_type = thread_state->exc_type;
    PyObject *saved_exception_value = thread_state->exc_value;
    PyObject *saved_exception_traceback = thread_state->exc_traceback;

    thread_state->exc_type = thread_state->frame->f_exc_type;
    thread_state->exc_value = thread_state->frame->f_exc_value;
    thread_state->exc_traceback = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;

#if PYTHON_VERSION >= 340
    generator->m_frame->f_executing -= 1;
#endif

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

#if PYTHON_VERSION >= 340
    generator->m_frame->f_executing += 1;
#endif

    // When returning from yield, the exception of the frame is preserved, and
    // the one that enters should be there.
    thread_state = PyThreadState_GET();

    saved_exception_type = thread_state->exc_type;
    saved_exception_value = thread_state->exc_value;
    saved_exception_traceback = thread_state->exc_traceback;

    thread_state->exc_type = thread_state->frame->f_exc_type;
    thread_state->exc_value = thread_state->frame->f_exc_value;
    thread_state->exc_traceback = thread_state->frame->f_exc_traceback;

    thread_state->frame->f_exc_type = saved_exception_type;
    thread_state->frame->f_exc_value = saved_exception_value;
    thread_state->frame->f_exc_traceback = saved_exception_traceback;

    // Check for thrown exception.
    if (unlikely( generator->m_exception_type ))
    {
        PyErr_Restore(
            generator->m_exception_type,
            generator->m_exception_value,
            (PyObject *)generator->m_exception_tb
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
extern PyObject *YIELD_FROM( Nuitka_GeneratorObject *generator, PyObject *value );
extern PyObject *YIELD_FROM_IN_HANDLER( Nuitka_GeneratorObject *generator, PyObject *value );
#endif

#endif
