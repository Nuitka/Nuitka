#     Copyright 2024, Kevin Rodriguez <mailto:turcioskevinr@gmail.com> find license text at end of file


""" Plugin for Playwright.

spell-checker: ignore Playwright
"""

import os

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginPlaywright(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "playwright"
    plugin_desc = "Required by 'playwright' package."

    def __init__(self, include_browsers, exclude_browsers):
        self.include_browsers = list(include_browsers)
        self.exclude_browsers = list(exclude_browsers)
        self.installed_browsers = None

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
        group.add_option(
            "--playwright-exclude-browser",
            action="append",
            dest="exclude_browsers",
            default=[],
            help="""\
            Playwright browser to exclude. Can be specified multiple times, use "all" to exclude all installed browsers.
            """,
        )

    def _getPlaywrightPath(self):
        """Determine the path of the playwright module."""
        info = self.locateModule("playwright")

        if info is None:
            self.sysexit("Error, it seems 'playwright' is not installed or broken.")

        return info

    def _getPlaywrightRegistryDirectory(self):
        # this is a port of playwright's JS script which determines where the browsers are installed

        env_defined = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        path_home = os.path.expanduser("~")
        playwright_module_path = self._getPlaywrightPath()

        result = os.path.join(
            playwright_module_path, "driver", "package", ".local-browsers"
        )

        # TODO: This is seemingly a test for non-empty directory, which we should
        # then add to FileOperations.

        if os.path.exists(result) and next(os.scandir(result), False):
            return result
        elif env_defined == "0":
            return result
        elif env_defined:
            result = os.path.normpath(env_defined)
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

    def getInstalledPlaywrightBrowsers(self):
        registry_directory = self._getPlaywrightRegistryDirectory()
        if not os.path.exists(registry_directory):
            return

        # TODO: Seems useless use of os.scandir, our helper for listing a directory
        # would be better to use.
        browsers_installed = [
            browser
            for browser in os.scandir(registry_directory)
            if browser.name != ".links"
        ]
        self.installed_browsers = {}
        for browser in browsers_installed:
            self.installed_browsers[browser.name] = browser

    def considerDataFiles(self, module):
        if module.getFullName() != "playwright":
            return

        if not self.include_browsers and not self.exclude_browsers:
            self.sysexit(
                "No browsers included. Use '--playwright-include-browser=browser_name' or 'all' to include them.\n"
                "Or '--playwright-exclude-browser=browser_name' to exclude specific browsers."
            )

        self.getInstalledPlaywrightBrowsers()
        available_browsers = set(self.installed_browsers.keys())

        if not available_browsers:
            self.warning("No browsers installed - nothing to include or exclude.")
            return

        if "all" in self.exclude_browsers:
            self.info("All browsers excluded.")
            return

        browsers_to_include = set(
            available_browsers
            if "all" in self.include_browsers
            else self.include_browsers
        )
        browsers_to_exclude = set(self.exclude_browsers)

        invalid_includes = browsers_to_include - available_browsers
        if invalid_includes:
            self.sysexit(
                "Browsers not found: %s. Available: %s"
                % (", ".join(invalid_includes), ", ".join(available_browsers))
            )

        invalid_excludes = browsers_to_exclude - available_browsers
        if invalid_excludes:
            self.warning(
                "Excluding non-existent browsers: %s" % ", ".join(invalid_excludes)
            )

        final_browsers = browsers_to_include - browsers_to_exclude

        for browser in final_browsers:
            source_path = self.installed_browsers[browser].path
            self.info('Including browser "%s" from "%s".' % (browser, source_path))
            yield self.makeIncludedDataDirectory(
                source_path=source_path,
                dest_path=os.path.join(
                    "playwright", "driver", "package", ".local-browsers", browser
                ),
                reason='Playwright browser "%s"' % browser,
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
