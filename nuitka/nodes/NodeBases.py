#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

These classes provide the generic base classes available for nodes.

"""


from nuitka import Options, Tracing, TreeXML, Variables
from nuitka.__past__ import iterItems
from nuitka.odict import OrderedDict
from nuitka.oset import OrderedSet
from nuitka.VariableRegistry import addVariableUsage


class NodeCheckMetaClass(type):
    kinds = set()

    def __new__(cls, name, bases, dictionary):
        # This is in conflict with either PyDev or Pylint, pylint: disable=C0204
        assert len(bases) == len(set(bases))

        return type.__new__(cls, name, bases, dictionary)

    def __init__(cls, name, bases, dictionary):
        if not name.endswith("Base"):
            assert ("kind" in dictionary), name
            kind = dictionary["kind"]

            assert type(kind) is str, name
            assert kind not in NodeCheckMetaClass.kinds, name

            NodeCheckMetaClass.kinds.add(kind)

            def convert(value):
                if value in ("AND", "OR", "NOT"):
                    return value
                else:
                    return value.title()

            kind_to_name_part = "".join(
                [convert(x) for x in kind.split('_')]
            )
            assert name.endswith(kind_to_name_part), \
              (name, kind_to_name_part)

            # Automatically add checker methods for everything to the common
            # base class
            checker_method = "is" + kind_to_name_part

            def checkKind(self):
                return self.kind == kind

            if not hasattr(NodeBase, checker_method):
                setattr(NodeBase, checker_method, checkKind)

        type.__init__(cls, name, bases, dictionary)

# For every node type, there is a test, and then some more members,

# For Python2/3 compatible source, we create a base class that has the metaclass
# used and doesn't require making a choice.
NodeMetaClassBase = NodeCheckMetaClass("NodeMetaClassBase", (object,), {})

class NodeBase(NodeMetaClassBase):
    kind = None

    def __init__(self, source_ref):
        # The base class has no __init__ worth calling.

        # Check source reference to meet basic standards, so we note errors
        # when they occur.
        assert source_ref is not None
        assert source_ref.line is not None

        self.parent = None

        self.source_ref = source_ref

    def __repr__(self):
        # This is to avoid crashes, because of bugs in detail.
        # pylint: disable=W0703
        try:
            detail = self.getDetail()
        except Exception as e:
            detail = "detail raises exception %s" % e

        if not detail:
            return "<Node %s>" % self.getDescription()
        else:
            return "<Node %s %s>" % (self.getDescription(), detail)

    def getDescription(self):
        """ Description of the node, intented for use in __repr__ and
            graphical display.

        """
        return "%s at %s" % (self.kind, self.source_ref.getAsString())

    def getDetails(self):
        """ Details of the node, intended for use in __repr__ and dumps.

        """
        # Virtual method, pylint: disable=R0201
        return {}

    def getDetail(self):
        """ Details of the node, intended for use in __repr__ and graphical
            display.

        """
        return str(self.getDetails())[1:-1]

    def getParent(self):
        """ Parent of the node. Every node except modules have to have a parent.

        """

        if self.parent is None and not self.isPythonModule():
            assert False, (self,  self.source_ref)

        return self.parent

    def getParents(self):
        """ Parents of the node. Up to module level.

        """
        result = []
        current = self

        while True:
            current = current.getParent()

            result.append(current)

            if current.isPythonModule() or current.isExpressionFunctionBody():
                break

        assert None not in result, self

        result.reverse()
        return result

    def getChildName(self):
        """ Return the role in the current parent, subject to changes.

        """
        parent = self.getParent()

        for key, value in parent.child_values.items():
            if self is value:
                return key

        # TODO: Not checking tuples yet
        return None

    def getParentFunction(self):
        """ Return the parent that is a function.

        """

        parent = self.getParent()

        while parent is not None and not parent.isExpressionFunctionBody():
            parent = parent.getParent()

        return parent

    def getParentModule(self):
        """ Return the parent that is module.

        """
        parent = self

        while not parent.isPythonModule():
            if hasattr(parent, "provider"):
                # After we checked, we can use it, will be much faster route
                # to take.
                parent = parent.provider
            else:
                parent = parent.getParent()

        return parent

    def isParentVariableProvider(self):
        # Check if it's a closure giver, in which cases it can provide variables,
        return isinstance(self, ClosureGiverNodeBase)

    def getParentVariableProvider(self):
        parent = self.getParent()

        while not parent.isParentVariableProvider():
            parent = parent.getParent()

        return parent

    def getParentStatementsFrame(self):
        current = self.getParent()

        while True:
            if current.isStatementsFrame():
                return current

            if current.isParentVariableProvider():
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

        for key, value in iterItems(self.getDetails()):
            value = str(value)

            if value.startswith('<') and value.endswith('>'):
                value = value[1:-1]

            result.set(key, str(value))

        for name, children in self.getVisitableNodesNamed():
            if type(children) not in (list, tuple):
                children = (children,)

            role = TreeXML.Element(
                "role",
                name = name
            )

            result.append(role)

            for child in children:
                if child is not None:
                    role.append(
                        child.asXml()
                    )

        return result

    def dump(self, level = 0):
        Tracing.printIndented(level, self)
        Tracing.printSeparator(level)

        for visitable in self.getVisitableNodes():
            visitable.dump(level + 1)

        Tracing.printSeparator(level)

    @staticmethod
    def isPythonModule():
        # For overload by module nodes
        return False

    def isExpression(self):
        return self.kind.startswith("EXPRESSION_")

    def isStatement(self):
        return self.kind.startswith("STATEMENT_")

    def isExpressionBuiltin(self):
        return self.kind.startswith("EXPRESSION_BUILTIN_")

    def isOperation(self):
        return self.kind.startswith("EXPRESSION_OPERATION_")

    def isStatementReraiseException(self):
        # Virtual method, pylint: disable=R0201
        return False

    def isExpressionMakeSequence(self):
        # Virtual method, pylint: disable=R0201
        return False

    def isIteratorMaking(self):
        # Virtual method, pylint: disable=R0201
        return False

    def isNumberConstant(self):
        # Virtual method, pylint: disable=R0201
        return False

    def isExpressionCall(self):
        # Virtual method, pylint: disable=R0201
        return False

    def visit(self, context, visitor):
        visitor(self)

        for visitable in self.getVisitableNodes():
            visitable.visit(context, visitor)

    def getVisitableNodes(self):
        # Virtual method, pylint: disable=R0201
        return ()

    def getVisitableNodesNamed(self):
        # Virtual method, pylint: disable=R0201
        return ()

    def replaceWith(self, new_node):
        self.parent.replaceChild(
            old_node = self,
            new_node = new_node
        )

    def getName(self):
        # Virtual method, pylint: disable=R0201
        return None

    def mayHaveSideEffects(self):
        """ Unless we are told otherwise, everything may have a side effect. """
        # Virtual method, pylint: disable=R0201

        return True

    def isOrderRelevant(self):
        return self.mayHaveSideEffects()

    def mayHaveSideEffectsBool(self):
        """ Unless we are told otherwise, everything may have a side effect. """
        # Virtual method, pylint: disable=R0201

        return True

    def extractSideEffects(self):
        """ Unless defined otherwise, the expression is the side effect. """

        return (self,)

    def mayRaiseException(self, exception_type):
        """ Unless we are told otherwise, everything may raise everything. """
        # Virtual method, pylint: disable=R0201,W0613

        return True

    def mayRaiseExceptionBool(self, exception_type):
        """ Unless we are told otherwise, everything may raise being checked. """
        # Virtual method, pylint: disable=R0201,W0613

        return True

    def mayReturn(self):
        return "_RETURN" in self.kind

    def mayBreak(self):
        # For overload, pylint: disable=R0201
        return False

    def mayContinue(self):
        # For overload, pylint: disable=R0201
        return False

    def needsFrame(self):
        """ Unless we are tolder otherwise, this depends on exception raise. """

        return self.mayRaiseException(BaseException)

    def willRaiseException(self, exception_type):
        """ Unless we are told otherwise, nothing may raise anything. """
        # Virtual method, pylint: disable=R0201,W0613

        return False


    def isIndexable(self):
        """ Unless we are told otherwise, it's not indexable. """
        # Virtual method, pylint: disable=R0201

        return False

    def isStatementAborting(self):
        """ Is the node aborting, control flow doesn't continue after this node.  """
        assert self.isStatement(), self.kind

        return False

    def needsLocalsDict(self):
        """ Node requires a locals dictionary by provider. """

        # Virtual method, pylint: disable=R0201
        return False

    def getIntegerValue(self):
        """ Node as integer value, if possible."""
        # Virtual method, pylint: disable=R0201
        return None


