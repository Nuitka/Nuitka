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

static PyObject *loader_frozen_modules = NULL;

static struct _inittab *frozes_modules = NULL;

static char *_kwlist[] = { (char *)"fullname", (char *)"unused", NULL };

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

    struct _inittab *current = frozes_modules;

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
    assert( PyString_Check( module_name ) );

    char *name = Nuitka_String_AsString( module_name );

    struct _inittab *current = frozes_modules;

    while ( current->name != NULL )
    {
       if ( strcmp( name, current->name ) == 0 )
       {
#if _DEBUG_UNFREEZER
           printf( "Loading %s\n", name );
#endif
           current->initfunc();

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


static PyMethodDef _method_def_loader_find_module
{
    "find_module",
    (PyCFunction)_path_unfreezer_find_module,
    METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_loader_load_module
{
    "load_module",
    (PyCFunction)_path_unfreezer_load_module,
    METH_KEYWORDS,
    NULL
};

void registerMetaPathBasedUnfreezer( struct _inittab *_frozes_modules )
{
    frozes_modules = _frozes_modules;

    PyObject *method_dict = PyDict_New();

    assertObject( method_dict );

    PyObject *loader_find_module = PyCFunction_New( &_method_def_loader_find_module, NULL );
    assertObject( loader_find_module );
    PyDict_SetItemString( method_dict, "find_module", loader_find_module );

    PyObject *loader_load_module = PyCFunction_New( &_method_def_loader_load_module, NULL );
    assertObject( loader_load_module );
    PyDict_SetItemString( method_dict, "load_module", loader_load_module );

    loader_frozen_modules = PyObject_CallFunctionObjArgs(
        (PyObject *)&PyType_Type,
#if PYTHON_VERSION < 300
        PyString_FromString( "_nuitka_compiled_modules_loader" ),
#else
        PyUnicode_FromString( "_nuitka_compiled_modules_loader" ),
#endif
        _python_tuple_empty,
        method_dict,
        NULL
    );

    assertObject( loader_frozen_modules );

    int res = PyList_Insert( PySys_GetObject( ( char *)"meta_path" ), 0, loader_frozen_modules );

    assert( res == 0 );
}
