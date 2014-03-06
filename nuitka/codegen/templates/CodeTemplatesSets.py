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
""" Set related templates.

"""

template_make_set_function = """\
NUITKA_MAY_BE_UNUSED static PyObject *MAKE_SET%(argument_count)d( %(argument_decl)s )
{
    PyObject *result = PySet_New( NULL );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

%(add_elements_code)s

    assert( Py_REFCNT( result ) == 1 );

    return result;
}
"""

template_add_set_element_code = """\
    assertObject( %(set_value)s );
    PySet_Add( result, %(set_value)s );"""
