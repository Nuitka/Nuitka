#     Copyright 2020, Jorj McKie, mailto:<jorj.x.mckie@outlook.de> find license text at end of file


"""Details see below in class definition."""

import os
import sys

from nuitka.options.Options import isStandaloneMode, shallCreateAppBundle
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonFlavors import (
    getHomebrewInstallPath,
    isHomebrewPython,
    isPyenvHomebrewPython,
)
from nuitka.PythonPrefixes import getSystemPrefixPath
from nuitka.PythonVersions import getTkInterVersion
from nuitka.utils.FileOperations import getUserInputNormalizedPath, listDir
from nuitka.utils.Utils import isMacOS, isWin32Windows
from nuitka.utils.Zipfiles import doesZipFileMatch, hasZipFileOverlay

# spell-checker: ignore libtcl,libtk,tcltest,tcltk


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

    # Many attributes for the different TCL/TK aspects, pylint: disable=too-many-instance-attributes

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
        self.tcl_library_dir = (
            getUserInputNormalizedPath(tcl_library_dir)
            if tcl_library_dir is not None
            else None
        )
        self.tk_library_dir = (
            getUserInputNormalizedPath(tk_library_dir)
            if tk_library_dir is not None
            else None
        )

        # The directories or DLL zip overlays used, once detected.
        self.tcl_library_source_dir = None
        self.tk_library_source_dir = None

        # ensure one-time action, we deal with several names for the execution,
        # yet we only want to do it once.
        self.files_copied = False
        self._tcl_uses_zip_overlay = False
        self._tk_uses_zip_overlay = False

        self.tk_inter_version = getTkInterVersion()

        if self.tk_inter_version is None:
            self.sysexit("Error, it seems 'tk-inter' is not installed.")

        # Only ever saw these in use, report if there are more.
        if self.tk_inter_version not in ("8.5", "8.6", "9.0", "9.1"):
            self.sysexit("""\
Error, it seems 'tk-inter' has an unsupported version '%s'. \
Please report as a issue.""" % self.tk_inter_version)

        return None

    def getReportData(self, make_report_path):
        yield "tk_inter_version", self.tk_inter_version
        yield "tcl_library_source_dir", (
            make_report_path(self.tcl_library_source_dir)
            if self.tcl_library_source_dir is not None
            else "none"
        )
        yield "tk_library_source_dir", (
            make_report_path(self.tk_library_source_dir)
            if self.tk_library_source_dir is not None
            else "none"
        )

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone, else False.
        """
        return isStandaloneMode()

    def createPreModuleLoadCode(self, module):
        if _isTkInterModule(module):
            # Detect Tcl/Tk locations early so directory vs. DLL zip overlay
            # handling matches what considerDataFiles will later package.
            self._detectTclTkLibraries()

            lines = ["import os"]

            if not self._tcl_uses_zip_overlay or not self._tk_uses_zip_overlay:
                lines.append(
                    'nuitka_info = globals().get("__uncompiled__", globals().get("__compiled__"))'
                )

            if self._tcl_uses_zip_overlay:
                lines.append('os.environ.pop("TCL_LIBRARY", None)')
            else:
                lines.append(
                    'os.environ["TCL_LIBRARY"] = os.path.join(nuitka_info.python_runtime_dir, "%s")'
                    % self.getTclTargetPath()
                )

            if self._tk_uses_zip_overlay:
                lines.append('os.environ.pop("TK_LIBRARY", None)')
            else:
                lines.append(
                    'os.environ["TK_LIBRARY"] = os.path.join(nuitka_info.python_runtime_dir, "%s")'
                    % self.getTkTargetPath()
                )

            return (
                "\n".join(lines),
                "Need to make sure we set environment variables for TCL.",
            )

    def createPostModuleLoadCode(self, module):
        # Starting with Tk 9, it loads ICU DLLs dynamically, and on Windows it
        # prefers versioned DLLs found in PATH over the ICU included with
        # Windows. Temporarily strip PATH during '_tkinter.create' so
        # standalone builds do not pick up incompatible third-party ICU DLLs.
        if (
            isWin32Windows()
            and self.tk_inter_version.startswith("9.")
            and _isTkInterModule(module)
        ):
            # The following code will be executed after importing the module. The
            # Tk initialization happens in "_tkinter.create" and that is where
            # the ICU DLLs are being loaded from PATH, if not found in the
            # Windows directory.
            code = r"""
