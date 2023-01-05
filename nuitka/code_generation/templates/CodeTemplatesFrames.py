#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

template_frame_guard_normal_main_block = """\
{% if frame_cache_identifier %}
if (isFrameUnusable({{frame_cache_identifier}})) {
    Py_XDECREF({{frame_cache_identifier}});

#if _DEBUG_REFCOUNTS
    if ({{frame_cache_identifier}} == NULL) {
        count_active_frame_cache_instances += 1;
    } else {
        count_released_frame_cache_instances += 1;
    }
    count_allocated_frame_cache_instances += 1;
#endif
    {{frame_cache_identifier}} = {{make_frame_code}};
#if _DEBUG_REFCOUNTS
} else {
    count_hit_frame_cache_instances += 1;
#endif
}
assert({{frame_cache_identifier}}->m_type_description == NULL);
{{frame_identifier}} = {{frame_cache_identifier}};
{% else %}
{{frame_identifier}} = {{make_frame_code}};
{% endif %}
{% if frame_init_code %}
{{frame_init_code}}
{% endif %}
{% if context_identifier and is_python34_or_later %}
Nuitka_SetFrameGenerator({{context_identifier}}->m_frame, (PyObject *){{context_identifier}});
{% endif %}

// Push the new frame as the currently active one, and we should be exclusively
// owning it.
pushFrameStack({{frame_identifier}});
assert(Py_REFCNT({{frame_identifier}}) == 2);

// Framed code:
{{codes}}

{% if needs_preserve %}
// Restore frame exception if necessary.
RESTORE_FRAME_EXCEPTION({{frame_identifier}});
{% endif %}

// Put the previous frame back on top.
popFrameStack();
{% if frame_exit_code %}
{{frame_exit_code}}
{% endif %}

goto {{no_exception_exit}};
"""

template_frame_guard_normal_return_handler = """\
{{frame_return_exit}}:
{% if needs_preserve %}
RESTORE_FRAME_EXCEPTION({{frame_identifier}});
{% endif %}

// Put the previous frame back on top.
popFrameStack();
{% if frame_exit_code %}
{{frame_exit_code}}s
{% endif %}

goto {{return_exit}};
"""

template_frame_attach_locals = """\
Nuitka_Frame_AttachLocals(
    %(frame_identifier)s,
    %(type_description)s%(frame_variable_refs)s
);
"""

template_frame_guard_normal_exception_handler = """\
{{frame_exception_exit}}:

{% if needs_preserve %}
RESTORE_FRAME_EXCEPTION({{frame_identifier}});
{% endif %}

if ({{exception_tb}} == NULL) {
    {{exception_tb}} = {{tb_making_code}};
} else if ({{exception_tb}}->tb_frame != &{{frame_identifier}}->m_frame) {
    {{exception_tb}} = ADD_TRACEBACK({{exception_tb}}, {{frame_identifier}}, {{exception_lineno}});
}

{% if attach_locals_code %}
// Attaches locals to frame if any.
{{attach_locals_code}}
{% endif %}

{% if frame_cache_identifier %}
// Release cached frame if used for exception.
if ({{frame_identifier}} == {{frame_cache_identifier}}) {
#if _DEBUG_REFCOUNTS
    count_active_frame_cache_instances -= 1;
    count_released_frame_cache_instances += 1;
#endif
    Py_DECREF({{frame_cache_identifier}});
    {{frame_cache_identifier}} = NULL;
}
{% endif %}

assertFrameObject({{frame_identifier}});

// Put the previous frame back on top.
popFrameStack();
{% if frame_exit_code %}
{{frame_exit_code}}
{% endif %}

// Return the error.
goto {{parent_exception_exit}};
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
Nuitka_SetFrameGenerator(%(context_identifier)s->m_frame, (PyObject *)%(context_identifier)s);
#endif

assert(%(context_identifier)s->m_frame->m_frame.f_back == NULL);

pushFrameStack(%(context_identifier)s->m_frame);

// Taking a reference prevents reuse of generator frame while it is being used.
Py_INCREF(%(context_identifier)s->m_frame->m_frame.f_back);

#if PYTHON_VERSION >= 0x300
// Store currently existing exception as the one to publish again when we
// yield or yield from.
STORE_%(generator_kind)s_EXCEPTION(%(context_identifier)s);
#endif

// Framed code:
%(codes)s

Nuitka_Frame_MarkAsNotExecuting(%(context_identifier)s->m_frame);

#if PYTHON_VERSION >= 0x300
// Release exception attached to the frame
DROP_%(generator_kind)s_EXCEPTION(%(context_identifier)s);
#endif

// Allow re-use of the frame again.
Py_DECREF(%(context_identifier)s->m_frame);
goto %(no_exception_exit)s;
"""


# Coroutines and asyncgen do this
template_frame_guard_generator_return_handler = """\
%(frame_return_exit)s:;

#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION < 0x3b0
Py_CLEAR(EXC_TYPE_F(%(context_identifier)s));
#endif
Py_CLEAR(EXC_VALUE_F(%(context_identifier)s));
#if PYTHON_VERSION < 0x3b0
Py_CLEAR(EXC_TRACEBACK_F(%(context_identifier)s));
#endif
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
#if PYTHON_VERSION < 0x3b0
Py_CLEAR(EXC_TYPE_F(%(context_identifier)s));
#endif
Py_CLEAR(EXC_VALUE_F(%(context_identifier)s));
#if PYTHON_VERSION < 0x3b0
Py_CLEAR(EXC_TRACEBACK_F(%(context_identifier)s));
#endif
#endif

Py_DECREF(%(frame_identifier)s);

// Return the error.
goto %(parent_exception_exit)s;
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
