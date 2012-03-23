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
""" Class building and defining related templates.

"""

class_decl_template = """
static PyObject *%(class_identifier)s( %(class_dict_args)s );
"""

class_dict_template = """
static PyFrameObject *frame_%(class_identifier)s = NULL;
static PyCodeObject *_CODEOBJ_%(class_identifier)s = NULL;

static PyObject *%(class_identifier)s( %(class_dict_args)s )
{
    bool traceback = false;

    if ( isFrameUnusable( frame_%(class_identifier)s ) )
    {
        if ( frame_%(class_identifier)s )
        {
#if _DEBUG_REFRAME
            puts( "reframe for %(class_identifier)s" );
#endif

            Py_DECREF( frame_%(class_identifier)s );
        }

        if ( _CODEOBJ_%(class_identifier)s == NULL )
        {
            _CODEOBJ_%(class_identifier)s = MAKE_CODEOBJ( %(filename_identifier)s, %(name_identifier)s, %(line_number)d, _python_tuple_empty, 0 );
        }

        frame_%(class_identifier)s = MAKE_FRAME( _CODEOBJ_%(class_identifier)s, %(module_identifier)s );
    }

    FrameGuard frame_guard( frame_%(class_identifier)s );

    // Local variable declarations.
%(class_var_decl)s

    try
    {
        // Actual class code.
%(class_body)s
    }
    catch ( _PythonException &_exception )
    {
        if ( traceback == false )
        {
            _exception.addTraceback( frame_guard.getFrame() );
            throw _exception;
        }
        else
        {
            throw;
        }
    }
}

"""
