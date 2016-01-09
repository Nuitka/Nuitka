//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
        "<compiled_function %s at %p>",
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
    CHECK_OBJECT( args );
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
            int( PyTuple_GET_SIZE( args ) )
        );
    }
}

static long Nuitka_Function_tp_traverse( Nuitka_FunctionObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting other owned objects. It appears
    // to be mostly harmless, as these are strings.
    Py_VISIT( function->m_dict );

    if ( function->m_closure )
    {
        for( Py_ssize_t i = 0; i < function->m_closure_given; i++ )
        {
            Py_VISIT( function->m_closure[i] );
        }
    }

    return 0;
}

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
    PyObject *old = object->m_doc;

    if ( value == NULL )
    {
        value = Py_None;
    }

    object->m_doc = value;
    Py_INCREF( value );

    Py_DECREF( old );

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

static PyObject *Nuitka_Function_get_closure( Nuitka_FunctionObject *object )
{
    if ( object->m_closure )
    {
        PyObject *result = PyTuple_New( object->m_closure_given );

        for( Py_ssize_t i = 0; i < object->m_closure_given; i++ )
        {
            PyTuple_SET_ITEM( result, i, (PyObject *)object->m_closure[i] );
            Py_INCREF( (PyObject *)object->m_closure[i] );
        }

        return result;
    }
    else
    {
        Py_INCREF( Py_None );
        return Py_None;
    }
}


static int Nuitka_Function_set_closure( Nuitka_FunctionObject *object, PyObject *value )
{
    PyErr_Format(
#if PYTHON_VERSION < 300
        PyExc_TypeError,
#else
        PyExc_AttributeError,
#endif
        "readonly attribute"
    );

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

extern PyObject *const_str_plain___module__;

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

    return PyDict_SetItem( object->m_dict, const_str_plain___module__, value );
}

static PyObject *Nuitka_Function_get_module( Nuitka_FunctionObject *object )
{
    if ( object->m_dict )
    {
        PyObject *result = PyDict_GetItem( object->m_dict, const_str_plain___module__ );

        if ( result != NULL )
        {
            return INCREASE_REFCOUNT( result );
        }
    }

    return INCREASE_REFCOUNT( MODULE_NAME( object->m_module ) );
}


static PyGetSetDef Nuitka_Function_getset[] =
{
#if PYTHON_VERSION >= 330
   { (char *)"__qualname__",    (getter)Nuitka_Function_get_qualname,    (setter)Nuitka_Function_set_qualname, NULL },
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
   { (char *)"__closure__",     (getter)Nuitka_Function_get_closure,     (setter)Nuitka_Function_set_closure, NULL },
#if PYTHON_VERSION < 300
   { (char *)"func_closure",    (getter)Nuitka_Function_get_closure,     (setter)Nuitka_Function_set_closure, NULL },
#endif
   { (char *)"__globals__",     (getter)Nuitka_Function_get_globals,     (setter)Nuitka_Function_set_globals, NULL },
   { (char *)"__module__",      (getter)Nuitka_Function_get_module,      (setter)Nuitka_Function_set_module, NULL },
#if PYTHON_VERSION >= 300
   { (char *)"__kwdefaults__",  (getter)Nuitka_Function_get_kwdefaults,  (setter)Nuitka_Function_set_kwdefaults, NULL },
   { (char *)"__annotations__", (getter)Nuitka_Function_get_annotations, (setter)Nuitka_Function_set_annotations, NULL },

#endif
   { NULL }
};

static PyObject *Nuitka_Function_reduce( Nuitka_FunctionObject *function )
{
#if PYTHON_VERSION < 330
    return INCREASE_REFCOUNT( function->m_name );
#else
    return INCREASE_REFCOUNT( function->m_qualname );
#endif
}

static PyMethodDef Nuitka_Function_methods[] =
{
    { "__reduce__", (PyCFunction)Nuitka_Function_reduce, METH_NOARGS, NULL },
    { NULL }
};


static void Nuitka_Function_tp_dealloc( Nuitka_FunctionObject *function )
{
#ifndef __NUITKA_NO_ASSERT__
    // Save the current exception, if any, we must to not corrupt it.
    PyObject *save_exception_type, *save_exception_value;
    PyTracebackObject *save_exception_tb;
    FETCH_ERROR_OCCURRED( &save_exception_type, &save_exception_value, &save_exception_tb );
    RESTORE_ERROR_OCCURRED( save_exception_type, save_exception_value, save_exception_tb );
#endif

    Nuitka_GC_UnTrack( function );

    if ( function->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)function );
    }

    Py_DECREF( function->m_name );
#if PYTHON_VERSION >= 330
    Py_DECREF( function->m_qualname );
#endif

    // These may actually re-surrect the object, not?
    Py_XDECREF( function->m_dict );
    Py_DECREF( function->m_defaults );

    Py_DECREF( function->m_doc );

#if PYTHON_VERSION >= 300
    Py_DECREF( function->m_kwdefaults );
    Py_DECREF( function->m_annotations );
