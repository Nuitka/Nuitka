#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nuitka templates can have more checks that the normal '%' operation.

This wraps strings with a class derived from "str" that does more checks.
"""

import hashlib

from nuitka.__past__ import iterItems
from nuitka.code_generation.Emission import getCodeString
from nuitka.States import states
from nuitka.Tracing import optimization_logger


def _getTemplateHash(value):
    if type(value) is not bytes:
        value = value.encode("utf8")

    return hashlib.sha256(value).hexdigest()


class TemplateWrapper(object):
    """Wrapper around templates.

    To better trace and control template usage.

    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return self.value

    def __add__(self, other):
        return self.__class__(self.name + "+" + other.name, self.value + other.value)

    def __mod__(self, other):
        assert type(other) is dict, self.name

        for key in other.keys():
            if "%%(%s)" % key not in self.value:
                optimization_logger.warning(
                    "Extra value %r provided to template %r." % (key, self.name)
                )

        try:
            return self.value % other
        except KeyError as e:
            raise KeyError(self.name, *e.args)

    def split(self, sep):
        return self.value.split(sep)


class PreparedTemplate(object):
    """Wrapper around generated template emitter code."""

    def __init__(
        self, name, value, template_hash, variables, emit_func, readable_emit_func
    ):
        self.name = name
        self.value = value
        self.template_hash = template_hash
        self.variables = variables
        self.emit_func = emit_func
        self.readable_emit_func = readable_emit_func

        if _getTemplateHash(value) != template_hash:
            raise AssertionError(
                "Generated template code for %r is out of date." % name
            )

    def __str__(self):
        return self.value

    def __add__(self, other):
        return self.value + str(other)

    def __radd__(self, other):
        return str(other) + self.value

    def _checkValues(self, values):
        assert type(values) is dict, self.name

        for key in values.keys():
            if key not in self.variables:
                optimization_logger.warning(
                    "Extra value %r provided to template %r." % (key, self.name)
                )

    def __mod__(self, other):
        if states.is_debug:
            self._checkValues(other)
        else:
            assert type(other) is dict, self.name

        try:
            return self.value % other
        except KeyError as e:
            raise KeyError(self.name, *e.args)

    def render(self, values):
        result = []

        self.emit(result.append, values)

        return "".join(getCodeString(value) for value in result)

    def emit(self, emit, values):
        if states.is_debug:
            self._checkValues(values)
        else:
            assert type(values) is dict, self.name

        try:
            if states.is_readable_code:
                emit_func = self.readable_emit_func
            else:
                emit_func = self.emit_func

            emit_func(emit, values)
        except KeyError as e:
            raise KeyError(self.name, *e.args)

    def __call__(self, emit, values):
        self.emit(emit, values)

    def split(self, sep):
        return self.value.split(sep)


def _getGeneratedTemplateInfos():
    try:
        from .CodeTemplatesGenerated import template_infos
    except ImportError:
        return {}
    else:
        return template_infos


def enablePrepared(globals_dict):
    template_infos = _getGeneratedTemplateInfos()
    module_name = globals_dict["__name__"]

    for template_name, template_value in iterItems(dict(globals_dict)):
        if not template_name.startswith("template_") or type(template_value) is not str:
            continue

        template_key = "%s.%s" % (module_name, template_name)

        if template_key not in template_infos:
            continue

        template_info = template_infos[template_key]

        if len(template_info) == 3:
            template_hash, variables, emit_func = template_info
            readable_emit_func = emit_func
        else:
            template_hash, variables, emit_func, readable_emit_func = template_info

        globals_dict[template_name] = PreparedTemplate(
            name=template_key,
            value=template_value,
            template_hash=template_hash,
            variables=variables,
            emit_func=emit_func,
            readable_emit_func=readable_emit_func,
        )


def emitTemplate(template, emit, values):
    if hasattr(template, "emit") and hasattr(emit, "emitTemplate"):
        emit.emitTemplate(template, values)
    elif hasattr(template, "render"):
        emit(template.render(values))
    else:
        emit(template % values)


def enableDebug(globals_dict):
    templates = dict(globals_dict)

    for template_name, template_value in iterItems(templates):
        # Ignore internal attribute like "__name__" that the module will also
        # have of course.
        if template_name.startswith("_"):
            continue

        if type(template_value) is str and "{%" not in template_value:
            globals_dict[template_name] = TemplateWrapper(template_name, template_value)


def checkDebug(globals_dict):
    enablePrepared(globals_dict)

    if states.is_debug:
        enableDebug(globals_dict)


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
