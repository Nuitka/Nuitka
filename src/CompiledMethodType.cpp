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

#include "nuitka/compiled_method.hpp"

#include "structmember.h"

static PyObject *Nuitka_Method_get__doc__( Nuitka_MethodObject *method, void *closure )
{
    return INCREASE_REFCOUNT( method->m_function->m_doc );
}

static PyGetSetDef Nuitka_Method_getsets[] =
{
    { (char *)"__doc__", (getter)Nuitka_Method_get__doc__, NULL, NULL },
    { NULL }
};

#define OFF( x ) offsetof( Nuitka_MethodObject, x )

static PyMemberDef Nuitka_Method_members[] =
{
    { (char *)"im_class", T_OBJECT, OFF( m_class ), READONLY|RESTRICTED, (char *)"the class associated with a method"},
    { (char *)"im_func", T_OBJECT, OFF( m_function ), READONLY|RESTRICTED, (char *)"the function (or other callable) implementing a method" },
    { (char *)"__func__", T_OBJECT, OFF( m_function ), READONLY|RESTRICTED, (char *)"the function (or other callable) implementing a method" },
    { (char *)"im_self",  T_OBJECT, OFF( m_object ), READONLY|RESTRICTED, (char *)"the instance to which a method is bound; None for unbound method" },
    { (char *)"__self__", T_OBJECT, OFF( m_object ), READONLY|RESTRICTED, (char *)"the instance to which a method is bound; None for unbound method" },
    { NULL }
};

static char const *GET_CLASS_NAME( PyObject *klass )
{
    if ( klass == NULL )
    {
        return "?";
    }
    else
    {
        PyObject *name = PyObject_GetAttrString( klass, "__name__" );

        if ( name == NULL || !PyString_Check( name ) )
        {
            PyErr_Clear();
            return "?";
        }
        else
        {
            return PyString_AS_STRING( name );
        }
    }
}

static char const *GET_INSTANCE_CLASS_NAME( PyObject *instance )
{
    PyObject *klass = PyObject_GetAttrString( instance, "__class__" );

    // Fallback to type as this cannot fail.
    if ( klass == NULL )
    {
        PyErr_Clear();
        klass = INCREASE_REFCOUNT( (PyObject *)instance->ob_type );
    }

    char const *result = GET_CLASS_NAME( klass );

    Py_DECREF( klass );

    return result;
}

static PyObject *Nuitka_Method_tp_call( Nuitka_MethodObject *method, PyObject *args, PyObject *kw )
{
    Py_ssize_t arg_count = PyTuple_Size( args );

    if ( method->m_object == NULL )
    {
        if (unlikely( arg_count < 1 ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "unbound compiled_method %s%s must be called with %s instance as first argument (got nothing instead)",
                GET_CALLABLE_NAME( (PyObject *)method->m_function ),
                GET_CALLABLE_DESC( (PyObject *)method->m_function ),
                GET_CLASS_NAME( method->m_class )
            );
            return NULL;
        }
        else
        {
            PyObject *self = PyTuple_GET_ITEM( args, 0 );
            assert( self != NULL );

            int result = PyObject_IsInstance( self, method->m_class );

            if (unlikely( result < 0 ))
            {
                return NULL;
            }
            else if (unlikely( result == 0 ))
            {
                PyErr_Format(
                    PyExc_TypeError,
                    "unbound compiled_method %s%s must be called with %s instance as first argument (got %s instance instead)",
                    GET_CALLABLE_NAME( (PyObject *)method->m_function ),
                    GET_CALLABLE_DESC( (PyObject *)method->m_function ),
                    GET_CLASS_NAME( method->m_class ),
                    GET_INSTANCE_CLASS_NAME( (PyObject *)self )
                );

                return NULL;
            }
        }

        return method->m_function->ob_type->tp_call(
            (PyObject *)method->m_function, args, kw
        );
    }
    else
    {
        if (unlikely( method->m_function->m_method_arg_parser == NULL ))
        {
            // This injects the extra argument, and is not normally used.
            PyObject *new_args = PyTuple_New( arg_count + 1 );

            PyTuple_SET_ITEM( new_args, 0, INCREASE_REFCOUNT( method->m_object ) );

            for ( int i = 0; i < arg_count; i++ )
            {
                PyObject *v = PyTuple_GET_ITEM( args, i );
                Py_XINCREF( v );

                PyTuple_SET_ITEM( new_args, i + 1, v );
            }

            PyObject *result = method->m_function->ob_type->tp_call(
                (PyObject *)method->m_function,
                new_args,
                kw
                                                                    );

            Py_DECREF( new_args );

            return result;
        }
        else
        {
            assert( method->m_function->m_has_args );

            return method->m_function->m_method_arg_parser(
                (PyObject *)method->m_function->m_context,
                method->m_object,
                args,
                kw
            );
        }
    }
}


