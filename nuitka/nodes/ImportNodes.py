#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes related to importing modules or names.

Normally imports are mostly relatively static, but Nuitka also attempts to
cover the uses of "__import__" built-in and other import techniques, that
allow dynamic values.

If other optimizations make it possible to predict these, the compiler can go
deeper that what it normally could. The import expression node can lead to
modules being added. After optimization it will be asked about used modules.
"""

import sys

from nuitka.__past__ import long, unicode, xrange
from nuitka.code_generation.Reports import onMissingTrust
from nuitka.HardImportRegistry import (
    addModuleSingleAttributeNodeFactory,
    hard_modules_aliases,
    hard_modules_limited,
    hard_modules_non_stdlib,
    hard_modules_stdlib,
    hard_modules_trust,
    isHardModule,
    isHardModuleWithoutSideEffect,
    trust_constant,
    trust_importable,
    trust_may_exist,
    trust_node,
    trust_node_factory,
    trust_undefined,
)
from nuitka.importing.Importing import (
    isNonRaisingBuiltinModule,
    isPackageDir,
    locateModule,
    makeModuleUsageAttempt,
    makeParentModuleUsagesAttempts,
)
from nuitka.importing.ImportResolving import resolveModuleName
from nuitka.importing.Recursion import decideRecursion
from nuitka.importing.StandardLibrary import isStandardLibraryPath
from nuitka.Options import (
    isExperimental,
    isStandaloneMode,
    shallMakeModule,
    shallWarnUnusualCode,
)
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.specs.BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    extractBuiltinArgs,
)
from nuitka.Tracing import unusual_logger
from nuitka.utils.ModuleNames import ModuleName

from .ChildrenHavingMixins import (
    ChildHavingModuleMixin,
    ChildrenExpressionBuiltinImportMixin,
    ChildrenExpressionImportlibImportModuleCallMixin,
)
from .ExpressionBases import ExpressionBase
from .ImportHardNodes import (
    ExpressionImportHardBase,
    ExpressionImportModuleNameHardExists,
    ExpressionImportModuleNameHardExistsSpecificBase,
    ExpressionImportModuleNameHardMaybeExists,
)
from .LocalsScopes import GlobalsDictHandle
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseExceptionReplacementExpression,
    makeRaiseImportErrorReplacementExpression,
)
from .shapes.BuiltinTypeShapes import tshape_module, tshape_module_builtin
from .StatementBasesGenerated import StatementImportStarBase


def makeExpressionImportModuleNameHard(
    module_name, import_name, module_guaranteed, source_ref
):
    if hard_modules_trust[module_name].get(import_name) is None:
        return ExpressionImportModuleNameHardMaybeExists(
            module_name=module_name,
            import_name=import_name,
            module_guaranteed=module_guaranteed,
            source_ref=source_ref,
        )
    else:
        return ExpressionImportModuleNameHardExists(
            module_name=module_name,
            import_name=import_name,
            module_guaranteed=module_guaranteed,
            source_ref=source_ref,
        )


class ExpressionImportAllowanceMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self, using_module_name):
        self.using_module_name = using_module_name

        if self.finding == "not-found":
            self.allowed = False
        elif self.finding == "built-in":
            self.allowed = True
        elif self.module_name in hard_modules_stdlib:
            self.allowed = True
        else:
            self.allowed, _reason = decideRecursion(
                using_module_name=self.using_module_name,
                module_filename=self.module_filename,
                module_name=self.module_name,
                module_kind=self.module_kind,
            )

            # In case of hard imports, that are not forbidden explicitly, allow their use
            # anyway.
            if self.allowed is None and self.isExpressionImportModuleHard():
                self.allowed = True


class ExpressionImportModuleFixed(ExpressionBase):
    """Hard coded import names, that we know to exist."

    These created as result of builtin imports and "importlib.import_module" calls
    that were compile time resolved, and for known module names.
    """

    kind = "EXPRESSION_IMPORT_MODULE_FIXED"

    __slots__ = (
        "module_name",
        "value_name",
        "found_module_name",
        "found_module_filename",
        "module_kind",
        "finding",
        "module_usages",
    )

    def __init__(self, module_name, value_name, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.module_name = ModuleName(module_name)
        self.value_name = ModuleName(value_name)

        self.finding = None

        # If not found, we import the package at least
        (
            self.found_module_name,
            self.found_module_filename,
            self.module_kind,
            self.finding,
        ) = self._attemptFollow()

        self.module_usages = makeParentModuleUsagesAttempts(
            makeModuleUsageAttempt(
                module_name=self.found_module_name,
                filename=self.found_module_filename,
                finding=self.finding,
                module_kind=self.module_kind,
                level=0,
                source_ref=self.source_ref,
                reason="import",
            )
        )

    # TODO: This is called in constructor only, is it, then inline it.
    def _attemptFollow(self):
        found_module_name, found_module_filename, module_kind, finding = locateModule(
            module_name=self.module_name,
            parent_package=None,
            level=0,
        )

        if self.finding == "not-found":
            while True:
                module_name = found_module_filename.getPackageName()

                if module_name is None:
                    break

                (
                    found_module_name,
                    found_module_filename,
                    module_kind,
                    finding,
                ) = locateModule(
                    module_name=module_name,
                    parent_package=None,
                    level=0,
                )

                if self.finding != "not-found":
                    break

        return found_module_name, found_module_filename, module_kind, finding

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"module_name": self.module_name, "value_name": self.value_name}

    def getModuleName(self):
        return self.module_name

    def getValueName(self):
        return self.value_name

    @staticmethod
    def mayHaveSideEffects():
        # TODO: For included modules, we might be able to tell, not not done now.
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        # TODO: For included modules, we might be able to tell, not not done now.
        return True

    def getTypeShape(self):
        # TODO: This ought to be dead code, built-in modules have their own nodes now
        # and may only be hard imports, but not this.
        if self.module_name in sys.builtin_module_names:
            return tshape_module_builtin
        else:
            return tshape_module

    def getModuleUsageAttempts(self):
        return self.module_usages

    def computeExpressionRaw(self, trace_collection):
        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Trace the module usage attempt.
        trace_collection.onModuleUsageAttempts(self.getModuleUsageAttempts())

        # Nothing to do about it.
        return self, None, None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        # TODO: For include modules, something might be possible here, consider self.allowance
        # when that is implemented.
        return self.computeExpressionAttribute(
            lookup_node=import_node,
            attribute_name=import_name,
            trace_collection=trace_collection,
        )


class ExpressionImportModuleBuiltin(ExpressionBase):
    """Hard coded import names, that we know to exist."

    These created as result of builtin imports and "importlib.import_module" calls
    that were compile time resolved, and for known module names.
    """

    kind = "EXPRESSION_IMPORT_MODULE_BUILTIN"

    __slots__ = (
        "module_name",
        "value_name",
        "module_kind",
        "builtin_module",
        "module_usages",
    )

    def __init__(self, module_name, value_name, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.module_name = ModuleName(module_name)
        self.value_name = ModuleName(value_name)

        self.builtin_module = __import__(module_name.asString())

        # If not found, we import the package at least
        _module_name, _module_filename, _module_kind, _finding = locateModule(
            module_name=self.module_name,
            parent_package=None,
            level=0,
        )

        assert _module_name == self.module_name, _module_name
        assert _finding == "built-in", _finding
        assert _module_kind is None, _module_kind

        self.module_usages = makeParentModuleUsagesAttempts(
            makeModuleUsageAttempt(
                module_name=self.module_name,
                filename=None,
                finding="built-in",
                module_kind=None,
                level=0,
                source_ref=self.source_ref,
                reason="import",
            )
        )

    @staticmethod
    def getTypeShape():
        return tshape_module_builtin

    def mayRaiseExceptionImportName(self, exception_type, import_name):
        return not hasattr(self.builtin_module, import_name)

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"module_name": self.module_name, "value_name": self.value_name}

    def getModuleName(self):
        return self.module_name

    def getValueName(self):
        return self.value_name

    @staticmethod
    def mayHaveSideEffects():
        return True

    def mayRaiseException(self, exception_type):
        return isNonRaisingBuiltinModule(self.module_name) is not False

    def getModuleUsageAttempts(self):
        return self.module_usages

    def computeExpressionRaw(self, trace_collection):
        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Trace the module usage attempt.
        trace_collection.onModuleUsageAttempts(self.getModuleUsageAttempts())

        # Nothing to do about it.
        return self, None, None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        # TODO: For include modules, something might be possible here, consider self.allowance
        # when that is implemented.
        return self.computeExpressionAttribute(
            lookup_node=import_node,
            attribute_name=import_name,
            trace_collection=trace_collection,
        )


class ExpressionImportModuleHard(
    ExpressionImportAllowanceMixin, ExpressionImportHardBase
):
    """Hard coded import names, e.g. of "__future__"

    These are directly created for some Python mechanics, but also due to
    compile time optimization for imports of statically known modules.
    """

    kind = "EXPRESSION_IMPORT_MODULE_HARD"

    __slots__ = (
        "using_module_name",
        "module",
        "allowed",
        "guaranteed",
        "value_name",
        "is_package",
    )

    def __init__(self, using_module_name, module_name, value_name, source_ref):
        ExpressionImportHardBase.__init__(
            self, module_name=module_name, source_ref=source_ref
        )

        self.value_name = value_name

        ExpressionImportAllowanceMixin.__init__(
            self, using_module_name=using_module_name
        )

        if self.finding != "not-found" and isHardModuleWithoutSideEffect(
            self.module_name
        ):
            __import__(self.module_name.asString())
            self.module = sys.modules[self.value_name]

            self.is_package = hasattr(self.module, "__path__")
        else:
            self.module = None
            self.is_package = None

        self.guaranteed = self.allowed and (
            not shallMakeModule() or self.module_name not in hard_modules_non_stdlib
        )

    @staticmethod
    def isExpressionImportModuleHard():
        return True

    @staticmethod
    def hasVeryTrustedValue():
        return True

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {
            "using_module_name": self.using_module_name,
            "module_name": self.module_name,
            "value_name": self.value_name,
        }

    def getModuleName(self):
        return self.module_name

    def getValueName(self):
        return self.value_name

    def mayHaveSideEffects(self):
        return self.module is None or not self.guaranteed

    def mayRaiseException(self, exception_type):
        return not self.allowed or self.mayHaveSideEffects()

    def getTypeShape(self):
        if self.module_name in sys.builtin_module_names:
            return tshape_module_builtin
        else:
            return tshape_module

    def computeExpressionRaw(self, trace_collection):
        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Trace the module usage attempt.
        trace_collection.onModuleUsageAttempts(self.getModuleUsageAttempts())

        return self, None, None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        return self._computeExpressionAttribute(
            lookup_node=import_node,
            attribute_name=import_name,
            trace_collection=trace_collection,
            is_import=True,
        )

    @staticmethod
    def _getImportNameErrorString(module, module_name, name):
        if python_version < 0x300:
            return "cannot import name %s" % name
        elif python_version < 0x370:
            return "cannot import name %r" % name
        elif isStandaloneMode():
            return "cannot import name %r from %r" % (name, module_name)
        else:
            return "cannot import name %r from %r (%s)" % (
                name,
                module_name,
                module.__file__ if hasattr(module, "__file__") else "unknown location",
            )

    def _makeRaiseExceptionReplacementExpression(
        self, lookup_node, attribute_name, is_import
    ):
        if is_import:
            return makeRaiseExceptionReplacementExpression(
                expression=lookup_node,
                exception_type="ImportError",
                exception_value=self._getImportNameErrorString(
                    self.module, self.value_name, attribute_name
                ),
            )
        else:
            return makeRaiseExceptionReplacementExpression(
                expression=lookup_node,
                exception_type="AttributeError",
                # TODO: Not the right error message
                exception_value=self._getImportNameErrorString(
                    self.module, self.value_name, attribute_name
                ),
            )

    def _computeExpressionAttribute(
        self, lookup_node, attribute_name, trace_collection, is_import
    ):
        # Return driven handling of many cases
        # pylint: disable=too-many-branches,too-many-return-statements

        if self.allowed:
            full_name = self.value_name.getChildNamed(attribute_name)
            full_name = ModuleName(hard_modules_aliases.get(full_name, full_name))

            if isHardModule(full_name):
                trace_collection.onExceptionRaiseExit(BaseException)

                new_node = ExpressionImportModuleHard(
                    using_module_name=self.using_module_name,
                    module_name=full_name,
                    value_name=full_name,
                    source_ref=lookup_node.source_ref,
                )

                return (
                    new_node,
                    "new_expression",
                    "Hard module '%s' submodule '%s' pre-computed."
                    % (self.value_name, attribute_name),
                )

            if self.value_name in hard_modules_trust:
                trust = hard_modules_trust[self.value_name].get(
                    attribute_name, trust_undefined
                )
            else:
                trust = trust_undefined

            if trust is trust_importable:
                # TODO: Change this is a hard module import itself, currently these are not all trusted
                # themselves yet. We do not have to indicate exception, but it makes no sense to annotate
                # that here at this point.
                trace_collection.onExceptionRaiseExit(BaseException)
            elif trust is trust_may_exist:
                trace_collection.onExceptionRaiseExit(BaseException)
            elif (
                trust is not trust_undefined
                and self.module is not None
                and not hasattr(self.module, attribute_name)
            ):
                # TODO: Unify with below branches.
                trace_collection.onExceptionRaiseExit(ImportError)

                new_node = self._makeRaiseExceptionReplacementExpression(
                    lookup_node=lookup_node,
                    attribute_name=attribute_name,
                    is_import=is_import,
                )

                return (
                    new_node,
                    "new_raise",
                    "Hard module '%s' attribute missing '%s* pre-computed."
                    % (self.value_name, attribute_name),
                )
            else:
                if trust is trust_undefined:
                    # Need to attempt module imports if this is for an import
                    # lookup of code like "from value_name import attribute_name".
                    if self.is_package:
                        full_name = self.value_name.getChildNamed(attribute_name)

                        (
                            _sub_module_name,
                            _sub_module_filename,
                            _sub_module_kind,
                            finding,
                        ) = locateModule(
                            module_name=full_name,
                            parent_package=None,
                            level=0,
                        )

                        if finding != "not-found":
                            trace_collection.onExceptionRaiseExit(ImportError)

                            result = makeExpressionImportModuleFixed(
                                using_module_name=self.getParentModule().getFullName(),
                                module_name=full_name,
                                value_name=full_name,
                                source_ref=lookup_node.getSourceReference(),
                            )

                            return (
                                result,
                                "new_expression",
                                "Attribute lookup '%s' of hard module '%s' becomes hard module name import."
                                % (self.value_name, attribute_name),
                            )

                    trace_collection.onExceptionRaiseExit(ImportError)

                    onMissingTrust(
                        "Hard module '%s' attribute '%s' missing trust config for existing value.",
                        lookup_node.getSourceReference(),
                        self.value_name,
                        attribute_name,
                    )
                elif trust is trust_constant and self.module is not None:
                    # Make sure it's actually there, and not becoming the getattr default by accident.
                    assert hasattr(self.module, attribute_name), self

                    return (
                        makeConstantReplacementNode(
                            constant=getattr(self.module, attribute_name),
                            node=lookup_node,
                            user_provided=True,
                        ),
                        "new_constant",
                        "Hard module '%s' imported '%s' pre-computed to constant value."
                        % (self.value_name, attribute_name),
                    )
                elif trust is trust_node:
                    # TODO: Unify with other branches.
                    trace_collection.onExceptionRaiseExit(ImportError)

                    result = trust_node_factory[self.value_name, attribute_name](
                        source_ref=lookup_node.source_ref
                    )

                    return (
                        result,
                        "new_expression",
                        "Attribute lookup '%s' of hard module '%s' becomes node '%s'."
                        % (self.value_name, attribute_name, result.kind),
                    )
                else:
                    result = makeExpressionImportModuleNameHard(
                        module_name=self.value_name,
                        import_name=attribute_name,
                        module_guaranteed=self.guaranteed,
                        source_ref=lookup_node.getSourceReference(),
                    )

                    return (
                        result,
                        "new_expression",
                        "Attribute lookup '%s' of hard module '%s' becomes hard module name import."
                        % (self.value_name, attribute_name),
                    )

        else:
            # Nothing can be known, but lets not do control flow escape, that is just
            # too unlikely.
            trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        return self._computeExpressionAttribute(
            lookup_node=lookup_node,
            attribute_name=attribute_name,
            trace_collection=trace_collection,
            is_import=False,
        )

    def hasShapeTrustedAttributes(self):
        return True


importlib_import_module_spec = BuiltinParameterSpec(
    "importlib.import_module", ("name", "package"), default_count=1
)


class ExpressionImportlibImportModuleRef(
    ExpressionImportModuleNameHardExistsSpecificBase
):
    kind = "EXPRESSION_IMPORTLIB_IMPORT_MODULE_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="importlib",
            import_name="import_module",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    @staticmethod
    def getDetails():
        return {}

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibImportModuleCall,
            builtin_spec=importlib_import_module_spec,
        )

        return result, "new_expression", "Call of 'importlib.import_module' recognized."


def _getImportNameAsStr(value):
    if value is None:
        result = None
    else:
        result = value.getCompileTimeConstant()

    if type(result) in (str, unicode):
        # TODO: This is not handling decoding errors all that well.
        if str is not unicode and type(result) is unicode:
            result = str(result)

    return result


class ExpressionImportlibImportModuleCall(
    ChildrenExpressionImportlibImportModuleCallMixin, ExpressionBase
):
    """Call to "importlib.import_module" """

    kind = "EXPRESSION_IMPORTLIB_IMPORT_MODULE_CALL"

    named_children = "name", "package|optional"

    def __init__(self, name, package, source_ref):
        ChildrenExpressionImportlibImportModuleCallMixin.__init__(
            self,
            name=name,
            package=package,
        )

        ExpressionBase.__init__(self, source_ref)

    @staticmethod
    def _resolveImportLibArgs(module_name, package_name):
        # Relative imports need to be resolved by package name.
        if module_name.startswith("."):
            if not package_name:
                return None

                # TODO: Static exception should be created and warned about, Python2/Python3 differ
                # raise TypeError("relative imports require the 'package' argument")
                # msg = ("the 'package' argument is required to perform a relative import for {!r}")
                # raise TypeError(msg.format(name))

            level = 0
            for character in module_name:
                if character != ".":
                    break
                level += 1
            module_name = module_name[level:]

            dot = len(package_name)
            for _i in xrange(level, 1, -1):
                try:
                    dot = package_name.rindex(".", 0, dot)
                except ValueError:
                    return None
                    # TODO: Static exception should be created and warned about.
                    # raise ValueError("attempted relative import beyond top-level package")

            package_name = package_name[:dot]
            if module_name == "":
                return package_name
            else:
                return "%s.%s" % (package_name, module_name)

        return module_name

    def computeExpression(self, trace_collection):
        module_name = self.subnode_name
        package_name = self.subnode_package

        if (
            package_name is None or package_name.isCompileTimeConstant()
        ) and module_name.isCompileTimeConstant():
            imported_module_name = _getImportNameAsStr(module_name)
            imported_package_name = _getImportNameAsStr(package_name)

            if (
                imported_package_name is None or type(imported_package_name) is str
            ) and type(imported_module_name) is str:
                resolved_module_name = self._resolveImportLibArgs(
                    imported_module_name, imported_package_name
                )

                if resolved_module_name is not None:
                    # Importing may raise an exception obviously, unless we know it will
                    # not.
                    trace_collection.onExceptionRaiseExit(BaseException)

                    result = makeExpressionImportModuleFixed(
                        using_module_name=self.getParentModule().getFullName(),
                        module_name=resolved_module_name,
                        value_name=resolved_module_name,
                        source_ref=self.source_ref,
                    )

                    return (
                        result,
                        "new_expression",
                        "Resolved importlib.import_module call to import of '%s'."
                        % resolved_module_name,
                    )

        # TODO: This is special for this node, need to support for for call base of hard imports

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Importing may raise an exception obviously, unless we know it will
        # not.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None


addModuleSingleAttributeNodeFactory(
    "importlib", "import_module", ExpressionImportlibImportModuleRef
)


def _makeParentImportModuleUsages(module_name, source_ref):
    for parent_package_name in module_name.getParentPackageNames():
        (
            _parent_package_name,
            parent_module_filename,
            parent_module_kind,
            parent_module_finding,
        ) = locateModule(
            module_name=parent_package_name,
            parent_package=None,
            level=0,
        )

        yield makeModuleUsageAttempt(
            module_name=parent_package_name,
            filename=parent_module_filename,
            finding=parent_module_finding,
            module_kind=parent_module_kind,
            level=0,
            source_ref=source_ref,
            reason="import path parent",
        )


class ExpressionBuiltinImport(ChildrenExpressionBuiltinImportMixin, ExpressionBase):
    __slots__ = (
        "follow_attempted",
        "finding",
        "used_modules",
    )

    kind = "EXPRESSION_BUILTIN_IMPORT"

    named_children = (
        "name|setter",
        "globals_arg|optional",
        "locals_arg|optional",
        "fromlist|optional",
        "level|optional",
    )

    def __init__(self, name, globals_arg, locals_arg, fromlist, level, source_ref):
        ChildrenExpressionBuiltinImportMixin.__init__(
            self,
            name=name,
            globals_arg=globals_arg,
            locals_arg=locals_arg,
            fromlist=fromlist,
            level=level,
        )

        ExpressionBase.__init__(self, source_ref)

        self.follow_attempted = False

        # The modules actually referenced in that import if it can be detected. Name
        # imports are considered too.
        self.used_modules = []

        self.finding = None

    def _getLevelValue(self):
        parent_module = self.getParentModule()
        level = self.subnode_level

        if level is None:
            return 0 if parent_module.getFutureSpec().isAbsoluteImport() else -1
        elif not level.isCompileTimeConstant():
            return None
        else:
            level_value = level.getCompileTimeConstant()

            # TODO: Catch this as a static error maybe.
            if type(level_value) not in (int, long):
                return None

            return level_value

    def _attemptFollow(self, module_name):
        # Complex stuff, pylint: disable=too-many-branches

        # Without the level value, we don't know what it is.
        level_value = self._getLevelValue()
        if level_value is None:
            return

        parent_module = self.getParentModule()

        if level_value != 0:
            parent_package = parent_module.getFullName()
            if not parent_module.isCompiledPythonPackage():
                parent_package = parent_package.getPackageName()
        else:
            parent_package = None

        module_name_resolved = resolveModuleName(module_name)
        if module_name_resolved != module_name:
            module_name = module_name_resolved

            self.setChildName(
                makeConstantReplacementNode(
                    constant=module_name.asString(),
                    node=self.subnode_name,
                    user_provided=True,
                )
            )

        module_name = ModuleName(module_name)
        module_name_found, module_filename, module_kind, self.finding = locateModule(
            module_name=ModuleName(module_name),
            parent_package=parent_package,
            level=level_value,
        )

        # Allow for the import look ahead, to change what modules are
        # considered hard imports.
        Plugins.onModuleUsageLookAhead(
            module_name=module_name_found,
            module_filename=module_filename,
            module_kind=module_kind,
        )

        self.used_modules = makeParentModuleUsagesAttempts(
            makeModuleUsageAttempt(
                module_name=module_name_found,
                filename=module_filename,
                module_kind=module_kind,
                finding=self.finding,
                level=level_value,
                source_ref=self.source_ref,
                reason="import",
            )
        )

        if self.finding != "not-found":
            module_name = module_name_found

            import_list = self.subnode_fromlist

            if import_list is not None:
                if import_list.isCompileTimeConstant():
                    import_list = import_list.getCompileTimeConstant()

                if type(import_list) not in (tuple, list):
                    import_list = None

            if (
                module_filename is not None
                and import_list
                and isPackageDir(module_filename)
            ):
                for import_item in import_list:
                    if import_item == "*":
                        continue

                    (
                        name_import_module_name,
                        name_import_module_filename,
                        name_import_module_kind,
                        name_import_finding,
                    ) = locateModule(
                        module_name=ModuleName(import_item),
                        parent_package=module_name,
                        level=1,  # Relative import
                    )

                    self.used_modules = list(self.used_modules)

                    self.used_modules.append(
                        makeModuleUsageAttempt(
                            module_name=name_import_module_name,
                            filename=name_import_module_filename,
                            module_kind=name_import_module_kind,
                            finding=name_import_finding,
                            level=1,
                            source_ref=self.source_ref,
                            reason="import fromlist",
                        )
                    )

                self.used_modules = tuple(self.used_modules)

            return module_filename
        else:
            return None

    def _getImportedValueName(self, imported_module_name):
        from_list_truth = (
            self.subnode_fromlist is not None and self.subnode_fromlist.getTruthValue()
        )

        if from_list_truth is True:
            return imported_module_name
        else:
            return imported_module_name.getTopLevelPackageName()

    def computeExpression(self, trace_collection):
        # Attempt to recurse if not already done, many cases to consider and its
        # return driven, pylint: disable=too-many-branches,too-many-return-statements
        if self.follow_attempted:
            if self.finding == "not-found":
                # Importing and not finding, may raise an exception obviously.
                trace_collection.onExceptionRaiseExit(BaseException)
            else:
                # If we know it exists, only RuntimeError shall occur.
                trace_collection.onExceptionRaiseExit(RuntimeError)

            # Trace the module usage attempts.
            trace_collection.onModuleUsageAttempts(self.used_modules)

            # We stay here.
            return self, None, None

        # Importing may raise an exception obviously, unless we know it will
        # not.
        if self.finding != "built-in":
            trace_collection.onExceptionRaiseExit(BaseException)

        module_name = self.subnode_name

        if module_name.isCompileTimeConstant():
            imported_module_name = module_name.getCompileTimeConstant()

            module_filename = self._attemptFollow(module_name=imported_module_name)
            self.follow_attempted = True

            # Trace the module usage attempts.
            for module_usage_attempt in self.used_modules:
                trace_collection.onModuleUsageAttempt(module_usage_attempt)

            if type(imported_module_name) in (str, unicode):
                if self.finding == "relative":
                    parent_module = self.getParentModule()

                    parent_package = parent_module.getFullName()
                    if not parent_module.isCompiledPythonPackage():
                        parent_package = parent_package.getPackageName()

                    level_value = abs(self._getLevelValue())
                    level_value -= 1

                    while level_value > 0:
                        parent_package = parent_package.getPackageName()
                        level_value -= 1

                    if imported_module_name != "":
                        candidate_module_name = parent_package.getChildNamed(
                            imported_module_name
                        )
                    else:
                        candidate_module_name = parent_package

                    if (
                        candidate_module_name in hard_modules_non_stdlib
                        or module_filename is None
                        or isStandardLibraryPath(module_filename)
                    ):
                        result = ExpressionImportModuleHard(
                            using_module_name=self.getParentModule().getFullName(),
                            module_name=candidate_module_name,
                            value_name=self._getImportedValueName(
                                candidate_module_name
                            ),
                            source_ref=self.source_ref,
                        )

                        return (
                            result,
                            "new_expression",
                            "Lowered import %s module '%s' to hard import."
                            % (
                                (
                                    "hard import"
                                    if candidate_module_name in hard_modules_non_stdlib
                                    else "standard library"
                                ),
                                candidate_module_name.asString(),
                            ),
                        )

                imported_module_name = resolveModuleName(imported_module_name)

                if self.finding == "absolute" and isHardModule(imported_module_name):
                    if (
                        imported_module_name in hard_modules_non_stdlib
                        or module_filename is None
                        or isStandardLibraryPath(module_filename)
                    ):
                        result = ExpressionImportModuleHard(
                            using_module_name=self.getParentModule().getFullName(),
                            module_name=imported_module_name,
                            value_name=self._getImportedValueName(imported_module_name),
                            source_ref=self.source_ref,
                        )

                        return (
                            result,
                            "new_expression",
                            "Lowered import %s module '%s' to hard import."
                            % (
                                (
                                    "hard import"
                                    if imported_module_name in hard_modules_non_stdlib
                                    else "standard library"
                                ),
                                imported_module_name.asString(),
                            ),
                        )
                    elif shallWarnUnusualCode():
                        unusual_logger.warning(
                            "%s: Standard library module '%s' used from outside path %r."
                            % (
                                self.source_ref.getAsString(),
                                imported_module_name.asString(),
                                self.module_filename,
                            )
                        )

                # Built-in module imports can be specialized right away.

                if self.finding == "built-in":
                    result = makeExpressionImportModuleBuiltin(
                        using_module_name=self.getParentModule().getFullName(),
                        module_name=imported_module_name,
                        value_name=self._getImportedValueName(imported_module_name),
                        source_ref=self.source_ref,
                    )

                    # TODO: This ought to preserve side effects from arguments
                    # for full compatibility with strange uses of __import__
                    return (
                        result,
                        "new_expression",
                        "Lowered import of built-in module '%s' to hard import."
                        % imported_module_name.asString(),
                    )

                if self.finding == "not-found":
                    if imported_module_name in hard_modules_limited:
                        result = makeRaiseImportErrorReplacementExpression(
                            expression=self, module_name=imported_module_name
                        )

                        return (
                            result,
                            "new_raise",
                            "Lowered import of missing standard library module '%s' to hard import."
                            % imported_module_name.asString(),
                        )

                elif (
                    isStandaloneMode()
                    and self.used_modules
                    and isExperimental("standalone-imports")
                ):
                    result = makeExpressionImportModuleFixed(
                        using_module_name=self.getParentModule().getFullName(),
                        module_name=self.used_modules[0].module_name,
                        value_name=self._getImportedValueName(
                            self.used_modules[0].module_name
                        ),
                        source_ref=self.source_ref,
                    )

                    return (
                        result,
                        "new_expression",
                        "Lowered import of module '%s' to fixed import."
                        % imported_module_name.asString(),
                    )
            else:
                # TODO: This doesn't preserve side effects.

                # Non-strings is going to raise an error.
                (
                    new_node,
                    change_tags,
                    message,
                ) = trace_collection.getCompileTimeComputationResult(
                    node=self,
                    computation=lambda: __import__(
                        module_name.getCompileTimeConstant()
                    ),
                    description="Replaced '__import__' call with non-string module name argument.",
                )

                # Must fail, must not go on when it doesn't.
                assert change_tags == "new_raise", module_name

                return new_node, change_tags, message

        # Trace the module usage attempts, doing it twice will not harm, this
        # becomes a set.
        for module_usage_attempt in self.used_modules:
            trace_collection.onModuleUsageAttempt(module_usage_attempt)

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None

    # TODO: Add computeExpressionImportName

    def mayRaiseException(self, exception_type):
        return self.finding != "built-in"


class StatementImportStar(StatementImportStarBase):
    kind = "STATEMENT_IMPORT_STAR"

    named_children = ("module",)
    node_attributes = ("target_scope",)
    auto_compute_handling = "post_init,operation"

    def postInitNode(self):
        # TODO: Abstract these things in some better way, and do not make it permanent.
        if type(self.target_scope) is GlobalsDictHandle:
            self.target_scope.markAsEscaped()

    def getTargetDictScope(self):
        return self.target_scope

    def computeStatementOperation(self, trace_collection):
        trace_collection.onLocalsDictEscaped(self.target_scope)

        # Need to invalidate everything, and everything could be assigned to
        # something else now.
        trace_collection.removeAllKnowledge()

        # We could always encounter that __all__ is a strange beast and causes
        # the exception.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # Not done. TODO: Later we can try and check for "__all__" if it
        # really can be that way.
        return True

    @staticmethod
    def getStatementNiceName():
        return "star import statement"


class ExpressionImportName(ChildHavingModuleMixin, ExpressionBase):
    kind = "EXPRESSION_IMPORT_NAME"

    named_children = ("module",)

    __slots__ = ("import_name", "level")

    def __init__(self, module, import_name, level, source_ref):
        ChildHavingModuleMixin.__init__(self, module=module)

        ExpressionBase.__init__(self, source_ref)

        self.import_name = import_name
        self.level = level

        # Not allowed.
        assert level is not None

        assert module is not None

    def getImportName(self):
        return self.import_name

    def getImportLevel(self):
        return self.level

    def getDetails(self):
        return {"import_name": self.import_name, "level": self.level}

    def computeExpression(self, trace_collection):
        return self.subnode_module.computeExpressionImportName(
            import_node=self,
            import_name=self.import_name,
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_module.mayRaiseExceptionImportName(
            exception_type=exception_type, import_name=self.import_name
        )


def makeExpressionImportModuleFixed(
    using_module_name, module_name, value_name, source_ref
):
    module_name = resolveModuleName(module_name)
    value_name = resolveModuleName(value_name)

    if isHardModule(module_name):
        return ExpressionImportModuleHard(
            using_module_name=using_module_name,
            module_name=module_name,
            value_name=value_name,
            source_ref=source_ref,
        )
    else:
        return ExpressionImportModuleFixed(
            module_name=module_name,
            value_name=value_name,
            source_ref=source_ref,
        )


def makeExpressionImportModuleBuiltin(
    using_module_name, module_name, value_name, source_ref
):
    module_name = resolveModuleName(module_name)
    value_name = resolveModuleName(value_name)

    if isHardModule(module_name):
        return ExpressionImportModuleHard(
            using_module_name=using_module_name,
            module_name=module_name,
            value_name=value_name,
            source_ref=source_ref,
        )
    else:
        return ExpressionImportModuleBuiltin(
            module_name=module_name,
            value_name=value_name,
            source_ref=source_ref,
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
