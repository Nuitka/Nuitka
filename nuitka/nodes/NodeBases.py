#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node base classes.

These classes provide the generic base classes available for nodes,
statements or expressions alike. There is a dedicated module for
expression only stuff.

"""

# from abc import abstractmethod

import ast
from abc import abstractmethod

from nuitka import Options, Tracing, TreeXML, Variables
from nuitka.__past__ import iterItems
from nuitka.Errors import NuitkaNodeError
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import SourceCodeReference
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)

from .FutureSpecs import fromFlags
from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions
from .NodeMetaClasses import NodeCheckMetaClass, NodeMetaClassBase


class NodeBase(NodeMetaClassBase):
    __slots__ = "parent", "source_ref"

    # This can trigger if this is included to early.
    assert Options.is_full_compat is not None

    # Avoid the attribute unless it's really necessary.
    if Options.is_full_compat:
        __slots__ += ("effective_source_ref",)

    # String to identify the node class, to be consistent with its name.
    kind = None

    @counted_init
    def __init__(self, source_ref):
        # The base class has no __init__ worth calling.

        # Check source reference to meet basic standards, so we note errors
        # when they occur.
        assert source_ref is not None
        assert source_ref.line is not None

        self.parent = None

        self.source_ref = source_ref

    if isCountingInstances():
        __del__ = counted_del()

    @abstractmethod
    def finalize(self):
        pass

    def __repr__(self):
        return "<Node %s>" % (self.getDescription())

    def getDescription(self):
        """Description of the node, intended for use in __repr__ and
        graphical display.

        """
        details = self.getDetailsForDisplay()

        if details:
            return "'%s' with %s" % (self.kind, details)
        else:
            return "'%s'" % self.kind

    def getDetails(self):
        """Details of the node, intended for re-creation.

        We are not using the pickle mechanisms, but this is basically
        part of what the constructor call needs. Real children will
        also be added.

        """
        # Virtual method, pylint: disable=no-self-use
        return {}

    def getDetailsForDisplay(self):
        """Details of the node, intended for use in __repr__ and dumps.

        This is also used for XML.
        """
        return self.getDetails()

    def getCloneArgs(self):
        return self.getDetails()

    def makeClone(self):
        try:
            # Using star dictionary arguments here for generic use.
            result = self.__class__(source_ref=self.source_ref, **self.getCloneArgs())
        except TypeError as e:
            raise NuitkaNodeError("Problem cloning node", self, e)

        effective_source_ref = self.getCompatibleSourceReference()

        if effective_source_ref is not self.source_ref:
            result.setCompatibleSourceReference(effective_source_ref)

        return result

    def makeCloneShallow(self):
        args = self.getDetails()
        args.update(self.getVisitableNodesNamed())

        try:
            # Using star dictionary arguments here for generic use.
            result = self.__class__(source_ref=self.source_ref, **args)
        except TypeError as e:
            raise NuitkaNodeError("Problem cloning node", self, e)

        effective_source_ref = self.getCompatibleSourceReference()

        if effective_source_ref is not self.source_ref:
            result.setCompatibleSourceReference(effective_source_ref)

        return result

    def getParent(self):
        """Parent of the node. Every node except modules has to have a parent."""

        if self.parent is None and not self.isCompiledPythonModule():
            assert False, (self, self.source_ref)

        return self.parent

    def getChildName(self):
        """Return the role in the current parent, subject to changes."""
        parent = self.getParent()

        for key, value in parent.getVisitableNodesNamed():
            if self is value:
                return key

            if type(value) is tuple:
                if self in value:
                    return key, value.index(self)

        return None

    def getChildNameNice(self):
        child_name = self.getChildName()

        if hasattr(self.parent, "nice_children_dict"):
            return self.parent.nice_children_dict[child_name]
        else:
            return child_name

    def getParentFunction(self):
        """Return the parent that is a function."""

        parent = self.getParent()

        while parent is not None and not parent.isExpressionFunctionBodyBase():
            parent = parent.getParent()

        return parent

    def getParentModule(self):
        """Return the parent that is module."""
        parent = self

        while not parent.isCompiledPythonModule():
            if hasattr(parent, "provider"):
                # After we checked, we can use it, will be much faster route
                # to take.
                parent = parent.provider
            else:
                parent = parent.getParent()

        return parent

    def isParentVariableProvider(self):
        # Check if it's a closure giver, in which cases it can provide variables,
        return isinstance(self, ClosureGiverNodeMixin)

    def getParentVariableProvider(self):
        parent = self.getParent()

        while not parent.isParentVariableProvider():
            parent = parent.getParent()

        return parent

    def getParentReturnConsumer(self):
        parent = self.getParent()

        while (
            not parent.isParentVariableProvider()
            and not parent.isExpressionOutlineBody()
        ):
            parent = parent.getParent()

        return parent

    def getParentStatementsFrame(self):
        current = self.getParent()

        while True:
            if current.isStatementsFrame():
                return current

            if current.isParentVariableProvider():
                return None

            if current.isExpressionOutlineBody():
                return None

            current = current.getParent()

    def getSourceReference(self):
        return self.source_ref

    def setCompatibleSourceReference(self, source_ref):
        """Bug compatible line numbers information.

        As CPython outputs the last bit of bytecode executed, and not the
        line of the operation. For example calls, output the line of the
        last argument, as opposed to the line of the operation start.

        For tests, we wants to be compatible. In improved more, we are
        not being fully compatible, and just drop it altogether.
        """

        # Getting the same source reference can be dealt with quickly, so do
        # this first.
        if (
            self.source_ref is not source_ref
            and Options.is_full_compat
            and self.source_ref != source_ref
        ):
            # An attribute outside of "__init__", so we save one memory for the
            # most cases. Very few cases involve splitting across lines.
            # false alarm for non-slot:
            # pylint: disable=I0021,assigning-non-slot,attribute-defined-outside-init
            self.effective_source_ref = source_ref

    def getCompatibleSourceReference(self):
        """Bug compatible line numbers information.

        See above.
        """
        return getattr(self, "effective_source_ref", self.source_ref)

    def asXml(self):
        line = self.source_ref.getLineNumber()

        result = TreeXML.Element("node", kind=self.__class__.__name__, line=str(line))

        compat_line = self.getCompatibleSourceReference().getLineNumber()

        if compat_line != line:
            result.attrib["compat_line"] = str(compat_line)

        for key, value in iterItems(self.getDetailsForDisplay()):
            result.set(key, str(value))

        for name, children in self.getVisitableNodesNamed():
            role = TreeXML.Element("role", name=name)

            result.append(role)

            if children is None:
                role.attrib["type"] = "none"
            elif type(children) not in (list, tuple):
                role.append(children.asXml())
            else:
                role.attrib["type"] = "list"

                for child in children:
                    role.append(child.asXml())

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        # Only some things need a provider, pylint: disable=unused-argument
        return cls(source_ref=source_ref, **args)

    def asXmlText(self):
        xml = self.asXml()

        return TreeXML.toString(xml)

    def dump(self, level=0):
        Tracing.printIndented(level, self)
        Tracing.printSeparator(level)

        for visitable in self.getVisitableNodes():
            visitable.dump(level + 1)

        Tracing.printSeparator(level)

    @staticmethod
    def isStatementsSequence():
        return False

    @staticmethod
    def isStatementsFrame():
        return False

    @staticmethod
    def isCompiledPythonModule():
        # For overload by module nodes
        return False

    @abstractmethod
    def isExpression(self):
        """Is an expression node."""

    @abstractmethod
    def isStatement(self):
        """Is a statement node."""

    def isExpressionBuiltin(self):
        return self.kind.startswith("EXPRESSION_BUILTIN_")

    @staticmethod
    def isStatementAssignmentVariable():
        return False

    @staticmethod
    def isStatementDelVariable():
        return False

    @staticmethod
    def isStatementReleaseVariable():
        return False

    @staticmethod
    def isExpressionConstantRef():
        return False

    @staticmethod
    def isExpressionConstantBoolRef():
        return False

    @staticmethod
    def isExpressionOperationUnary():
        return False

    @staticmethod
    def isExpressionOperationBinary():
        return False

    @staticmethod
    def isExpressionOperationInplace():
        return False

    @staticmethod
    def isExpressionComparison():
        return False

    @staticmethod
    def isExpressionSideEffects():
        return False

    @staticmethod
    def isExpressionMakeSequence():
        return False

    @staticmethod
    def isNumberConstant():
        return False

    @staticmethod
    def isExpressionCall():
        return False

    @staticmethod
    def isExpressionFunctionBodyBase():
        return False

    @staticmethod
    def isExpressionOutlineFunctionBase():
        return False

    @staticmethod
    def isExpressionClassBodyBase():
        return False

    @staticmethod
    def isExpressionImportModuleNameHard():
        return False

    @staticmethod
    def isExpressionFunctionCreation():
        return False

    def visit(self, context, visitor):
        visitor(self)

        for visitable in self.getVisitableNodes():
            visitable.visit(context, visitor)

    @staticmethod
    def getVisitableNodes():

        return ()

    @staticmethod
    def getVisitableNodesNamed():
        """Named children dictionary.

        For use in debugging and XML output.
        """

        return ()

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

    @staticmethod
    def getName():
        """Name of the node if any."""

        return None

    @staticmethod
    def mayHaveSideEffects():
        """Unless we are told otherwise, everything may have a side effect."""

        return True

    def isOrderRelevant(self):
        return self.mayHaveSideEffects()

    def extractSideEffects(self):
        """Unless defined otherwise, the expression is the side effect."""

        return (self,)

    @staticmethod
    def mayRaiseException(exception_type):
        """Unless we are told otherwise, everything may raise everything."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayReturn():
        """May this node do a return exit, to be overloaded for things that might."""
        return False

    @staticmethod
    def mayBreak():
        return False

    @staticmethod
    def mayContinue():
        return False

    def needsFrame(self):
        """Unless we are tolder otherwise, this depends on exception raise."""

        return self.mayRaiseException(BaseException)

    @staticmethod
    def willRaiseAnyException():
        return False

    @staticmethod
    def isStatementAborting():
        """Is the node aborting, control flow doesn't continue after this node."""
        return False


class CodeNodeMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self, name, code_prefix):
        assert name is not None

        self.name = name
        self.code_prefix = code_prefix

        # The code name is determined on demand only.
        self.code_name = None

        # The "UID" values of children kinds are kept here.
        self.uids = {}

    def getName(self):
        return self.name

    def getCodeName(self):
        if self.code_name is None:
            provider = self.getParentVariableProvider().getEntryPoint()
            parent_name = provider.getCodeName()

            uid = "_%d" % provider.getChildUID(self)

            assert isinstance(self, CodeNodeMixin)

            if self.name:
                name = uid + "_" + self.name.strip("<>")
            else:
                name = uid

            if str is not bytes:
                name = name.encode("ascii", "c_identifier").decode()

            self.code_name = "%s$$$%s_%s" % (parent_name, self.code_prefix, name)

        return self.code_name

    def getChildUID(self, node):
        if node.kind not in self.uids:
            self.uids[node.kind] = 0

        self.uids[node.kind] += 1

        return self.uids[node.kind]


class ClosureGiverNodeMixin(CodeNodeMixin):
    """Base class for nodes that provide variables for closure takers."""

    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self, name, code_prefix):
        CodeNodeMixin.__init__(self, name=name, code_prefix=code_prefix)

        self.temp_variables = {}

        self.temp_scopes = {}

        self.preserver_id = 0

    def hasProvidedVariable(self, variable_name):
        return self.locals_scope.hasProvidedVariable(variable_name)

    def getProvidedVariable(self, variable_name):
        if not self.locals_scope.hasProvidedVariable(variable_name):
            variable = self.createProvidedVariable(variable_name=variable_name)
            self.locals_scope.registerProvidedVariable(variable)

        return self.locals_scope.getProvidedVariable(variable_name)

    @abstractmethod
    def createProvidedVariable(self, variable_name):
        """Create a variable provided by this function."""

    def allocateTempScope(self, name):
        self.temp_scopes[name] = self.temp_scopes.get(name, 0) + 1

        return "%s_%d" % (name, self.temp_scopes[name])

    def allocateTempVariable(self, temp_scope, name, temp_type=None):
        if temp_scope is not None:
            full_name = "%s__%s" % (temp_scope, name)
        else:
            assert name != "result"

            full_name = name

        # No duplicates please.
        assert full_name not in self.temp_variables, full_name

        result = self.createTempVariable(temp_name=full_name, temp_type=temp_type)

        # Late added temp variables should be treated with care for the
        # remaining trace.
        if self.trace_collection is not None:
            self.trace_collection.initVariableUnknown(result).addUsage()

        return result

    def createTempVariable(self, temp_name, temp_type):
        if temp_name in self.temp_variables:
            return self.temp_variables[temp_name]

        if temp_type is None:
            temp_class = Variables.TempVariable
        elif temp_type == "bool":
            temp_class = Variables.TempVariableBool
        else:
            assert False, temp_type

        result = temp_class(owner=self, variable_name=temp_name)

        self.temp_variables[temp_name] = result

        return result

    def getTempVariable(self, temp_scope, name):
        if temp_scope is not None:
            full_name = "%s__%s" % (temp_scope, name)
        else:
            full_name = name

        return self.temp_variables[full_name]

    def getTempVariables(self):
        return self.temp_variables.values()

    def _removeTempVariable(self, variable):
        del self.temp_variables[variable.getName()]

    def optimizeUnusedTempVariables(self):
        remove = []

        for temp_variable in self.getTempVariables():
            empty = self.trace_collection.hasEmptyTraces(variable=temp_variable)

            if empty:
                remove.append(temp_variable)

        for temp_variable in remove:
            self._removeTempVariable(temp_variable)

    def allocatePreserverId(self):
        if python_version >= 0x300:
            self.preserver_id += 1

        return self.preserver_id


