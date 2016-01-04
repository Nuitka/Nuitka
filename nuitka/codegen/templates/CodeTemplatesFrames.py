#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code templates for frames of all kinds.

"""

template_frame_guard_cache_decl = """\
static PyFrameObject *cache_%(frame_identifier)s = NULL;
"""

template_frame_guard_frame_decl = """\
PyFrameObject *%(frame_identifier)s;
"""

# Frame in a function
template_frame_guard_full_block = """\
MAKE_OR_REUSE_FRAME( cache_%(frame_identifier)s, %(code_identifier)s, %(module_identifier)s );
%(frame_identifier)s = cache_%(frame_identifier)s;

// Push the new frame as the currently active one.
pushFrameStack( %(frame_identifier)s );

// Mark the frame object as in use, ref count 1 will be up for reuse.
Py_INCREF( %(frame_identifier)s );
assert( Py_REFCNT( %(frame_identifier)s ) == 2 ); // Frame stack

#if PYTHON_VERSION >= 340
%(frame_identifier)s->f_executing += 1;
#endif

// Framed code:
%(codes)s

#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );
#endif
// Put the previous frame back on top.
popFrameStack();
#if PYTHON_VERSION >= 340
%(frame_identifier)s->f_executing -= 1;
#endif
Py_DECREF( %(frame_identifier)s );
goto %(no_exception_exit)s;
"""

template_frame_guard_full_return_handler = """\
%(frame_return_exit)s:;
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );
#endif
popFrameStack();
#if PYTHON_VERSION >= 340
%(frame_identifier)s->f_executing -= 1;
#endif
Py_DECREF( %(frame_identifier)s );
goto %(return_exit)s;
"""

template_frame_guard_full_exception_handler = """\
%(frame_exception_exit)s:;
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );
#endif

{
    bool needs_detach = false;

    if ( exception_tb == NULL )
    {
        exception_tb = %(tb_making)s;
        needs_detach = true;
    }
    else if ( exception_lineno != -1 )
    {
        PyTracebackObject *traceback_new = MAKE_TRACEBACK( %(frame_identifier)s, exception_lineno );
        traceback_new->tb_next = exception_tb;
        exception_tb = traceback_new;

        needs_detach = true;
    }

    if (needs_detach)
    {
%(store_frame_locals)s

        detachFrame( exception_tb, %(frame_locals_name)s );
    }
}

popFrameStack();

#if PYTHON_VERSION >= 340
%(frame_identifier)s->f_executing -= 1;
#endif
Py_DECREF( %(frame_identifier)s );

// Return the error.
goto %(parent_exception_exit)s;
"""

# Frame for a module. TODO: Use it for functions called only once.
# TODO: The once guard need not take a reference count in its frame class.
template_frame_guard_once = """\
// Frame without reuse.
%(frame_identifier)s = MAKE_MODULE_FRAME( %(code_identifier)s, %(module_identifier)s );

// Push the new frame as the currently active one, and we should be exclusively
// owning it.
pushFrameStack( %(frame_identifier)s );
assert( Py_REFCNT( %(frame_identifier)s ) == 1 );

#if PYTHON_VERSION >= 340
%(frame_identifier)s->f_executing += 1;
#endif

// Framed code:
%(codes)s

// Restore frame exception if necessary.
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );
#endif
popFrameStack();

assertFrameObject( %(frame_identifier)s );
Py_DECREF( %(frame_identifier)s );

goto %(no_exception_exit)s;
%(frame_exception_exit)s:;
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );
#endif

if ( exception_tb == NULL )
{
    exception_tb = %(tb_making)s;
}
else if ( exception_tb->tb_frame != %(frame_identifier)s )
{
    PyTracebackObject *traceback_new = MAKE_TRACEBACK( %(frame_identifier)s, exception_lineno );
    traceback_new->tb_next = exception_tb;
    exception_tb = traceback_new;
}

// Put the previous frame back on top.
popFrameStack();

#if PYTHON_VERSION >= 340
%(frame_identifier)s->f_executing -= 1;
#endif
Py_DECREF( %(frame_identifier)s );

// Return the error.
goto %(parent_exception_exit)s;
%(no_exception_exit)s:;"""

template_generator_initial_throw = """\
// Throwing into not started generators is possible. As they don't stand any
// chance to deal with them, we might as well create traceback on the
// outside,
if ( generator->m_exception_type )
{
    generator->m_yielded = NULL;

    exception_type = generator->m_exception_type;
    generator->m_exception_type = NULL;

    exception_value = generator->m_exception_value;
    generator->m_exception_value = NULL;

    exception_tb = generator->m_exception_tb;;
    generator->m_exception_tb = NULL;

    if (exception_tb == NULL)
    {
        %(set_error_line_number)s
        goto %(frame_exception_exit)s;
    }
    else
    {
        goto function_exception_exit;
    }
}
"""

# Frame in a generator
template_frame_guard_generator = """\
MAKE_OR_REUSE_FRAME( %(frame_cache_identifier)s, %(code_identifier)s, %(module_identifier)s );
generator->m_frame = %(frame_cache_identifier)s;
Py_INCREF( generator->m_frame );

