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
contraction_decl_template = """\
static PyObject *%(contraction_identifier)s( %(contraction_parameters)s );
"""

contraction_loop_iterated = """\
    PyObjectTemporary iterator_%(iter_count)d( MAKE_ITERATOR( %(iterated)s ) );

    while ( PyObject *_python_contraction_iter_value_%(iter_count)d = ITERATOR_NEXT( iterator_%(iter_count)d.asObject() ) )
    {
        // TODO: Use PyObjectTemporary instead of try/catch here.
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

        if ( %(contraction_condition)s )
        {
%(contraction_loop)s
        }
    }
"""

list_contraction_loop_production = """\
            APPEND_TO_LIST(
                _python_contraction_result,
                %(contraction_body)s
            );"""

set_contraction_loop_production = """\
            ADD_TO_SET(
                _python_contraction_result,
                %(contraction_body)s
            );"""


dict_contraction_loop_production = """\
            DICT_SET_ITEM(
                _python_contraction_result,
                %(key_identifier)s,
                %(value_identifier)s
            );"""


contraction_code_template = """\
static PyObject *%(contraction_identifier)s( %(contraction_parameters)s )
{
%(contraction_var_decl)s

%(contraction_body)s

    return _python_contraction_result;
}
"""

# Note: List contractions have no local variables, they share everything with the outside world.
list_contration_var_decl = """\
PyObject *_python_contraction_result = MAKE_LIST();""";

dict_contration_var_decl = """\
PyObject *_python_contraction_result = MAKE_DICT();
%(local_var_decl)s""";

set_contration_var_decl = """\
PyObject *_python_contraction_result = MAKE_SET();
%(local_var_decl)s""";