#endif

    if ( function->m_closure )
    {
        for( Py_ssize_t i = 0; i < function->m_closure_given; i++ )
        {
            Py_DECREF( function->m_closure[i] );
        }

        free( function->m_closure );
    }

    PyObject_GC_Del( function );

#ifndef __NUITKA_NO_ASSERT__
    PyThreadState *tstate = PyThreadState_GET();

    assert( tstate->curexc_type == save_exception_type );
    assert( tstate->curexc_value == save_exception_value );
    assert( (PyTracebackObject *)tstate->curexc_traceback == save_exception_tb );
#endif
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
    0,                                              // tp_compare
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
    Nuitka_Function_methods,                        // tp_methods
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
static inline PyObject *make_compiled_function( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given )
#elif PYTHON_VERSION < 330
static inline PyObject *make_compiled_function( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given)
#else
static inline PyObject *make_compiled_function( function_arg_parser code, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given )
#endif
{
    Nuitka_FunctionObject *result = PyObject_GC_New( Nuitka_FunctionObject, &Nuitka_Function_Type );

    assert( result );

    result->m_code = code;
    result->m_direct_arg_parser = dparse;

    result->m_name = INCREASE_REFCOUNT( name );

#if PYTHON_VERSION >= 330
    result->m_qualname = INCREASE_REFCOUNT( qualname ? qualname : name );
#endif

    if ( defaults == NULL )
    {
        defaults = INCREASE_REFCOUNT( Py_None );
    }
    CHECK_OBJECT( defaults );
    assert( defaults == Py_None || ( PyTuple_Check( defaults ) && PyTuple_Size( defaults ) > 0 ) );
    result->m_defaults = defaults;
    result->m_defaults_given = defaults == Py_None ? 0 : PyTuple_GET_SIZE( defaults );

#if PYTHON_VERSION >= 300
    if ( kwdefaults == NULL )
    {
        kwdefaults = INCREASE_REFCOUNT( Py_None );
    }
    assert( kwdefaults == Py_None || ( PyDict_Check( kwdefaults ) && DICT_SIZE( kwdefaults ) > 0 ) );
    result->m_kwdefaults = kwdefaults;

    assert( annotations == Py_None || PyDict_Check( annotations ) );
    result->m_annotations = INCREASE_REFCOUNT( annotations );
#endif

    result->m_code_object = code_object;

    result->m_module = module;
    result->m_doc    = INCREASE_REFCOUNT( doc );

    result->m_dict   = NULL;
    result->m_weakrefs = NULL;

    static long Nuitka_Function_counter = 0;
    result->m_counter = Nuitka_Function_counter++;

    result->m_closure = closure;
    result->m_closure_given = closure_given;

    Nuitka_GC_Track( result );
    return (PyObject *)result;
}

// Make a function without closure.
#if PYTHON_VERSION < 300
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc )
{
    return make_compiled_function( fparse, dparse, name, code_object, defaults, module, doc, NULL, 0 );
}
#elif PYTHON_VERSION < 330
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc )
{
    return make_compiled_function( fparse, dparse, name, code_object, defaults, kwdefaults, annotations, module, doc, NULL, 0 );
}
#else
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc )
{
    return make_compiled_function( fparse, dparse, name, qualname, code_object, defaults, kwdefaults, annotations, module, doc, NULL, 0 );
}
#endif

// Make a function with closure.
#if PYTHON_VERSION < 300
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given )
{
    return make_compiled_function( fparse, dparse, name, code_object, defaults, module, doc, closure, closure_given );
}
#elif PYTHON_VERSION < 330
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given )
{
    return make_compiled_function( fparse, dparse, name, code_object, defaults, kwdefaults, annotations, module, doc, closure, closure_given );
}
#else
PyObject *Nuitka_Function_New( function_arg_parser fparse, direct_arg_parser dparse, PyObject *name, PyObject *qualname, PyCodeObject *code_object, PyObject *defaults, PyObject *kwdefaults, PyObject *annotations, PyObject *module, PyObject *doc, PyCellObject **closure, Py_ssize_t closure_given )
{
    return make_compiled_function( fparse, dparse, name, qualname, code_object, defaults, kwdefaults, annotations, module, doc, closure, closure_given );
}
#endif

static void ERROR_NO_ARGUMENTS_ALLOWED( Nuitka_FunctionObject const *function,
#if PYTHON_VERSION >= 330
                                        PyObject *kw,
#endif
                                        Py_ssize_t given )
{
    char const *function_name =
       Nuitka_String_AsString( function->m_name );

#if PYTHON_VERSION < 330
    PyErr_Format(
        PyExc_TypeError,
        "%s() takes no arguments (%zd given)",
        function_name,
        given );
#else
    if ( kw == NULL )
    {
        PyErr_Format(
            PyExc_TypeError,
            "%s() takes 0 positional arguments but %zd was given",
            function_name,
            given
         );
    }
    else
    {
       PyObject *tmp_iter = PyObject_GetIter( kw );
       PyObject *tmp_arg_name = PyIter_Next( tmp_iter );
       Py_DECREF( tmp_iter );

       PyErr_Format( PyExc_TypeError,
           "%s() got an unexpected keyword argument '%s'",
           function_name,
           Nuitka_String_AsString( tmp_arg_name )
       );

       Py_DECREF( tmp_arg_name );
    }
#endif
}

