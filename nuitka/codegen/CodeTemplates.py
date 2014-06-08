#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code templates one stop access. """

# Wildcard imports are here to centralize the templates for access through one
# module name, this one, they are not used here though.
# pylint: disable=W0401,W0614

from nuitka.Options import isDebug

from .templates.CodeTemplatesCalls import *
from .templates.CodeTemplatesConstants import *
from .templates.CodeTemplatesExceptions import *
from .templates.CodeTemplatesFrames import *
from .templates.CodeTemplatesFunction import *
from .templates.CodeTemplatesGeneratorFunction import *
from .templates.CodeTemplatesIterators import *
from .templates.CodeTemplatesMain import *
from .templates.CodeTemplatesParameterParsing import *
from .templates.CodeTemplatesVariables import *


def enableDebug():
    templates = dict(globals())

    class TemplateWrapper:
        """ Wrapper around templates.

            To better trace and control template usage.

        """
        def __init__(self, name, value):
            self.name = name
            self.value = value

        def __str__(self):
            return self.value

        def __mod__(self, other):
            assert type( other ) is dict, self.name

            for key in other.keys():
                if "%%(%s)" % key not in self.value:
                    from logging import warning

                    warning(
                        "Extra value '%s' provided to template '%s'.",
                        key,
                        self.name
                    )

            return self.value % other

        def split(self, sep):
            return self.value.split( sep )

    from nuitka.__past__ import iterItems

    for template_name, template_value in iterItems(templates):
        # Ignore internal attribute like "__name__" that the module will also
        # have of course.
        if template_name.startswith("_"):
            continue

        if type(template_value) is str:
            globals()[template_name] = TemplateWrapper(
                template_name,
                template_value
            )


if isDebug():
    enableDebug()
