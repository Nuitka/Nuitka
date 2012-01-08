//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit patches or make the software available to licensors of
//     this software in either form, you automatically them grant them a
//     license for your part of the code under "Apache License 2.0" unless you
//     choose to remove this notice.
//
//     Kay Hayen uses the right to license his code under only GPL version 3,
//     to discourage a fork of Nuitka before it is "finished". He will later
//     make a new "Nuitka" release fully under "Apache License 2.0".
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

static PyMethodDef _method_def_inspect_isfunction_replacement
{
    "isfunction",
    (PyCFunction)_inspect_isfunction_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_inspect_ismethod_replacement
{
    "ismethod",
    (PyCFunction)_inspect_ismethod_replacement,
    METH_VARARGS | METH_KEYWORDS,
    NULL
};

static PyMethodDef _method_def_inspect_isgenerator_replacement
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

    PyObject *inspect_isfunction_replacement = PyCFunction_New( &_method_def_inspect_isfunction_replacement, NULL );
    assertObject( inspect_isfunction_replacement );

    PyObject_SetAttrString( module_inspect, "isfunction", inspect_isfunction_replacement );

    PyObject *inspect_ismethod_replacement = PyCFunction_New( &_method_def_inspect_ismethod_replacement, NULL );
    assertObject( inspect_ismethod_replacement );

    PyObject_SetAttrString( module_inspect, "ismethod", inspect_ismethod_replacement );

    PyObject *inspect_isgenerator_replacement = PyCFunction_New( &_method_def_inspect_isgenerator_replacement, NULL );
    assertObject( inspect_isgenerator_replacement );

    PyObject_SetAttrString( module_inspect, "isgenerator", inspect_isgenerator_replacement );

}
