#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

""" Plugin for Playwright.

spell-checker: ignore Playwright
"""

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
import os


class NuitkaPluginPlaywright(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "Playwright"
    plugin_desc = "Required by 'playwright' package."

    def __init__(self, include_browsers):
        self.include_browsers = include_browsers
        self.installed_browsers = self.get_Installed_Playwright_Browsers()

        if "all" in self.include_browsers:
            self.include_browsers = self.installed_browsers
        elif "ffmpeg" not in self.include_browsers and any(
            browser.startswith("chrom") for browser in self.include_browsers
        ):
            for browser in self.installed_browsers:
                if "ffmpeg" in self.installed_browsers[browser].name:
                    self.include_browsers.append(browser)
                    self.info(
                        "Including 'ffmpeg' for chromium-based browser. It is required by playwright."
                    )
                    break

        for browser in self.include_browsers:
            if browser not in self.installed_browsers:
                self.sysexit(
                    f"Error, requested to include browser '{browser}' that was not found, the list of installed ones is '{', '.join(self.installed_browsers.keys())}'."
                )

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def isRelevant():
        return isStandaloneMode()

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--playwright-include-browser",
            action="append",
            dest="include_browsers",
            default=[],
            help="""\
            Playwright browser to include. Can be specified multiple times. use "all" to include all installed browsers.
            """,
        )

    def getRegistryDirectory(self):
        import playwright

        env_defined = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        path_home = os.path.expanduser("~")
        playwright_module_path = os.path.dirname(playwright.__file__)
        result = os.path.join(
            playwright_module_path, "driver", "package", ".local-browsers"
        )
        if os.path.exists(result) and os.path.getsize(result) > 0:
            return result
        elif env_defined == "0":
            return result
        elif env_defined:
            result = os.path(env_defined)
        else:
            cache_directory = ""
            if os.name == "posix":
                cache_directory = os.environ.get(
                    "XDG_CACHE_HOME", os.path.join(path_home, ".cache")
                )
            elif os.name == "darwin":
                cache_directory = os.path.join(path_home, "Library", "Caches")
            elif os.name == "nt":
                cache_directory = os.environ.get(
                    "LOCALAPPDATA", os.path.join(path_home, "AppData", "Local")
                )

            result = os.path.join(cache_directory, "ms-playwright")

        if not os.path.isabs(result):
            init_cwd = os.environ.get("INIT_CWD") or os.getcwd()
            result = os.path.join(os.path.abspath(init_cwd), result)

        return result

    def get_Installed_Playwright_Browsers(self):

        registry_directory = self.getRegistryDirectory()

        if not os.path.exists(registry_directory):
            return {}

        browsers_installed = list(os.scandir(registry_directory))
        for browser in browsers_installed:
            if browser.name == ".links":
                browsers_installed.remove(browser)
                break

        return {browser.name: browser for browser in browsers_installed}

    def considerDataFiles(self, module):

        if module.getFullName() != "playwright" or not self.include_browsers:
            return

        for browser in self.include_browsers:
            self.info(
                f"Including '{browser}' from '{self.installed_browsers[browser].path}'."
            )

            yield self.makeIncludedDataDirectory(
                source_path=self.installed_browsers[browser],
                dest_path=os.path.join(
                    "playwright", "driver", "package", ".local-browsers", browser
                ),
                reason="Playwright browser '%s'" % browser,
                tags="playwright",
                raw=True,
            )


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
