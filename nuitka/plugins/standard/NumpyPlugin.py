#     Copyright 2020, Jorj McKie, mailto:<jorj.x.mckie@outlook.de>
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

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import getActivePlugins
from nuitka.utils import Execution
from nuitka.utils.FileOperations import getFileList, makePath
from nuitka.utils.Utils import isWin32Windows

# ------------------------------------------------------------------------------
# The following code is largely inspired by PyInstaller hook_numpy.core.py
# START
# ------------------------------------------------------------------------------


def get_sys_prefix():
    """ Return sys.prefix as guaranteed abspath format.
    """
    sys_prefix = getattr(sys, "real_prefix", getattr(sys, "base_prefix", sys.prefix))
    sys_prefix = os.path.abspath(sys_prefix)
    return sys_prefix


def getScipyCoreBinaries(module):
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


def getNumpyCoreBinaries(module):
    """ Return any binaries in numpy/core and/or numpy/.libs.

    Notes:
        This covers the special cases like MKL binaries.

    Returns:
        tuple of abspaths of binaries.
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


def getMatplotlibRc():
    """Determine the filename of matplotlibrc and the default backend.

    Notes:
        There might exist a local version outside 'matplotlib/mpl-data' which
        we then must use instead. Determine its name by aksing matplotlib.
    """
    cmd = """\
from __future__ import print_function
from matplotlib import matplotlib_fname, get_backend
print(matplotlib_fname())
print(get_backend())
"""

    feedback = Execution.check_output([sys.executable, "-c", cmd])

    if str is not bytes:  # ensure str in Py3 and up
        feedback = feedback.decode()
    feedback = feedback.replace("\r", "")
    matplotlibrc, backend = feedback.splitlines()
    return matplotlibrc, backend


def copyMplDataFiles(module, dist_dir):
    """ Write matplotlib data files ('mpl-data')."""

    data_dir = os.path.join(module.getCompileTimeDirectory(), "mpl-data")  # must exist
    if not os.path.isdir(data_dir):
        sys.exit("mpl-data missing: matplotlib installation is broken")

    matplotlibrc, backend = getMatplotlibRc()  # get matplotlibrc, backend

    prefix = os.path.join("matplotlib", "mpl-data")
    for item in getFileList(data_dir):  # copy data files to dist folder
        if item.endswith("matplotlibrc"):  # handle config separately
            continue
        idx = item.find(prefix)  # need string starting with 'matplotlib/mpl-data'
        tar_file = os.path.join(dist_dir, item[idx:])
        makePath(os.path.dirname(tar_file))  # create intermediate folders
        shutil.copyfile(item, tar_file)

    old_lines = open(matplotlibrc).read().splitlines()  # old config file lines
    new_lines = ["# modified by Nuitka plugin 'numpy'"]  # new config file lines
    found = False  # checks whether backend definition encountered
    for line in old_lines:
        line = line.strip()  # omit meaningless lines
        if line.startswith("#") or line == "":
            continue
        new_lines.append(line)
        if line.startswith(("backend ", "backend:")):
            found = True  # old config file has a backend definition
            new_lines.append("# backend definition copied from installation")

    if not found:
        # get the string from interpreted mode and insert it in matplotlibrc
        new_lines.append("backend: %s" % backend)

    matplotlibrc = os.path.join(dist_dir, prefix, "matplotlibrc")
    outfile = open(matplotlibrc, "w")
    outfile.write("\n".join(new_lines))
    outfile.close()


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

    def __init__(self, matplotlib, scipy):
        self.matplotlib = matplotlib
        self.scipy = scipy

        self.enabled_plugins = None  # list of active standard plugins
        self.numpy_copied = False  # indicator: numpy files copied
        self.scipy_copied = True  # indicator: scipy files copied
        if self.scipy:
            self.scipy_copied = False

        self.mpl_data_copied = True  # indicator: matplotlib data copied
        if self.matplotlib:
            self.mpl_data_copied = False
            for p in getActivePlugins():
                if p.plugin_name.endswith("hinted-mods.py"):
                    break
            else:
                self.warning(
                    "matplotlib may need hinted compilation for non-standard backends"
                )

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--include-scipy",
            action="store_true",
            dest="scipy",
            default=False,
            help="""\
Should scipy be included with numpy, Default is %default.""",
        )

        group.add_option(
            "--include-matplotlib",
            action="store_true",
            dest="matplotlib",
            default=False,
            help="""\