static PyObject *Nuitka_Method_tp_descr_get( Nuitka_MethodObject *method, PyObject *object, PyObject *klass )
{
    // Don't rebind already bound methods.
    if ( method->m_object != NULL )
    {
        return INCREASE_REFCOUNT( (PyObject *)method );
    }

    if ( method->m_class != NULL && klass != NULL )
    {
        // Quick subclass test, bound methods remain the same if the class is a sub class
        int result = PyObject_IsSubclass( klass, method->m_class );

        if (unlikely( result < 0 ))
        {
            return NULL;
        }
        else if ( result == 0 )
        {
            return INCREASE_REFCOUNT( (PyObject *)method );
        }
    }

    return Nuitka_Method_New( method->m_function, object, klass );
}

static PyObject *Nuitka_Method_tp_getattro( Nuitka_MethodObject *method, PyObject *name )
{
    PyObject *descr = _PyType_Lookup( &Nuitka_Method_Type, name );

    if ( descr != NULL )
    {
        if ( PyType_HasFeature( descr->ob_type, Py_TPFLAGS_HAVE_CLASS ) && ( descr->ob_type->tp_descr_get != NULL ) )
        {
            return descr->ob_type->tp_descr_get(
                descr,
                (PyObject *)method,
                (PyObject *)method->ob_type
            );
        }
        else
        {
            return INCREASE_REFCOUNT( descr );
        }
    }

    return PyObject_GetAttr( (PyObject *)method->m_function, name );
}


static long Nuitka_Method_tp_traverse( Nuitka_MethodObject *method, visitproc visit, void *arg )
{
    Py_VISIT( method->m_function );
    Py_VISIT( method->m_object );
    Py_VISIT( method->m_class );

    return 0;
}

 // tp_repr slot, decide how a function shall be output
static PyObject *Nuitka_Method_tp_repr( Nuitka_MethodObject *method )
{
    if ( method->m_object == NULL )
    {
        return PyString_FromFormat(
            "<unbound compiled_method %s.%s>",
            GET_CLASS_NAME( method->m_class ),
            PyString_AsString( method->m_function->m_name )
        );
    }
    else
    {
        // Note: CPython uses repr ob the object, although a comment despises it, we
        // do it for compatibility.
        PyObject *object_repr = PyObject_Repr( method->m_object );

        if ( object_repr == NULL )
        {
            return NULL;
        }
        else if ( !PyString_Check( object_repr ) )
        {
            Py_DECREF( object_repr );
            return NULL;
        }

        PyObject *result = PyString_FromFormat(
            "<bound compiled_method %s.%s of %s>",
            GET_CLASS_NAME( method->m_class ),
            PyString_AsString( method->m_function->m_name ),
            PyString_AS_STRING( object_repr )
        );

        Py_DECREF( object_repr );

        return result;
    }
}

static int Nuitka_Method_tp_compare( Nuitka_MethodObject *a, Nuitka_MethodObject *b )
{
    if ( a->m_function->m_counter < b->m_function->m_counter )
    {
        return -1;
    }
    else if ( a->m_function->m_counter > b->m_function->m_counter )
    {
        return 1;
    }
    else if ( a->m_object == b->m_object )
    {
        return 0;
    }
    else if ( a->m_object == NULL )
    {
        return -1;
    }
    else if ( b->m_object == NULL )
    {
        return 1;
    }
    else
    {
        return PyObject_Compare( a->m_object, b->m_object );
    }
}

static long Nuitka_Method_tp_hash( Nuitka_MethodObject *method )
{
    // Just give the hash of the method function, that ought to be good enough.
    return method->m_function->m_counter;
}

// Cache for method object, try to avoid malloc overhead.
static Nuitka_MethodObject *method_cache_head = NULL;
static int method_cache_size = 0;
static const int max_method_cache_size = 4096;

