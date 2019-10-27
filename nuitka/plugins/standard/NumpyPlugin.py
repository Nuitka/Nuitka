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
import re
import shutil
import sys
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import makePath
from nuitka.utils.Utils import isWin32Windows

# ------------------------------------------------------------------------------
# The following code is largely inspired by PyInstaller hook_numpy.core.py
# ------------------------------------------------------------------------------
# START
# ------------------------------------------------------------------------------


def get_sys_prefix():
    """ Return sys.prefix as guaranteed abspath format.
    """
    sys_prefix = getattr(sys, "real_prefix", getattr(sys, "base_prefix", sys.prefix))
    sys_prefix = os.path.abspath(sys_prefix)
    return sys_prefix


def get_scipy_core_binaries(module):
    """ Return binaries from the extra-dlls folder (Windows only).
    """
    binaries = []
    scipy_dir = module.getCompileTimeDirectory()
    extra_dll = os.path.join(scipy_dir, "extra-dll")
    if not os.path.isdir(extra_dll):
        return binaries

    netto_bins = os.listdir(extra_dll)
    suffix_start = len(extra_dll) + 1  # this will put the files in dist root

    for f in netto_bins:
        if not f.endswith(".dll"):
            continue
        binaries.append((os.path.join(extra_dll, f), suffix_start))

    return binaries


def get_numpy_core_binaries(module):
    """ Return any binaries in numpy/core and/or numpy/.libs, whether or not actually used by our script.

    Notes:
        This covers the special cases like MKL binaries, which cannot be detected by dependency managers.

    Returns:
        tuple of abspaths of binaries
    """
    numpy_dir = module.getCompileTimeDirectory()
    numpy_core_dir = os.path.join(numpy_dir, "core")
    base_prefix = get_sys_prefix()

    binaries = []

    # first look in numpy/.libs for binaries
    libdir = os.path.join(numpy_dir, ".libs")
    suffix_start = len(libdir) + 1
    if os.path.isdir(libdir):
        dlls_pkg = os.listdir(libdir)
        binaries += [[os.path.join(libdir, f), suffix_start] for f in dlls_pkg]

    # then look for libraries in numpy.core package path
    # should already return the MKL files in ordinary cases

    re_anylib = re.compile(r"\w+\.(?:dll|so|dylib)", re.IGNORECASE)

    dlls_pkg = [f for f in os.listdir(numpy_core_dir) if re_anylib.match(f)]
    binaries += [[os.path.join(numpy_core_dir, f), suffix_start] for f in dlls_pkg]

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
        self.matplotlib = self.getPluginOptionBool("matplotlib", False)
        self.scipy = self.getPluginOptionBool("scipy", False)
        if self.scipy:
            self.scipy_copied = False  # indicator: scipy files copied
        else:
            self.scipy_copied = True

    def considerExtraDlls(self, dist_dir, module):
        """ Copy extra shared libraries or data for this installation.

        Args:
            dist_dir: the name of the program's dist folder
            module: module object
        Returns:
            empty tuple
        """
        full_name = module.getFullName()

        if full_name == "numpy" and not self.numpy_copied:
            self.numpy_copied = True
            binaries = get_numpy_core_binaries(module)

            for f in binaries:
                bin_file, idx = f  # (filename, pos. prefix + 1)
                back_end = bin_file[idx:]
                tar_file = os.path.join(dist_dir, back_end)
                makePath(  # create any missing intermediate folders
                    os.path.dirname(tar_file)
                )
                shutil.copyfile(bin_file, tar_file)

            bin_total = len(binaries)  # anything there at all?
            if bin_total > 0:
                msg = "Copied %i %s from 'numpy' installation." % (
                    bin_total,
                    "file" if bin_total < 2 else "files",
                )
                info(msg)

        if full_name == "scipy" and not self.scipy_copied:
            self.scipy_copied = True
            binaries = get_scipy_core_binaries(module)

            for f in binaries:
                bin_file, idx = f  # (filename, pos. prefix + 1)
                back_end = bin_file[idx:]
                tar_file = os.path.join(dist_dir, back_end)
                makePath(  # create any missing intermediate folders
                    os.path.dirname(tar_file)
                )
                shutil.copyfile(bin_file, tar_file)

            bin_total = len(binaries)
            if bin_total > 0:
                msg = "Copied %i %s from 'scipy' installation." % (
                    bin_total,
                    "file" if bin_total < 2 else "files",
                )
                info(msg)

        return ()

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # pylint: disable=too-many-branches,too-many-return-statements
        elements = module_name.split(".")
        if not self.scipy and elements[0] in ("scipy", "sklearn"):
            return False, "Omit unneeded components"

        if module_name == "scipy.sparse.csgraph._validation":
            return True, "Replicate implicit import"

        if elements[0] == "mpl_toolkits" and self.matplotlib is True:
            return True, "Needed by matplotlib"

        if module_name.getPackageName() is None:
            return None

        if module_name in ("cv2", "cv2.cv2", "cv2.data"):
            return True, "Needed for OpenCV"

        if module_name in (
            "sklearn.utils.sparsetools._graph_validation",
            "sklearn.utils.sparsetools._graph_tools",
        ):
            return True, "Needed by sklearn"

        if module_name in (
            "sklearn.utils.lgamma",
            "sklearn.utils.weight_vector",
            "sklearn.utils._unittest_backport",
        ):
            return True, "Needed by sklearn"

        posix = (
            "sklearn.externals.joblib.externals.loky.backend.managers",
            "sklearn.externals.joblib.externals.loky.backend.synchronize",
            "sklearn.externals.joblib.externals.loky.backend.compat_posix",
            "sklearn.externals.joblib.externals.loky.backend._posix_reduction",
            "sklearn.externals.joblib.externals.loky.backend.popen_loky_posix",
        )
        win32 = (
            "sklearn.externals.joblib.externals.loky.backend.managers",
            "sklearn.externals.joblib.externals.loky.backend.synchronize",
            "sklearn.externals.joblib.externals.loky.backend._win_wait",
            "sklearn.externals.joblib.externals.loky.backend._win_reduction",
            "sklearn.externals.joblib.externals.loky.backend.popen_loky_win32",
        )

        if isWin32Windows():
            valid_list = win32
        else:
            valid_list = posix

        if module_name in valid_list:
            return True, "Needed by sklearn"

        if module_name == "sklearn.externals.joblib.externals.cloudpickle.dumps":
            return True, "Needed by sklearn"

        # some special handling for matplotlib:
        # keep certain modules depending on whether Tk or Qt plugins are enabled
        if self.enabled_plugins is None:
            self.enabled_plugins = Options.getPluginsEnabled()

        if "tk-inter" in self.enabled_plugins:
            if module_name in (
                "matplotlib.backends.backend_tk",
                "matplotlib.backends.backend_tkagg",
                "matplotlib.backend.tkagg",
            ):
                return True, "Needed for tkinter interaction"

        if "qt-plugins" in self.enabled_plugins:
            if module_name == "matplotlib.backends.backend_qt":
                return True, "Needed for Qt interaction"

        if module_name == "matplotlib.backends.backend_agg":
            return True, "Needed as standard backend"


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
