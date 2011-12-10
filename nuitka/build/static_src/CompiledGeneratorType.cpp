//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//

#include "nuitka/prelude.hpp"

static PyObject *Nuitka_Generator_tp_repr( Nuitka_GeneratorObject *generator )
{
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<compiled generator object %s at %p>",
        Nuitka_String_AsString( generator->m_name ),
        generator
    );
}

static long Nuitka_Generator_tp_traverse( PyObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it could be NULL
    // instead. The methodobject visits its self and module. I understand this is probably
    // so that back references of this function to its upper do not make it stay in the
    // memory. A specific test if that works might be needed.
    return 0;
}


static PyObject *Nuitka_Generator_send( Nuitka_GeneratorObject *generator, PyObject *value )
{
    if ( generator->m_status == Generator_Status::status_Unused && value != NULL && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started generator" );
        return NULL;
    }

    if ( generator->m_status != Generator_Status::status_Finished )
    {
        if ( generator->m_running )
        {
            PyErr_Format( PyExc_ValueError, "generator already executing" );
            return NULL;
        }

        if ( generator->m_status == Generator_Status::status_Unused )
        {
            generator->m_status = Generator_Status::status_Running;

            // Prepare the generator context to run. TODO: Make stack size rational.
            prepareFiber( &generator->m_yielder_context, generator->m_code, (unsigned long)generator );
        }

        generator->m_yielded = value;

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = PyThreadState_GET()->frame;
#ifndef __NUITKA_NO_ASSERT__
        if ( return_frame )
        {
            assertFrameObject( return_frame );
        }
#endif

        if ( generator->m_frame )
        {
            // It would be nice if our frame were still alive. Nobody had the right to release it.
            assertFrameObject( generator->m_frame );

            // It's not supposed to be on the top right now.
            assert( return_frame != generator->m_frame );

            Py_XINCREF( return_frame );
            generator->m_frame->f_back = return_frame;

            PyThreadState_GET()->frame = generator->m_frame;
        }

        // Continue the yielder function while preventing recursion.
        generator->m_running = true;
        swapFiber( &generator->m_caller_context, &generator->m_yielder_context );
        generator->m_running = false;

        // Remove the generator from the frame stack.
        assert( PyThreadState_GET()->frame == generator->m_frame );
        assertFrameObject( generator->m_frame );

        PyThreadState_GET()->frame = return_frame;
        Py_CLEAR( generator->m_frame->f_back );

        if ( generator->m_yielded == NULL )
        {
            generator->m_status = Generator_Status::status_Finished;

            return NULL;
        }
        else
        {
            return generator->m_yielded;
        }
    }
    else
    {
        PyErr_SetNone( PyExc_StopIteration );
        return NULL;
    }
}

static PyObject *Nuitka_Generator_tp_iternext( Nuitka_GeneratorObject *generator )
{
    return Nuitka_Generator_send( generator, Py_None );
}


static PyObject *Nuitka_Generator_close( Nuitka_GeneratorObject *generator, PyObject *args )
{
    if ( generator->m_status == Generator_Status::status_Running )
    {
        generator->m_exception_type = PyExc_GeneratorExit;
        generator->m_exception_value = NULL;
        generator->m_exception_tb = NULL;

        PyObject *result = Nuitka_Generator_send( generator, Py_None );

        if ( result )
        {
            Py_DECREF( result );

            PyErr_Format( PyExc_RuntimeError, "generator ignored GeneratorExit" );
            return NULL;
        } else if ( PyErr_ExceptionMatches( PyExc_StopIteration ) || PyErr_ExceptionMatches( PyExc_GeneratorExit ))
        {
            PyErr_Clear();
            return INCREASE_REFCOUNT( Py_None );
        }
        else
        {
            return NULL;
        }
    }

    return INCREASE_REFCOUNT( Py_None );
}

static void Nuitka_Generator_tp_dealloc( Nuitka_GeneratorObject *generator )
{
    assert( Py_REFCNT( generator ) == 0 );
    Py_REFCNT( generator ) = 1;

    PyObject *close_result = Nuitka_Generator_close( generator, NULL );

    if ( close_result == NULL )
    {
        PyErr_WriteUnraisable( (PyObject *)generator );
    }
    else
    {
        Py_DECREF( close_result );
    }

    assert( Py_REFCNT( generator ) == 1 );
    Py_REFCNT( generator ) = 0;

    releaseFiber( &generator->m_yielder_context );

    // Now it is safe to release references and memory for it.
    Nuitka_GC_UnTrack( generator );

    if ( generator->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)generator );
    }

    if ( generator->m_context )
    {
        generator->m_cleanup( generator->m_context );
    }

    Py_DECREF( generator->m_name );

    Py_XDECREF( generator->m_frame );

    PyObject_GC_Del( generator );
}

