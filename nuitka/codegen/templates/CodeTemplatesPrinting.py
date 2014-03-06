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
""" Code Templates for printing. """

template_print_statement = """\
{
    PyObject *target_file = %(target_file)s;

    if ( target_file == Py_None )
    {
        target_file = GET_STDOUT();
        Py_INCREF( target_file );
    }

    PyObjectTemporary file_reference( target_file );

%(print_elements_code)s}"""

template_print_value = """\
PRINT_ITEM_TO( %(target_file)s, %(print_value)s );"""

template_print_newline = """\
PRINT_NEW_LINE_TO( %(target_file)s );"""
