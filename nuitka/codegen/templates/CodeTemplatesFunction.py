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
""" Normal function (no yield) related templates.

"""

template_function_make_declaration = """\
#define MAKE_FUNCTION_%(function_identifier)s( %(function_creation_arg_names)s ) _MAKE_FUNCTION_%(function_identifier)s( %(function_creation_arg_reversal)s )

static PyObject *_MAKE_FUNCTION_%(function_identifier)s( %(function_creation_arg_spec)s );
"""

template_function_direct_declaration = """\
static PyObject *impl_%(function_identifier)s( %(parameter_objects_decl)s );
"""

function_context_body_template = """
// This structure is for attachment as self of %(function_identifier)s.
// It is allocated at the time the function object is created.
struct _context_%(function_identifier)s_t {
    // The function can access a read-only closure of the creator.
%(context_decl)s
};

static void _context_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_%(function_identifier)s_t *_python_context = (_context_%(function_identifier)s_t *)context_voidptr;

%(context_free)s

    delete _python_context;
}
"""

make_function_with_context_template = """
static PyObject *_MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_%(function_identifier)s_t *_python_context = new _context_%(function_identifier)s_t;

    // Copy the parameter default values and closure values over.
%(context_copy)s

    PyObject *result = Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(mparse_function_identifier)s,
        %(function_name_obj)s,
        _make_codeobj_%(function_identifier)s(),
        %(defaults)s,
        %(module_identifier)s,
        %(function_doc)s,
        _python_context,
        _context_%(function_identifier)s_destructor
    );

    return result;
}
"""

make_function_without_context_template = """
static PyObject *_MAKE_FUNCTION_%(function_identifier)s()
{
    PyObject *result = Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(mparse_function_identifier)s,
        %(function_name_obj)s,
        _make_codeobj_%(function_identifier)s(),
        %(defaults)s,
        %(module_identifier)s,
        %(function_doc)s
    );

    return result;
}
"""

function_frame_body_template = """\
static PyFrameObject *frame_%(function_identifier)s = NULL;
static PyCodeObject *_codeobj_%(function_identifier)s = NULL;

static PyCodeObject *_make_codeobj_%(function_identifier)s( void )
{
    if ( _codeobj_%(function_identifier)s == NULL )
    {
        _codeobj_%(function_identifier)s = MAKE_CODEOBJ( %(filename_identifier)s, %(function_name_obj)s, %(line_number)d, %(arg_names)s, %(arg_count)d );
    }

    return _codeobj_%(function_identifier)s;
}

static PyObject *impl_%(function_identifier)s( %(parameter_objects_decl)s )
{
%(context_access_function_impl)s
    bool traceback = false;

    if ( isFrameUnusable( frame_%(function_identifier)s ) )
    {
        if ( frame_%(function_identifier)s )
        {
#if _DEBUG_REFRAME
            puts( "reframe for %(function_identifier)s" );
#endif
            Py_DECREF( frame_%(function_identifier)s );
        }

        frame_%(function_identifier)s = MAKE_FRAME( _make_codeobj_%(function_identifier)s(), %(module_identifier)s );
    }

    FrameGuard frame_guard( frame_%(function_identifier)s );

    try
    {
        // Local variable declarations.
%(function_locals)s

        // Actual function code.
%(function_body)s

        return INCREASE_REFCOUNT( Py_None );
    }
    catch ( _PythonException &_exception )
    {
        if ( traceback == false )
        {
            _exception.addTraceback( frame_guard.getFrame() );
        }

        _exception.toPython();
        return NULL;
    }
}
"""

function_dict_setup = """\
// Locals dictionary setup.
PyObjectTemporary locals_dict( PyDict_New() );
"""

function_context_access_template = """\
    // The context of the function.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)self;"""

function_context_unused_template = """\
    // No context is used."""
