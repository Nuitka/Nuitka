//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
extern PyObject *_python_int_0;

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

void patchInspectModule( void )
{
    PyObject *module_inspect = IMPORT_MODULE( _python_str_plain_inspect, Py_None, Py_None, _python_tuple_empty, _python_int_0 );
    assertObject( module_inspect );

    // Patch "inspect.isfunction" unless it is already patched.
    PyObject *old_isfunction = PyObject_GetAttrString( module_inspect, "isfunction" );
    assertObject( old_isfunction );

    if (PyFunction_Check( old_isfunction ))
    {
        PyObject *inspect_isfunction_replacement = PyCFunction_New( &_method_def_inspect_isfunction_replacement, NULL );
        assertObject( inspect_isfunction_replacement );

        PyObject_SetAttrString( module_inspect, "isfunction", inspect_isfunction_replacement );
    }

    Py_DECREF( old_isfunction );

    // Patch "inspect.ismethod" unless it is already patched.
    PyObject *old_ismethod = PyObject_GetAttrString( module_inspect, "ismethod" );
    assertObject( old_ismethod );

    if (PyFunction_Check( old_ismethod ))
    {
        PyObject *inspect_ismethod_replacement = PyCFunction_New( &_method_def_inspect_ismethod_replacement, NULL );
        assertObject( inspect_ismethod_replacement );

        PyObject_SetAttrString( module_inspect, "ismethod", inspect_ismethod_replacement );
    }

    Py_DECREF( old_ismethod );

    // Patch "inspect.isgenerator" unless it is already patched.
    PyObject *old_isgenerator = PyObject_GetAttrString( module_inspect, "isgenerator" );
    assertObject( old_isgenerator );

    if (PyFunction_Check( old_isgenerator ))
    {
        PyObject *inspect_isgenerator_replacement = PyCFunction_New( &_method_def_inspect_isgenerator_replacement, NULL );
        assertObject( inspect_isgenerator_replacement );

        PyObject_SetAttrString( module_inspect, "isgenerator", inspect_isgenerator_replacement );
    }

    Py_DECREF( old_isgenerator );
}
