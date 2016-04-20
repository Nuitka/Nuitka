#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import re

from nuitka import Options, Variables
from nuitka.containers.oset import OrderedSet
from nuitka.importing.Importing import (
    findModule,
    getModuleNameAndKindFromFilename
)
from nuitka.importing.Recursion import decideRecursion, recurseTo
from nuitka.optimizations.TraceCollections import ConstraintCollectionModule
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import SourceCodeReference, fromFilename
from nuitka.utils import Utils

from .Checkers import checkStatementsSequenceOrNone
from .CodeObjectSpecs import CodeObjectSpec
from .ConstantRefNodes import ExpressionConstantRef
from .FutureSpecs import FutureSpec
from .NodeBases import (
    ChildrenHavingMixin,
    ClosureGiverNodeBase,
    ExpressionMixin,
    NodeBase
)


class PythonModuleMixin:
    def __init__(self, name, package_name):
        assert type(name) is str, type(name)
        assert '.' not in name, name
        assert package_name is None or \
               (type(package_name) is str and package_name != "")

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
            package_package, package_filename, _finding = findModule(
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

            assert package_filename is not None, self.package_name

            _package_name, package_kind = getModuleNameAndKindFromFilename(package_filename)
            # assert _package_name == self.package_name, (package_filename, _package_name, self.package_name)

            decision, _reason = decideRecursion(
                module_filename = package_filename,
                module_name     = self.package_name,
                module_package  = package_package,
                module_kind     = package_kind
            )

            if decision is not None:
                imported_module, is_added = recurseTo(
                    module_package  = package_package,
                    module_filename = package_filename,
                    module_relpath  = Utils.relpath(package_filename),
                    module_kind     = "py",
                    reason          = "Containing package of recursed module '%s'." % self.getFullName(),
                )

                self.package = imported_module

                if is_added:
                    result.append(imported_module)

        if self.package:
            from nuitka.ModuleRegistry import addUsedModule

            addUsedModule(self.package)

#            print "Recursed to package", self.package_name
            result.extend(self.package.attemptRecursion())

        return result

    def getCodeName(self):
        # Abstract method, pylint: disable=R0201
        return None

    def getCompileTimeFilename(self):
        return Utils.abspath(self.getSourceReference().getFilename())

    def getRunTimeFilename(self):
        reference_mode = Options.getFileReferenceMode()

        if reference_mode == "original":
            return self.getCompileTimeFilename()
        elif reference_mode == "frozen":
            return "<frozen %s>" % self.getFullName()
        else:
            filename = self.getCompileTimeFilename()

            full_name = self.getFullName()

            result = Utils.basename(filename)
            current = filename

            levels = full_name.count('.')
            if self.isCompiledPythonPackage():
                levels += 1

            for _i in range(levels):
                current = Utils.dirname(current)
                result = Utils.joinpath(Utils.basename(current), result)

            return result


class CompiledPythonModule(PythonModuleMixin, ChildrenHavingMixin,
                           ClosureGiverNodeBase):
    """ Compiled Python Module

    """

    kind = "COMPILED_PYTHON_MODULE"

    named_children = (
        "body",
    )

    checkers = {
        "body": checkStatementsSequenceOrNone
    }

    def __init__(self, name, package_name, mode, source_ref):
        ClosureGiverNodeBase.__init__(
            self,
            name        = name,
            code_prefix = "module",
            source_ref  = source_ref
        )

        PythonModuleMixin.__init__(
            self,
            name         = name,
            package_name = package_name
        )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "body" : None # delayed
            },
        )

        self.mode = mode

        self.variables = {}

        # The list functions contained in that module.
        self.functions = OrderedSet()

        self.active_functions = OrderedSet()
        self.cross_used_functions = OrderedSet()

        # SSA trace based information about the module.
        self.constraint_collection = None

        self.code_object = CodeObjectSpec(
            code_name     = "<module>" if self.isMainModule() else self.getName(),
            code_kind     = "Module",
            arg_names     = (),
            kw_only_count = 0,
            has_stardict  = False,
            has_starlist  = False,
        )

    def getCodeObject(self):
        return self.code_object

    def getDetails(self):
        return {
            "filename" : self.source_ref.getFilename(),
            "package"  : self.package_name,
            "name"     : self.name
        }

    def asXml(self):
        result = super(CompiledPythonModule, self).asXml()

        for function_body in self.active_functions:
            result.append(function_body.asXml())

        return result

    def asGraph(self, computation_counter):
        from graphviz import Digraph # @UnresolvedImport pylint: disable=F0401,I0021

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
            constraint_collection = function_body.constraint_collection

            for (_variable, _version), variable_trace in constraint_collection.getVariableTracesAll().items():
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

    @staticmethod
    def isCompiledPythonModule():
        return True

    def getParent(self):
        assert False

    def getParentVariableProvider(self):
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

    def isEarlyClosure(self):
        # Modules should immediately closure variables on use.
        # pylint: disable=R0201
        return True

    def getCodeName(self):
        def r(match):
            c = match.group()
            if c == '.':
                return '$'
            else:
                return "$$%d$" % ord(c)

        return "".join(
            re.sub("[^a-zA-Z0-9_]", r ,c)
            for c in
            self.getFullName()
        )

    def addFunction(self, function_body):
        assert function_body not in self.functions

        self.functions.add(function_body)

    def getFunctions(self):
        return self.functions

    def startTraversal(self):
        self.active_functions = OrderedSet()

    def addUsedFunction(self, function_body):
        assert function_body in self.functions

        assert function_body.isExpressionFunctionBody() or \
               function_body.isExpressionClassBody() or \
               function_body.isExpressionGeneratorObjectBody() or \
               function_body.isExpressionCoroutineObjectBody()

        if function_body not in self.active_functions:
            self.active_functions.add(function_body)

    def getUsedFunctions(self):
        return self.active_functions

    def getUnusedFunctions(self):
        for function in self.functions:
            if function not in self.active_functions:
                yield function

    def addCrossUsedFunction(self, function_body):
        if function_body not in self.cross_used_functions:
            self.cross_used_functions.add(function_body)

    def getCrossUsedFunctions(self):
        return self.cross_used_functions

    def getOutputFilename(self):
        main_filename = self.getFilename()

        if main_filename.endswith(".py"):
            result = main_filename[:-3]
        else:
            result = main_filename

        # There are some characters that somehow are passed to shell, by
        # Scons or unknown, so lets avoid them for now.
        return result.replace(')',"").replace('(',"")

    # TODO: Can't really use locals for modules, this should probably be made
    # sure to not be used.
    @staticmethod
    def getLocalsMode():
        return "copy"

    def computeModule(self):
        old_collection = self.constraint_collection

        self.constraint_collection = ConstraintCollectionModule(self)

        module_body = self.getBody()

        if module_body is not None:
            result = module_body.computeStatementsSequence(
                constraint_collection = self.constraint_collection
            )

            if result is not module_body:
                self.setBody(result)

        new_modules = self.attemptRecursion()

        for new_module in new_modules:
            self.constraint_collection.signalChange(
                source_ref = new_module.getSourceReference(),
                tags       = "new_code",
                message    = "Recursed to module package."
            )

        self.constraint_collection.updateFromCollection(old_collection)

    def getTraceCollections(self):
        yield self.constraint_collection

        for function in self.getUsedFunctions():
            yield function.constraint_collection


