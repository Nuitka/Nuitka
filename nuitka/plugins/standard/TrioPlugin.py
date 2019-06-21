#     Copyright 2019, Jorj McKie, mailto:<jorj.x.mckie@outlook.de>
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
""" Details see below in class definition.
"""
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase


class GeventPlugin(NuitkaPluginBase):
    """ This class represents the main logic of the plugin.
    """

    plugin_name = "trio"
    plugin_desc = "Required by the trio package"

    def onModuleSourceCode(self, module_name, source_code):
        """

        """
        if not module_name == "trio":
            return source_code

        source_lines = source_code.splitlines()
        new_lines = []
        for l in source_lines:
            l = l.replace("from . ", "from trio ")
            l = l.replace("from .", "from trio.")
            new_lines.append(l)

        return "\n".join(new_lines)


class GeventPluginDetector(NuitkaPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "trio"

    @staticmethod
    def isRelevant():
        """ One time only check: may this plugin be required?

        Returns:
            True if this is a standalone compilation.
        """
        return True

    def onModuleDiscovered(self, module):
        """ This method checks whether gevent is imported.

        Notes:
            Issue a warning if package gevent is encountered.
        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName()
        if full_name.startswith("trio"):
            self.warnUnusedPlugin("trio support.")