static void ERROR_MULTIPLE_VALUES( Nuitka_FunctionObject const *function, Py_ssize_t index )
{
    char const *function_name =
       Nuitka_String_AsString( function->m_name );

    PyErr_Format(
        PyExc_TypeError,
#if PYTHON_VERSION < 330
        "%s() got multiple values for keyword argument '%s'",
#else
        "%s() got multiple values for argument '%s'",
#endif
        function_name,
        Nuitka_String_AsString(
            PyTuple_GET_ITEM(
                function->m_code_object->co_varnames,
                index
            )
        )
    );
}

static void ERROR_TOO_FEW_ARGUMENTS( Nuitka_FunctionObject const *function,
#if PYTHON_VERSION < 270
                              Py_ssize_t kw_size,
#endif
                              Py_ssize_t given )
{
    Py_ssize_t required_parameter_count =
        function->m_code_object->co_argcount;

    if ( function->m_defaults != Py_None )
    {
        required_parameter_count -= PyTuple_GET_SIZE( function->m_defaults );
    }

    char const *function_name =
       Nuitka_String_AsString( function->m_name );
    char const *violation =
        ( function->m_defaults != Py_None || function->m_code_object->co_flags & CO_VARARGS ) ? "at least" : "exactly";
    char const *plural =
       required_parameter_count == 1 ? "" : "s";

#if PYTHON_VERSION < 270
    if ( kw_size > 0 )
    {
        PyErr_Format(
            PyExc_TypeError,
            "%s() takes %s %zd non-keyword argument%s (%zd given)",
            function_name,
            violation,
            required_parameter_count,
            plural,
            given - function->m_defaults_given
        );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "%s() takes %s %zd argument%s (%zd given)",
            function_name,
            violation,
            required_parameter_count,
            plural,
            given
        );
    }
#else
    PyErr_Format(
        PyExc_TypeError,
        "%s() takes %s %zd argument%s (%zd given)",
        function_name,
        violation,
        required_parameter_count,
        plural,
        given
    );
#endif
}

static void ERROR_TOO_MANY_ARGUMENTS( Nuitka_FunctionObject const *function,
                                      Py_ssize_t given
#if PYTHON_VERSION < 270
                                    , Py_ssize_t kw_size

#endif
#if PYTHON_VERSION >= 330
                                    , Py_ssize_t kw_only
#endif
)
{
    Py_ssize_t top_level_parameter_count = function->m_code_object->co_argcount;

    char const *function_name =
       Nuitka_String_AsString( function->m_name );
#if PYTHON_VERSION < 330
    char const *violation =
       function->m_defaults != Py_None ? "at most" : "exactly";
#endif
    char const *plural =
       top_level_parameter_count == 1 ? "" : "s";

#if PYTHON_VERSION < 270
    PyErr_Format(
        PyExc_TypeError,
        "%s() takes %s %zd %sargument%s (%zd given)",
        function_name,
        violation,
        top_level_parameter_count,
        kw_size > 0 ? "non-keyword " : "",
        plural,
        given
    );
#elif PYTHON_VERSION < 300
    PyErr_Format(
        PyExc_TypeError,
        "%s() takes %s %zd argument%s (%zd given)",
        function_name,
        violation,
        top_level_parameter_count,
        plural,
        given
    );
#elif PYTHON_VERSION < 330
    PyErr_Format(
        PyExc_TypeError,
        "%s() takes %s %zd positional argument%s (%zd given)",
        function_name,
        violation,
        top_level_parameter_count,
        plural,
        given
    );
#else
    char keyword_only_part[100];

    if ( kw_only > 0 )
    {
        sprintf(
            keyword_only_part,
            " positional argument%s (and %" PY_FORMAT_SIZE_T "d keyword-only argument%s)",
            given != 1 ? "s" : "",
            kw_only,
            kw_only != 1 ? "s" : ""
        );
    }
    else
    {
        keyword_only_part[0] = 0;
    }

    if ( function->m_defaults_given == 0 )
    {
        PyErr_Format(
            PyExc_TypeError,
            "%s() takes %zd positional argument%s but %zd%s were given",
            function_name,
            top_level_parameter_count,
            plural,
            given,
            keyword_only_part
        );
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "%s() takes from %zd to %zd positional argument%s but %zd%s were given",
            function_name,
            top_level_parameter_count - function->m_defaults_given,
            top_level_parameter_count,
            plural,
            given,
            keyword_only_part
        );
    }
#endif
}

