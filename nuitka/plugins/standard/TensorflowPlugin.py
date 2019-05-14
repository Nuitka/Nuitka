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
import pkgutil
import shutil
from logging import info
from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.Utils import isWin32Windows


def get_module_file_attribute(package):
    """ Get the absolute path of the module with the passed-in name.

    Args:
        package: the fully-qualified name of this module.
    Returns:
        absolute path of this module.
    """
    loader = pkgutil.find_loader(package)
    attr = loader.get_filename(package)
    if not attr:
        raise ImportError
    return os.path.dirname(attr)


class TensorflowPlugin(NuitkaPluginBase):
    """ This class represents the main logic of the plugin.

    This is a plugin to ensure tensorflow scripts compile and work well in
    standalone mode.

    This plugin copies any files required by tensorflow installations.

    Args:
        NuitkaPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "tensorflow"
    plugin_desc = "Required by the tensorflow package"

    def __init__(self):
        """ Maintain switch to ensure once-only copy of tensorflow files.
        """
        self.files_copied = False
        return None

    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        if module_package is not None:
            full_name = module_package + "." + module_name
        else:
            full_name = module_name

        if full_name.startswith("tensor"):
            return True, "accept everything"

    def considerExtraDlls(self, dist_dir, module):
        """ Copy tensorflow.datasets folders to the dist folder.

        Notes:

        Args:
            dist_dir: the name of the program's dist folder
            module: the module object (not used here)

        Returns:
            None
        """
        if self.files_copied:
            return ()
        if not module.getFullName() == "tensorflow.datasets":
            return ()
        self.files_copied = True
        info(" ***** tensorflow datasets need to be copied ...!")

        return ()

    def decideCompilation(self, module_name, source_ref):
        if module_name.startswith(("tensor", "boto")):
            return "bytecode"

    def getImplicitImports(self, module):
        full_name = module.getFullName()

        if full_name == "tensorflow":
            yield "tensorflow._api", True
            yield "tensorflow.python", True

        elif full_name == "tensorflow._api":
            yield "tensorflow._api.v1.app", True
            yield "tensorflow._api.v1.audio", True
            yield "tensorflow._api.v1.autograph", True
            yield "tensorflow._api.v1.bitwise", True
            yield "tensorflow._api.v1.compat", True
            yield "tensorflow._api.v1.config", True
            yield "tensorflow._api.v1.data", True
            yield "tensorflow._api.v1.debugging", True
            yield "tensorflow._api.v1.distribute", True
            yield "tensorflow._api.v1.distributions", True
            yield "tensorflow._api.v1.dtypes", True
            yield "tensorflow._api.v1.errors", True
            yield "tensorflow._api.v1.experimental", True
            yield "tensorflow._api.v1.feature_column", True
            yield "tensorflow._api.v1.gfile", True
            yield "tensorflow._api.v1.graph_util", True
            yield "tensorflow._api.v1.image", True
            yield "tensorflow._api.v1.initializers", True
            yield "tensorflow._api.v1.io", True
            yield "tensorflow._api.v1.layers", True
            yield "tensorflow._api.v1.linalg", True
            yield "tensorflow._api.v1.lite", True
            yield "tensorflow._api.v1.logging", True
            yield "tensorflow._api.v1.lookup", True
            yield "tensorflow._api.v1.losses", True
            yield "tensorflow._api.v1.manip", True
            yield "tensorflow._api.v1.math", True
            yield "tensorflow._api.v1.metrics", True
            yield "tensorflow._api.v1.nest", True
            yield "tensorflow._api.v1.nn", True
            yield "tensorflow._api.v1.profiler", True
            yield "tensorflow._api.v1.python_io", True
            yield "tensorflow._api.v1.quantization", True
            yield "tensorflow._api.v1.queue", True
            yield "tensorflow._api.v1.ragged", True
            yield "tensorflow._api.v1.random", True
            yield "tensorflow._api.v1.raw_ops", True
            yield "tensorflow._api.v1.resource_loader", True
            yield "tensorflow._api.v1.saved_model", True
            yield "tensorflow._api.v1.sets", True
            yield "tensorflow._api.v1.signal", True
            yield "tensorflow._api.v1.sparse", True
            yield "tensorflow._api.v1.spectral", True
            yield "tensorflow._api.v1.strings", True
            yield "tensorflow._api.v1.summary", True
            yield "tensorflow._api.v1.sysconfig", True
            yield "tensorflow._api.v1.test", True
            yield "tensorflow._api.v1.tpu", True
            yield "tensorflow._api.v1.train", True
            yield "tensorflow._api.v1.user_ops", True
            yield "tensorflow._api.v1.version", True
            yield "tensorflow._api.v1.xla", True

        elif full_name == "tensorflow.lite.python.lite":
            yield "tensorflow.python.framework.importer", True

        elif full_name == "tensorflow.python":
            yield "tensorflow.python.pywrap_tensorflow", True
            yield "tensorflow.python._pywrap_tensorflow_internal", True
            yield "tensorflow.python.tools.module_util", True


class TensorflowPluginDetector(NuitkaPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "tensorflow"  # Nuitka knows us by this name

    @staticmethod
    def isRelevant():
        """ This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """ This method checks whether a tensorflow module is imported.

        Notes:
            For this we check whether its full name contains the string "tensorflow".
        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName().split(".")
        if "tensorflow" in full_name:
            self.warnUnusedPlugin("tensorflow support.")
