//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

// Another cornerstone of the integration into CPython. Try to behave as well as normal
// generator function objects do or even better.


// *** Nuitka_Generator type begin

#include "fibers.hpp"

// Status of the generator object.
enum Generator_Status {
    status_Unused,  // Not used so far
    status_Running, // Running, used but didn't stop yet
    status_Finished // Stoped, no more values to come
};

// The Nuitka_GeneratorObject is the storage associated with a compiled generator object
// instance of which there can be many for each code.
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

static inline void CHECK_EXCEPTION( Nuitka_GeneratorObject *generator )
{
    if ( generator->m_exception_type )
    {
        assertObject( generator->m_exception_type );

        Py_INCREF( generator->m_exception_type );
        Py_XINCREF( generator->m_exception_value );
        Py_XINCREF( generator->m_exception_tb );

        PyErr_Restore( generator->m_exception_type, generator->m_exception_value, (PyObject *)generator->m_exception_tb );

        generator->m_exception_type = NULL;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        throw _PythonException();
    }
}

static inline PyObject *YIELD_VALUE( Nuitka_GeneratorObject *generator, PyObject *value )
{
    assertObject( value );

    generator->m_yielded = value;

    // Return to the calling context.
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

    CHECK_EXCEPTION( generator );

    return generator->m_yielded;
}


static inline void YIELD_RETURN( Nuitka_GeneratorObject *generator, PyObject *value )
{
#if PYTHON_VERSION < 270
    if ( value != Py_None )
    {
        YIELD_VALUE( generator, value );
    }
#endif
}

#endif
