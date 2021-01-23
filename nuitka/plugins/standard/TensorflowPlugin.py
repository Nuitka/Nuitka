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


class TensorflowPlugin(NuitkaPluginBase):
    """This class represents the main logic of the plugin.

    This is a plugin to ensure tensorflow scripts compile and work well in
    standalone mode.

    This plugin copies any files required by tensorflow installations.

    Args:
        NuitkaPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "tensorflow"
    plugin_desc = "Required by the tensorflow package"

    def __init__(self):
        """Maintain switch to ensure once-only copy of tensorflow files."""
        self.files_copied = False
        return None

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        for candidate in ("tensor", "google"):
            if module_name.hasNamespace(candidate):
                return True, "Accept everything from %s" % candidate

    def onModuleSourceCode(self, module_name, source_code):
        """Neutralize some path magic in tensorflow.

        Notes:
            Make sure tensorflow understands, we are not running as a PIP
            installed application.
        """
        if module_name != "tensorflow":
            return source_code
        source_lines = source_code.splitlines()
        found_insert = False
        for i, l in enumerate(source_lines):
            if l.startswith("def ") and "_running_from_pip_package():" in l:
                source_lines.insert(i, "_site_packages_dirs = []")
                source_lines.insert(i, "from tensorflow.python import keras")
                found_insert = True
                break

        if found_insert is True:
            self.info("Patched 'running-from-pip' path magic.")
        else:
            self.sysexit("Did not find path magic code." % self.plugin_name)

        return "\n".join(source_lines)

    def decideCompilation(self, module_name, source_ref):
        """Include major packages as bytecode.

        Notes:
            Tensorflow is a very large package and mainly used to interactively
            create the actual application. Therefore, compilation makes no
            sense for it and the packages it references.
        """
        elements = module_name.split(".")
        if elements[0] in (
            "tensor",
            "boto",
            "google",
            "keras",
            "sklearn",
            "pandas",
            "matplotlib",
        ):
            return "bytecode"
        else:
            return "compiled"


class TensorflowPluginDetector(NuitkaPluginBase):
    """Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = TensorflowPlugin

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """This method checks whether a tensorflow module is imported.

        Notes:
            For this we check whether its full name contains the string "tensorflow".
        Args:
            module: the module object
        Returns:
            None
        """
        if module.getFullName().hasNamespace("tensorflow"):
            self.warnUnusedPlugin("tensorflow support.")
