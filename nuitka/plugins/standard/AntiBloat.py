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

* cffi importing setuptools is not needed, workaround that with
  --noinclude-setuptools-mode=nofollow if warned about including it.

  Setuptools includes massive amounts of build tools which use other
  things optionally.

"""

import ast
import pkgutil

from nuitka.containers.odict import OrderedDict
from nuitka.Errors import NuitkaForbiddenImportEncounter
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Yaml import parseYaml


class NuitkaPluginAntiBloat(NuitkaPluginBase):
    plugin_name = "anti-bloat"
    plugin_desc = (
        "Patch stupid imports out of widely used library modules source codes."
    )

    def __init__(
        self, noinclude_setuptools_mode, noinclude_pytest_mode, custom_choices
    ):
        self.config = parseYaml(
            pkgutil.get_data("nuitka.plugins.standard", "anti-bloat.yml")
        )

        self.handled_modules = OrderedDict()

        if noinclude_setuptools_mode != "allow":
            self.handled_modules["setuptools"] = noinclude_setuptools_mode

        if noinclude_pytest_mode != "allow":
            self.handled_modules["pytest"] = noinclude_pytest_mode

        for custom_choice in custom_choices:
            if ":" not in custom_choice:
                self.sysexit(
                    "Error, malformed value  '%s' for '--noinclude-custom-mode' used."
                    % custom_choice
                )

            module_name, mode = custom_choice.rsplit(":", 1)

            if mode not in ("error", "warning", "nofollow", "allow"):
                self.sysexit(
                    "Error, illegal mode given '%s' in '--noinclude-custom-mode=%s'"
                    % (mode, custom_choice)
                )

            self.handled_modules[ModuleName(module_name)] = mode

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--noinclude-setuptools-mode",
            action="store",
            dest="noinclude_setuptools_mode",
            choices=("error", "warning", "nofollow", "allow"),
            default="warning",
            help="""\
What to do if a setuptools import is encountered. This can be big with
dependencies, and should definitely be avoided.""",
        )

        group.add_option(
            "--noinclude-pytest-mode",
            action="store",
            dest="noinclude_pytest_mode",
            choices=("error", "warning", "nofollow", "allow"),
            default="warning",
            help="""\
What to do if a pytest import is encountered. This can be big with
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
"warning", "nofollow", e.g. PyQt5:error.""",
        )

    def onModuleSourceCode(self, module_name, source_code):
        # Complex dealing with many cases, pylint: disable=too-many-branches,too-many-locals

        config = self.config.get(module_name)

        if not config:
            return source_code

        description = config.get("description", "description not given")

        # To allow detection if it did anything.
        change_count = 0

        context = {}
        context_code = config.get("context", "")
        if type(context_code) in (tuple, list):
            context_code = "\n".join(context_code)

        # We trust the yaml files, pylint: disable=eval-used,exec-used
        context_ready = not bool(context_code)

        for replace_src, replace_code in config.get("replacements", {}).items():
            # Avoid the eval, if the replace doesn't hit.
            if replace_src not in source_code:
                continue

            if replace_code:
                if not context_ready:
                    exec(context_code, context)
                    context_ready = True
                try:
                    replace_dst = eval(replace_code, context)
                except Exception as e:  # pylint: disable=broad-except
                    self.sysexit(
                        "Error, cannot evaluate code '%s' in '%s' due to: %s"
                        % (replace_code, context_code, e)
                    )
            else:
                replace_dst = ""

            old = source_code
            source_code = source_code.replace(replace_src, replace_dst)

            if old != source_code:
                change_count += 1

        append_code = config.get("append_result", "")
        if type(append_code) in (tuple, list):
            append_code = "\n".join(append_code)

        if append_code:
            if not context_ready:
                exec(context_code, context)
                context_ready = True

            try:
                append_result = eval(append_code, context)
            except Exception as e:  # pylint: disable=broad-except
                self.sysexit(
                    "Error, cannot evaluate code '%s' in '%s' due to: %s"
                    % (append_code, context_code, e)
                )

            source_code += "\n" + append_result
            change_count += 1

        if change_count > 0:
            self.info(
                "Handling module '%s' with %d change(s) for: %s."
                % (module_name.asString(), change_count, description)
            )

        return source_code

    def onFunctionAssignmentParsed(self, module_name, function_body, assign_node):
        config = self.config.get(module_name)

        if not config:
            return

        context = {}
        context_code = config.get("context", "")
        if type(context_code) in (tuple, list):
            context_code = "\n".join(context_code)

        # We trust the yaml files, pylint: disable=eval-used,exec-used
        context_ready = not bool(context_code)

        for function_name, replace_code in config.get("change_function", {}).items():
            if assign_node.getVariableName() != function_name:
                continue

            if not context_ready:
                exec(context_code, context)
                context_ready = True

            try:
                replacement = eval(replace_code, context)
            except Exception as e:  # pylint: disable=broad-except
                self.sysexit(
                    "Error, cannot evaluate code '%s' in '%s' due to: %s"
                    % (replace_code, context_code, e)
                )

            # Single node is required, extrace the generated module body with
            # single expression only statement value.
            (new_node,) = ast.parse(replacement).body
            new_node = new_node.value

            # Cyclic dependencies.
            from nuitka.tree.Building import buildNode

            replace_node = buildNode(
                provider=function_body.getParentVariableProvider(),
                node=new_node,
                source_ref=assign_node.source_ref,
            )

            assign_node.setChild("source", replace_node)

            self.info(
                "Updated '%s' function '%s'." % (module_name.asString(), function_name)
            )

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        for handled_module_name, mode in self.handled_modules.items():
            if module_name.hasNamespace(handled_module_name):
                # Make sure the compilation abrts.
                if mode == "error":
                    raise NuitkaForbiddenImportEncounter(module_name)

                # Either issue a warning, or pretend the module doesn't exist for standalone or
                # at least will not be included.
                if mode == "warning":
                    self.warning("Unwanted import of '%s' encountered." % module_name)
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
