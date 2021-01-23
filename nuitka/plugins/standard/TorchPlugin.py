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
import os
import shutil

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase


def get_torch_core_binaries(module):
    """Return required files from the torch folders.

    Notes:
        So far only tested for Windows. Requirements for other platforms
        are unknown.
    """
    binaries = []
    torch_dir = module.getCompileTimeDirectory()
    extras = os.path.join(torch_dir, "lib")

    if os.path.isdir(extras):
        for f in os.listdir(extras):
            # apart from shared libs, also the C header files are required!
            if f.endswith((".dll", ".so", ".h")) or ".so." in f:
                item = os.path.join(extras, f)
                if os.path.isfile(item):
                    binaries.append((item, "."))

    # this folder exists in the Linux version
    extras = os.path.join(torch_dir, "bin")

    if os.path.isdir(extras):
        for f in os.listdir(extras):
            item = os.path.join(extras, f)
            if os.path.isfile(item):
                binaries.append((item, "."))

    # this folder exists in the Linux version
    extras = os.path.join(torch_dir, "include")

    if os.path.isdir(extras):
        for root, _, files in os.walk(extras):
            for f in files:
                item = os.path.join(root, f)
                if os.path.isfile(item):
                    binaries.append((item, "."))

    return binaries


class TorchPlugin(NuitkaPluginBase):
    """This class represents the main logic of the plugin.

    This is a plugin to ensure torch scripts compile and work well in
    standalone mode.

    This plugin copies any files required by torch installations.

    Args:
        NuitkaPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "torch"
    plugin_desc = "Required by the torch / torchvision packages"

    def __init__(self):
        """Maintain switch to ensure once-only copy of torch/lib files."""
        self.files_copied = False
        return None

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def considerExtraDlls(self, dist_dir, module):
        """Copy extra files from torch/lib.

        Args:
            dist_dir: the name of the script's dist folder
            module: module object
        Returns:
            empty tuple
        """
        if self.files_copied:  # not the first time here
            return ()

        if module.getFullName() == "torch":
            self.files_copied = True  # fall through next time
            binaries = get_torch_core_binaries(module)
            bin_total = len(binaries)
            if bin_total == 0:
                return ()
            self.info("Copying files from 'torch' installation:")
            for f in binaries:
                bin_file = f[0]  # full binary file name
                idx = bin_file.find("torch")  # this will always work (idx > 0)
                back_end = bin_file[idx:]  # tail of the string
                tar_file = os.path.join(dist_dir, back_end)

                # create any missing intermediate folders
                if not os.path.exists(os.path.dirname(tar_file)):
                    os.makedirs(os.path.dirname(tar_file))

                shutil.copy(bin_file, tar_file)

            self.info(
                "Copied %i %s." % (bin_total, "file" if bin_total < 2 else "files")
            )
        return ()


class TorchPluginDetector(NuitkaPluginBase):
    """Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = TorchPlugin

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """This method checks whether a torch module is imported.

        Notes:
            For this we check whether its full name contains the string "torch".
        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName()
        if "torch" in full_name or "torchvision" in full_name:
            self.warnUnusedPlugin("torch support.")