import os
import _tkinter

if not getattr(_tkinter.create, "_nuitka_clean_path", False):
    _original_create = _tkinter.create

    def _create_clean_path(*args, **kwargs):
        _path = os.environ.pop("PATH", None)
        try:
            return _original_create(*args, **kwargs)
        finally:
            if _path is not None:
                os.environ["PATH"] = _path

    _create_clean_path._nuitka_clean_path = True
    _tkinter.create = _create_clean_path"""

            return code, "Need to avoid Tk loading ICU DLLs from PATH."

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

    def _getTclCandidatePaths(self, system_locations):
        if not system_locations:
            # Check typical locations of the dirs
            tcl_library = os.getenv("TCL_LIBRARY")
            if tcl_library:
                yield getUserInputNormalizedPath(tcl_library)

            # Inside the Python install, esp. on Windows.
            for sys_prefix_path in (sys.prefix, getSystemPrefixPath()):
                yield os.path.join(
                    sys_prefix_path, "tcl", "tcl%s" % self.tk_inter_version
                )
                yield os.path.join(
                    sys_prefix_path, "lib", "tcl%s" % self.tk_inter_version
                )

                # Newer Anaconda.
                yield os.path.join(
                    sys_prefix_path, "Library", "lib", "tcl%s" % self.tk_inter_version
                )
        else:
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

    def _getTkCandidatePaths(self, system_locations):
        if not system_locations:
            tk_library = os.getenv("TK_LIBRARY")
            if tk_library:
                yield getUserInputNormalizedPath(tk_library)

            for sys_prefix_path in (sys.prefix, getSystemPrefixPath()):
                yield os.path.join(
                    sys_prefix_path, "tcl", "tk%s" % self.tk_inter_version
                )
                yield os.path.join(
                    sys_prefix_path, "lib", "tk%s" % self.tk_inter_version
                )

                # Newer Anaconda.
                yield os.path.join(
                    sys_prefix_path, "Library", "lib", "tk%s" % self.tk_inter_version
                )
        else:
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
    def _getOverlayDllCandidatePaths(prefixes, system_locations):
        candidate_dirs = []

        if not system_locations:
            for sys_prefix_path in (sys.prefix, getSystemPrefixPath()):
                if isWin32Windows():
                    candidate_dirs.extend(
                        (
                            os.path.join(sys_prefix_path, "DLLs"),
                            os.path.join(sys_prefix_path, "Library", "bin"),
                            sys_prefix_path,
                        )
                    )
                else:
                    candidate_dirs.extend(
                        (
                            os.path.join(sys_prefix_path, "lib"),
                            os.path.join(sys_prefix_path, "lib64"),
                        )
                    )
        elif not isWin32Windows():
            candidate_dirs.extend(("/usr/lib64", "/usr/lib"))

        seen_dirs = set()
        for candidate_dir in candidate_dirs:
            if (
                not candidate_dir
                or candidate_dir in seen_dirs
                or not os.path.isdir(candidate_dir)
            ):
                continue
            seen_dirs.add(candidate_dir)

            for full_path, filename in listDir(candidate_dir):
                filename_lower = filename.lower()
                if not filename_lower.startswith(prefixes):
                    continue

                if isWin32Windows():
                    is_shared_lib = filename_lower.endswith(".dll")
                else:
                    is_shared_lib = ".so" in filename_lower or filename_lower.endswith(
                        ".dylib"
                    )

                if is_shared_lib and hasZipFileOverlay(full_path):
                    yield full_path

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

    def _getZipAndOverlayCandidates(
        self, candidate_paths, dll_prefixes, zip_prefixes, system_locations
    ):
        for candidate in self._getOverlayDllCandidatePaths(
            prefixes=dll_prefixes,
            system_locations=system_locations,
        ):
            yield candidate

        for candidate in self._getZipCandidatePaths(
            candidate_paths=candidate_paths,
            prefixes=zip_prefixes,
        ):
            yield candidate

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

    def _findLibrarySource(
        self,
        explicit_dir,
        get_candidate_paths,
        dll_prefixes,
        zip_prefixes,
        marker_filename,
    ):
        def _matchesZipMarker(candidate):
            return doesZipFileMatch(
                zip_path=candidate,
                decide_filename=lambda filename: filename == marker_filename
                or filename.endswith("/" + marker_filename),
                error_exit=False,
                logger=self,
            )

        if explicit_dir is not None:
            uses_zip = hasZipFileOverlay(explicit_dir) or (
                os.path.isfile(explicit_dir) and explicit_dir.endswith(".zip")
            )
            return explicit_dir, uses_zip

        # First check explicit environment variable and Python prefix locations
        # (both filesystem directories and ZipFS overlays) so a self-contained
        # Python build does not fall back to unrelated system /usr/share files.
        for system_locations in (False, True):
            candidate_paths = tuple(
                get_candidate_paths(system_locations=system_locations)
            )

            for candidate_dir in candidate_paths:
                if os.path.exists(os.path.join(candidate_dir, marker_filename)):
                    return candidate_dir, False

                if hasZipFileOverlay(candidate_dir) and _matchesZipMarker(
                    candidate_dir
                ):
                    return candidate_dir, True

            for candidate in self._getZipAndOverlayCandidates(
                candidate_paths=candidate_paths,
                dll_prefixes=dll_prefixes,
                zip_prefixes=zip_prefixes,
                system_locations=system_locations,
            ):
                if _matchesZipMarker(candidate):
                    return candidate, True

        return None, False

    def _detectTclTkLibraries(self):
        if self.tcl_library_source_dir is not None:
            return

        tcl_library_dir, tcl_uses_zip_overlay = self._findLibrarySource(
            explicit_dir=self.tcl_library_dir,
            get_candidate_paths=self._getTclCandidatePaths,
            dll_prefixes=("tcl", "libtcl"),
            zip_prefixes=("libtcl", "tcl"),
            marker_filename="init.tcl",
        )

        if tcl_library_dir is None or not os.path.exists(tcl_library_dir):
            self.sysexit("""\
