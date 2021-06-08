#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

# Frame in a function
template_frame_guard_full_block = """\
if (isFrameUnusable(%(frame_cache_identifier)s)) {
    Py_XDECREF(%(frame_cache_identifier)s);

#if _DEBUG_REFCOUNTS
    if (%(frame_cache_identifier)s == NULL) {
        count_active_frame_cache_instances += 1;
    } else {
        count_released_frame_cache_instances += 1;
    }
    count_allocated_frame_cache_instances += 1;
#endif
    %(frame_cache_identifier)s = MAKE_FUNCTION_FRAME(%(code_identifier)s, %(module_identifier)s, %(locals_size)s);
#if _DEBUG_REFCOUNTS
} else {
    count_hit_frame_cache_instances += 1;
#endif
}
assert(%(frame_cache_identifier)s->m_type_description == NULL);
%(frame_identifier)s = %(frame_cache_identifier)s;

// Push the new frame as the currently active one.
pushFrameStack(%(frame_identifier)s);

// Mark the frame object as in use, ref count 1 will be up for reuse.
assert(Py_REFCNT(%(frame_identifier)s) == 2); // Frame stack

// Framed code:
%(codes)s

#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);
#endif

// Put the previous frame back on top.
popFrameStack();

goto %(no_exception_exit)s;
"""

template_frame_guard_full_return_handler = """\
%(frame_return_exit)s:;
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);
#endif

// Put the previous frame back on top.
popFrameStack();

goto %(return_exit)s;
"""

template_frame_attach_locals = """\
Nuitka_Frame_AttachLocals(
    %(frame_identifier)s,
    %(type_description)s%(frame_variable_refs)s
);
"""

template_frame_guard_full_exception_handler = """\
%(frame_exception_exit)s:;

#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);
#endif

if (%(exception_tb)s == NULL) {
    %(exception_tb)s = %(tb_making)s;
} else if (%(exception_tb)s->tb_frame != &%(frame_identifier)s->m_frame) {
    %(exception_tb)s = ADD_TRACEBACK(%(exception_tb)s, %(frame_identifier)s, %(exception_lineno)s);
}

// Attaches locals to frame if any.
%(attach_locals)s

// Release cached frame if used for exception.
if (%(frame_identifier)s == %(frame_cache_identifier)s) {
#if _DEBUG_REFCOUNTS
    count_active_frame_cache_instances -= 1;
    count_released_frame_cache_instances += 1;
#endif

    Py_DECREF(%(frame_cache_identifier)s);
    %(frame_cache_identifier)s = NULL;
}

assertFrameObject(%(frame_identifier)s);

// Put the previous frame back on top.
popFrameStack();

// Return the error.
goto %(parent_exception_exit)s;
"""

# Frame for a module. TODO: Use it for functions called only once.
# TODO: The once guard need not take a reference count in its frame class.
template_frame_guard_once_block = """\
// Frame without reuse.
%(frame_identifier)s = MAKE_MODULE_FRAME(%(code_identifier)s, %(module_identifier)s);

// Push the new frame as the currently active one, and we should be exclusively
// owning it.
pushFrameStack(%(frame_identifier)s);
assert(Py_REFCNT(%(frame_identifier)s) == 2);

// Framed code:
%(codes)s

// Restore frame exception if necessary.
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);
#endif
popFrameStack();

assertFrameObject(%(frame_identifier)s);

goto %(no_exception_exit)s;
"""

template_frame_guard_once_exception_handler = """\
%(frame_exception_exit)s:;
#if %(needs_preserve)d
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);
#endif

if (%(exception_tb)s == NULL) {
    %(exception_tb)s = %(tb_making)s;
} else if (exception_tb->tb_frame != &%(frame_identifier)s->m_frame) {
    %(exception_tb)s = ADD_TRACEBACK(%(exception_tb)s, %(frame_identifier)s, %(exception_lineno)s);
}

// Put the previous frame back on top.
popFrameStack();

// Return the error.
goto %(parent_exception_exit)s;
"""

