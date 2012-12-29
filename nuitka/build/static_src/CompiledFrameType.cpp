//     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
#include "nuitka/prelude.hpp"

#include "structmember.h"

#define OFF( x ) offsetof( PyFrameObject, x )

struct Nuitka_FrameObject
{
    PyFrameObject m_frame;
};

static PyMemberDef Nuitka_Frame_memberlist[] = {
    { (char *)"f_back", T_OBJECT, OFF( f_back ), READONLY | RESTRICTED },
    { (char *)"f_code", T_OBJECT, OFF( f_code ), READONLY | RESTRICTED },
    { (char *)"f_builtins", T_OBJECT, OFF( f_builtins ), READONLY | RESTRICTED },
    { (char *)"f_globals", T_OBJECT, OFF( f_globals ), READONLY | RESTRICTED },
    { (char *)"f_lasti", T_INT, OFF( f_lasti ), READONLY | RESTRICTED },
    { NULL }
};

#if PYTHON_VERSION < 300

static PyObject *Nuitka_Frame_get_exc_traceback( PyFrameObject *frame )
{
    if ( frame->f_exc_traceback != NULL )
    {
        return INCREASE_REFCOUNT( frame->f_exc_traceback );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_None );
    }
}

static int Nuitka_Frame_set_exc_traceback( PyFrameObject *frame, PyObject *traceback )
{
    if ( frame->f_exc_traceback != NULL )
    {
        Py_DECREF(frame->f_exc_traceback );
    }

    if ( traceback == Py_None )
    {
        frame->f_exc_traceback = NULL;
    }
    else
    {
        frame->f_exc_traceback = INCREASE_REFCOUNT_X( traceback );
    }

    return 0;
}

static PyObject *Nuitka_Frame_get_exc_type( PyFrameObject *frame )
{
    if ( frame->f_exc_type != NULL )
    {
        return INCREASE_REFCOUNT( frame->f_exc_type );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_None );
    }
}

static int Nuitka_Frame_set_exc_type( PyFrameObject *frame, PyObject *exception_type )
{
    if ( frame->f_exc_type != NULL )
    {
        Py_DECREF( frame->f_exc_type );
    }

    if ( exception_type == Py_None )
    {
        frame->f_exc_type = NULL;
    }
    else
    {
        frame->f_exc_type = INCREASE_REFCOUNT_X( exception_type );
    }

    return 0;
}

static PyObject *Nuitka_Frame_get_exc_value( PyFrameObject *frame )
{
    if ( frame->f_exc_value != NULL )
    {
        return INCREASE_REFCOUNT( frame->f_exc_value );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_None );
    }
}

static int Nuitka_Frame_set_exc_value( PyFrameObject *frame, PyObject *exception_value )
{
    if ( frame->f_exc_value != NULL )
    {
        Py_DECREF( frame->f_exc_value );
    }

    if ( exception_value == Py_None )
    {
        frame->f_exc_value = NULL;
    }
    else
    {
        frame->f_exc_value = INCREASE_REFCOUNT_X( exception_value );
    }

    return 0;
}
#endif

static PyObject *Nuitka_Frame_getlocals( PyFrameObject *frame, void *closure )
{
    // Note: Very important that we correctly support this function to work:
    PyFrame_FastToLocals( frame );

    return INCREASE_REFCOUNT( frame->f_locals );
}

static PyObject *Nuitka_Frame_getlineno( PyFrameObject *frame, void *closure )
{
    return PyInt_FromLong( frame->f_lineno );
}

static PyObject *Nuitka_Frame_gettrace( PyFrameObject *frame, void *closure )
{
    return INCREASE_REFCOUNT( frame->f_trace );
}

static int Nuitka_Frame_settrace( PyFrameObject *frame, PyObject* v, void *closure )
{
    PyErr_Format( PyExc_RuntimeError, "f_trace is not writable in Nuitka" );
    return -1;
}

static PyObject *Nuitka_Frame_get_restricted( PyFrameObject *frame, void *closure )
{
    return INCREASE_REFCOUNT( Py_False );
}

