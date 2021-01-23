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
import shutil
import sys

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import copyTree


def _isTkInterModule(module):
    full_name = module.getFullName()
    return full_name in ("Tkinter", "tkinter", "PySimpleGUI", "PySimpleGUI27")


class TkinterPlugin(NuitkaPluginBase):
    """This class represents the main logic of the plugin.

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

    Args:
        NuitkaPluginBase: the plugin template class we are inheriting.

    Notes:
        You can enforce using a specific TCL folder by using TCL_LIBRARY
        and a Tk folder by using TK_LIBRARY, but that ought to normally
        not be necessary.
    """

    plugin_name = "tk-inter"  # Nuitka knows us by this name
    plugin_desc = "Required by Python's Tk modules"

    def __init__(self, tcl_library_dir, tk_library_dir):
        self.tcl_library_dir = tcl_library_dir
        self.tk_library_dir = tk_library_dir

        self.files_copied = False  # ensure one-time action
        return None

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone, else False.
        """
        return Options.isStandaloneMode()

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
        if not _isTkInterModule(module):
            return None, None

        # The following code will be executed before importing the module.
        # If required we set the respective environment values.
        code = """import os
if not os.environ.get("TCL_LIBRARY"):
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
override it here. Should it fail to discover, please report the bug. Default
is automatic detection.""",
        )

        group.add_option(
            "--tcl-library-dir",
            action="store",
            dest="tcl_library_dir",
            default=None,
            help="""\
The Tcl library dir. See comments for Tk library dir.""",
        )

    def considerExtraDlls(self, dist_dir, module):
        """Copy TCL libraries to the dist folder.

        Notes:
            We will copy the TCL/TK directories to the program's root directory.
            The general intention is that we return a tuple of file names.
            We need however two subdirectories inserted, and therefore do the
            copy ourselves and return an empty tuple.

        Args:
            dist_dir: the name of the program's dist folder
            module: the module object (not used here)

        Returns:
            None
        """
        if not _isTkInterModule(module):
            return ()
        if self.files_copied:
            return ()
        self.files_copied = True

        # Check typical locations of the dirs
        candidates_tcl = (
            os.environ.get("TCL_LIBRARY"),
            os.path.join(sys.prefix, "tcl", "tcl8.5"),
            os.path.join(sys.prefix, "tcl", "tcl8.6"),
            "/usr/share/tcltk/tcl8.6",
            "/usr/share/tcltk/tcl8.5",
            "/usr/share/tcl8.6",
            "/usr/share/tcl8.5",
            "/usr/lib64/tcl/tcl8.5",
            "/usr/lib64/tcl/tcl8.6",
        )
        candidates_tk = (
            os.environ.get("TK_LIBRARY"),
            os.path.join(sys.prefix, "tcl", "tk8.5"),
            os.path.join(sys.prefix, "tcl", "tk8.6"),
            "/usr/share/tcltk/tk8.6",
            "/usr/share/tcltk/tk8.5",
            "/usr/share/tk8.6",
            "/usr/share/tk8.5",
            "/usr/lib64/tcl/tk8.5",
            "/usr/lib64/tcl/tk8.6",
        )

        tcl = self.tcl_library_dir
        if tcl is None:
            for tcl in candidates_tcl:
                if tcl is not None and os.path.exists(tcl):
                    break

        if tcl is None or not os.path.exists(tcl):
            self.sysexit("Could not find Tcl. Aborting standalone generation.")

        tk = self.tk_library_dir
        if tk is None:
            for tk in candidates_tk:
                if tk is not None and os.path.exists(tk):
                    break

        if tk is None or not os.path.exists(tcl):
            self.sysexit("Could not find Tk. Aborting standalone generation.")

        # survived the above, now do the copying to following locations
        target_tk = os.path.join(dist_dir, "tk")
        target_tcl = os.path.join(dist_dir, "tcl")

        copyTree(tk, target_tk)
        self.info("Copied Tk libraries from %s." % tk)  # just to entertain

        # Definitely don't need the demos, so remove them again.
        # TODO: Anything else?
        shutil.rmtree(os.path.join(target_tk, "demos"), ignore_errors=True)

        copyTree(tcl, target_tcl)
        self.info("Copied TCL libraries from %s." % tcl)  # just to entertain

        return ()


class TkinterPluginDetector(NuitkaPluginBase):
    """Used only if plugin is not activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = TkinterPlugin

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation on Windows, else False.
        """
        return Options.isStandaloneMode()

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
