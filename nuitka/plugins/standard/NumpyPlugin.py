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
import re
import shutil
import sys
from collections import namedtuple

from nuitka import Options
from nuitka.freezer.IncludedEntryPoints import makeDllEntryPoint
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import hasActivePlugin
from nuitka.PythonVersions import getSystemPrefixPath
from nuitka.utils import Execution
from nuitka.utils.FileOperations import (
    getFileList,
    listDir,
    makePath,
    putTextFileContents,
)
from nuitka.utils.Utils import getOS, isWin32Windows


def getNumpyCoreBinaries(module):
    """Return any binaries in numpy/core and/or numpy/.libs.

    Notes:
        This covers the special cases like MKL binaries.

    Returns:
        tuple of abspaths of binaries.
    """
    numpy_dir = module.getCompileTimeDirectory()
    numpy_core_dir = os.path.join(numpy_dir, "core")
    base_prefix = getSystemPrefixPath()

    binaries = []

    # first look in numpy/.libs for binaries
    libdir = os.path.join(numpy_dir, ".libs" if getOS() != "Darwin" else ".dylibs")
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


class NumpyPlugin(NuitkaPluginBase):
    """This class represents the main logic of the plugin.

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

    def __init__(self, include_matplotlib, include_scipy):
        self.matplotlib = include_matplotlib
        self.scipy = include_scipy

        self.enabled_plugins = None  # list of active standard plugins
        self.numpy_copied = False  # indicator: numpy files copied
        self.scipy_copied = True  # indicator: scipy files copied
        if self.scipy:
            self.scipy_copied = False

        self.mpl_data_copied = False  # indicator: matplotlib data copied

        # Information about matplotlib install.
        self.matplotlib_info = None

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--noinclude-scipy",
            action="store_false",
            dest="include_scipy",
            default=True,
            help="""\
Should scipy, sklearn or skimage when used be not included with numpy, Default is %default.""",
        )

        group.add_option(
            "--noinclude-matplotlib",
            action="store_false",
            dest="include_matplotlib",
            default=True,
            help="""\
Should matplotlib not be be included with numpy, Default is %default.""",
        )

    def considerExtraDlls(self, dist_dir, module):
        """Copy extra shared libraries or data for this installation.

        Args:
            dist_dir: the name of the program's dist folder
            module: module object
        Returns:
            empty tuple
        """
        full_name = module.getFullName()

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

        if os.name == "nt" and not self.scipy_copied and full_name == "scipy":
            # TODO: We are not getting called twice, are we?
            assert not self.scipy_copied
            self.scipy_copied = True

            bin_total = 0
            for entry_point in self._getScipyCoreBinaries(
                scipy_dir=module.getCompileTimeDirectory()
            ):
                yield entry_point
                bin_total += 1

            if bin_total > 0:
                msg = "Copied %i %s from 'scipy' installation." % (
                    bin_total,
                    "file" if bin_total < 2 else "files",
                )
                self.info(msg)

        # TODO: Ouch, do not copy data files when asked to copy DLLs.
        if self.matplotlib and full_name == "matplotlib" and not self.mpl_data_copied:
            self.mpl_data_copied = True

            self.copyMplDataFiles(dist_dir)

    def _getMatplotlibInfo(self):
        """Determine the filename of matplotlibrc and the default backend, etc.

        Notes:
            There might exist a local version outside 'matplotlib/mpl-data' which
            we then must use instead. Determine its name by aksing matplotlib.
        """
        if self.matplotlib_info is None:
            cmd = r"""\
