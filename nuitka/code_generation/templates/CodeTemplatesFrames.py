#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code templates for frames of all kinds."""

# This uses STORE_GENERATOR_EXCEPTION,STORE_COROUTINE_EXCEPTION,STORE_ASYNCGEN_EXCEPTION

template_frame_guard_normal_main_block = """\
{
{% if frame_cache_identifier %}
struct Nuitka_FrameCacheHandle *{{cache_claim_identifier}};

{{cache_claim_identifier}} = Nuitka_FrameCache_Take(&{{frame_cache_identifier}}, &{{frame_identifier}});

if ({{cache_claim_identifier}} == NULL) {
    // Another call owns the cache, use an uncached frame for this call.
    {{frame_identifier}} = {{make_frame_code}};
} else if ({{frame_identifier}} == NULL) {
    {{frame_identifier}} = {{make_frame_code}};
    Nuitka_FrameCache_Attach({{cache_claim_identifier}}, {{frame_identifier}});
}
{% else %}
{{frame_identifier}} = {{make_frame_code}};
{% endif %}
{% if frame_init_code %}
{{frame_init_code}}
{% endif %}
{% if context_identifier %}
{% if frame_cache_identifier %}
// The generator owns a reference only when it claimed the cache. For an
// uncached frame, the initial reference already belongs to the generator.
if ({{cache_claim_identifier}} != NULL) {
    Py_INCREF({{context_identifier}}->m_frame);
}
{% endif %}

{% if is_python3 %}
Nuitka_SetFrameGenerator({{context_identifier}}->m_frame, (PyObject *){{context_identifier}});
{% endif %}

assert({{context_identifier}}->m_frame->m_frame.f_back == NULL);
{% endif %}

// Push the new frame as the currently active one, and we should be exclusively
// owning it.
{% if context_identifier %}
pushFrameStackGeneratorCompiledFrame(tstate, {{frame_identifier}});
{% else %}
pushFrameStackCompiledFrame(tstate, {{frame_identifier}});
{% endif %}
{% if context_identifier and frame_cache_identifier %}
assert(Py_REFCNT({{frame_identifier}}) == ({{cache_claim_identifier}} != NULL ? 2 : 1));
{% else %}
assert(Py_REFCNT({{frame_identifier}}) == 2);
{% endif %}

{% if context_identifier and is_python3 %}
// Store currently existing exception as the one to publish again when we
// yield or yield from.
STORE_{{context_identifier.upper()}}_EXCEPTION(tstate, {{context_identifier}});

{% endif %}
// Framed code:
{{codes}}

{% if context_identifier and is_python3 %}
// Release exception attached to the frame
DROP_{{context_identifier.upper()}}_EXCEPTION({{context_identifier}});

{% endif %}
{% if needs_preserve %}
// Restore frame exception if necessary.
RESTORE_FRAME_EXCEPTION(tstate, {{frame_identifier}});
{% endif %}

{% if not context_identifier %}
{% if frame_exit_code %}
{{frame_exit_code}}
{% endif %}
// Put the previous frame back on top.
popFrameStack(tstate);
{% if frame_cache_identifier %}
Nuitka_FrameCache_Return({{frame_identifier}});
{% endif %}
{% endif %}

goto {{no_exception_exit}};
}
"""

template_frame_guard_normal_return_handler = """\
{{frame_return_exit}}:
{% if needs_preserve %}
RESTORE_FRAME_EXCEPTION(tstate, {{frame_identifier}});
{% endif %}

{% if frame_exit_code %}
{{frame_exit_code}}
{% endif %}
// Put the previous frame back on top.
popFrameStack(tstate);
{% if frame_cache_identifier %}
Nuitka_FrameCache_Return({{frame_identifier}});
{% endif %}

goto {{return_exit}};
"""

template_frame_attach_locals = """\
Nuitka_Frame_AttachLocals(
    %(frame_identifier)s
);
"""

template_frame_guard_normal_exception_handler = """\
{{frame_exception_exit}}:

{% if needs_preserve %}
RESTORE_FRAME_EXCEPTION(tstate, {{frame_identifier}});
{% endif %}

{
    PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(&{{exception_state_name}});
    if (exception_tb == NULL) {
        exception_tb = {{tb_making_code}};
        SET_EXCEPTION_STATE_TRACEBACK(&{{exception_state_name}}, exception_tb);
    } else if (exception_tb->tb_frame != &{{frame_identifier}}->m_frame) {
        exception_tb = ADD_TRACEBACK(exception_tb, {{frame_identifier}}, {{exception_lineno}});
        SET_EXCEPTION_STATE_TRACEBACK(&{{exception_state_name}}, exception_tb);
    }
}

{% if attach_locals_code %}
// Attaches locals to frame if any.
{{attach_locals_code}}
{% endif %}

{% if frame_cache_identifier %}
// Release the cache reference or the call's own reference. The traceback
// keeps the frame alive.
Nuitka_FrameCache_DropCall({{frame_identifier}});
{% endif %}

assertFrameObject({{frame_identifier}});

// Put the previous frame back on top.
popFrameStack(tstate);

// Return the error.
goto {{parent_exception_exit}};
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

goto %(return_exit)s;
"""


template_frame_guard_generator_exception_handler = """\
{{frame_exception_exit}}:;

// If it's not an exit exception, consider and create a traceback for it.
if (!EXCEPTION_STATE_MATCH_GENERATOR(tstate, &{{exception_state_name}})) {
    PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(&{{exception_state_name}});
    if (exception_tb == NULL) {
        exception_tb = {{tb_making}};
        SET_EXCEPTION_STATE_TRACEBACK(&{{exception_state_name}}, exception_tb);
    } else if (({{exception_lineno}} != 0) && (exception_tb->tb_frame != &{{frame_identifier}}->m_frame)) {
        exception_tb = ADD_TRACEBACK(exception_tb, {{frame_identifier}}, {{exception_lineno}});
        SET_EXCEPTION_STATE_TRACEBACK(&{{exception_state_name}}, exception_tb);
    }

{{attach_locals}}

{% if frame_cache_identifier %}
    // Release the cache reference; the generator keeps its own reference.
    Nuitka_FrameCache_DropCache({{frame_identifier}});
{% endif %}

    assertFrameObject({{frame_identifier}});
}

{% if is_python3 %}
// Release exception attached to the frame
DROP_{{context_identifier.upper()}}_EXCEPTION({{context_identifier}});

{% endif %}

// Return the error.
goto {{parent_exception_exit}};
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())

#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
