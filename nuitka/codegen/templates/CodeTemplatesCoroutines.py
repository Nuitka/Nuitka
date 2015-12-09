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
""" Coroutines function (await/async) related templates.

"""

template_make_coroutine_without_context_template = """
%(to_name)s = Nuitka_Coroutine_New(
    %(coroutine_identifier)s_context,
    self->m_name,
    self->m_qualname,
    %(code_identifier)s,
    NULL,
    0
);
"""

template_make_coroutine_with_context_template = """
{
%(closure_making)s

    %(to_name)s = Nuitka_Coroutine_New(
        %(coroutine_identifier)s_context,
        self->m_name,
        self->m_qualname,
        %(code_identifier)s,
        closure,
        %(closure_count)d
    );
}
"""

template_coroutine_await = """
{
    PyObject *awaitable = _PyCoro_GetAwaitableIter( %(value)s );

    if (likely( awaitable != NULL ))
    {
        %(to_name) = COROUTINE_AWAIT( awaitable );
    }
    else
    {
        %(to_name) = NULL;
    }
}
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
