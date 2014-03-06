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

typedef void (*yielder_func)( Nuitka_GeneratorObject * );

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

static void RAISE_GENERATOR_EXCEPTION( Nuitka_GeneratorObject *generator )
{
    assertObject( generator->m_exception_type );

    Py_INCREF( generator->m_exception_type );
    Py_XINCREF( generator->m_exception_value );
    Py_XINCREF( generator->m_exception_tb );

    PyErr_Restore(
        generator->m_exception_type,
        generator->m_exception_value,
        (PyObject *)generator->m_exception_tb
    );

    generator->m_exception_type = NULL;
    generator->m_exception_value = NULL;
    generator->m_exception_tb = NULL;

    throw PythonException();
}

static inline void CHECK_EXCEPTION( Nuitka_GeneratorObject *generator )
{
    if ( generator->m_exception_type )
    {
        RAISE_GENERATOR_EXCEPTION( generator );
    }
}

static inline PyObject *YIELD( Nuitka_GeneratorObject *generator, PyObject *value )
{
    assertObject( value );

    generator->m_yielded = value;

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

    CHECK_EXCEPTION( generator );

    return generator->m_yielded;
}

static inline PyObject *YIELD_IN_HANDLER( Nuitka_GeneratorObject *generator, PyObject *value )
{
    assertObject( value );

    generator->m_yielded = value;

#if PYTHON_VERSION >= 300
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

#endif

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

    // When yielding, the exception preserved to the frame is restore, while the
    // current one is put there.
#if PYTHON_VERSION >= 300
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
#endif

    CHECK_EXCEPTION( generator );

    return generator->m_yielded;
}

#if PYTHON_VERSION >= 330
extern PyObject *ERROR_GET_STOP_ITERATION_VALUE();
extern PyObject *PyGen_Send( PyGenObject *gen, PyObject *arg );

static inline PyObject *YIELD_FROM( Nuitka_GeneratorObject *generator, PyObject *value )
{
    // This is the value, propagated back and forth the sub-generator and the
    // yield from consumer.
    PyObject *send_value = Py_None;

    while( 1 )
    {
        // Send iteration value to the sub-generator, which may be a CPython
        // generator object, something with an iterator next, or a send method,
        // where the later is only required if values other than "None" need to
        // be passed in.
        PyObject *retval;

        // Exception, was thrown into us, need to send that to sub-generator.
        if ( generator->m_exception_type )
        {
            // The yielding generator is being closed, but we also are tasked to
            // immediately close the currently running sub-generator.
            if ( PyErr_GivenExceptionMatches( generator->m_exception_type, PyExc_GeneratorExit ) )
            {
                PyObject *close_method = PyObject_GetAttrString( value, (char *)"close" );

                if ( close_method )
                {
                    PyObject *close_value = PyObject_Call( close_method, const_tuple_empty, NULL );
                    Py_DECREF( close_method );

                    if (unlikely( close_value == NULL ))
                    {
                        throw PythonException();
                    }

                    Py_DECREF( close_value );
                }

                RAISE_GENERATOR_EXCEPTION( generator );
            }

            PyObject *throw_method = PyObject_GetAttrString( value, (char *)"throw" );

            if ( throw_method )
            {
                retval = PyObject_CallFunctionObjArgs( throw_method, generator->m_exception_type, generator->m_exception_value, generator->m_exception_tb, NULL );
                Py_DECREF( throw_method );

                if (unlikely( send_value == NULL ))
                {
                    if ( PyErr_ExceptionMatches( PyExc_StopIteration ) )
                    {

                        return ERROR_GET_STOP_ITERATION_VALUE();
                    }

                    throw PythonException();
                }


                generator->m_exception_type = NULL;
                generator->m_exception_value = NULL;
                generator->m_exception_tb = NULL;
            }
            else if ( PyErr_ExceptionMatches( PyExc_AttributeError ) )
            {
                PyErr_Clear();

                RAISE_GENERATOR_EXCEPTION( generator );
            }
            else
            {
                throw PythonException();
            }

        }
        else if ( PyGen_CheckExact( value ) )
        {
            retval = PyGen_Send( (PyGenObject *)value, Py_None );
        }
        else if ( send_value == Py_None )
        {
            retval = Py_TYPE( value )->tp_iternext( value );
        }
        else
        {
            retval = PyObject_CallMethod( value, (char *)"send", (char *)"O", send_value );
        }

        // Check the sub-generator result
        if ( retval == NULL )
        {
            assert( ERROR_OCCURED() );

            // The sub-generator has given an exception. In case of
            // StopIteration, we need to check the value, as it is going to be
            // the expression value of this "yield from", and we are done. All
            // other errors, we need to raise.
            if (likely( PyErr_ExceptionMatches( PyExc_StopIteration ) ))
            {
                return ERROR_GET_STOP_ITERATION_VALUE();
            }

            throw PythonException();
        }
        else
        {
            generator->m_yielded = retval;

            // Return to the calling context.
            swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

            send_value = generator->m_yielded;

            assertObject( send_value );
        }
    }
}

#endif

#endif