Should matplotlib be included with numpy, Default is %default.""",
        )

    def considerExtraDlls(self, dist_dir, module):
        """ Copy extra shared libraries or data for this installation.

        Args:
            dist_dir: the name of the program's dist folder
            module: module object
        Returns:
            empty tuple
        """
        full_name = module.getFullName()
        elements = full_name.split(".")

        if not self.numpy_copied and full_name == "numpy":
            self.numpy_copied = True
            binaries = getNumpyCoreBinaries(module)

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
                self.info(msg)

        if not self.scipy_copied and full_name == "scipy":
            self.scipy_copied = True
            binaries = getScipyCoreBinaries(module)

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
                self.info(msg)

        if not self.mpl_data_copied and "matplotlib" in elements:
            self.mpl_data_copied = True
            copyMplDataFiles(module, dist_dir)
            self.info("Copied 'matplotlib/mpl-data'.")

        return ()

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # pylint: disable=too-many-branches,too-many-return-statements
        if not self.scipy and module_name.hasOneOfNamespaces(
            "scipy", "sklearn", "skimage"
        ):
            return False, "Omit unneeded components"

        if not self.matplotlib and module_name.hasOneOfNamespaces(
            "matplotlib", "skimage"
        ):
            return False, "Omit unneeded components"

        if module_name == "scipy.sparse.csgraph._validation":
            return True, "Replicate implicit import"

        if self.matplotlib and module_name.hasNamespace("mpl_toolkits"):
            return True, "Needed by matplotlib"

        if module_name in ("cv2", "cv2.cv2", "cv2.data"):
            return True, "Needed for OpenCV"

        sklearn_mods = [
            "sklearn.utils.sparsetools._graph_validation",
            "sklearn.utils.sparsetools._graph_tools",
            "sklearn.utils.lgamma",
            "sklearn.utils.weight_vector",
            "sklearn.utils._unittest_backport",
            "sklearn.externals.joblib.externals.cloudpickle.dumps",
            "sklearn.externals.joblib.externals.loky.backend.managers",
        ]

        if isWin32Windows():
            sklearn_mods.extend(
                [
                    "sklearn.externals.joblib.externals.loky.backend.synchronize",
                    "sklearn.externals.joblib.externals.loky.backend._win_wait",
                    "sklearn.externals.joblib.externals.loky.backend._win_reduction",
                    "sklearn.externals.joblib.externals.loky.backend.popen_loky_win32",
                ]
            )
        else:
            sklearn_mods.extend(
                [
                    "sklearn.externals.joblib.externals.loky.backend.synchronize",
                    "sklearn.externals.joblib.externals.loky.backend.compat_posix",
                    "sklearn.externals.joblib.externals.loky.backend._posix_reduction",
                    "sklearn.externals.joblib.externals.loky.backend.popen_loky_posix",
                ]
            )

        if self.scipy and module_name in sklearn_mods:
            return True, "Needed by sklearn"

        # some special handling for matplotlib:
        # depending on whether 'tk-inter' resp. 'qt-plugins' are enabled,
        # matplotlib backends are included.
        if self.enabled_plugins is None:
            self.enabled_plugins = Options.getPluginsEnabled()

        if self.matplotlib:
            if "tk-inter" in self.enabled_plugins:
                if module_name in (
                    "matplotlib.backends.backend_tk",
                    "matplotlib.backends.backend_tkagg",
                    "matplotlib.backend.tkagg",
                ):
                    return True, "Needed for tkinter backend"

            if "qt-plugins" in self.enabled_plugins:
                if module_name.startswith("matplotlib.backends.backend_qt"):
                    return True, "Needed for Qt backend"

            if module_name == "matplotlib.backends.backend_agg":
                return True, "Needed as standard backend"


class NumpyPluginDetector(NuitkaPluginBase):
    """ Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = NumpyPlugin

    @classmethod
    def isRelevant(cls):
        """ Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """ This method checks whether numpy is required.

        Notes:
            For this we check whether its first name part is numpy relevant.
        Args:
            module: the module object
        Returns:
            None
        """
        if module.getFullName().hasOneOfNamespaces(
            "numpy", "scipy", "skimage", "pandas", "matplotlib", "sklearn",
        ):
            self.warnUnusedPlugin("Numpy support.")
