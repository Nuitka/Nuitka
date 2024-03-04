#     Copyright 2024, Jorj McKie, mailto:<jorj.x.mckie@outlook.de> find license text at end of file


""" Details see below in class definition.
"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginEventlet(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "eventlet"
    plugin_desc = "Support for including 'eventlet' dependencies and its need for 'dns' package monkey patching."

    # TODO: Change this to Yaml configuration.

    @staticmethod
    def isAlwaysEnabled():
        return True

    def getImplicitImports(self, module):
        full_name = module.getFullName()

        if full_name == "eventlet":
            yield self.locateModules("dns")
            yield "eventlet.hubs"

        elif full_name == "eventlet.hubs":
            yield "eventlet.hubs.epolls"
            yield "eventlet.hubs.hub"
            yield "eventlet.hubs.kqueue"
            yield "eventlet.hubs.poll"
            yield "eventlet.hubs.pyevent"
            yield "eventlet.hubs.selects"
            yield "eventlet.hubs.timer"

    def decideCompilation(self, module_name):
        if module_name.hasNamespace("dns"):
            return "bytecode"


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