static void Nuitka_Method_tp_dealloc( Nuitka_MethodObject *method )
{
    _PyObject_GC_UNTRACK( method );

    if ( method->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)method );
    }

    Py_XDECREF( method->m_dict );
    Py_XDECREF( method->m_object );

    Py_DECREF( (PyObject *)method->m_function );

    if (likely( method_cache_size < max_method_cache_size ))
    {
        method->m_object = (PyObject *)method_cache_head;
        method_cache_head = method;
        method_cache_size += 1;
    }
    else {
        PyObject_GC_Del( method );
    }
}

static PyObject *Nuitka_Method_tp_new( PyTypeObject* type, PyObject* args, PyObject *kw )
{
    PyObject *func;
    PyObject *self;
    PyObject *klass = NULL;

    if ( !_PyArg_NoKeywords( "instancemethod", kw ) )
    {
        return NULL;
    }
    else if ( !PyArg_UnpackTuple( args, "compiled_method", 2, 3, &func, &self, &klass ) )
    {
        return NULL;
    }
    else if ( !PyCallable_Check( func ) )
    {
        PyErr_Format( PyExc_TypeError, "first argument must be callable" );
        return NULL;
    }
    else
    {
        if ( self == Py_None )
        {
            self = NULL;
        }

        if ( self == NULL && klass == NULL )
        {
            PyErr_Format( PyExc_TypeError, "unbound methods must have non-NULL im_class" );
            return NULL;
        }
    }

    assert( Nuitka_Function_Check( func ) );

    return Nuitka_Method_New( (Nuitka_FunctionObject *)func, self, klass );
}

static const long tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_HAVE_WEAKREFS;

PyTypeObject Nuitka_Method_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_method",
    sizeof(Nuitka_MethodObject),
    0,
    (destructor)Nuitka_Method_tp_dealloc,        // tp_dealloc
    0,                                           // tp_print
    0,                                           // tp_getattr
    0,                                           // tp_setattr
    (cmpfunc)Nuitka_Method_tp_compare,           // tp_compare
    (reprfunc)Nuitka_Method_tp_repr,             // tp_repr
    0,                                           // tp_as_number
    0,                                           // tp_as_sequence
    0,                                           // tp_as_mapping
    (hashfunc)Nuitka_Method_tp_hash,             // tp_hash
    (ternaryfunc)Nuitka_Method_tp_call,          // tp_call
    0,                                           // tp_str
    (getattrofunc)Nuitka_Method_tp_getattro,     // tp_getattro
    PyObject_GenericSetAttr,                     // tp_setattro
    0,                                           // tp_as_buffer
    tp_flags,                                    // tp_flags
    0,                                           // tp_doc
    (traverseproc)Nuitka_Method_tp_traverse,     // tp_traverse
    0,                                           // tp_clear
    0,                                           // tp_richcompare
    offsetof( Nuitka_MethodObject, m_weakrefs ), // tp_weaklistoffset
    0,                                           // tp_iter
    0,                                           // tp_iternext
    0,                                           // tp_methods
    Nuitka_Method_members,                       // tp_members
    Nuitka_Method_getsets,                       // tp_getset
    0,                                           // tp_base
    0,                                           // tp_dict
    (descrgetfunc)Nuitka_Method_tp_descr_get,    // tp_descr_get
    0,                                           // tp_descr_set
    0,                                           // tp_dictoffset
    0,                                           // tp_init
    0,                                           // tp_alloc
    Nuitka_Method_tp_new                         // tp_new
};

PyObject *Nuitka_Method_New( Nuitka_FunctionObject *function, PyObject *object, PyObject *klass )
{
    Nuitka_MethodObject *result = method_cache_head;

    if ( result != NULL )
    {
        method_cache_head = (Nuitka_MethodObject *)method_cache_head->m_object;
        method_cache_size -= 1;

        PyObject_INIT( result, &Nuitka_Method_Type );
    }
    else
    {
        result = PyObject_GC_New( Nuitka_MethodObject, &Nuitka_Method_Type );
    }

    if (unlikely( result == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create method %s", PyString_AsString( function->m_name ) );
        throw _PythonException();
    }

    result->m_function = (Nuitka_FunctionObject * )INCREASE_REFCOUNT( (PyObject *)function );

    result->m_object = object;
    Py_XINCREF( object );
    result->m_class = klass;

    result->m_module = function->m_module;

    result->m_dict   = NULL;
    result->m_weakrefs = NULL;

    _PyObject_GC_TRACK( result );
    return (PyObject *)result;
}
