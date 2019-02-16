#     Copyright 2019, Jorj McKie, mailto:<lorj.x.mckie@outlook.de>
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
"""
Plug-in to ensure numpy scripts compile and work well in standalone mode.

In addition, if the numpy+MKL (Intel's Math Kernel Library) version is
installed, this plugin will copy its binaries to the dist/numpy/core folder,
because these are not detectable by dependency walkers.
"""

import os
import pkgutil
import re
import shutil
import sys
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import UserPluginBase

# ------------------------------------------------------------------------------
# The following code is largely inspired by PyInstaller hook_numpy.core.py
# ------------------------------------------------------------------------------
# START
# ------------------------------------------------------------------------------


def remove_suffix(string, suffix):
    """
    This function removes the given suffix from a string, if the string
    does indeed end with the prefix; otherwise, it returns the string
    unmodified.
    """
    # Special case: if suffix is empty, string[:0] returns ''. So, test
    # for a non-empty suffix.
    if suffix and string.endswith(suffix):
        return string[: -len(suffix)]
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
    pkg_base = remove_suffix(pkg_dir, package.replace(".", os.sep))

    return pkg_base, pkg_dir


def get_numpy_core_binaries():
    """Return any binaries in numpy/core and/or numpy/.libs, whether
    or not actually used by our script.
    This covers the special case of MKL binaries, which cannot be detected
    by dependency managers.
    """
    # covers/unifies cases, where sys.base_prefix does not deliver
    # everything we need and/or is not an abspath.
    base_prefix = getattr(sys, "real_prefix", getattr(sys, "base_prefix", sys.prefix))
    base_prefix = os.path.abspath(base_prefix)
    is_win = os.name == "nt"

    binaries = []

    # first look in numpy/.libs for binaries
    _, pkg_dir = get_package_paths("numpy")
    libdir = os.path.join(pkg_dir, ".libs")
    if os.path.isdir(libdir):
        dlls_pkg = [f for f in os.listdir(libdir)]
        binaries += [(os.path.join(libdir, f), ".") for f in dlls_pkg]

    # then look for libraries in numpy.core package path
    # should already return the MKL DLLs in ordinary cases
    _, pkg_dir = get_package_paths("numpy.core")
    re_anylib = re.compile(r"\w+\.(?:dll|so|dylib)", re.IGNORECASE)
    dlls_pkg = [f for f in os.listdir(pkg_dir) if re_anylib.match(f)]
    binaries += [(os.path.join(pkg_dir, f), ".") for f in dlls_pkg]

    # Also look for MKL libraries in Python's lib directory if present.
    # Anything found here will have to land in the dist folder, because there
    # just is no logical other place, and hope for the best ...
    # TODO: not supported yet!
    if is_win:
        lib_dir = os.path.join(base_prefix, "Library", "bin")
    else:
        lib_dir = os.path.join(base_prefix, "lib")

    if os.path.isdir(lib_dir):
        re_mkllib = re.compile(r"^(?:lib)?mkl\w+\.(?:dll|so|dylib)", re.IGNORECASE)
        dlls_mkl = [f for f in os.listdir(lib_dir) if re_mkllib.match(f)]
        if dlls_mkl:
            info(" Additional MKL libraries found.")
            info(" Not copying MKL binaries in '%s' for numpy!" % libdir)
            # binaries += [(os.path.join(lib_dir, f), '.') for f in dlls_mkl]

    return binaries


# ------------------------------------------------------------------------------
# END PyInstaller inspired code
# ------------------------------------------------------------------------------


class NumpyPlugin(UserPluginBase):
    """ This is for plugging in numpy support correctly.
    """

    plugin_name = "numpy-plugin"

    def __init__(self):
        self.files_copied = False  # ensure one-time action

    def considerExtraDlls(self, dist_dir, module):
        """Copy the extra numpy binaries.
        """
        if self.files_copied:
            return ()
        self.files_copied = True

        binaries = get_numpy_core_binaries()
        bin_total = len(binaries)  # anything there at all?
        if bin_total == 0:
            return ()

        info(" Now copying extra binaries from 'numpy' installation:")
        for f in binaries:
            bin_file = f[0].lower()  # full binary file name
            idx = bin_file.find("numpy")  # this will always work (idx > 0)
            back_end = bin_file[idx:]  # => like 'numpy/core/file.so'
            tar_file = os.path.join(dist_dir, back_end)
            info(" " + bin_file)

            # create any missing intermediate folders
            if not os.path.exists(os.path.dirname(tar_file)):
                os.makedirs(os.path.dirname(tar_file))

            shutil.copy(bin_file, tar_file)

        msg = " Copied %i %s."
        msg = msg % (bin_total, "binary" if bin_total < 2 else "binaries")
        info(msg)
        return ()


class NumpyPluginDetector(UserPluginBase):
    plugin_name = "numpy-plugin"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    # TODO: Temporary disabled until we get the warning criterion sorted out.
    def x_onModuleDiscovered(self, module):
        full_name = module.getFullName().split(".")
        if "numpy" in full_name:
            self.warnUnusedPlugin("numpy support.")