#if PYTHON_VERSION >= 330
static void ERROR_TOO_FEW_ARGUMENTS( Nuitka_FunctionObject const *function,
                                     PyObject **values )
{
    char const *function_name =
       Nuitka_String_AsString( function->m_name );

    PyCodeObject *code_object = function->m_code_object;

    Py_ssize_t max_missing = 0;

    for( Py_ssize_t i = code_object->co_argcount - 1 - function->m_defaults_given; i >= 0; --i )
    {
        if ( values[ i ] == NULL )
        {
            max_missing += 1;
        }
    }

    PyObject *list_str = PyUnicode_FromString( "" );

    PyObject *comma_str = PyUnicode_FromString( ", " );
    PyObject *and_str = PyUnicode_FromString(
        max_missing == 2 ? " and " : ", and "
    );

    Py_ssize_t missing = 0;
    for( Py_ssize_t i = code_object->co_argcount - 1 - function->m_defaults_given; i >= 0; --i )
    {
        if ( values[ i ] == NULL )
        {
            PyObject *current_str = PyTuple_GET_ITEM(
                code_object->co_varnames,
                i
            );

            PyObject *current = PyObject_Repr( current_str );

            if ( missing == 0 )
            {
                PyObject *old = list_str;

                list_str = PyUnicode_Concat(
                    list_str,
                    current
                );

                Py_DECREF( old );
            }
            else if ( missing == 1 )
            {
                PyObject *old = list_str;

                list_str = PyUnicode_Concat(
                    and_str,
                    list_str
                );

                Py_DECREF( old );
                old = list_str;

                list_str = PyUnicode_Concat(
                    current,
                    list_str
                );

                Py_DECREF( old );
            }
            else
            {
                PyObject *old = list_str;

                list_str = PyUnicode_Concat(
                    comma_str,
                    list_str
                );

                Py_DECREF( old );
                old = list_str;

                list_str = PyUnicode_Concat(
                    current,
                    list_str
                );

                Py_DECREF( old );
            }

            Py_DECREF( current );

            missing += 1;
        }
    }

    Py_DECREF( comma_str );
    Py_DECREF( and_str );

    PyErr_Format(
        PyExc_TypeError,
        "%s() missing %zd required positional argument%s: %s",
        function_name,
        max_missing,
        max_missing > 1 ? "s" : "",
        Nuitka_String_AsString( list_str )
    );

    Py_DECREF( list_str );
}


static void ERROR_TOO_FEW_KWONLY( Nuitka_FunctionObject const *function,
                                  PyObject **kw_vars )
{
    char const *function_name = Nuitka_String_AsString( function->m_name );

    PyCodeObject *code_object = function->m_code_object;

    Py_ssize_t max_missing = 0;

    for( Py_ssize_t i = code_object->co_kwonlyargcount-1; i >= 0; --i )
    {
        if ( kw_vars[ i ] == NULL )
        {
            max_missing += 1;
        }
    }

    PyObject *list_str = PyUnicode_FromString( "" );

    PyObject *comma_str = PyUnicode_FromString( ", " );
    PyObject *and_str = PyUnicode_FromString(
        max_missing == 2 ? " and " : ", and "
    );

    Py_ssize_t missing = 0;
    for( Py_ssize_t i = code_object->co_kwonlyargcount-1; i >= 0; --i )
    {
        if ( kw_vars[ i ] == NULL )
        {
            PyObject *current_str = PyTuple_GET_ITEM(
                code_object->co_varnames,
                code_object->co_argcount + i
            );

            PyObject *current = PyObject_Repr( current_str );

            if ( missing == 0 )
            {
                PyObject *old = list_str;

                list_str = PyUnicode_Concat(
                    list_str,
                    current
                );

                Py_DECREF( old );
            }
            else if ( missing == 1 )
            {
                PyObject *old = list_str;

                list_str = PyUnicode_Concat(
                    and_str,
                    list_str
                );

                Py_DECREF( old );
                old = list_str;

                list_str = PyUnicode_Concat(
                    current,
                    list_str
                );

                Py_DECREF( old );
            }
            else
            {
                PyObject *old = list_str;

                list_str = PyUnicode_Concat(
                    comma_str,
                    list_str
                );

                Py_DECREF( old );
                old = list_str;

                list_str = PyUnicode_Concat(
                    current,
                    list_str
                );

                Py_DECREF( old );
            }

            Py_DECREF( current );

            missing += 1;
        }
    }

    Py_DECREF( comma_str );
    Py_DECREF( and_str );

    PyErr_Format(
        PyExc_TypeError,
        "%s() missing %zd required keyword-only argument%s: %s",
        function_name,
        max_missing,
        max_missing > 1 ? "s" : "",
        Nuitka_String_AsString( list_str )
    );

    Py_DECREF( list_str );
}
#endif


