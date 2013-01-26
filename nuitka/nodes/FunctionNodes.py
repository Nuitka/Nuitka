#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

Lambdas are functions too. The functions are at the core of the language and have their
complexities.

"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonParameterHavingNodeBase,
    CPythonExpressionMixin,
    CPythonChildrenHaving,
    CPythonClosureTaker,
    CPythonNodeBase
)

from .IndicatorMixins import (
    MarkUnoptimizedFunctionIndicator,
    MarkContainsTryExceptIndicator,
    MarkLocalsDictIndicator,
    MarkGeneratorIndicator
)

from .ParameterSpec import TooManyArguments, matchCall

from nuitka import Variables, Utils

from nuitka.__past__ import iterItems


class CPythonExpressionFunctionBody( CPythonClosureTaker, CPythonChildrenHaving,
                                     CPythonParameterHavingNodeBase, CPythonExpressionMixin,
                                     MarkContainsTryExceptIndicator,
                                     MarkGeneratorIndicator,
                                     MarkLocalsDictIndicator, MarkUnoptimizedFunctionIndicator ):
    # We really want these many ancestors, as per design, we add properties via base class
    # mixins a lot, pylint: disable=R0901

    kind = "EXPRESSION_FUNCTION_BODY"

    named_children = ( "body", )

    def __init__( self, provider, name, doc, parameters, source_ref, is_class = False ):
        # Register ourselves immediately with the module.
        provider.getParentModule().addFunction( self )

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

        CPythonClosureTaker.__init__(
            self,
            provider      = provider,
            early_closure = is_class
        )

        CPythonParameterHavingNodeBase.__init__(
            self,
            name        = name,
            code_prefix = code_prefix,
            parameters  = parameters,
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

        MarkContainsTryExceptIndicator.__init__( self )

        MarkGeneratorIndicator.__init__( self )

        MarkLocalsDictIndicator.__init__( self )

        MarkUnoptimizedFunctionIndicator.__init__( self )

        self.is_class = is_class
        self.doc = doc

        # Indicator, if this is a function that uses "super", because if it does, it would
        # like to get the final "__class__" attached.
        self.has_super = False

        # Indicator if the return value exception might be required.
        self.return_exception = False

        # Indicator if the generator return exception might be required.
        self.generator_return_exception = False

        # Indicator if the function needs to be created as a function object.
        self.needs_creation = False

        # Indicator if the function is called directly.
        self.needs_direct = False

        # Indicator if the function is used outside of where it's defined.
        self.cross_module_use = False

    def getDetails( self ):
        return {
            "name"       : self.getFunctionName(),
            "ref_name"   : self.getCodeName(),
            "parameters" : self.getParameters(),
            "provider"   : self.provider.getCodeName(),
            "doc"        : self.doc
        }

    def getParent( self ):
        assert False

    def isClassDictCreation( self ):
        return self.is_class

    def getDetail( self ):
        return "named %s with %s" % ( self.name, self.parameters )

    def getFunctionName( self ):
        if self.is_lambda:
            return "<lambda>"
        elif self.is_genexpr:
            return "<genexpr>"
        else:
            return self.name

    def getDoc( self ):
        return self.doc

    def getLocalVariableNames( self ):
        return Variables.getNames( self.getLocalVariables() )

    def getLocalVariables( self ):
        return [
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable()
        ]

    def getUserLocalVariables( self ):
        return tuple(
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable() and not variable.isParameterVariable()
        )

    def getVariables( self ):
        return self.providing.values()

    def removeVariable( self, variable ):
        assert variable.getOwner() is self
        assert variable in self.providing.values(), ( self.providing, variable )
        assert not variable.getReferences()

        del self.providing[ variable.getName() ]

        assert not variable.isParameterVariable()
        self.taken.remove( variable )

    def getVariableForAssignment( self, variable_name ):
        # print ( "ASS func", self, variable_name )

        if self.hasTakenVariable( variable_name ):
            result = self.getTakenVariable( variable_name )

            if self.isClassDictCreation():
                if result.isModuleVariableReference() and not result.isFromGlobalStatement():
                    result = self.getProvidedVariable( variable_name )

                    if result.isModuleVariableReference():
                        del self.providing[ variable_name ]

                        result = self.getProvidedVariable( variable_name )
        else:
            result = self.getProvidedVariable( variable_name )

        return result

    def getVariableForReference( self, variable_name ):
        # print ( "REF func", self, variable_name )

        if self.hasProvidedVariable( variable_name ):
            result = self.getProvidedVariable( variable_name )
        else:
            # For exec containing/star import containing, get a closure variable and if it
            # is a module variable, only then make it a maybe local variable.
            result = self.getClosureVariable(
                variable_name = variable_name
            )

            if self.isUnoptimized() and result.isModuleVariable():
                result = Variables.MaybeLocalVariable(
                    owner         = self,
                    variable_name = variable_name
                )

            # Remember that we need that closure for something.
            self.registerProvidedVariable( result )

        return result

    def getVariableForClosure( self, variable_name ):
        # print( "createProvidedVariable", self, variable_name )

        # The class bodies provide no closure, except under CPython3, "__class__" and
        # nothing else.

        if self.isClassDictCreation() and ( variable_name != "__class__" or Utils.python_version < 300 ):
            return self.provider.getVariableForReference( variable_name )

        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            return self.provider.getVariableForClosure( variable_name )

    def createProvidedVariable( self, variable_name ):
        # print( "createProvidedVariable", self, variable_name )

        if self.local_locals:
            if self.isClassDictCreation():
                return Variables.ClassVariable(
                    owner         = self,
                    variable_name = variable_name
                )
            else:
                return Variables.LocalVariable(
                    owner         = self,
                    variable_name = variable_name
                )
        else:
            # Make sure the provider knows it has to provide a variable of this name for
            # the assigment.
            self.provider.getVariableForAssignment(
                variable_name = variable_name
            )

            return self.getClosureVariable(
                variable_name = variable_name
            )

    def addNonlocalsDeclaration( self, names, source_ref ):
        self.non_local_declarations.append( ( names, source_ref ) )

    def getNonlocalDeclarations( self ):
        return self.non_local_declarations

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def needsCreation( self ):
        # TODO: This looks kind of arbitrary, the users should decide, if they need it.
        return self.needs_creation

    def markAsNeedsCreation( self ):
        self.needs_creation = True

    def needsDirectCall( self ):
        return self.needs_direct

    def markAsDirectlyCalled( self ):
        self.needs_direct = True

    def isCrossModuleUsed( self ):
        return self.cross_module_use

    def markAsCrossModuleUsed( self ):
        self.cross_module_use = True

    def computeNode( self, constraint_collection ):
        # Function body is quite irreplacable.
        return self, None, None

    def computeNodeCall( self, call_node, constraint_collection ):
        # TODO: Until we have something to re-order the arguments, we need to skip this. For
        # the immediate need, we avoid this complexity, as a re-ordering will be needed.
        if call_node.getNamedArgumentPairs():
            return call_node, None, None

        call_spec = self.getParameters()

        try:
            args_dict = matchCall(
                func_name     = self.getName(),
                args          = call_spec.getArgumentNames(),
                star_list_arg = call_spec.getStarListArgumentName(),
                star_dict_arg = call_spec.getStarDictArgumentName(),
                num_defaults  = call_spec.getDefaultCount(),
                positional    = call_node.getPositionalArguments(),
                pairs         = ()
            )

            values = []

            for positional_arg in call_node.getPositionalArguments():
                for _arg_name, arg_value in iterItems( args_dict ):
                    if arg_value is positional_arg:
                        values.append( arg_value )

            result = CPythonExpressionFunctionCall(
                function_body = self,
                values        = values,
                source_ref    = call_node.getSourceReference()
            )

            return (
                result,
                "new_statements", # TODO: More appropiate tag maybe.
                "Replaced call to created function body '%s' with direct function call" % self.getName()
            )

        except TooManyArguments as e:
            from nuitka.nodes.NodeMakingHelpers import (
                makeRaiseExceptionReplacementExpressionFromInstance,
                wrapExpressionWithSideEffects
            )

            result = wrapExpressionWithSideEffects(
                new_node = makeRaiseExceptionReplacementExpressionFromInstance(
                    expression     = call_node,
                    exception      = e.getRealException()
                ),
                old_node           = call_node,
                side_effects = call_node.extractPreCallSideEffects()
            )

            return (
                result,
                "new_statements,new_raise", # TODO: More appropiate tag maybe.
                "Replaced call to created function body '%s' to argument error" % self.getName()
            )


    def isCompileTimeConstant( self ):
        # TODO: It's actually pretty much compile time accessible mayhaps.
        return None

    def mayHaveSideEffects( self, constraint_collection ):
        # The function definition has no side effects, calculating the defaults would be,
        # but that is done outside of this.
        return False

    def markAsClassClosureTaker( self ):
        self.has_super = True

    def isClassClosureTaker( self ):
        return self.has_super

    def makeCloneAt( self, source_ref ):
        result = self.__class__(
            provider   = self.provider,
            name       = self.name,
            doc        = self.name,
            # TODO: Clone parameters too, when we start to mutate them.
            parameters = self.parameters,
            source_ref =  source_ref
        )

        result.setBody(
            self.getBody().makeCloneAt( source_ref )
        )

        return result

    def markAsExceptionReturnValue( self ):
        self.return_exception = True

    def needsExceptionReturnValue( self ):
        return self.return_exception

    def markAsExceptionGeneratorReturn( self ):
        self.generator_return_exception = True

    def needsExceptionGeneratorReturn( self ):
        return self.generator_return_exception


class CPythonExpressionFunctionCreation( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_FUNCTION_CREATION"

    # Note: The order of evaluation for these is a bit unexpected, but true. Keyword
    # defaults go first, then normal defaults, and annotations of all kinds go last.
    named_children = ( "kw_defaults", "defaults", "annotations", "function_ref" )

    def __init__( self, function_ref, defaults, kw_defaults, annotations, source_ref ):
        assert kw_defaults is None or kw_defaults.isExpression()
        assert annotations is None or annotations.isExpression()
        assert function_ref.isExpressionFunctionRef()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "function_ref"  : function_ref,
                "defaults"      : tuple( defaults ),
                "kw_defaults"   : kw_defaults,
                "annotations"   : annotations
            },
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        # TODO: Function body may know something.
        return self, None, None

    getFunctionRef = CPythonExpressionChildrenHavingBase.childGetter( "function_ref" )
    getDefaults = CPythonExpressionChildrenHavingBase.childGetter( "defaults" )
    getKwDefaults = CPythonExpressionChildrenHavingBase.childGetter( "kw_defaults" )
    getAnnotations = CPythonExpressionChildrenHavingBase.childGetter( "annotations" )


class CPythonExpressionFunctionRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_FUNCTION_REF"

    def __init__( self, function_body, source_ref ):
        assert function_body.isExpressionFunctionBody()

        CPythonNodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.function_body = function_body

    def getDetails( self ):
        return {
            "function" : self.function_body.getCodeName()
        }

    def makeCloneAt( self, source_ref ):
        return CPythonExpressionFunctionRef(
            function_body = self.function_body,
            source_ref    = source_ref
        )

    def getFunctionBody( self ):
        return self.function_body

    def computeNode( self, constraint_collection ):
        # TODO: Function body may know something.
        return self, None, None


class CPythonExpressionFunctionCall( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_FUNCTION_CALL"

    named_children = ( "function", "values" )

    def __init__( self, function, values, source_ref ):
        assert function.isExpressionFunctionCreation()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "function" : function,
                "values"   : tuple( values ),
            },
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        return self, None, None

    getFunction = CPythonExpressionChildrenHavingBase.childGetter( "function" )
    getArgumentValues = CPythonExpressionChildrenHavingBase.childGetter( "values" )
