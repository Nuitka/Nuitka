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

import_helper = """

#ifdef _NUITKA_EXE
static bool FIND_EMBEDDED_MODULE( char const *name );
#endif

static PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *import_name )
{

#ifdef _NUITKA_EXE
    // First try our own package resistent form of frozen modules if we have
    // them embedded. And avoid recursion here too, in case of cyclic dependencies.
    if ( !HAS_KEY( PySys_GetObject( (char *)"modules" ), module_name ) )
    {
        if ( FIND_EMBEDDED_MODULE( PyString_AsString( module_name ) ) )
        {
            return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
        }
    }
#endif

    int line = _current_line;
    PyObject *result = PyImport_ImportModuleEx( PyString_AsString( module_name ), NULL, NULL, NULL );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    // Release the reference returned from the __import__ call, we don't trust it, because
    // it doesn't work well with packages. Look up in sys.modules instead.
    Py_DECREF( result );

    return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
}

static void IMPORT_MODULE_STAR( PyObject *target, bool is_module, PyObject *module_name )
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

    while ( PyObject *item = PyIter_Next( iter ) )
    {
        assert( PyString_Check( item ) );

        // TODO: Not yet clear, what happens with __all__ and "_" of its contents.
        if ( all_case == false )
        {
            if ( PyString_AS_STRING( item )[0] == '_' )
            {
                continue;
            }
        }

        // TODO: Check if the reference is handled correctly
        if ( is_module )
        {
            SET_ATTRIBUTE( target, item, LOOKUP_ATTRIBUTE( module, item ) );
        }
        else
        {
            SET_SUBSCRIPT( target, item, LOOKUP_ATTRIBUTE( module, item ) );
        }

        Py_DECREF( item );
    }

    if ( PyErr_Occurred() )
    {
        throw _PythonException();
    }
}
"""

import_from_template = """\
{
    PyObject *_module_temp = PyImport_ImportModuleEx( (char *)"%(module_name)s", NULL, NULL, %(import_list)s );

    if (unlikely( _module_temp == NULL ))
    {
        throw _PythonException();
    }

%(module_imports)s

    Py_DECREF( _module_temp );
}
"""

import_item_code = """\
// Template import_item_code
try
{
    %(lookup_code)s
}
catch( _PythonException &_exception )
{
    _exception.setType( PyExc_ImportError );
    throw _exception;
}"""