static PyGetSetDef Nuitka_Frame_getsetlist[] = {
    { (char *)"f_locals", (getter)Nuitka_Frame_getlocals, NULL, NULL },
    { (char *)"f_lineno", (getter)Nuitka_Frame_getlineno, NULL, NULL },
    { (char *)"f_trace", (getter)Nuitka_Frame_gettrace, (setter)Nuitka_Frame_settrace, NULL },
    { (char *)"f_restricted", (getter)Nuitka_Frame_get_restricted, NULL, NULL },
#if PYTHON_VERSION < 300
    { (char *)"f_exc_traceback", (getter)Nuitka_Frame_get_exc_traceback, (setter)Nuitka_Frame_set_exc_traceback, NULL },
    { (char *)"f_exc_type", (getter)Nuitka_Frame_get_exc_type, (setter)Nuitka_Frame_set_exc_type, NULL },
    { (char *)"f_exc_value", (getter)Nuitka_Frame_get_exc_value, (setter)Nuitka_Frame_set_exc_value, NULL },
#endif
    { NULL }
};

static void Nuitka_Frame_tp_dealloc( Nuitka_FrameObject *nuitka_frame )
{
    Nuitka_GC_UnTrack( nuitka_frame );
    Py_TRASHCAN_SAFE_BEGIN( nuitka_frame )

    PyFrameObject *frame = &nuitka_frame->m_frame;

    // locals
    PyObject **valuestack = frame->f_valuestack;
    for ( PyObject **p = frame->f_localsplus; p < valuestack; p++ )
    {
        Py_CLEAR( *p );
    }

    // stack if any
    if ( frame->f_stacktop != NULL )
    {
        for ( PyObject **p = valuestack; p < frame->f_stacktop; p++ )
        {
            Py_XDECREF( *p );
        }
    }

    Py_XDECREF( frame->f_back );
    Py_DECREF( frame->f_builtins );
    Py_DECREF( frame->f_globals );
    Py_CLEAR( frame->f_locals );
    Py_CLEAR( frame->f_trace );
    Py_CLEAR( frame->f_exc_type );
    Py_CLEAR( frame->f_exc_value );
    Py_CLEAR( frame->f_exc_traceback );

    PyObject_GC_Del( nuitka_frame );

    Py_TRASHCAN_SAFE_END( nuitka_frame )
}

static int Nuitka_Frame_tp_traverse( PyFrameObject *frame, visitproc visit, void *arg )
{
    Py_VISIT( frame->f_back );
    Py_VISIT( frame->f_code );
    Py_VISIT( frame->f_builtins );
    Py_VISIT( frame->f_globals );
    Py_VISIT( frame->f_locals );
    Py_VISIT( frame->f_trace );
    Py_VISIT( frame->f_exc_type );
    Py_VISIT( frame->f_exc_value );
    Py_VISIT( frame->f_exc_traceback );

    // locals
    int slots = frame->f_code->co_nlocals + PyTuple_GET_SIZE( frame->f_code->co_cellvars ) + PyTuple_GET_SIZE( frame->f_code->co_freevars );
    PyObject **fastlocals = frame->f_localsplus;
    for ( int i = slots; --i >= 0; ++fastlocals )
    {
        Py_VISIT( *fastlocals );
    }

    // stack if any
    if ( frame->f_stacktop != NULL )
    {
        for ( PyObject **p = frame->f_valuestack; p < frame->f_stacktop; p++ )
        {
            Py_VISIT( *p );
        }
    }

    return 0;
}

static void Nuitka_Frame_tp_clear( PyFrameObject *frame )
{
    PyObject **oldtop = frame->f_stacktop;
    frame->f_stacktop = NULL;

    Py_CLEAR( frame->f_exc_type );
    Py_CLEAR( frame->f_exc_value );
    Py_CLEAR( frame->f_exc_traceback );
    Py_CLEAR( frame->f_trace );

    // locals
    int slots = frame->f_code->co_nlocals + PyTuple_GET_SIZE( frame->f_code->co_cellvars ) + PyTuple_GET_SIZE( frame->f_code->co_freevars );
    PyObject **fastlocals = frame->f_localsplus;

    for ( int i = slots; --i >= 0; ++fastlocals )
    {
        Py_CLEAR( *fastlocals );
    }

    // stack if any
    if ( oldtop != NULL )
    {
        for ( PyObject **p = frame->f_valuestack; p < oldtop; p++ )
        {
            Py_CLEAR( *p );
        }
    }
}

static PyObject *Nuitka_Frame_sizeof( PyFrameObject *frame )
{
    Py_ssize_t slots =
        frame->f_code->co_stacksize +
        frame->f_code->co_nlocals +
        PyTuple_GET_SIZE( frame->f_code->co_cellvars ) +
        PyTuple_GET_SIZE( frame->f_code->co_freevars );

    return PyInt_FromSsize_t( sizeof( Nuitka_FrameObject ) + slots * sizeof(PyObject *) );
}

