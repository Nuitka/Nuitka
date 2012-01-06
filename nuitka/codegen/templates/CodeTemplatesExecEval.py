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
""" Code templates for local and module level (global) uses of exec/eval.

"""

exec_local_template = """\
{
    PyObjectTemporary globals( %(globals_identifier)s );
    PyObjectTemporary locals( %(locals_identifier)s );

    bool own_locals;

    if ( locals.asObject() == Py_None && globals.asObject() == Py_None )
    {
        globals.assign( %(make_globals_identifier)s );
        locals.assign( %(make_locals_identifier)s );

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
        globals.assign( %(make_globals_identifier)s );
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
