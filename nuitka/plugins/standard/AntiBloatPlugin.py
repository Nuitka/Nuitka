#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to avoid bloat at compile time.

Nuitka hard codes stupid monkey patching normally not needed here and avoids
that to be done and causing massive degradations.

"""

import ast
import re

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.Errors import NuitkaForbiddenImportEncounter
from nuitka.ModuleRegistry import getModuleByName
from nuitka.Options import isExperimental
from nuitka.plugins.YamlPluginBase import NuitkaYamlPluginBase
from nuitka.utils.ModuleNames import ModuleName

# spell-checker: ignore dask,numba,statsmodels,matplotlib,sqlalchemy,ipykernel,pyximport

_mode_choices = ("error", "warning", "nofollow", "allow")


class NuitkaPluginAntiBloat(NuitkaYamlPluginBase):
    # Lots of details, a bunch of state is cached and tracked across functions
    # pylint: disable=too-many-instance-attributes

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
        noinclude_pydoc_mode,
        noinclude_ipython_mode,
        noinclude_dask_mode,
        noinclude_numba_mode,
        noinclude_default_mode,
        custom_choices,
        show_changes,
    ):
        # Many details, due to many repetitive arguments,
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements

        NuitkaYamlPluginBase.__init__(self)

        self.show_changes = show_changes

        # Default manually to default argument value:
        if noinclude_setuptools_mode is None:
            noinclude_setuptools_mode = noinclude_default_mode
        if noinclude_pytest_mode is None:
            noinclude_pytest_mode = noinclude_default_mode
        if noinclude_unittest_mode is None:
            noinclude_unittest_mode = noinclude_default_mode
        if noinclude_pydoc_mode is None:
            noinclude_pydoc_mode = noinclude_default_mode
        if noinclude_ipython_mode is None:
            noinclude_ipython_mode = noinclude_default_mode
        if noinclude_dask_mode is None:
            noinclude_dask_mode = noinclude_default_mode
        if noinclude_numba_mode is None:
            noinclude_numba_mode = noinclude_default_mode

        self.handled_modules = OrderedDict()

        # These should be checked, to allow disabling anti-bloat contents.
        self.control_tags = OrderedDict()

        if noinclude_setuptools_mode != "allow":
            self.handled_modules["setuptools"] = noinclude_setuptools_mode, "setuptools"
            self.handled_modules["setuptools_scm"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["triton"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["Cython"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["cython"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["pyximport"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["paddle.utils.cpp_extension"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["torch.utils.cpp_extension"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["numpy.distutils"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
            self.handled_modules["wheel.util"] = (
                noinclude_setuptools_mode,
                "setuptools",
            )
        else:
            self.control_tags["use_setuptools"] = True

        if noinclude_pytest_mode != "allow":
            self.handled_modules["_pytest"] = noinclude_pytest_mode, "pytest"
            self.handled_modules["pytest"] = noinclude_pytest_mode, "pytest"
            self.handled_modules["py"] = noinclude_pytest_mode, "pytest"
            self.handled_modules["nose2"] = noinclude_pytest_mode, "pytest"
            self.handled_modules["nose"] = noinclude_pytest_mode, "pytest"
            self.handled_modules["statsmodels.tools._testing"] = (
                noinclude_pytest_mode,
                "pytest",
            )
            self.handled_modules["sqlalchemy.testing"] = (
                noinclude_pytest_mode,
                "pytest",
            )
            self.handled_modules["distributed.utils_test"] = (
                noinclude_pytest_mode,
                "pytest",
            )
        else:
            self.control_tags["use_pytest"] = True

        if noinclude_unittest_mode != "allow":
            self.handled_modules["unittest"] = noinclude_unittest_mode, "unittest"
            self.handled_modules["doctest"] = noinclude_unittest_mode, "unittest"
            self.handled_modules["test.support"] = noinclude_unittest_mode, "unittest"
            self.handled_modules["test.test_support"] = (
                noinclude_unittest_mode,
                "unittest",
            )
            self.handled_modules["future.moves.test.support"] = (
                noinclude_unittest_mode,
                "unittest",
            )
            self.handled_modules["keras.src.testing_infra"] = (
                noinclude_unittest_mode,
                "unittest",
            )
            self.handled_modules["tf_keras.src.testing_infra"] = (
                noinclude_unittest_mode,
                "unittest",
            )
        else:
            self.control_tags["use_unittest"] = True

        if noinclude_ipython_mode != "allow":
            self.handled_modules["IPython"] = noinclude_ipython_mode, "IPython"
            self.handled_modules["ipykernel"] = noinclude_ipython_mode, "IPython"
            self.handled_modules["jupyter_client"] = (
                noinclude_ipython_mode,
                "IPython",
            )
            self.handled_modules["matplotlib_inline.backend_inline"] = (
                noinclude_ipython_mode,
                "IPython",
            )
            self.handled_modules["altair._magics"] = (
                noinclude_ipython_mode,
                "IPython",
            )
        else:
            self.control_tags["use_ipython"] = True

        if noinclude_dask_mode != "allow":
            self.handled_modules["dask"] = noinclude_dask_mode, "dask"
            self.handled_modules["distributed"] = noinclude_dask_mode, "dask"
        else:
            self.control_tags["use_dask"] = True

        if noinclude_pydoc_mode != "allow":
            self.handled_modules["pydoc"] = noinclude_pydoc_mode, "pydoc"
        else:
            self.control_tags["use_pydoc"] = True

        if noinclude_numba_mode != "allow":
            self.handled_modules["numba"] = noinclude_numba_mode, "numba"
            self.handled_modules["sparse"] = noinclude_numba_mode, "numba"
            self.handled_modules["stumpy"] = noinclude_numba_mode, "numba"
            self.handled_modules["pandas.core._numba.kernels"] = (
                noinclude_numba_mode,
                "numba",
            )
        else:
            self.control_tags["use_numba"] = True

        for custom_choice in custom_choices:
            if custom_choice.count(":") != 1:
                self.sysexit(
                    """\
