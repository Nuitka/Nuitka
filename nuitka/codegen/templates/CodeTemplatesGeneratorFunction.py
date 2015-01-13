#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
        %(kw_defaults)s,
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
        %(kw_defaults)s,
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
#ifdef _NUITKA_MAKECONTEXT_INTS
static void %(function_identifier)s_context( int generator_address_1, int generator_address_2 )
{
    // Restore the pointer from ints should it be necessary, often it can be
    // directly received.
    int generator_addresses[2] = {
        generator_address_1,
        generator_address_2
    };

    Nuitka_GeneratorObject *generator = (Nuitka_GeneratorObject *)*(uintptr_t *)&generator_addresses[0];
#else
static void %(function_identifier)s_context( Nuitka_GeneratorObject *generator )
{
#endif

    assertObject( (PyObject *)generator );
    assert( Nuitka_Generator_Check( (PyObject *)generator ) );

    // Make context accessible if one is used.
%(context_access)s

    // Local variable inits
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(generator_exit)s
}"""

template_generator_exception_exit = """\
    PyErr_Restore( INCREASE_REFCOUNT( PyExc_StopIteration ), NULL, NULL );

    generator->m_yielded = NULL;
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

    // The above won't return, but we need to make it clear to the compiler
    // as well, or else it will complain and/or generate inferior code.
    assert(false);
    return;
function_exception_exit:
    assert( exception_type );
    assert( exception_tb );
    PyErr_Restore( exception_type, exception_value, (PyObject *)exception_tb );
    generator->m_yielded = NULL;
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );
"""

template_generator_noexception_exit = """\
    // Return statement must be present.
    assert(false);
    generator->m_yielded = NULL;
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );
"""

template_generator_return_exit = """\
    // The above won't return, but we need to make it clear to the compiler
    // as well, or else it will complain and/or generate inferior code.
    assert(false);
    return;
function_return_exit:
#if PYTHON_VERSION < 330
    PyErr_Restore( INCREASE_REFCOUNT( PyExc_StopIteration ), NULL, NULL );
#else
    PyErr_Restore( INCREASE_REFCOUNT( PyExc_StopIteration ), tmp_return_value, NULL );
#endif
    generator->m_yielded = NULL;
    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );

"""


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
"""

generator_context_access_template = """
// The context of the generator.
struct _context_common_%(function_identifier)s_t *_python_context = (struct _context_common_%(function_identifier)s_t *)self->m_context;
"""

generator_context_unused_template = """\
// No context is used.
"""

# TODO: The NUITKA_MAY_BE_UNUSED is because Nuitka doesn't yet detect the case
# of unused parameters (which are stored in the context for generators to share)
# reliably.
generator_context_access_template2 = """
NUITKA_MAY_BE_UNUSED struct _context_generator_%(function_identifier)s_t *_python_context = (_context_generator_%(function_identifier)s_t *)generator->m_context;
"""
