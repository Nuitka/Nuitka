//     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

#if PYTHON_VERSION >= 350
static PyObject *old_getcoroutinestate = NULL;

static PyObject *_inspect_getcoroutinestate_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:getcoroutinestate", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Coroutine_Check( object ) )
    {
        Nuitka_CoroutineObject *coroutine = (Nuitka_CoroutineObject *)object;

        if ( coroutine->m_running )
        {
            return PyObject_GetAttrString( module_inspect, "CORO_RUNNING" );
        }
        else if ( coroutine->m_status == status_Finished )
        {
            return PyObject_GetAttrString( module_inspect, "CORO_CLOSED" );
        }
        else if ( coroutine->m_status == status_Unused )
        {
            return PyObject_GetAttrString( module_inspect, "CORO_CREATED" );
        }
        else
        {
           return PyObject_GetAttrString( module_inspect, "CORO_SUSPENDED" );
        }
    }
    else
    {
        return old_getcoroutinestate->ob_type->tp_call( old_getcoroutinestate, args, kwds );
    }
}
#endif

#endif

#if PYTHON_VERSION >= 300
static PyMethodDef _method_def_inspect_getgeneratorstate_replacement =
{
    "getgeneratorstate",
    (PyCFunction)_inspect_getgeneratorstate_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

#if PYTHON_VERSION >= 350
static PyMethodDef _method_def_inspect_getcoroutinestate_replacement =
{
    "getcoroutinestate",
    (PyCFunction)_inspect_getcoroutinestate_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};
#endif

// Replace inspect functions with ones that accept compiled types too.
static void patchInspectModule( void )
{
#if PYTHON_VERSION >= 300
#ifdef _NUITKA_EXE
    // May need to import the "site" module, because otherwise the patching can
    // fail with it being unable to load it.
    if ( Py_NoSiteFlag == 0 )
    {
        PyObject *site_module = IMPORT_MODULE( const_str_plain_site, Py_None, Py_None, const_tuple_empty, const_int_0 );

        if ( site_module == NULL )
        {
            // Ignore ImportError, site is not a must.
            CLEAR_ERROR_OCCURRED();
        }
    }
#endif

    module_inspect = IMPORT_MODULE( const_str_plain_inspect, Py_None, Py_None, const_tuple_empty, const_int_0 );

    if ( module_inspect == NULL )
    {
        PyErr_PrintEx( 0 );
        Py_Exit( 1 );
    }
    CHECK_OBJECT( module_inspect );

    // Patch "inspect.getgeneratorstate" unless it is already patched.
    old_getgeneratorstate = PyObject_GetAttrString( module_inspect, "getgeneratorstate" );
    CHECK_OBJECT( old_getgeneratorstate );

    if ( PyFunction_Check( old_getgeneratorstate ) )
    {
        PyObject *inspect_getgeneratorstate_replacement = PyCFunction_New( &_method_def_inspect_getgeneratorstate_replacement, NULL );
        CHECK_OBJECT( inspect_getgeneratorstate_replacement );

        PyObject_SetAttrString( module_inspect, "getgeneratorstate", inspect_getgeneratorstate_replacement );
    }

#if PYTHON_VERSION >= 350
    // Patch "inspect.getcoroutinestate" unless it is already patched.
    old_getcoroutinestate = PyObject_GetAttrString( module_inspect, "getcoroutinestate" );
    CHECK_OBJECT( old_getcoroutinestate );

    if ( PyFunction_Check( old_getcoroutinestate ) )
    {
        PyObject *inspect_getcoroutinestate_replacement = PyCFunction_New( &_method_def_inspect_getcoroutinestate_replacement, NULL );
        CHECK_OBJECT( inspect_getcoroutinestate_replacement );

        PyObject_SetAttrString( module_inspect, "getcoroutinestate", inspect_getcoroutinestate_replacement );
    }
#endif

#endif

}
#endif

extern int Nuitka_IsInstance( PyObject *inst, PyObject *cls );
extern PyObject *original_isinstance;

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

extern PyModuleObject *builtin_module;

void patchBuiltinModule()
{
#if defined(_NUITKA_MODULE)
    static bool init_done = false;

    if (init_done == true) return;
    init_done = true;
#endif
    CHECK_OBJECT( (PyObject *)builtin_module );

    // Patch "inspect.isinstance" unless it is already patched.
    original_isinstance = PyObject_GetAttrString( (PyObject *)builtin_module, "isinstance" );
    CHECK_OBJECT( original_isinstance );

    // TODO: Find safe criterion, there was a C method before
    PyObject *builtin_isinstance_replacement = PyCFunction_New( &_method_def_builtin_isinstance_replacement, NULL );
    CHECK_OBJECT( builtin_isinstance_replacement );

    PyObject_SetAttrString( (PyObject *)builtin_module, "isinstance", builtin_isinstance_replacement );

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

    CHECK_OBJECT( a );
    CHECK_OBJECT( b );

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