class ClosureTakerMixin(object):
    """Mixin for nodes that accept variables from closure givers."""

    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self, provider):
        self.provider = provider

        self.taken = set()

    def getParentVariableProvider(self):
        return self.provider

    def getClosureVariable(self, variable_name):
        result = self.provider.getVariableForClosure(variable_name=variable_name)
        assert result is not None, variable_name

        if not result.isModuleVariable():
            self.addClosureVariable(result)

        return result

    def addClosureVariable(self, variable):
        self.taken.add(variable)

        return variable

    def getClosureVariables(self):
        return tuple(
            sorted(
                [take for take in self.taken if not take.isModuleVariable()],
                key=lambda x: x.getName(),
            )
        )

    def getClosureVariableIndex(self, variable):
        closure_variables = self.getClosureVariables()

        for count, closure_variable in enumerate(closure_variables):
            if variable is closure_variable:
                return count

        raise IndexError(variable)

    def hasTakenVariable(self, variable_name):
        for variable in self.taken:
            if variable.getName() == variable_name:
                return True

        return False

    def getTakenVariable(self, variable_name):
        for variable in self.taken:
            if variable.getName() == variable_name:
                return variable

        return None


class StatementBase(NodeBase):
    """Base class for all statement nodes."""

    # Base classes can be abstract, pylint: disable=abstract-method

    @staticmethod
    def isStatement():
        return True

    @staticmethod
    def isExpression():
        return False

    # TODO: Have them all.
    # @abstractmethod
    @staticmethod
    def getStatementNiceName():
        return "un-described statement"

    def computeStatementSubExpressions(self, trace_collection):
        """Compute a statement.

        Default behavior is to just visit the child expressions first, and
        then the node "computeStatement". For a few cases this needs to
        be overloaded.
        """
        expressions = self.getVisitableNodes()

        for count, expression in enumerate(expressions):
            assert expression.isExpression(), (self, expression)

            expression = trace_collection.onExpression(expression)

            if expression.willRaiseAnyException():
                wrapped_expression = makeStatementOnlyNodesFromExpressions(
                    expressions[: count + 1]
                )

                assert wrapped_expression is not None

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For %s the child expression '%s' will raise."
                    % (self.getStatementNiceName(), expression.getChildNameNice()),
                )

        return self, None, None


