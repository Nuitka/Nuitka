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
from logging import info, warning

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import copyTree, makePath
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


def get_sys_prefix():
    """ Return sys.prefix as guaranteed abspath format.
    """
    sys_prefix = getattr(sys, "real_prefix", getattr(sys, "base_prefix", sys.prefix))
    sys_prefix = os.path.abspath(sys_prefix)
    return sys_prefix


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

    extra_dll = os.path.join(
        os.path.dirname(get_module_file_attribute("scipy")), "extra-dll"
    )
    if not os.path.isdir(extra_dll):
        return binaries

    netto_bins = os.listdir(extra_dll)
    suffix_start = len(extra_dll) + 1  # this will put the files in dist root

    for f in netto_bins:
        if not f.endswith(".dll"):
            continue
        binaries.append((os.path.join(extra_dll, f), suffix_start))

    return binaries


def get_matplotlib_data():
    """ Return 'mpl-data' folder name for matplotlib.
    """
    mpl_data = os.path.join(
        os.path.dirname(get_module_file_attribute("matplotlib")), "mpl-data"
    )
    if not os.path.isdir(mpl_data):
        return None
    suffix_start = mpl_data.find("matplotlib")
    return mpl_data, suffix_start


def get_numpy_core_binaries():
    """ Return any binaries in numpy/core and/or numpy/.libs, whether or not actually used by our script.

    Notes:
        This covers the special cases like MKL binaries, which cannot be detected by dependency managers.

    Returns:
        tuple of abspaths of binaries
    """

    base_prefix = get_sys_prefix()
    suffix_start = len(base_prefix) + 1
    binaries = []

    # first look in numpy/.libs for binaries
    _, pkg_dir = get_package_paths("numpy")
    libdir = os.path.join(pkg_dir, ".libs")
    suffix_start = len(libdir) + 1
    if os.path.isdir(libdir):
        dlls_pkg = [f for f in os.listdir(libdir)]
        binaries += [[os.path.join(libdir, f), suffix_start] for f in dlls_pkg]

    # then look for libraries in numpy.core package path
    # should already return the MKL files in ordinary cases
    _, pkg_dir = get_package_paths("numpy.core")
    re_anylib = re.compile(r"\w+\.(?:dll|so|dylib)", re.IGNORECASE)
    dlls_pkg = [f for f in os.listdir(pkg_dir) if re_anylib.match(f)]
    binaries += [[os.path.join(pkg_dir, f), suffix_start] for f in dlls_pkg]

    # Also look for MKL libraries in folder "above" numpy.
    # This should meet the layout of Anaconda installs.

    if isWin32Windows():
        lib_dir = os.path.join(base_prefix, "Library", "bin")
        suffix_start = len(lib_dir) + 1
    else:
        lib_dir = os.path.join(base_prefix, "lib")
        suffix_start = len(lib_dir) + 1

    if not os.path.isdir(lib_dir):
        return binaries

    re_mkllib = re.compile(r"^(?:lib)?mkl\w+\.(?:dll|so|dylib)", re.IGNORECASE)

    for f in os.listdir(lib_dir):
        if isWin32Windows():
            if not (f.startswith(("libi", "libm", "mkl")) and f.endswith(".dll")):
                continue
        else:
            if not re_mkllib.match(f):
                continue

        binaries.append([os.path.join(lib_dir, f), suffix_start])

    return binaries


# ------------------------------------------------------------------------------
# END PyInstaller inspired code
# ------------------------------------------------------------------------------


