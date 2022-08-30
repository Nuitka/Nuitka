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
""" Details see below in class definition.
"""

import os

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import getActiveQtPlugin
from nuitka.utils.FileOperations import getFileList, hasFilenameExtension
from nuitka.utils.Utils import getArchitecture, getOS, isMacOS, isWin32Windows

# spellchecker: ignore pywebview,mshtml


class NuitkaPluginPywebview(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "pywebview"
    plugin_desc = "Required by the webview package (pywebview on PyPI)"

    @staticmethod
    def isAlwaysEnabled():
        return True

    @classmethod
    def isRelevant(cls):
        """One time only check: may this plugin be required?

        Returns:
            True if this is a standalone compilation.
        """
        return isStandaloneMode()

    @staticmethod
    def _getWebviewFiles(module, dlls):
        # TODO: Clarify non-Windows needs.
        if not isWin32Windows():
            return

        webview_libdir = os.path.join(module.getCompileTimeDirectory(), "lib")
        for filename in getFileList(webview_libdir):
            filename_relative = os.path.relpath(filename, webview_libdir)

            if getArchitecture() == "x86":
                if "x64" in filename_relative:
                    continue
            else:
                if "x86" in filename_relative:
                    continue

            is_dll = hasFilenameExtension(filename_relative, ".dll")

            if dlls and not is_dll or not dlls and is_dll:
                continue

            yield filename, filename_relative

    def getExtraDlls(self, module):
        if module.getFullName() == "webview":
            for filename, filename_relative in self._getWebviewFiles(module, dlls=True):
                yield self.makeDllEntryPoint(
                    source_path=filename,
                    dest_path=os.path.normpath(
                        os.path.join(
                            "webview/lib",
                            filename_relative,
                        )
                    ),
                    package_name=module.getFullName(),
                    reason="needed by 'webview'",
                )

    def considerDataFiles(self, module):
        if module.getFullName() == "webview":
            for filename, filename_relative in self._getWebviewFiles(
                module, dlls=False
            ):
                yield self.makeIncludedDataFile(
                    source_path=filename,
                    dest_path=os.path.normpath(
                        os.path.join(
                            "webview/lib",
                            filename_relative,
                        )
                    ),
                    reason="Package 'webview' datafile",
                )

    def onModuleEncounter(self, module_name, module_filename, module_kind):
        # Make sure webview platforms are included as needed.
        if module_name.isBelowNamespace("webview.platforms"):
            if isWin32Windows():
                result = module_name in (
                    "webview.platforms.winforms",
                    "webview.platforms.edgechromium",
                    "webview.platforms.edgehtml",
                    "webview.platforms.mshtml",
                    "webview.platforms.cef",
                )
                reason = "Platforms package of webview used on '%s'." % getOS()
            elif isMacOS():
                result = module_name == "webview.platforms.cocoa"
                reason = "Platforms package of webview used on '%s'." % getOS()
            elif getActiveQtPlugin() is not None:
                result = module_name = "webview.platforms.qt"
                reason = (
                    "Platforms package of webview used due to '%s'."
                    % getActiveQtPlugin()
                )
            else:
                result = module_name = "webview.platforms.gtk"
                reason = (
                    "Platforms package of webview used on '%s' without Qt plugin enabled."
                    % getOS()
                )

            return result, reason