class SideEffectsFromChildrenMixin(object):
    # Mixins are not allowed to specify slots.
    __slots__ = ()

    def mayHaveSideEffects(self):
        for child in self.getVisitableNodes():
            if child.mayHaveSideEffects():
                return True
        return False

    def extractSideEffects(self):
        # No side effects at all but from the children.
        result = []

        for child in self.getVisitableNodes():
            result.extend(child.extractSideEffects())

        return tuple(result)

    def computeExpressionDrop(self, statement, trace_collection):
        # Expression only statement plays no role, pylint: disable=unused-argument

        side_effects = self.extractSideEffects()

        # TODO: Have a method for nicer output and remove existing overloads
        # by using classes and prefer generic implementation here.
        if side_effects:
            return (
                makeStatementOnlyNodesFromExpressions(side_effects),
                "new_statements",
                "Lowered unused expression %s to its side effects." % self.kind,
            )
        else:
            return (
                None,
                "new_statements",
                "Removed %s without side effects." % self.kind,
            )


def makeChild(provider, child, source_ref):
    child_type = child.attrib.get("type")

    if child_type == "list":
        return [
            fromXML(provider=provider, xml=sub_child, source_ref=source_ref)
            for sub_child in child
        ]
    elif child_type == "none":
        return None
    else:
        return fromXML(provider=provider, xml=child[0], source_ref=source_ref)


