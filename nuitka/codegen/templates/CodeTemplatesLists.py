#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" List related templates.

"""

template_make_list_function = """\
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_LIST%(argument_count)d( %(argument_decl)s )
{
    PyObject *result = PyList_New( %(argument_count)d );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

%(add_elements_code)s

    assert( Py_REFCNT( result ) == 1 );

    return result;
}
"""

template_add_list_element_code = """\
    assertObject( %(list_value)s );
    PyList_SET_ITEM( result, %(list_index)d, %(list_value)s );"""
