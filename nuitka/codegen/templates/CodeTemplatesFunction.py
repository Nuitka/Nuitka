#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
struct _context_%(function_identifier)s_t
{
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
        %(code_identifier)s,
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
        %(code_identifier)s,
        %(defaults)s,
        %(module_identifier)s,
        %(function_doc)s
    );

    return result;
}
"""

function_body_template = """\
static PyObject *impl_%(function_identifier)s( %(parameter_objects_decl)s )
{
%(context_access_function_impl)s

    // Local variable declarations.
%(function_locals)s

    // Actual function code.
%(function_body)s

    return INCREASE_REFCOUNT( Py_None );
}
"""

function_dict_setup = """\
// Locals dictionary setup.
PyObjectTemporary locals_dict( PyDict_New() );
"""

frame_guard_full_template = """\
bool traceback = false;

static PyFrameObject *frame_%(frame_identifier)s = NULL;

if ( isFrameUnusable( frame_%(frame_identifier)s ) )
{
    if ( frame_%(frame_identifier)s )
    {
#if _DEBUG_REFRAME
        puts( "reframe for %(frame_identifier)s" );
#endif
        Py_DECREF( frame_%(frame_identifier)s );
    }

    frame_%(frame_identifier)s = MAKE_FRAME( %(code_identifier)s, %(module_identifier)s );
}

FrameGuard frame_guard( frame_%(frame_identifier)s );
try
{
    assert( Py_REFCNT( frame_%(frame_identifier)s ) == 2 ); // Frame stack
%(codes)s
}
catch ( _PythonException &_exception )
{
    if ( traceback == false )
    {
        _exception.addTraceback( frame_guard.getFrame() );
    }
%(return_code)s
}"""

frame_guard_python_return = """
    _exception.toPython();
    return NULL;"""

frame_guard_cpp_return = """
    throw;"""

frame_guard_listcontr_template = """\
FrameGuardVeryLight frame_guard;

%(codes)s"""

function_context_access_template = """\
    // The context of the function.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)self->m_context;"""

function_context_unused_template = """\
    // No context is used."""
