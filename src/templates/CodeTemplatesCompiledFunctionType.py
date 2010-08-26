# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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

kfunction_type_code = """


PyTypeObject PyKFunction_Type;

// The PyKFunctionObject must have identical layout to PyCFunctionTypeObject.
// TODO: Get rid of that.
typedef struct {
    PyObject_HEAD

    PyMethodDef *m_ml;
    PyObject *m_self;

    PyObject *m_module;

    PyObject *m_doc;
    PyObject *m_dict;

    PyObject *m_weakrefs;

    long m_counter;
} PyKFunctionObject;

// *** KFunction type begin

// tp_descr_get slot, bind a function to an object.
static PyObject *PyKFunction_descr_get( PyObject *function, PyObject *object, PyObject *klass )
{
    return PyMethod_New( function, object == Py_None ? NULL : object, klass );
}

 // tp_repr slot, decide how a function shall be output
static PyObject *PyKFunction_repr( PyKFunctionObject *object )
{
    return PyString_FromFormat( "<compiled function %s at %p>", object->m_ml->ml_name, object->m_self );
}

static PyObject *PyKFunction_tp_call( PyObject *function, PyObject *arg, PyObject *kw)
{
    PyCFunctionWithKeywords code = (PyCFunctionWithKeywords)PyCFunction_GET_FUNCTION( function );
    return code( PyCFunction_GET_SELF( function ), arg, kw );
}

static long PyKFunction_tp_traverse( PyObject *function, visitproc visit, void *arg )
{
    // TODO: Identify the impact of not visiting owned objects and/or if it could be NULL
    // instead. The methodobject visits its self and module. I understand this is probably
    // so that back references of this function to its upper do not make it stay in the
    // memory. A specific test if that works might be needed.
    return 0;
}

static int PyKFunction_tp_compare( PyKFunctionObject *a, PyKFunctionObject *b)
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

static long PyKFunction_tp_hash( PyKFunctionObject *function )
{
    return function->m_counter;
}

static PyObject *PyKFunction_get_name( PyKFunctionObject *object )
{
    return INCREASE_REFCOUNT( PyString_FromString( object->m_ml->ml_name ) );
}

static int PyKFunction_set_name( PyKFunctionObject *object, PyObject *value )
{
    if (value == NULL || PyString_Check( value ) == 0)
    {
       PyErr_Format( PyExc_TypeError, "__name__ must be set to a string object" );
       return -1;
    }

    // TODO: Leaking memory here, because it's hard to tell if free() should be done
    object->m_ml->ml_name = strdup( PyString_AsString( value ) );

    return 0;
}

static PyObject *PyKFunction_get_doc( PyKFunctionObject *object )
{
    return INCREASE_REFCOUNT( object->m_doc );
}

static int PyKFunction_set_doc( PyKFunctionObject *object, PyObject *value )
{
    if ( value == Py_None || value == NULL )
    {
       object->m_doc = Py_None;
    }
    else if ( PyString_Check( value ) == 0 )
    {
       PyErr_Format( PyExc_TypeError, "__name__ must be set to a string object" );
       return -1;
    }
    else
    {
       object->m_doc = INCREASE_REFCOUNT( value );
    }

    return 0;
}

static PyObject *PyKFunction_get_dict( PyKFunctionObject *object )
{
   if ( object->m_dict == NULL )
   {
      object->m_dict = PyDict_New();
   }

   return INCREASE_REFCOUNT( object->m_dict );
}

static int PyKFunction_set_dict( PyKFunctionObject *object, PyObject *value )
{
    if (value == NULL)
    {
        PyErr_Format( PyExc_TypeError, "function's dictionary may not be deleted");
        return -1;
    }

    if ( PyDict_Check(value) )
    {
        PyObject *old = object->m_dict;

        object->m_dict = INCREASE_REFCOUNT( value );
        Py_DECREF( object->m_dict );
    }
    else
    {
        PyErr_SetString( PyExc_TypeError, "setting function's dictionary to a non-dict" );
        return -1;
    }
}

static int PyKFunction_set_globals( PyKFunctionObject *object, PyObject *value )
{
    PyErr_Format( PyExc_TypeError, "readonly attribute" );
    return -1;
}

static PyObject *PyKFunction_get_globals( PyKFunctionObject *object )
{
    return INCREASE_REFCOUNT( PyModule_GetDict( object->m_module ) );
}

static int PyKFunction_set_module( PyKFunctionObject *object, PyObject *value )
{
    if ( object->m_dict == NULL )
    {
       object->m_dict = PyDict_New();
    }

    return PyDict_SetItemString( object->m_dict, (char * )"__module__", value );
}

static PyObject *PyKFunction_get_module( PyKFunctionObject *object )
{
    if ( object->m_dict )
    {
        PyObject *result = PyDict_GetItemString( object->m_dict, (char * )"__module__" );

        if ( result != NULL )
        {
            return INCREASE_REFCOUNT( result );
        }
    }

    int res = PyKFunction_set_module( object, PyString_FromString( PyModule_GetName( object->m_module ) ) );

    assert( res == 0 );

    return PyDict_GetItemString( object->m_dict, (char * )"__module__" );
}


static PyGetSetDef PyKFunction_getset[] =
{
   { (char *)"func_name", (getter)PyKFunction_get_name, (setter)PyKFunction_set_name, NULL },
   { (char *)"__name__" , (getter)PyKFunction_get_name, (setter)PyKFunction_set_name, NULL },
   { (char *)"func_doc",  (getter)PyKFunction_get_doc, (setter)PyKFunction_set_doc, NULL },
   { (char *)"__doc__" ,  (getter)PyKFunction_get_doc, (setter)PyKFunction_set_doc, NULL },
   { (char *)"func_dict", (getter)PyKFunction_get_dict, (setter)PyKFunction_set_dict, NULL },
   { (char *)"__dict__",  (getter)PyKFunction_get_dict, (setter)PyKFunction_set_dict, NULL },
   { (char *)"func_globals", (getter)PyKFunction_get_globals, (setter)PyKFunction_set_globals, NULL },
   { (char *)"__globals__", (getter)PyKFunction_get_globals, (setter)PyKFunction_set_globals, NULL },
   { (char *)"__module__", (getter)PyKFunction_get_module,  (setter)PyKFunction_set_module, NULL },
   { NULL }
};

static PyObject *PyKFunction_New( PyMethodDef *ml, PyObject *self, PyObject *module, PyObject *doc )
{
    PyKFunctionObject *result = PyObject_GC_New( PyKFunctionObject, &PyKFunction_Type );

    // Pointer to a static structure, no need to duplicate it.
    result->m_ml = ml;

    Py_INCREF( self );
    result->m_self = self;

    // printf( "creating %s\\n", result->m_ml->ml_name );
    result->m_module = module;
    result->m_doc    = doc;
    result->m_dict   = NULL;

    result->m_weakrefs = NULL;

    static long PyKFunction_counter = 0;
    result->m_counter = PyKFunction_counter++;

    _PyObject_GC_TRACK( result );
    return (PyObject *)result;
}

static void PyKFunction_tp_dealloc( PyKFunctionObject *function )
{
    _PyObject_GC_UNTRACK( function );

    if ( function->m_weakrefs != NULL )
    {
        PyObject_ClearWeakRefs( (PyObject *)function );
    }

    Py_DECREF( function->m_self );
    Py_XDECREF( function->m_dict );

    PyObject_GC_Del( function );
}


static void initKFunctionType()
{
    PyKFunction_Type = PyCFunction_Type;

    PyKFunction_Type.tp_name      = "compiled_function_or_method";
    PyKFunction_Type.tp_basicsize = sizeof(PyKFunctionObject);
    PyKFunction_Type.tp_itemsize  = 0;

    PyKFunction_Type.tp_print = NULL;
    PyKFunction_Type.tp_getattr = NULL;
    PyKFunction_Type.tp_setattr = NULL;
    PyKFunction_Type.tp_getattro = PyObject_GenericGetAttr;
    PyKFunction_Type.tp_setattro = NULL;

    PyKFunction_Type.tp_compare = (cmpfunc)PyKFunction_tp_compare;
    PyKFunction_Type.tp_hash = (hashfunc)PyKFunction_tp_hash;

    PyKFunction_Type.tp_as_number = NULL;
    PyKFunction_Type.tp_as_sequence = NULL;
    PyKFunction_Type.tp_as_mapping = NULL;
    PyKFunction_Type.tp_as_buffer = NULL;

    PyKFunction_Type.tp_str       = NULL;
    PyKFunction_Type.tp_doc       = NULL;
    PyKFunction_Type.tp_clear     = NULL;

    PyKFunction_Type.tp_dealloc   = (destructor)PyKFunction_tp_dealloc;
    PyKFunction_Type.tp_repr      = (reprfunc)PyKFunction_repr;
    PyKFunction_Type.tp_descr_get = PyKFunction_descr_get;
    PyKFunction_Type.tp_call      = PyKFunction_tp_call;

    PyKFunction_Type.tp_traverse  = (traverseproc)PyKFunction_tp_traverse;

    // Support weakrefs.
    PyKFunction_Type.tp_weaklistoffset = offsetof(PyKFunctionObject, m_weakrefs);

    PyKFunction_Type.tp_getset    = PyKFunction_getset;
    PyKFunction_Type.tp_members   = NULL;

    PyKFunction_Type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC;

    PyKFunction_Type.tp_dict = 0;
    PyKFunction_Type.tp_dictoffset = offsetof( PyKFunctionObject, m_dict );

    PyType_Ready( &PyKFunction_Type );
}

// *** KFunction type end

"""
