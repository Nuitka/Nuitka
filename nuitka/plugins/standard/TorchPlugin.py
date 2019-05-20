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
    return attr


def get_torch_core_binaries():
    """ Return required files from the torch folders.

    Notes:
        So far only tested for Windows. Requirements for other platforms
        are unknown.
    """
    binaries = []

    extras = os.path.join(os.path.dirname(get_module_file_attribute("torch")), "lib")

    if os.path.isdir(extras):
        for f in os.listdir(extras):
            # apart from shared libs, also the C header files are required!
            if f.endswith((".dll", ".so", ".h")) or ".so." in f:
                item = os.path.join(extras, f)
                if os.path.isfile(item):
                    binaries.append((item, "."))

    # this folder exists in the Linux version
    extras = os.path.join(os.path.dirname(get_module_file_attribute("torch")), "bin")

    if os.path.isdir(extras):
        for f in os.listdir(extras):
            item = os.path.join(extras, f)
            if os.path.isfile(item):
                binaries.append((item, "."))

    # this folder exists in the Linux version
    extras = os.path.join(
        os.path.dirname(get_module_file_attribute("torch")), "include"
    )

    if os.path.isdir(extras):
        for root, _, files in os.walk(extras):
            for f in files:
                item = os.path.join(root, f)
                if os.path.isfile(item):
                    binaries.append((item, "."))

    return binaries


class TorchPlugin(NuitkaPluginBase):
    """ This class represents the main logic of the plugin.

    This is a plugin to ensure torch scripts compile and work well in
    standalone mode.

    This plugin copies any files required by torch installations.

    Args:
        NuitkaPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "torch"
    plugin_desc = "Required by the torch / torchvision packages"

    def __init__(self):
        """ Maintain switch to ensure once-only copy of torch/lib files.
        """
        self.files_copied = False
        return None

    def considerExtraDlls(self, dist_dir, module):
        """ Copy extra files from torch/lib.

        Args:
            dist_dir: the name of the script's dist folder
            module: module object (not used here)
        Returns:
            empty tuple
        """
        if self.files_copied is True:  # not the first time here
            return ()

        if module.getFullName() == "torch":
            self.files_copied = True  # fall thru next time
            binaries = get_torch_core_binaries()
            bin_total = len(binaries)
            if bin_total == 0:
                return ()
            info("")
            info(" Copying files from 'torch/lib' and 'torch/bin':")
            for f in binaries:
                bin_file = f[0].lower()  # full binary file name
                idx = bin_file.find("torch")  # this will always work (idx > 0)
                back_end = bin_file[idx:]  # tail of the string
                tar_file = os.path.join(dist_dir, back_end)

                # create any missing intermediate folders
                if not os.path.exists(os.path.dirname(tar_file)):
                    os.makedirs(os.path.dirname(tar_file))

                shutil.copy(bin_file, tar_file)

            msg = " Copied %i %s."
            msg = msg % (bin_total, "file" if bin_total < 2 else "files")
            info(msg)
        return ()


class TorchPluginDetector(NuitkaPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "torch"  # Nuitka knows us by this name

    @staticmethod
    def isRelevant():
        """ This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """ This method checks whether a torch module is imported.

        Notes:
            For this we check whether its full name contains the string "torch".
        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName().split(".")
        if "torch" in full_name:
            self.warnUnusedPlugin("torch support.")