Error, malformed value '%s' for '--noinclude-custom-mode' used. It has to be of \
form 'module_name:[%s]'."""
                    % (custom_choice, "|".join(_mode_choices))
                )

            module_name, mode = custom_choice.rsplit(":", 1)

            if mode not in _mode_choices and mode != "bytecode":
                self.sysexit(
                    "Error, illegal mode given '%s' in '--noinclude-custom-mode=%s'"
                    % (mode, custom_choice)
                )

            self.handled_modules[ModuleName(module_name)] = mode, module_name

            if mode == "allow":
                self.control_tags["use_%s" % module_name] = True

        self.handled_module_namespaces = {}

        for handled_module_name, (
            mode,
            intended_module_name,
        ) in self.handled_modules.items():
            if mode == "warning":
                if intended_module_name not in self.handled_module_namespaces:
                    self.handled_module_namespaces[intended_module_name] = set()
                self.handled_module_namespaces[intended_module_name].add(
                    handled_module_name
                )

        self.warnings_given = set()

        # Keep track of modules prevented from automatically following and the
        # information given for that.
        self.no_auto_follows = {}

        # Keep track of modules prevented from being followed at all.
        self.no_follows = OrderedDict()

        # Cache execution context for anti-bloat configs.
        self.context_codes = {}

    def getEvaluationConditionControlTags(self):
        return self.control_tags

    def getCacheContributionValues(self, module_name):
        config = self.config.get(module_name, section="anti-bloat")

        if config:
            yield str(config)

            # TODO: Until we can change the evaluation to tell us exactly what
            # control tag values were used, we have to make this one. We sort
            # the values, to try and have order changes in code not matter.
            yield str(tuple(sorted(self.handled_modules.items())))

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--show-anti-bloat-changes",
            action="store_true",
            dest="show_changes",
            default=False,
            help="""\
Annotate what changes are done by the plugin.""",
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
            "--noinclude-pydoc-mode",
            action="store",
            dest="noinclude_pydoc_mode",
            choices=_mode_choices,
            default=None,
            help="""\
What to do if a pydoc import is encountered. This package use is mark of useless
code for deployments and should be avoided.""",
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

    def _getContextCode(self, module_name, anti_bloat_config):
        context_code = anti_bloat_config.get("context", "")
        if type(context_code) in (tuple, list):
            context_code = "\n".join(context_code)

        if context_code not in self.context_codes:
            context = {}

            try:
                # We trust the yaml files, pylint: disable=exec-used
                exec(context_code, context)
            except Exception as e:  # pylint: disable=broad-except
                self.sysexit(
                    """\
