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
""" Standard plug-in to avoid bloat at compile time.

Nuitka hard codes stupid monkey patching normally not needed here and avoids
that to be done and causing massive degradations.

"""

import ast
import re

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.Errors import NuitkaForbiddenImportEncounter
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Yaml import getYamlPackageConfiguration

# spell-checker: ignore dask,numba

_mode_choices = ("error", "warning", "nofollow", "allow")


class NuitkaPluginAntiBloat(NuitkaPluginBase):
    plugin_name = "anti-bloat"
    plugin_desc = (
        "Patch stupid imports out of widely used library modules source codes."
    )

    @staticmethod
    def isAlwaysEnabled():
        return True

    def __init__(
        self,
        noinclude_setuptools_mode,
        noinclude_pytest_mode,
        noinclude_unittest_mode,
        noinclude_ipython_mode,
        noinclude_dask_mode,
        noinclude_numba_mode,
        noinclude_default_mode,
        custom_choices,
        show_changes,
    ):
        # Many details, due to many repetitive arguments, pylint: disable=too-many-branches,too-many-statements

        self.show_changes = show_changes

        # Default manually to default argument value:
        if noinclude_setuptools_mode is None:
            noinclude_setuptools_mode = noinclude_default_mode
        if noinclude_pytest_mode is None:
            noinclude_pytest_mode = noinclude_default_mode
        if noinclude_unittest_mode is None:
            noinclude_unittest_mode = noinclude_default_mode
        if noinclude_ipython_mode is None:
            noinclude_ipython_mode = noinclude_default_mode
        if noinclude_dask_mode is None:
            noinclude_dask_mode = noinclude_default_mode
        if noinclude_numba_mode is None:
            noinclude_numba_mode = noinclude_default_mode

        self.config = getYamlPackageConfiguration()

        self.handled_modules = OrderedDict()

        # These should be checked, to allow disabling anti-bloat contents.
        self.control_tags = OrderedDict()

        if noinclude_setuptools_mode != "allow":
            self.handled_modules["setuptools"] = noinclude_setuptools_mode
            self.handled_modules["setuptools_scm"] = noinclude_setuptools_mode
        else:
            self.control_tags["use_setuptools"] = True

        if noinclude_pytest_mode != "allow":
            self.handled_modules["pytest"] = noinclude_pytest_mode
            self.handled_modules["nose2"] = noinclude_pytest_mode
            self.handled_modules["nose"] = noinclude_pytest_mode
        else:
            self.control_tags["use_pytest"] = True

        if noinclude_unittest_mode != "allow":
            self.handled_modules["unittest"] = noinclude_unittest_mode
        else:
            self.control_tags["use_unittest"] = True

        if noinclude_ipython_mode != "allow":
            self.handled_modules["IPython"] = noinclude_ipython_mode
        else:
            self.control_tags["use_ipython"] = True

        if noinclude_dask_mode != "allow":
            self.handled_modules["dask"] = noinclude_dask_mode
        else:
            self.control_tags["use_dask"] = True

        if noinclude_numba_mode != "allow":
            self.handled_modules["numba"] = noinclude_numba_mode
            self.handled_modules["sparse"] = noinclude_numba_mode
        else:
            self.control_tags["use_numba"] = True

        for custom_choice in custom_choices:
            if ":" not in custom_choice:
                self.sysexit(
                    "Error, malformed value '%s' for '--noinclude-custom-mode' used."
                    % custom_choice
                )

            module_name, mode = custom_choice.rsplit(":", 1)

            if mode not in _mode_choices and mode != "bytecode":
                self.sysexit(
                    "Error, illegal mode given '%s' in '--noinclude-custom-mode=%s'"
                    % (mode, custom_choice)
                )

            self.handled_modules[ModuleName(module_name)] = mode

    def getCacheContributionValues(self, module_name):
        config = self.config.get(module_name, section="anti-bloat")

        if config:
            yield str(config)

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--show-anti-bloat-changes",
            action="store_true",
            dest="show_changes",
            default=False,
            help="""\
Annotate what changes are by the plugin done.""",
        )

        group.add_option(
            "--noinclude-setuptools-mode",
            action="store",
            dest="noinclude_setuptools_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a 'setuptools' or import is encountered. This package can be big with
dependencies, and should definitely be avoided. Also handles 'setuptools_scm'.""",
        )

        group.add_option(
            "--noinclude-pytest-mode",
            action="store",
            dest="noinclude_pytest_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a 'pytest' import is encountered. This package can be big with
dependencies, and should definitely be avoided. Also handles 'nose' imports.""",
        )

        group.add_option(
            "--noinclude-unittest-mode",
            action="store",
            dest="noinclude_unittest_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a unittest import is encountered. This package can be big with
dependencies, and should definitely be avoided.""",
        )

        group.add_option(
            "--noinclude-IPython-mode",
            action="store",
            dest="noinclude_ipython_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a IPython import is encountered. This package can be big with
dependencies, and should definitely be avoided.""",
        )

        group.add_option(
            "--noinclude-dask-mode",
            action="store",
            dest="noinclude_dask_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a 'dask' import is encountered. This package can be big with
dependencies, and should definitely be avoided.""",
        )

        group.add_option(
            "--noinclude-numba-mode",
            action="store",
            dest="noinclude_numba_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a 'numba' import is encountered. This package can be big with
dependencies, and is currently not working for standalone. This package is
big with dependencies, and should definitely be avoided.""",
        )

        group.add_option(
            "--noinclude-default-mode",
            action="store",
            dest="noinclude_default_mode",
            choices=_mode_choices,
            default="warning",
            help="""\
This actually provides the default "warning" value for above options, and
can be used to turn all of these on.""",
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

    def _onModuleSourceCode(self, module_name, anti_bloat_config, source_code):
        # Complex dealing with many cases, pylint: disable=too-many-branches,too-many-locals,too-many-statements

        description = anti_bloat_config.get("description", "description not given")

        # To allow detection if it did anything.
        change_count = 0

        context = {}
        context_code = anti_bloat_config.get("context", "")
        if type(context_code) in (tuple, list):
            context_code = "\n".join(context_code)
        context["version"] = self.getPackageVersion

        # We trust the yaml files, pylint: disable=eval-used,exec-used
        context_ready = not bool(context_code)

        for replace_src, replace_code in anti_bloat_config.get(
            "replacements", {}
        ).items():
            # Avoid the eval, if the replace doesn't hit.
            if replace_src not in source_code:
                continue

            if replace_code:
                if not context_ready:
                    try:
                        exec(context_code, context)
                    except Exception as e:  # pylint: disable=broad-except
                        self.sysexit(
                            "Error, cannot execute context code '%s' due to: %s"
                            % (context_code, e)
                        )

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

            if type(replace_dst) is not str:
                self.sysexit(
                    "Error, expression needs to generate string, not %s"
                    % type(replace_dst)
                )

            old = source_code
            source_code = source_code.replace(replace_src, replace_dst)

            if old != source_code:
                change_count += 1

        for replace_src, replace_dst in anti_bloat_config.get(
            "replacements_plain", {}
        ).items():
            old = source_code
            source_code = source_code.replace(replace_src, replace_dst)

            if old != source_code:
                change_count += 1

        for replace_src, replace_dst in anti_bloat_config.get(
            "replacements_re", {}
        ).items():
            old = source_code
            source_code = re.sub(replace_src, replace_dst, source_code)

            if old != source_code:
                change_count += 1

        append_code = anti_bloat_config.get("append_result", "")
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

        append_plain = anti_bloat_config.get("append_plain", "")
        if type(append_plain) in (tuple, list):
            append_plain = "\n".join(append_plain)

        if append_plain:
            source_code += "\n" + append_plain
            change_count += 1

        if change_count > 0 and self.show_changes:
            self.info(
                "Handling module '%s' with %d change(s) for: %s."
                % (module_name.asString(), change_count, description)
            )

        module_code = anti_bloat_config.get("module_code", None)

        if module_code is not None:
            assert not change_count

            if self.show_changes:
                self.info(
                    "Handling module '%s' with full replacement : %s."
                    % (module_name.asString(), description)
                )

            source_code = module_code

        return source_code

    def onModuleSourceCode(self, module_name, source_code):
        for anti_bloat_config in self.config.get(module_name, section="anti-bloat"):
            if self.evaluateCondition(
                full_name=module_name,
                condition=anti_bloat_config.get("when", "True"),
                # Allow disabling config for a module with matching control tags.
                control_tags=self.control_tags,
            ):
                source_code = self._onModuleSourceCode(
                    module_name=module_name,
                    anti_bloat_config=anti_bloat_config,
                    source_code=source_code,
                )

        return source_code

    def _onFunctionBodyParsing(
        self, module_name, anti_bloat_config, function_name, body
    ):
        context = {}
        context_code = anti_bloat_config.get("context", "")
        if type(context_code) in (tuple, list):
            context_code = "\n".join(context_code)

        # We trust the yaml files, pylint: disable=eval-used,exec-used
        context_ready = not bool(context_code)

        replace_code = anti_bloat_config.get("change_function", {}).get(function_name)

        if replace_code == "un-callable":
            replace_code = """'raise RuntimeError("Must not call %s.%s")'""" % (
                module_name,
                function_name,
            )

        if replace_code is not None:
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

            # Single node is required, extract the generated module body with
            # single expression only statement value or a function body.
            replacement = ast.parse(replacement).body[0]

            if type(replacement) is ast.Expr:
                if type(replacement.value) is ast.Lambda:
                    body[:] = [ast.Return(replacement.value.body)]
                else:
                    body[:] = [ast.Return(replacement.value)]
            elif type(replacement) is ast.Raise:
                body[:] = [replacement]
            else:
                body[:] = replacement.body

            if self.show_changes:
                self.info(
                    "Updated module '%s' function '%s'."
                    % (module_name.asString(), function_name)
                )

    def onFunctionBodyParsing(self, module_name, function_name, body):
        config = self.config.get(module_name, section="anti-bloat")

        if config:
            for anti_bloat_config in config:
                self._onFunctionBodyParsing(
                    module_name=module_name,
                    anti_bloat_config=anti_bloat_config,
                    function_name=function_name,
                    body=body,
                )

    def onModuleRecursion(
        self, module_name, module_filename, module_kind, using_module, source_ref
    ):
        for handled_module_name, mode in self.handled_modules.items():
            if module_name.hasNamespace(handled_module_name):
                # Make sure the compilation aborts or warns if asked to
                if mode == "error":
                    raise NuitkaForbiddenImportEncounter(module_name)
                if mode == "warning" and (
                    (
                        using_module is None
                        or not using_module.getFullName().hasNamespace(
                            handled_module_name
                        )
                    )
                    and source_ref is not None
                ):

                    self.warning(
                        "Undesirable import of '%s' at '%s' encountered. It may slow down compilation."
                        % (handled_module_name, source_ref.getAsString()),
                        mnemonic="unwanted-module",
                    )

    def onModuleEncounter(self, module_name, module_filename, module_kind):
        for handled_module_name, mode in self.handled_modules.items():
            if module_name.hasNamespace(handled_module_name):
                # Either issue a warning, or pretend the module doesn't exist for standalone or
                # at least will not be included.
                if mode == "nofollow":
                    if self.show_changes:
                        self.info(
                            "Forcing import of '%s' to not be followed." % module_name
                        )
                    return (
                        False,
                        "user requested to not follow '%s' import" % module_name,
                    )

        # Do not provide an opinion about it.
        return None

    def decideCompilation(self, module_name):
        for handled_module_name, mode in self.handled_modules.items():
            if mode != "bytecode":
                continue

            if module_name.hasNamespace(handled_module_name):
                return "bytecode"
