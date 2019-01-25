#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" User plug-in to make tkinter scripts work well in standalone mode.

To run properly, scripts need copies of the TCL / TK libraries as sub-folders
of the script's dist folder.
"""

import os
import shutil
import sys
from logging import info

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase, pre_modules, post_modules
from nuitka.utils import Execution, Utils
from nuitka.utils.FileOperations import (
    getFileList,
    getSubDirectories,
    removeDirectory
)

class TkinterPlugin(NuitkaPluginBase):
    """ This is for plugging in tkinter TCL / TK libraries and making sure
    that tkinter requests are directed to them.
    """

    plugin_name = "tk-plugin"

    def __init__(self):
        self.tk_dirs = False           # indicate dirs already copied

    @staticmethod
    def createPreModuleLoadCode(module):
        """Ensure that tkinter libs are being correctly pointed to
        **before** a module starts executing.
        """
        if os.name != "nt":
            return None, None
        code = """import os
if not os.environ.get("TCL_LIBRARY", None):
    import sys
    os.environ["TCL_LIBRARY"] = os.path.join(sys.path[0], "tcl")
    os.environ["TK_LIBRARY"] = os.path.join(sys.path[0], "tk")
"""
        full_name = module.getFullName()
        # only insert above code for tkinter modules
        if not "tkinter" in full_name.lower():
            return None, None
        return code, None

    def onModuleDiscovered(self, module):
        """Make sure our pre-module code is recorded.
        """

        if os.name != "nt":
            return None, None
        full_name = module.getFullName()

        pre_code, reason = self.createPreModuleLoadCode(module)
        if pre_code:
            if full_name is pre_modules:
                sys.exit("Error, conflicting plug-ins for %s" % full_name)

            pre_modules[full_name] = self._createTriggerLoadedModule(
                module       = module,
                trigger_name = "-preLoad",
                code         = pre_code
            )


    def considerExtraDlls(self, dist_dir, module):
        """Copy the TCL / TK directories to binary root directory (dist_dir).
        We do not tell the caller to copy anything: we are doing it ourselves.
        Therefore always return an empty tuple.

        Note: this code will work for Windows systems only.
        """
        if self.tk_dirs is True:            # already done
            return ()

        if os.name != "nt":
            info("tkinter plugin only supported under Windows")
            self.tk_dirs = True
            return ()

        if str is bytes:                    # last tk/tcl qualifyers Py 2
            tk_lq  = "tk8.5"
            tcl_lq = "tcl8.5"
        else:                               # last tk/tcl qualifyers Py 3+
            tk_lq  = "tk8.6"
            tcl_lq = "tcl8.6"

        # check various locations of the dirs
        sys_tcl = os.path.join(os.path.dirname(sys.executable), "tcl")
        tk  = os.path.join(sys_tcl, tk_lq)
        tcl = os.path.join(sys_tcl, tcl_lq)

        # if this was not the right place, try this:
        if not (os.path.exists(tk) and os.path.exists(tcl)):
            tk = os.environ.get("TCL_LIBRARY", None)
            tcl = os.environ.get("TCL_LIBRARY", None)
            if not (tk and tcl):
                info("could not find TK / TCL libraries")
                sys.exit("aborting standalone generation.")

        info("Starting copy of tkinter libraries.")
        tar_tk  = os.path.join(dist_dir, "tk")
        tar_tcl = os.path.join(dist_dir, "tcl")
        shutil.copytree(tk, tar_tk)
        shutil.copytree(tcl, tar_tcl)
        # Definitely do not need the demos and delete them again.
        # TODO: Anything else?
        shutil.rmtree(os.path.join(tar_tk, "demos"), ignore_errors=True)
        info("Finished copying tkinter libraries.")
        self.tk_dirs = True
        return ()



class TkinterPluginDetector(NuitkaPluginBase):
    plugin_name = "tk-plugin"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode() and os.name == "nt"

    def onModuleDiscovered(self, module):
        full_name = module.getFullName().split(".")
        if full_name[0].lower() == "tkinter":
            self.warnUnusedPlugin("tkinter support.")
