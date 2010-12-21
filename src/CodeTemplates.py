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

from templates.CodeTemplatesMain import *

from templates.CodeTemplatesFunction import *
from templates.CodeTemplatesGeneratorExpression import *
from templates.CodeTemplatesGeneratorFunction import *
from templates.CodeTemplatesListContraction import *

from templates.CodeTemplatesParameterParsing import *

from templates.CodeTemplatesAssignments import *
from templates.CodeTemplatesExceptions import *
from templates.CodeTemplatesImporting import *
from templates.CodeTemplatesClass import *
from templates.CodeTemplatesLoops import *

global_copyright = """
// Generated code for Python source for module '%(name)s'

// This code is in part copyright Kay Hayen, license GPLv3. This has the consequence that
// your must either obtain a commercial license or also publish your original source code
// under the same license unless you don't distribute this source or its binary.
"""

# Template for the global stuff that must be had, compiling one or multple modules.
global_prelude = """\
#include "nuitka/prelude.hpp"
"""

try_finally_template = """
_PythonExceptionKeeper _caught_%(try_count)d;
bool _continue_%(try_count)d = false;
bool _break_%(try_count)d = false;
bool _return_%(try_count)d = false;
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(try_count)d.save( _exception );
}
catch ( ContinueException &e )
{
    _continue_%(try_count)d = true;
}
catch ( BreakException &e )
{
    _break_%(try_count)d = true;
}
catch ( ReturnException &e )
{
    _return_%(try_count)d = true;
}

%(final_code)s

_caught_%(try_count)d.rethrow();

if ( _continue_%(try_count)d )
{
    throw ContinueException();
}
if ( _break_%(try_count)d )
{
    throw BreakException();
}
if ( _return_%(try_count)d )
{
    throw ReturnException();
}
"""

try_except_template = """
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
        traceback = true;
    }

    _exception.toExceptionHandler();

%(exception_code)s
}
"""

try_except_else_template = """
bool _caught_%(except_count)d = false;
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(except_count)d = true;

    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
        traceback = true;
    }
    _exception.toExceptionHandler();

%(exception_code)s
}
if ( _caught_%(except_count)d == false )
{
%(else_code)s
}
"""

exec_local_template = """\
{
    PyObjectTemporary globals( %(globals_identifier)s );
    PyObjectTemporary locals( %(locals_identifier)s );

    bool own_locals = true;

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
}
"""

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
}
"""

eval_local_template = """\
EVAL_CODE( PyObjectTemporary( COMPILE_CODE(  %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) ).asObject(), ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ? %(make_globals_identifier)s : _eval_globals_tmp, ( _eval_locals_tmp = %(locals_identifier)s ) == Py_None ? ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ?  %(make_locals_identifier)s : _eval_globals_tmp : _eval_locals_tmp )"""


eval_global_template = """\
EVAL_CODE( PyObjectTemporary( COMPILE_CODE(  %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) ).asObject(), ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ? %(make_globals_identifier)s : _eval_globals_tmp, %(locals_identifier)s )"""

with_template = """\
{
    _PythonExceptionKeeper _caught_%(with_count)d;

    PyObjectTemporary %(manager)s( %(source)s );

    // TODO: The exit lookup is not used at this time, but the lookup is required for
    // compatability.
    PyObjectTemporary %(manager)s_exit( LOOKUP_WITH_EXIT( %(manager)s.asObject() ) );
    PyObjectTemporary %(manager)s_enter( LOOKUP_WITH_ENTER( %(manager)s.asObject() ) );

    PyObject *_enter_result = PyObject_Call( %(manager)s_enter.asObject(), _python_tuple_empty, _python_dict_empty );

    if (unlikely( _enter_result == NULL ))
    {
        throw _PythonException();
    }

    PyObjectTemporary %(value)s( _enter_result );

    try
    {
%(assign)s
%(body)s
    }
    catch ( _PythonException &_exception )
    {
        _exception.toPython();
        ADD_TRACEBACK( %(module_identifier)s, %(filename_identifier)s, %(name_identifier)s, _exception.getLine() );
        traceback = true;
        _exception._importFromPython();

        _caught_%(with_count)d.save( _exception );

        PyObject *exception_type  = _exception.getType();
        PyObject *exception_value = _exception.getObject();
        PyObject *exception_tb    = _exception.getTraceback();

        assert( exception_type != NULL );
        assert( exception_value != NULL );
        assert( exception_tb != NULL );

        PyObjectTemporary exit_result( CALL_FUNCTION( NULL, PyObjectTemporary( MAKE_TUPLE( INCREASE_REFCOUNT( exception_tb ), INCREASE_REFCOUNT( exception_value ), INCREASE_REFCOUNT( exception_type ) ) ).asObject(), %(manager)s_exit.asObject() ) );

        if ( CHECK_IF_TRUE( exit_result.asObject() ) )
        {
            traceback = false;
            PyErr_Clear();
        }
        else
        {
            _caught_%(with_count)d.rethrow();
        }
    }

    if ( _caught_%(with_count)d.isEmpty() )
    {
        PyObjectTemporary exit_result( CALL_FUNCTION( NULL, %(triple_none_tuple)s, %(manager)s_exit.asObject() ) );
    }
}
"""
