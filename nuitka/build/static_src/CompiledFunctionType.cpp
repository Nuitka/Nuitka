//     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "nuitka/compiled_method.hpp"

// Needed for offsetof
#include <stddef.h>

// tp_descr_get slot, bind a function to an object.
static PyObject *Nuitka_Function_descr_get( PyObject *function, PyObject *object, PyObject *klass )
{
    assert( Nuitka_Function_Check( function ) );

#if PYTHON_VERSION >= 300
    if ( object == NULL || object == Py_None )
    {
        return INCREASE_REFCOUNT( function );
    }
#endif

    return Nuitka_Method_New(
        (Nuitka_FunctionObject *)function,
        object == Py_None ? NULL : object,
        klass
    );
}

 // tp_repr slot, decide how a function shall be output
static PyObject *Nuitka_Function_tp_repr( Nuitka_FunctionObject *function )
{
#if PYTHON_VERSION < 300
    return PyString_FromFormat(
#else
    return PyUnicode_FromFormat(
#endif
        "<compiled function %s at %p>",
#if PYTHON_VERSION < 330
        Nuitka_String_AsString( function->m_name ),
#else
        Nuitka_String_AsString( function->m_qualname ),
#endif
        function
    );
}

static PyObject *Nuitka_Function_tp_call( Nuitka_FunctionObject *function, PyObject *args, PyObject *kw )
{
    assertObject( args );
    assert( PyTuple_Check( args ) );

    if ( kw || function->m_direct_arg_parser == NULL )
    {
        return function->m_code(
            function,
            &PyTuple_GET_ITEM( args, 0 ),
            PyTuple_GET_SIZE( args ),
            kw
        );
    }
    else
    {
        return function->m_direct_arg_parser(
            function,
            &PyTuple_GET_ITEM( args, 0 ),
            PyTuple_GET_SIZE( args )
        );
    }
}

static long Nuitka_Function_tp_traverse( PyObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it
    // could be NULL instead. The methodobject visits its self and module. I
    // understand this is probably so that back references of this function to
    // its upper do not make it stay in the memory. A specific test if that
    // works might be needed.
    return 0;
}

#if PYTHON_VERSION < 300
static int Nuitka_Function_tp_compare( Nuitka_FunctionObject *a, Nuitka_FunctionObject *b )
{
    if ( a->m_counter == b->m_counter )
    {
       return 0;
    }
    else
    {
       return a->m_counter < b->m_counter ? -1 : 1;
    }
}
#endif

static long Nuitka_Function_tp_hash( Nuitka_FunctionObject *function )
{
    return function->m_counter;
}

static PyObject *Nuitka_Function_get_name( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( object->m_name );
}

static int Nuitka_Function_set_name( Nuitka_FunctionObject *object, PyObject *value )
{
#if PYTHON_VERSION < 300
    if (unlikely( value == NULL || PyString_Check( value ) == 0 ))
#else
    if (unlikely( value == NULL || PyUnicode_Check( value ) == 0 ))
#endif
    {
       PyErr_Format( PyExc_TypeError, "__name__ must be set to a string object" );
       return -1;
    }

    PyObject *old = object->m_name;
    object->m_name = INCREASE_REFCOUNT( value );
    Py_DECREF( old );

    return 0;
}

#if PYTHON_VERSION >= 330
static PyObject *Nuitka_Function_get_qualname( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( object->m_qualname );
}

static int Nuitka_Function_set_qualname( Nuitka_FunctionObject *object, PyObject *value )
{
    if (unlikely( value == NULL || PyUnicode_Check( value ) == 0 ))
    {
       PyErr_Format( PyExc_TypeError, "__qualname__ must be set to a string object" );
       return -1;
    }

    PyObject *old = object->m_qualname;
    object->m_qualname = INCREASE_REFCOUNT( value );
    Py_DECREF( old );

    return 0;
}
#endif

static PyObject *Nuitka_Function_get_doc( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( object->m_doc );
}

static int Nuitka_Function_set_doc( Nuitka_FunctionObject *object, PyObject *value )
{
    if ( value == Py_None || value == NULL )
    {
       object->m_doc = Py_None;
    }
#if PYTHON_VERSION < 300
    else if (unlikely( PyString_Check( value ) == 0 ))
    {
       PyErr_Format( PyExc_TypeError, "__name__ must be set to a string object" );
       return -1;
    }
#else
    else if (unlikely( PyUnicode_Check( value ) == 0 ))
    {
       PyErr_Format( PyExc_TypeError, "__name__ must be set to a string object" );
       return -1;
    }
#endif
    else
    {
       object->m_doc = INCREASE_REFCOUNT( value );
    }

    return 0;
}

static PyObject *Nuitka_Function_get_dict( Nuitka_FunctionObject *object )
{
    if ( object->m_dict == NULL )
    {
        object->m_dict = PyDict_New();
    }

    return INCREASE_REFCOUNT( object->m_dict );
}

static int Nuitka_Function_set_dict( Nuitka_FunctionObject *object, PyObject *value )
{
    if (unlikely( value == NULL ))
    {
        PyErr_Format( PyExc_TypeError, "function's dictionary may not be deleted");
        return -1;
    }

    if (likely( PyDict_Check( value ) ))
    {
        PyObject *old = object->m_dict;
        object->m_dict = INCREASE_REFCOUNT( value );
        Py_XDECREF( old );

        return 0;
    }
    else
    {
        PyErr_SetString( PyExc_TypeError, "setting function's dictionary to a non-dict" );
        return -1;
    }
}

static PyObject *Nuitka_Function_get_code( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( (PyObject *)object->m_code_object );
}

static int Nuitka_Function_set_code( Nuitka_FunctionObject *object, PyObject *value )
{
    PyErr_Format( PyExc_RuntimeError, "__code__ is not writable in Nuitka" );
    return -1;
}

static PyObject *Nuitka_Function_get_defaults( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( (PyObject *)object->m_defaults );
}

static int Nuitka_Function_set_defaults( Nuitka_FunctionObject *object, PyObject *value )
{
    if ( value == NULL )
    {
        value = Py_None;
    }

    if (unlikely( value != Py_None && PyTuple_Check( value ) == false ))
    {
        PyErr_Format( PyExc_TypeError, "__defaults__ must be set to a tuple object" );
        return -1;
    }

    if ( object->m_defaults == Py_None && value != Py_None )
    {
        PyErr_Format( PyExc_TypeError, "Nuitka doesn't support __defaults__ size changes" );
        return -1;
    }

    if ( object->m_defaults != Py_None && ( value == Py_None || PyTuple_Size( object->m_defaults ) != PyTuple_Size( value ) ) )
    {
        PyErr_Format( PyExc_TypeError, "Nuitka doesn't support __defaults__ size changes" );
        return -1;
    }

    PyObject *old = object->m_defaults;
    object->m_defaults = INCREASE_REFCOUNT( value );
    Py_DECREF( old );

    return 0;
}

#if PYTHON_VERSION >= 300
static PyObject *Nuitka_Function_get_kwdefaults( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( (PyObject *)object->m_kwdefaults );
}

static int Nuitka_Function_set_kwdefaults( Nuitka_FunctionObject *object, PyObject *value )
{
    if ( value == NULL )
    {
        value = Py_None;
    }

    if (unlikely( value != Py_None && PyDict_Check( value ) == false ))
    {
        PyErr_Format( PyExc_TypeError, "__kwdefaults__ must be set to a dict object" );
        return -1;
    }

    PyObject *old = object->m_kwdefaults;
    object->m_kwdefaults = INCREASE_REFCOUNT( value );
    Py_DECREF( old );

    return 0;
}
static PyObject *Nuitka_Function_get_annotations( Nuitka_FunctionObject *object )
{
    if ( object->m_annotations == NULL )
    {
        object->m_annotations = PyDict_New();
    }

    return INCREASE_REFCOUNT( (PyObject *)object->m_annotations );
}

static int Nuitka_Function_set_annotations( Nuitka_FunctionObject *object, PyObject *value )
{
    // CPython silently converts None to empty dictionary.
    if ( value == Py_None || value == NULL )
    {
        value = PyDict_New();
    }

    if (unlikely( PyDict_Check( value ) == false ))
    {
        PyErr_Format( PyExc_TypeError, "__annotations__ must be set to a dict object" );
        return -1;
    }

    PyObject *old = object->m_annotations;
    object->m_annotations = INCREASE_REFCOUNT( value );
    Py_XDECREF( old );

    return 0;
}

#endif

static int Nuitka_Function_set_globals( Nuitka_FunctionObject *object, PyObject *value )
{
    PyErr_Format( PyExc_TypeError, "readonly attribute" );
    return -1;
}

static PyObject *Nuitka_Function_get_globals( Nuitka_FunctionObject *object )
{
    return INCREASE_REFCOUNT( PyModule_GetDict( object->m_module ) );
}

extern PyObject *_python_str_plain___module__;

static int Nuitka_Function_set_module( Nuitka_FunctionObject *object, PyObject *value )
{
    if ( object->m_dict == NULL )
    {
       object->m_dict = PyDict_New();
    }

    if ( value == NULL )
    {
        value = Py_None;
    }

    return PyDict_SetItem( object->m_dict, _python_str_plain___module__, value );
}

static PyObject *Nuitka_Function_get_module( Nuitka_FunctionObject *object )
{
    if ( object->m_dict )
    {
        PyObject *result = PyDict_GetItem( object->m_dict, _python_str_plain___module__ );

        if ( result != NULL )
        {
            return INCREASE_REFCOUNT( result );
        }
    }

    return MODULE_NAME( object->m_module );
}


static PyGetSetDef Nuitka_Function_getset[] =
{
#if PYTHON_VERSION >= 330
   { (char *)"__qualname__",    (getter)Nuitka_Function_get_qualname,    (setter)Nuitka_Function_set_qualname},
#endif
#if PYTHON_VERSION < 300
   { (char *)"func_name",       (getter)Nuitka_Function_get_name,        (setter)Nuitka_Function_set_name, NULL },
#endif
   { (char *)"__name__" ,       (getter)Nuitka_Function_get_name,        (setter)Nuitka_Function_set_name, NULL },
#if PYTHON_VERSION < 300
   { (char *)"func_doc",        (getter)Nuitka_Function_get_doc,         (setter)Nuitka_Function_set_doc, NULL },
#endif
   { (char *)"__doc__" ,        (getter)Nuitka_Function_get_doc,         (setter)Nuitka_Function_set_doc, NULL },
#if PYTHON_VERSION < 300
   { (char *)"func_dict",       (getter)Nuitka_Function_get_dict,        (setter)Nuitka_Function_set_dict, NULL },
#endif
   { (char *)"__dict__",        (getter)Nuitka_Function_get_dict,        (setter)Nuitka_Function_set_dict, NULL },
#if PYTHON_VERSION < 300
   { (char *)"func_code",       (getter)Nuitka_Function_get_code,        (setter)Nuitka_Function_set_code, NULL },
#endif
   { (char *)"__code__",        (getter)Nuitka_Function_get_code,        (setter)Nuitka_Function_set_code, NULL },
#if PYTHON_VERSION < 300
   { (char *)"func_defaults",   (getter)Nuitka_Function_get_defaults,    (setter)Nuitka_Function_set_defaults, NULL },
#endif
   { (char *)"__defaults__",    (getter)Nuitka_Function_get_defaults,    (setter)Nuitka_Function_set_defaults, NULL },
#if PYTHON_VERSION < 300
   { (char *)"func_globals",    (getter)Nuitka_Function_get_globals,     (setter)Nuitka_Function_set_globals, NULL },
#endif
   { (char *)"__globals__",     (getter)Nuitka_Function_get_globals,     (setter)Nuitka_Function_set_globals, NULL },
   { (char *)"__module__",      (getter)Nuitka_Function_get_module,      (setter)Nuitka_Function_set_module, NULL },
#if PYTHON_VERSION >= 300
   { (char *)"__kwdefaults__",  (getter)Nuitka_Function_get_kwdefaults,  (setter)Nuitka_Function_set_kwdefaults},
   { (char *)"__annotations__", (getter)Nuitka_Function_get_annotations, (setter)Nuitka_Function_set_annotations},

#endif
   { NULL }
};

static PyObject *Nuitka_Function_reduce( Nuitka_FunctionObject *function )
{
    return INCREASE_REFCOUNT( function->m_name );
}

static PyMethodDef Nuitka_Generator_methods[] =
{
    { "__reduce__", (PyCFunction)Nuitka_Function_reduce, METH_NOARGS, NULL },
    { NULL }
};


static void Nuitka_Function_tp_dealloc( Nuitka_FunctionObject *function )
{
    Nuitka_GC_UnTrack( function );

    if ( function->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)function );
    }

    Py_DECREF( function->m_name );
