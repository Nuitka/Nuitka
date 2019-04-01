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
import re
import shutil
import sys
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import UserPluginBase
from nuitka.utils.Utils import isWin32Windows

# ------------------------------------------------------------------------------
# The following code is largely inspired by PyInstaller hook_numpy.core.py
# ------------------------------------------------------------------------------
# START
# ------------------------------------------------------------------------------


def remove_suffix(string, suffix):
    """ Remove the given suffix from a string.

    Notes:
        If the string does indeed end with it. Otherwise, it return the string unmodified.

    Args:
        string: the string from which to cut off a suffix
        suffix: this should be cut off the string
    Returns:
        string from which the suffix was removed
    """
    # Special case: if suffix is empty, string[:0] returns ''. So, test
    # for a non-empty suffix.
    if suffix and string.endswith(suffix):
        return string[: -len(suffix)]
    else:
        return string


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


def get_package_paths(package):
    """ Return the path to package stored on this machine.

    Notes:
        Also returns the path to this particular package. For example, if
        pkg.subpkg lives in /abs/path/to/python/libs, then this function returns
        (/abs/path/to/python/libs, /abs/path/to/python/libs/pkg/subpkg).
    Args:
        package: package name
    Returns:
        tuple
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


def get_scipy_core_binaries():
    """ Return binaries from the extra-dlls folder (Windows only).
    """
    binaries = []
    if not isWin32Windows():
        return binaries
    extra_dll = os.path.join(
        os.path.dirname(get_module_file_attribute("scipy")), "extra-dll"
    )
    if not os.path.isdir(extra_dll):
        return binaries

    netto_bins = os.listdir(extra_dll)

    for f in netto_bins:
        if not f.endswith(".dll"):
            continue
        binaries.append((os.path.join(extra_dll, f), "."))

    return binaries


def get_numpy_core_binaries():
    """ Return any binaries in numpy/core and/or numpy/.libs, whether or not actually used by our script.

    Notes:
        This covers the special cases like MKL binaries, which cannot be detected by dependency managers.

    Returns:
        tuple of abspaths of binaries
    """

    # covers/unifies cases, where sys.base_prefix does not deliver
    # everything we need and/or is not an abspath.
    base_prefix = getattr(sys, "real_prefix", getattr(sys, "base_prefix", sys.prefix))

    base_prefix = os.path.abspath(base_prefix)

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
    if isWin32Windows():
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
    """ This class represents the main logic of the plugin.

    This is a plugin to ensure numpy and scipy scripts compile and work well in standalone mode.

    While there already are relevant entries in the "ImplicitImports.py" plugin,
    this plugin copies any additional binary files required by many installations.
    Typically, these binaries are used for acceleration by replacing parts of the packages'
    homegrown code with highly tuned routines.

    Typical examples are MKL (Intel's Math Kernel Library), OpenBlas, scipy
    extra-dll and others.

    Many of these special libraries are not detectable by dependency walkers,
    and this is why this plugin may be required.

    Args:
        UserPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "numpy"  # Nuitka knows us by this name

    def considerExtraDlls(self, dist_dir, module):
        """ Copy extra shared libraries for this numpy / scipy installation.

        Args:
            dist_dir: the name of the program's dist folder
            module: module object (not used here)
        Returns:
            empty tuple
        """
        full_name = module.getFullName()
        if full_name not in ("numpy", "scipy"):
            return ()

        if full_name == "numpy":
            binaries = get_numpy_core_binaries()
            bin_total = len(binaries)  # anything there at all?
            if bin_total == 0:
                return ()
            info("")
            info(" Copying extra binaries from 'numpy' installation:")
            for f in binaries:
                bin_file = f[0].lower()  # full binary file name
                idx = bin_file.find("numpy")  # this will always work (idx > 0)
                back_end = bin_file[idx:]  # => like 'numpy/core/file.so'
                tar_file = os.path.join(dist_dir, back_end)

                # create any missing intermediate folders
                if not os.path.exists(os.path.dirname(tar_file)):
                    os.makedirs(os.path.dirname(tar_file))

                shutil.copy(bin_file, tar_file)

            msg = " Copied %i %s."
            msg = msg % (bin_total, "binary" if bin_total < 2 else "binaries")
            info(msg)
            return ()

        if full_name == "scipy":
            if not self.getPluginOptionBool("scipy", False):
                return ()
            binaries = get_scipy_core_binaries()
            bin_total = len(binaries)
            if bin_total == 0:
                return ()
            info("")
            info(" Copying extra binaries from 'scipy' installation:")
            for f in binaries:
                bin_file = f[0].lower()  # full binary file name
                idx = bin_file.find("scipy")  # this will always work (idx > 0)
                back_end = bin_file[idx:]
                tar_file = os.path.join(dist_dir, back_end)

                # create any missing intermediate folders
                if not os.path.exists(os.path.dirname(tar_file)):
                    os.makedirs(os.path.dirname(tar_file))

                shutil.copy(bin_file, tar_file)

            msg = " Copied %i %s."
            msg = msg % (bin_total, "binary" if bin_total < 2 else "binaries")
            info(msg)
            return ()


class NumpyPluginDetector(UserPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "numpy"  # Nuitka knows us by this name

    @staticmethod
    def isRelevant():
        """ This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """ This method checks whether a numpy module is imported.

        Notes:
            For this we check whether its full name contains the string "numpy".
        Args:
            module: the module object
        Returns:
            None
        """
        full_name = module.getFullName().split(".")
        if "numpy" in full_name:
            self.warnUnusedPlugin("numpy support.")
