#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
""" Class building and defining related templates.

"""

class_decl_template = """
static PyObject *%(class_identifier)s( %(class_dict_args)s );

static PyObject *MAKE_CLASS_%(class_identifier)s( %(class_creation_args)s );

"""

class_dict_template = """
static PyFrameObject *_FRAME_%(class_identifier)s = NULL;
static PyCodeObject *_CODEOBJ_%(class_identifier)s = NULL;

static PyObject *%(class_identifier)s( %(class_dict_args)s )
{
    bool traceback = false;

    if ( _FRAME_%(class_identifier)s == NULL || _FRAME_%(class_identifier)s->ob_refcnt > 1 )
    {
        if ( _FRAME_%(class_identifier)s )
        {
#if REFRAME_DEBUG
            puts( "reframe for %(class_identifier)s" );
#endif

            Py_DECREF( _FRAME_%(class_identifier)s );
        }

        if ( _CODEOBJ_%(class_identifier)s == NULL )
        {
            _CODEOBJ_%(class_identifier)s = MAKE_CODEOBJ( %(filename_identifier)s, %(name_identifier)s, %(line_number)d, 0 );
        }

        _FRAME_%(class_identifier)s = MAKE_FRAME( _CODEOBJ_%(class_identifier)s, %(module_identifier)s );
    }

    FrameGuard frame_guard( _FRAME_%(class_identifier)s );

    // Local variable declarations.
%(class_var_decl)s

    try
    {
        // Actual class code.
%(class_body)s

%(class_dict_creation)s
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

static PyObject *MAKE_CLASS_%(class_identifier)s( %(class_creation_args)s )
{
    // TODO: This selection is dynamic, although it is something that
    // might be determined at compile time already in many cases.
    PyObject *metaclass = PyDict_GetItemString( dict, "__metaclass__" );

    // Prefer the metaclass attribute of the new class, otherwise search the base
    // classes for their metaclass.

    if ( metaclass )
    {
        /* Hold a reference to the metaclass while we use it. */
        Py_INCREF( metaclass );
    }
    else
    {
        if ( PyTuple_GET_SIZE( bases ) > 0 )
        {
            PyObject *base = PyTuple_GET_ITEM( bases, 0 );

            metaclass = PyObject_GetAttrString( base, "__class__" );

            if ( metaclass == NULL )
            {
                PyErr_Clear();

                metaclass = INCREASE_REFCOUNT( (PyObject *)base->ob_type );
            }
        }
        else if ( %(metaclass_global_test)s )
        {
            metaclass = INCREASE_REFCOUNT( %(metaclass_global_var)s );
        }
        else
        {
            // Default to old style class.
            metaclass = INCREASE_REFCOUNT( (PyObject *)&PyClass_Type );
        }
    }

    PyObject *result = PyObject_CallFunctionObjArgs( metaclass, %(name_identifier)s, bases, dict, NULL );

    Py_DECREF( metaclass );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    // Apply decorators if any
%(class_decorator_calls)s\

    return result;
}
"""
