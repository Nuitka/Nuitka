# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)PyCObject_AsVoidPtr(self);
"""

function_context_unused_template = """
    // The function uses no context.
"""

make_function_with_context_template = """
static PyMethodDef _methoddef_%(function_identifier)s = {"%(function_name)s", (PyCFunction)%(function_identifier)s, METH_VARARGS | METH_KEYWORDS, NULL};

static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_%(function_identifier)s_t *_python_context = new _context_%(function_identifier)s_t;

    // Copy the parameter default values and closure values over.
    %(function_context_copy)s

    PyObject *_python_self = PyCObject_FromVoidPtr( _python_context, _context_%(function_identifier)s_destructor );

    if (_python_self == NULL)
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
        throw _PythonException();
    }

    PyObject *result = PyKFunction_New( &_methoddef_%(function_identifier)s, _python_self, %(module)s, %(function_doc)s );

    // The self is to be released along with the new function which holds its own reference now, so release ours.
    Py_DECREF( _python_self );

    if (result == NULL)
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
        throw _PythonException();
    }

    // Apply decorators if any
    %(function_decorator_calls)s

    return result;
}
"""

make_function_without_context_template = """
static PyMethodDef _methoddef_%(function_identifier)s = {"%(function_name)s", (PyCFunction)%(function_identifier)s, METH_VARARGS | METH_KEYWORDS, NULL};

static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    PyObject *result = PyKFunction_New( &_methoddef_%(function_identifier)s, Py_None, %(module)s, %(function_doc)s );
    if (result == NULL)
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
        throw _PythonException();
    }

    // Apply decorators if any
    %(function_decorator_calls)s

    return result;
}
"""

function_body_template = """
static PyObject *%(function_identifier)s( PyObject *self, PyObject *args, PyObject *kw )
{
%(context_access_template)s

    try
    {
        %(parameter_parsing_code)s

        // Local variable declarations.
        %(function_locals)s

        // Actual function code.
        %(function_body)s

        return INCREASE_REFCOUNT( Py_None );
    }
    catch (_PythonException &_exception)
    {
        _exception.toPython();
        ADD_TRACEBACK( %(module)s, %(file_identifier)s, %(name_identifier)s, _exception.getLine() );

        return NULL;
    }
}
"""
