#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Compiled generator object type.

Another cornerstone of the integration into CPython. Try to behave as well as normal
generator does or even better.
"""

gfunction_type_code = """

// *** KFunction type begin
static PyTypeObject PyGFunction_Type;

// The PyGFunctionObject must have identical layout to PyCFunctionTypeObject.
typedef struct {
    PyObject_HEAD

    PyObject *m_name;
    PyObject *m_self;

    PyObject *m_module;
    PyObject *m_doc;

    // Put this up as a return value of "yield" in the generator function.
    PyObject *m_yield_send;

    // Put this up as the exception to be raised in the generator once it is continued
    // or the exception occured during continuation.
    PyObject *exception_type, *exception_value, *exception_tb;

    // This is the value produced by "yield" to the outside caller.
    PyObject *m_yield_value;

    void *m_code;

    PyObject *m_dict;
    PyObject *m_weakrefs;

    // Was it ever used, is it still running, or already finished.
    int m_status;

    bool m_running;
    long m_counter;
} PyGFunctionObject;

const int state_unused = 0;
const int state_running = 1;
const int state_finished = 2;

static long PyGFunction_tp_traverse( PyObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it could be NULL
    // instead. The methodobject visits its self and module. I understand this is probably
    // so that back references of this function to its upper do not make it stay in the
    // memory. A specific test if that works might be needed.
    return 0;
}


static PyObject *PyGFunction_handover( PyGFunctionObject *generator )
{
    if ( generator->m_running )
    {
        PyErr_Format( PyExc_ValueError, "generator already executing" );
        return NULL;
    }

    // Set value or exception.

    if ( generator->m_yield_send != NULL && generator->m_yield_send != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "can't send non-None value to a just-started generator" );
        return NULL;
    }

    if ( generator->exception_type != NULL )
    {
        PyErr_Restore( generator->exception_type, generator->exception_value, generator->exception_tb );
    }

    generator->m_running = true;

    // TODO: Swap context here.

    generator->m_running = false;

    // TODO: Treat StopIteration raising

    return generator->m_yield_value;
}

static PyObject *PyGFunction_send( PyGFunctionObject *generator, PyObject *value )
{
    // TODO: Need to define a way to handover value before switching context
    // where we should check if it is already the running context and give
    // value as the return code of yield

    assert (false);
}

static PyObject *PyGFunction_close( PyGFunctionObject *generator, PyObject *args )
{
    generator->exception_type = PyExc_GeneratorExit;

    PyGFunction_handover( generator );
    generator->m_status = state_finished;

    PyErr_Restore( generator->exception_type, generator->exception_value, generator->exception_tb );

    if ( PyErr_ExceptionMatches( PyExc_GeneratorExit ) || PyErr_ExceptionMatches( PyExc_StopIteration ))
    {
        PyErr_Clear();

        return INCREASE_REFCOUNT( Py_None );
    }

    PyErr_Format( PyExc_RuntimeError, "generator ignored GeneratorExit" );
    return NULL;
}

static void PyGFunction_tp_del( PyGFunctionObject *generator )
{
    if ( generator->m_status != state_running )
    {
        return;
    }

    // Keep it alive for just a little bit longer, enough to close the generator and
    // avoid memory/reference loss.
    assert( generator->ob_refcnt == 0 );
    generator->ob_refcnt = 1;

    // Remember current exception. CPython calls del with it set sometimes.
    PyObject *exception_type, *exception_value, *exception_tb;
    PyErr_Fetch( &exception_type, &exception_value, &exception_tb );

    PyObject *result = PyGFunction_close( generator, NULL );

    if ( result == NULL )
    {
        PyErr_WriteUnraisable( (PyObject *)generator );
    }
    else
    {
        Py_DECREF( result );
    }

    /* Restore the saved exception. */
    PyErr_Restore( exception_type, exception_value, exception_tb );

    generator->ob_refcnt -= 1;
}

static void PyGFunction_tp_dealloc( PyGFunctionObject *generator )
{
    // Make sure the generator is "closed" first.
    if ( generator->m_status == state_running )
    {
        PyGFunction_tp_del( generator );
    }

    // Now it is safe to release references and memory for it.
    _PyObject_GC_UNTRACK( generator );

    if ( generator->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)generator );
    }

    Py_DECREF( generator->m_self );
    Py_DECREF( generator->m_name );
    Py_XDECREF( generator->m_dict );

    PyObject_GC_Del( generator );
}