from __future__ import print_function
from matplotlib import matplotlib_fname, get_backend, _get_data_path, __version__
from inspect import getsource
print(repr(matplotlib_fname()))
print(repr(get_backend()))
print(repr(_get_data_path()))
print(repr(__version__))
print(repr("MATPLOTLIBDATA" in getsource(_get_data_path)))
"""

            # TODO: Make this is a re-usable pattern, output from a script with values per line
            feedback = Execution.check_output([sys.executable, "-c", cmd])

            if str is not bytes:  # ensure str in Py3 and up
                feedback = feedback.decode("utf8")

            # Ignore Windows newlines difference.
            feedback = feedback.replace("\r", "")

            MatplotlibInfo = namedtuple(
                "MatplotlibInfo",
                (
                    "matplotlibrc_filename",
                    "backend",
                    "data_path",
                    "matplotlib_version",
                    "needs_matplotlibdata_env",
                ),
            )

            # We are being lazy here, the code is trusted, pylint: disable=eval-used
            self.matplotlib_info = MatplotlibInfo(
                *(eval(value) for value in feedback.splitlines())
            )

        return self.matplotlib_info

    def copyMplDataFiles(self, dist_dir):
        """ Write matplotlib data files ('mpl-data')."""

        matplotlib_info = self._getMatplotlibInfo()

        if not os.path.isdir(matplotlib_info.data_path):
            self.sysexit(
                "mpl-data missing, matplotlib installation appears to be broken"
            )

        # Copy data files to dist folder
        for fullname in getFileList(matplotlib_info.data_path):
            filename = os.path.relpath(fullname, matplotlib_info.data_path)

            if filename.endswith("matplotlibrc"):  # handle config separately
                continue

            target_filename = os.path.join(dist_dir, "matplotlib", "mpl-data", filename)

            makePath(os.path.dirname(target_filename))  # create intermediate folders
            shutil.copyfile(fullname, target_filename)

        old_lines = (
            open(matplotlib_info.matplotlibrc_filename).read().splitlines()
        )  # old config file lines
        new_lines = []  # new config file lines

        found = False  # checks whether backend definition encountered
        for line in old_lines:
            line = line.rstrip()

            # omit meaningless lines
            if line.startswith("#") and matplotlib_info.matplotlib_version < "3":
                continue

            new_lines.append(line)

            if line.startswith(("backend ", "backend:")):
                # old config file has a backend definition
                found = True

        if not found and matplotlib_info.matplotlib_version < "3":
            # Set the backend, so even if it was run time determined, we now enforce it.
            new_lines.append("backend: %s" % matplotlib_info.backend)

        matplotlibrc_filename = os.path.join(
            dist_dir, "matplotlib", "mpl-data", "matplotlibrc"
        )

        putTextFileContents(filename=matplotlibrc_filename, contents=new_lines)

        self.info("Copied 'matplotlib/mpl-data'.")

    @staticmethod
    def _getScipyCoreBinaries(scipy_dir):
        """Return binaries from the extra-dlls folder (Windows only)."""

        for dll_dir_name in ("extra_dll", ".libs"):
            dll_dir_path = os.path.join(scipy_dir, dll_dir_name)

            if os.path.isdir(dll_dir_path):
                for source_path, source_filename in listDir(dll_dir_path):
                    if source_filename.lower().endswith(".dll"):
                        yield makeDllEntryPoint(
                            source_path=source_path,
                            dest_path=os.path.join(
                                "scipy", dll_dir_name, source_filename
                            ),
                            package_name="scipy",
                        )

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
        if self.matplotlib:
            if hasActivePlugin("tk-inter"):
                if module_name in (
                    "matplotlib.backends.backend_tk",
                    "matplotlib.backends.backend_tkagg",
                    "matplotlib.backend.tkagg",
                ):
                    return True, "Needed for tkinter matplotplib backend"

            if hasActivePlugin("qt-plugins"):
                if module_name in (
                    "matplotlib.backends.backend_qt5",
                    "matplotlib.backends.backend_qt5.py",
                    "matplotlib.backends.backend_qt5cairo.py",
                    "matplotlib.backend.backend_qt5.py",
                ):
                    return True, "Needed for Qt5 matplotplib backend"

            if module_name == "matplotlib.backends.backend_agg":
                return True, "Needed as standard matplotplib backend"

    def createPreModuleLoadCode(self, module):
        """Method called when a module is being imported.

        Notes:
            If full name equals "matplotlib" we insert code to set the
            environment variable that e.g. Debian versions of matplotlib
            use.

        Args:
            module: the module object
        Returns:
            Code to insert and descriptive text (tuple), or (None, None).
        """

        # Matplotlib might be off, or not need the environment variable.
        if (
            not self.matplotlib
            or module.getFullName() != "matplotlib"
            or not self._getMatplotlibInfo().needs_matplotlibdata_env
        ):
            return None, None

        code = r"""
import os
os.environ["MATPLOTLIBDATA"] = os.path.join(__nuitka_binary_dir, "matplotlib", "mpl-data")
"""
        return (
            code,
            "Setting 'MATPLOTLIBDATA' environment variable for matplotlib to find package data.",
        )


class NumpyPluginDetector(NuitkaPluginBase):
    """Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = NumpyPlugin

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """This method checks whether numpy is required.

        Notes:
            For this we check whether its first name part is numpy relevant.
        Args:
            module: the module object
        Returns:
            None
        """
        module_name = module.getFullName()
        if module_name.hasOneOfNamespaces(
            "numpy", "scipy", "skimage", "pandas", "matplotlib", "sklearn"
        ):
            self.warnUnusedPlugin(
                "Numpy support for at least '%s'."
                % module_name.getTopLevelPackageName()
            )
