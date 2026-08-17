#     Copyright 2020, Jorj McKie, mailto:<jorj.x.mckie@outlook.de> find license text at end of file


"""Details see below in class definition."""

import io
import os
import sys

from nuitka.options.Options import isStandaloneMode, shallCreateAppBundle
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonFlavors import (
    getHomebrewInstallPath,
    isHomebrewPython,
    isPyenvHomebrewPython,
)
from nuitka.PythonVersions import getSystemPrefixPath, getTkInterVersion
from nuitka.utils.FileOperations import listDir
from nuitka.utils.Utils import isMacOS, isWin32Windows
from nuitka.utils.Zipfiles import createZipFile, doesZipFileMatch, getZipFile

# spell-checker: ignore tcltk,tcltest


def _isTkInterModule(module):
    full_name = module.getFullName()
    return full_name in ("Tkinter", "tkinter", "PySimpleGUI", "PySimpleGUI27")


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
    plugin_desc = "Required by 'tkinter' package."
    plugin_category = "package-support"

    # Automatically suppress detectors for any other toolkit
    plugin_gui_toolkit = True

    # Only used in control tags
    binding_name = "tkinter"

    _tcl_ignore_filenames = (
        "tcltest-2.3.6.tm",
        "tcltest-2.3.8.tm",
        "tcltest-2.4.0.tm",
        "tcltest-2.5.0.tm",
        "tcltest-2.5.3.tm",
        "tcltest-2.5.8.tm",
        "tcltest.tcl",
    )
    _tcl_ignore_dirs = ("tcltest",)
    _tcl_ignore_dirs_appbundle = ("opt0.4", "http1.0")
    _tk_ignore_dirs = ("demos",)

    def __init__(self, tcl_library_dir, tk_library_dir):
        self.tcl_library_dir = tcl_library_dir
        self.tk_library_dir = tk_library_dir

        # ensure one-time action, we deal with several names for the execution,
        # yet we only want to do it once.
        self.files_copied = False
        self._tcl_is_zip = False
        self._tk_is_zip = False

        self.tk_inter_version = getTkInterVersion()

        if self.tk_inter_version is None:
            self.sysexit("Error, it seems 'tk-inter' is not installed.")

        # Only ever saw these in use, report if there are more.
        if self.tk_inter_version not in ("8.5", "8.6", "9.0"):
            self.sysexit("""\
Error, it seems 'tk-inter' has an unsupported version '%s'. \
Please report as a issue.""" % self.tk_inter_version)

        return None

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone, else False.
        """
        return isStandaloneMode()

    def createPreModuleLoadCode(self, module):
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
            # If the original library was a zip, we provide a zip file as well.
            tcl_target = self.getTclTargetPath()
            tk_target = self.getTkTargetPath()

            if self._tcl_is_zip:
                tcl_target += ".zip"
            if self._tk_is_zip:
                tk_target += ".zip"

            # The following code will be executed before importing the module.
            # If required we set the respective environment values.
            code = r"""
