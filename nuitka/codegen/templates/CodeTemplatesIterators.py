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
""" Templates for the iterator handling.

"""


template_iterator_check = """\
// Check if iterator has left-over elements.
assertObject( %(iterator_name)s ); assert( PyIter_Check( %(iterator_name)s ) );

%(attempt_name)s = (*Py_TYPE( %(iterator_name)s )->tp_iternext)( %(iterator_name)s );

if (likely( %(attempt_name)s == NULL ))
{
    // TODO: Could first fetch, then check, should be faster.
    if ( !ERROR_OCCURRED() )
    {
    }
    else if ( PyErr_ExceptionMatches( PyExc_StopIteration ))
    {
        PyErr_Clear();
    }
    else
    {
        PyErr_Fetch( &exception_type, &exception_value, (PyObject **)&exception_tb );
%(release_temps_1)s
        goto %(exception_exit)s;
    }
}
else
{
    Py_DECREF( %(attempt_name)s );

    // TODO: Could avoid PyErr_Format.
#if PYTHON_VERSION < 300
    PyErr_Format( PyExc_ValueError, "too many values to unpack" );
#else
    PyErr_Format( PyExc_ValueError, "too many values to unpack (expected %(count)d)" );
#endif
    PyErr_Fetch( &exception_type, &exception_value, (PyObject **)&exception_tb );
%(release_temps_2)s
    goto %(exception_exit)s;
}"""
