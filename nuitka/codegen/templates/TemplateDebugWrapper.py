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
""" Nuitka templates can have more checks that the normal '%' operation.

This wraps strings with a class derived from "str" that does more checks.
"""


from nuitka import Options
from nuitka.__past__ import iterItems
from nuitka.Tracing import optimization_logger


def enableDebug(globals_dict):
    templates = dict(globals_dict)

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
            return self.__class__(
                self.name + "+" + other.name, self.value + other.value
            )

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

    for template_name, template_value in iterItems(templates):
        # Ignore internal attribute like "__name__" that the module will also
        # have of course.
        if template_name.startswith("_"):
            continue

        if type(template_value) is str:
            globals_dict[template_name] = TemplateWrapper(template_name, template_value)


def checkDebug(globals_dict):
    if Options.is_debug:
        enableDebug(globals_dict)