class CodeNodeBase(NodeBase):
    def __init__(self, name, code_prefix, source_ref):
        assert name is not None

        NodeBase.__init__(self, source_ref = source_ref)

        self.name = name
        self.code_prefix = code_prefix

        # The code name is determined on demand only.
        self.code_name = None

        # The "UID" values of children kinds are kept here.
        self.uids = {}

    def getName(self):
        return self.name

    def getFullName(self):
        result = self.getName()

        current = self

        while True:
            current = current.getParent()

            if current is None:
                break

            name = current.getName()

            if name is not None:
                result = "%s__%s" % (name, result)

        assert '<' not in result, result

        return result

    def getCodeName(self):
        if self.code_name is None:
            provider = self.getParentVariableProvider()
            parent_name = provider.getCodeName()

            uid = "_%d" % provider.getChildUID(self)

            assert isinstance(self, CodeNodeBase)

            if self.name:
                name = uid + '_' + self.name
            else:
                name = uid

            self.code_name = "%s%s_of_%s" % (self.code_prefix, name, parent_name)

        return self.code_name

    def getChildUID(self, node):
        if node.kind not in self.uids:
            self.uids[ node.kind ] = 0

        self.uids[ node.kind ] += 1

        return self.uids[ node.kind ]


class ChildrenHavingMixin:
    named_children = ()

    checkers = {}

    def __init__(self, values):
        assert type(self.named_children) is tuple and len(self.named_children)

        # Check for completeness of given values, everything should be there
        # but of course, might be put to None.
        assert set(values.keys()) == set(self.named_children)

        self.child_values = dict(values)

        for key, value in self.child_values.items():
            if key in self.checkers:
                value = self.child_values[key] = self.checkers[key](value)

            assert type(value) is not list, key

            if type(value) is tuple:
                assert None not in value, key

                for val in value:
                    val.parent = self
            elif value is not None:
                value.parent = self
            elif value is None:
                pass
            else:
                assert False, type(value)

    def setChild(self, name, value):
        """ Set a child value.

            Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name in self.child_values, name

        # Lists as inputs are OK, but turn them into tuples.
        if type(value) is list:
            value = tuple(value)

        if name in self.checkers:
            value = self.checkers[name](value)

        # Reparent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about loosing its parent.
        old_value = self.child_values[name]

        assert old_value is not value, value

        self.child_values[name] = value

    def getChild(self, name):
        # Only accept legal child names
        assert name in self.child_values, name

        return self.child_values[name]

    def hasChild(self, name):
        return name in self.child_values

    @staticmethod
    def childGetter(name):
        def getter(self):
            return self.getChild(name)

        return getter

    @staticmethod
    def childSetter(name):
        def setter(self, value):
            self.setChild(name, value)

        return setter

    def getVisitableNodes(self):
        result = []

        for name in self.named_children:
            value = self.child_values[ name ]

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
        result = []

        for name in self.named_children:
            value = self.child_values[ name ]

            result.append((name, value))

        return result

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )

        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.
        for key, value in self.child_values.items():
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

    def makeCloneAt(self, source_ref):
        values = {}

        for key, value in self.child_values.items():
            assert type(value) is not list, key

            if value is None:
                values[key] = None
            elif type(value) is tuple:
                values[key] = tuple(
                    v.makeCloneAt(
                        source_ref = v.getSourceReference()
                    )
                    for v in
                    value
                )
            else:
                values[ key ] = value.makeCloneAt(
                    value.getSourceReference()
                )

        values.update(
            self.getDetails()
        )

        try:
            # Using star dictionary arguments here for generic use,
            # pylint: disable=W0142,E1123
            return self.__class__(
                source_ref = source_ref,
                **values
            )
        except TypeError:
            print("Problem cloning", self.__class__)

            raise


class ClosureGiverNodeBase(CodeNodeBase):
    """ Mixin for nodes that provide variables for closure takers. """
    def __init__(self, name, code_prefix, source_ref):
        CodeNodeBase.__init__(
            self,
            name        = name,
            code_prefix = code_prefix,
            source_ref  = source_ref
        )

        self.providing = OrderedDict()

        self.keeper_variables = OrderedSet()

        self.temp_variables = OrderedDict()

        self.temp_scopes = OrderedDict()

    def hasProvidedVariable(self, variable_name):
        return variable_name in self.providing

    def getProvidedVariable(self, variable_name):
        if variable_name not in self.providing:
            self.providing[variable_name] = self.createProvidedVariable(
                variable_name = variable_name
            )

        return self.providing[variable_name]

    def createProvidedVariable(self, variable_name):
        # Virtual method, pylint: disable=R0201
        assert type(variable_name) is str

        return None

    def registerProvidedVariables(self, *variables):
        for variable in variables:
            self.registerProvidedVariable(variable)

    def registerProvidedVariable(self, variable):
        assert variable is not None

        self.providing[variable.getName()] = variable

    def getProvidedVariables(self):
        return self.providing.values()

    def allocateTempScope(self, name, allow_closure = False):
        self.temp_scopes[name] = self.temp_scopes.get(name, 0) + 1

        # TODO: Instead of using overly long code name, could just visit parents
        # and make sure to allocate the scope at the top.
        if allow_closure:
            return "%s_%s_%d" % (
                self.getCodeName(),
                name,
                self.temp_scopes[name]
            )
        else:
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

        del name

        assert full_name not in self.temp_variables, full_name

        result = Variables.TempVariable(
            owner         = self,
            variable_name = full_name
        )

        self.temp_variables[full_name] = result

        addVariableUsage(result, self)

        return result

    def getTempVariable(self, temp_scope, name):
        if temp_scope is not None:
            full_name = "%s__%s" % (temp_scope, name)
        else:
            full_name = name

        return self.temp_variables[full_name]

    def getTempVariables(self):
        return tuple(self.temp_variables.values())

    def removeTempVariable(self, variable):
        del self.temp_variables[variable.getName()]


class ClosureTakerMixin:
    """ Mixin for nodes that accept variables from closure givers. """

    def __init__(self, provider, early_closure):
        assert provider.isParentVariableProvider(), provider

        self.provider = provider
        self.early_closure = early_closure

        self.taken = set()

        self.temp_variables = set()

    def getParentVariableProvider(self):
        return self.provider

    def getClosureVariable(self, variable_name):
        result = self.provider.getVariableForClosure(
            variable_name = variable_name
        )
        assert result is not None, variable_name

        # There is no maybe with closures. It means, it is closure variable in
        # this case.
        if result.isMaybeLocalVariable():
            result = result.getMaybeVariable()

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

    def isEarlyClosure(self):
        """ Early closure taking means immediate binding of references.

        Normally it's good to lookup name references immediately, but not for
        functions. In case of a function body it is not allowed to do that,
        because a later assignment needs to be queried first. Nodes need to
        indicate via this if they would like to resolve references at the same
        time as assignments.
        """

        return self.early_closure


class ExpressionMixin:
    def isCompileTimeConstant(self):
        """ Has a value that we can use at compile time.

            Yes or no. If it has such a value, simulations can be applied at
            compile time and e.g. operations or conditions, or even calls may
            be executed against it.
        """
        # Virtual method, pylint: disable=R0201
        return False

    def getCompileTimeConstant(self):
        assert self.isCompileTimeConstant(), self

        assert False

    def getTruthValue(self):
        """ Return known truth value. The "None" value indicates unknown. """

        if self.isCompileTimeConstant():
            return bool(self.getCompileTimeConstant())
        else:
            return None

    def mayBeNone(self):
        """ Could this evaluate to be "None".

            Yes or no. Defaults to pessimistic yes."""
        # For overload, pylint: disable=R0201

        return True

    def isKnownToBeIterable(self, count):
        """ Can be iterated at all (count is None) or exactly count times.

            Yes or no. If it can be iterated a known number of times, it may
            be asked to unpack itself.
        """

        # Virtual method, pylint: disable=R0201,W0613
        return False

    def isKnownToBeIterableAtMin(self, count):
        # Virtual method, pylint: disable=R0201,W0613
        return False

    def isKnownToBeIterableAtMax(self, count):
        # Virtual method, pylint: disable=R0201,W0613
        return False

    def getIterationLength(self):
        """ Value that "len" or "PyObject_Size" would give, if known.

            Otherwise it is "None" to indicate unknown.
        """

        # Virtual method, pylint: disable=R0201
        return None

    def getStringValue(self):
        """ Node as integer value, if possible."""
        # Virtual method, pylint: disable=R0201
        return None

    def getStrValue(self):
        """ Value that "str" or "PyObject_Str" would give, if known.

            Otherwise it is "None" to indicate unknown. Users must not
            forget to take side effects into account, when replacing a
            node with its string value.
        """
        string_value = self.getStringValue()

        if string_value is not None:
            from .NodeMakingHelpers import makeConstantReplacementNode

            return makeConstantReplacementNode(
                node     = self,
                constant = string_value
            )

        return None

    def isKnownToBeHashable(self):
        """ Is the value hashable, i.e. suitable for dictionary/set keying."""

        # Virtual method, pylint: disable=R0201
        # Unknown by default.
        return None

    def onRelease(self, constraint_collection):
        # print "onRelease", self
        pass

    def computeExpressionRaw(self, constraint_collection):
        """ Compute an expression.

            Default behavior is to just visit the child expressions first, and
            then the node "computeExpression". For a few cases this needs to
            be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before.
        sub_expressions = self.getVisitableNodes()

        for sub_expression in sub_expressions:
            constraint_collection.onExpression(
                expression = sub_expression
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(
            constraint_collection = constraint_collection
        )

    def computeExpressionAttribute(self, lookup_node, attribute_name,
                                    constraint_collection):
        # By default, an attribute lookup may change everything about the lookup
        # source. Virtual method, pylint: disable=R0201,W0613
        constraint_collection.removeKnowledge(lookup_node)

        return lookup_node, None, None

    def computeExpressionSubscript(self, lookup_node, subscript,
                                   constraint_collection):
        # By default, an subscript may change everything about the lookup
        # source.
        constraint_collection.removeKnowledge(lookup_node)
        constraint_collection.removeKnowledge(subscript)

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(self)

        return lookup_node, None, None

    def computeExpressionSlice(self, lookup_node, lower, upper,
                               constraint_collection):
        # By default, a slicing may change everything about the lookup source.
        # Virtual method, pylint: disable=R0201,W0613
        constraint_collection.removeKnowledge(lookup_node)

        return lookup_node, None, None

    def computeExpressionCall(self, call_node, constraint_collection):
        # Virtual method, pylint: disable=R0201
        call_node.getCalled().onContentEscapes(constraint_collection)

        return call_node, None, None

    def computeExpressionIter1(self, iter_node, constraint_collection):
        # Virtual method, pylint: disable=R0201
        iter_node.getValue().onContentEscapes(constraint_collection)

        return iter_node, None, None

    def computeExpressionOperationNot(self, not_node, constraint_collection):
        # Virtual method, pylint: disable=R0201

        # The value of that node escapes and could change its contents.
        constraint_collection.removeKnowledge(not_node)

        # Any code could be run, note that.
        constraint_collection.onControlFlowEscape(not_node)

        return not_node, None, None

    def computeExpressionDrop(self, statement, constraint_collection):
        if not self.mayHaveSideEffects():
            return None, "new_statements", "Removed statement without effect."

        return statement, None, None

    def onContentEscapes(self, constraint_collection):
        pass



class CompileTimeConstantExpressionMixin(ExpressionMixin):
    # TODO: Do this for all computations, do this in the base class of all
    # nodes.
    computed_attribute = False

    def __init__(self):
        pass

    def isCompileTimeConstant(self):
        """ Has a value that we can use at compile time.

            Yes or no. If it has such a value, simulations can be applied at
            compile time and e.g. operations or conditions, or even calls may
            be executed against it.
        """
        return True

    def mayHaveSideEffects(self):
        # Virtual method, pylint: disable=R0201
        return False

    def mayHaveSideEffectsBool(self):
        # Virtual method, pylint: disable=R0201
        return False

    def mayBeNone(self):
        return self.getCompileTimeConstant() is None

    def computeExpressionOperationNot(self, not_node, constraint_collection):
        from .NodeMakingHelpers import getComputationResult

        return getComputationResult(
            node        = not_node,
            computation = lambda : not self.getCompileTimeConstant(),
            description = """\
Compile time constant negation truth value pre-computed."""
        )


    def computeExpressionAttribute(self, lookup_node, attribute_name, constraint_collection):
        if self.computed_attribute:
            return lookup_node, None, None

        value = self.getCompileTimeConstant()

        from .NodeMakingHelpers import getComputationResult, isCompileTimeConstantValue

        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if not hasattr(value, attribute_name) or \
           isCompileTimeConstantValue(getattr(value, attribute_name)):

            return getComputationResult(
                node        = lookup_node,
                computation = lambda : getattr(value, attribute_name),
                description = "Attribute lookup to '%s' pre-computed." % (
                    attribute_name
                )
            )

        self.computed_attribute = True

        return lookup_node, None, None

    def computeExpressionSubscript(self, lookup_node, subscript, constraint_collection):
        from .NodeMakingHelpers import getComputationResult

        if subscript.isCompileTimeConstant():
            return getComputationResult(
                node        = lookup_node,
                computation = lambda : self.getCompileTimeConstant()[ subscript.getCompileTimeConstant() ],
                description = "Subscript of constant with constant value."
            )

        # TODO: Look-up of subscript to index may happen.

        return lookup_node, None, None

    def computeExpressionSlice(self, lookup_node, lower, upper, constraint_collection):
        from .NodeMakingHelpers import getComputationResult

        # TODO: Could be happy with predictable index values and not require
        # constants.
        if lower is not None:
            if upper is not None:
                if lower.isCompileTimeConstant() and upper.isCompileTimeConstant():

                    return getComputationResult(
                        node        = lookup_node,
                        computation = lambda : self.getCompileTimeConstant()[
                            lower.getCompileTimeConstant() : upper.getCompileTimeConstant()
                        ],
                        description = """\
Slicing of constant with constant indexes."""
                    )
            else:
                if lower.isCompileTimeConstant():
                    return getComputationResult(
                        node        = lookup_node,
                        computation = lambda : self.getCompileTimeConstant()[
                            lower.getCompileTimeConstant() :
                        ],
                        description = """\
Slicing of constant with constant lower index only."""
                    )
        else:
            if upper is not None:
                if upper.isCompileTimeConstant():
                    return getComputationResult(
                        node        = lookup_node,
                        computation = lambda : self.getCompileTimeConstant()[
                            : upper.getCompileTimeConstant()
                        ],
                        description = """\
Slicing of constant with constant upper index only."""
                    )
            else:
                return getComputationResult(
                    node        = lookup_node,
                    computation = lambda : self.getCompileTimeConstant()[ : ],
                    description = "Slicing of constant with no indexes."
                )

        return lookup_node, None, None


class ExpressionSpecBasedComputationMixin(ExpressionMixin):
    builtin_spec = None

    def computeBuiltinSpec(self, given_values):
        assert self.builtin_spec is not None, self

        for value in given_values:
            if value is not None and not value.isCompileTimeConstant():
                return self, None, None

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            return self, None, None

        from .NodeMakingHelpers import getComputationResult

        return getComputationResult(
            node        = self,
            computation = lambda : self.builtin_spec.simulateCall(given_values),
            description = "Built-in call to '%s' pre-computed." % (
                self.builtin_spec.getName()
            )
        )


class ExpressionChildrenHavingBase(ChildrenHavingMixin, NodeBase,
                                   ExpressionMixin):
    def __init__(self, values, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        ChildrenHavingMixin.__init__(
            self,
            values = values
        )

class StatementChildrenHavingBase(ChildrenHavingMixin, NodeBase):
    def __init__(self, values, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)

        ChildrenHavingMixin.__init__(
            self,
            values = values
        )


class ExpressionBuiltinNoArgBase(NodeBase, ExpressionMixin):
    def __init__(self, builtin_function, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.builtin_function = builtin_function

    def computeExpression(self, constraint_collection):
        from .NodeMakingHelpers import getComputationResult

        # The lambda is there for make sure that no argument parsing will reach
        # the built-in function at all, pylint: disable=W0108
        return getComputationResult(
            node        = self,
            computation = lambda : self.builtin_function(),
            description = "No arg %s built-in" % self.builtin_function.__name__
        )


class ExpressionBuiltinSingleArgBase(ExpressionChildrenHavingBase,
                                     ExpressionSpecBasedComputationMixin):
    named_children = (
        "value",
    )

    def __init__(self, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "value" : value,
            },
            source_ref = source_ref
        )

    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def computeExpression(self, constraint_collection):
        value = self.getValue()

        assert self.builtin_spec is not None, self

        if value is None:
            return self.computeBuiltinSpec(
                given_values = ()
            )
        else:
            if value.willRaiseException(BaseException):
                return value, "new_raise", """\
Built-in call raises exception while building argument."""

            return self.computeBuiltinSpec(
                given_values = (value,)
            )


class SideEffectsFromChildrenMixin:
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


# TODO: Maybe this should be in a "Checkers" module
def checkStatementsSequenceOrNone(value):
    assert value is None or value.kind == "STATEMENTS_SEQUENCE"

    return value
