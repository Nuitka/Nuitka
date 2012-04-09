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
static PyObject *_MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_common_%(function_identifier)s_t *_python_context = new _context_common_%(function_identifier)s_t;
    _python_context->ref_count = 1;

    // Copy the parameter default values and closure values over.
%(context_copy)s

    return Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(mparse_function_identifier)s,
        %(function_name_obj)s,
        _make_codeobj_%(function_identifier)s(),
        %(defaults)s,
        %(module_identifier)s,
        %(function_doc)s,
        _python_context,
        _context_common_%(function_identifier)s_destructor
    );
}
"""

make_genfunc_without_context_template = """
static PyObject *_MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    return Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(mparse_function_identifier)s,
        %(function_name_obj)s,
        _make_codeobj_%(function_identifier)s(),
        %(defaults)s,
        %(module_identifier)s,
        %(function_doc)s
    );
}
"""

genfunc_yielder_template = """
static PyFrameObject *frame_%(function_identifier)s = NULL;
static PyCodeObject *_codeobj_%(function_identifier)s = NULL;

static PyCodeObject *_make_codeobj_%(function_identifier)s( void )
{
    if ( _codeobj_%(function_identifier)s == NULL )
    {
        _codeobj_%(function_identifier)s = MAKE_CODEOBJ( %(filename_identifier)s, %(function_name_obj)s, %(line_number)d, %(arg_names)s, %(arg_count)d, true );
    }

    return _codeobj_%(function_identifier)s;
}

static void %(function_identifier)s_context( Nuitka_GeneratorObject *generator )
{
    bool traceback;

    // Must be inside block, or else its d-tor will not be run.
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

    Py_INCREF( frame_%(function_identifier)s );
    generator->m_frame = frame_%(function_identifier)s;

    Py_CLEAR( generator->m_frame->f_back );

    generator->m_frame->f_back = PyThreadState_GET()->frame;
    Py_INCREF( generator->m_frame->f_back );

    PyThreadState_GET()->frame = generator->m_frame;

    FrameGuardLight frame_guard( &generator->m_frame );

    try
    {
        traceback = true;
        CHECK_EXCEPTION( generator );
        traceback = false;

        // Make context accessible if one is used.
%(context_access)s

        // Local variable inits
%(function_var_inits)s

        // Actual function code.
%(function_body)s

        PyErr_SetNone( PyExc_StopIteration );
        generator->m_yielded = NULL;
    }
    catch ( ReturnException &e )
    {
        PyErr_SetNone( PyExc_StopIteration );
        generator->m_yielded = NULL;
    }
    catch ( _PythonException &_exception )
    {
        if ( traceback == false )
        {
           _exception.addTraceback( INCREASE_REFCOUNT( generator->m_frame ) );
        }

        _exception.toPython();

        generator->m_yielded = NULL;
    }

    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );
}
"""

genfunc_common_context_use_template = """\
struct _context_common_%(function_identifier)s_t *_python_common_context = (struct _context_common_%(function_identifier)s_t *)self;
struct _context_generator_%(function_identifier)s_t *_python_context = new _context_generator_%(function_identifier)s_t;

_python_context->common_context = _python_common_context;
_python_common_context->ref_count += 1;"""

genfunc_local_context_use_template = """\
struct _context_generator_%(function_identifier)s_t *_python_context = new _context_generator_%(function_identifier)s_t;"""


genfunc_generator_without_context_making = """\
        PyObject *result = Nuitka_Generator_New(
            %(function_identifier)s_context,
            %(function_name_obj)s,
            _make_codeobj_%(function_identifier)s()
        );"""

genfunc_generator_with_context_making = """\
        PyObject *result = Nuitka_Generator_New(
            %(function_identifier)s_context,
            %(function_name_obj)s,
            _make_codeobj_%(function_identifier)s(),
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
    catch ( _PythonException &_exception )
    {
        _exception.toPython();

        return NULL;
    }
}
"""

generator_context_access_template = """
// The context of the generator.
struct _context_common_%(function_identifier)s_t *_python_context = (struct _context_common_%(function_identifier)s_t *)self;
"""

generator_context_unused_template = """\
// No context is used.
"""

# TODO: The NUITKA_MAY_BE_UNUSED is because Nuitka doesn't yet detect the case of unused
# parameters (which are stored in the context for generators to share) reliably.
generator_context_access_template2 = """
NUITKA_MAY_BE_UNUSED struct _context_generator_%(function_identifier)s_t *_python_context = (_context_generator_%(function_identifier)s_t *)generator->m_context;
"""
