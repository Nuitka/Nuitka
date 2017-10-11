#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Module/Package nodes

The top of the tree. Packages are also modules. Modules are what hold a program
together and cross-module optimizations are the most difficult to tackle.
"""

import os

from nuitka import Options, Variables
from nuitka.containers.oset import OrderedSet
from nuitka.importing.Importing import (
    findModule,
    getModuleNameAndKindFromFilename
)
from nuitka.importing.Recursion import decideRecursion, recurseTo
from nuitka.ModuleRegistry import getModuleByName, getOwnerFromCodeName
from nuitka.optimizations.TraceCollections import TraceCollectionModule
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import SourceCodeReference, fromFilename
from nuitka.utils.CStrings import encodePythonIdentifierToC
from nuitka.utils.FileOperations import relpath

from .Checkers import checkStatementsSequenceOrNone
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase
from .FutureSpecs import FutureSpec, fromFlags
from .IndicatorMixins import EntryPointMixin, MarkNeedsAnnotationsMixin
from .NodeBases import (
    ChildrenHavingMixin,
    ClosureGiverNodeMixin,
    NodeBase,
    extractKindAndArgsFromXML,
    fromXML
)


class PythonModuleBase(NodeBase):
    __slots__ = "name", "package_name", "package"

    def __init__(self, name, package_name, source_ref):
        assert type(name) is str, type(name)
        assert '.' not in name, name
        assert package_name is None or \
               (type(package_name) is str and package_name != "")

        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.name = name
        self.package_name = package_name
        self.package = None

    def getName(self):
        return self.name

    def getPackage(self):
        return self.package_name

    def getFullName(self):
        if self.package_name:
            return self.package_name + '.' + self.getName()
        else:
            return self.getName()

    @staticmethod
    def isMainModule():
        return False

    @staticmethod
    def isInternalModule():
        return False

    def attemptRecursion(self):
        # Make sure the package is recursed to.

        # Return the list of newly added modules.
        result = []

        if self.package_name is not None and self.package is None:
            self.package = getModuleByName(self.package_name)

        if self.package_name is not None and self.package is None:
            package_package, package_filename, finding = findModule(
                importing      = self,
                module_name    = self.package_name,
                parent_package = None,
                level          = 1,
                warn           = python_version < 330
            )

            # TODO: Temporary, if we can't find the package for Python3.3 that
            # is semi-OK, maybe.
            if python_version >= 330 and not package_filename:
                return []

            if self.package_name == "uniconvertor.app.modules":
                return []

            assert package_filename is not None, (self.package_name, finding)

            _package_name, package_kind = getModuleNameAndKindFromFilename(package_filename)
            # assert _package_name == self.package_name, (package_filename, _package_name, self.package_name)

            decision, _reason = decideRecursion(
                module_filename = package_filename,
                module_name     = self.package_name,
                module_package  = package_package,
                module_kind     = package_kind
            )

            if decision is not None:
                self.package, is_added = recurseTo(
                    module_package  = package_package,
                    module_filename = package_filename,
                    module_relpath  = relpath(package_filename),
                    module_kind     = "py",
                    reason          = "Containing package of recursed module '%s'." % self.getFullName(),
                )

                if is_added:
                    result.append(self.package)

        if self.package:
            from nuitka.ModuleRegistry import addUsedModule

            addUsedModule(self.package)

#            print "Recursed to package", self.package_name
            result.extend(self.package.attemptRecursion())

        return result

    def getCodeName(self):
        # Abstract method, pylint: disable=no-self-use
        return None

    def getCompileTimeFilename(self):
        return os.path.abspath(self.getSourceReference().getFilename())

    def getRunTimeFilename(self):
        # TODO: Don't look at such things this late, push this into building.
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

            levels = full_name.count('.')
            if self.isCompiledPythonPackage():
                levels += 1

            for _i in range(levels):
                current = os.path.dirname(current)

                result = os.path.join(
                    os.path.basename(current),
                    result
                )

            return result


class CompiledPythonModule(ChildrenHavingMixin, ClosureGiverNodeMixin,
                           MarkNeedsAnnotationsMixin, EntryPointMixin,
                           PythonModuleBase):
    """ Compiled Python Module

    """

    kind = "COMPILED_PYTHON_MODULE"

    named_children = (
        "body",
        "functions"
    )

    checkers = {
        "body": checkStatementsSequenceOrNone
    }

    def __init__(self, name, package_name, mode, future_spec, source_ref):
        PythonModuleBase.__init__(
            self,
            name         = name,
            package_name = package_name,
            source_ref   = source_ref
        )

        ClosureGiverNodeMixin.__init__(
            self,
            name        = name,
            code_prefix = "module"
        )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "body" : None, # delayed
                "functions" : (),
            },
        )

        MarkNeedsAnnotationsMixin.__init__(self)

        EntryPointMixin.__init__(self)

        self.mode = mode

        self.variables = {}

        self.active_functions = OrderedSet()
        self.cross_used_functions = OrderedSet()

        # Often "None" until tree building finishes its part.
        self.future_spec = future_spec

    def getDetails(self):
        return {
            "filename" : self.source_ref.getFilename(),
            "package"  : self.package_name,
            "name"     : self.name
        }

    def getDetailsForDisplay(self):
        result = self.getDetails()

        if self.future_spec is not None:
            result["code_flags"] = ','.join(self.future_spec.asFlags())

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        # Modules are not having any provider, must not be used,
        assert False

    def getFutureSpec(self):
        return self.future_spec

    def asGraph(self, computation_counter):
        from graphviz import Digraph # @UnresolvedImport pylint: disable=I0021,import-error

        graph = Digraph("cluster_%d" % computation_counter, comment = "Graph for %s" % self.getName())
        graph.body.append("style=filled")
        graph.body.append("color=lightgrey")
        graph.body.append("label=Iteration_%d" % computation_counter)


        def makeTraceNodeName(variable_trace):
            return "%d/ %s %s %s" % (
                computation_counter,
                variable_trace.getVariable(),
                variable_trace.getVersion(),
                variable_trace.__class__.__name__
            )

        for function_body in self.active_functions:
            trace_collection = function_body.trace_collection

            for (_variable, _version), variable_trace in trace_collection.getVariableTracesAll().items():
                node = makeTraceNodeName(variable_trace)

                previous = variable_trace.getPrevious()

                if variable_trace.hasDefiniteUsages():
                    graph.attr("node", style = "filled", color = "blue")
                elif variable_trace.hasPotentialUsages():
                    graph.attr("node", style = "filled", color = "yellow")
                else:
                    graph.attr("node", style = "filled", color = "red")

                graph.node(node)

                if type(previous) is tuple:
                    for previous in previous:
                        graph.edge(makeTraceNodeName(previous), node)
                elif previous is not None:
                    graph.edge(makeTraceNodeName(previous), node)

        return graph

    getBody = ChildrenHavingMixin.childGetter("body")
    setBody = ChildrenHavingMixin.childSetter("body")

    getFunctions = ChildrenHavingMixin.childGetter("functions")
    setFunctions = ChildrenHavingMixin.childSetter("functions")

    @staticmethod
    def isCompiledPythonModule():
        return True

    def getParent(self):
        # We have never have a parent
        return None

    def getParentVariableProvider(self):
        # We have never have a provider
        return None

    def hasVariableName(self, variable_name):
        return variable_name in self.variables or variable_name in self.temp_variables

    def getVariables(self):
        return self.variables.values()

    def getFilename(self):
        return self.source_ref.getFilename()

    def getVariableForAssignment(self, variable_name):
        return self.getProvidedVariable(variable_name)

    def getVariableForReference(self, variable_name):
        return self.getProvidedVariable(variable_name)

    def getVariableForClosure(self, variable_name):
        return self.getProvidedVariable(
            variable_name = variable_name
        )

    def createProvidedVariable(self, variable_name):
        assert variable_name not in self.variables

        result = Variables.ModuleVariable(
            module        = self,
            variable_name = variable_name
        )

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

        return encodePythonIdentifierToC(self.getFullName())

    def addFunction(self, function_body):
        functions = self.getFunctions()
        assert function_body not in functions
        functions += (function_body,)
        self.setFunctions(functions)

    def startTraversal(self):
        self.active_functions = OrderedSet()

    def addUsedFunction(self, function_body):
        assert function_body in self.getFunctions()

        assert function_body.isExpressionFunctionBody() or \
               function_body.isExpressionClassBody() or \
               function_body.isExpressionGeneratorObjectBody() or \
               function_body.isExpressionCoroutineObjectBody() or \
               function_body.isExpressionAsyncgenObjectBody()

        if function_body not in self.active_functions:
            self.active_functions.add(function_body)

    def getUsedFunctions(self):
        return self.active_functions

    def getUnusedFunctions(self):
        for function in self.getFunctions():
            if function not in self.active_functions:
                yield function

    def addCrossUsedFunction(self, function_body):
        if function_body not in self.cross_used_functions:
            self.cross_used_functions.add(function_body)

    def getCrossUsedFunctions(self):
        return self.cross_used_functions

    def getFunctionFromCodeName(self, code_name):
        for function in self.getFunctions():
            if function.getCodeName() == code_name:
                return function

    def getOutputFilename(self):
        main_filename = self.getFilename()

        if main_filename.endswith(".py"):
            result = main_filename[:-3]
        else:
            result = main_filename

        # There are some characters that somehow are passed to shell, by
        # Scons or unknown, so lets avoid them for now.
        return result.replace(')',"").replace('(',"")

    def computeModule(self):
        old_collection = self.trace_collection

        self.trace_collection = TraceCollectionModule(self)

        module_body = self.getBody()

        if module_body is not None:
            result = module_body.computeStatementsSequence(
                trace_collection = self.trace_collection
            )

            if result is not module_body:
                self.setBody(result)

        new_modules = self.attemptRecursion()

        for new_module in new_modules:
            self.trace_collection.signalChange(
                source_ref = new_module.getSourceReference(),
                tags       = "new_code",
                message    = "Recursed to module package."
            )

        self.trace_collection.updateVariablesFromCollection(old_collection)

    def getTraceCollections(self):
        yield self.trace_collection

        for function in self.getUsedFunctions():
            yield function.trace_collection

    def markAsLocalsDict(self):
        # Does not apply to modules.
        pass

    def hasLocalsDict(self):
        return False

    def isUnoptimized(self):
        return False

    def getLocalVariables(self):
        return ()

    def getUserLocalVariables(self):
        return ()

    def getOutlineLocalVariables(self):
        outlines = self.getTraceCollection().getOutlineFunctions()

        if outlines is None:
            return ()

        result = []

        for outline in outlines:
            result.extend(outline.getUserLocalVariables())

        return tuple(result)

    def hasClosureVariable(self, variable):
        return False

    def removeUserVariable(self, variable):
        outlines = self.getTraceCollection().getOutlineFunctions()

        for outline in outlines:
            user_locals = outline.getUserLocalVariables()

            if variable in user_locals:
                outline.removeUserVariable(variable)
                break


class CompiledPythonPackage(CompiledPythonModule):
    kind = "COMPILED_PYTHON_PACKAGE"

    def __init__(self, name, package_name, mode, future_spec, source_ref):
        assert name, source_ref

        CompiledPythonModule.__init__(
            self,
            name         = name,
            package_name = package_name,
            mode         = mode,
            future_spec  = future_spec,
            source_ref   = source_ref
        )

    def getOutputFilename(self):
        return os.path.dirname(self.getFilename())

    @staticmethod
    def canHaveExternalImports():
        return True


def makeUncompiledPythonModule(module_name, filename, bytecode, is_package,
                               user_provided, technical):
    parts = module_name.rsplit('.', 1)
    name = parts[-1]

    package_name = parts[0] if len(parts) == 2 else None
    source_ref = fromFilename(filename)

    if is_package:
        return UncompiledPythonPackage(
            name          = name,
            package_name  = package_name,
            bytecode      = bytecode,
            filename      = filename,
            user_provided = user_provided,
            technical     = technical,
            source_ref    = source_ref
        )
    else:
        return UncompiledPythonModule(
            name          = name,
            package_name  = package_name,
            bytecode      = bytecode,
            filename      = filename,
            user_provided = user_provided,
            technical     = technical,
            source_ref    = source_ref
        )


class UncompiledPythonModule(PythonModuleBase):
    """ Compiled Python Module

    """

    kind = "UNCOMPILED_PYTHON_MODULE"

    __slots__ = "bytecode", "filename", "user_provided", "technical", "used_modules"

    def __init__(self, name, package_name, bytecode, filename, user_provided,
                 technical, source_ref):
        PythonModuleBase.__init__(
            self,
            name         = name,
            package_name = package_name,
            source_ref   = source_ref
        )

        self.bytecode = bytecode
        self.filename = filename

        self.user_provided = user_provided
        self.technical = technical

        self.used_modules = ()

    @staticmethod
    def isUncompiledPythonModule():
        return True

    def isUserProvided(self):
        return self.user_provided

    def isTechnical(self):
        """ Must be bytecode as it's used in CPython library initialization. """
        return self.technical

    def getByteCode(self):
        return self.bytecode

    def getFilename(self):
        return self.filename

    def getUsedModules(self):
        return self.used_modules

    def setUsedModules(self, used_modules):
        self.used_modules = used_modules

    def startTraversal(self):
        pass


