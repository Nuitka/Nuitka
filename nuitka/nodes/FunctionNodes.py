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
""" Nodes for functions and their creations.

Lambdas are functions too. The functions are at the core of the language and
have their complexities.

Creating a CPython function object is an optional thing. Some things might
only be used to be called directly, while knowing exactly what it is. So
the "ExpressionFunctionCreation" might be used to provide that kind of
CPython reference, and may escape.


"""

from nuitka import Utils, Variables
from nuitka.__past__ import iterItems

from .IndicatorMixins import (
    MarkGeneratorIndicator,
    MarkLocalsDictIndicator,
    MarkUnoptimizedFunctionIndicator
)
from .NodeBases import (
    ChildrenHavingMixin,
    ClosureGiverNodeBase,
    ClosureTakerMixin,
    CompileTimeConstantExpressionMixin,
    ExpressionChildrenHavingBase,
    ExpressionMixin,
    NodeBase,
    SideEffectsFromChildrenMixin
)
from .ParameterSpecs import TooManyArguments, matchCall


class ExpressionFunctionBody(ClosureTakerMixin, ChildrenHavingMixin,
                             ClosureGiverNodeBase, ExpressionMixin,
                             MarkGeneratorIndicator,
                             MarkLocalsDictIndicator,
                             MarkUnoptimizedFunctionIndicator):
    # We really want these many ancestors, as per design, we add properties via
    # base class mix-ins a lot, leading to many instance attributes, and
    # methods, pylint: disable=R0901,R0902

    kind = "EXPRESSION_FUNCTION_BODY"

    named_children = (
        "body",
    )

    if Utils.python_version >= 340:
        qualname_setup = None

    def __init__(self, provider, name, doc, parameters, source_ref,
                 is_class = False):
        # Register ourselves immediately with the module.
        provider.getParentModule().addFunction(self)

        if is_class:
            code_prefix = "class"
        else:
            code_prefix = "function"

        if name == "<lambda>":
            name = "lambda"
            code_prefix = name

            self.is_lambda = True
        else:
            self.is_lambda = False

        if name == "<listcontraction>":
            assert Utils.python_version >= 300

            code_prefix = "listcontr"
            name = ""

            self.local_locals = Utils.python_version >= 300
        else:
            self.local_locals = True

        if name == "<setcontraction>":
            code_prefix = "setcontr"
            name = ""

        if name == "<dictcontraction>":
            code_prefix = "dictcontr"
            name = ""

        if name == "<genexpr>":
            code_prefix = "genexpr"
            name = ""

            self.is_genexpr = True
        else:
            self.is_genexpr = False

        self.non_local_declarations = []

        ClosureTakerMixin.__init__(
            self,
            provider      = provider,
            early_closure = is_class
        )

        ClosureGiverNodeBase.__init__(
            self,
            name        = name,
            code_prefix = code_prefix,
            source_ref  = source_ref
        )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "body" : None # delayed
            }
        )


        MarkGeneratorIndicator.__init__(self)

        MarkLocalsDictIndicator.__init__(self)

        MarkUnoptimizedFunctionIndicator.__init__(self)

        self.is_class = is_class
        self.doc = doc

        # Indicator, if this is a function that uses "super", because if it
        # does, it would like to get the final "__class__" attached.
        self.has_super = False

        # Indicator if the return value exception might be required.
        self.return_exception = False

        # Indicator if the function needs to be created as a function object.
        self.needs_creation = False

        # Indicator if the function is called directly.
        self.needs_direct = False

        # Indicator if the function is used outside of where it's defined.
        self.cross_module_use = False

        # Python3.4: Might be overridden by global statement on the class name.
        if Utils.python_version >= 340:
            self.qualname_provider = provider

        self.parameters = parameters
        self.parameters.setOwner(self)

        self.registerProvidedVariables(
            *self.parameters.getVariables()
        )


    def getDetails(self):
        return {
            "name"       : self.getFunctionName(),
            "ref_name"   : self.getCodeName(),
            "parameters" : self.getParameters(),
            "provider"   : self.provider.getCodeName(),
            "doc"        : self.doc
        }

    def getDetail(self):
        return "named %s with %s" % (self.name, self.parameters)

    def getParent(self):
        assert False

    def isClassDictCreation(self):
        return self.is_class

    def getContainingClassDictCreation(self):
        current = self

        while not current.isPythonModule():
            if current.isClassDictCreation():
                return current

            current = current.getParentVariableProvider()

        return None

    def getFunctionName(self):
        if self.is_lambda:
            return "<lambda>"
        elif self.is_genexpr:
            return "<genexpr>"
        else:
            return self.name

    def getFunctionQualname(self):
        """ Function __qualname__ new in CPython3.3

        Should contain some kind of full name descriptions for the closure to
        recognize and will be used for outputs.
        """

        function_name = self.getFunctionName()

        if Utils.python_version < 340:
            provider = self.getParentVariableProvider()
        else:
            provider = self.qualname_provider

        if provider.isPythonModule():
            return function_name
        elif provider.isClassDictCreation():
            return provider.getFunctionQualname() + '.' + function_name
        else:
            return provider.getFunctionQualname() + ".<locals>." + function_name

    def getDoc(self):
        return self.doc

    def getParameters(self):
        return self.parameters

    def getLocalVariableNames(self):
        return Variables.getNames(self.getLocalVariables())

    def getLocalVariables(self):
        return [
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable()
        ]

    def getUserLocalVariables(self):
        return tuple(
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable() and not variable.isParameterVariable()
            if variable.getOwner() is self
        )

    def getVariables(self):
        return self.providing.values()

    def removeVariable(self, variable):
        assert variable in self.providing.values(), (self.providing, variable)

        del self.providing[variable.getName()]

        assert not variable.isParameterVariable() or \
               not variable.getOwner() is self

        self.taken.remove(variable)

    def getVariableForAssignment(self, variable_name):
        # print ("ASS func", self, variable_name)

        if self.hasTakenVariable(variable_name):
            result = self.getTakenVariable(variable_name)
        else:
            result = self.getProvidedVariable(variable_name)

        return result

    def getVariableForReference(self, variable_name):
        # print ( "REF func", self, variable_name )

        if self.hasProvidedVariable(variable_name):
            result = self.getProvidedVariable(variable_name)
        else:
            result = self.getClosureVariable(
                variable_name = variable_name
            )

            # Remember that we need that closure variable for something, so
            # we don't redo it all the time.
            if not result.isModuleVariable():
                self.registerProvidedVariable(result)

            # For exec containing/star import containing, get a closure variable
            # and if it is a module variable, only then make it a maybe local
            # variable.
            if self.isUnoptimized() and result.isModuleVariable():
                result = Variables.MaybeLocalVariable(
                    owner          = self,
                    maybe_variable = result
                )

                self.registerProvidedVariable(result)

        return result

    def getVariableForClosure(self, variable_name):
        # print( "getVariableForClosure", self, variable_name )

        # The class bodies provide no closure, except under CPython3.x, there
        # they provide "__class__" but nothing else.

        if self.isClassDictCreation():
            if variable_name == "__class__":
                if Utils.python_version < 300:
                    return self.provider.getVariableForClosure(
                        variable_name
                    )
                elif Utils.python_version >= 340 and False: # TODO: Temporarily reverted
                    result = self.getTempVariable(
                        temp_scope = None,
                        name       = "__class__"
                    )

                    return result
            else:
                return self.provider.getVariableForClosure(
                    variable_name
                )

        if self.hasProvidedVariable(variable_name):
            return self.getProvidedVariable(variable_name)
        else:
            return self.provider.getVariableForClosure(variable_name)

    def createProvidedVariable(self, variable_name):
        # print("createProvidedVariable", self, variable_name)

        if self.local_locals:
            return Variables.LocalVariable(
                owner         = self,
                variable_name = variable_name
            )
        else:
            # Make sure the provider knows it has to provide a variable of this
            # name for the assignment.
            self.provider.getVariableForAssignment(
                variable_name = variable_name
            )

            return self.getClosureVariable(
                variable_name = variable_name
            )

    def addNonlocalsDeclaration(self, names, source_ref):
        self.non_local_declarations.append(
            (names, source_ref)
        )

    def getNonlocalDeclarations(self):
        return self.non_local_declarations

    getBody = ChildrenHavingMixin.childGetter("body")
    setBody = ChildrenHavingMixin.childSetter("body")

    def needsCreation(self):
        # TODO: This looks kind of arbitrary, the users should decide, if they
        # need it.
        return self.needs_creation

    def markAsNeedsCreation(self):
        self.needs_creation = True

    def needsDirectCall(self):
        return self.needs_direct

    def markAsDirectlyCalled(self):
        self.needs_direct = True

    def isCrossModuleUsed(self):
        return self.cross_module_use

    def markAsCrossModuleUsed(self):
        self.cross_module_use = True

    def computeExpression(self, constraint_collection):
        assert False

        # Function body is quite irreplaceable.
        return self, None, None

    def getLocalsMode(self):
        if Utils.python_version >= 300:
            return "updated"
        elif self.isEarlyClosure() or self.isUnoptimized():
            return "updated"
        else:
            return "copy"

    def computeExpressionCall(self, call_node, constraint_collection):
        # TODO: Until we have something to re-order the arguments, we need to
        # skip this. For the immediate need, we avoid this complexity, as a
        # re-ordering will be needed.

        assert False, self

    def isCompileTimeConstant(self):
        # TODO: It's actually pretty much compile time accessible maybe.
        return None

    def mayHaveSideEffects(self):
        # The function definition has no side effects, calculating the defaults
        # would be, but that is done outside of this.
        return False

    def mayRaiseException(self, exception_type):
        return self.getBody().mayRaiseException(exception_type)

    def markAsClassClosureTaker(self):
        self.has_super = True

    def isClassClosureTaker(self):
        return self.has_super

    def makeCloneAt(self, source_ref):
        result = self.__class__(
            provider   = self.provider,
            name       = self.name,
            doc        = self.name,
            # TODO: Clone parameters too, when we start to mutate them.
            parameters = self.parameters,
            source_ref =  source_ref
        )

        result.setBody(
            self.getBody().makeCloneAt(source_ref)
        )

        return result

    def markAsExceptionReturnValue(self):
        self.return_exception = True

    def needsExceptionReturnValue(self):
        return self.return_exception