#if PYTHON_VERSION < 300
static Py_ssize_t _PARSE_ARGUMENTS_KW( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw )
#else
static Py_ssize_t _PARSE_ARGUMENTS_KW( Nuitka_FunctionObject const *function, PyObject **python_pars, Py_ssize_t *kw_only_found, PyObject *kw )
#endif
{
#if PYTHON_VERSION < 300
    Py_ssize_t arg_count = function->m_code_object->co_argcount;
#else
    Py_ssize_t arg_count = function->m_code_object->co_argcount + function->m_code_object->co_kwonlyargcount;
#endif

#if PYTHON_VERSION >= 300
    Py_ssize_t keyword_after_index = function->m_code_object->co_argcount;
#endif

    assert( ( function->m_code_object->co_flags & CO_VARKEYWORDS ) == 0 );

    Py_ssize_t kw_found = 0;
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while( PyDict_Next( kw, &ppos, &key, &value ) )
    {
#if PYTHON_VERSION < 300
        if (unlikely( !PyString_Check( key ) && !PyUnicode_Check( key ) ))
#else
        if (unlikely( !PyUnicode_Check( key ) ))
#endif
        {
            PyErr_Format(
                PyExc_TypeError,
                "%s() keywords must be strings",
                Nuitka_String_AsString( function->m_name )
            );
            return -1;
        }

        NUITKA_MAY_BE_UNUSED bool found = false;

        Py_INCREF( key );
        Py_INCREF( value );

        for( Py_ssize_t i = 0; i < arg_count; i++ )
        {
            if ( PyTuple_GET_ITEM( function->m_code_object->co_varnames, i ) == key )
            {
                assert( python_pars[ i ] == NULL );
                python_pars[ i ] = value;

#if PYTHON_VERSION >= 300
                if ( i >= keyword_after_index )
                {
                    *kw_only_found += 1;
                }
#endif

                found = true;
                break;
            }
        }

        if ( found == false )
        {
            for( Py_ssize_t i = 0; i < arg_count; i++ )
            {
                if ( RICH_COMPARE_BOOL_EQ_NORECURSE( PyTuple_GET_ITEM( function->m_code_object->co_varnames, i ), key ) )
                {
                    assert( python_pars[ i ] == NULL );
                    python_pars[ i ] = value;

#if PYTHON_VERSION >= 300
                    if ( i >= keyword_after_index )
                    {
                        *kw_only_found += 1;
                    }
#endif

                    found = true;
                    break;
                }
            }

        }

        if (unlikely( found == false ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "%s() got an unexpected keyword argument '%s'",
                Nuitka_String_AsString( function->m_name ),
                Nuitka_String_Check( key ) ? Nuitka_String_AsString( key ) : "<non-string>"
            );

            Py_DECREF( key );
            Py_DECREF( value );

            return -1;
        }

        Py_DECREF( key );

        kw_found += 1;
    }

    return kw_found;
}


static bool MAKE_STAR_DICT_DICTIONARY_COPY( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw )
{
    Py_ssize_t dict_star_index = function->m_code_object->co_argcount;
    assert( ( function->m_code_object->co_flags & CO_VARKEYWORDS ) != 0 );

#if PYTHON_VERSION >= 300
    dict_star_index += function->m_code_object->co_kwonlyargcount;
#endif

    if ( function->m_code_object->co_flags & CO_VARARGS )
    {
        dict_star_index += 1;
    }

    if ( kw == NULL )
    {
        python_pars[ dict_star_index ] = PyDict_New();
    }
    else if ( ((PyDictObject *)kw)->ma_used > 0 )
    {
#if PYTHON_VERSION < 330
        python_pars[ dict_star_index ] = _PyDict_NewPresized( ((PyDictObject *)kw)->ma_used );

        for ( int i = 0; i <= ((PyDictObject *)kw)->ma_mask; i++ )
        {
            PyDictEntry *entry = &((PyDictObject *)kw)->ma_table[ i ];

            if ( entry->me_value != NULL )
            {

#if PYTHON_VERSION < 300
                if (unlikely( !PyString_Check( entry->me_key ) && !PyUnicode_Check( entry->me_key ) ))
#else
                if (unlikely( !PyUnicode_Check( entry->me_key ) ))
#endif
                {
                    PyErr_Format(
                        PyExc_TypeError,
                        "%s() keywords must be strings",
                        Nuitka_String_AsString( function->m_name )
                    );

                    return false;
                }

                int res = PyDict_SetItem( python_pars[ dict_star_index ], entry->me_key, entry->me_value );

                if (unlikely( res != 0 ))
                {
                    return false;
                }
            }
        }
#else
        if ( _PyDict_HasSplitTable( (PyDictObject *)kw) )
        {
            PyDictObject *mp = (PyDictObject *)kw;

            PyObject **newvalues = PyMem_NEW( PyObject *, mp->ma_keys->dk_size );
            assert( newvalues != NULL );

            PyDictObject *split_copy = PyObject_GC_New( PyDictObject, &PyDict_Type );
            assert( split_copy != NULL );

            split_copy->ma_values = newvalues;
            split_copy->ma_keys = mp->ma_keys;
            split_copy->ma_used = mp->ma_used;

            mp->ma_keys->dk_refcnt += 1;

            Nuitka_GC_Track( split_copy );

            Py_ssize_t size = mp->ma_keys->dk_size;
            for ( Py_ssize_t i = 0; i < size; i++ )
            {
                PyDictKeyEntry *entry = &split_copy->ma_keys->dk_entries[ i ];

                if ( ( entry->me_key != NULL ) && unlikely( !PyUnicode_Check( entry->me_key ) ))
                {
                    PyErr_Format(
                        PyExc_TypeError,
                        "%s() keywords must be strings",
                        Nuitka_String_AsString( function->m_name )
                    );

                    return false;
                }

                split_copy->ma_values[ i ] = mp->ma_values[ i ];
                Py_XINCREF( split_copy->ma_values[ i ] );
            }

            python_pars[ dict_star_index ] = (PyObject *)split_copy;
        }
        else
        {
            python_pars[ dict_star_index ] = PyDict_New();

            PyDictObject *mp = (PyDictObject *)kw;

            Py_ssize_t size = mp->ma_keys->dk_size;
            for ( Py_ssize_t i = 0; i < size; i++ )
            {
                PyDictKeyEntry *entry = &mp->ma_keys->dk_entries[i];

                // TODO: One of these cases has been dealt with above.
                PyObject *value;
                if ( mp->ma_values )
                {
                    value = mp->ma_values[ i ];
                }
                else
                {
                    value = entry->me_value;
                }

                if ( value != NULL )
                {
                    if (unlikely( !PyUnicode_Check( entry->me_key ) ))
                    {
                        PyErr_Format(
                            PyExc_TypeError,
                            "%s() keywords must be strings",
                            Nuitka_String_AsString( function->m_name )
                        );

                        return false;
                    }

                    int res = PyDict_SetItem( python_pars[ dict_star_index ], entry->me_key, value );

                    if (unlikely( res != 0 ))
                    {
                        return false;
                    }
                }
            }
        }
#endif
    }
    else
    {
        python_pars[ dict_star_index ] = PyDict_New();
    }

    return true;
}


