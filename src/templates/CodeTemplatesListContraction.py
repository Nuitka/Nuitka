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
list_contraction_decl_template = """\
static PyObject *%(contraction_identifier)s( %(contraction_parameters)s );
"""

list_contraction_loop_iterated = """\
    PyObjectTemporary iterator_%(iter_count)d( MAKE_ITERATOR( %(iterated)s ) );

    while (PyObject *_python_contraction_iter_value_%(iter_count)d = ITERATOR_NEXT( iterator_%(iter_count)d.asObject() ) )
    {
        try
        {
            %(loop_var_assignment_code)s

            Py_DECREF( _python_contraction_iter_value_%(iter_count)d );
        }
        catch(...)
        {
            Py_DECREF( _python_contraction_iter_value_%(iter_count)d );
            throw;
        }

        if (%(contraction_condition)s)
        {
%(contraction_loop)s
        }
    }
"""

list_contraction_loop_production = """
            APPEND_TO_LIST(
                _python_contraction_result,
                %(contraction_body)s
            );
"""

list_contraction_code_template = """\
static PyObject *%(contraction_identifier)s( %(contraction_parameters)s )
{
    PyObject *_python_contraction_result = MAKE_LIST();

%(contraction_body)s 

    return _python_contraction_result;
}

"""
