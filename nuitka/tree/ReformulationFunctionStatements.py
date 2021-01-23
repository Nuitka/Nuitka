#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of function statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementAssignmentVariableName,
    StatementReleaseVariable,
)
from nuitka.nodes.AsyncgenNodes import (
    ExpressionAsyncgenObjectBody,
    ExpressionMakeAsyncgenObject,
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    StatementSpecialUnpackCheck,
)
from nuitka.nodes.BuiltinNextNodes import ExpressionSpecialUnpack
from nuitka.nodes.BuiltinRefNodes import makeExpressionBuiltinTypeRef
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.CoroutineNodes import (
    ExpressionCoroutineObjectBody,
    ExpressionMakeCoroutineObject,
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCreation,
    ExpressionFunctionRef,
)
from nuitka.nodes.GeneratorNodes import (
    ExpressionGeneratorObjectBody,
    ExpressionMakeGeneratorObject,
    StatementGeneratorReturnNone,
)
from nuitka.nodes.LocalsDictNodes import StatementSetLocalsDictionary
from nuitka.nodes.OutlineNodes import ExpressionOutlineFunction
from nuitka.nodes.ReturnNodes import StatementReturn, StatementReturnNone
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableNameRef,
    ExpressionVariableRef,
)
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import ParameterSpec

from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .SyntaxErrors import raiseSyntaxError
from .TreeHelpers import (
    buildAnnotationNode,
    buildFrameNode,
    buildNode,
    buildNodeList,
    detectFunctionBodyKind,
    extractDocFromBody,
    getKind,
    makeCallNode,
    makeDictCreationOrConstant2,
    makeStatementsSequenceFromStatement,
    mangleName,
)


def _insertFinalReturnStatement(function_statements_body, return_statement):
    if function_statements_body is None:
        function_statements_body = makeStatementsSequenceFromStatement(
            statement=return_statement
        )
    elif not function_statements_body.isStatementAborting():
        function_statements_body.setChild(
            "statements",
            function_statements_body.subnode_statements + (return_statement,),
        )

    return function_statements_body


def _insertInitialSetLocalsDictStatement(function_body, function_statements_body):
    locals_statement = StatementSetLocalsDictionary(
        locals_scope=function_body.getLocalsScope(), source_ref=function_body.source_ref
    )

    if function_statements_body is None:
        function_statements_body = makeStatementsSequenceFromStatement(
            statement=locals_statement
        )
    else:
        function_statements_body.setChild(
            "statements",
            (locals_statement,) + function_statements_body.subnode_statements,
        )

    return function_statements_body


def _injectDecorator(decorators, inject, acceptable, source_ref):
    assert type(inject) is str
    assert type(acceptable) is tuple

    for decorator in decorators:
        if (
            decorator.isExpressionVariableNameRef()
            and decorator.getVariableName() in acceptable
        ):
            break
    else:
        decorators.append(
            makeExpressionBuiltinTypeRef(builtin_name=inject, source_ref=source_ref)
        )