#if PYTHON_VERSION >= 330
    Py_DECREF( function->m_qualname );
#endif

    Py_XDECREF( function->m_dict );

    Py_DECREF( function->m_defaults );

#if PYTHON_VERSION >= 300
    Py_DECREF( function->m_kwdefaults );
    Py_XDECREF( function->m_annotations );
#endif

    if ( function->m_context )
    {
        function->m_cleanup( function->m_context );
    }

    PyObject_GC_Del( function );
}

static const long tp_flags =
    Py_TPFLAGS_DEFAULT       |
#if PYTHON_VERSION < 300
    Py_TPFLAGS_HAVE_WEAKREFS |
#endif
    Py_TPFLAGS_HAVE_GC;

PyTypeObject Nuitka_Function_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_function",                            // tp_name
    sizeof(Nuitka_FunctionObject),                  // tp_basicsize
    0,                                              // tp_itemsize
    (destructor)Nuitka_Function_tp_dealloc,         // tp_dealloc
    0,                                              // tp_print
    0,                                              // tp_getattr
    0,                                              // tp_setattr
#if PYTHON_VERSION < 300
    (cmpfunc)Nuitka_Function_tp_compare,            // tp_compare
#else
    0,
#endif
    (reprfunc)Nuitka_Function_tp_repr,              // tp_repr
    0,                                              // tp_as_number
    0,                                              // tp_as_sequence
    0,                                              // tp_as_mapping
    (hashfunc)Nuitka_Function_tp_hash,              // tp_hash
    (ternaryfunc)Nuitka_Function_tp_call,           // tp_call
    0,                                              // tp_str
    PyObject_GenericGetAttr,                        // tp_getattro
    0,                                              // tp_setattro
    0,                                              // tp_as_buffer
    tp_flags,                                       // tp_flags
    0,                                              // tp_doc
    (traverseproc)Nuitka_Function_tp_traverse,      // tp_traverse
    0,                                              // tp_clear
    0,                                              // tp_richcompare
    offsetof( Nuitka_FunctionObject, m_weakrefs ),  // tp_weaklistoffset
    0,                                              // tp_iter
    0,                                              // tp_iternext
    Nuitka_Generator_methods,                       // tp_methods
    0,                                              // tp_members
    Nuitka_Function_getset,                         // tp_getset
    0,                                              // tp_base
    0,                                              // tp_dict
    Nuitka_Function_descr_get,                      // tp_descr_get
    0,                                              // tp_descr_set
    offsetof( Nuitka_FunctionObject, m_dict ),      // tp_dictoffset
    0,                                              // tp_init
    0,                                              // tp_alloc
    0,                                              // tp_new
    0,                                              // tp_free
    0,                                              // tp_is_gc
    0,                                              // tp_bases
    0,                                              // tp_mro
    0,                                              // tp_cache
    0,                                              // tp_subclasses
    0,                                              // tp_weaklist
    0,                                              // tp_del
};

