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
import shutil
import sys
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import UserPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.Utils import isWin32Windows


def _isTkInterModule(module):
    full_name = module.getFullName()

    if python_version < 300:
        return full_name == "Tkinter"
    else:
        return full_name == "tkinter"


class TkinterPlugin(UserPluginBase):
    """ This class represents the main logic of the plugin.

    This is a plug-in to make programs work well in standalone mode which are using tkinter.
    These programs require the presence of certain libraries written in the TCL language.
    On Windows platforms, the existence of these libraries cannot be assumed. We therefore

    1. Copy the TCL libraries as sub-folders to the program's dist folder
    2. Redirect the program's tkinter requests to these library copies. This is
       done by setting appropriate variables in the os.environ dictionary.
       Tkinter will use these variable value to locate the library locations.

    Each time before the program issues an import to a tkinter module, we make
    sure, that the TCL environment variables are correctly set.

    Args:
        UserPluginBase: the plugin template class we are inheriting.
    """

    plugin_name = "tk-inter"  # Nuitka knows us by this name

    @staticmethod
    def createPreModuleLoadCode(module):
        """ This method is called with a module that will be imported.

        Notes:
            If the word "tkinter" occurs in its full name, we know that the correct
            setting of the TCL environment must be ensured before this happens.

        Args:
            module: the module object
        Returns:
            Code to insert and None (tuple)
        """
        if not isWin32Windows():  # we are only relevant on Windows
            return None, None

        # only insert code for tkinter related modules
        if not _isTkInterModule(module):
            return None, None

        # The following code will be executed before importing the module.
        # If required we set the respective environment values.
        code = """import os
if not os.environ.get("TCL_LIBRARY", None):
    os.environ["TCL_LIBRARY"] = os.path.join(__nuitka_binary_dir, "tcl")
    os.environ["TK_LIBRARY"] = os.path.join(__nuitka_binary_dir, "tk")"""
        return code, "Need to make sure we set environment variables for TCL."

    def considerExtraDlls(self, dist_dir, module):
        """ Copy TCL libraries to the dist folder.

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

        if not isWin32Windows():  # if not Windows notify wrong usage once
            info("tkinter plugin supported on Windows only")
            return ()

        if python_version < 340:  # last tk/tcl qualifyers Py 2
            tk_lq = "tk8.5"
            tcl_lq = "tcl8.5"
        else:  # last tk/tcl qualifyers Py 3+
            tk_lq = "tk8.6"
            tcl_lq = "tcl8.6"

        # check possible locations of the dirs
        sys_tcl = os.path.join(os.path.dirname(sys.executable), "tcl")
        tk = os.path.join(sys_tcl, tk_lq)
        tcl = os.path.join(sys_tcl, tcl_lq)

        # if this was not the right place, try this:
        if not (os.path.exists(tk) and os.path.exists(tcl)):
            tk = os.environ.get("TK_LIBRARY", None)
            tcl = os.environ.get("TCL_LIBRARY", None)
            if not (tk and tcl):
                info(" Could not find TK / TCL libraries")
                sys.exit("aborting standalone generation.")

        # survived the above, now do the copying to following locations
        tar_tk = os.path.join(dist_dir, "tk")
        tar_tcl = os.path.join(dist_dir, "tcl")

        info(" Now copying tk libraries from %r." % tk)  # just to entertain
        shutil.copytree(tk, tar_tk)
        info(" Now copying tkinter libraries from %r." % tcl)  # just to entertain
        shutil.copytree(tcl, tar_tcl)

        # Definitely don't need the demos, so remove them again.
        # TODO: Anything else?
        shutil.rmtree(os.path.join(tar_tk, "demos"), ignore_errors=True)

        return ()


class TkinterPluginDetector(UserPluginBase):
    """ Used only if plugin is not activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    plugin_name = "tk-inter"  # this is how Nuitka knows us

    @staticmethod
    def isRelevant():
        """ This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation on Windows, else False.
        """
        return Options.isStandaloneMode() and isWin32Windows()

    def onModuleSourceCode(self, module_name, source_code):
        """ This method passes the source code and expects it back - potentially modified.

        Notes:
            We only use it to check whether this is the main module, and whether
            it contains the keyword "tkinter".
            We assume that the main program determines whether tkinter is used.
            References by dependent or imported modules are assumed irrelevant.

        Args:
            module_name: the name of the module
            source_code: the module's source code

        Returns:
            source_code
        """
        if module_name == "__main__":
            if "tkinter" in source_code or "Tkinter" in source_code:
                self.warnUnusedPlugin("Tkinter needs TCL included.")

        return source_code
