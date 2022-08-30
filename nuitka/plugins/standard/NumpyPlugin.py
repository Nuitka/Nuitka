#     Copyright 2022, Jorj McKie, mailto:<jorj.x.mckie@outlook.de>
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

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import getSystemPrefixPath
from nuitka.utils.FileOperations import listDir, listDllFilesFromDirectory
from nuitka.utils.Utils import isMacOS, isWin32Windows

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

    This is a plugin to ensure scripts using numpy, scipy work well in
    standalone mode.

    While there already are relevant entries in the "ImplicitImports.py" plugin,
    this plugin copies any additional binary or data files required by many
    installations.

    """

    plugin_name = "numpy"  # Nuitka knows us by this name
    plugin_desc = "Required for numpy."

    def __init__(self, include_scipy):
        self.include_numpy = True  # For consistency
        self.include_scipy = include_scipy

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

    def getExtraDlls(self, module):
        """Copy extra shared libraries or data for this installation.

        Args:
            module: module object
        Yields:
            DLL entry point objects
        """
        full_name = module.getFullName()

        if self.include_numpy and full_name == "numpy":
            numpy_binaries = tuple(
                self._getNumpyCoreBinaries(numpy_dir=module.getCompileTimeDirectory())
            )

            for full_path, target_filename in numpy_binaries:
                yield self.makeDllEntryPoint(
                    source_path=full_path,
                    dest_path=target_filename,
                    package_name=full_name,
                    reason="core binary of 'numpy'",
                )

            self.reportFileCount(full_name, len(numpy_binaries))

        if full_name == "scipy" and self.include_scipy and isWin32Windows():
            scipy_binaries = tuple(
                self._getScipyCoreBinaries(scipy_dir=module.getCompileTimeDirectory())
            )

            for source_path, target_filename in scipy_binaries:
                yield self.makeDllEntryPoint(
                    source_path=source_path,
                    dest_path=target_filename,
                    package_name=full_name,
                    reason="core binary of 'scipy'",
                )

            self.reportFileCount(full_name, len(scipy_binaries))

    @staticmethod
    def _getNumpyCoreBinaries(numpy_dir):
        """Return any binaries in numpy package.

        Notes:
            This covers the special cases like MKL binaries.

        Returns:
            tuple of abspaths of binaries.
        """
        # First look in numpy folder for binaries, this is for PyPI package.
        numpy_lib_dir = os.path.join(numpy_dir, ".libs" if not isMacOS() else ".dylibs")
        if os.path.isdir(numpy_lib_dir):
            for full_path, filename in listDir(numpy_lib_dir):
                yield full_path, filename

        # Then look for libraries in numpy.core package path should already
        # return the MKL files in ordinary cases
        numpy_core_dir = os.path.join(numpy_dir, "core")
        if os.path.exists(numpy_core_dir):
            for full_path, filename in listDllFilesFromDirectory(numpy_core_dir):
                yield full_path, filename

        # Also look for MKL libraries in folder "above" numpy.
        # This should meet the layout of Anaconda installs.
        base_prefix = getSystemPrefixPath()

        if isWin32Windows():
            lib_dir = os.path.join(base_prefix, "Library", "bin")
        else:
            lib_dir = os.path.join(base_prefix, "lib")

        # TODO: This doesn't actually match many files on macOS and seems not needed
        # there, check if it has an impact on Windows, where maybe DLL detection is
        # weaker.
        if os.path.isdir(lib_dir):
            for full_path, filename in listDir(lib_dir):
                if isWin32Windows():
                    if not (
                        filename.startswith(("libi", "libm", "mkl"))
                        and filename.endswith(".dll")
                    ):
                        continue
                else:
                    re_mkllib = re.compile(
                        r"^(?:lib)?mkl[_\w]+\.(?:dll|so|dylib)", re.IGNORECASE
                    )

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

    def onModuleEncounter(self, module_name, module_filename, module_kind):
        if not self.include_scipy and module_name.hasOneOfNamespaces(
            "scipy", "sklearn", "skimage"
        ):
            return False, "Omit unneeded components"

        if module_name in ("cv2", "cv2.cv2", "cv2.data"):
            return True, "Needed for OpenCV"

        if self.include_scipy and module_name in sklearn_mods:
            return True, "Needed by sklearn"


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
        if module_name == "numpy":
            self.warnUnusedPlugin("Numpy may miss DLLs otherwise.")
