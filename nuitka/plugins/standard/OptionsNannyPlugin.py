#     Copyright 2022, Fire-Cube <ben7@gmx.ch>
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


from nuitka.Options import (
    isOnefileMode,
    isStandaloneMode,
    mayDisableConsoleWindow,
    shallCreateAppBundle,
    shallDisableConsoleWindow,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.Utils import isMacOS


class NuitkaPluginOptionsNanny(NuitkaPluginBase):
    plugin_name = "options-nanny"

    def _get_options(self, full_name):
        options_config = self.config.get(full_name, sections="options")
        if options_config.get("checks"):
            for check in options_config.get("checks"):
                if check.get("control_tags"):
                    if not self.evaluateControlTags(check.get("control_tags")):
                        continue

                macos_bundle = options_config.get("macos_bundle")
                console = options_config.get("console")
                macos_bundle_as_onefile = options_config.get("macos_bundle_as_onefile")

                if macos_bundle is not None:
                    if macos_bundle == "yes":
                        macos_bundle = True

                    elif macos_bundle == "no":
                        macos_bundle = False

                if macos_bundle_as_onefile is not None:
                    if macos_bundle_as_onefile == "yes":
                        macos_bundle_as_onefile = True

                    elif macos_bundle_as_onefile == "no":
                        macos_bundle_as_onefile = False

                if console is not None:
                    if console == "yes":
                        console = True

                    elif console == "no":
                        console = False

                    if console == "recommend":
                        recommend_console = True

                    else:
                        recommend_console = False

                    if isMacOS():
                        if macos_bundle:
                            if isStandaloneMode() and not shallCreateAppBundle():
                                self.sysexit(
                                    """\
    Error, package '%s' requires '--macos-create-app-bundle' to be used or else it cannot work."""
                                    % full_name
                                )
                        elif macos_bundle_as_onefile:
                            if shallCreateAppBundle() and not isOnefileMode():
                                self.sysexit(
                                    """\
    Error, package '%s' requires '--onefile' to be used on top of '--macos-create-app-bundle' or else it cannot work."""
                                    % full_name
                                )

                    if (
                        recommend_console
                        and mayDisableConsoleWindow()
                        and shallDisableConsoleWindow() is None
                    ):
                        if isMacOS():
                            downside_message = "Otherwise high resolution will not be available and a terminal window will open."
                        else:
                            downside_message = "Otherwise a terminal window will open."

                        self.info(
                            "Note, when using '%s', consider using '--disable-console' option. %s"
                            % (full_name, downside_message)
                        )

                    if (
                        console
                        and mayDisableConsoleWindow()
                        and shallDisableConsoleWindow() is not True
                    ):
                        self.sysexit(
                            "Note, when using '%s', you have to use '--disable-console' option."
                            % full_name
                        )