#if PYTHON_VERSION < 300
static Py_ssize_t _PARSE_ARGUMENTS_KW_STARDICT( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw )
#else
static Py_ssize_t _PARSE_ARGUMENTS_KW_STARDICT( Nuitka_FunctionObject const *function, PyObject **python_pars, Py_ssize_t *kw_only_found, PyObject *kw )
#endif
{
    assert( ( function->m_code_object->co_flags & CO_VARKEYWORDS ) != 0 );

    if (unlikely( MAKE_STAR_DICT_DICTIONARY_COPY( function, python_pars, kw ) == false ))
    {
        return -1;
    }

    Py_ssize_t kw_found = 0;
#if PYTHON_VERSION < 300
    Py_ssize_t arg_count = function->m_code_object->co_argcount;
#else
    Py_ssize_t arg_count = function->m_code_object->co_argcount + function->m_code_object->co_kwonlyargcount;
    Py_ssize_t keyword_after_index = function->m_code_object->co_argcount;
#endif

    Py_ssize_t dict_star_index = arg_count;

    if ( function->m_code_object->co_flags & CO_VARARGS )
    {
        dict_star_index += 1;
    }

    for( Py_ssize_t i = 0; i < arg_count; i++ )
    {
        PyObject *arg_name = PyTuple_GET_ITEM( function->m_code_object->co_varnames, i );

        PyObject *kw_arg_value = PyDict_GetItem(
            python_pars[ dict_star_index ],
            arg_name
        );

        if ( kw_arg_value != NULL )
        {
            assert( python_pars[ i ] == NULL );

            python_pars[ i ] = kw_arg_value;
            Py_INCREF( kw_arg_value );

            PyDict_DelItem( python_pars[ dict_star_index ], arg_name );

            kw_found += 1;

#if PYTHON_VERSION >= 300
            if ( i >= keyword_after_index )
            {
                *kw_only_found += 1;
            }
#endif
        }
    }

    return kw_found;
}

static void _MAKE_STAR_LIST_TUPLE_COPY( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject **args, Py_ssize_t args_size )
{
    assert( ( function->m_code_object->co_flags & CO_VARARGS ) != 0 );
    Py_ssize_t list_star_index = function->m_code_object->co_argcount;

#if PYTHON_VERSION >= 300
    list_star_index += function->m_code_object->co_kwonlyargcount;
#endif

    // Copy left-over argument values to the star list parameter given.
    if ( args_size > function->m_code_object->co_argcount )
    {
        python_pars[ list_star_index ] = PyTuple_New( args_size - function->m_code_object->co_argcount );

        for( Py_ssize_t i = 0; i < args_size - function->m_code_object->co_argcount; i++ )
        {
            PyObject *value = args[ function->m_code_object->co_argcount + i ];

            PyTuple_SET_ITEM( python_pars[ list_star_index ], i, value );
            Py_INCREF( value );
        }
    }
    else
    {
        python_pars[ list_star_index ] = const_tuple_empty;
        Py_INCREF( const_tuple_empty );
    }
}

// TODO: Use this.
#if  !defined(_NUITKA_FULL_COMPAT) || PYTHON_VERSION >= 330
#define NUITKA_BEST_ERROR_REPORTING 1
#endif



