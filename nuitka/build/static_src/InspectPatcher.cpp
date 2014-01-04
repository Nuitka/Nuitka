//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
// This is responsible for updating parts of CPython to better work with Nuitka
// by replacing CPython implementations with enhanced versions.

#include "nuitka/prelude.hpp"


#if PYTHON_VERSION >= 300
extern PyObject *const_str_plain_inspect;
extern PyObject *const_str_plain_site;
extern PyObject *const_int_0;

static PyObject *module_inspect;

static char *kwlist[] = { (char *)"object", NULL };

static PyObject *old_getgeneratorstate = NULL;

static PyObject *_inspect_getgeneratorstate_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:getgeneratorstate", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Generator_Check( object ) )
    {
        Nuitka_GeneratorObject *generator = (Nuitka_GeneratorObject *)object;

        if ( generator->m_running )
        {
            return PyObject_GetAttrString( module_inspect, "GEN_RUNNING" );
        }
        else if ( generator->m_status == status_Finished )
        {
            return PyObject_GetAttrString( module_inspect, "GEN_CLOSED" );
        }
        else if ( generator->m_status == status_Unused )
        {
            return PyObject_GetAttrString( module_inspect, "GEN_CREATED" );
        }
        else
        {
           return PyObject_GetAttrString( module_inspect, "GEN_SUSPENDED" );
        }
    }
    else
    {
        return old_getgeneratorstate->ob_type->tp_call( old_getgeneratorstate, args, kwds );
    }
}
#endif

#if PYTHON_VERSION >= 300
static PyMethodDef _method_def_inspect_getgeneratorstate_replacement =
{
    "isframe",
    (PyCFunction)_inspect_getgeneratorstate_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

// Replace inspect functions with ones that accept compiled types too.
static void patchInspectModule( void )
{
#if PYTHON_VERSION >= 300
#ifdef _NUITKA_EXE
    // May need to import the "site" module, because otherwise the patching can
    // fail with it being unable to load it.
    if ( Py_NoSiteFlag == 0 )
    {
        try
        {
            IMPORT_MODULE( const_str_plain_site, Py_None, Py_None, const_tuple_empty, const_int_0 );
        }
        catch( PythonException & )
        {
            PyErr_Clear();
            // Ignore ImportError, site is not a must.
        }
    }
#endif

    try
    {
        module_inspect = IMPORT_MODULE( const_str_plain_inspect, Py_None, Py_None, const_tuple_empty, const_int_0 );
    }
    catch( PythonException &e )
    {
        e.toPython();

        PyErr_PrintEx( 0 );
        Py_Exit( 1 );
    }
    assertObject( module_inspect );

    // Patch "inspect.getgeneratorstate" unless it is already patched.
    old_getgeneratorstate = PyObject_GetAttrString( module_inspect, "getgeneratorstate" );
    assertObject( old_getgeneratorstate );

    if ( PyFunction_Check( old_getgeneratorstate ) )
    {
        PyObject *inspect_getgeneratorstate_replacement = PyCFunction_New( &_method_def_inspect_getgeneratorstate_replacement, NULL );
        assertObject( inspect_getgeneratorstate_replacement );

        PyObject_SetAttrString( module_inspect, "getgeneratorstate", inspect_getgeneratorstate_replacement );
    }
#endif

}
#endif

extern int Nuitka_IsInstance( PyObject *inst, PyObject *cls );

static PyObject *_builtin_isinstance_replacement( PyObject *self, PyObject *args )
{
    PyObject *inst, *cls;

    if (unlikely( PyArg_UnpackTuple(args, "isinstance", 2, 2, &inst, &cls) == 0 ))
    {
        return NULL;
    }

    int res = Nuitka_IsInstance( inst, cls );

    if (unlikely( res < 0 ))
    {
        return NULL;
    }

    return PyBool_FromLong( res );
}

static PyMethodDef _method_def_builtin_isinstance_replacement =
{
    "isinstance",
    (PyCFunction)_builtin_isinstance_replacement,
    METH_VARARGS,
    NULL
};

extern PyModuleObject *module_builtin;

void patchBuiltinModule()
{
    assertObject( (PyObject *)module_builtin );

    // Patch "inspect.isfunction" unless it is already patched.
    PyObject *old_isinstance = PyObject_GetAttrString( (PyObject *)module_builtin, "isinstance" );
    assertObject( old_isinstance );

    // TODO: Find safe criterion, these was a C method before
    if ( true || PyFunction_Check( old_isinstance ))
    {
        PyObject *builtin_isinstance_replacement = PyCFunction_New( &_method_def_builtin_isinstance_replacement, NULL );
        assertObject( builtin_isinstance_replacement );

        PyObject_SetAttrString( (PyObject *)module_builtin, "isinstance", builtin_isinstance_replacement );
    }

    Py_DECREF( old_isinstance );

#if PYTHON_VERSION >= 300
    patchInspectModule();
#endif
}

static richcmpfunc original_PyType_tp_richcompare = NULL;

static PyObject *Nuitka_type_tp_richcompare( PyObject *a, PyObject *b, int op )
{
    if (likely( op == Py_EQ || op == Py_NE ))
    {
        if ( a == (PyObject *)&Nuitka_Function_Type )
        {
            a = (PyObject *)&PyFunction_Type;
        }
        else if ( a == (PyObject *)&Nuitka_Method_Type )
        {
            a = (PyObject *)&PyMethod_Type;
        }
        else if ( a == (PyObject *)&Nuitka_Generator_Type )
        {
            a = (PyObject *)&PyGen_Type;
        }

        if ( b == (PyObject *)&Nuitka_Function_Type )
        {
            b = (PyObject *)&PyFunction_Type;
        }
        else if ( b == (PyObject *)&Nuitka_Method_Type )
        {
            b = (PyObject *)&PyMethod_Type;
        }
        else if ( b == (PyObject *)&Nuitka_Generator_Type )
        {
            b = (PyObject *)&PyGen_Type;
        }
    }

    assertObject( a );
    assertObject( b );

    assert( original_PyType_tp_richcompare );

    return original_PyType_tp_richcompare( a, b, op );
}

void patchTypeComparison()
{
    if ( original_PyType_tp_richcompare == NULL )
    {
        original_PyType_tp_richcompare = PyType_Type.tp_richcompare;
        PyType_Type.tp_richcompare = Nuitka_type_tp_richcompare;
    }
}
