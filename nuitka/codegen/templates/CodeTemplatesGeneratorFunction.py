#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Generator function (with yield) related templates.

"""

genfunc_context_body_template = """

// This structure is for attachment as self of the generator function %(function_identifier)s and
// contains the common closure. It is allocated at the time the genexpr object is created.
struct _context_common_%(function_identifier)s_t
{
    // Ref count to keep track of common context usage and release only when it's the last one
    int ref_count;

    // The generator function can access a read-only closure of the creator.
%(function_common_context_decl)s
};

struct _context_generator_%(function_identifier)s_t
{
    _context_common_%(function_identifier)s_t *common_context;

    // The generator function instance can access its parameters from creation time.
%(function_instance_context_decl)s
};

static void _context_common_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_common_%(function_identifier)s_t *_python_context = (struct _context_common_%(function_identifier)s_t *)context_voidptr;

    assert( _python_context->ref_count > 0 );
    _python_context->ref_count -= 1;
%(context_free)s

    if ( _python_context->ref_count == 0 )
    {
        delete _python_context;
    }
}

static void _context_generator_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_generator_%(function_identifier)s_t *_python_context = (struct _context_generator_%(function_identifier)s_t *)context_voidptr;

    _context_common_%(function_identifier)s_destructor( _python_context->common_context );

    delete _python_context;
}
"""

genfunc_context_local_only_template = """
struct _context_generator_%(function_identifier)s_t
{
    // The generator function instance can access its parameters from creation time.
%(function_instance_context_decl)s
};

static void _context_generator_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_generator_%(function_identifier)s_t *_python_context = (struct _context_generator_%(function_identifier)s_t *)context_voidptr;

    delete _python_context;
}
"""

make_genfunc_with_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_common_%(function_identifier)s_t *_python_context = new _context_common_%(function_identifier)s_t;
    _python_context->ref_count = 1;

    // Copy the parameter default values and closure values over.
%(context_copy)s

    return Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(dparse_function_identifier)s,
        %(function_name_obj)s,
#if PYTHON_VERSION >= 330
        %(function_qualname_obj)s,
#endif
        %(code_identifier)s,
        %(defaults)s,
#if PYTHON_VERSION >= 300
        %(kwdefaults)s,
        %(annotations)s,
#endif
        %(module_identifier)s,
        %(function_doc)s,
        _python_context,
        _context_common_%(function_identifier)s_destructor
    );
}
"""

make_genfunc_without_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    return Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(dparse_function_identifier)s,
        %(function_name_obj)s,
#if PYTHON_VERSION >= 330
        %(function_qualname_obj)s,
#endif
        %(code_identifier)s,
        %(defaults)s,
#if PYTHON_VERSION >= 300
        %(kwdefaults)s,
        %(annotations)s,
#endif
        %(module_identifier)s,
        %(function_doc)s
    );
}
"""

# TODO: Make the try/catch below unnecessary by detecting the presence
# or return statements in generators.
genfunc_yielder_template = """
static void %(function_identifier)s_context( Nuitka_GeneratorObject *generator )
{
    try
    {
        // Make context accessible if one is used.
%(context_access)s

        // Local variable inits
%(function_var_inits)s

        // Actual function code.
%(function_body)s
    }
    catch( ReturnValueException &e )
    {
        PyErr_SetObject( PyExc_StopIteration, e.getValue0() );
    }

    assert( ERROR_OCCURED() );

    // TODO: Won't return, we should tell the compiler about that.
    generator->m_yielded = NULL;
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );
}
"""

frame_guard_genfunc_template = """\
static PyFrameObject *frame_%(frame_identifier)s = NULL;

// Must be inside block, or else its d-tor will not be run.
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

Py_INCREF( frame_%(frame_identifier)s );
generator->m_frame = frame_%(frame_identifier)s;

Py_CLEAR( generator->m_frame->f_back );

generator->m_frame->f_back = PyThreadState_GET()->frame;
Py_INCREF( generator->m_frame->f_back );

PyThreadState_GET()->frame = generator->m_frame;

FrameGuardLight frame_guard( &generator->m_frame );

// TODO: The inject of the exception through C++ is very non-optimal, this flag
// now indicates only if the exception occurs initially as supposed, or during
// life, this could and should be shortcut.
bool traceback;

try
{
    // TODO: In case we don't raise exceptions ourselves, we would still have to do this, so
    // beware to not optimize this away for generators without a replacement.
    traceback = true;
    CHECK_EXCEPTION( generator );
    traceback = false;

%(codes)s

    PyErr_SetObject( PyExc_StopIteration, (PyObject *)NULL );
}
catch ( PythonException &_exception )
{
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
    }
    else if ( traceback == false )
    {
        _exception.addTraceback( generator->m_frame );
    }
    _exception.toPython();

    // TODO: Moving this code is not allowed yet.
    generator->m_yielded = NULL;
}"""

genfunc_common_context_use_template = """\
struct _context_common_%(function_identifier)s_t *_python_common_context = (struct _context_common_%(function_identifier)s_t *)self->m_context;
struct _context_generator_%(function_identifier)s_t *_python_context = new _context_generator_%(function_identifier)s_t;

_python_context->common_context = _python_common_context;
_python_common_context->ref_count += 1;"""

genfunc_local_context_use_template = """\
struct _context_generator_%(function_identifier)s_t *_python_context = \
new _context_generator_%(function_identifier)s_t;"""


genfunc_generator_without_context_making = """\
        PyObject *result = Nuitka_Generator_New(
            %(function_identifier)s_context,
            %(function_name_obj)s,
            %(code_identifier)s
        );"""

genfunc_generator_with_context_making = """\
        PyObject *result = Nuitka_Generator_New(
            %(function_identifier)s_context,
            %(function_name_obj)s,
            %(code_identifier)s,
            _python_context,
            _context_generator_%(function_identifier)s_destructor
        );"""


genfunc_function_maker_template = """
static PyObject *impl_%(function_identifier)s( %(parameter_objects_decl)s )
{
    // Create context if any
%(context_making)s

    try
    {
%(generator_making)s

        if (unlikely( result == NULL ))
        {
            PyErr_Format( PyExc_RuntimeError, "cannot create function %(function_name)s" );
            return NULL;
        }

        // Copy to context parameter values and closured variables if any.
%(context_copy)s

        return result;
    }
    catch ( PythonException &_exception )
    {
        _exception.toPython();

        return NULL;
    }
}
"""

generator_context_access_template = """
// The context of the generator.
struct _context_common_%(function_identifier)s_t *_python_context = (struct _context_common_%(function_identifier)s_t *)self->m_context;
"""

generator_context_unused_template = """\
// No context is used.
"""

# TODO: The NUITKA_MAY_BE_UNUSED is because Nuitka doesn't yet detect the case of unused
# parameters (which are stored in the context for generators to share) reliably.
generator_context_access_template2 = """
NUITKA_MAY_BE_UNUSED struct _context_generator_%(function_identifier)s_t *_python_context = (_context_generator_%(function_identifier)s_t *)generator->m_context;
"""