import os
os.environ["TCL_LIBRARY"] = os.path.join(__nuitka_binary_dir, "%(tcl_target_path)s")
os.environ["TK_LIBRARY"] = os.path.join(__nuitka_binary_dir, "%(tk_target_path)s")""" % {
                "tcl_target_path": tcl_target,
                "tk_target_path": tk_target,
            }

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
        tcl_library = os.getenv("TCL_LIBRARY")
        if tcl_library is not None:
            yield tcl_library

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

        if isHomebrewPython() or isPyenvHomebrewPython():
            yield os.path.normpath(
                os.path.join(
                    getHomebrewInstallPath(),
                    "lib",
                    "tcl%s" % self.tk_inter_version,
                )
            )

            # Homebrew is compiled to think it's 8.6, but it might actually
            # be the version 9.
            yield os.path.normpath(
                os.path.join(
                    getHomebrewInstallPath(),
                    "lib",
                    "tcl9",
                )
            )

        if isMacOS():
            yield os.path.normpath(
                os.path.join(
                    getSystemPrefixPath(),
                    "Frameworks",
                    "Tcl.framework",
                    "Resources",
                    "Scripts",
                )
            )

    def _getTkCandidatePaths(self):
        tk_library = os.getenv("TK_LIBRARY")
        if tk_library is not None:
            yield tk_library

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

        if isHomebrewPython() or isPyenvHomebrewPython():
            yield os.path.normpath(
                os.path.join(
                    getHomebrewInstallPath(),
                    "lib",
                    "tk%s" % self.tk_inter_version,
                )
            )

            if self.tk_inter_version == "8.6":
                # Homebrew is compiled to think it's 8.6, but it might actually
                # be the version 9.
                yield os.path.normpath(
                    os.path.join(
                        getHomebrewInstallPath(),
                        "lib",
                        "tk9.0",
                    )
                )

        if isMacOS():
            yield os.path.normpath(
                os.path.join(
                    getSystemPrefixPath(),
                    "Frameworks",
                    "Tk.framework",
                    "Resources",
                    "Scripts",
                )
            )

    @staticmethod
    def _getZipCandidatePaths(candidate_paths, prefixes):
        seen_bases = set()
        for candidate_path in candidate_paths:
            # Env var may already point directly to a zip file.
            if candidate_path.endswith(".zip"):
                if os.path.isfile(candidate_path):
                    yield candidate_path
                continue

            base = os.path.dirname(candidate_path)
            if not base or base in seen_bases:
                continue
            seen_bases.add(base)

            if os.path.isdir(base):
                for full_path, filename in reversed(listDir(base)):
                    if filename.endswith(".zip") and filename.startswith(prefixes):
                        yield full_path

    def _getTclZipCandidatePaths(self):
        for candidate in self._getZipCandidatePaths(
            candidate_paths=self._getTclCandidatePaths(), prefixes=("libtcl", "tcl")
        ):
            yield candidate

    def _getTkZipCandidatePaths(self):
        for candidate in self._getZipCandidatePaths(
            candidate_paths=self._getTkCandidatePaths(), prefixes=("libtk", "tk")
        ):
            yield candidate

    def _makeIncludedFromZip(
        self, source_path, dest_path, reason, tags, ignore_dirs, ignore_filenames
    ):
        # TODO: Currently we cannot ignore anything in zip files, we should make
        # this a proper included data file type, or apply the options for no-include
        # manually.

        # Create a filtered zip file ourselves, do not expand to many individual
        # data files. Follows argument ordering of makeIncludedDataDirectory.
        out = io.BytesIO()

        with getZipFile(
            zip_path=source_path, error_exit=True, logger=self
        ) as source_zip:
            target_zip = createZipFile(file_obj=out)
            for zip_info in source_zip.infolist():
                filename = zip_info.filename

                if filename.endswith("/"):
                    continue

                parts = filename.split("/")
                if len(parts) > 1 and parts[0].endswith("_library"):
                    filename_relative = "/".join(parts[1:])
                else:
                    filename_relative = filename

                if not filename_relative:
                    continue

                rel_parts = filename_relative.split("/")
                if any(part in ignore_dirs for part in rel_parts[:-1]):
                    continue

                if os.path.basename(filename_relative) in ignore_filenames:
                    continue

                target_zip.writestr(
                    filename_relative, source_zip.read(zip_info.filename)
                )

            target_zip.close()

        yield self.makeIncludedGeneratedDataFile(
            data=out.getvalue(),
            dest_path=dest_path + ".zip",
            reason=reason,
            tags=tags,
        )

    @staticmethod
    def getTclTargetPath():
        if isMacOS():
            return "tcl-files"
        else:
            return "tcl"

    @staticmethod
    def getTkTargetPath():
        if isMacOS():
            return "tk-files"
        else:
            return "tk"

    def considerDataFiles(self, module):  # pylint: disable=too-many-branches
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
        tcl_is_zip = False
        if tcl_library_dir is None:
            for tcl_library_dir in self._getTclCandidatePaths():
                if os.path.exists(os.path.join(tcl_library_dir, "init.tcl")):
                    break
            else:
                tcl_library_dir = None

            if tcl_library_dir is None or not os.path.exists(tcl_library_dir):
                for candidate in self._getTclZipCandidatePaths():
                    if doesZipFileMatch(
                        zip_path=candidate,
                        decide_filename=lambda filename: filename == "init.tcl"
                        or filename.endswith("/init.tcl"),
                        error_exit=False,
                        logger=self,
                    ):
                        tcl_library_dir = candidate
                        tcl_is_zip = True
                        break
        else:
            if os.path.isfile(tcl_library_dir) and tcl_library_dir.endswith(".zip"):
                tcl_is_zip = True

        if tcl_library_dir is None or not os.path.exists(tcl_library_dir):
            self.sysexit("""\
