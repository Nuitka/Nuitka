#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Matplotlib standard plugin module. """
import os

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import getActiveQtPlugin, hasActivePlugin
from nuitka.utils.FileOperations import getFileContentByLine

# spellchecker: ignore matplotlib, scipy, scikit, matplotlibrc, matplotlibdata, mpl_toolkits, tkagg


class NuitkaPluginMatplotlib(NuitkaPluginBase):
    """This class represents the main logic of the plugin.

    This is a plugin to ensure scripts using numpy, scipy, matplotlib, pandas,
    scikit-learn, etc. work well in standalone mode.

    While there already are relevant entries in the "ImplicitImports.py" plugin,
    this plugin copies any additional binary or data files required by many
    installations.

    """

    plugin_name = "matplotlib"  # Nuitka knows us by this name
    plugin_desc = "Required for matplotlib module"

    @staticmethod
    def isAlwaysEnabled():
        """Request to be always enabled."""

        return True

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return isStandaloneMode()

    def _getMatplotlibInfo(self):
        """Determine the filename of matplotlibrc and the default backend, etc.

        Notes:
            There might exist a local version outside 'matplotlib/mpl-data' which
            we then must use instead. Determine its name by asking matplotlib.
        """
        info = self.queryRuntimeInformationMultiple(
            info_name="matplotlib_info",
            setup_codes="""
from matplotlib import matplotlib_fname, get_backend, __version__
try:
    from matplotlib import get_data_path
except ImportError:
    from matplotlib import _get_data_path as get_data_path
from inspect import getsource
""",
            values=(
                ("matplotlibrc_filename", "matplotlib_fname()"),
                ("backend", "get_backend()"),
                ("data_path", "get_data_path()"),
                ("matplotlib_version", "__version__"),
                (
                    "needs_matplotlibdata_env",
                    "'MATPLOTLIBDATA' in getsource(get_data_path)",
                ),
            ),
        )

        if info is None:
            self.sysexit("Error, it seems 'matplotlib' is not installed or broken.")

        return info

    def considerDataFiles(self, module):
        if module.getFullName() != "matplotlib":
            return

        matplotlib_info = self._getMatplotlibInfo()

        if not os.path.isdir(matplotlib_info.data_path):
            self.sysexit(
                "mpl-data missing, matplotlib installation appears to be broken"
            )

        # Include the "mpl-data" files.
        yield self.makeIncludedDataDirectory(
            source_path=matplotlib_info.data_path,
            dest_path=os.path.join("matplotlib", "mpl-data"),
            ignore_dirs=("sample_data",),
            ignore_filenames=("matplotlibrc",),
            reason="package data for 'matplotlib",
            tags="mpl-data",
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

        yield self.makeIncludedGeneratedDataFile(
            data=new_lines,
            dest_path=os.path.join("matplotlib", "mpl-data", "matplotlibrc"),
            reason="updated matplotlib config file with backend to use",
        )

    def onModuleEncounter(self, module_name, module_filename, module_kind):
        if module_name.hasNamespace("mpl_toolkits"):
            return True, "Needed by matplotlib"

        # some special handling for matplotlib:
        # depending on whether 'tk-inter' resp. 'qt-plugins' are enabled,
        # their matplotlib backends are included.
        if hasActivePlugin("tk-inter"):
            if module_name in (
                "matplotlib.backends.backend_tk",
                "matplotlib.backends.backend_tkagg",
                "matplotlib.backend.tkagg",
            ):
                return True, "Needed for tkinter matplotlib backend"

        if getActiveQtPlugin() is not None:
            # Note, their code tries everything behind that name, the qt5 is
            # misleading therefore, PySide will work there too.
            if module_name in (
                "matplotlib.backends.backend_qt5",
                "matplotlib.backends.backend_qt5.py",
                "matplotlib.backends.backend_qt5cairo.py",
                "matplotlib.backend.backend_qt5.py",
            ):
                return True, "Needed for Qt matplotlib backend"

        if module_name == "matplotlib.backends.backend_agg":
            return True, "Needed as standard matplotlib backend"

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

        # The version may not need the environment variable.
        if (
            module.getFullName() == "matplotlib"
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