Error, cannot exec module '%s', context code '%s' due to: %s"""
                    % (module_name, context_code, e)
                )

            self.context_codes[context_code] = context

        return dict(self.context_codes[context_code])

    def _onModuleSourceCode(self, module_name, anti_bloat_config, source_code):
        # Complex dealing with many cases, pylint: disable=too-many-branches

        description = anti_bloat_config.get("description", "description not given")

        # To allow detection if it did anything.
        change_count = 0

        for replace_src, replace_code in (
            anti_bloat_config.get("replacements") or {}
        ).items():
            # Avoid the eval, if the replace doesn't hit.
            if replace_src not in source_code:
                continue

            if replace_code:
                replace_dst = self.evaluateExpression(
                    full_name=module_name,
                    expression=replace_code,
                    config_name="module '%s' config 'replacements'" % module_name,
                    extra_context=self._getContextCode(
                        module_name=module_name, anti_bloat_config=anti_bloat_config
                    ),
                    single_value=True,
                )
            else:
                replace_dst = ""

            old = source_code
            source_code = source_code.replace(replace_src, replace_dst)

            if old != source_code:
                change_count += 1

        for replace_src, replace_dst in (
            anti_bloat_config.get("replacements_plain") or {}
        ).items():
            old = source_code
            source_code = source_code.replace(replace_src, replace_dst)

            if old != source_code:
                change_count += 1

        for replace_src, replace_dst in (
            anti_bloat_config.get("replacements_re") or {}
        ).items():
            old = source_code
            source_code = re.sub(replace_src, replace_dst, source_code, re.S)

            if old != source_code:
                change_count += 1
            elif isExperimental("display-anti-bloat-mismatches"):
                self.info("No match in %s no match %r" % (module_name, replace_src))

        append_code = anti_bloat_config.get("append_result", "")
        if type(append_code) in (tuple, list):
            append_code = "\n".join(append_code)

        if append_code:
            append_result = self.evaluateExpression(
                full_name=module_name,
                expression=append_code,
                config_name="module '%s' config 'append_code'" % module_name,
                extra_context=self._getContextCode(
                    module_name=module_name, anti_bloat_config=anti_bloat_config
                ),
                single_value=True,
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

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        for anti_bloat_config in self.config.get(module_name, section="anti-bloat"):
            if self.evaluateCondition(
                full_name=module_name, condition=anti_bloat_config.get("when", "True")
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
        replace_code = anti_bloat_config.get("change_function", {}).get(function_name)

        if replace_code == "un-callable":
            replace_code = """'raise RuntimeError("Must not call %s.%s")'""" % (
                module_name,
                function_name,
            )

        if replace_code is None:
            return False

        replacement = self.evaluateExpression(
            full_name=module_name,
            expression=replace_code,
            config_name="module '%s' config 'change_function' of '%s'"
            % (module_name, function_name),
            extra_context=self._getContextCode(
                module_name=module_name, anti_bloat_config=anti_bloat_config
            ),
            single_value=True,
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

        return True

    def onFunctionBodyParsing(self, module_name, function_name, body):
        result = False

        for anti_bloat_config in self.config.get(module_name, section="anti-bloat"):
            if self.evaluateCondition(
                full_name=module_name, condition=anti_bloat_config.get("when", "True")
            ):
                if self._onFunctionBodyParsing(
                    module_name=module_name,
                    anti_bloat_config=anti_bloat_config,
                    function_name=function_name,
                    body=body,
                ):
                    result = True

        return result

    def _onClassBodyParsing(self, module_name, anti_bloat_config, class_name, node):
        replace_code = anti_bloat_config.get("change_class", {}).get(class_name)

        if replace_code == "un-usable":
            replace_code = """
