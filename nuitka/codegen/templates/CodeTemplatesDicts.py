#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
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
""" Dict related templates.

"""

template_make_dict_function = """\
#define MAKE_DICT%(pair_count)d( %(args)s ) _MAKE_DICT%(pair_count)d( EVAL_ORDERED_%(argument_count)d( %(args)s ) )

NUITKA_MAY_BE_UNUSED static PyObject *_MAKE_DICT%(pair_count)d( EVAL_ORDERED_%(argument_count)d( %(argument_decl)s ) )
{
    PyObject *result = PyDict_New();

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

%(add_elements_code)s

    assert( Py_REFCNT( result ) == 1 );

    return result;
}
"""

template_add_dict_element_code = """\
    assertObject( %(dict_key)s );
    assertObject( %(dict_value)s );

    {
        int status = PyDict_SetItem( result, %(dict_key)s, %(dict_value)s );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }"""
