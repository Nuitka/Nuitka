#     Copyright 2024, Jorj McKie, mailto:<jorj.x.mckie@outlook.de> find license text at end of file


""" Details see below in class definition.
"""

import os
import sys

from nuitka.Options import isStandaloneMode, shallCreateAppBundle
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonFlavors import isHomebrewPython
from nuitka.PythonVersions import getSystemPrefixPath, getTkInterVersion
from nuitka.utils.Utils import isMacOS, isWin32Windows

# spell-checker: ignore tkinterdnd,tkdnd,tcltk


def _isTkInterModule(module):
    full_name = module.getFullName()
    return full_name in ("Tkinter", "tkinter", "PySimpleGUI", "PySimpleGUI27")


def _getHomebrewPrefix(logger):
    result = os.path.normpath(
        os.path.join(getSystemPrefixPath(), "..", "..", "..", "..", "..", "..", "..")
    )

    if not os.path.isdir(result):
        logger.sysexit("Error, failed to determine Homebrew prefix, report this bug.")

    return result


class NuitkaPluginTkinter(NuitkaPluginBase):
    """This class represents the main logic of the TkInter plugin.

     This is a plug-in to make programs work well in standalone mode which are using tkinter.
     These programs require the presence of certain libraries written in the TCL language.
     On Windows platforms, and even on Linux, the existence of these libraries cannot be
     assumed. We therefore

     1. Copy the TCL libraries as sub-folders to the program's dist folder
     2. Redirect the program's tkinter requests to these library copies. This is
        done by setting appropriate variables in the os.environ dictionary.
        Tkinter will use these variable value to locate the library locations.

     Each time before the program issues an import to a tkinter module, we make
     sure, that the TCL environment variables are correctly set.

    Notes:
         You can enforce using a specific TCL folder by using TCL_LIBRARY
         and a Tk folder by using TK_LIBRARY, but that ought to normally
         not be necessary.
    """

    plugin_name = "tk-inter"  # Nuitka knows us by this name
    plugin_desc = "Required by Python's Tk modules."
    # Automatically suppress detectors for any other toolkit
    plugin_gui_toolkit = True

    # Only used in control tags
    binding_name = "tkinter"

    def __init__(self, tcl_library_dir, tk_library_dir):
        self.tcl_library_dir = tcl_library_dir
        self.tk_library_dir = tk_library_dir

        # ensure one-time action, we deal with several names for the execution,
        # yet we only want to do it once.
        self.files_copied = False

        self.tk_inter_version = getTkInterVersion()

        if self.tk_inter_version is None:
            self.sysexit("Error, it seems 'tk-inter' is not installed.")

        # Only ever saw these 2 in use.
        assert self.tk_inter_version in ("8.5", "8.6"), self.tk_inter_version

        return None

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone, else False.
        """
        return isStandaloneMode()

    @staticmethod
    def createPreModuleLoadCode(module):
        """This method is called with a module that will be imported.

        Notes:
            If the word "tkinter" occurs in its full name, we know that the correct
            setting of the TCL environment must be ensured before this happens.

        Args:
            module: the module object
        Returns:
            Code to insert and None (tuple)
        """
        # only insert code for tkinter related modules
        if _isTkInterModule(module):
            # The following code will be executed before importing the module.
            # If required we set the respective environment values.
            code = r"""
import os
os.environ["TCL_LIBRARY"] = os.path.join(__nuitka_binary_dir, "tcl")
os.environ["TK_LIBRARY"] = os.path.join(__nuitka_binary_dir, "tk")"""

            return code, "Need to make sure we set environment variables for TCL."

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--tk-library-dir",
            action="store",
            dest="tk_library_dir",
            default=None,
            help="""\
The Tk library dir. Nuitka is supposed to automatically detect it, but you can
override it here. Default is automatic detection.""",
        )

        group.add_option(
            "--tcl-library-dir",
            action="store",
            dest="tcl_library_dir",
            default=None,
            help="""\
