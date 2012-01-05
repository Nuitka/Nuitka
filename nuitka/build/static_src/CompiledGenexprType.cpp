//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
//     This is to reserve my ability to re-license the code at a later time to
//     the PSF. With this version of Nuitka, using it for a Closed Source and
//     distributing the binary only is not allowed.
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

static PyObject *Nuitka_Genexpr_tp_repr( Nuitka_GenexprObject *generator )
{
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<compiled generator object <%s> at %p>",
        Nuitka_String_AsString( generator->m_name ),
        generator
    );
}

static long Nuitka_Genexpr_tp_traverse( PyObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it could be NULL
    // instead. The methodobject visits its self and module. I understand this is probably
    // so that back references of this function to its upper do not make it stay in the
    // memory. A specific test if that works might be needed.
    return 0;
}

static void Nuitka_Genexpr_tp_dealloc( Nuitka_GenexprObject *generator )
{
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

    for( int i = 0; i <= generator->iterator_level; i++ )
    {
        if ( generator->iterators[ i ] )
        {
            Py_DECREF( generator->iterators[ i ] );
        }
    }

    Py_XDECREF( generator->m_frame );

    PyObject_GC_Del( generator );
}

static PyObject *Nuitka_Genexpr_tp_iternext( Nuitka_GenexprObject *generator )
{
    if ( generator->m_status != Generator_Status::status_Finished )
    {
        if ( generator->m_running )
        {
            PyErr_Format( PyExc_ValueError, "generator already executing" );
            return NULL;
        }

        // Query the next value

        // Put the generator back on the frame stack.
        PyFrameObject *return_frame = PyThreadState_GET()->frame;
        assertFrameObject( return_frame );

        if ( generator->m_frame )
        {
            // It would be nice if our frame were still alive. Nobody had the right to release it.
            assertFrameObject( generator->m_frame );

            // It's not supposed to be on the top right now.
            assert( return_frame != generator->m_frame );

            Py_INCREF( return_frame );
            generator->m_frame->f_back = return_frame;

            PyThreadState_GET()->frame = generator->m_frame;
        }

        generator->m_running = true;
        PyObject *result = ((producer)(generator->m_code))( generator );
        generator->m_running = false;

        // Remove the generator from the frame stack.
        assert( PyThreadState_GET()->frame == generator->m_frame );
        assertFrameObject( generator->m_frame );

        PyThreadState_GET()->frame = return_frame;
        Py_CLEAR( generator->m_frame->f_back );

        if ( result == _sentinel_value )
        {
            generator->m_status = Generator_Status::status_Finished;

            PyErr_SetNone( PyExc_StopIteration );
            return NULL;
        }
        else
        {
            if ( result )
            {
                generator->m_status = Generator_Status::status_Running;
            }
            else
            {
                generator->m_status = Generator_Status::status_Finished;
            }

            return result;
        }
    }
    else
    {
        PyErr_SetNone( PyExc_StopIteration );
        return NULL;
    }
}

static PyObject *Nuitka_Genexpr_send( Nuitka_GenexprObject *generator, PyObject *value )
{
    if ( generator->m_status == Generator_Status::status_Unused && value != NULL && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started generator" );
        return NULL;
    }

    return Nuitka_Genexpr_tp_iternext( generator );
}

static PyObject *Nuitka_Genexpr_close( Nuitka_GenexprObject *generator, PyObject *args )
{
    generator->m_status = Generator_Status::status_Finished;
    return INCREASE_REFCOUNT( Py_None );
}

static PyObject *Nuitka_Genexpr_throw( Nuitka_GenexprObject *generator, PyObject *args )
{
    PyObject *exception_type, *exception_value = NULL, *exception_tb = NULL;

    int res = PyArg_UnpackTuple( args, "throw", 1, 3, &exception_type, &exception_value, &exception_tb );

    if ( res == 0 )
    {
        return NULL;
    }

    assertObject( exception_type );

    if ( PyExceptionClass_Check( exception_type ) )
    {
        PyErr_NormalizeException( &exception_type, &exception_value, (PyObject **)&exception_tb );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        // TODO: What should be done with old value, Py_DECREF maybe?
        exception_value = exception_type;
        exception_type = INCREASE_REFCOUNT( PyExceptionInstance_Class( exception_type ) );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );
        return NULL;
    }

    assertObject( exception_type );
    assertObject( exception_value );

#if PYTHON_VERSION >= 300
    if ( exception_tb == NULL )
    {
        exception_tb = PyException_GetTraceback( exception_value );
    }
#endif

    assertObject( exception_tb );

    _SET_CURRENT_EXCEPTION( exception_type, exception_value, exception_tb );
    PyErr_Restore( exception_type, exception_value, exception_tb );
    generator->m_status = Generator_Status::status_Finished;

    return NULL;
}

