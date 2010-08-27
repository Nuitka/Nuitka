#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
#     Please leave the whole of this copyright notice intact.
#

prepare_other_module = """\
{ int res = PyImport_AppendInittab( (char *)"%(module_full_name)s", init%(module_name)s ); assert( res != -1 ); }"""

import_helper = """
static PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *import_name )
{
    int line = _current_line;

    PyObject *result = PyImport_ImportModuleLevel( PyString_AsString( module_name ), NULL, NULL, NULL, -1 );

    if (unlikely( result == NULL ))
    {
        _current_line = line;
        throw _PythonException();
    }

    // Release the reference returned from the __import__ call, we don't trust it, because
    // it doesn't work well with packages. Look up in sys.modules instead.
    Py_DECREF( result );

    return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
}

static void IMPORT_MODULE_STAR( PyObject *target, PyObject *module_name )
{
    PyObject *module = IMPORT_MODULE( module_name, module_name );

    // IMPORT_MODULE would raise exception already
    assert( module != NULL );

    PyObject *iter;
    bool all_case;

    if ( PyObject *all = PyMapping_GetItemString( module, (char *)"__all__" ) )
    {
        iter = MAKE_ITERATOR( all );
        all_case = true;
    }
    else
    {
        PyErr_Clear();

        iter = MAKE_ITERATOR( PyModule_GetDict( module ) );
        all_case = false;
    }

    while (PyObject *item = PyIter_Next( iter ))
    {
        assert( PyString_Check( item ) );

        // TODO: Not yet clear, what happens with __all__ and "_" of its contents.
        if (!all_case)
        {
            if ( PyString_AS_STRING( item )[0] == '_' )
            {
                continue;
            }
        }

        // TODO: Check if the reference is handled correctly
        SET_ATTRIBUTE( target, item, LOOKUP_ATTRIBUTE( module, item ) );

        Py_DECREF( item );
    }

    if ( PyErr_Occurred() )
    {
        throw _PythonException();
    }
}
"""