Could not find Tcl, you might need to use '--tcl-library-dir' and if \
that works, report a bug so it can be added to Nuitka.""")

        tk_library_dir, tk_uses_zip_overlay = self._findLibrarySource(
            explicit_dir=self.tk_library_dir,
            get_candidate_paths=self._getTkCandidatePaths,
            dll_prefixes=("tcl", "tk", "libtcl", "libtk"),
            zip_prefixes=("libtk", "tk"),
            marker_filename="dialog.tcl",
        )

        if tk_library_dir is None or not os.path.exists(tk_library_dir):
            self.sysexit("""\
Could not find Tk, you might need to use '--tk-library-dir' and if \
that works, report a bug.""")

        # Survived the above, now record the locations.
        self.tcl_library_source_dir = tcl_library_dir
        self.tk_library_source_dir = tk_library_dir

        self._tcl_uses_zip_overlay = tcl_uses_zip_overlay
        self._tk_uses_zip_overlay = tk_uses_zip_overlay

    def considerDataFiles(self, module):
        """Provide TCL libraries to the dist folder when not embedded in the DLLs."""
        if not _isTkInterModule(module) or self.files_copied:
            return

        self._detectTclTkLibraries()

        if not self._tk_uses_zip_overlay:
            yield self.makeIncludedDataDirectory(
                source_path=self.tk_library_source_dir,
                dest_path=self.getTkTargetPath(),
                reason="Tk needed for tkinter usage",
                ignore_dirs=self._tk_ignore_dirs,
                tags="tk",
            )

        if not self._tcl_uses_zip_overlay:
            yield self.makeIncludedDataDirectory(
                source_path=self.tcl_library_source_dir,
                ignore_dirs=self._tcl_ignore_dirs
                + (self._tcl_ignore_dirs_appbundle if shallCreateAppBundle() else ()),
                ignore_filenames=self._tcl_ignore_filenames,
                dest_path=self.getTclTargetPath(),
                reason="Tcl needed for tkinter usage",
                tags="tcl",
            )

            if isWin32Windows():
                tcl8_path = os.path.join(self.tcl_library_source_dir, "..", "tcl8")
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