class NumpyPlugin(NuitkaPluginBase):
    """ This class represents the main logic of the plugin.

    This is a plugin to ensure scripts using numpy, scipy, matplotlib, pandas,
    scikit-learn, etc. work well in standalone mode.

    While there already are relevant entries in the "ImplicitImports.py" plugin,
    this plugin copies any additional binary or data files required by many
    installations.

    Args:
        NuitkaPluginBase: plugin template class we are inheriting.
    """

    plugin_name = "numpy"  # Nuitka knows us by this name
    plugin_desc = "Required for numpy, scipy, pandas, matplotlib, etc."

    def __init__(self):
        self.enabled_plugins = None  # list of active standard plugins
        self.numpy_copied = False  # indicator: numpy files copied
        self.scipy_copied = False  # indicator: scipy files copied
        self.mpl_copied = False  # indicator: mpl-data files copied
        self.sklearn_copied = False  # indicator: sklearn files copied

    def considerExtraDlls(self, dist_dir, module):
        """ Copy extra shared libraries or data for this installation.

        Args:
            dist_dir: the name of the program's dist folder
            module: module object
        Returns:
            empty tuple
        """
        # pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements
        full_name = module.getFullName()
        if full_name not in ("numpy", "scipy", "matplotlib", "sklearn.datasets"):
            return ()

        if full_name == "numpy":
            if self.numpy_copied:
                return ()
            self.numpy_copied = True
            binaries = get_numpy_core_binaries()
            bin_total = len(binaries)  # anything there at all?
            if bin_total == 0:
                return ()

            for f in binaries:
                bin_file, idx = f  # (filename, pos. prefix + 1)
                back_end = bin_file[idx:]
                tar_file = os.path.join(dist_dir, back_end)
                makePath(  # create any missing intermediate folders
                    os.path.dirname(tar_file)
                )
                shutil.copyfile(bin_file, tar_file)

            msg = "Copied %i %s from 'numpy' installation." % (
                bin_total,
                "file" if bin_total < 2 else "files",
            )
            info(msg)
            return ()

        if full_name == "scipy":
            if self.scipy_copied:
                return ()
            self.scipy_copied = True
            if not self.getPluginOptionBool("scipy", False):
                return ()
            binaries = get_scipy_core_binaries()
            bin_total = len(binaries)
            if bin_total == 0:
                return ()

            for f in binaries:
                bin_file, idx = f  # (filename, pos. prefix + 1)
                back_end = bin_file[idx:]
                tar_file = os.path.join(dist_dir, back_end)
                makePath(  # create any missing intermediate folders
                    os.path.dirname(tar_file)
                )
                shutil.copyfile(bin_file, tar_file)

            msg = "Copied %i %s from 'scipy' installation." % (
                bin_total,
                "file" if bin_total < 2 else "files",
            )
            info(msg)
            return ()

        if full_name == "matplotlib":
            if self.mpl_copied:
                return ()
            self.mpl_copied = True
            if not self.getPluginOptionBool("matplotlib", False):
                return ()
            mpl_data = get_matplotlib_data()
            if not mpl_data:
                warning("'mpl-data' folder not found in matplotlib.")
                return ()
            mpl_data, idx = mpl_data  # (folder, pos. of 'matplotlib')
            back_end = mpl_data[idx:]
            tar_dir = os.path.join(dist_dir, back_end)
            copyTree(mpl_data, tar_dir)

            msg = "Copied 'mpl-data' from 'matplotlib' installation."
            info(msg)
            return ()

        if full_name == "sklearn.datasets":
            if self.sklearn_copied:
                return ()
            self.sklearn_copied = True
            if not self.getPluginOptionBool("sklearn", False):
                return ()
            sklearn_dir = os.path.dirname(get_module_file_attribute("sklearn"))
            source_data = os.path.join(sklearn_dir, "datasets", "data")
            target_data = os.path.join(dist_dir, "sklearn", "datasets", "data")
            source_descr = os.path.join(sklearn_dir, "datasets", "descr")
            target_descr = os.path.join(dist_dir, "sklearn", "datasets", "descr")
            copyTree(source_data, target_data)
            info("Copied folder sklearn/datasets/data")
            copyTree(source_descr, target_descr)
            info("Copied folder sklearn/datasets/descr")
            return ()

    def onModuleEncounter(
        self, module_filename, module_name, module_package, module_kind
    ):
        # pylint: disable=too-many-branches,too-many-return-statements
        if module_package == "scipy.sparse.csgraph" and module_name == "_validation":
            return True, "Replicate implicit import"

        if module_package is None:
            return None
        if module_package == module_name:
            full_name = module_package
        else:
            full_name = module_package + "." + module_name

        if full_name in ("cv2", "cv2.cv2", "cv2.data"):
            return True, "needed for OpenCV"

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

        # some special handling for matplotlib:
        # keep certain modules depending on whether Tk or Qt plugins are enabled
        if self.enabled_plugins is None:
            self.enabled_plugins = [p for p in Options.getPluginsEnabled()]

        if module_package == "matplotlib.backends":
            if "tk-inter" in self.enabled_plugins and (
                "backend_tk" in module_name or "tkagg" in module_name
            ):
                return True, "needed for tkinter interaction"
            if "qt-plugins" in self.enabled_plugins and "backend_qt" in module_name:
                return True, "needed for Qt interaction"
            if module_name == "backend_agg":
                return True, "needed as standard backend"


class NumpyPluginDetector(NuitkaPluginBase):
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
