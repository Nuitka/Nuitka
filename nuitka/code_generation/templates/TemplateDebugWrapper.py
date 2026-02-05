#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nuitka templates can have more checks that the normal '%' operation.

This wraps strings with a class derived from "str" that does more checks.
"""

from nuitka.__past__ import iterItems
from nuitka.States import states
from nuitka.Tracing import optimization_logger


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
    if states.is_debug:
        enableDebug(globals_dict)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
