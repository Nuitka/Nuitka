#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Standard plug-in to make enum module work when compiled.

The enum module provides a free function __new__ in class dictionaries to
manual metaclass calls. These become then unbound methods instead of static
methods, due to CPython only checking for plain uncompiled functions.
"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginEnumWorkarounds(NuitkaPluginBase):
    """ This is to make enum module work when compiled with Nuitka.

    """
    plugin_name = "enum_compat"

    @staticmethod
    def createPostModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "enum":
            code = """\
import enum
try:
    enum.Enum.__new__ = staticmethod(enum.Enum.__new__.__func__)
    enum.IntEnum.__new__ = staticmethod(enum.IntEnum.__new__.__func__)
except AttributeError:
    pass
"""
            return code, """\
Monkey patching "enum" for compiled '__new__' methods."""

        return None, None


class NuitkaPluginDetectorEnumWorkarounds(NuitkaPluginBase):
    plugin_name = "enum_compat"

    @staticmethod
    def isRelevant():
        return True

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "enum":
            if "temp_enum_dict['__new__'] = __new__" in source_code:
                self.warnUnusedPlugin("Enum workarounds for compiled code.")

        return source_code
