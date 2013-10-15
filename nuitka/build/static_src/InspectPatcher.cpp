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

extern PyObject *_python_str_plain_inspect;
extern PyObject *_python_str_plain_site;
extern PyObject *_python_int_0;

static PyObject *module_inspect;

static char *kwlist[] = { (char *)"object", NULL };

static PyObject *_inspect_isfunction_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:isfunction", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Function_Check( object ) || PyFunction_Check( object ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_False );
    }
}

static PyObject *_inspect_ismethod_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:ismethod", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Method_Check( object ) )
    {
#if PYTHON_VERSION < 300
        return INCREASE_REFCOUNT( Py_True );
#else
        return INCREASE_REFCOUNT( ((Nuitka_MethodObject *)object)->m_object ? Py_True : Py_False );
#endif
    }
    else if ( PyMethod_Check( object ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_False );
    }
}

static PyObject *_inspect_isgenerator_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:isgenerator", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Generator_Check( object ) || PyGen_Check( object ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_False );
    }
}

static PyObject *_inspect_isframe_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:isframe", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Frame_Check( object ) || PyFrame_Check( object ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }
    else
    {
        return INCREASE_REFCOUNT( Py_False );
    }
}

#if PYTHON_VERSION >= 300
static PyObject *old_getgeneratorstate = NULL;

static PyObject *_inspect_getgeneratorstate_replacement( PyObject *self, PyObject *args, PyObject *kwds )
{
    PyObject *object;

    if ( !PyArg_ParseTupleAndKeywords( args, kwds, "O:getgeneratorstate", kwlist, &object, NULL ))
    {
        return NULL;
    }

    if ( Nuitka_Generator_Check( object ))
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

static PyMethodDef _method_def_inspect_isfunction_replacement =
{
    "isfunction",
    (PyCFunction)_inspect_isfunction_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_inspect_ismethod_replacement =
{
    "ismethod",
    (PyCFunction)_inspect_ismethod_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_inspect_isgenerator_replacement =
{
    "isgenerator",
    (PyCFunction)_inspect_isgenerator_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_inspect_isframe_replacement =
{
    "isframe",
    (PyCFunction)_inspect_isframe_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

#if PYTHON_VERSION >= 300
static PyMethodDef _method_def_inspect_getgeneratorstate_replacement =
{
    "isframe",
    (PyCFunction)_inspect_getgeneratorstate_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};
#endif

void patchInspectModule( void )
{
#ifdef _NUITKA_EXE
    // May need to import the "site" module, because otherwise the patching can
    // fail with it being unable to load it.
    if ( Py_NoSiteFlag == 0 )
    {
        try
        {
            IMPORT_MODULE( _python_str_plain_site, Py_None, Py_None, _python_tuple_empty, _python_int_0 );
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
        module_inspect = IMPORT_MODULE( _python_str_plain_inspect, Py_None, Py_None, _python_tuple_empty, _python_int_0 );
    }
    catch( PythonException &e )
    {
        e.toPython();

        PyErr_PrintEx( 0 );
        Py_Exit( 1 );
    }
    assertObject( module_inspect );

    // Patch "inspect.isfunction" unless it is already patched.
    PyObject *old_isfunction = PyObject_GetAttrString( module_inspect, "isfunction" );
    assertObject( old_isfunction );

    if ( PyFunction_Check( old_isfunction ) )
    {
        PyObject *inspect_isfunction_replacement = PyCFunction_New( &_method_def_inspect_isfunction_replacement, NULL );
        assertObject( inspect_isfunction_replacement );

        PyObject_SetAttrString( module_inspect, "isfunction", inspect_isfunction_replacement );
    }

    Py_DECREF( old_isfunction );

    // Patch "inspect.ismethod" unless it is already patched.
    PyObject *old_ismethod = PyObject_GetAttrString( module_inspect, "ismethod" );
    assertObject( old_ismethod );

    if ( PyFunction_Check( old_ismethod ) )
    {
        PyObject *inspect_ismethod_replacement = PyCFunction_New( &_method_def_inspect_ismethod_replacement, NULL );
        assertObject( inspect_ismethod_replacement );

        PyObject_SetAttrString( module_inspect, "ismethod", inspect_ismethod_replacement );
    }

    Py_DECREF( old_ismethod );

    // Patch "inspect.isgenerator" unless it is already patched.
    PyObject *old_isgenerator = PyObject_GetAttrString( module_inspect, "isgenerator" );
    assertObject( old_isgenerator );

    if ( PyFunction_Check( old_isgenerator ) )
    {
        PyObject *inspect_isgenerator_replacement = PyCFunction_New( &_method_def_inspect_isgenerator_replacement, NULL );
        assertObject( inspect_isgenerator_replacement );

        PyObject_SetAttrString( module_inspect, "isgenerator", inspect_isgenerator_replacement );
    }

    Py_DECREF( old_isgenerator );

    // Patch "inspect.isframe" unless it is already patched.
    PyObject *old_isframe = PyObject_GetAttrString( module_inspect, "isframe" );
    assertObject( old_isframe );

    if ( PyFunction_Check( old_isframe ) )
    {
        PyObject *inspect_isframe_replacement = PyCFunction_New( &_method_def_inspect_isframe_replacement, NULL );
        assertObject( inspect_isframe_replacement );

        PyObject_SetAttrString( module_inspect, "isframe", inspect_isframe_replacement );
    }

    Py_DECREF( old_isframe );

#if PYTHON_VERSION >= 300
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

}