class CompiledPythonPackage(CompiledPythonModule):
    kind = "COMPILED_PYTHON_PACKAGE"

    def __init__(self, name, package_name, mode, source_ref):
        assert name

        CompiledPythonModule.__init__(
            self,
            name         = name,
            package_name = package_name,
            mode         = mode,
            source_ref   = source_ref
        )

    def getOutputFilename(self):
        return Utils.dirname(self.getFilename())


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


class UncompiledPythonModule(PythonModuleMixin, NodeBase):
    """ Compiled Python Module

    """

    kind = "UNCOMPILED_PYTHON_MODULE"

    def __init__(self, name, package_name, bytecode, filename, user_provided,
                 technical, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        PythonModuleMixin.__init__(
            self,
            name         = name,
            package_name = package_name
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


class SingleCreationMixin:
    created = set()

    def __init__(self):
        assert self.__class__ not in self.created
        self.created.add(self.__class__)


class PythonMainModule(CompiledPythonModule, SingleCreationMixin):
    kind = "PYTHON_MAIN_MODULE"

    def __init__(self, main_added, mode, source_ref):
        CompiledPythonModule.__init__(
            self,
            name         = "__main__",
            package_name = None,
            mode         = mode,
            source_ref   = source_ref
        )

        SingleCreationMixin.__init__(self)

        self.main_added = main_added

    @staticmethod
    def isMainModule():
        return True

    def getOutputFilename(self):
        if self.main_added:
            return Utils.dirname(self.getFilename())
        else:
            return CompiledPythonModule.getOutputFilename(self)


class PythonInternalModule(CompiledPythonModule, SingleCreationMixin):
    kind = "PYTHON_INTERNAL_MODULE"

    def __init__(self):
        CompiledPythonModule.__init__(
            self,
            name         = "__internal__",
            package_name = None,
            mode         = "compiled",
            source_ref   = SourceCodeReference.fromFilenameAndLine(
                filename    = "internal",
                line        = 0,
                future_spec = FutureSpec()
            )
        )

        SingleCreationMixin.__init__(self)

    @staticmethod
    def isInternalModule():
        return True

    def getOutputFilename(self):
        return "__internal"


class PythonShlibModule(PythonModuleMixin, NodeBase):
    kind = "PYTHON_SHLIB_MODULE"

    avoid_duplicates = set()

    def __init__(self, name, package_name, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        PythonModuleMixin.__init__(
            self,
            name         = name,
            package_name = package_name
        )

        # That would be a mistake we just made.
        assert Utils.basename(source_ref.getFilename()) != "<frozen>"

        # That is too likely a bug.
        assert name != "__main__"

        # Duplicates should be avoided by us caching elsewhere before creating
        # the object.
        assert self.getFullName() not in self.avoid_duplicates, self.getFullName()
        self.avoid_duplicates.add(self.getFullName())

    def getDetails(self):
        return {
            "name"         : self.name,
            "package_name" : self.package_name
        }

    def getFilename(self):
        return self.getSourceReference().getFilename()

    def startTraversal(self):
        pass


class ExpressionModuleFileAttributeRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_MODULE_FILE_ATTRIBUTE_REF"

    def __init__(self, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

    def mayRaiseException(self, exception_type):
        return False

    def computeExpression(self, constraint_collection):
        # There is not a whole lot to do here, the path will change at run
        # time
        if Options.getFileReferenceMode() != "runtime":
            result = ExpressionConstantRef(
                constant   = self.getRunTimeFilename(),
                source_ref = self.getSourceReference()
            )

            return result, "new_expression", "Using original '__file__' value."

        return self, None, None

    def getCompileTimeFilename(self):
        return self.getParentModule().getCompileTimeFilename()

    def getRunTimeFilename(self):
        return self.getParentModule().getRunTimeFilename()
