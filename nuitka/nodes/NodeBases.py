#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

from abc import abstractmethod

from nuitka import Options, Tracing, TreeXML, Variables
from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    intern,
    iterItems
)
from nuitka.Errors import NuitkaNodeError
from nuitka.PythonVersions import python_version
from nuitka.SourceCodeReferences import SourceCodeReference
from nuitka.utils.InstanceCounters import counted_del, counted_init

from .FutureSpecs import fromFlags
from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions
from .NodeMetaClasses import NodeCheckMetaClass, NodeMetaClassBase


class NodeBase(NodeMetaClassBase):
    __slots__ = "parent", "source_ref"

    # Avoid the attribute unless it's really necessary.
    if Options.isFullCompat():
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

    __del__ = counted_del()

    @abstractmethod
    def finalize(self):
        pass

    def __repr__(self):
        return "<Node %s>" % (self.getDescription())

    def getDescription(self):
        """ Description of the node, intended for use in __repr__ and
            graphical display.

        """
        details = self.getDetails()

        if details:
            return "'%s' with %s" % (self.kind, self.getDetails())
        else:
            return "'%s'" % self.kind

    def getDetails(self):
        """ Details of the node, intended for re-creation.

            We are not using the pickle mechanisms, but this is basically
            part of what the constructor call needs. Real children will
            also be added.

        """
        # Virtual method, pylint: disable=no-self-use
        return {}

    def getDetailsForDisplay(self):
        """ Details of the node, intended for use in __repr__ and dumps.

            This is also used for XML.
        """
        return self.getDetails()


    def getDetail(self):
        """ Details of the node, intended for use in __repr__ and graphical
            display.

        """
        return str(self.getDetails())[1:-1]

    def getCloneArgs(self):
        return self.getDetails()

    def makeClone(self):
        try:
            # Using star dictionary arguments here for generic use.
            result = self.__class__(
                source_ref = self.source_ref,
                **self.getCloneArgs()
            )
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
            result = self.__class__(
                source_ref = self.source_ref,
                **args
            )
        except TypeError as e:
            raise NuitkaNodeError("Problem cloning node", self, e)

        effective_source_ref = self.getCompatibleSourceReference()

        if effective_source_ref is not self.source_ref:
            result.setCompatibleSourceReference(effective_source_ref)

        return result

    def getParent(self):
        """ Parent of the node. Every node except modules have to have a parent.

        """

        if self.parent is None and not self.isCompiledPythonModule():
            # print self.getVisitableNodesNamed()
            assert False, (self,  self.source_ref)

        return self.parent

    def getChildName(self):
        """ Return the role in the current parent, subject to changes.

        """
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

        if hasattr(self.parent, "nice_children"):
            return self.parent.nice_children[self.parent.named_children.index(child_name)]
        elif hasattr(self.parent, "nice_child"):
            return self.parent.nice_child
        else:
            return child_name

    def getParentFunction(self):
        """ Return the parent that is a function.

        """

        parent = self.getParent()

        while parent is not None and \
              not parent.isExpressionFunctionBodyBase():
            parent = parent.getParent()

        return parent

    def getParentModule(self):
        """ Return the parent that is module.

        """
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

        while not parent.isParentVariableProvider() and \
              not parent.isExpressionOutlineBody():
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
        """ Bug compatible line numbers information.

            As CPython outputs the last bit of bytecode executed, and not the
            line of the operation. For example calls, output the line of the
            last argument, as opposed to the line of the operation start.

            For tests, we wants to be compatible. In improved more, we are
            not being fully compatible, and just drop it altogether.
        """

        # Getting the same source reference can be dealt with quickly, so do
        # this first.
        if self.source_ref is not source_ref and \
           Options.isFullCompat() and \
           self.source_ref != source_ref:
            # An attribute outside of "__init__", so we save one memory for the
            # most cases. Very few cases involve splitting across lines.
            # pylint: disable=W0201
            self.effective_source_ref = source_ref


    def getCompatibleSourceReference(self):
        """ Bug compatible line numbers information.

            See above.
        """
        return getattr(self, "effective_source_ref", self.source_ref)

    def asXml(self):
        line = self.getSourceReference().getLineNumber()

        result = TreeXML.Element(
            "node",
            kind = self.__class__.__name__,
            line = "%s" % line
        )

        compat_line = self.getCompatibleSourceReference().getLineNumber()

        if compat_line != line:
            result.attrib["compat_line"] = str(compat_line)

        for key, value in iterItems(self.getDetailsForDisplay()):
            result.set(key, str(value))

        for name, children in self.getVisitableNodesNamed():
            role = TreeXML.Element(
                "role",
                name = name
            )

            result.append(role)

            if children is None:
                role.attrib["type"] = "none"
            elif type(children) not in (list, tuple):
                role.append(
                    children.asXml()
                )
            else:
                role.attrib["type"] = "list"

                for child in children:
                    role.append(
                        child.asXml()
                    )

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        # Only some things need a provider, pylint: disable=unused-argument
        return cls(source_ref = source_ref, **args)

    def asXmlText(self):
        xml = self.asXml()

        return TreeXML.toString(xml)

    def dump(self, level = 0):
        Tracing.printIndented(level, self)
        Tracing.printSeparator(level)

        for visitable in self.getVisitableNodes():
            visitable.dump(level + 1)

        Tracing.printSeparator(level)

    @staticmethod
    def isStatementsFrame():
        return False

    @staticmethod
    def isCompiledPythonModule():
        # For overload by module nodes
        return False

    def isExpression(self):
        return self.kind.startswith("EXPRESSION_")

    def isStatement(self):
        return self.kind.startswith("STATEMENT_")

    def isExpressionBuiltin(self):
        return self.kind.startswith("EXPRESSION_BUILTIN_")

    @staticmethod
    def isExpressionConstantRef():
        return False

    @staticmethod
    def isExpressionOperationBinary():
        return False

    def isExpressionSideEffects(self):
        # Virtual method, pylint: disable=no-self-use

        # We need to provide this, as these node kinds are only imported if
        # necessary, but we test against them.
        return False

    def isStatementReraiseException(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def isExpressionMakeSequence(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def isNumberConstant(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def isExpressionCall(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def isExpressionFunctionBodyBase(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def isExpressionOutlineFunctionBodyBase(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def visit(self, context, visitor):
        visitor(self)

        for visitable in self.getVisitableNodes():
            visitable.visit(context, visitor)

    def getVisitableNodes(self):
        # Virtual method, pylint: disable=no-self-use
        return ()

    def getVisitableNodesNamed(self):
        """ Named children dictionary.

            For use in debugging and XML output.
        """

        # Virtual method, pylint: disable=no-self-use
        return ()

    def getName(self):
        # Virtual method, pylint: disable=no-self-use
        return None

    def mayHaveSideEffects(self):
        """ Unless we are told otherwise, everything may have a side effect. """
        # Virtual method, pylint: disable=no-self-use

        return True

    def isOrderRelevant(self):
        return self.mayHaveSideEffects()

    def extractSideEffects(self):
        """ Unless defined otherwise, the expression is the side effect. """

        return (self,)

    def mayRaiseException(self, exception_type):
        """ Unless we are told otherwise, everything may raise everything. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayReturn(self):
        return "_RETURN" in self.kind

    def mayBreak(self):
        # For overload, pylint: disable=no-self-use
        return False

    def mayContinue(self):
        # For overload, pylint: disable=no-self-use
        return False

    def needsFrame(self):
        """ Unless we are tolder otherwise, this depends on exception raise. """

        return self.mayRaiseException(BaseException)

    def willRaiseException(self, exception_type):
        """ Unless we are told otherwise, nothing may raise anything. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return False

    def isStatementAborting(self):
        """ Is the node aborting, control flow doesn't continue after this node.  """
        assert self.isStatement(), self.kind

        return False


class CodeNodeMixin(object):
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
                name = uid + '_' + self.name.strip("<>")
            else:
                name = uid

            self.code_name = "%s$$$%s%s" % (
                parent_name,
                self.code_prefix,
                name
            )

        return self.code_name

    def getChildUID(self, node):
        if node.kind not in self.uids:
            self.uids[node.kind] = 0

        self.uids[node.kind] += 1

        return self.uids[node.kind]


class ChildrenHavingMixin(object):
    named_children = ()

    checkers = {}

    def __init__(self, values):
        assert type(self.named_children) is tuple and self.named_children

        # TODO: Make this true.
        # assert len(self.named_children) > 1, self.kind

        # Check for completeness of given values, everything should be there
        # but of course, might be put to None.
        assert set(values.keys()) == set(self.named_children)

        for name, value in values.items():
            if name in self.checkers:
                value = self.checkers[name](value)

            assert type(value) is not list, name

            if type(value) is tuple:
                assert None not in value, name

                for val in value:
                    val.parent = self
            elif value is not None:
                value.parent = self
            elif value is None:
                pass
            else:
                assert False, type(value)

            attr_name = "subnode_" + name
            setattr(self, attr_name, value)

    def setChild(self, name, value):
        """ Set a child value.

            Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name in self.named_children, name

        # Lists as inputs are OK, but turn them into tuples.
        if type(value) is list:
            value = tuple(value)

        if name in self.checkers:
            value = self.checkers[name](value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        attr_name = "subnode_" + name

        # Determine old value, and inform it about loosing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def getChild(self, name):
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

    @staticmethod
    def childGetter(name):
        attr_name = intern("subnode_" + name)

        def getter(self):
            return getattr(self, attr_name)

        return getter

    @staticmethod
    def childSetter(name):
        def setter(self, value):
            self.setChild(name, value)

        return setter

    def getVisitableNodes(self):
        # TODO: Consider if a generator would be faster.
        result = []

        for name in self.named_children:
            attr_name = "subnode_" + name

            value = getattr(self, attr_name)

            if value is None:
                pass
            elif type(value) is tuple:
                result += list(value)
            elif isinstance(value, NodeBase):
                result.append(value)
            else:
                raise AssertionError(
                    self,
                    "has illegal child", name, value, value.__class__
                )

        return tuple(result)

    def getVisitableNodesNamed(self):
        """ Named children dictionary.

            For use in debugging and XML output.
        """
        for name in self.named_children:
            attr_name = "subnode_" + name
            value = getattr(self, attr_name)

            yield name, value


    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )

        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.
        for key in self.named_children:
            value = self.getChild(key)

            if value is None:
                pass
            elif type(value) is tuple:
                if old_node in value:
                    if new_node is not None:
                        self.setChild(
                            key,
                            tuple(
                                (val if val is not old_node else new_node)
                                for val in
                                value
                            )
                        )
                    else:
                        self.setChild(
                            key,
                            tuple(
                                val
                                for val in
                                value
                                if val is not old_node
                            )
                        )

                    return key
            elif isinstance(value, NodeBase):
                if old_node is value:
                    self.setChild(key, new_node)

                    return key
            else:
                assert False, (key, value, value.__class__)

        raise AssertionError(
            "Didn't find child",
            old_node,
            "in",
            self
        )

    def getCloneArgs(self):
        values = {}

        for key in self.named_children:
            value = self.getChild(key)

            assert type(value) is not list, key

            if value is None:
                values[key] = None
            elif type(value) is tuple:
                values[key] = tuple(
                    v.makeClone()
                    for v in
                    value
                )
            else:
                values[key] = value.makeClone()

        values.update(
            self.getDetails()
        )

        return values

    def finalize(self):
        del self.parent

        for c in self.getVisitableNodes():
            c.finalize()


class ClosureGiverNodeMixin(CodeNodeMixin):
    """ Blass class for nodes that provide variables for closure takers. """
    def __init__(self, name, code_prefix):
        CodeNodeMixin.__init__(
            self,
            name        = name,
            code_prefix = code_prefix
        )

        self.providing = {}
        self.variable_order = []

        self.temp_variables = {}

        self.temp_scopes = {}

        self.preserver_id = 0

    def hasProvidedVariable(self, variable_name):
        return variable_name in self.providing

    def getProvidedVariable(self, variable_name):
        if variable_name not in self.providing:
            self.providing[variable_name] = self.createProvidedVariable(
                variable_name = variable_name
            )
            self.variable_order.append(variable_name)

        return self.providing[variable_name]

    def createProvidedVariable(self, variable_name):
        # Virtual method, pylint: disable=no-self-use
        assert type(variable_name) is str

        return None

    def registerProvidedVariable(self, variable):
        assert variable is not None

        variable_name = variable.getName()
        self.providing[variable_name] = variable
        self.variable_order.append(variable_name)

    def getProvidedVariableOrder(self):
        return self.variable_order

    def allocateTempScope(self, name):
        self.temp_scopes[name] = self.temp_scopes.get(name, 0) + 1

        return "%s_%d" % (
            name,
            self.temp_scopes[name]
        )

    def allocateTempVariable(self, temp_scope, name):
        if temp_scope is not None:
            full_name = "%s__%s" % (
                temp_scope,
                name
            )
        else:
            assert name != "result"

            full_name = name

        # No duplicates please.
        assert full_name not in self.temp_variables, full_name

        result = self.createTempVariable(
            temp_name = full_name
        )

        # Late added temp variables should be treated with care for the
        # remaining trace.
        if self.trace_collection is not None:
            self.trace_collection.initVariableUnknown(result).addUsage()

        return result

    def createTempVariable(self, temp_name):
        if temp_name in self.temp_variables:
            return self.temp_variables[ temp_name ]

        result = Variables.TempVariable(
            owner         = self,
            variable_name = temp_name
        )

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

    def removeTempVariable(self, variable):
        del self.temp_variables[variable.getName()]

    def allocatePreserverId(self):
        if python_version >= 300:
            self.preserver_id += 1

        return self.preserver_id


class ClosureTakerMixin(object):
    """ Mixin for nodes that accept variables from closure givers. """

    def __init__(self, provider):
        self.provider = provider

        self.taken = set()

    def getParentVariableProvider(self):
        return self.provider

    def getClosureVariable(self, variable_name):
        result = self.provider.getVariableForClosure(
            variable_name = variable_name
        )
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
                [
                    take
                    for take in
                    self.taken
                    if not take.isModuleVariable()
                ],
                key = lambda x : x.getName()
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
    """ Base class for all statements.

    """
    # Base classes can be abstract, pylint: disable=abstract-method

    # TODO: Have them all.
    # @abstractmethod
    def getStatementNiceName(self):
        # Virtual method, pylint: disable=no-self-use
        return "undescribed statement"

    def computeStatementSubExpressions(self, trace_collection):
        """ Compute a statement.

            Default behavior is to just visit the child expressions first, and
            then the node "computeStatement". For a few cases this needs to
            be overloaded.
        """
        expressions = self.getVisitableNodes()

        for count, expression in enumerate(expressions):
            assert expression.isExpression(), (self, expression)

            expression = trace_collection.onExpression(
                expression = expression
            )

            if expression.willRaiseException(BaseException):
                wrapped_expression = makeStatementOnlyNodesFromExpressions(
                    expressions[:count+1]
                )

                assert wrapped_expression is not None

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda : "For %s the child expression '%s' will raise." % (
                        self.getStatementNiceName(),
                        expression.getChildNameNice()
                    )
                )

        return self, None, None


class StatementChildrenHavingBase(ChildrenHavingMixin, StatementBase):
    def __init__(self, values, source_ref):
        StatementBase.__init__(self, source_ref = source_ref)

        ChildrenHavingMixin.__init__(
            self,
            values = values
        )


class StatementChildHavingBase(StatementBase):
    named_child = ""

    checker = None

    def __init__(self, value, source_ref):
        StatementBase.__init__(self, source_ref = source_ref)

        assert type(self.named_child) is str and self.named_child

        if self.checker is not None:
            value = self.checker(value)  # False alarm, pylint: disable=not-callable

        assert type(value) is not list, self.named_child

        if type(value) is tuple:
            assert None not in value, self.named_child

            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self
        elif value is None:
            pass
        else:
            assert False, type(value)

        attr_name = "subnode_" + self.named_child
        setattr(self, attr_name, value)

    def setChild(self, name, value):
        """ Set a child value.

            Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name == self.named_child, name

        # Lists as inputs are OK, but turn them into tuples.
        if type(value) is list:
            value = tuple(value)

        if self.checker is not None:
            value = self.checker(value)  # False alarm, pylint: disable=not-callable

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        attr_name = "subnode_" + name

        # Determine old value, and inform it about loosing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def getChild(self, name):
        # Only accept legal child names
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

    @staticmethod
    def childGetter(name):
        attr_name = "subnode_" + name

        def getter(self):
            return getattr(self, attr_name)

        return getter

    @staticmethod
    def childSetter(name):
        def setter(self, value):
            self.setChild(name, value)

        return setter

    def getVisitableNodes(self):
        # TODO: Consider if a generator would be faster.
        attr_name = "subnode_" + self.named_child
        value = getattr(self, attr_name)

        if value is None:
            return ()
        elif type(value) is tuple:
            return value
        elif isinstance(value, NodeBase):
            return (value,)
        else:
            raise AssertionError(
                self,
                "has illegal child", value, value.__class__
            )

    def getVisitableNodesNamed(self):
        """ Named children dictionary.

            For use in debugging and XML output.
        """
        attr_name = "subnode_" + self.named_child
        value = getattr(self, attr_name)

        yield self.named_child, value

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )

        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.
        key = self.named_child
        value = self.getChild(key)

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.setChild(
                        key,
                        tuple(
                            (val if val is not old_node else new_node)
                            for val in
                            value
                        )
                    )
                else:
                    self.setChild(
                        key,
                        tuple(
                            val
                            for val in
                            value
                            if val is not old_node
                        )
                    )

                return key
        elif isinstance(value, NodeBase):
            if old_node is value:
                self.setChild(key, new_node)

                return key
        else:
            assert False, (key, value, value.__class__)

        raise AssertionError(
            "Didn't find child",
            old_node,
            "in",
            self
        )

    def getCloneArgs(self):
        # Make clones of child nodes too.
        values = {}
        key = self.named_child

        value = self.getChild(key)

        assert type(value) is not list, key

        if value is None:
            values[key] = None
        elif type(value) is tuple:
            values[key] = tuple(
                v.makeClone()
                for v in
                value
            )
        else:
            values[key] = value.makeClone()

        values.update(
            self.getDetails()
        )

        return values

    def finalize(self):
        del self.parent

        for c in self.getVisitableNodes():
            c.finalize()


class SideEffectsFromChildrenMixin(object):
    def mayHaveSideEffects(self):
        for child in self.getVisitableNodes():
            if child.mayHaveSideEffects():
                return True
        return False

    def extractSideEffects(self):
        # No side effects at all but from the children.

        result = []

        for child in self.getVisitableNodes():
            result.extend(
                child.extractSideEffects()
            )

        return tuple(result)


def makeChild(provider, child, source_ref):
    child_type = child.attrib.get("type")

    if child_type == "list":
        return [
            fromXML(
                provider   = provider,
                xml        = sub_child,
                source_ref = source_ref
            )
            for sub_child in
            child
        ]
    elif child_type == "none":
        return None
    else:
        return fromXML(
            provider   = provider,
            xml        = child[0],
            source_ref = source_ref
        )


def getNodeClassFromKind(kind):
    return NodeCheckMetaClass.kinds[kind]


def extractKindAndArgsFromXML(xml, source_ref):
    kind = xml.attrib["kind"]

    args = dict(xml.attrib)
    del args["kind"]

    if source_ref is None:
        source_ref = SourceCodeReference.fromFilenameAndLine(
            args["filename"],
            int(args["line"])
        )

        del args["filename"]
        del args["line"]

    else:
        source_ref = source_ref.atLineNumber(int(args["line"]))
        del args["line"]

    node_class = getNodeClassFromKind(kind)

    return kind, node_class, args, source_ref


def fromXML(provider, xml, source_ref = None):
    assert xml.tag == "node", xml

    kind, node_class, args, source_ref = extractKindAndArgsFromXML(xml, source_ref)

    if "constant" in args:
        # TODO: Try and reduce/avoid this, use marshal and/or pickle from a file
        # global stream     instead. For now, this will do. pylint: disable=eval-used
        args["constant"] = eval(args["constant"])

    if kind in ("ExpressionFunctionBody", "PythonMainModule",
                "PythonCompiledModule", "PythonCompiledPackage",
                "PythonInternalModule"):
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
        return node_class.fromXML(
            provider   = provider,
            source_ref = source_ref,
            **args
        )
    except (TypeError, AttributeError):
        Tracing.printLine(node_class, args, source_ref)
        raise