def getNodeClassFromKind(kind):
    return NodeCheckMetaClass.kinds[kind]


def extractKindAndArgsFromXML(xml, source_ref):
    kind = xml.attrib["kind"]

    args = dict(xml.attrib)
    del args["kind"]

    if source_ref is None:
        source_ref = SourceCodeReference.fromFilenameAndLine(
            args["filename"], int(args["line"])
        )

        del args["filename"]
        del args["line"]

    else:
        source_ref = source_ref.atLineNumber(int(args["line"]))
        del args["line"]

    node_class = getNodeClassFromKind(kind)

    return kind, node_class, args, source_ref


def fromXML(provider, xml, source_ref=None):
    assert xml.tag == "node", xml

    kind, node_class, args, source_ref = extractKindAndArgsFromXML(xml, source_ref)

    if "constant" in args:
        args["constant"] = ast.literal_eval(args["constant"])

    if kind in (
        "ExpressionFunctionBody",
        "PythonMainModule",
        "PythonCompiledModule",
        "PythonCompiledPackage",
        "PythonInternalModule",
    ):
        delayed = node_class.named_children

        if "code_flags" in args:
            args["future_spec"] = fromFlags(args["code_flags"])
    else:
        delayed = ()

    for child in xml:
        assert child.tag == "role", child.tag

        child_name = child.attrib["name"]

        # Might want to want until provider is updated with some
        # children. In these cases, we pass the XML node, rather
        # than a Nuitka node.
        if child_name not in delayed:
            args[child_name] = makeChild(provider, child, source_ref)
        else:
            args[child_name] = child

    try:
        return node_class.fromXML(provider=provider, source_ref=source_ref, **args)
    except (TypeError, AttributeError):
        Tracing.printLine(node_class, args, source_ref)
        raise
