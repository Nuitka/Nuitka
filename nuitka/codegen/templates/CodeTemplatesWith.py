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
""" Template used for code related to 'with' statements.

"""


# Note: The exit lookup is not used this early, but the lookup is required for full
# compatability, because CPython looks up __exit__ and __enter__ in that order at the
# beginning of a with statement bytecode, we have to emulate it, or else we won't b
# raising attribute error exceptions the same way than CPython will.

with_template = """\
{
    PyObjectTemporary %(manager)s( %(source)s );

    PyObjectTemporary %(manager)s_exit( LOOKUP_WITH_EXIT( %(manager)s.asObject() ) );
    PyObjectTemporary %(manager)s_enter( LOOKUP_WITH_ENTER( %(manager)s.asObject() ) );

    PyObject *_enter_result = PyObject_Call( %(manager)s_enter.asObject(), _python_tuple_empty, NULL );

    if (unlikely( _enter_result == NULL ))
    {
        throw _PythonException();
    }

    PyObjectTemporary %(value)s( _enter_result );

    _PythonExceptionKeeper _caught_%(with_count)d;

    try
    {
%(assign)s
%(body)s
    }
    catch ( _PythonException &_exception )
    {
        if ( traceback == true )
        {
           _caught_%(with_count)d.save( _exception );
        }

        if ( !_exception.hasTraceback() )
        {
            _exception.setTraceback( %(tb_making)s );
        }
        else if ( traceback == false )
        {
            _exception.addTraceback( frame_guard.getFrame() );
        }

        if ( traceback == false )
        {
           _caught_%(with_count)d.save( _exception );
        }

        PyObject *exception_type  = _exception.getType();
        PyObject *exception_value = _exception.getObject();
        PyObject *exception_tb    = (PyObject *)_exception.getTraceback();

        assertObject( exception_type );
        assertObject( exception_value );
        assertObject( exception_tb );

        PyObject *_exit_result = PyObject_Call(
           %(manager)s_exit.asObject(),
           PyObjectTemporary( MAKE_TUPLE3( exception_type, exception_value, exception_tb ) ).asObject(),
           NULL
        );

        if (unlikely( _exit_result == NULL ))
        {
            throw _PythonException();
        }

        if ( CHECK_IF_TRUE( PyObjectTemporary( _exit_result ).asObject() ) )
        {
            traceback = false;
        }
        else
        {
            traceback = true;
            _caught_%(with_count)d.rethrow();
        }
    }

    if ( _caught_%(with_count)d.isEmpty() )
    {
        PyObject *_exit_result = PyObject_Call( %(manager)s_exit.asObject(), %(triple_none_tuple)s, NULL );

        if (unlikely( _exit_result == NULL ))
        {

            throw _PythonException();
        }

        Py_DECREF( _exit_result );
    }
}"""
