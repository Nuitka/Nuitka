#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to tell user about needed or useful options for packages.

When certain GUI packages are used, disabling the console may or may not be what
the user wants, or even be required, as e.g. "wx" on macOS will crash unless the
console is disabled. This reads Yaml configuration.
"""

from nuitka.Options import (
    isOnefileMode,
    isStandaloneMode,
    shallCreateAppBundle,
)
from nuitka.plugins.YamlPluginBase import NuitkaYamlPluginBase
from nuitka.utils.Utils import isMacOS


class NuitkaPluginOptionsNanny(NuitkaYamlPluginBase):
    plugin_name = "options-nanny"
    plugin_desc = (
        "Inform the user about potential problems as per package configuration files."
    )
    plugin_category = "core"

    @staticmethod
    def isAlwaysEnabled():
        return True

    def sysexitIllegalOptionValue(self, full_name, option, value):
        self.sysexit(
            "Illegal value for package '%s' option '%s' ('%s')"
            % (full_name, option, value)
        )

    def _checkSupportedVersion(self, full_name, support_info, description, condition):
        # Configured to not report, default value.
        if support_info == "ignore":
            return

        if support_info == "parameter":
            message = "Module has parameter: " + description
        elif support_info == "plugin":
            message = "Module has plugin consideration: " + description
        else:
            if condition != "True":
                problem_desc = (
                    " with incomplete support due to condition '%s'" % condition
                )
            else:
                problem_desc = " with incomplete support"

            message = "Using module '%s' (version %s)%s: %s" % (
                full_name,
                ".".join(str(d) for d in self.getPackageVersion(full_name)),
                problem_desc,
                description,
            )

        if support_info == "error":
            self.sysexit(message)
        elif support_info in ("warning", "parameter", "plugin"):
            self.warning(message)
        elif support_info == "info":
            self.info(message)
        else:
            self.sysexit(
                "Error, unknown support_info level '%s' for module '%s'"
                % full_name.asString()
            )

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
            if not shallCreateAppBundle():
                self.info(
                    """\
Note, when using '%s', consider using '--macos-create-app-bundle' option. \
Otherwise high resolution will not be available and a terminal window will \
open. However for debugging, terminal output is the easiest way to see \
informative traceback and error information, so launch it from there if \
possible."""
                    % full_name
                )
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
                condition = check.get("when", "True")

                if self.evaluateCondition(full_name=full_name, condition=condition):
                    self._checkSupportedVersion(
                        full_name=full_name,
                        support_info=check.get("support_info", "ignore"),
                        description=check.get("description", "not given"),
                        condition=condition,
                    )

                    if isMacOS():
                        self._checkMacOSBundleMode(
                            full_name=full_name,
                            macos_bundle=check.get("macos_bundle", "no"),
                        )

                        self._checkMacOSBundleOnefileMode(
                            full_name=full_name,
                            macos_bundle_as_onefile=check.get(
                                "macos_bundle_as_onefile", "no"
                            ),
                        )

        return ()


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