'''
class %(class_name)s:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("Must not call %(module_name)s.%(class_name)s")
'''
""" % {
                "module_name": module_name,
                "class_name": class_name,
            }

        if replace_code is None:
            return False

        replacement = self.evaluateExpression(
            full_name=module_name,
            expression=replace_code,
            config_name="module '%s' config 'change_class' of '%s'"
            % (module_name, class_name),
            extra_context=self._getContextCode(
                module_name=module_name, anti_bloat_config=anti_bloat_config
            ),
            single_value=True,
        )

        # Single node is required, extract the generated module body with
        # single expression only statement value or a function body.
        replacement = ast.parse(replacement).body[0]

        node.body[:] = replacement.body
        node.bases[:] = replacement.bases

        if self.show_changes:
            self.info(
                "Updated module '%s' class '%s'." % (module_name.asString(), class_name)
            )

        return True

    def onClassBodyParsing(self, module_name, class_name, node):
        result = False

        for anti_bloat_config in self.config.get(module_name, section="anti-bloat"):
            if self.evaluateCondition(
                full_name=module_name, condition=anti_bloat_config.get("when", "True")
            ):
                if self._onClassBodyParsing(
                    module_name=module_name,
                    anti_bloat_config=anti_bloat_config,
                    class_name=class_name,
                    node=node,
                ):
                    result = True

        return result

    def _getModuleBloatModeOverrides(self, using_module_name, intended_module_name):
        # Finding a matching configuration aborts the search, not finding one
        # means default behavior should apply.
        for _config_module_name, bloat_mode_overrides in self.getYamlConfigItem(
            module_name=using_module_name,
            section="anti-bloat",
            item_name="bloat-mode-overrides",
            default={},
            decide_relevant=(lambda config_item: intended_module_name in config_item),
            recursive=True,
        ):
            return bloat_mode_overrides[intended_module_name]

        return None

    def decideAnnotations(self, module_name):
        # Finding a matching configuration aborts the search, not finding one
        # means default behavior should apply.
        for _config_module_name, annotations_config_value in self.getYamlConfigItem(
            module_name=module_name,
            section="anti-bloat",
            item_name="annotations",
            default=None,
            decide_relevant=(lambda config_item: config_item in ("yes", "no")),
            recursive=True,
        ):
            return annotations_config_value == "yes"

        return None

    def decideDocStrings(self, module_name):
        # Finding a matching configuration aborts the search, not finding one
        # means default behavior should apply.
        for _config_module_name, doc_strings_config_value in self.getYamlConfigItem(
            module_name=module_name,
            section="anti-bloat",
            item_name="doc_strings",
            default=None,
            decide_relevant=(lambda config_item: config_item in ("yes", "no")),
            recursive=True,
        ):
            return doc_strings_config_value == "yes"

        return None

    def decideAsserts(self, module_name):
        # Finding a matching configuration aborts the search, not finding one
        # means default behavior should apply.
        for _config_module_name, asserts_config_value in self.getYamlConfigItem(
            module_name=module_name,
            section="anti-bloat",
            item_name="asserts",
            default=None,
            decide_relevant=(lambda config_item: config_item in ("yes", "no")),
            recursive=True,
        ):
            return asserts_config_value == "yes"

        return None

    def _applyNoFollowConfiguration(self, module_name):
        for (
            config_of_module_name,
            no_follow_pattern,
            description,
        ) in self.getYamlConfigItemItems(
            module_name=module_name,
            section="anti-bloat",
            item_name="no-follow",
            decide_relevant=lambda key, value: True,
            recursive=True,
        ):
            self.no_follows[no_follow_pattern] = (config_of_module_name, description)

    def onModuleRecursion(
        self,
        module_name,
        module_filename,
        module_kind,
        using_module_name,
        source_ref,
        reason,
    ):
        # pylint: disable=too-many-branches

        # First off, activate "no-follow" configurations of this module.
        self._applyNoFollowConfiguration(module_name=module_name)

        # Do not even look at these. It's either included by a module that is in standard
        # library, or included for a module in standard library.
        if reason == "stdlib" or (
            using_module_name is not None
            and getModuleByName(using_module_name).reason == "stdlib"
        ):
            return

        # This will allow "unittest.mock" to pass "unittest". It's kind of a hack and
        # hopefully unusual.
        if module_name == "unittest" and reason == "import path parent":
            return
        if module_name == "unittest.mock" and module_name not in self.handled_modules:
            return

        for handled_module_name, (
            mode,
            intended_module_name,
        ) in self.handled_modules.items():
            # This will ignore internal usages. In case of error, e.g. above unittest
            # could cause them to happen.
            if using_module_name is not None and using_module_name.hasNamespace(
                handled_module_name
            ):
                return

            if module_name.hasNamespace(handled_module_name):
                if using_module_name is not None:
                    override_mode = self._getModuleBloatModeOverrides(
                        using_module_name=using_module_name,
                        intended_module_name=intended_module_name,
                    )

                    if override_mode is not None:
                        mode = override_mode

                # Make sure the compilation aborts or warns if asked to
                if mode == "error":
                    raise NuitkaForbiddenImportEncounter(
                        module_name, intended_module_name
                    )
                if mode == "warning" and source_ref is not None:
                    if using_module_name.hasOneOfNamespaces(
                        self.handled_module_namespaces[intended_module_name]
                    ):
                        continue

                    key = (
                        module_name,
                        using_module_name,
                        source_ref.getLineNumber(),
                    )

                    if key not in self.warnings_given:
                        if handled_module_name == intended_module_name:
                            handled_module_name_desc = "'%s'" % handled_module_name
                        else:
                            handled_module_name_desc = (
                                "'%s' (intending to avoid '%s')"
                                % (handled_module_name, intended_module_name)
                            )

                        self.warning(
                            """\