static PyObject *Nuitka_Genexpr_get_name( Nuitka_GenexprObject *generator )
{
    return INCREASE_REFCOUNT( generator->m_name );
}

static PyObject *Nuitka_Genexpr_get_code( Nuitka_GenexprObject *object )
{
    return INCREASE_REFCOUNT( (PyObject *)object->m_code_object );
}

static int Nuitka_Genexpr_set_code( Nuitka_GenexprObject *object, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_code is not writable in Nuitka" );
    return -1;
}

static PyObject *Nuitka_Genexpr_get_frame( Nuitka_GenexprObject *object )
{
    if ( object->m_frame )
    {
        return INCREASE_REFCOUNT( (PyObject *)object->m_frame );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_None );
    }
}

static int Nuitka_Genexpr_set_frame( Nuitka_GenexprObject *object, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "gi_frame is not writable in Nuitka" );
    return -1;
}

static PyGetSetDef Nuitka_Genexpr_getsetlist[] =
{
    { (char *)"__name__", (getter)Nuitka_Genexpr_get_name, NULL, NULL },
    { (char *)"gi_code",  (getter)Nuitka_Genexpr_get_code, (setter)Nuitka_Genexpr_set_code, NULL },
    { (char *)"gi_frame", (getter)Nuitka_Genexpr_get_frame, (setter)Nuitka_Genexpr_set_frame, NULL },

    { NULL }
};

static PyMethodDef Nuitka_Genexpr_methods[] =
{
    {  "send", (PyCFunction)Nuitka_Genexpr_send,  METH_O, NULL },
    { "throw", (PyCFunction)Nuitka_Genexpr_throw, METH_VARARGS, NULL },
    { "close", (PyCFunction)Nuitka_Genexpr_close, METH_NOARGS, NULL },
    { NULL }
};

#include <structmember.h>

static PyMemberDef Nuitka_Genexpr_members[] =
{
    { (char *)"gi_running", T_INT, offsetof( Nuitka_GenexprObject, m_running ), READONLY },
    { NULL }
};

PyTypeObject Nuitka_Genexpr_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_generator",                          // tp_name
    sizeof(Nuitka_GenexprObject),                  // tp_basicsize
    0,                                             // tp_itemsize
    (destructor)Nuitka_Genexpr_tp_dealloc,         // tp_dealloc
    0,                                             // tp_print
    0,                                             // tp_getattr
    0,                                             // tp_setattr
    // TODO: Compare should be easy, check the benefit of doing it.
    0,                                             // tp_compare
    (reprfunc)Nuitka_Genexpr_tp_repr,              // tp_repr
    0,                                             // tp_as_number
    0,                                             // tp_as_sequence
    0,                                             // tp_as_mapping
    0,                                             // tp_hash
    0,                                             // tp_call
    0,                                             // tp_str
    PyObject_GenericGetAttr,                       // tp_getattro
    0,                                             // tp_setattro
    0,                                             // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,       // tp_flags
    0,                                             // tp_doc
    (traverseproc)Nuitka_Genexpr_tp_traverse,      // tp_traverse
    0,                                             // tp_clear
    0,                                             // tp_richcompare
    offsetof( Nuitka_GenexprObject, m_weakrefs ),  // tp_weaklistoffset
    PyObject_SelfIter,                             // tp_iter
    (iternextfunc)Nuitka_Genexpr_tp_iternext,      // tp_iternext
    Nuitka_Genexpr_methods,                        // tp_methods
    Nuitka_Genexpr_members,                        // tp_members
    Nuitka_Genexpr_getsetlist,                     // tp_getset
    0,                                             // tp_base
    0,                                             // tp_dict
    0,                                             // tp_descr_get
    0,                                             // tp_descr_set
    0                                       ,      // tp_dictoffset
    0,                                             // tp_init
    0,                                             // tp_alloc
    0,                                             // tp_new
    0,                                             // tp_free
    0,                                             // tp_is_gc
    0,                                             // tp_bases
    0,                                             // tp_mro
    0,                                             // tp_cache
    0,                                             // tp_subclasses
    0,                                             // tp_weaklist
    0                                              // tp_del
};


PyObject *Nuitka_Genexpr_New( producer code, PyObject *name, PyCodeObject *code_object, PyObject *iterated, int iterator_count, void *context, releaser cleanup )
{
    Nuitka_GenexprObject *result = PyObject_GC_New( Nuitka_GenexprObject, &Nuitka_Genexpr_Type );

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

    // Store the iterator information provided at creation time here.
    assert( iterator_count < MAX_ITERATOR_COUNT );

    result->iterator_level = 0;
    result->iterators[ 0 ] = MAKE_ITERATOR( iterated );

    for( int i = 1; i < iterator_count; i++ )
    {
        result->iterators[ i ] = NULL;
    }

    result->m_frame = NULL;

    result->m_code_object = code_object;

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}
