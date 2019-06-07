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
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import copyTree
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


class SklearnPlugin(NuitkaPluginBase):
    """ This class represents the main logic of the plugin.

    This is a plugin to ensure sklearn scripts compile and work well in
    standalone mode.

    This plugin copies any files required by sklearn installations.

    Args:
        NuitkaPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "sklearn"
    plugin_desc = "Required by the scikit-learn package"

    def __init__(self):
        """ Maintain switch to ensure once-only copy of sklearn files.
        """
        self.files_copied = False
        return None

    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        if module_package == "sklearn.utils.sparsetools" and module_name in (
            "_graph_validation",
            "_graph_tools",
        ):
            return True, "Needed by sklearn"

        if module_package == "sklearn.utils" and module_name in (
            "lgamma",
            "weight_vector",
            "_unittest_backport",
        ):
            return True, "Needed by sklearn"

        posix = (
            "managers",
            "synchronize",
            "compat_posix",
            "_posix_reduction",
            "popen_loky_posix",
        )
        win32 = (
            "managers",
            "synchronize",
            "_win_wait",
            "_win_reduction",
            "popen_loky_win32",
        )

        if isWin32Windows():
            valid_list = win32
        else:
            valid_list = posix

        if (
            module_package == "sklearn.externals.joblib.externals.loky.backend"
            and module_name in valid_list
        ):
            return True, "Needed by sklearn"

        if (
            module_package == "sklearn.externals.joblib.externals.cloudpickle"
            and module_name == "dumps"
        ):
            return True, "Needed by sklearn"

    def considerExtraDlls(self, dist_dir, module):
        """ Copy sklearn.datasets folders to the dist folder.

        Notes:

        Args:
            dist_dir: the name of the program's dist folder
            module: the module object (not used here)

        Returns:
            None
        """
        if self.files_copied:
            return ()
        if not module.getFullName() == "sklearn.datasets":
            return ()
        self.files_copied = True

        sklearn_dir = get_module_file_attribute("sklearn")
        source_data = os.path.join(sklearn_dir, "datasets", "data")
        target_data = os.path.join(dist_dir, "sklearn", "datasets", "data")
        source_descr = os.path.join(sklearn_dir, "datasets", "descr")
        target_descr = os.path.join(dist_dir, "sklearn", "datasets", "descr")
        info("")
        info(" Copying folder sklearn/datasets/data")
        copyTree(source_data, target_data)
        info(" Copying folder sklearn/datasets/descr")
        copyTree(source_descr, target_descr)

        return ()

    def suppressBuiltinImportWarning(self, module, source_ref):
        """ Whether to suppress import warnings for modules.

        Notes:
            Suppress messages "Unresolved '__import__' at ..."
        Args:
            module: the module object
            source_ref: source of module with line number
        Returns:
            True or False
        """
        if module.getFullName().startswith("sklearn"):
            return True

        return False


class SklearnPluginDetector(NuitkaPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "sklearn"  # Nuitka knows us by this name

    @staticmethod
    def isRelevant():
        """ This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """ This method checks whether a sklearn module is imported.

        Notes:
            For this we check whether its full name contains the string "sklearn".
        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName().split(".")
        if "sklearn" in full_name:
            self.warnUnusedPlugin("sklearn support.")
