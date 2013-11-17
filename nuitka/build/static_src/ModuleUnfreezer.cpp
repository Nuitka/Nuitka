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
// This implements the loading of modules embedded. This is achieved mainly by
// registered a "sys.meta_path" loader, that gets asked for module names, and
// responds if it is an embedded one.

#include "nuitka/prelude.hpp"
#include "nuitka/unfreezing.hpp"

// For Python3.3, the loader is a module attribute, so we need tp make it
// accessible from this variable.
#if PYTHON_VERSION < 330
static
#endif
PyObject *loader_frozen_modules = NULL;

static Nuitka_FreezeTableEntry *frozen_modules = NULL;

static char *_kwlist[] = {
    (char *)"fullname",
    (char *)"unused", NULL
};

static PyObject *_path_unfreezer_find_module( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O|O:find_module",
        _kwlist,
        &module_name,
        &unused
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    char *name = Nuitka_String_AsString( module_name );

#if _DEBUG_UNFREEZER
    printf( "Looking for module '%s'...\n", name );
#endif

    struct Nuitka_FreezeTableEntry *current = frozen_modules;

    while ( current->name != NULL )
    {
       if ( strcmp( name, current->name ) == 0 )
       {
           return INCREASE_REFCOUNT( loader_frozen_modules );
       }

       current++;
    }

#if _DEBUG_UNFREEZER
    printf( "Didn't find module '%s'.\n", name );
#endif

    return INCREASE_REFCOUNT( Py_None );
}

static PyObject *_path_unfreezer_load_module( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *module_name;
    PyObject *unused;

    int res = PyArg_ParseTupleAndKeywords(
        args,
        kwds,
        "O|O:load_module",
        _kwlist,
        &module_name,
        &unused
    );

    if (unlikely( res == 0 ))
    {
        return NULL;
    }

    assert( module_name );
    assert( Nuitka_String_Check( module_name ) );

    char *name = Nuitka_String_AsString( module_name );

    struct Nuitka_FreezeTableEntry *current = frozen_modules;

    while ( current->name != NULL )
    {
       if ( strcmp( name, current->name ) == 0 )
       {
#if _DEBUG_UNFREEZER
           printf( "Loading %s\n", name );
#endif

           // Check prelude on why this is necessary.
           current->python_initfunc();

           if (unlikely( ERROR_OCCURED() ))
           {
               return NULL;
           }

           PyObject *sys_modules = PySys_GetObject( (char *)"modules" );

#if _DEBUG_UNFREEZER
           printf( "Loaded %s\n", name );
#endif

           return LOOKUP_SUBSCRIPT( sys_modules, module_name );
       }

       current++;
    }

    assert( false );

    return INCREASE_REFCOUNT( Py_None );
}


static PyMethodDef _method_def_loader_find_module =
{
    "find_module",
    (PyCFunction)_path_unfreezer_find_module,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_loader_load_module =
{
    "load_module",
    (PyCFunction)_path_unfreezer_load_module,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

void registerMetaPathBasedUnfreezer( struct Nuitka_FreezeTableEntry *_frozen_modules )
{
    // Do it only once.
    if ( frozen_modules )
    {
        assert( _frozen_modules == frozen_modules );

        return;
    }

    frozen_modules = _frozen_modules;

    // Build the dictionary of the "loader" object, which needs to have two
    // methods "find_module" where we acknowledge that we are capable of loading
    // the module, and "load_module" that does the actual thing.
    PyObject *method_dict = PyDict_New();
    assertObject( method_dict );

    PyObject *loader_find_module = PyCFunction_New(
        &_method_def_loader_find_module,
        NULL
    );
    assertObject( loader_find_module );
    PyDict_SetItemString( method_dict, "find_module", loader_find_module );

    PyObject *loader_load_module = PyCFunction_New(
        &_method_def_loader_load_module,
        NULL
    );
    assertObject( loader_load_module );
    PyDict_SetItemString( method_dict, "load_module", loader_load_module );

    // Build the actual class.
    loader_frozen_modules = PyObject_CallFunctionObjArgs(
        (PyObject *)&PyType_Type,
#if PYTHON_VERSION < 300
        PyString_FromString( "_nuitka_compiled_modules_loader" ),
#else
        PyUnicode_FromString( "_nuitka_compiled_modules_loader" ),
#endif
        const_tuple_empty,
        method_dict,
        NULL
    );

    assertObject( loader_frozen_modules );

    // And also provide it as a meta path loader.
    int res = PyList_Insert( PySys_GetObject( ( char *)"meta_path" ), 0, loader_frozen_modules );
    assert( res == 0 );
}
