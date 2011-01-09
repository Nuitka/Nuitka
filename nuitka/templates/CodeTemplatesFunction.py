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
""" Function related templates. """

function_decl_template = """\
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s );
"""

function_context_body_template = """
// This structure is for attachment as self of %(function_identifier)s.
// It is allocated at the time the function object is created.
struct _context_%(function_identifier)s_t {
    // The function can access a read-only closure of the creator.
    %(function_context_decl)s
};

static void _context_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_%(function_identifier)s_t *_python_context = (_context_%(function_identifier)s_t *)context_voidptr;

%(function_context_free)s

    delete _python_context;
}
"""

function_context_access_template = """
    // The context of the function.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)self;
"""

function_context_unused_template = """\
    // No context is used.
"""

make_function_with_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_%(function_identifier)s_t *_python_context = new _context_%(function_identifier)s_t;

    // Copy the parameter default values and closure values over.
    %(function_context_copy)s

    PyObject *result = Nuitka_Function_New( %(function_identifier)s, %(function_name_obj)s, %(module)s, %(function_doc)s, _python_context, _context_%(function_identifier)s_destructor );

    // Apply decorators if any
%(function_decorator_calls)s

    return result;
}
"""

make_function_without_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    PyObject *result = Nuitka_Function_New( %(function_identifier)s, %(function_name_obj)s, %(module)s, %(function_doc)s );

    // Apply decorators if any
%(function_decorator_calls)s

    return result;
}
"""

function_body_template = """

static PyObject *impl_%(function_identifier)s( PyObject *self%(parameter_object_decl)s )
{
%(context_access_function_impl)s
    bool traceback = false;

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
        _exception.toPython();

        if ( traceback == false )
        {
            ADD_TRACEBACK( %(module_identifier)s, %(filename_identifier)s, %(name_identifier)s, _exception.getLine() );
        }

        return NULL;
    }
}

static PyObject *%(function_identifier)s( PyObject *self, PyObject *args, PyObject *kw )
{
%(context_access_arg_parsing)s
%(parameter_parsing_code)s

    return impl_%(function_identifier)s( self%(parameter_object_list)s );

error_exit:;

%(parameter_release_code)s
    return NULL;

}
"""

function_dict_setup = """\
// Locals dictionary setup.
PyObjectTemporary locals_dict( PyDict_New() );
"""