#if PYTHON_VERSION >= 340
generator->m_frame->f_gen = (PyObject *)generator;
#endif

Py_CLEAR( generator->m_frame->f_back );

generator->m_frame->f_back = PyThreadState_GET()->frame;
Py_INCREF( generator->m_frame->f_back );

PyThreadState_GET()->frame = generator->m_frame;
Py_INCREF( generator->m_frame );

#if PYTHON_VERSION >= 340
generator->m_frame->f_executing += 1;
#endif

#if PYTHON_VERSION >= 300
// Accept currently existing exception as the one to publish again when we
// yield or yield from.

PyThreadState *thread_state = PyThreadState_GET();

generator->m_frame->f_exc_type = thread_state->exc_type;
if ( generator->m_frame->f_exc_type == Py_None ) generator->m_frame->f_exc_type = NULL;
Py_XINCREF( generator->m_frame->f_exc_type );
generator->m_frame->f_exc_value = thread_state->exc_value;
Py_XINCREF( generator->m_frame->f_exc_value );
generator->m_frame->f_exc_traceback = thread_state->exc_traceback;
Py_XINCREF( generator->m_frame->f_exc_traceback );
#endif

// Framed code:
%(codes)s

#if PYTHON_VERSION >= 340
generator->m_frame->f_executing -= 1;
#endif

#if PYTHON_VERSION >= 300
Py_CLEAR( generator->m_frame->f_exc_type );
Py_CLEAR( generator->m_frame->f_exc_value );
Py_CLEAR( generator->m_frame->f_exc_traceback );
#endif

Py_DECREF( generator->m_frame );
goto %(no_exception_exit)s;
"""

# Frame in a coroutine
template_frame_guard_coroutine = """\
MAKE_OR_REUSE_FRAME( %(frame_cache_identifier)s, %(code_identifier)s, %(module_identifier)s );
coroutine->m_frame = %(frame_cache_identifier)s;
Py_INCREF( coroutine->m_frame );

coroutine->m_frame->f_gen = (PyObject *)coroutine;

Py_CLEAR( coroutine->m_frame->f_back );

coroutine->m_frame->f_back = PyThreadState_GET()->frame;
Py_INCREF( coroutine->m_frame->f_back );

PyThreadState_GET()->frame = coroutine->m_frame;
Py_INCREF( coroutine->m_frame );

coroutine->m_frame->f_executing += 1;

// Accept currently existing exception as the one to publish again when we
// yield or yield from.

PyThreadState *thread_state = PyThreadState_GET();

coroutine->m_frame->f_exc_type = thread_state->exc_type;
if ( coroutine->m_frame->f_exc_type == Py_None ) coroutine->m_frame->f_exc_type = NULL;
Py_XINCREF( coroutine->m_frame->f_exc_type );
coroutine->m_frame->f_exc_value = thread_state->exc_value;
Py_XINCREF( coroutine->m_frame->f_exc_value );
coroutine->m_frame->f_exc_traceback = thread_state->exc_traceback;
Py_XINCREF( coroutine->m_frame->f_exc_traceback );

// Framed code:
%(codes)s

coroutine->m_frame->f_executing -= 1;

Py_CLEAR( coroutine->m_frame->f_exc_type );
Py_CLEAR( coroutine->m_frame->f_exc_value );
Py_CLEAR( coroutine->m_frame->f_exc_traceback );

Py_DECREF( coroutine->m_frame );
goto %(no_exception_exit)s;
"""


# TODO: This cannot happen, can it?
template_frame_guard_generator_return_handler = """\
%(frame_return_exit)s:;

#if PYTHON_VERSION >= 300
Py_CLEAR( %(frame_identifier)s->f_exc_type );
Py_CLEAR( %(frame_identifier)s->f_exc_value );
Py_CLEAR( %(frame_identifier)s->f_exc_traceback );
#endif

Py_DECREF( %(frame_identifier)s );
goto %(return_exit)s;
"""


template_frame_guard_generator_exception_handler = """\
%(frame_exception_exit)s:;

// If it's not an exit exception, consider and create a traceback for it.
if ( !EXCEPTION_MATCH_GENERATOR( exception_type ) )
{
    int needs_detach = false;

    if ( exception_tb == NULL )
    {
        exception_tb = %(tb_making)s;
        needs_detach = true;
    }
    else if ( exception_tb->tb_frame != %(frame_identifier)s )
    {
        PyTracebackObject *traceback_new = MAKE_TRACEBACK( %(frame_identifier)s, exception_lineno );
        traceback_new->tb_next = exception_tb;
        exception_tb = traceback_new;

        needs_detach = true;
    }

    if (needs_detach)
    {
%(store_frame_locals)s

        detachFrame( exception_tb, %(frame_locals_name)s );
    }
}

#if PYTHON_VERSION >= 300
Py_CLEAR( %(frame_identifier)s->f_exc_type );
Py_CLEAR( %(frame_identifier)s->f_exc_value );
Py_CLEAR( %(frame_identifier)s->f_exc_traceback );
#endif

Py_DECREF( %(frame_identifier)s );
// Return the error.
goto %(parent_exception_exit)s;
%(no_exception_exit)s:;
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