static PyObject *Nuitka_Generator_throw( Nuitka_GeneratorObject *generator, PyObject *args )
{
    generator->m_exception_value = NULL;
    generator->m_exception_tb = NULL;

    int res = PyArg_UnpackTuple( args, "throw", 1, 3, &generator->m_exception_type, &generator->m_exception_value, &generator->m_exception_tb );

    if ( res == 0 )
    {
        generator->m_exception_type = NULL;

        return NULL;
    }

    if ( PyExceptionInstance_Check( generator->m_exception_type ) )
    {
        if ( generator->m_exception_value && generator->m_exception_value != Py_None )
        {
            PyErr_Format( PyExc_TypeError, "instance exception may not have a separate value" );
            return NULL;
        }

        generator->m_exception_value = generator->m_exception_type;
        generator->m_exception_type = INCREASE_REFCOUNT( PyExceptionInstance_Class( generator->m_exception_type ) );
    }
    else if ( !PyExceptionClass_Check( generator->m_exception_type ) )
    {
        PyErr_Format( PyExc_TypeError, "exceptions must be classes, or instances, not %s", generator->m_exception_type->ob_type->tp_name );
        return NULL;
    }

    if ( generator->m_exception_tb != NULL && generator->m_exception_tb != Py_None && !PyTraceBack_Check( generator->m_exception_tb ) )
    {
        PyErr_Format( PyExc_TypeError, "throw() third argument must be a traceback object" );
        return NULL;
    }

    PyErr_NormalizeException( &generator->m_exception_type, &generator->m_exception_value, &generator->m_exception_tb );

    if ( generator->m_status != Generator_Status::status_Finished )
    {
        return Nuitka_Generator_send( generator, Py_None );
    }
    else
    {
        PyErr_Restore( generator->m_exception_type, generator->m_exception_value, generator->m_exception_tb );
        return NULL;
    }
}

static PyObject *Nuitka_Generator_get_name( Nuitka_GeneratorObject *generator )
{
    return INCREASE_REFCOUNT( generator->m_name );
}

static PyGetSetDef Nuitka_Generator_getsetlist[] =
{
    { (char * )"__name__", (getter)Nuitka_Generator_get_name, NULL, NULL },
    { NULL }
};

static PyMethodDef Nuitka_Generator_methods[] =
{
    { "send",  (PyCFunction)Nuitka_Generator_send,  METH_O, NULL },
    { "throw", (PyCFunction)Nuitka_Generator_throw, METH_VARARGS, NULL },
    { "close", (PyCFunction)Nuitka_Generator_close, METH_NOARGS, NULL },
    { NULL }
};

#include <structmember.h>

static PyMemberDef Nuitka_Generator_members[] =
{
    { (char *)"gi_running", T_INT, offsetof( Nuitka_GeneratorObject, m_running ), READONLY },
    { NULL }
};


PyTypeObject Nuitka_Generator_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_generator",                            // tp_name
    sizeof(Nuitka_GeneratorObject),                  // tp_basicsize
    0,                                               // tp_itemsize
    (destructor)Nuitka_Generator_tp_dealloc,         // tp_dealloc
    0,                                               // tp_print
    0,                                               // tp_getattr
    0,                                               // tp_setattr
    // TODO: Compare should be easy, check the benefit of doing it.
    0,                                               // tp_compare
    (reprfunc)Nuitka_Generator_tp_repr,              // tp_repr
    0,                                               // tp_as_number
    0,                                               // tp_as_sequence
    0,                                               // tp_as_mapping
    0,                                               // tp_hash
    0,                                               // tp_call
    0,                                               // tp_str
    PyObject_GenericGetAttr,                         // tp_getattro
    0,                                               // tp_setattro
    0,                                               // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,         // tp_flags
    0,                                               // tp_doc
    (traverseproc)Nuitka_Generator_tp_traverse,      // tp_traverse
    0,                                               // tp_clear
    0,                                               // tp_richcompare
    offsetof( Nuitka_GeneratorObject, m_weakrefs ),  // tp_weaklistoffset
    PyObject_SelfIter,                               // tp_iter
    (iternextfunc)Nuitka_Generator_tp_iternext,      // tp_iternext
    Nuitka_Generator_methods,                        // tp_methods
    Nuitka_Generator_members,                        // tp_members
    Nuitka_Generator_getsetlist,                     // tp_getset
    0,                                               // tp_base
    0,                                               // tp_dict
    0,                                               // tp_descr_get
    0,                                               // tp_descr_set
    0,                                               // tp_dictoffset
    0,                                               // tp_init
    0,                                               // tp_alloc
    0,                                               // tp_new
    0,                                               // tp_free
    0,                                               // tp_is_gc
    0,                                               // tp_bases
    0,                                               // tp_mro
    0,                                               // tp_cache
    0,                                               // tp_subclasses
    0,                                               // tp_weaklist
    0                                                // tp_del
};

PyObject *Nuitka_Generator_New( yielder_func code, PyObject *name, void *context, releaser cleanup )
{
    Nuitka_GeneratorObject *result = PyObject_GC_New( Nuitka_GeneratorObject, &Nuitka_Generator_Type );

    if (unlikely( result == NULL ))
    {
        PyErr_Format(
            PyExc_RuntimeError,
            "cannot create genexpr %s",
            Nuitka_String_AsString( name )
        );

        throw _PythonException();
    }

    result->m_code = (void *)code;

    result->m_name = INCREASE_REFCOUNT( name );

    result->m_context = context;
    result->m_cleanup = cleanup;

    result->m_weakrefs = NULL;

    result->m_status = Generator_Status::status_Unused;
    result->m_running = false;

    initFiber( &result->m_yielder_context );

    result->m_exception_type = NULL;
    result->m_yielded = NULL;

    result->m_frame = NULL;

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}