def buildFunctionNode(provider, node, source_ref):
    # Functions have way too many details, pylint: disable=too-many-locals

    assert getKind(node) == "FunctionDef"

    function_statement_nodes, function_doc = extractDocFromBody(node)

    function_kind, flags = detectFunctionBodyKind(nodes=function_statement_nodes)

    function_body, code_body, code_object = buildFunctionWithParsing(
        provider=provider,
        function_kind=function_kind,
        name=node.name,
        function_doc=function_doc,
        flags=flags,
        node=node,
        source_ref=source_ref,
    )

    if function_kind in ("Generator", "Coroutine"):
        if function_kind == "Coroutine":
            code_body = ExpressionCoroutineObjectBody(
                provider=function_body,
                name=node.name,
                code_object=code_object,
                flags=flags,
                auto_release=None,
                source_ref=source_ref,
            )

            maker_class = ExpressionMakeCoroutineObject
        else:
            code_body = ExpressionGeneratorObjectBody(
                provider=function_body,
                name=node.name,
                code_object=code_object,
                flags=flags,
                auto_release=None,
                source_ref=source_ref,
            )

            maker_class = ExpressionMakeGeneratorObject

        code_body.qualname_provider = provider

        for variable in function_body.getProvidedVariables():
            code_body.getVariableForReference(variable.getName())

        function_body.setChild(
            "body",
            makeStatementsSequenceFromStatement(
                statement=StatementReturn(
                    expression=maker_class(
                        ExpressionFunctionRef(
                            function_body=code_body, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                )
            ),
        )

    decorators = buildNodeList(
        provider=provider, nodes=reversed(node.decorator_list), source_ref=source_ref
    )

    defaults = buildNodeList(
        provider=provider, nodes=node.args.defaults, source_ref=source_ref
    )

    kw_defaults = buildParameterKwDefaults(
        provider=provider, node=node, function_body=function_body, source_ref=source_ref
    )

    function_statements_body = buildFrameNode(
        provider=code_body,
        nodes=function_statement_nodes,
        code_object=code_object,
        source_ref=source_ref,
    )

    if function_kind == "Function":
        # TODO: Generators might have to raise GeneratorExit instead.
        function_statements_body = _insertFinalReturnStatement(
            function_statements_body=function_statements_body,
            return_statement=StatementReturnNone(source_ref=source_ref),
        )

    if "has_exec" in flags:
        function_statements_body = _insertInitialSetLocalsDictStatement(
            function_body=code_body, function_statements_body=function_statements_body
        )

    if function_statements_body.isStatementsFrame():
        function_statements_body = makeStatementsSequenceFromStatement(
            statement=function_statements_body
        )

    code_body.setChild("body", function_statements_body)

    annotations = buildParameterAnnotations(provider, node, source_ref)

    function_creation = ExpressionFunctionCreation(
        function_ref=ExpressionFunctionRef(
            function_body=function_body, source_ref=source_ref
        ),
        defaults=defaults,
        kw_defaults=kw_defaults,
        annotations=annotations,
        source_ref=source_ref,
    )

    # Add the "staticmethod" decorator to __new__ methods if not provided.

    # CPython made these optional, but secretly applies them when it does
    # "class __new__".  We add them earlier, so our optimization will see it.
    if (
        python_version < 0x300
        and node.name == "__new__"
        and provider.isExpressionClassBody()
    ):
        _injectDecorator(
            decorators, "staticmethod", ("staticmethod", "classmethod"), source_ref
        )

    # Add the "classmethod" decorator to __init_subclass__ methods if not provided.
    if (
        python_version >= 0x360
        and node.name == "__init_subclass__"
        and provider.isExpressionClassBody()
    ):
        _injectDecorator(decorators, "classmethod", ("classmethod",), source_ref)

    if (
        python_version >= 0x370
        and node.name == "__class_getitem__"
        and provider.isExpressionClassBody()
    ):
        _injectDecorator(decorators, "classmethod", ("classmethod",), source_ref)

    decorated_function = function_creation
    for decorator in decorators:
        decorated_function = makeCallNode(
            decorator, decorated_function, decorator.getSourceReference()
        )

    result = StatementAssignmentVariableName(
        provider=provider,
        variable_name=mangleName(node.name, provider),
        source=decorated_function,
        source_ref=source_ref,
    )

    if python_version >= 0x340:
        function_body.qualname_setup = result.getVariableName()

    return result


def buildAsyncFunctionNode(provider, node, source_ref):
    # We are creating a function here that creates coroutine objects, with
    # many details each, pylint: disable=too-many-locals
    assert getKind(node) == "AsyncFunctionDef"

    function_statement_nodes, function_doc = extractDocFromBody(node)

    function_kind, flags = detectFunctionBodyKind(
        nodes=function_statement_nodes, start_value="Coroutine"
    )

    creator_function_body, _, code_object = buildFunctionWithParsing(
        provider=provider,
        function_kind=function_kind,
        name=node.name,
        function_doc=function_doc,
        flags=(),
        node=node,
        source_ref=source_ref,
    )

    if function_kind == "Coroutine":
        function_body = ExpressionCoroutineObjectBody(
            provider=creator_function_body,
            name=node.name,
            code_object=code_object,
            flags=flags,
            auto_release=None,
            source_ref=source_ref,
        )
    else:
        function_body = ExpressionAsyncgenObjectBody(
            provider=creator_function_body,
            name=node.name,
            code_object=code_object,
            flags=flags,
            auto_release=None,
            source_ref=source_ref,
        )

    function_body.qualname_provider = provider

    for variable in creator_function_body.getProvidedVariables():
        function_body.getVariableForReference(variable.getName())

    decorators = buildNodeList(
        provider=provider, nodes=reversed(node.decorator_list), source_ref=source_ref
    )

    defaults = buildNodeList(
        provider=provider, nodes=node.args.defaults, source_ref=source_ref
    )

    function_statements_body = buildFrameNode(
        provider=function_body,
        nodes=function_statement_nodes,
        code_object=code_object,
        source_ref=source_ref,
    )

    function_statements_body = _insertFinalReturnStatement(
        function_statements_body=function_statements_body,
        return_statement=StatementGeneratorReturnNone(source_ref=source_ref),
    )

    if function_statements_body.isStatementsFrame():
        function_statements_body = makeStatementsSequenceFromStatement(
            statement=function_statements_body
        )

    function_body.setChild("body", function_statements_body)

    annotations = buildParameterAnnotations(provider, node, source_ref)

    kw_defaults = buildParameterKwDefaults(
        provider=provider,
        node=node,
        function_body=creator_function_body,
        source_ref=source_ref,
    )

    if function_kind == "Coroutine":
        creation_node = ExpressionMakeCoroutineObject(
            coroutine_ref=ExpressionFunctionRef(
                function_body=function_body, source_ref=source_ref
            ),
            source_ref=source_ref,
        )
    else:
        creation_node = ExpressionMakeAsyncgenObject(
            asyncgen_ref=ExpressionFunctionRef(
                function_body=function_body, source_ref=source_ref
            ),
            source_ref=source_ref,
        )

    creator_function_body.setChild(
        "body",
        makeStatementsSequenceFromStatement(
            statement=StatementReturn(expression=creation_node, source_ref=source_ref)
        ),
    )

    function_creation = ExpressionFunctionCreation(
        function_ref=ExpressionFunctionRef(
            function_body=creator_function_body, source_ref=source_ref
        ),
        defaults=defaults,
        kw_defaults=kw_defaults,
        annotations=annotations,
        source_ref=source_ref,
    )

    decorated_function = function_creation
    for decorator in decorators:
        decorated_function = makeCallNode(
            decorator, decorated_function, decorator.getSourceReference()
        )

    result = StatementAssignmentVariableName(
        provider=provider,
        variable_name=mangleName(node.name, provider),
        source=decorated_function,
        source_ref=source_ref,
    )

    function_body.qualname_setup = result.getVariableName()

    # Share the non-local declarations. TODO: This may also apply to generators
    # and async generators.
    creator_function_body.non_local_declarations = function_body.non_local_declarations

    return result


def buildParameterKwDefaults(provider, node, function_body, source_ref):
    # Build keyword only arguments default values. We are hiding here, that it
    # is a Python3 only feature.

    if python_version >= 0x300:
        kw_only_names = function_body.getParameters().getKwOnlyParameterNames()

        if kw_only_names:
            keys = []
            values = []

            for kw_only_name, kw_default in zip(kw_only_names, node.args.kw_defaults):
                if kw_default is not None:
                    keys.append(kw_only_name)
                    values.append(buildNode(provider, kw_default, source_ref))

            kw_defaults = makeDictCreationOrConstant2(
                keys=keys, values=values, source_ref=source_ref
            )
        else:
            kw_defaults = None
    else:
        kw_defaults = None

    return kw_defaults


def buildParameterAnnotations(provider, node, source_ref):
    # Too many branches, because there is too many cases, pylint: disable=too-many-branches

    # Build annotations. We are hiding here, that it is a Python3 only feature.
    if python_version < 0x300:
        return None

    # Starting with Python 3.4, the names of parameters are mangled in
    # annotations as well.
    if python_version < 0x340:
        mangle = lambda variable_name: variable_name
    else:
        mangle = lambda variable_name: mangleName(variable_name, provider)

    keys = []
    values = []

    def addAnnotation(key, value):
        keys.append(mangle(key))
        values.append(value)

    def extractArgAnnotation(arg):
        if getKind(arg) == "Name":
            assert arg.annotation is None
        elif getKind(arg) == "arg":
            if arg.annotation is not None:
                addAnnotation(
                    key=arg.arg,
                    value=buildAnnotationNode(provider, arg.annotation, source_ref),
                )
        elif getKind(arg) == "Tuple":
            for sub_arg in arg.elts:
                extractArgAnnotation(sub_arg)
        else:
            assert False, getKind(arg)

    if python_version >= 0x380:
        for arg in node.args.posonlyargs:
            extractArgAnnotation(arg)

    for arg in node.args.args:
        extractArgAnnotation(arg)

    for arg in node.args.kwonlyargs:
        extractArgAnnotation(arg)

    if python_version < 0x340:
        if node.args.varargannotation is not None:
            addAnnotation(
                key=node.args.vararg,
                value=buildNode(provider, node.args.varargannotation, source_ref),
            )

        if node.args.kwargannotation is not None:
            addAnnotation(
                key=node.args.kwarg,
                value=buildNode(provider, node.args.kwargannotation, source_ref),
            )
    else:
        if node.args.vararg is not None:
            extractArgAnnotation(node.args.vararg)
        if node.args.kwarg is not None:
            extractArgAnnotation(node.args.kwarg)

    # Return value annotation (not there for lambdas)
    if hasattr(node, "returns") and node.returns is not None:
        addAnnotation(
            key="return", value=buildAnnotationNode(provider, node.returns, source_ref)
        )

    if keys:
        return makeDictCreationOrConstant2(
            keys=keys, values=values, source_ref=source_ref
        )
    else:
        return None


def _wrapFunctionWithSpecialNestedArgs(
    name, outer_body, parameters, special_args, source_ref
):
    inner_name = name.strip("<>") + "$inner"
    iter_vars = []

    values = []

    statements = []

    def unpackFrom(source, arg_names):
        accesses = []

        sub_special_index = 0

        iter_var = outer_body.allocateTempVariable(None, "arg_iter_%d" % len(iter_vars))
        iter_vars.append(iter_var)

        statements.append(
            StatementAssignmentVariable(
                variable=iter_var,
                source=ExpressionBuiltinIter1(value=source, source_ref=source_ref),
                source_ref=source_ref,
            )
        )

        for element_index, arg_name in enumerate(arg_names):
            if getKind(arg_name) == "Name":
                arg_var = outer_body.createProvidedVariable(arg_name.id)
                outer_body.getLocalsScope().registerProvidedVariable(arg_var)

                statements.append(
                    StatementAssignmentVariable(
                        variable=arg_var,
                        source=ExpressionSpecialUnpack(
                            value=ExpressionTempVariableRef(
                                variable=iter_var, source_ref=source_ref
                            ),
                            count=element_index + 1,
                            expected=len(arg_names),
                            starred=False,
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    )
                )

                accesses.append(
                    ExpressionVariableRef(variable=arg_var, source_ref=source_ref)
                )
            elif getKind(arg_name) == "Tuple":
                accesses.extend(
                    unpackFrom(
                        source=ExpressionSpecialUnpack(
                            value=ExpressionTempVariableRef(
                                variable=iter_var, source_ref=source_ref
                            ),
                            count=element_index + 1,
                            expected=len(arg_names),
                            starred=False,
                            source_ref=source_ref,
                        ),
                        arg_names=arg_name.elts,
                    )
                )

                sub_special_index += 1
            else:
                assert False, arg_name

        statements.append(
            StatementSpecialUnpackCheck(
                iterator=ExpressionTempVariableRef(
                    variable=iter_var, source_ref=source_ref
                ),
                count=len(arg_names),
                source_ref=source_ref,
            )
        )

        return accesses

    for arg_name in parameters.getParameterNames():
        if arg_name.startswith("."):
            source = ExpressionVariableNameRef(
                provider=outer_body, variable_name=arg_name, source_ref=source_ref
            )

            values.extend(unpackFrom(source, special_args[arg_name]))
        else:
            values.append(
                ExpressionVariableNameRef(
                    provider=outer_body, variable_name=arg_name, source_ref=source_ref
                )
            )

    code_body = ExpressionOutlineFunction(
        provider=outer_body, name=inner_name, source_ref=source_ref
    )

    statements.append(StatementReturn(expression=code_body, source_ref=source_ref))

    outer_body.setChild(
        "body",
        makeStatementsSequenceFromStatement(
            statement=makeTryFinallyStatement(
                provider=outer_body,
                tried=statements,
                final=[
                    StatementReleaseVariable(variable=variable, source_ref=source_ref)
                    for variable in sorted(
                        outer_body.getTempVariables(),
                        key=lambda variable: variable.getName(),
                    )
                ],
                source_ref=source_ref,
                public_exc=False,
            )
        ),
    )

    return code_body


def buildFunctionWithParsing(
    provider, function_kind, name, function_doc, flags, node, source_ref
):
    # This contains a complex re-formulation for nested parameter functions.
    # pylint: disable=too-many-locals

    kind = getKind(node)
    assert kind in ("FunctionDef", "Lambda", "AsyncFunctionDef"), (
        "unsupported for kind " + kind
    )

    def extractArg(arg):
        if arg is None:
            return None
        elif type(arg) is str:
            return mangleName(arg, provider)
        elif getKind(arg) == "Name":
            return mangleName(arg.id, provider)
        elif getKind(arg) == "arg":
            return mangleName(arg.arg, provider)
        elif getKind(arg) == "Tuple":
            # These are to be re-formulated on the outside.
            assert False
        else:
            assert False, getKind(arg)

    special_args = {}

    def extractNormalArgs(args):
        normal_args = []

        for arg in args:
            if type(arg) is not str and getKind(arg) == "Tuple":
                special_arg_name = ".%d" % (len(special_args) + 1)

                special_args[special_arg_name] = arg.elts
                normal_args.append(special_arg_name)
            else:
                normal_args.append(extractArg(arg))

        return normal_args

    parameters = ParameterSpec(
        ps_name=name,
        ps_normal_args=extractNormalArgs(node.args.args),
        ps_pos_only_args=[extractArg(arg) for arg in node.args.posonlyargs]
        if python_version >= 0x380
        else (),
        ps_kw_only_args=[extractArg(arg) for arg in node.args.kwonlyargs]
        if python_version >= 0x300
        else (),
        ps_list_star_arg=extractArg(node.args.vararg),
        ps_dict_star_arg=extractArg(node.args.kwarg),
        ps_default_count=len(node.args.defaults),
    )

    message = parameters.checkParametersValid()

    if message is not None:
        raiseSyntaxError(message, source_ref.atColumnNumber(node.col_offset))

    parent_module = provider.getParentModule()

    code_object = CodeObjectSpec(
        co_name=name,
        co_kind=function_kind,
        co_varnames=parameters.getParameterNames(),
        co_freevars=(),
        co_argcount=parameters.getArgumentCount(),
        co_posonlyargcount=parameters.getPosOnlyParameterCount(),
        co_kwonlyargcount=parameters.getKwOnlyParameterCount(),
        co_has_starlist=parameters.getStarListArgumentName() is not None,
        co_has_stardict=parameters.getStarDictArgumentName() is not None,
        co_filename=parent_module.getRunTimeFilename(),
        co_lineno=source_ref.getLineNumber(),
        future_spec=parent_module.getFutureSpec(),
    )

    outer_body = ExpressionFunctionBody(
        provider=provider,
        name=name,
        code_object=code_object,
        flags=flags,
        doc=function_doc,
        parameters=parameters,
        auto_release=None,
        source_ref=source_ref,
    )

    # Wrap if necessary for special nested arguments.
    if special_args:
        code_body = _wrapFunctionWithSpecialNestedArgs(
            name=name,
            outer_body=outer_body,
            parameters=parameters,
            special_args=special_args,
            source_ref=source_ref,
        )

    else:
        code_body = outer_body

    return outer_body, code_body, code_object


def addFunctionVariableReleases(function):
    assert function.isExpressionFunctionBodyBase()

    releases = []

    # We attach everything to the function definition source location.
    source_ref = function.getSourceReference()

    for variable in function.getLocalVariables():
        # Shared variables are freed by function attachment.
        if variable.getOwner() is not function:
            continue

        releases.append(
            StatementReleaseVariable(variable=variable, source_ref=source_ref)
        )

    if releases:
        body = function.subnode_body

        if body.isStatementsFrame():
            body = makeStatementsSequenceFromStatement(statement=body)

        body = makeTryFinallyStatement(
            provider=function, tried=body, final=releases, source_ref=source_ref
        )

        function.setChild("body", makeStatementsSequenceFromStatement(statement=body))
