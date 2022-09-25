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
""" Standard plug-in to tell user about needed or useful options for packages.

When certain GUI packages are used, disabling the console may or may not be what
the user wants, or even be required, as e.g. "wx" on macOS will crash unless the
console is disabled. This reads Yaml configuration.
"""

from nuitka.Options import (
    isOnefileMode,
    isStandaloneMode,
    mayDisableConsoleWindow,
    shallCreateAppBundle,
    shallDisableConsoleWindow,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.Utils import isMacOS
from nuitka.utils.Yaml import getYamlPackageConfiguration


class NuitkaPluginOptionsNanny(NuitkaPluginBase):
    plugin_name = "options-nanny"

    def __init__(self):
        self.config = getYamlPackageConfiguration()

    @staticmethod
    def isAlwaysEnabled():
        return True

    def sysexitIllegalOptionValue(self, full_name, option, value):
        self.sysexit(
            "Illegal value for package '%s' option '%s' ('%s')"
            % (full_name, option, value)
        )

    def _checkConsoleMode(self, full_name, console):
        if console == "no":
            if shallDisableConsoleWindow() is not True:
                self.sysexit(
                    "Error, when using '%s', you have to use '--disable-console' option."
                    % full_name
                )
        elif console == "yes":
            pass
        elif console == "recommend":
            if shallDisableConsoleWindow() is None:
                if isMacOS():
                    downside_message = """\
Otherwise high resolution will not be available and a terminal window will open."""
                else:
                    downside_message = """\
Otherwise a terminal window will open."""

                self.info(
                    "Note, when using '%s', consider using '--disable-console' option. %s"
                    % (full_name, downside_message)
                )

        else:
            self.sysexitIllegalOptionValue(full_name, "console", console)

    def _checkMacOSBundleMode(self, full_name, macos_bundle):
        if macos_bundle == "yes":
            if isStandaloneMode() and not shallCreateAppBundle():
                self.sysexit(
                    """\
Error, package '%s' requires '--macos-create-app-bundle' to be used or else it cannot work."""
                    % full_name
                )
        elif macos_bundle == "no":
            pass
        elif macos_bundle == "recommend":
            # TODO: Not really recommending with a message it yet.
            pass
        else:
            self.sysexitIllegalOptionValue(full_name, "macos_bundle", macos_bundle)

    def _checkMacOSBundleOnefileMode(self, full_name, macos_bundle_as_onefile):
        if macos_bundle_as_onefile == "yes":
            if isStandaloneMode() and shallCreateAppBundle() and not isOnefileMode():
                self.sysexit(
                    """\
Error, package '%s' requires '--onefile' to be used on top of '--macos-create-app-bundle' or else it cannot work."""
                    % full_name
                )
        elif macos_bundle_as_onefile == "no":
            pass
        else:
            self.sysexitIllegalOptionValue(
                full_name, "macos_bundle_onefile_mode", macos_bundle_as_onefile
            )

    # TODO: Definitely the wrong function to use, but we migrated this out of
    # implicit imports, where it was done there.
    def getImplicitImports(self, module):
        full_name = module.getFullName()

        for options_config in self.config.get(full_name, section="options"):
            for check in options_config.get("checks", ()):
                if self.evaluateCondition(
                    full_name=full_name, condition=check.get("when", "True")
                ):
                    if mayDisableConsoleWindow():
                        self._checkConsoleMode(
                            full_name=full_name,
                            console=options_config.get("console", "yes"),
                        )

                    if isMacOS():
                        self._checkMacOSBundleMode(
                            full_name=full_name,
                            macos_bundle=options_config.get("macos_bundle", "no"),
                        )

                        self._checkMacOSBundleOnefileMode(
                            full_name=full_name,
                            macos_bundle_as_onefile=options_config.get(
                                "macos_bundle_as_onefile", "no"
                            ),
                        )

        return ()
