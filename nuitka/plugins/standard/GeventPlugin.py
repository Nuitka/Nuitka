#     Copyright 2021, Jorj McKie, mailto:<jorj.x.mckie@outlook.de>
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

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.Utils import getOS


class GeventPlugin(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "gevent"
    plugin_desc = "Required by the gevent package"

    @classmethod
    def isRelevant(cls):
        """One time only check: may this plugin be required?

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        if module_name.hasNamespace("gevent"):
            return True, "everything from gevent"

        return None

    def onModuleSourceCode(self, module_name, source_code):
        """Append a statement to gevent/_config.py."""
        if module_name != "gevent._config":
            return source_code
        source_lines = source_code.splitlines()
        source_lines.append("config.track_greenlet_tree = False")
        self.info("Greenlet tree tracking switched off")
        return "\n".join(source_lines)

    def decideCompilation(self, module_name, source_ref):
        if (
            module_name == "gevent" or module_name.startswith("gevent.")
        ) and getOS() == "Windows":
            return "bytecode"


class GeventPluginDetector(NuitkaPluginBase):
    """Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = GeventPlugin

    @classmethod
    def isRelevant(cls):
        """One time only check: may this plugin be required?

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """This method checks whether gevent is imported.

        Notes:
            Issue a warning if package gevent is encountered.
        Args:
            module: the module object
        Returns:
            None
        """
        if module.getFullName().hasNamespace("gevent"):
            self.warnUnusedPlugin("gevent support.")
