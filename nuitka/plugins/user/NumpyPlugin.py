#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" User plug-in to make tkinter scripts work well in standalone mode.

To run properly, scripts need copies of the TCL / TK libraries as sub-folders
of the script's dist folder.
"""

import os
import shutil
import sys
import glob
import pkgutil
import re
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase, pre_modules, post_modules
from nuitka.utils import Execution, Utils
from nuitka.utils.FileOperations import (
    getFileList,
    getSubDirectories,
    removeDirectory
)

#------------------------------------------------------------------------------
# The following code is largely inspired by PyInstaller hook_numpy.core.py
#------------------------------------------------------------------------------
# START
#------------------------------------------------------------------------------
def remove_suffix(string, suffix):
    """
    This function removes the given suffix from a string, if the string
    does indeed end with the prefix; otherwise, it returns the string
    unmodified.
    """
    # Special case: if suffix is empty, string[:0] returns ''. So, test
    # for a non-empty suffix.
    if suffix and string.endswith(suffix):
        return string[:-len(suffix)]
    else:
        return string

def get_module_file_attribute(package):
    """ Get the absolute path of the module with the passed name.
    :arg str package: Fully-qualified name of this module.
    :returns: (str) Absolute path of this module.
    """
    loader = pkgutil.find_loader(package)
    attr = loader.get_filename(package)
    if not attr:
        raise ImportError
    return attr

def get_package_paths(package):
    """
    Given a package, return the path to packages stored on this machine
    and also returns the path to this particular package. For example,
    if pkg.subpkg lives in /abs/path/to/python/libs, then this function
    returns (/abs/path/to/python/libs,
             /abs/path/to/python/libs/pkg/subpkg).
    """
    file_attr = get_module_file_attribute(package)

    # package.__file__ = /abs/path/to/package/subpackage/__init__.py.
    # Search for Python files in /abs/path/to/package/subpackage.
    # pkg_dir stores this path.
    pkg_dir = os.path.dirname(file_attr)
    # When found, remove /abs/path/to/ from the filename.
    # pkg_base stores this path to be removed.
    pkg_base = remove_suffix(pkg_dir, package.replace('.', os.sep))

    return pkg_base, pkg_dir

def get_numpy_core_binaries():
    base_prefix = getattr(sys, 'real_prefix',
                          getattr(sys, 'base_prefix', sys.prefix)
                         )
    base_prefix = os.path.abspath(base_prefix)
    is_win = sys.platform == "win32"

    binaries = []

    # look for libraries in numpy package path
    pkg_base, pkg_dir = get_package_paths('numpy.core')
    re_anylib = re.compile(r'\w+\.(?:dll|so|dylib)', re.IGNORECASE)
    dlls_pkg = [f for f in os.listdir(pkg_dir) if re_anylib.match(f)]
    binaries += [(os.path.join(pkg_dir, f), '.') for f in dlls_pkg]

    # look for MKL libraries in pythons lib directory
    if is_win:
        lib_dir = os.path.join(base_prefix, "Library", "bin")
    else:
        lib_dir = os.path.join(base_prefix, "lib")
    if os.path.isdir(lib_dir):
        re_mkllib = re.compile(r'^(?:lib)?mkl\w+\.(?:dll|so|dylib)', re.IGNORECASE)
        dlls_mkl = [f for f in os.listdir(lib_dir) if re_mkllib.match(f)]
        if dlls_mkl:
            print("MKL libraries found when importing numpy. Adding MKL to binaries")
            binaries += [(os.path.join(lib_dir, f), '.') for f in dlls_mkl]

    return binaries
#------------------------------------------------------------------------------
# END PyInstaller inspired code
#------------------------------------------------------------------------------

class NumpyPlugin(NuitkaPluginBase):
    """ This is for plugging in numpy support correctly.
    """

    plugin_name = "numpy-plugin"

    def __init__(self):
        self.bin_copied = False        # indicate binaries copied yet

    @staticmethod
    def createPreModuleLoadCode(module):
        """Ensure that module '_dtype_ctypes' is not missing.
        """
        code = """from numpy.core import _dtype_ctypes
        """
        full_name = module.getFullName()
        # select when to insert the code
        if full_name == "numpy":
            return code, None
        return None, None

    def onModuleDiscovered(self, module):
        """Make sure our pre-module code is recorded.
        """

        full_name = module.getFullName()

        pre_code, reason = self.createPreModuleLoadCode(module)
        if pre_code:
            if full_name is pre_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            pre_modules[full_name] = self._createTriggerLoadedModule(
                module       = module,
                trigger_name = "-preLoad",
                code         = pre_code
            )

    def considerExtraDlls(self, dist_dir, module):
        """Copy all binaries in 'numpy.core'.
        """
        if self.bin_copied is True:         # already done
            return ()

        info("Now copying binaries from 'numpy.core'.")

        tar_dir  = os.path.join(dist_dir, "numpy", "core")

        binaries = get_numpy_core_binaries()
        bin_total = len(binaries)
        mkl_count = 0
        for f in binaries:
            core_file = f[0].lower()
            base_file = os.path.basename(core_file)
            if base_file.startswith(("mkl", "tbb", "lib", "svml")):
                mkl_count += 1
            shutil.copy(core_file, tar_dir)
        msg = "Done, copied %i 'numpy.core' binaries, thereof %i for MKL."
        msg = msg % (bin_total, mkl_count)
        info(msg)
        self.bin_copied = True
        return ()

class NumpyPluginDetector(NuitkaPluginBase):
    plugin_name = "numpy-plugin"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        full_name = module.getFullName().split(".")
        if "numpy" in full_name:
            self.warnUnusedPlugin("numpy support.")