#if PYTHON_VERSION < 300
static inline PyObject *make_kfunction( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, void *context, releaser cleanup )
#elif PYTHON_VERSION < 330
static inline PyObject *make_kfunction( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, void *context, releaser cleanup )
#else
static inline PyObject *make_kfunction( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, void *context, releaser cleanup )
#endif
{
    Nuitka_FunctionObject *result = PyObject_GC_New( Nuitka_FunctionObject, &Nuitka_Function_Type );

    if (unlikely( result == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create function %s", Nuitka_String_AsString( name ) );
        throw PythonException();
    }

    result->m_code = code;
    result->m_direct_arg_parser = dparse;

    result->m_name = INCREASE_REFCOUNT( name );

#if PYTHON_VERSION >= 330
    result->m_qualname = INCREASE_REFCOUNT( qualname ? qualname : name );
#endif

    result->m_context = context;
    result->m_cleanup = cleanup;

    assertObject( defaults );
    assert( defaults == Py_None || ( PyTuple_Check( defaults ) && PyTuple_Size( defaults ) > 0 ) );
    result->m_defaults = defaults;

#if PYTHON_VERSION >= 300
    assert( kwdefaults == Py_None || ( PyDict_Check( kwdefaults ) && PyDict_Size( kwdefaults ) > 0 ) );
    result->m_kwdefaults = kwdefaults;

    assert( annotations == NULL || PyDict_Check( annotations ) );
    result->m_annotations = annotations;
#endif

    result->m_code_object = code_object;

    result->m_module = module;
    result->m_doc    = doc;

    result->m_dict   = NULL;
    result->m_weakrefs = NULL;

    static long Nuitka_Function_counter = 0;
    result->m_counter = Nuitka_Function_counter++;

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}

// Make a function without context.
#if PYTHON_VERSION < 300
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc )
{
    return make_kfunction( fparse, dparse, name, code_object, defaults, module, doc, NULL, NULL );
}
#elif PYTHON_VERSION < 330
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc )
{
    return make_kfunction( fparse, dparse, name, code_object, defaults, kwdefaults, annotations, module, doc, NULL, NULL );
}
#else
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc )
{
    return make_kfunction( fparse, dparse, name, qualname, code_object, defaults, kwdefaults, annotations, module, doc, NULL, NULL );
}
#endif

// Make a function with context.
#if PYTHON_VERSION < 300
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, void *context, releaser cleanup )
{
    return make_kfunction( fparse, dparse, name, code_object, defaults, module, doc, context, cleanup );
}
#elif PYTHON_VERSION < 330
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, void *context, releaser cleanup )
{
    return make_kfunction( fparse, dparse, name, code_object, defaults, kwdefaults, annotations, module, doc, context, cleanup );
}
#else
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, void *context, releaser cleanup )
{
    return make_kfunction( fparse, dparse, name, qualname, code_object, defaults, kwdefaults, annotations, module, doc, context, cleanup );
}
#endif