# Frame in a generator, coroutine or asyncgen.
template_frame_guard_generator = """\
if (isFrameUnusable(%(frame_cache_identifier)s)) {
    Py_XDECREF(%(frame_cache_identifier)s);

#if _DEBUG_REFCOUNTS
    if (%(frame_cache_identifier)s == NULL) {
        count_active_frame_cache_instances += 1;
    } else {
        count_released_frame_cache_instances += 1;
    }
    count_allocated_frame_cache_instances += 1;
#endif
    %(frame_cache_identifier)s = MAKE_FUNCTION_FRAME(%(code_identifier)s, %(module_identifier)s, %(locals_size)s);
#if _DEBUG_REFCOUNTS
} else {
    count_hit_frame_cache_instances += 1;
#endif
}
%(context_identifier)s->m_frame = %(frame_cache_identifier)s;

// Mark the frame object as in use, ref count 1 will be up for reuse.
Py_INCREF(%(context_identifier)s->m_frame);
assert(Py_REFCNT(%(context_identifier)s->m_frame) == 2); // Frame stack

#if PYTHON_VERSION >= 0x340
%(context_identifier)s->m_frame->m_frame.f_gen = (PyObject *)%(context_identifier)s;
#endif

assert(%(context_identifier)s->m_frame->m_frame.f_back == NULL);
Py_CLEAR(%(context_identifier)s->m_frame->m_frame.f_back);

%(context_identifier)s->m_frame->m_frame.f_back = PyThreadState_GET()->frame;
Py_INCREF(%(context_identifier)s->m_frame->m_frame.f_back);

PyThreadState_GET()->frame = &%(context_identifier)s->m_frame->m_frame;
Py_INCREF(%(context_identifier)s->m_frame);

Nuitka_Frame_MarkAsExecuting(%(context_identifier)s->m_frame);

#if PYTHON_VERSION >= 0x300
// Accept currently existing exception as the one to publish again when we
// yield or yield from.
{
    PyThreadState *thread_state = PyThreadState_GET();

    EXC_TYPE_F(%(context_identifier)s) = EXC_TYPE(thread_state);
    if (EXC_TYPE_F(%(context_identifier)s) == Py_None) EXC_TYPE_F(%(context_identifier)s) = NULL;
    Py_XINCREF(EXC_TYPE_F(%(context_identifier)s));
    EXC_VALUE_F(%(context_identifier)s) = EXC_VALUE(thread_state);
    Py_XINCREF(EXC_VALUE_F(%(context_identifier)s));
    EXC_TRACEBACK_F(%(context_identifier)s) = EXC_TRACEBACK(thread_state);
    Py_XINCREF(EXC_TRACEBACK_F(%(context_identifier)s));
}

#endif

// Framed code:
%(codes)s

Nuitka_Frame_MarkAsNotExecuting(%(context_identifier)s->m_frame);

#if PYTHON_VERSION >= 0x300
Py_CLEAR(EXC_TYPE_F(%(context_identifier)s));
Py_CLEAR(EXC_VALUE_F(%(context_identifier)s));
Py_CLEAR(EXC_TRACEBACK_F(%(context_identifier)s));
#endif

// Allow re-use of the frame again.
Py_DECREF(%(context_identifier)s->m_frame);
goto %(no_exception_exit)s;
"""


# TODO: This cannot happen, can it?
template_frame_guard_generator_return_handler = """\
%(frame_return_exit)s:;

#if PYTHON_VERSION >= 0x300
Py_CLEAR(EXC_TYPE_F(%(context_identifier)s));
Py_CLEAR(EXC_VALUE_F(%(context_identifier)s));
Py_CLEAR(EXC_TRACEBACK_F(%(context_identifier)s));
#endif

Py_DECREF(%(frame_identifier)s);
goto %(return_exit)s;
"""


template_frame_guard_generator_exception_handler = """\
%(frame_exception_exit)s:;

// If it's not an exit exception, consider and create a traceback for it.
if (!EXCEPTION_MATCH_GENERATOR(%(exception_type)s)) {
    if (%(exception_tb)s == NULL) {
        %(exception_tb)s = %(tb_making)s;
    } else if (%(exception_tb)s->tb_frame != &%(frame_identifier)s->m_frame) {
        %(exception_tb)s = ADD_TRACEBACK(%(exception_tb)s, %(frame_identifier)s, %(exception_lineno)s);
    }

%(attach_locals)s

    // Release cached frame if used for exception.
    if (%(frame_identifier)s == %(frame_cache_identifier)s) {
#if _DEBUG_REFCOUNTS
        count_active_frame_cache_instances -= 1;
        count_released_frame_cache_instances += 1;
#endif

        Py_DECREF(%(frame_cache_identifier)s);
        %(frame_cache_identifier)s = NULL;
    }

    assertFrameObject(%(frame_identifier)s);
}

#if PYTHON_VERSION >= 0x300
Py_CLEAR(EXC_TYPE_F(%(context_identifier)s));
Py_CLEAR(EXC_VALUE_F(%(context_identifier)s));
Py_CLEAR(EXC_TRACEBACK_F(%(context_identifier)s));
#endif

Py_DECREF(%(frame_identifier)s);

// Return the error.
goto %(parent_exception_exit)s;
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
