#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Details see below in class definition."""

from nuitka.options.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import getActiveQtPlugin
from nuitka.utils.Utils import getOS, isMacOS, isWin32Windows

# spell-checker: ignore edgechromium,edgehtml,mshtml,pywebview,webview2core,win32,winforms,winui3

# Platform modules of "webview" that are only usable on certain operating
# systems. Platform modules not listed here are included, so that new backends
# added to "webview" do not require a Nuitka change to work.
_win32_platform_names = frozenset(
    (
        "cef",
        "edgechromium",
        "edgehtml",
        "mshtml",
        "webview2core",
        "win32",
        "winforms",
        "winui3",
    )
)
_macos_platform_names = frozenset(("cocoa",))
_linux_platform_names = frozenset(("gtk", "qt"))
_android_platform_names = frozenset(("android",))

_non_win32_platform_names = (
    _macos_platform_names | _linux_platform_names | _android_platform_names
)
_non_macos_platform_names = (
    _win32_platform_names | _linux_platform_names | _android_platform_names
)
_non_linux_platform_names = (
    _win32_platform_names | _macos_platform_names | _android_platform_names
)


class NuitkaPluginPywebview(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "pywebview"
    plugin_desc = "Required by 'webview' package."
    plugin_category = "package-support"

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

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        # Make sure webview platforms are included as needed, and backends for
        # other platforms are excluded.
        if module_name.isBelowNamespace("webview.platforms"):
            platform_name = module_name.getBasename()

            if isWin32Windows():
                excluded_platform_names = _non_win32_platform_names
                reason = "Platforms package of webview used on '%s'." % getOS()
            elif isMacOS():
                excluded_platform_names = _non_macos_platform_names
                reason = "Platforms package of webview used on '%s'." % getOS()
            elif getActiveQtPlugin() is not None:
                excluded_platform_names = _non_linux_platform_names | frozenset(
                    ("gtk",)
                )
                reason = (
                    "Platforms package of webview used due to '%s' plugin being active."
                    % getActiveQtPlugin()
                )
            else:
                excluded_platform_names = _non_linux_platform_names | frozenset(("qt",))
                reason = (
                    "Platforms package of webview used on '%s' without Qt plugin enabled."
                    % getOS()
                )

            return platform_name not in excluded_platform_names, reason


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
