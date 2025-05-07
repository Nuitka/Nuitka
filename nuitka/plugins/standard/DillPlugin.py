#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to make dill module work for compiled stuff.

"""

from nuitka.Options import shallMakeModule
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginDillWorkarounds(NuitkaPluginBase):
    """This is to make dill module work with compiled methods."""

    plugin_name = "dill-compat"
    plugin_desc = "Required for 'dill' package and 'cloudpickle' compatibility."
    plugin_category = "package-support"

    pickle_package_names = ("dill", "cloudpickle", "ray")

    @staticmethod
    def isAlwaysEnabled():
        return False

    def __init__(self, pickle_supported_modules):
        self.pickle_supported_modules = pickle_supported_modules or ["all"]

        self.pickle_selected_packages = [
            self._getPickleSupportPackageName(pickle_package_name)
            for pickle_package_name in self.pickle_package_names
            if self.shallIncludePickleSupportModule(pickle_package_name)
        ]

    def shallIncludePickleSupportModule(self, name):
        return (
            name in self.pickle_supported_modules
            or "all" in self.pickle_supported_modules
        )

    @staticmethod
    def _getPickleSupportPackageName(name):
        if name == "ray":
            return "ray.cloudpickle"

        return name

    def _getPostLoadCode(self, name):
        if name == "ray.cloudpickle":
            result = self._getPostLoadCode("cloudpickle")

            assert "import cloudpickle" in result
            result = result.replace(
                "import cloudpickle", "import ray.cloudpickle as cloudpickle"
            )
            return result

        return self.getPluginDataFileContents("%s-postLoad.py" % name)

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--include-pickle-support-module",
            action="append",
            dest="pickle_supported_modules",
            choices=("all",) + cls.pickle_package_names,
            default=[],
            help="""\
Include support for these modules to pickle nested compiled functions. You
can use "all" which is the default, but esp. in module mode, just might
want to limit yourself to not create unnecessary run-time usages. For
standalone mode, you can leave it at the default, at it will detect
the usage.""",
        )

    def createPostModuleLoadCode(self, module):
        full_name = module.getFullName()

        if not shallMakeModule():
            for candidate in self.pickle_selected_packages:
                if full_name == candidate:
                    return (
                        self._getPostLoadCode(candidate),
                        """\
Extending "%s" for compiled types to be pickle-able as well."""
                        % candidate,
                    )
        elif module.isTopModule():
            return (
                """\
import sys
sys.modules[__compiled__.main]._create_compiled_function = \
    sys.modules[__name__.replace("-postLoad", "-preLoad")]._create_compiled_function
sys.modules[__compiled__.main]._create_compiled_function.__module__ = \
    __compiled__.main
""",
                """
Extending for compiled types to be pickle-able as well.""",
            )

    def createPreModuleLoadCode(self, module):
        if shallMakeModule() and module.isTopModule():
            for candidate in self.pickle_selected_packages:
                if self.shallIncludePickleSupportModule(candidate):
                    yield (
                        self._getPostLoadCode(candidate),
                        """\
Extending "%s" for compiled types to be pickle-able as well.""",
                    )

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        if module_name.hasOneOfNamespaces(*self.pickle_selected_packages):
            return True, "Needed to handle %s" % module_name.getTopLevelPackageName()

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