#if PYTHON_VERSION < 270
static bool _PARSE_ARGUMENTS_PLAIN( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw, PyObject **args, int args_size, Py_ssize_t kw_found, Py_ssize_t kw_size )
#elif PYTHON_VERSION < 300
static bool _PARSE_ARGUMENTS_PLAIN( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw, PyObject **args, int args_size, Py_ssize_t kw_found )
#else
static bool _PARSE_ARGUMENTS_PLAIN( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw, PyObject **args, int args_size, Py_ssize_t kw_found, Py_ssize_t kw_only_found )
#endif
{
    Py_ssize_t arg_count = function->m_code_object->co_argcount;

    // Check if too many arguments were given in case of non list star arg.
    // For Python3.3 it's done only later, when more knowledge has
    // been gained. TODO: Could be done this way for improved mode
    // on all versions.
#if PYTHON_VERSION < 330
    if ( ( function->m_code_object->co_flags & CO_VARARGS ) == 0 )
    {
        if (unlikely( args_size > arg_count ))
        {
#if PYTHON_VERSION < 270
            ERROR_TOO_MANY_ARGUMENTS( function, args_size, kw_size );
#else
            ERROR_TOO_MANY_ARGUMENTS( function, args_size + kw_found );
#endif
            return false;
        }
    }
#endif

#if PYTHON_VERSION >= 330
    bool parameter_error = false;
#endif

    if ( kw_found > 0 )
    {
        Py_ssize_t i;
        for( i = 0; i < (args_size < arg_count ? args_size : arg_count); i++ )
        {
            if (unlikely( python_pars[ i ] != NULL ))
            {
                ERROR_MULTIPLE_VALUES( function, i );
                return false;
            }

            python_pars[ i ] = args[ i ];
            Py_INCREF( python_pars[ i ] );
        }

        Py_ssize_t defaults_given = function->m_defaults_given;

        for( ; i < arg_count; i++ )
        {
            if ( python_pars[ i ] == NULL )
            {

                if ( i + defaults_given >= arg_count  )
                {
                    python_pars[ i ] = PyTuple_GET_ITEM( function->m_defaults, defaults_given + i - arg_count );
                    Py_INCREF( python_pars[ i ] );
                }
                else
                {
#if PYTHON_VERSION < 270
                    ERROR_TOO_FEW_ARGUMENTS( function, kw_size, args_size + kw_found );
                    return false;
#elif PYTHON_VERSION < 300
                    ERROR_TOO_FEW_ARGUMENTS( function, args_size + kw_found );
                    return false;
#elif PYTHON_VERSION < 330
                    ERROR_TOO_FEW_ARGUMENTS( function, args_size + kw_found - kw_only_found );
                    return false;
#else
                    parameter_error = true;
#endif
                }
            }
        }
    }
    else
    {
        Py_ssize_t usable = (args_size < arg_count ? args_size : arg_count);
        Py_ssize_t defaults_given = function->m_defaults_given;

        if ( defaults_given < arg_count - usable )
        {
#if PYTHON_VERSION < 270
            ERROR_TOO_FEW_ARGUMENTS( function, kw_size, args_size + kw_found );
            return false;
#elif PYTHON_VERSION < 300
            ERROR_TOO_FEW_ARGUMENTS( function, args_size + kw_found );
            return false;
#elif PYTHON_VERSION < 330
            ERROR_TOO_FEW_ARGUMENTS( function, args_size + kw_found - kw_only_found );
            return false;
#else
            parameter_error = true;
#endif
        }

        for( Py_ssize_t i = 0; i < usable; i++ )
        {
            assert( python_pars[ i ] == NULL );

            python_pars[ i ] = args[ i ];
            Py_INCREF( python_pars[ i ] );
        }

#if PYTHON_VERSION >= 330
        if ( parameter_error == false )
        {
#endif
            PyObject **source = &PyTuple_GET_ITEM( function->m_defaults, 0 );

            for( Py_ssize_t i = usable; i < arg_count; i++ )
            {
                assert( python_pars[ i ] == NULL );
                assert( i + defaults_given >= arg_count );

                python_pars[ i ] = source[ defaults_given + i - arg_count ];
                Py_INCREF( python_pars[ i ] );
            }
#if PYTHON_VERSION >= 330
        }
#endif
    }

#if PYTHON_VERSION >= 330
    if (unlikely( parameter_error ))
    {
        ERROR_TOO_FEW_ARGUMENTS( function, python_pars );
        return false;
    }

    if( ( function->m_code_object->co_flags & CO_VARARGS ) == 0 )
    {
        // Check if too many arguments were given in case of non list star arg
        if (unlikely( args_size > arg_count ))
        {
            ERROR_TOO_MANY_ARGUMENTS( function, args_size, kw_only_found );
            return false;
        }
    }
#endif

    if( ( function->m_code_object->co_flags & CO_VARARGS ) != 0 )
    {
        _MAKE_STAR_LIST_TUPLE_COPY( function, python_pars, args, args_size );
    }

    return true;
}


