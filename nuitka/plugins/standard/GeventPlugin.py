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
import os
from logging import info
from nuitka import Options
from nuitka.plugins.PluginBase import UserPluginBase


class GeventPlugin(UserPluginBase):
    """ This class represents the main logic of the plugin.
    """

    plugin_name = "gevent"

    def __init__(self):
        """ Maintain any switches etc.
        """
        self.files_copied = False
        return None

    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        if module_package:
            # the standard case:
            full_name = module_package + "." + module_name

            # also happens: module_name = package.module
            # then use module_name as the full_name
            if module_name.startswith(module_package):
                t = module_name[len(module_package) :]
                if t.startswith("."):
                    full_name = module_name
            # also happens: package = a.b.c.module
            # then use package as full_name
            elif module_package.endswith(module_name):
                full_name = module_package
        else:
            full_name = module_name

        if full_name.startswith("gevent"):
            return True, "everything from gevent"

        return None

    def onModuleSourceCode(self, module_name, source_code):
        """ This method passes the source code and expects it back - potentially modified.
        """

        return source_code

    def decideCompilation(self, module_name, source_ref):
        if module_name.startswith("gevent"):
            return "bytecode"


class GeventPluginDetector(UserPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "gevent"  # Nuitka knows us by this name

    @staticmethod
    def isRelevant():
        """ This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """ This method checks whether gevent is imported.

        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName()
        if full_name.startswith("gevent"):
            self.warnUnusedPlugin("gevent support.")
