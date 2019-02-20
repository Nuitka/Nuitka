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
"""
This is a plug-in to make programs work well in standalone mode which are
using tkinter. These programs require the presence of certain libraries
written in the TCL language. On Windows platforms, the existence of these
libraries cannot be assumed. We therefore

1. Copy the TCL libraries as sub-folders to the program's dist folder
2. Redirect the program's tkinter requests to these library copies. This is
   done by setting appropriate variables in the os.environ dictionary.
   Tkinter will use these variable value to locate the library locations.

Each time before the program issues an import to a tkinter module, we make
sure, that the TCL environment variables are correctly set.

"""

import os
import shutil
import sys
from logging import info

from nuitka import Options
from nuitka.utils.Utils import isWin32Windows
from nuitka.plugins.PluginBase import UserPluginBase, pre_modules


## This class represents the main logic of the plugin.
# It contains the Nuitka identifier, determines if we need to insert code
# and copies TCL libraries.
# @param UserPluginBase is the plugin template class we are inheriting.
#
class TkinterPlugin(UserPluginBase):

    plugin_name = "tk-plugin"  # Nuitka knows us by this name

    ## We need to ensure certain actions are executed only once.
    # The following indicator is set to true if we are done.
    def __init__(self):
        self.files_copied = False  # ensure that file copy occurs once only

    @staticmethod
    ## This method is called with a module that will be imported.
    # If the word "tkinter" occurs in its full name, we know that the correct
    # setting of the TCL environment must be ensured before this happens.
    # @param module the module object
    # @returns code to insert and None (tuple)
    def createPreModuleLoadCode(module):
        if not isWin32Windows():  # we are only relevant on Windows
            return None, None

        full_name = module.getFullName()

        # only insert code for tkinter related modules
        if not "tkinter" in full_name.lower():
            return None, None

        # The following code will be executed before importing the module.
        # If required we set the respective environment values.
        code = """import os
if not os.environ.get("TCL_LIBRARY", None):
    import sys
    os.environ["TCL_LIBRARY"] = os.path.join(sys.path[0], "tcl")
    os.environ["TK_LIBRARY"] = os.path.join(sys.path[0], "tk")
"""
        return code, None

    ## This method is called to let us check, whether a to-be imported
    # module is relevant for us.
    # In our case, we insert code to be executed before such an import
    # happens.
    # @param module the module object
    def onModuleDiscovered(self, module):
        if not isWin32Windows():  # only relevant on Windows
            return None, None

        # call the previous method to make the code
        pre_code, _ = self.createPreModuleLoadCode(module)
        
        if pre_code:
            # We found the module relevant. We must ensure that we are the
            # only plugin that prepends code to it (other plugins might still
            # append code to the same module).
            full_name = module.getFullName()
            if full_name is pre_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            # store module and our code in a list
            pre_modules[full_name] = self._createTriggerLoadedModule(
                module=module, trigger_name="-preLoad", code=pre_code
            )

    ## This method is called to let us insert extra data.
    # We will copy the TCL/TK directories to the program's root directory.
    # The general intention is that we return a tuple of file names.
    # We need however two subdirectories inserted, and therefore do the
    # copy ourselves and return an empty tuple.
    # @param dist_dir: the name of the program's dist folder
    # @param module the module object (not used here)
    #
    # Note: we will skip this method if not running on Windows platforms.
    def considerExtraDlls(self, dist_dir, module):
        if self.files_copied:  # skip after first invocation
            return ()

        if not isWin32Windows():  # if not Windows notify wrong usage once
            info("tkinter plugin supported under Windows only")
            self.files_copied = True
            return ()

        self.files_copied = True  # execute the following ever only once

        if str is bytes:  # last tk/tcl qualifyers Py 2
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

        info(" Now copying tkinter libraries.")  # just to entertain
        shutil.copytree(tk, tar_tk)
        shutil.copytree(tcl, tar_tcl)

        # Definitely don't need the demos, so remove them again.
        # TODO: Anything else?
        shutil.rmtree(os.path.join(tar_tk, "demos"), ignore_errors=True)

        info(" Finished copying tkinter libraries.")
        return ()


## This class is used only if plugin is not activated.
# We are given the chance to issue a warning if we think we may be required.
class TkinterPluginDetector(UserPluginBase):
    plugin_name = "tk-plugin"  # this is how Nuitka knows us

    @staticmethod
    ## This method is called one time only to check, whether the plugin
    # might make sense at all.
    # We return true if this is a standalone compilation on Windows.
    def isRelevant():
        return Options.isStandaloneMode() and isWin32Windows()

    ## This method passes the source code and expects it back - potentially
    # modified.
    # We only use it to check whether this is the main module, and whether
    # it contains the keyword "tkinter".
    # We assume that the main program determines whether tkinter is used.
    # References by dependent or imported modules are assumed irrelevant.
    # @param module_name the name of the module
    # @param source_code the module's source code
    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "__main__":
            if "tkinter" in source_code or "Tkinter" in source_code:
                self.warnUnusedPlugin("Tkinter needs TCL included.")

        return source_code
