#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Module/Package nodes

The top of the tree. Packages are also modules. Modules are what hold a program
together and cross-module optimizations are the most difficult to tackle.
"""

import os

from nuitka import Options, Variables
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import locateModule, makeModuleUsageAttempt
from nuitka.importing.Recursion import decideRecursion, recurseTo
from nuitka.ModuleRegistry import getModuleByName, getOwnerFromCodeName
from nuitka.optimizations.TraceCollections import TraceCollectionModule
from nuitka.Options import hasPythonFlagIsolated
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import fromFilename
from nuitka.tree.SourceHandling import parsePyIFile, readSourceCodeFromFilename
from nuitka.utils.CStrings import encodePythonIdentifierToC
from nuitka.utils.FileOperations import switchFilenameExtension
from nuitka.utils.Importing import (
    getExtensionModuleSuffixes,
    getPackageDirFilename,
)
from nuitka.utils.ModuleNames import ModuleName

from .ChildrenHavingMixins import (
    ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin,
)
from .FutureSpecs import fromFlags
from .IndicatorMixins import EntryPointMixin, MarkNeedsAnnotationsMixin
from .LocalsScopes import getLocalsDictHandle
from .NodeBases import (
    ClosureGiverNodeMixin,
    NodeBase,
    extractKindAndArgsFromXML,
    fromXML,
)


class PythonModuleBase(NodeBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = ("module_name", "reason")

    def __init__(self, module_name, reason, source_ref):
        assert type(module_name) is ModuleName, module_name
        assert module_name != "", source_ref

        NodeBase.__init__(self, source_ref=source_ref)

        self.module_name = module_name
        self.reason = reason

    def getDetails(self):
        return {"module_name": self.module_name}

    def getFullName(self):
        return self.module_name

    @staticmethod
    def isMainModule():
        return False

    @staticmethod
    def isTopModule():
        return False

    def attemptRecursion(self):
        # Make sure the package is recursed to if any
        package_name = self.module_name.getPackageName()
        if package_name is None:
            return ()

        # Return the list of newly added modules.

        package = getModuleByName(package_name)

        if package_name is not None and package is None:
            (
                _package_name,
                package_filename,
                package_module_kind,
                finding,
            ) = locateModule(
                module_name=package_name,
                parent_package=None,
                level=0,
            )

            # If we can't find the package for Python3 that is semi-OK, it might be in a
            # namespace package, these have no init code.
            if python_version >= 0x300 and not package_filename:
                return ()

            if package_name == "uniconvertor.app.modules":
                return ()

            assert package_filename is not None, (package_name, finding)

            assert _package_name == package_name, (
                package_filename,
                _package_name,
                package_name,
            )

            decision, _reason = decideRecursion(
                using_module_name=self.getFullName(),
                module_filename=package_filename,
                module_name=package_name,
                module_kind=package_module_kind,
            )

            if decision is not None:
                package = recurseTo(
                    module_name=package_name,
                    module_filename=package_filename,
                    module_kind=package_module_kind,
                    source_ref=self.source_ref,
                    reason="parent package",
                    using_module_name=self.module_name,
                )

        if package:
            from nuitka.ModuleRegistry import addUsedModule

            addUsedModule(
                package,
                using_module=self,
                usage_tag="package",
                reason="Containing package of '%s'." % self.getFullName(),
                source_ref=self.source_ref,
            )

    def getCodeName(self):
        # Virtual method, pylint: disable=no-self-use
        return None

    def getCompileTimeFilename(self):
        """The compile time filename for the module.

        Returns:
            Full path to module file at compile time.
        Notes:
            We are getting the absolute path here, since we do
            not want to have to deal with resolving paths at
            all.

        """
        return os.path.abspath(self.source_ref.getFilename())

    def getCompileTimeDirectory(self):
        """The compile time directory for the module.

        Returns:
            Full path to module directory at compile time.
        Notes:
            For packages, we let the package directory be
            the result, otherwise the containing directory
            is the result.
        Notes:
            Use this to find files nearby a module, mainly
            in plugin code.
        """
        result = self.getCompileTimeFilename()
        if not os.path.isdir(result):
            result = os.path.dirname(result)
        return result

    def getRunTimeFilename(self):
        reference_mode = Options.getFileReferenceMode()

        if reference_mode == "original":
            return self.getCompileTimeFilename()
        elif reference_mode == "frozen":
            return "<frozen %s>" % self.getFullName()
        else:
            filename = self.getCompileTimeFilename()

            full_name = self.getFullName()

            result = os.path.basename(filename)
            current = filename

            levels = full_name.count(".")
            if (
                self.isCompiledPythonPackage()
                and not self.isCompiledPythonNamespacePackage()
            ):
                levels += 1

            for _i in range(levels):
                current = os.path.dirname(current)

                result = os.path.join(os.path.basename(current), result)

            # Avoid unnecessary unicode path values
            if str is not bytes:
                try:
                    result = str(result)
                except UnicodeDecodeError:
                    pass

            return result

    @staticmethod
    def isExtensionModulePackage():
        return False


class CompiledPythonModule(
    ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin,
    ClosureGiverNodeMixin,
    MarkNeedsAnnotationsMixin,
    EntryPointMixin,
    PythonModuleBase,
):
    """Compiled Python Module"""

    # This one has a few indicators, pylint: disable=too-many-instance-attributes

    kind = "COMPILED_PYTHON_MODULE"

    __slots__ = (
        "is_top",
        "name",
        "code_prefix",
        "code_name",
        "uids",
        "temp_variables",
        "temp_scopes",
        "preserver_id",
        "needs_annotations_dict",
        "trace_collection",
        "mode",
        "variables",
        "active_functions",
        "visited_functions",
        "cross_used_functions",
        "used_modules",
        "future_spec",
        "source_code",
        "module_dict_name",
        "locals_scope",
    )

    named_children = ("body|statements_or_none+setter", "functions|tuple+setter")

    def __init__(self, module_name, reason, is_top, mode, future_spec, source_ref):
        PythonModuleBase.__init__(
            self,
            module_name=module_name,
            reason=reason,
            source_ref=source_ref,
        )

        ClosureGiverNodeMixin.__init__(
            self, name=module_name.getBasename(), code_prefix="module"
        )

        ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin.__init__(
            self,
            body=None,  # delayed
            functions=(),
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        EntryPointMixin.__init__(self)

        self.is_top = is_top

        self.mode = mode

        self.variables = {}

        # Functions that have been used.
        self.active_functions = OrderedSet()

        # Functions that should be visited again.
        self.visited_functions = set()

        self.cross_used_functions = OrderedSet()

        self.used_modules = OrderedSet()

        # Often "None" until tree building finishes its part.
        self.future_spec = future_spec

        # The source code of the module if changed or not from disk.
        self.source_code = None

        self.module_dict_name = "globals_%s" % (self.getCodeName(),)

        self.locals_scope = getLocalsDictHandle(
            self.module_dict_name, "module_dict", self
        )

        self.used_modules = OrderedSet()

    @staticmethod
    def isCompiledPythonModule():
        return True

    def getDetails(self):
        return {
            "filename": self.source_ref.getFilename(),
            "module_name": self.module_name,
        }

    def getDetailsForDisplay(self):
        result = self.getDetails()

        if self.future_spec is not None:
            result["code_flags"] = ",".join(self.future_spec.asFlags())

        return result

    def getCompilationMode(self):
        return self.mode

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        # Modules are not having any provider, must not be used,
        assert False

    def getFutureSpec(self):
        return self.future_spec

    def setFutureSpec(self, future_spec):
        self.future_spec = future_spec

    def isTopModule(self):
        return self.is_top

    def asGraph(self, graph, desc):
        graph = graph.add_subgraph(
            name="cluster_%s" % desc, comment="Graph for %s" % self.getName()
        )

        #        graph.body.append("style=filled")
        #        graph.body.append("color=lightgrey")
        #        graph.body.append("label=Iteration_%d" % desc)

        def makeTraceNodeName(variable, version, variable_trace):
            return "%s/ %s %s %s" % (
                desc,
                variable.getName(),
                version,
                variable_trace.__class__.__name__,
            )

        for function_body in self.active_functions:
            trace_collection = function_body.trace_collection

            node_names = {}

            for (
                (variable, version),
                variable_trace,
            ) in trace_collection.getVariableTracesAll().items():
                node_name = makeTraceNodeName(variable, version, variable_trace)

                node_names[variable_trace] = node_name

            for (
                (variable, version),
                variable_trace,
            ) in trace_collection.getVariableTracesAll().items():
                node_name = node_names[variable_trace]

                previous = variable_trace.getPrevious()

                attrs = {"style": "filled"}

                if variable_trace.getUsageCount():
                    attrs["color"] = "blue"
                else:
                    attrs["color"] = "red"

                graph.add_node(node_name, **attrs)

                if type(previous) is tuple:
                    for prev_trace in previous:
                        graph.add_edge(node_names[prev_trace], node_name)

                        assert prev_trace is not variable_trace

                elif previous is not None:
                    assert previous is not variable_trace
                    graph.add_edge(node_names[previous], node_name)

        return graph

    def getSourceCode(self):
        if self.source_code is not None:
            return self.source_code
        else:
            # This should of course give same result as before.
            return readSourceCodeFromFilename(
                module_name=self.getFullName(),
                source_filename=self.getCompileTimeFilename(),
            )

    def setSourceCode(self, code):
        self.source_code = code

    def getParent(self):
        # We have never have a parent
        return None

    def getParentVariableProvider(self):
        # We have never have a provider
        return None

    def hasVariableName(self, variable_name):
        return variable_name in self.variables or variable_name in self.temp_variables

    def getProvidedVariables(self):
        return self.variables.values()

    def getFilename(self):
        return self.source_ref.getFilename()

    def getVariableForAssignment(self, variable_name):
        return self.getProvidedVariable(variable_name)

    def getVariableForReference(self, variable_name):
        return self.getProvidedVariable(variable_name)

    def getVariableForClosure(self, variable_name):
        return self.getProvidedVariable(variable_name=variable_name)

    def createProvidedVariable(self, variable_name):
        assert variable_name not in self.variables

        result = Variables.ModuleVariable(module=self, variable_name=variable_name)

        self.variables[variable_name] = result

        return result

    @staticmethod
    def getContainingClassDictCreation():
        return None

    @staticmethod
    def isEarlyClosure():
        # Modules should immediately closure variables on use.
        return True

    def getEntryPoint(self):
        return self

    def getCodeName(self):
        # For code name of modules, we need to translate to C identifiers,
        # removing characters illegal for that.

        if self.code_name is None:
            self.code_name = encodePythonIdentifierToC(self.module_name)

        return self.code_name

    @staticmethod
    def getChildQualname(function_name):
        return function_name

    def addFunction(self, function_body):
        functions = self.subnode_functions
        assert function_body not in functions
        functions += (function_body,)
        self.setChildFunctions(functions)

    def startTraversal(self):
        self.used_modules = None
        self.active_functions = OrderedSet()

    def restartTraversal(self):
        self.visited_functions = set()
        self.used_modules = None

    def getUsedModules(self):
        if self.trace_collection is None:
            # Optimization is not yet done at all, but report writing for error
            # exit may happen.
            return ()

        return self.trace_collection.getModuleUsageAttempts()

    def getUsedDistributions(self):
        return self.trace_collection.getUsedDistributions()

    def addUsedFunction(self, function_body):
        assert function_body in self.subnode_functions, function_body

        assert (
            function_body.isExpressionFunctionBody()
            or function_body.isExpressionClassBodyBase()
            or function_body.isExpressionGeneratorObjectBody()
            or function_body.isExpressionCoroutineObjectBody()
            or function_body.isExpressionAsyncgenObjectBody()
        )

        self.active_functions.add(function_body)

        result = function_body not in self.visited_functions
        self.visited_functions.add(function_body)

        return result

    def getUsedFunctions(self):
        return self.active_functions

    def getUnusedFunctions(self):
        for function in self.subnode_functions:
            if function not in self.active_functions:
                yield function

    def addCrossUsedFunction(self, function_body):
        if function_body not in self.cross_used_functions:
            self.cross_used_functions.add(function_body)

    def getCrossUsedFunctions(self):
        return self.cross_used_functions

    def getFunctionFromCodeName(self, code_name):
        for function in self.subnode_functions:
            if function.getCodeName() == code_name:
                return function

    def getOutputFilename(self):
        main_filename = self.getFilename()

        if main_filename.endswith(".py"):
            result = main_filename[:-3]
        elif main_filename.endswith(".pyw"):
            result = main_filename[:-4]
        else:
            result = main_filename

        # There are some characters that somehow are passed to shell, by
        # Scons or unknown, so lets avoid them for now.
        return result.replace(")", "").replace("(", "")

    def computeModule(self):
        self.restartTraversal()

        old_collection = self.trace_collection

        self.trace_collection = TraceCollectionModule(
            self,
            very_trusted_module_variables=(
                old_collection.getVeryTrustedModuleVariables()
                if old_collection is not None
                else {}
            ),
        )

        module_body = self.subnode_body

        if module_body is not None:
            result = module_body.computeStatementsSequence(
                trace_collection=self.trace_collection
            )

            if result is not module_body:
                self.setChildBody(result)

        self.attemptRecursion()

        # We determine the trusted module variable for use on next turnaround to provide functions with traces for them.
        very_trusted_module_variables = {}
        for module_variable in self.locals_scope.getLocalsRelevantVariables():
            very_trusted_node = self.trace_collection.getVariableCurrentTrace(
                module_variable
            ).getAttributeNodeVeryTrusted()
            if very_trusted_node is not None:
                very_trusted_module_variables[module_variable] = very_trusted_node

        if self.trace_collection.updateVeryTrustedModuleVariables(
            very_trusted_module_variables
        ):
            self.trace_collection.signalChange(
                tags="trusted_module_variables",
                message="Trusting module variable(s) '%s'"
                % ",".join(
                    variable.getName()
                    for variable in self.trace_collection.getVeryTrustedModuleVariables()
                ),
                source_ref=self.source_ref,
            )

        # Finalize locals scopes previously determined for removal in last pass.
        self.trace_collection.updateVariablesFromCollection(
            old_collection=old_collection, source_ref=self.source_ref
        )

        # Indicate if this is pass 1 for the module as return value.
        was_complete = not self.locals_scope.complete

        def markAsComplete(body, trace_collection):
            if body.locals_scope is not None:
                # Make sure the propagated stuff releases memory.
                if body.locals_scope.isMarkedForPropagation():
                    body.locals_scope.onPropagationComplete()

                body.locals_scope.markAsComplete(trace_collection)

        def markEntryPointAsComplete(body):
            markAsComplete(body, body.trace_collection)

            outline_bodies = body.trace_collection.getOutlineFunctions()

            if outline_bodies is not None:
                for outline_body in outline_bodies:
                    markAsComplete(outline_body, body.trace_collection)

            body.optimizeUnusedTempVariables()

        markEntryPointAsComplete(self)

        for function_body in self.getUsedFunctions():
            markEntryPointAsComplete(function_body)

            function_body.optimizeUnusedClosureVariables()
            function_body.optimizeVariableReleases()

        return was_complete

    def getTraceCollections(self):
        yield self.trace_collection

        for function in self.getUsedFunctions():
            yield function.trace_collection

    def isUnoptimized(self):
        # Modules don't do this, pylint: disable=no-self-use
        return False

    def getLocalVariables(self):
        # Modules don't do this, pylint: disable=no-self-use
        return ()

    def getUserLocalVariables(self):
        # Modules don't do this, pylint: disable=no-self-use
        return ()

    @staticmethod
    def getFunctionVariablesWithAutoReleases():
        """Return the list of function variables that should be released at exit."""
        return ()

    def getOutlineLocalVariables(self):
        outlines = self.getTraceCollection().getOutlineFunctions()

        if outlines is None:
            return ()

        result = []

        for outline in outlines:
            result.extend(outline.getUserLocalVariables())

        return result

    def hasClosureVariable(self, variable):
        # Modules don't do this, pylint: disable=no-self-use,unused-argument
        return False

    def removeUserVariable(self, variable):
        outlines = self.getTraceCollection().getOutlineFunctions()

        for outline in outlines:
            user_locals = outline.getUserLocalVariables()

            if variable in user_locals:
                outline.removeUserVariable(variable)
                break

    def getLocalsScope(self):
        return self.locals_scope

    def getRuntimePackageValue(self):
        if self.isCompiledPythonPackage():
            return self.getFullName().asString()

        value = self.getFullName().getPackageName()

        if value is not None:
            return value.asString()

        if self.isMainModule():
            if self.main_added:
                return ""
            else:
                return None
        else:
            return None

    def getRuntimeNameValue(self):
        if self.isMainModule() and Options.hasPythonFlagPackageMode():
            return "__main__"
        elif self.module_name.isMultidistModuleName():
            return "__main__"
        else:
            return self.getFullName().asString()


class CompiledPythonPackage(CompiledPythonModule):
    kind = "COMPILED_PYTHON_PACKAGE"

    def __init__(self, module_name, reason, is_top, mode, future_spec, source_ref):
        CompiledPythonModule.__init__(
            self,
            module_name=module_name,
            reason=reason,
            is_top=is_top,
            mode=mode,
            future_spec=future_spec,
            source_ref=source_ref,
        )

    @staticmethod
    def isCompiledPythonPackage():
        return True

    def getOutputFilename(self):
        result = self.getFilename()

        if os.path.isdir(result):
            return result
        else:
            return os.path.dirname(result)

    @staticmethod
    def canHaveExternalImports():
        return not hasPythonFlagIsolated()


class CompiledPythonNamespacePackage(CompiledPythonPackage):
    kind = "COMPILED_PYTHON_NAMESPACE_PACKAGE"

    @staticmethod
    def isCompiledPythonNamespacePackage():
        return True

    # These have no source code obviously.
    @staticmethod
    def getSourceCode():
        return None


def makeUncompiledPythonModule(
    module_name, reason, filename, bytecode, is_package, technical
):
    source_ref = fromFilename(filename)

    if is_package:
        return UncompiledPythonPackage(
            module_name=module_name,
            reason=reason,
            bytecode=bytecode,
            filename=filename,
            technical=technical,
            source_ref=source_ref,
        )
    else:
        return UncompiledPythonModule(
            module_name=module_name,
            reason=reason,
            bytecode=bytecode,
            filename=filename,
            technical=technical,
            source_ref=source_ref,
        )


class UncompiledPythonModule(PythonModuleBase):
    """Uncompiled Python Module"""

    kind = "UNCOMPILED_PYTHON_MODULE"

    __slots__ = (
        "bytecode",
        "filename",
        "technical",
        "used_modules",
        "distribution_names",
    )

    def __init__(
        self,
        module_name,
        reason,
        bytecode,
        filename,
        technical,
        source_ref,
    ):
        PythonModuleBase.__init__(
            self,
            module_name=module_name,
            reason=reason,
            source_ref=source_ref,
        )

        self.bytecode = bytecode
        self.filename = filename

        self.technical = technical

        self.used_modules = ()
        self.distribution_names = ()

    def finalize(self):
        del self.used_modules
        del self.bytecode

    @staticmethod
    def isUncompiledPythonModule():
        return True

    def isTechnical(self):
        """Must be bytecode as it's used in CPython library initialization."""
        return self.technical

    def getByteCode(self):
        return self.bytecode

    def getFilename(self):
        return self.filename

    def getUsedModules(self):
        return self.used_modules

    def setUsedModules(self, used_modules):
        self.used_modules = used_modules

    def getUsedDistributions(self):
        return self.distribution_names

    def setUsedDistributions(self, distribution_names):
        self.distribution_names = distribution_names

    @staticmethod
    def startTraversal():
        pass


