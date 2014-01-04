#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Utils, SyntaxErrors

from nuitka.nodes.ParameterSpecs import ParameterSpec

from nuitka.nodes.VariableRefNodes import ExpressionTargetVariableRef
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinRef
from nuitka.nodes.CallNodes import ExpressionCallNoKeywords
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionCreation,
    ExpressionFunctionBody,
    ExpressionFunctionRef
)
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.AssignNodes import StatementAssignmentVariable

from .Helpers import (
    makeStatementsSequenceFromStatement,
    makeDictCreationOrConstant,
    buildStatementsNode,
    extractDocFromBody,
    buildNodeList,
    buildNode,
    getKind
)

def buildFunctionNode(provider, node, source_ref):
    assert getKind( node ) == "FunctionDef"

    # Remove "exec" flag if any.
    source_ref = source_ref.getExecReference( False )

    function_statements, function_doc = extractDocFromBody( node )

    function_body = ExpressionFunctionBody(
        provider   = provider,
        name       = node.name,
        doc        = function_doc,
        parameters = buildParameterSpec( node.name, node, source_ref ),
        source_ref = source_ref
    )

    # Hack:
    function_body.parent = provider

    decorators = buildNodeList(
        provider   = provider,
        nodes      = reversed( node.decorator_list ),
        source_ref = source_ref
    )

    defaults = buildNodeList(
        provider   = provider,
        nodes      = node.args.defaults,
        source_ref = source_ref
    )

    kw_defaults = buildParameterKwDefaults(
        provider, node, function_body, source_ref
    )

    function_statements_body = buildStatementsNode(
        provider   = function_body,
        nodes      = function_statements,
        frame      = True,
        source_ref = source_ref
    )

    if function_body.isExpressionFunctionBody() and function_body.isGenerator():
        # TODO: raise generator exit?
        pass
    elif function_statements_body is None:
        function_statements_body = makeStatementsSequenceFromStatement(
            statement = StatementReturn(
                expression = ExpressionConstantRef(
                    constant   = None,
                    source_ref = source_ref.atInternal()
                ),
                source_ref = source_ref.atInternal()
            )
        )
    elif not function_statements_body.isStatementAborting():
        function_statements_body.setStatements(
            function_statements_body.getStatements() +
            (
                StatementReturn(
                    expression = ExpressionConstantRef(
                        constant   = None,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref.atInternal()
                ),
            )
        )

    function_body.setBody( function_statements_body )

    annotations = buildParameterAnnotations( provider, node, source_ref )

    decorated_body = ExpressionFunctionCreation(
        function_ref = ExpressionFunctionRef(
            function_body,
            source_ref = source_ref
        ),
        defaults     = defaults,
        kw_defaults  = kw_defaults,
        annotations  = annotations,
        source_ref   = source_ref
    )

    # Add the staticmethod decorator to __new__ methods if not provided.

    # CPython made these optional, but applies them to every class __new__. We
    # add them early, so our optimization will see it.
    if node.name == "__new__" and not decorators and \
         provider.isExpressionFunctionBody() and provider.isClassDictCreation():

        decorators = (
            ExpressionBuiltinRef(
                builtin_name = "staticmethod",
                source_ref   = source_ref
            ),
        )

    for decorator in decorators:
        decorated_body = ExpressionCallNoKeywords(
            called     = decorator,
            args       = ExpressionMakeTuple(
                elements    = ( decorated_body, ),
                source_ref = source_ref
            ),
            source_ref = decorator.getSourceReference()
        )

    return StatementAssignmentVariable(
        variable_ref = ExpressionTargetVariableRef(
            variable_name = node.name,
            source_ref    = source_ref
        ),
        source       = decorated_body,
        source_ref   = source_ref
    )

def buildParameterKwDefaults(provider, node, function_body, source_ref):
    # Build keyword only arguments default values. We are hiding here, that it
    # is a Python3 only feature.

    if Utils.python_version >= 300:
        kw_only_names = function_body.getParameters().getKwOnlyParameterNames()

        if kw_only_names:
            keys = []
            values = []

            for kw_only_name, kw_default in \
              zip( kw_only_names, node.args.kw_defaults ):
                if kw_default is not None:
                    keys.append(
                        ExpressionConstantRef(
                            constant   = kw_only_name,
                            source_ref = source_ref
                        )
                    )
                    values.append(
                        buildNode( provider, kw_default, source_ref )
                    )

            kw_defaults = makeDictCreationOrConstant(
                keys       = keys,
                values     = values,
                lazy_order = False,
                source_ref = source_ref
            )
        else:
            kw_defaults = None
    else:
        kw_defaults = None

    return kw_defaults

def buildParameterAnnotations(provider, node, source_ref):
    # Too many branches, because there is too many cases, pylint: disable=R0912

    # Build annotations. We are hiding here, that it is a Python3 only feature.
    if Utils.python_version < 300:
        return None

    keys = []
    values = []

    def addAnnotation(key, value):
        keys.append(
            ExpressionConstantRef(
                constant      = key,
                source_ref    = source_ref,
                user_provided = True
            )
        )
        values.append( value )

    def extractArg(arg):
        if getKind( arg ) == "Name":
            assert arg.annotation is None
        elif getKind( arg ) == "arg":
            if arg.annotation is not None:
                addAnnotation(
                    key   = arg.arg,
                    value = buildNode( provider, arg.annotation, source_ref )
                )
        elif getKind( arg ) == "Tuple":
            for arg in arg.elts:
                extractArg( arg )
        else:
            assert False, getKind( arg )

    for arg in node.args.args:
        extractArg( arg )

    for arg in node.args.kwonlyargs:
        extractArg( arg )

    if Utils.python_version < 340:
        if node.args.varargannotation is not None:
            addAnnotation(
                key   = node.args.vararg,
                value = buildNode(
                    provider, node.args.varargannotation, source_ref
                )
            )

        if node.args.kwargannotation is not None:
            addAnnotation(
                key   = node.args.kwarg,
                value = buildNode(
                    provider, node.args.kwargannotation, source_ref
                )
            )
    else:
        if node.args.vararg is not None:
            extractArg( node.args.vararg )
        if node.args.kwarg is not None:
            extractArg( node.args.kwarg )

    # Return value annotation (not there for lambdas)
    if hasattr( node, "returns" ) and node.returns is not None:
        addAnnotation(
            key   = "return",
            value = buildNode( provider, node.returns, source_ref )
        )

    if keys:
        return makeDictCreationOrConstant(
            keys       = keys,
            values     = values,
            lazy_order = False,
            source_ref = source_ref
        )
    else:
        return None

def buildParameterSpec(name, node, source_ref):
    kind = getKind( node )

    assert kind in ( "FunctionDef", "Lambda" ), "unsupported for kind " + kind

    def extractArg(arg):
        if type( arg ) is str or arg is None:
            return arg
        elif getKind( arg ) == "Name":
            return arg.id
        elif getKind( arg ) == "arg":
            return arg.arg
        elif getKind( arg ) == "Tuple":
            return tuple( extractArg( arg ) for arg in arg.elts )
        else:
            assert False, getKind( arg )

    result = ParameterSpec(
        name           = name,
        normal_args    = [ extractArg( arg ) for arg in node.args.args ],
        kw_only_args   = [ extractArg( arg ) for arg in node.args.kwonlyargs ]
                           if Utils.python_version >= 300 else
                         [],
        list_star_arg  = extractArg( node.args.vararg ),
        dict_star_arg  = extractArg( node.args.kwarg ),
        default_count  = len(node.args.defaults)
    )

    message = result.checkValid()

    if message is not None:
        SyntaxErrors.raiseSyntaxError(
            message,
            source_ref
        )

    return result