// Release them all in case of an error.
static void releaseParameters( Nuitka_FunctionObject const *function, PyObject **python_pars )
{
    Py_ssize_t arg_count = function->m_code_object->co_argcount;

#if PYTHON_VERSION >= 300
    arg_count += function->m_code_object->co_kwonlyargcount;
#endif

    if ( ( function->m_code_object->co_flags & CO_VARARGS ) != 0 )
    {
        arg_count += 1;
    }

    if ( ( function->m_code_object->co_flags & CO_VARKEYWORDS ) != 0 )
    {
        arg_count += 1;
    }

    for ( Py_ssize_t i = 0; i < arg_count; i++ )
    {
        Py_XDECREF( python_pars[ i ] );
    }
}


bool PARSE_ARGUMENTS( Nuitka_FunctionObject const *function, PyObject **python_pars, PyObject *kw, PyObject **args, Py_ssize_t args_size )
{
    Py_ssize_t kw_size = kw ? DICT_SIZE( kw ) : 0;
    Py_ssize_t kw_found;
    bool result;
#if PYTHON_VERSION >= 300
    Py_ssize_t kw_only_found;
#endif
#if PYTHON_VERSION >= 330
    bool kw_only_error;
#endif

#if PYTHON_VERSION < 300
    Py_ssize_t arg_count = function->m_code_object->co_argcount;
#else
    Py_ssize_t arg_count = function->m_code_object->co_argcount + function->m_code_object->co_kwonlyargcount;
#endif

    if (unlikely( arg_count == 0 && ( function->m_code_object->co_flags & (CO_VARARGS | CO_VARKEYWORDS ) ) == 0 && args_size + kw_size > 0 ))
    {
#if PYTHON_VERSION < 330
        ERROR_NO_ARGUMENTS_ALLOWED(
            function,
            args_size + kw_size
        );
#else
        ERROR_NO_ARGUMENTS_ALLOWED(
            function,
            kw_size > 0 ? kw : NULL,
            args_size
        );
#endif

        goto error_exit;
    }

#if PYTHON_VERSION >= 300
        kw_only_found = 0;
#endif
    if ( ( function->m_code_object->co_flags & CO_VARKEYWORDS ) != 0 )
    {
#if PYTHON_VERSION < 300
        kw_found = _PARSE_ARGUMENTS_KW_STARDICT( function, python_pars, kw );
#else
        kw_found = _PARSE_ARGUMENTS_KW_STARDICT( function, python_pars, &kw_only_found, kw );
#endif
        if ( kw_found == -1 ) goto error_exit;
    }
    else if ( kw == NULL || DICT_SIZE( kw ) == 0 )
    {
        kw_found = 0;
    }
    else
    {
#if PYTHON_VERSION < 300
        kw_found = _PARSE_ARGUMENTS_KW( function, python_pars, kw );
#else
        kw_found =  _PARSE_ARGUMENTS_KW( function, python_pars, &kw_only_found, kw );
#endif
        if ( kw_found == -1 ) goto error_exit;
    }

#if PYTHON_VERSION < 270
    result = _PARSE_ARGUMENTS_PLAIN( function, python_pars, kw, args, args_size, kw_found, kw_size );
#elif PYTHON_VERSION < 300
    result = _PARSE_ARGUMENTS_PLAIN( function, python_pars, kw, args, args_size, kw_found );
#else
    result = _PARSE_ARGUMENTS_PLAIN( function, python_pars, kw, args, args_size, kw_found, kw_only_found );
#endif

    if ( result == false ) goto error_exit;

#if PYTHON_VERSION >= 300

    // For Python3.3 the keyword only errors are all reported at once.
#if PYTHON_VERSION >= 330
    kw_only_error = false;
#endif

    for( Py_ssize_t i = function->m_code_object->co_argcount; i < function->m_code_object->co_argcount + function->m_code_object->co_kwonlyargcount; i++ )
    {
        if ( python_pars[ i ] == NULL )
        {
            PyObject *arg_name = PyTuple_GET_ITEM( function->m_code_object->co_varnames, i );

            python_pars[ i ] = PyDict_GetItem( function->m_kwdefaults, arg_name );

#if PYTHON_VERSION < 330
            if (unlikely( python_pars[ i ] == NULL ))
            {
                PyErr_Format(
                    PyExc_TypeError,
                    "%s() needs keyword-only argument %s",
                    Nuitka_String_AsString( function->m_name ),
                    Nuitka_String_AsString( arg_name )
                );

                goto error_exit;
            }

            Py_INCREF( python_pars[ i ] );
#else
            if ( python_pars[ i ] == NULL )
            {
                kw_only_error = true;
            }
            else
            {
                Py_INCREF( python_pars[ i ] );
            }
#endif
        }
    }

#if PYTHON_VERSION >= 330
    if (unlikely( kw_only_error ))
    {
        ERROR_TOO_FEW_KWONLY( function, &python_pars[ function->m_code_object->co_argcount ] );

        goto error_exit;
    }
#endif

#endif

    return true;

error_exit:

    releaseParameters( function, python_pars );
    return false;
}
