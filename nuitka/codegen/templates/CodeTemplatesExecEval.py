#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code templates for local and module level (global) uses of exec/eval.

"""

exec_local_template = """\
{
    PyObjectTemporary globals( %(globals_identifier)s );
    PyObjectTemporary locals( %(locals_identifier)s );

    bool own_locals;

    if ( locals.asObject() == Py_None && globals.asObject() == Py_None )
    {
        globals.assign1( %(make_globals_identifier)s );
        locals.assign1( %(make_locals_identifier)s );

        own_locals = true;
    }
    else
    {
        own_locals = false;
    }

    PyObjectTemporary code( COMPILE_CODE( %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) );

    PyObject *result = EVAL_CODE( code.asObject(), globals.asObject(), locals.asObject() );
    Py_DECREF( result );

    if ( own_locals )
    {
%(store_locals_code)s
    }
}"""

exec_global_template = """\
{
    PyObjectTemporary globals( %(globals_identifier)s );
    PyObjectTemporary locals( %(locals_identifier)s );

    if ( globals.asObject() == Py_None )
    {
        globals.assign1( %(make_globals_identifier)s );
    }

    PyObjectTemporary code( COMPILE_CODE( %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) );

    PyObject *result = EVAL_CODE( code.asObject(), globals.asObject(), locals.asObject() );
    Py_DECREF( result );
}"""

# Bad to read, but we wan't all on same line
# pylint: disable=C0301

eval_local_template = """\
EVAL_CODE( PyObjectTemporary( COMPILE_CODE( %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) ).asObject(), ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ? %(make_globals_identifier)s : _eval_globals_tmp, ( _eval_locals_tmp = %(locals_identifier)s ) == Py_None ? ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ?  %(make_locals_identifier)s : _eval_globals_tmp : _eval_locals_tmp )"""

eval_global_template = """\
EVAL_CODE( PyObjectTemporary( COMPILE_CODE(  %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) ).asObject(), ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ? %(make_globals_identifier)s : _eval_globals_tmp, %(locals_identifier)s )"""