Undesirable import of %s in '%s' (at '%s') encountered. It may \
slow down compilation."""
                            % (
                                handled_module_name_desc,
                                using_module_name,
                                source_ref.getAsString(),
                            ),
                            mnemonic="unwanted-module",
                        )

                        self.warnings_given.add(key)

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        for handled_module_name, (
            mode,
            intended_module_name,
        ) in self.handled_modules.items():
            if module_name.hasNamespace(handled_module_name):
                # Either issue a warning, or pretend the module doesn't exist for standalone or
                # at least will not be included.
                if mode == "nofollow":
                    if self.show_changes:
                        self.info(
                            "Forcing import of '%s' (intending to avoid '%s') to not be followed."
                            % (module_name, intended_module_name)
                        )
                    return (
                        False,
                        "user requested to not follow '%s' (intending to avoid '%s') import"
                        % (module_name, intended_module_name),
                    )

        if using_module_name is not None:

            def decideRelevant(key, value):
                # Only checking keys of configs, pylint: disable=unused-argument

                return module_name.hasNamespace(key)

            for (
                config_of_module_name,
                no_auto_follow,
                description,
            ) in self.getYamlConfigItemItems(
                module_name=using_module_name,
                section="anti-bloat",
                item_name="no-auto-follow",
                decide_relevant=decideRelevant,
                recursive=True,
            ):
                assert module_name.hasNamespace(no_auto_follow), no_auto_follow

                self.no_auto_follows[no_auto_follow] = description

                return (
                    False,
                    "according to yaml 'no-auto-follow' configuration of '%s' for '%s'"
                    % (config_of_module_name, no_auto_follow),
                )

        for no_follow_pattern, (
            config_of_module_name,
            description,
        ) in self.no_follows.items():
            if module_name.matchesToShellPattern(no_follow_pattern)[0]:
                return (
                    False,
                    "according to yaml 'no-follow' configuration of '%s' for '%s'"
                    % (config_of_module_name, no_follow_pattern),
                )

        # Do not provide an opinion about it.
        return None

    def decideCompilation(self, module_name):
        for handled_module_name, (
            mode,
            _intended_module_name,
        ) in self.handled_modules.items():
            if mode != "bytecode":
                continue

            if module_name.hasNamespace(handled_module_name):
                return "bytecode"

        # TODO: Detect effective "change_class" and "change_function"
        # configuration for standard library modules, but often enough we are
        # happy to let the bytecode not have the effect, but for these ones it's
        # required. TODO: Make the compilation mode part of the config.
        if module_name == "xmlrpc.server":
            return "compiled"

    def onModuleCompleteSet(self, module_set):
        # TODO: Maybe have an entry point that works on the set of names
        # instead, we are not looking at the modules, and most plugins probably
        # do not care.
        module_names = set(module.getFullName() for module in module_set)

        for module_name, description in self.no_auto_follows.items():
            # Some are irrelevant, e.g. when registering to a module that would have to
            # be used elsewhere.
            if description == "ignore":
                continue

            if module_name not in module_names:
                self.info(
                    """\
Not including '%s' automatically in order to avoid bloat, but this may cause: %s."""
                    % (module_name, description)
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