class UncompiledPythonPackage(UncompiledPythonModule):
    kind = "UNCOMPILED_PYTHON_PACKAGE"


class PythonMainModule(CompiledPythonModule):
    kind = "PYTHON_MAIN_MODULE"

    def __init__(self, main_added, mode, future_spec, source_ref):
        CompiledPythonModule.__init__(
            self,
            name         = "__main__",
            package_name = None,
            mode         = mode,
            future_spec  = future_spec,
            source_ref   = source_ref
        )

        self.main_added = main_added

    def getDetails(self):
        return {
            "filename"   : self.source_ref.getFilename(),
            "main_added" : self.main_added,
            "mode"       : self.mode
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        if "code_flags" in args:
            future_spec = fromFlags(args["code_flags"])

        result = cls(
            main_added  = args["main_added"] == "True",
            mode        = args["mode"],
            future_spec = future_spec,
            source_ref  = source_ref
        )

        from nuitka.ModuleRegistry import addRootModule
        addRootModule(result)

        function_work = []

        for xml in args["functions"]:
            _kind, node_class, func_args, source_ref = extractKindAndArgsFromXML(xml, source_ref)

            if "provider" in func_args:
                func_args["provider"] = getOwnerFromCodeName(func_args["provider"])
            else:
                func_args["provider"] = result

            if "flags" in args:
                func_args["flags"] = set(func_args["flags"].split(','))

            if "doc" not in args:
                func_args["doc"] = None

            function = node_class.fromXML(
                source_ref = source_ref,
                **func_args
            )

            # Could do more checks for look up of body here, but so what...
            function_work.append(
                (function, iter(iter(xml).next()).next())
            )

        for function, xml in function_work:
            function.setChild(
                "body",
                fromXML(
                    provider   = function,
                    xml        = xml,
                    source_ref = function.getSourceReference()
                )
            )

        result.setChild(
            "body",
            fromXML(
                provider   = result,
                xml        = args["body"][0],
                source_ref = source_ref
            )
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


class PythonInternalModule(CompiledPythonModule):
    kind = "PYTHON_INTERNAL_MODULE"

    def __init__(self):
        CompiledPythonModule.__init__(
            self,
            name         = "__internal__",
            package_name = None,
            mode         = "compiled",
            source_ref   = SourceCodeReference.fromFilenameAndLine(
                filename = "internal",
                line     = 0
            ),
            future_spec  = FutureSpec()
        )

    @staticmethod
    def isInternalModule():
        return True

    def getOutputFilename(self):
        return "__internal"


class PythonShlibModule(PythonModuleBase):
    kind = "PYTHON_SHLIB_MODULE"

    __slots__ = ("used_modules",)

    avoid_duplicates = set()

    def __init__(self, name, package_name, source_ref):
        PythonModuleBase.__init__(
            self,
            name         = name,
            package_name = package_name,
            source_ref   = source_ref
        )

        # That would be a mistake we just made.
        assert os.path.basename(source_ref.getFilename()) != "<frozen>"

        # That is too likely a bug.
        assert name != "__main__"

        # Duplicates should be avoided by us caching elsewhere before creating
        # the object.
        assert self.getFullName() not in self.avoid_duplicates, self.getFullName()
        self.avoid_duplicates.add(self.getFullName())

        self.used_modules = None

    def getDetails(self):
        return {
            "name"         : self.name,
            "package_name" : self.package_name
        }

    def getFilename(self):
        return self.getSourceReference().getFilename()

    def startTraversal(self):
        pass

    def getPyIFilename(self):
        """ Get Python type description filename. """

        path = self.getFilename()
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)

        return os.path.join(dirname, filename.split('.')[0]) + ".pyi"

    def _readPyPIFile(self):
        """ Read the .pyi file if present and scan for dependencies. """

        if self.used_modules is None:
            pyi_filename = self.getPyIFilename()

            if os.path.exists(pyi_filename):
                pyi_deps = OrderedSet()

                for line in open(pyi_filename):
                    line = line.strip()

                    if line.startswith("import "):
                        imported = line[7:]

                        pyi_deps.add(imported)
                    elif line.startswith("from "):
                        parts = line.split(None, 3)
                        assert parts[0] == "from"
                        assert parts[2] == "import"

                        if parts[1] == "typing":
                            continue

                        pyi_deps.add(parts[1])

                        imported = parts[3]
                        if imported.startswith('('):
                            # No multiline imports please
                            assert imported.endswith(')')
                            imported = imported[1:-1]

                            assert imported

                        if imported == '*':
                            continue

                        for name in imported.split(','):
                            name = name.strip()

                            pyi_deps.add(parts[1] + '.' + name)

                if "typing" in pyi_deps:
                    pyi_deps.discard("typing")

                self.used_modules = tuple(pyi_deps)
            else:
                self.used_modules = ()

    def getUsedModules(self):
        self._readPyPIFile()

        return self.used_modules

    def getParentModule(self):
        return self


class ExpressionModuleFileAttributeRef(ExpressionBase):
    kind = "EXPRESSION_MODULE_FILE_ATTRIBUTE_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

    def mayRaiseException(self, exception_type):
        return False

    def computeExpressionRaw(self, trace_collection):
        # There is not a whole lot to do here, the path will change at run
        # time
        if Options.getFileReferenceMode() != "runtime":
            result = makeConstantRefNode(
                constant   = self.getRunTimeFilename(),
                source_ref = self.getSourceReference()
            )

            return result, "new_expression", "Using original '__file__' value."

        return self, None, None

    def getCompileTimeFilename(self):
        return self.getParentModule().getCompileTimeFilename()

    def getRunTimeFilename(self):
        return self.getParentModule().getRunTimeFilename()


class ExpressionModuleLoaderRef(ExpressionBase):
    kind = "EXPRESSION_MODULE_LOADER_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

    def mayRaiseException(self, exception_type):
        return False

    def computeExpressionRaw(self, trace_collection):
        return self, None, None