The Tcl library dir. See comments for Tk library dir.""",
        )

    def _getTclCandidatePaths(self):
        # Check typical locations of the dirs
        yield os.getenv("TCL_LIBRARY")

        # Inside the Python install, esp. on Windows.
        for sys_prefix_path in (sys.prefix, getSystemPrefixPath()):
            yield os.path.join(sys_prefix_path, "tcl", "tcl%s" % self.tk_inter_version)
            yield os.path.join(sys_prefix_path, "lib", "tcl%s" % self.tk_inter_version)

            # Newer Anaconda.
            yield os.path.join(
                sys_prefix_path, "Library", "lib", "tcl%s" % self.tk_inter_version
            )

        # System installs on non-Windows
        if not isWin32Windows():
            yield "/usr/share/tcltk/tcl%s" % self.tk_inter_version
            yield "/usr/share/tcl%s" % self.tk_inter_version
            yield "/usr/lib64/tcl/tcl%s" % self.tk_inter_version
            yield "/usr/lib/tcl%s" % self.tk_inter_version

        if isHomebrewPython():
            yield os.path.normpath(
                os.path.join(
                    _getHomebrewPrefix(self),
                    "lib",
                    "tcl%s" % self.tk_inter_version,
                )
            )

            # Homebrew is compiled to think it's 8.6, but it might actually
            # be the version 9.
            yield os.path.normpath(
                os.path.join(
                    _getHomebrewPrefix(self),
                    "lib",
                    "tcl9",
                )
            )

    def _getTkCandidatePaths(self):
        yield os.getenv("TK_LIBRARY")

        for sys_prefix_path in (sys.prefix, getSystemPrefixPath()):
            yield os.path.join(sys_prefix_path, "tcl", "tk%s" % self.tk_inter_version)
            yield os.path.join(sys_prefix_path, "lib", "tk%s" % self.tk_inter_version)

            # Newer Anaconda.
            yield os.path.join(
                sys_prefix_path, "Library", "lib", "tk%s" % self.tk_inter_version
            )

        if not isWin32Windows():
            yield "/usr/share/tcltk/tk%s" % self.tk_inter_version
            yield "/usr/share/tk%s" % self.tk_inter_version
            yield "/usr/lib64/tcl/tk%s" % self.tk_inter_version
            yield "/usr/lib/tk%s" % self.tk_inter_version

        if isHomebrewPython():
            yield os.path.normpath(
                os.path.join(
                    _getHomebrewPrefix(self),
                    "lib",
                    "tk%s" % self.tk_inter_version,
                )
            )

            # Homebrew is compiled to think it's 8.6, but it might actually
            # be the version 9.
            yield os.path.normpath(
                os.path.join(
                    _getHomebrewPrefix(self),
                    "lib",
                    "tk9.0",
                )
            )

    def considerDataFiles(self, module):
        """Provide TCL libraries to the dist folder.

        Notes:
            We will provide the copy the TCL/TK directories to the program's root directory,
            that might be shiftable with some work.

        Args:
            module: the module in question, maybe ours

        Yields:
            IncludedDataFile objects.
        """

        if not _isTkInterModule(module) or self.files_copied:
            return

        tcl_library_dir = self.tcl_library_dir
        if tcl_library_dir is None:
            for tcl_library_dir in self._getTclCandidatePaths():
                if tcl_library_dir is not None and os.path.exists(
                    os.path.join(tcl_library_dir, "init.tcl")
                ):
                    break

        if tcl_library_dir is None or not os.path.exists(tcl_library_dir):
            self.sysexit(
                """\
Could not find Tcl, you might need to use '--tcl-library-dir' and if \
that works, report a bug so it can be added to Nuitka."""
            )

        tk_library_dir = self.tk_library_dir
        if tk_library_dir is None:
            for tk_library_dir in self._getTkCandidatePaths():
                if tk_library_dir is not None and os.path.exists(
                    os.path.join(tk_library_dir, "dialog.tcl")
                ):
                    break

        if tk_library_dir is None or not os.path.exists(tk_library_dir):
            self.sysexit(
                """\
Could not find Tk, you might need to use '--tk-library-dir' and if \
that works, report a bug."""
            )

        # survived the above, now do provide the locations
        yield self.makeIncludedDataDirectory(
            source_path=tk_library_dir,
            dest_path="tk",
            reason="Tk needed for tkinter usage",
            ignore_dirs=("demos",),
            tags="tk",
        )
        yield self.makeIncludedDataDirectory(
            source_path=tcl_library_dir,
            ignore_dirs=(
                ("opt0.4", "http1.0") if isMacOS() and shallCreateAppBundle() else ()
            ),
            dest_path="tcl",
            reason="Tcl needed for tkinter usage",
            tags="tcl",
        )

        if isWin32Windows():
            yield self.makeIncludedDataDirectory(
                source_path=os.path.join(tcl_library_dir, "..", "tcl8"),
                dest_path="tcl8",
                reason="Tcl needed for tkinter usage",
                tags="tcl",
            )

        self.files_copied = True

    def onModuleCompleteSet(self, module_set):
        if str is bytes:
            plugin_binding_name = "Tkinter"
        else:
            plugin_binding_name = "tkinter"

        self.onModuleCompleteSetGUI(
            module_set=module_set, plugin_binding_name=plugin_binding_name
        )


class NuitkaPluginDetectorTkinter(NuitkaPluginBase):
    """Used only if plugin is not activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = NuitkaPluginTkinter

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation on Windows, else False.
        """
        return isStandaloneMode()

    def checkModuleSourceCode(self, module_name, source_code):
        """This method checks the source code

        Notes:
            We only use it to check whether this is the main module, and whether
            it contains the keyword "tkinter".
            We assume that the main program determines whether tkinter is used.
            References by dependent or imported modules are assumed irrelevant.

        Args:
            module_name: the name of the module
            source_code: the module's source code

        Returns:
            None
        """
        if module_name == "__main__":
            for line in source_code.splitlines():
                # Ignore comments.
                if "#" in line:
                    line = line[: line.find("#")]

                if "tkinter" in line or "Tkinter" in line:
                    self.warnUnusedPlugin("Tkinter needs TCL included.")
                    break


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
