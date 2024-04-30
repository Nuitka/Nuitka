#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to make dill module work for compiled stuff.

"""

from nuitka.Options import shallMakeModule
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginDillWorkarounds(NuitkaPluginBase):
    """This is to make dill module work with compiled methods."""

    plugin_name = "dill-compat"

    plugin_desc = "Required for 'dill' package compatibility."

    @staticmethod
    def isAlwaysEnabled():
        return False

    def createPostModuleLoadCode(self, module):
        full_name = module.getFullName()

        if full_name == "dill" and not shallMakeModule():
            return (
                self.getPluginDataFileContents("dill-postLoad.py"),
                """\
Extending "dill" for compiled types to be pickle-able as well.""",
            )

        if shallMakeModule() and module.isTopModule():
            return (
                """\
import sys
sys.modules[__compiled__.main]._create_compiled_function%(version)s = \
    sys.modules["%(module_name)s-preLoad"]._create_compiled_function%(version)s
sys.modules[__compiled__.main]._create_compiled_function%(version)s.__module__ = \
    __compiled__.main
"""
                % {"module_name": full_name, "version": "2" if str is bytes else "3"},
                """
Extending "dill" for compiled types to be pickle-able as well.""",
            )

    def createPreModuleLoadCode(self, module):
        if shallMakeModule() and module.isTopModule():
            return (
                self.getPluginDataFileContents("dill-postLoad.py"),
                """\
Extending "dill" for compiled types to be pickle-able as well.""",
            )

    @staticmethod
    def getPreprocessorSymbols():
        return {"_NUITKA_PLUGIN_DILL_ENABLED": "1"}

    def getExtraCodeFiles(self):
        return {"DillPlugin.c": self.getPluginDataFileContents("DillPlugin.c")}


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