static PyMethodDef Nuitka_Frame_methods[] =
{
    { "__sizeof__", (PyCFunction)Nuitka_Frame_sizeof,  METH_NOARGS, "F.__sizeof__() -> size of F in memory, in bytes" },
    { NULL, NULL }
};

PyTypeObject Nuitka_Frame_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_frame",
    sizeof(Nuitka_FrameObject),
    sizeof(PyObject *),
    (destructor)Nuitka_Frame_tp_dealloc,        // tp_dealloc
    0,                                          // tp_print
    0,                                          // tp_getattr
    0,                                          // tp_setattr
    0,                                          // tp_compare
    0,                                          // tp_repr
    0,                                          // tp_as_number
    0,                                          // tp_as_sequence
    0,                                          // tp_as_mapping
    0,                                          // tp_hash
    0,                                          // tp_call
    0,                                          // tp_str
    PyObject_GenericGetAttr,                    // tp_getattro
    PyObject_GenericSetAttr,                    // tp_setattro
    0,                                          // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,    // tp_flags
    0,                                          // tp_doc
    (traverseproc)Nuitka_Frame_tp_traverse,     // tp_traverse
    (inquiry)Nuitka_Frame_tp_clear,             // tp_clear
    0,                                          // tp_richcompare
    0,                                          // tp_weaklistoffset
    0,                                          // tp_iter
    0,                                          // tp_iternext
    Nuitka_Frame_methods,                       // tp_methods
    Nuitka_Frame_memberlist,                    // tp_members
    Nuitka_Frame_getsetlist,                    // tp_getset
    0,                                          // tp_base
    0,                                          // tp_dict
};

static void tb_dealloc( PyTracebackObject *tb )
{
    // printf( "dealloc TB %ld %lx FR %ld %lx\n", Py_REFCNT( tb ), (long)tb, Py_REFCNT( tb->tb_frame ), (long)tb->tb_frame );

    PyObject_GC_UnTrack(tb);
    //    Py_TRASHCAN_SAFE_BEGIN(tb)
    Py_XDECREF( tb->tb_next );
    Py_XDECREF( tb->tb_frame );
    PyObject_GC_Del( tb );
    // Py_TRASHCAN_SAFE_END(tb)
}

PyFrameObject *MAKE_FRAME( PyCodeObject *code, PyObject *module )
{
    PyTraceBack_Type.tp_dealloc = (destructor)tb_dealloc;

    assertCodeObject( code );

    PyObject *globals = ((PyModuleObject *)module)->md_dict;
    assert( PyDict_Check( globals ) );

    Py_ssize_t ncells = PyTuple_GET_SIZE( code->co_cellvars );
    Py_ssize_t nfrees = PyTuple_GET_SIZE( code->co_freevars );
    Py_ssize_t extras = code->co_stacksize + code->co_nlocals + ncells + nfrees;

    Nuitka_FrameObject *result = PyObject_GC_NewVar( Nuitka_FrameObject, &Nuitka_Frame_Type, extras );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    PyFrameObject *frame = &result->m_frame;

    frame->f_code = code;

    extras = code->co_nlocals + ncells + nfrees;
    frame->f_valuestack = frame->f_localsplus + extras;

    for ( Py_ssize_t i = 0; i < extras; i++ )
    {
        frame->f_localsplus[i] = NULL;
    }

    frame->f_locals = NULL;
    frame->f_trace = INCREASE_REFCOUNT( Py_None );
    frame->f_exc_type = frame->f_exc_value = frame->f_exc_traceback = NULL;

    frame->f_stacktop = frame->f_valuestack;
    frame->f_builtins = INCREASE_REFCOUNT( module_builtin->md_dict );

    frame->f_back = NULL;

    frame->f_globals = INCREASE_REFCOUNT( globals );

    assert( ( code->co_flags & CO_NEWLOCALS ) == CO_NEWLOCALS );

    if (likely( (code->co_flags & CO_OPTIMIZED ) == CO_OPTIMIZED ))
    {
        frame->f_locals = NULL;
    }
    else
    {
        frame->f_locals = PyDict_New();

        if (unlikely( frame->f_locals == NULL ))
        {
            Py_DECREF( result );
            throw _PythonException();
        }
    }

    frame->f_tstate = PyThreadState_GET();

    frame->f_lasti = -1;
    frame->f_lineno = code->co_firstlineno;
    frame->f_iblock = 0;

    Nuitka_GC_Track( result );
    return (PyFrameObject *)result;
}