Could not find Tcl, you might need to use '--tcl-library-dir' and if \
that works, report a bug so it can be added to Nuitka.""")

        tk_library_dir = self.tk_library_dir
        tk_is_zip = False
        if tk_library_dir is None:
            for tk_library_dir in self._getTkCandidatePaths():
                if os.path.exists(os.path.join(tk_library_dir, "dialog.tcl")):
                    break
            else:
                tk_library_dir = None

            if tk_library_dir is None or not os.path.exists(tk_library_dir):
                for candidate in self._getTkZipCandidatePaths():
                    if doesZipFileMatch(
                        zip_path=candidate,
                        decide_filename=lambda filename: filename == "dialog.tcl"
                        or filename.endswith("/dialog.tcl"),
                        error_exit=False,
                        logger=self,
                    ):
                        tk_library_dir = candidate
                        tk_is_zip = True
                        break
        else:
            if os.path.isfile(tk_library_dir) and tk_library_dir.endswith(".zip"):
                tk_is_zip = True

        if tk_library_dir is None or not os.path.exists(tk_library_dir):
            self.sysexit("""\
Could not find Tk, you might need to use '--tk-library-dir' and if \
that works, report a bug.""")

        # survived the above, now do provide the locations
        self._tcl_is_zip = tcl_is_zip
        self._tk_is_zip = tk_is_zip

        if tk_is_zip:
            for included in self._makeIncludedFromZip(
                source_path=tk_library_dir,
                dest_path=self.getTkTargetPath(),
                reason="Tk needed for tkinter usage",
                tags="tk",
                ignore_dirs=self._tk_ignore_dirs,
                ignore_filenames=(),
            ):
                yield included
        else:
            yield self.makeIncludedDataDirectory(
                source_path=tk_library_dir,
                dest_path=self.getTkTargetPath(),
                reason="Tk needed for tkinter usage",
                ignore_dirs=self._tk_ignore_dirs,
                tags="tk",
            )

        if tcl_is_zip:
            for included in self._makeIncludedFromZip(
                source_path=tcl_library_dir,
                dest_path=self.getTclTargetPath(),
                reason="Tcl needed for tkinter usage",
                tags="tcl",
                ignore_dirs=self._tcl_ignore_dirs,
                ignore_filenames=self._tcl_ignore_filenames,
            ):
                yield included
        else:
            yield self.makeIncludedDataDirectory(
                source_path=tcl_library_dir,
                ignore_dirs=self._tcl_ignore_dirs
                + (self._tcl_ignore_dirs_appbundle if shallCreateAppBundle() else ()),
                ignore_filenames=self._tcl_ignore_filenames,
                dest_path=self.getTclTargetPath(),
                reason="Tcl needed for tkinter usage",
                tags="tcl",
            )

        if isWin32Windows() and not tcl_is_zip:
            tcl8_path = os.path.join(tcl_library_dir, "..", "tcl8")
            if os.path.isdir(tcl8_path):
                yield self.makeIncludedDataDirectory(
                    source_path=tcl8_path,
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

    def getReportData(self):
        return {
            "tk_inter_version": self.tk_inter_version,
            "tcl_library_dir": self.tcl_library_dir,
            "tk_library_dir": self.tk_library_dir,
        }


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