static PyObject *PyGFunction_throw( PyGFunctionObject *generator, PyObject *args )
{
    int res = PyArg_UnpackTuple( args, "throw", 1, 3, &generator->exception_type, &generator->exception_value, &generator->exception_tb );

    if ( res == 0 )
    {
        return NULL;
    }

    // TODO: Check types.
    PyGFunction_handover( generator );

    // TODO: Handle exceptions.
}


static PyObject *PyGFunction_iternext( PyGFunctionObject *generator )
{
    // TODO: Set None as the yield value
    PyGFunction_handover( generator );
    // TODO: return the yielded
}


static PyObject *PyGFunction_repr( PyGFunctionObject *generator )
{
    return PyString_FromFormat( "<compiled generator %s at %p>", PyString_AsString( generator->m_name ), generator );
}


static PyObject *PyGFunction_get_name( PyGFunctionObject *generator )
{
    return INCREASE_REFCOUNT( generator->m_name );
}

static PyGetSetDef PyGFunction_getsetlist[] =
{
    { (char * )"__name__", (getter)PyGFunction_get_name, NULL, NULL },
    { NULL }
};

static PyMethodDef PyGFunction_methods[] =
{
    { "send", (PyCFunction)PyGFunction_send,  METH_O, NULL },
    {"throw", (PyCFunction)PyGFunction_throw, METH_VARARGS, NULL },
    {"close", (PyCFunction)PyGFunction_close, METH_NOARGS, NULL },
    { NULL }
};

static void initGFunctionType()
{
    PyGFunction_Type =
    {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "compiled_generator",                       // tp_name
        sizeof(PyGFunctionObject),                  // tp_basicsize
        0,                                          // tp_itemsize
        (destructor)PyGFunction_tp_dealloc,         // tp_dealloc
        0,                                          // tp_print
        0,                                          // tp_getattr
        0,                                          // tp_setattr
        // TODO: Compare should be easy, check the benefit of doing it.
        0,                                          // tp_compare
        (reprfunc)PyGFunction_repr,                 // tp_repr
        0,                                          // tp_as_number
        0,                                          // tp_as_sequence
        0,                                          // tp_as_mapping
        0,                                          // tp_hash
        0,                                          // tp_call
        0,                                          // tp_str
        PyObject_GenericGetAttr,                    // tp_getattro
        0,                                          // tp_setattro
        0,                                          // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,    // tp_flags
        0,                                          // tp_doc
        (traverseproc)PyGFunction_tp_traverse,      // tp_traverse
        0,                                          // tp_clear
        0,                                          // tp_richcompare
        offsetof(PyGFunctionObject, m_weakrefs),    // tp_weaklistoffset
        PyObject_SelfIter,                          // tp_iter
        (iternextfunc)PyGFunction_iternext,         // tp_iternext
        PyGFunction_methods,                        // tp_methods
        0,                                          // tp_members
        PyGFunction_getsetlist,                     // tp_getset
        0,                                          // tp_base
        0,                                          // tp_dict
        0,                                          // tp_descr_get
        0,                                          // tp_descr_set
        offsetof( PyGFunctionObject, m_dict ),      // tp_dictoffset
        0,                                          // tp_init
        0,                                          // tp_alloc
        0,                                          // tp_new
        0,                                          // tp_free
        0,                                          // tp_is_gc
        0,                                          // tp_bases
        0,                                          // tp_mro
        0,                                          // tp_cache
        0,                                          // tp_subclasses
        0,                                          // tp_weaklist
        (destructor)PyGFunction_tp_del              // tp_del
    };
};

static PyObject *PyGFunction_New( void *code )
{
    PyGFunctionObject *result = PyObject_GC_New( PyGFunctionObject, &PyGFunction_Type );

    result->m_weakrefs = NULL;

    result->m_code = code;
    result->m_status = state_unused;

    result->m_name = PyString_FromString( "<generator>" );

    _PyObject_GC_TRACK( result );
    return (PyObject *)result;
}

"""
