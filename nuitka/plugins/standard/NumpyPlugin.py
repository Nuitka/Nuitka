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
import sys
from collections import namedtuple

from nuitka import Options
from nuitka.freezer.IncludedDataFiles import (
    makeIncludedDataFile,
    makeIncludedGeneratedDataFile,
)
from nuitka.freezer.IncludedEntryPoints import makeDllEntryPoint
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import getActiveQtPlugin, hasActivePlugin
from nuitka.PythonVersions import getSystemPrefixPath
from nuitka.utils import Execution
from nuitka.utils.FileOperations import (
    getFileContentByLine,
    getFileList,
    listDir,
)
from nuitka.utils.Utils import getOS, isWin32Windows

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


class NuitkaPluginNumpy(NuitkaPluginBase):
    """This class represents the main logic of the plugin.

    This is a plugin to ensure scripts using numpy, scipy, matplotlib, pandas,
    scikit-learn, etc. work well in standalone mode.

    While there already are relevant entries in the "ImplicitImports.py" plugin,
    this plugin copies any additional binary or data files required by many
    installations.

    """

    plugin_name = "numpy"  # Nuitka knows us by this name
    plugin_desc = "Required for numpy, scipy, pandas, matplotlib, etc."

    def __init__(self, include_matplotlib, include_scipy):
        self.include_numpy = True  # For consistency
        self.include_matplotlib = include_matplotlib
        self.include_scipy = include_scipy

        # Information about matplotlib install.
        self.matplotlib_info = None

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def reportFileCount(self, module_name, count):
        if count:
            msg = "Found %d %s DLLs from '%s' installation." % (
                count,
                "file" if count < 2 else "files",
                module_name.asString(),
            )

            self.info(msg)

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

    def getExtraDlls(self, module):
        """Copy extra shared libraries or data for this installation.

        Args:
            dist_dir: the name of the program's dist folder
            module: module object
        Returns:
            empty tuple
        """
        full_name = module.getFullName()

        if self.include_numpy and full_name == "numpy":
            numpy_binaries = tuple(
                self._getNumpyCoreBinaries(numpy_dir=module.getCompileTimeDirectory())
            )

            for full_path, target_filename in numpy_binaries:
                yield makeDllEntryPoint(
                    source_path=full_path,
                    dest_path=target_filename,
                    package_name=full_name,
                )

            self.reportFileCount(full_name, len(numpy_binaries))

        if full_name == "scipy" and self.include_scipy and isWin32Windows():
            scipy_binaries = tuple(
                self._getScipyCoreBinaries(scipy_dir=module.getCompileTimeDirectory())
            )

            for source_path, target_filename in scipy_binaries:
                yield makeDllEntryPoint(
                    source_path=source_path,
                    dest_path=target_filename,
                    package_name=full_name,
                )

            self.reportFileCount(full_name, len(scipy_binaries))

    def _getMatplotlibInfo(self):
        """Determine the filename of matplotlibrc and the default backend, etc.

        Notes:
            There might exist a local version outside 'matplotlib/mpl-data' which
            we then must use instead. Determine its name by aksing matplotlib.
        """
        # TODO: Replace this with using self.queryRuntimeInformationMultiple to remove
        # code duplication.
        if self.matplotlib_info is None:
            cmd = r"""\
from __future__ import print_function
from matplotlib import matplotlib_fname, get_backend, __version__
try:
    from matplotlib import get_data_path
except ImportError:
    from matplotlib import _get_data_path as get_data_path
from inspect import getsource
print(repr(matplotlib_fname()))
print(repr(get_backend()))
print(repr(get_data_path()))
print(repr(__version__))
print(repr("MATPLOTLIBDATA" in getsource(get_data_path)))
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

    @staticmethod
    def _getNumpyCoreBinaries(numpy_dir):
        """Return any binaries in numpy package.

        Notes:
            This covers the special cases like MKL binaries.

        Returns:
            tuple of abspaths of binaries.
        """
        numpy_core_dir = os.path.join(numpy_dir, "core")

        # first look in numpy/.libs for binaries
        libdir = os.path.join(numpy_dir, ".libs" if getOS() != "Darwin" else ".dylibs")
        if os.path.isdir(libdir):
            for full_path, filename in listDir(libdir):
                yield full_path, filename

        # Then look for libraries in numpy.core package path
        # should already return the MKL files in ordinary cases
        re_anylib = re.compile(r"\w+\.(?:dll|so|dylib)", re.IGNORECASE)

        for full_path, filename in listDir(numpy_core_dir):
            if not re_anylib.match(filename):
                continue

            yield full_path, filename

        # Also look for MKL libraries in folder "above" numpy.
        # This should meet the layout of Anaconda installs.
        base_prefix = getSystemPrefixPath()

        if isWin32Windows():
            lib_dir = os.path.join(base_prefix, "Library", "bin")
        else:
            lib_dir = os.path.join(base_prefix, "lib")

        if os.path.isdir(lib_dir):
            re_mkllib = re.compile(r"^(?:lib)?mkl\w+\.(?:dll|so|dylib)", re.IGNORECASE)

            for full_path, filename in listDir(lib_dir):
                if isWin32Windows():
                    if not (
                        filename.startswith(("libi", "libm", "mkl"))
                        and filename.endswith(".dll")
                    ):
                        continue
                else:
                    if not re_mkllib.match(filename):
                        continue

                yield full_path, filename

    @staticmethod
    def _getScipyCoreBinaries(scipy_dir):
        """Return binaries from the extra-dlls folder (Windows only)."""

        for dll_dir_name in ("extra_dll", ".libs"):
            dll_dir_path = os.path.join(scipy_dir, dll_dir_name)

            if os.path.isdir(dll_dir_path):
                for source_path, source_filename in listDir(dll_dir_path):
                    if source_filename.lower().endswith(".dll"):
                        yield source_path, os.path.join(
                            "scipy", dll_dir_name, source_filename
                        )

    def considerDataFiles(self, module):
        if module.getFullName() == "matplotlib":
            matplotlib_info = self._getMatplotlibInfo()

            if not os.path.isdir(matplotlib_info.data_path):
                self.sysexit(
                    "mpl-data missing, matplotlib installation appears to be broken"
                )

            # Include the "mpl-data" files.
            for fullname in getFileList(
                matplotlib_info.data_path,
                ignore_dirs=("sample_data",),
                ignore_filenames=("matplotlibrc",),
            ):
                filename = os.path.relpath(fullname, matplotlib_info.data_path)

                yield makeIncludedDataFile(
                    source_path=fullname,
                    dest_path=os.path.join("matplotlib", "mpl-data", filename),
                    reason="package data for 'matplotlib",
                )

            # Handle the config file with an update.
            new_lines = []  # new config file lines

            found = False  # checks whether backend definition encountered
            for line in getFileContentByLine(matplotlib_info.matplotlibrc_filename):
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

            yield makeIncludedGeneratedDataFile(
                data=new_lines,
                dest_path=os.path.join("matplotlib", "mpl-data", "matplotlibrc"),
                reason="Updated matplotlib config file with backend to use.",
            )

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # return driven, pylint: disable=too-many-return-statements
        if not self.include_scipy and module_name.hasOneOfNamespaces(
            "scipy", "sklearn", "skimage"
        ):
            return False, "Omit unneeded components"

        if not self.include_matplotlib and module_name.hasOneOfNamespaces(
            "matplotlib", "skimage"
        ):
            return False, "Omit unneeded components"

        if self.include_matplotlib and module_name.hasNamespace("mpl_toolkits"):
            return True, "Needed by matplotlib"

        if module_name in ("cv2", "cv2.cv2", "cv2.data"):
            return True, "Needed for OpenCV"

        if self.include_scipy and module_name in sklearn_mods:
            return True, "Needed by sklearn"

        # some special handling for matplotlib:
        # depending on whether 'tk-inter' resp. 'qt-plugins' are enabled,
        # matplotlib backends are included.
        if self.include_matplotlib:
            if hasActivePlugin("tk-inter"):
                if module_name in (
                    "matplotlib.backends.backend_tk",
                    "matplotlib.backends.backend_tkagg",
                    "matplotlib.backend.tkagg",
                ):
                    return True, "Needed for tkinter matplotplib backend"

            if getActiveQtPlugin() is not None:
                # Note, their code tries everything behind that name, the qt5 is
                # misleading therefore, PySide will work there too.
                if module_name in (
                    "matplotlib.backends.backend_qt5",
                    "matplotlib.backends.backend_qt5.py",
                    "matplotlib.backends.backend_qt5cairo.py",
                    "matplotlib.backend.backend_qt5.py",
                ):
                    return True, "Needed for Qt matplotplib backend"

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

        # Matplotlib might be off, or the version may not need the environment variable.
        if (
            self.include_matplotlib
            and module.getFullName() == "matplotlib"
            and self._getMatplotlibInfo().needs_matplotlibdata_env
        ):
            code = r"""
import os
os.environ["MATPLOTLIBDATA"] = os.path.join(__nuitka_binary_dir, "matplotlib", "mpl-data")
"""
            return (
                code,
                "Setting 'MATPLOTLIBDATA' environment variable for matplotlib to find package data.",
            )


class NuitkaPluginDetectorNumpy(NuitkaPluginBase):
    """Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = NuitkaPluginNumpy

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
