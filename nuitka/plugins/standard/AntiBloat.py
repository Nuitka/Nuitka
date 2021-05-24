#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Standard plug-in to avoid bloat at compile time.

Nuitka hard codes stupid monkey patching normally not needed here and avoids
that to be done and causing massive degradations.

cffi importing setuptools is not needed.

"""


from nuitka.containers.odict import OrderedDict
from nuitka.Errors import NuitkaForbiddenImportEncounter
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.ModuleNames import ModuleName


class NuitkaPluginAntiBloat(NuitkaPluginBase):
    plugin_name = "anti-bloat"
    plugin_desc = "Patch stupid imports out of common library modules source code."

    def __init__(self, setuptools_mode, custom_choices):
        self.handled_modules = OrderedDict()

        if setuptools_mode != "allow":
            self.handled_modules["setuptools"] = setuptools_mode

        for custom_choice in custom_choices:
            module_name, mode = custom_choice.rsplit(":", 1)

            self.handled_modules[ModuleName(module_name)] = mode

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--noinclude-setuptools-mode",
            action="store",
            dest="setuptools_mode",
            choices=("error", "warning", "nofollow", "allow"),
            default="allow",
            help="""\
What to do if a setuptools import is encountered. This can be big with
dependencies, and should definitely be avoided.""",
        )

        group.add_option(
            "--noinclude-custom-mode",
            action="append",
            dest="custom_choices",
            default=[],
            help="""\
What to do if a specific import is encountered. Format is module name,
which can and should be a top level package and then one choice, "error",
"warning", "nofollow".""",
        )

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        for handled_module_name, mode in self.handled_modules.items():
            if module_name.hasNamespace(handled_module_name):
                if mode == "error":
                    raise NuitkaForbiddenImportEncounter(module_name)

                if mode == "warning":
                    self.warning("Forbidden import of '%s' encountered." % module_name)
                elif mode == "nofollow":
                    self.info(
                        "Forcing import of '%s' to not be followed." % module_name
                    )
                    return (
                        False,
                        "user requested to not follow '%s' import" % module_name,
                    )

        # Do not provide an opinion about it.
        return None