class UncompiledPythonPackage(UncompiledPythonModule):
    kind = "UNCOMPILED_PYTHON_PACKAGE"


class PythonMainModule(CompiledPythonModule):
    """Main module of a program, typically "__main__" but can be inside a package too."""

    kind = "PYTHON_MAIN_MODULE"

    __slots__ = ("main_added", "standard_library_modules")

    def __init__(self, module_name, main_added, mode, future_spec, source_ref):
        assert not Options.shallMakeModule()

        # Is this one from a "__main__.py" file
        self.main_added = main_added

        CompiledPythonModule.__init__(
            self,
            module_name=module_name,
            reason="main",
            is_top=True,
            mode=mode,
            future_spec=future_spec,
            source_ref=source_ref,
        )

        self.standard_library_modules = ()

    def getDetails(self):
        return {
            "filename": self.source_ref.getFilename(),
            "module_name": self.module_name,
            "main_added": self.main_added,
            "mode": self.mode,
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        future_spec = fromFlags(args["code_flags"])

        result = cls(
            main_added=args["main_added"] == "True",
            mode=args["mode"],
            module_name=ModuleName(args["module_name"]),
            future_spec=future_spec,
            source_ref=source_ref,
        )

        from nuitka.ModuleRegistry import addRootModule

        addRootModule(result)

        function_work = []

        for xml in args["functions"]:
            _kind, node_class, func_args, source_ref = extractKindAndArgsFromXML(
                xml, source_ref
            )

            if "provider" in func_args:
                func_args["provider"] = getOwnerFromCodeName(func_args["provider"])
            else:
                func_args["provider"] = result

            if "flags" in args:
                func_args["flags"] = set(func_args["flags"].split(","))

            if "doc" not in args:
                func_args["doc"] = None

            function = node_class.fromXML(source_ref=source_ref, **func_args)

            # Could do more checks for look up of body here, but so what...
            function_work.append((function, iter(iter(xml).next()).next()))

        for function, xml in function_work:
            function.setChildBody(
                fromXML(
                    provider=function, xml=xml, source_ref=function.getSourceReference()
                )
            )

        result.setChildBody(
            fromXML(provider=result, xml=args["body"][0], source_ref=source_ref)
        )

        return result

    @staticmethod
    def isMainModule():
        return True

    def getOutputFilename(self):
        if self.main_added:
            return os.path.dirname(self.getFilename())
        else:
            return CompiledPythonModule.getOutputFilename(self)

    def getUsedModules(self):
        for used_module in CompiledPythonModule.getUsedModules(self):
            yield used_module

        for used_module in self.standard_library_modules:
            yield used_module

    def setStandardLibraryModules(self, early_module_names, stdlib_modules_names):
        self.standard_library_modules = OrderedSet()

        for early_module_name in early_module_names + stdlib_modules_names:
            _early_module_name, module_filename, module_kind, finding = locateModule(
                module_name=early_module_name,
                parent_package=None,
                level=0,
            )

            # Technically required, but not found must not happen
            assert finding != "not-found", early_module_name

            self.standard_library_modules.add(
                makeModuleUsageAttempt(
                    module_name=early_module_name,
                    filename=module_filename,
                    module_kind=module_kind,
                    finding=finding,
                    level=0,
                    source_ref=self.source_ref,
                    reason="stdlib",
                )
            )


class PythonExtensionModule(PythonModuleBase):
    kind = "PYTHON_EXTENSION_MODULE"

    __slots__ = ("used_modules", "module_filename", "technical", "is_package")

    avoid_duplicates = set()

    def __init__(
        self,
        module_name,
        module_filename,
        reason,
        technical,
        source_ref,
    ):
        PythonModuleBase.__init__(
            self,
            module_name=module_name,
            reason=reason,
            source_ref=source_ref,
        )

        # That would be a mistake we just made.
        assert os.path.basename(source_ref.getFilename()) != "<frozen>"

        # That is too likely a bug.
        assert module_name != "__main__"

        # Duplicates should be avoided by us caching elsewhere before creating
        # the object.
        assert self.getFullName() not in self.avoid_duplicates, self.getFullName()
        self.avoid_duplicates.add(self.getFullName())

        # Required to startup
        self.technical = technical

        self.used_modules = None

        if os.path.isdir(module_filename):
            module_filename = getPackageDirFilename(module_filename)
            self.is_package = True
        else:
            self.is_package = False

        self.module_filename = module_filename

    def isExtensionModulePackage(self):
        return self.is_package

    def finalize(self):
        del self.used_modules

    def getFilename(self):
        return self.module_filename

    @staticmethod
    def startTraversal():
        pass

    def isTechnical(self):
        """Must be present as it's used in CPython library initialization."""
        return self.technical

    def _getPyIFilename(self):
        """Get Python type description filename."""

        path = self.getFilename()

        for extension_module_suffix in getExtensionModuleSuffixes():
            if path.endswith(extension_module_suffix):
                for pyi_suffix in (".pyi", ".py"):
                    candidate = switchFilenameExtension(
                        path=path,
                        old_extension=extension_module_suffix,
                        new_extension=pyi_suffix,
                    )

                    if os.path.exists(candidate):
                        return candidate

        return None

    def _readPyIFile(self):
        """Read the .pyi file if present and scan for dependencies."""

        if self.used_modules is None:
            # TODO: Make this a locatePyIFilename function instead.
            pyi_filename = self._getPyIFilename()

            if pyi_filename is not None:
                pyi_deps = parsePyIFile(
                    module_name=self.getFullName(),
                    package_name=(
                        self.getFullName()
                        if self.is_package
                        else self.getFullName().getPackageName()
                    ),
                    pyi_filename=pyi_filename,
                )

                # These are not to be taken serious.
                if "typing" in pyi_deps:
                    pyi_deps.discard("typing")
                if "__future__" in pyi_deps:
                    pyi_deps.discard("__future__")

                # Dependency on itself makes no sense.
                if self.getFullName() in pyi_deps:
                    pyi_deps.discard(self.getFullName())

                # Dependency on containing package makes no sense.
                if self.getFullName().getPackageName() in pyi_deps:
                    pyi_deps.discard(self.getFullName().getPackageName())

                self.used_modules = tuple(pyi_deps)
            else:
                self.used_modules = ()

    def getPyIModuleImportedNames(self):
        self._readPyIFile()

        assert "." not in self.used_modules, self

        return self.used_modules

    @staticmethod
    def getUsedModules():
        # The PyI contents is currently delivered via implicit imports
        # plugin.
        return ()

    @staticmethod
    def getUsedDistributions():
        return {}

    def getParentModule(self):
        return self


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