def convertNoneConstantOrEmptyDictToNone(node):
    if node is None:
        return None
    elif node.isExpressionConstantRef() and node.getConstant() is None:
        return None
    elif node.isExpressionConstantRef() and node.getConstant() == {}:
        return None
    else:
        return node

# TODO: Function direct call node ought to be here too.

class ExpressionFunctionCreation(SideEffectsFromChildrenMixin,
                                 ExpressionChildrenHavingBase):

    kind = "EXPRESSION_FUNCTION_CREATION"

    # Note: The order of evaluation for these is a bit unexpected, but
    # true. Keyword defaults go first, then normal defaults, and annotations of
    # all kinds go last.

    # A bug of CPython3.x not fixed before version 3.4, see bugs.python.org/issue16967
    kw_defaults_before_defaults = Utils.python_version < 340

    if kw_defaults_before_defaults:
        named_children = (
            "kw_defaults", "defaults", "annotations", "function_ref"
        )
    else:
        named_children = (
            "defaults", "kw_defaults", "annotations", "function_ref"
        )

    checkers   = {
        "kw_defaults" : convertNoneConstantOrEmptyDictToNone,
    }

    def __init__(self, function_ref, defaults, kw_defaults, annotations,
                 source_ref):
        assert kw_defaults is None or kw_defaults.isExpression()
        assert annotations is None or annotations.isExpression()
        assert function_ref.isExpressionFunctionRef()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "function_ref" : function_ref,
                "defaults"     : tuple(defaults),
                "kw_defaults"  : kw_defaults,
                "annotations"  : annotations
            },
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        # TODO: Function body may know something, creation of defaults may
        # raise, etc.
        return self, None, None

    getFunctionRef = ExpressionChildrenHavingBase.childGetter("function_ref")
    getDefaults = ExpressionChildrenHavingBase.childGetter("defaults")
    getKwDefaults = ExpressionChildrenHavingBase.childGetter("kw_defaults")
    getAnnotations = ExpressionChildrenHavingBase.childGetter("annotations")

    def mayRaiseException(self, exception_type):
        return True

    def computeExpressionCall(self, call_node, constraint_collection):
        call_kw = call_node.getCallKw()

        # TODO: Until we have something to re-order the arguments, we need to
        # skip this. For the immediate need, we avoid this complexity, as a
        # re-ordering will be needed.
        if call_kw:
            return call_node, None, None

        # TODO: Actually the above disables it entirely, as it is at least
        # the empty dictionary node in any case. We will need some enhanced
        # interfaces for "matchCall" to work on.

        call_spec = self.getFunctionRef().getFunctionBody().getParameters()

        try:
            args_dict = matchCall(
                func_name     = self.getName(),
                args          = call_spec.getArgumentNames(),
                star_list_arg = call_spec.getStarListArgumentName(),
                star_dict_arg = call_spec.getStarDictArgumentName(),
                num_defaults  = call_spec.getDefaultCount(),
                positional    = call_node.getCallArgsTuple(),
                pairs         = ()
            )

            values = []

            for positional_arg in call_node.getCallArgs():
                for _arg_name, arg_value in iterItems(args_dict):
                    if arg_value is positional_arg:
                        values.append(arg_value)

            result = ExpressionFunctionCall(
                function   = self,
                values     = values,
                source_ref = call_node.getSourceReference()
            )

            return (
                result,
                "new_statements", # TODO: More appropriate tag maybe.
                """Replaced call to created function body '%s' with direct \
function call""" % self.getName()
            )

        except TooManyArguments as e:
            from .NodeMakingHelpers import (
                makeRaiseExceptionReplacementExpressionFromInstance,
                wrapExpressionWithSideEffects
            )

            result = wrapExpressionWithSideEffects(
                new_node     = makeRaiseExceptionReplacementExpressionFromInstance(
                    expression = call_node,
                    exception  = e.getRealException()
                ),
                old_node     = call_node,
                side_effects = call_node.extractPreCallSideEffects()
            )

            return (
                result,
                "new_statements,new_raise", # TODO: More appropriate tag maybe.
                """Replaced call to created function body '%s' to argument \
error""" % self.getName()
            )


class ExpressionFunctionRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_FUNCTION_REF"

    def __init__(self, function_body, source_ref):
        assert function_body.isExpressionFunctionBody()

        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.function_body = function_body

        # SSA trace based information about the function.
        self.collection = None

    def getDetails(self):
        return {
            "function" : self.function_body.getCodeName()
        }

    def makeCloneAt(self, source_ref):
        return ExpressionFunctionRef(
            function_body = self.function_body,
            source_ref    = source_ref
        )

    def getFunctionBody(self):
        return self.function_body

    def computeExpressionRaw(self, constraint_collection):
        function_body = self.getFunctionBody()

        owning_module = function_body.getParentModule()

        from nuitka.ModuleRegistry import addUsedModule
        addUsedModule(owning_module)

        owning_module.addUsedFunction(function_body)

        from nuitka.optimizations.ConstraintCollections import \
            ConstraintCollectionFunction

        collection = ConstraintCollectionFunction(
            parent        = constraint_collection,
            function_body = function_body
        )
        function_body.collection = collection

        # TODO: Function collection may now know something.
        return self, None, None

    def mayHaveSideEffects(self):
        # Using a function has no side effects.
        return False


class ExpressionFunctionCall(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_FUNCTION_CALL"

    named_children = (
        "function",
        "values"
    )

    def __init__(self, function, values, source_ref):
        assert function.isExpressionFunctionCreation()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "function" : function,
                "values"   : tuple(values),
            },
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        function = self.getFunction()

        if function.willRaiseException(BaseException):
            return function, "new_raise", "Called function is a raise"

        values = self.getArgumentValues()

        for count, value in enumerate(values):
            if value.willRaiseException(BaseException):
                from .NodeMakingHelpers import wrapExpressionWithSideEffects

                result = wrapExpressionWithSideEffects(
                    side_effects = [function] + list(values[:count]),
                    new_node     = value,
                    old_node     = self
                )

                return result, "new_raise", "Called function arguments raise"

        return self, None, None

    getFunction = ExpressionChildrenHavingBase.childGetter("function")
    getArgumentValues = ExpressionChildrenHavingBase.childGetter("values")


# Needed for Python3.3 and higher
class ExpressionFunctionQualnameRef(CompileTimeConstantExpressionMixin,
                                    NodeBase):
    kind = "EXPRESSION_FUNCTION_QUALNAME_REF"
    def __init__(self, function_body, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)
        CompileTimeConstantExpressionMixin.__init__(self)

        self.function_body = function_body

    def computeExpression(self, constraint_collection):
        from .NodeMakingHelpers import makeConstantReplacementNode

        result = makeConstantReplacementNode(
            node     = self,
            constant = self.function_body.getFunctionQualname()
        )

        return result, "new_constant", "Delayed __qualname__ resolution."
