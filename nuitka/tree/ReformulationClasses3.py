#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of Python3 class statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeCheck,
    ExpressionBuiltinGetattr,
    makeExpressionAttributeLookup,
)
from nuitka.nodes.BuiltinIteratorNodes import ExpressionBuiltinIter1
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.BuiltinRefNodes import makeExpressionBuiltinTypeRef
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinTuple
from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.ClassNodes import (
    ExpressionClassDictBody,
    ExpressionClassMappingBody,
    ExpressionSelectMetaclass,
)
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ComparisonNodes import makeComparisonExpression
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    makeStatementConditional,
)
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    makeExpressionMakeTuple,
    makeExpressionMakeTupleOrConstant,
)
from nuitka.nodes.ContainerOperationNodes import StatementListOperationAppend
from nuitka.nodes.DictionaryNodes import (
    ExpressionDictOperationGet2,
    ExpressionDictOperationIn,
    StatementDictOperationRemove,
)
from nuitka.nodes.ExceptionNodes import (
    ExpressionBuiltinMakeException,
    StatementRaiseException,
)
from nuitka.nodes.FunctionAttributeNodes import ExpressionFunctionQualnameRef
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionRef,
    makeExpressionFunctionCall,
    makeExpressionFunctionCreation,
)
from nuitka.nodes.ListOperationNodes import ExpressionListOperationExtend
from nuitka.nodes.LocalsDictNodes import (
    ExpressionLocalsDictRef,
    StatementLocalsDictOperationSet,
    StatementReleaseLocals,
    StatementSetLocals,
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.ModuleAttributeNodes import ExpressionModuleAttributeNameRef
from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionExpressionFromTemplate,
    mergeStatements,
)
from nuitka.nodes.OperatorNodes import makeBinaryOperationNode
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.SubscriptNodes import makeExpressionIndexLookup
from nuitka.nodes.TypeNodes import (
    ExpressionBuiltinType1,
    ExpressionSubtypeCheck,
    ExpressionTypeCheck,
    ExpressionTypeMakeGeneric,
)
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableNameNodes import (
    ExpressionVariableNameRef,
    StatementAssignmentVariableName,
)
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef,
)
from nuitka.Options import isExperimental
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import ParameterSpec

from .InternalModule import (
    internal_source_ref,
    makeInternalHelperFunctionBody,
    once_decorator,
)
from .ReformulationDictionaryCreation import buildDictionaryUnpacking
from .ReformulationSequenceCreation import buildTupleUnpacking
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import (
    makeTryFinallyReleaseStatement,
    makeTryFinallyStatement,
)
from .TreeHelpers import (
    buildFrameNode,
    buildNodeTuple,
    extractDocFromBody,
    getKind,
    makeDictCreationOrConstant2,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
    mangleName,
)


def _buildBasesTupleCreationNode(provider, elements, source_ref):
    """For use in Python3 classes for the bases."""

    for element in elements:
        if getKind(element) == "Starred":
            return buildTupleUnpacking(
                provider=provider, elements=elements, source_ref=source_ref
            )

    return makeExpressionMakeTupleOrConstant(
        elements=buildNodeTuple(provider, elements, source_ref),
        user_provided=True,
        source_ref=source_ref,
    )


def _selectClassBody(_static_qualname):
    if isExperimental("force-p2-class"):
        return ExpressionClassDictBody
    else:
        return ExpressionClassMappingBody


def _needsOrigBases(_static_qualname):
    if isExperimental("force-p2-class"):
        return False
    elif python_version < 0x370:
        return False
    else:
        return True


def buildClassNode3(provider, node, source_ref):
    # Many variables, due to the huge re-formulation that is going on here,
    # which just has the complexity and optimization checks:
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # This function is the Python3 special case with special re-formulation as
    # according to Developer Manual.

    # First, allow plugins to modify the code if they want to.
    Plugins.onClassBodyParsing(provider=provider, class_name=node.name, node=node)

    class_statement_nodes, class_doc = extractDocFromBody(node)

    # We need a scope for the temporary variables, and they might be closured.
    temp_scope = provider.allocateTempScope(name="class_creation")

    tmp_class_decl_dict = provider.allocateTempVariable(
        temp_scope=temp_scope, name="class_decl_dict", temp_type="object"
    )
    tmp_metaclass = provider.allocateTempVariable(
        temp_scope=temp_scope, name="metaclass", temp_type="object"
    )
    tmp_prepared = provider.allocateTempVariable(
        temp_scope=temp_scope, name="prepared", temp_type="object"
    )

    # Can be overridden, but for code object creation, we use that.
    static_qualname = provider.getChildQualname(node.name)

    class_body_class = _selectClassBody(static_qualname)

    class_creation_function = class_body_class(
        provider=provider, name=node.name, doc=class_doc, source_ref=source_ref
    )

    class_locals_scope = class_creation_function.getLocalsScope()

    # Only local variable, for provision to methods.
    class_variable = class_locals_scope.getLocalVariable(
        owner=class_creation_function,
        variable_name="__class__",
    )

    class_locals_scope.registerProvidedVariable(class_variable)

    if python_version >= 0x3C0:
        type_param_nodes = node.type_params
    else:
        type_param_nodes = None

    if type_param_nodes is not None:
        type_params_expressions = buildNodeTuple(
            provider=provider, nodes=type_param_nodes, source_ref=source_ref
        )
    else:
        type_params_expressions = ()

    type_variables = []

    for type_params_expression in type_params_expressions:
        type_variable = class_locals_scope.getLocalVariable(
            owner=class_creation_function,
            variable_name=type_params_expression.name,
        )

        class_locals_scope.registerProvidedVariable(type_variable)

        type_variables.append(type_variable)

    class_variable_ref = ExpressionVariableRef(
        variable=class_variable, source_ref=source_ref
    )

    parent_module = provider.getParentModule()

    code_object = CodeObjectSpec(
        co_name=node.name,
        co_qualname=static_qualname,
        co_kind="Class",
        co_varnames=(),
        co_freevars=(),
        co_argcount=0,
        co_posonlyargcount=0,
        co_kwonlyargcount=0,
        co_has_starlist=False,
        co_has_stardict=False,
        co_filename=parent_module.getRunTimeFilename(),
        co_lineno=source_ref.getLineNumber(),
        future_spec=parent_module.getFutureSpec(),
    )

    body = buildFrameNode(
        provider=class_creation_function,
        nodes=class_statement_nodes,
        code_object=code_object,
        source_ref=source_ref,
    )

    source_ref_orig = source_ref

    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref

    locals_scope = class_creation_function.getLocalsScope()

    statements = [
        StatementSetLocals(
            locals_scope=locals_scope,
            new_locals=ExpressionTempVariableRef(
                variable=tmp_prepared, source_ref=source_ref
            ),
            source_ref=source_ref,
        ),
        StatementAssignmentVariableName(
            provider=class_creation_function,
            variable_name="__module__",
            source=ExpressionModuleAttributeNameRef(
                variable=provider.getParentModule().getVariableForReference("__name__"),
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
    ]

    for type_variable, type_params_expression in zip(
        type_variables, type_params_expressions
    ):
        statements.append(
            makeStatementAssignmentVariable(
                variable=type_variable,
                source=type_params_expression,
                source_ref=source_ref,
            )
        )

    if type_params_expressions:
        statements.append(
            StatementAssignmentVariableName(
                provider=class_creation_function,
                variable_name="__type_params__",
                source=makeExpressionMakeTuple(
                    elements=tuple(
                        ExpressionVariableRef(
                            variable=type_variable, source_ref=source_ref
                        )
                        for type_variable in type_variables
                    ),
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )
        )

    if class_doc is not None:
        statements.append(
            StatementAssignmentVariableName(
                provider=class_creation_function,
                variable_name="__doc__",
                source=makeConstantRefNode(
                    constant=class_doc, source_ref=source_ref, user_provided=True
                ),
                source_ref=source_ref,
            )
        )

    # The "__qualname__" attribute has a dedicated node.
    qualname_ref = ExpressionFunctionQualnameRef(
        function_body=class_creation_function, source_ref=source_ref
    )

    statements.append(
        StatementLocalsDictOperationSet(
            locals_scope=locals_scope,
            variable_name="__qualname__",
            source=qualname_ref,
            source_ref=source_ref,
        )
    )

    if python_version >= 0x300:
        qualname_assign = statements[-1]

    if python_version >= 0x360 and class_creation_function.needsAnnotationsDictionary():
        statements.append(
            StatementLocalsDictOperationSet(
                locals_scope=locals_scope,
                variable_name="__annotations__",
                source=makeConstantRefNode(
                    constant={}, source_ref=source_ref, user_provided=True
                ),
                source_ref=source_ref,
            )
        )

    statements.append(body)

    needs_orig_bases = _needsOrigBases(static_qualname)

    has_bases = node.bases or type_params_expressions

    if has_bases:
        tmp_bases = provider.allocateTempVariable(
            temp_scope=temp_scope, name="bases", temp_type="object"
        )

        if needs_orig_bases:
            tmp_bases_orig = provider.allocateTempVariable(
                temp_scope=temp_scope, name="bases_orig", temp_type="object"
            )

        def makeBasesRef():
            return ExpressionTempVariableRef(variable=tmp_bases, source_ref=source_ref)

    else:

        def makeBasesRef():
            return makeConstantRefNode(constant=(), source_ref=source_ref)

        needs_orig_bases = False

    if has_bases and needs_orig_bases:
        statements.append(
            makeStatementConditional(
                condition=makeComparisonExpression(
                    comparator="NotEq",
                    left=ExpressionTempVariableRef(
                        variable=tmp_bases, source_ref=source_ref
                    ),
                    right=ExpressionTempVariableRef(
                        variable=tmp_bases_orig, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                yes_branch=StatementLocalsDictOperationSet(
                    locals_scope=locals_scope,
                    variable_name="__orig_bases__",
                    source=ExpressionTempVariableRef(
                        variable=tmp_bases_orig, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                no_branch=None,
                source_ref=source_ref,
            )
        )

    statements += (
        makeStatementAssignmentVariable(
            variable=class_variable,
            source=makeExpressionCall(
                called=ExpressionTempVariableRef(
                    variable=tmp_metaclass, source_ref=source_ref
                ),
                args=makeExpressionMakeTuple(
                    elements=(
                        makeConstantRefNode(
                            constant=node.name,
                            source_ref=source_ref,
                            user_provided=True,
                        ),
                        makeBasesRef(),
                        ExpressionLocalsDictRef(
                            locals_scope=locals_scope, source_ref=source_ref
                        ),
                    ),
                    source_ref=source_ref,
                ),
                kw=ExpressionTempVariableRef(
                    variable=tmp_class_decl_dict, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        StatementReturn(expression=class_variable_ref, source_ref=source_ref),
    )

    # TODO: Is this something similar to makeTryFinallyReleaseStatement
    body = makeStatementsSequenceFromStatement(
        statement=makeTryFinallyStatement(
            provider=class_creation_function,
            tried=mergeStatements(statements, True),
            final=StatementReleaseLocals(
                locals_scope=locals_scope, source_ref=source_ref
            ),
            source_ref=source_ref,
        )
    )

    # The class body is basically a function that implicitly, at the end
    # returns its locals and cannot have other return statements contained.
    class_creation_function.setChildBody(body)

    # The class body is basically a function that implicitly, at the end
    # returns its created class and cannot have other return statements
    # contained.

    decorated_body = class_creation_function

    for decorator in buildNodeTuple(
        provider, reversed(node.decorator_list), source_ref
    ):
        decorated_body = makeExpressionCall(
            called=decorator,
            args=makeExpressionMakeTuple(
                elements=(decorated_body,), source_ref=source_ref
            ),
            kw=None,
            source_ref=decorator.getSourceReference(),
        )

    statements = []

    if has_bases:
        if node.bases:
            bases_value = _buildBasesTupleCreationNode(
                provider=provider, elements=node.bases, source_ref=source_ref
            )

            if type_params_expressions:
                bases_value = makeBinaryOperationNode(
                    operator="Add",
                    left=bases_value,
                    right=ExpressionTypeMakeGeneric(
                        type_params=ExpressionVariableNameRef(
                            provider=class_creation_function,
                            variable_name="__type_params__",
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                )
        else:
            assert False

        statements.append(
            makeStatementAssignmentVariable(
                variable=tmp_bases_orig if needs_orig_bases else tmp_bases,
                source=bases_value,
                source_ref=source_ref,
            )
        )

        if needs_orig_bases:
            bases_conversion = makeExpressionFunctionCall(
                function=makeExpressionFunctionCreation(
                    function_ref=ExpressionFunctionRef(
                        function_body=getClassBasesMroConversionHelper(),
                        source_ref=source_ref,
                    ),
                    defaults=(),
                    kw_defaults=None,
                    annotations=None,
                    source_ref=source_ref,
                ),
                values=(
                    ExpressionTempVariableRef(
                        variable=tmp_bases_orig, source_ref=source_ref
                    ),
                ),
                source_ref=source_ref,
            )

            statements.append(
                makeStatementAssignmentVariable(
                    variable=tmp_bases, source=bases_conversion, source_ref=source_ref
                )
            )

    # TODO: It's not really clear, since when those in the middle keywords are accepted
    # and not a SyntaxError, and if then we might have to raise it.
    keyword_keys = tuple(keyword.arg for keyword in node.keywords)
    keyword_values = tuple(keyword.value for keyword in node.keywords)

    if None in keyword_keys:
        assert python_version >= 0x350

        make_keywords_dict = buildDictionaryUnpacking(
            provider,
            keys=keyword_keys,
            values=keyword_values,
            source_ref=source_ref,
        )
    else:
        make_keywords_dict = makeDictCreationOrConstant2(
            keys=keyword_keys,
            values=buildNodeTuple(provider, keyword_values, source_ref),
            source_ref=source_ref,
        )

    statements.append(
        makeStatementAssignmentVariable(
            variable=tmp_class_decl_dict,
            source=make_keywords_dict,
            source_ref=source_ref,
        )
    )

    # Check if there are bases, and if there are, go with the type of the
    # first base class as a metaclass unless it was specified in the class
    # decl dict of course.
    if node.bases:
        unspecified_metaclass_expression = ExpressionBuiltinType1(
            value=makeExpressionIndexLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_bases, source_ref=source_ref
                ),
                index_value=0,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )

        # Might become empty behind our back during conversion, therefore make the
        # check at run time for 3.7 or higher.
        if needs_orig_bases:
            unspecified_metaclass_expression = ExpressionConditional(
                condition=ExpressionTempVariableRef(
                    variable=tmp_bases, source_ref=source_ref
                ),
                expression_yes=unspecified_metaclass_expression,
                expression_no=makeExpressionBuiltinTypeRef(
                    builtin_name="type", source_ref=source_ref
                ),
                source_ref=source_ref,
            )
    else:
        unspecified_metaclass_expression = makeExpressionBuiltinTypeRef(
            builtin_name="type", source_ref=source_ref
        )

    call_prepare = makeStatementAssignmentVariable(
        variable=tmp_prepared,
        source=makeExpressionCall(
            called=makeExpressionAttributeLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_metaclass, source_ref=source_ref
                ),
                attribute_name="__prepare__",
                source_ref=source_ref,
            ),
            args=makeExpressionMakeTuple(
                elements=(
                    makeConstantRefNode(
                        constant=node.name, source_ref=source_ref, user_provided=True
                    ),
                    makeBasesRef(),
                ),
                source_ref=source_ref,
            ),
            kw=ExpressionTempVariableRef(
                variable=tmp_class_decl_dict, source_ref=source_ref
            ),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )

    if python_version >= 0x364:
        call_prepare = makeStatementsSequenceFromStatements(
            call_prepare,
            makeStatementConditional(
                condition=ExpressionAttributeCheck(
                    expression=ExpressionTempVariableRef(
                        variable=tmp_prepared, source_ref=source_ref
                    ),
                    attribute_name="__getitem__",
                    source_ref=source_ref,
                ),
                yes_branch=None,
                no_branch=makeRaiseExceptionExpressionFromTemplate(
                    exception_type="TypeError",
                    template="%s.__prepare__() must return a mapping, not %s",
                    template_args=(
                        ExpressionBuiltinGetattr(
                            expression=ExpressionTempVariableRef(
                                variable=tmp_metaclass, source_ref=source_ref
                            ),
                            name=makeConstantRefNode(
                                constant="__name__", source_ref=source_ref
                            ),
                            default=makeConstantRefNode(
                                constant="<metaclass>", source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        ),
                        makeExpressionAttributeLookup(
                            expression=ExpressionBuiltinType1(
                                value=ExpressionTempVariableRef(
                                    variable=tmp_prepared, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            attribute_name="__name__",
                            source_ref=source_ref,
                        ),
                    ),
                    source_ref=source_ref,
                ).asStatement(),
                source_ref=source_ref,
            ),
        )

    if class_body_class is ExpressionClassDictBody:
        prepare_condition = makeConstantRefNode(constant=False, source_ref=source_ref)
    else:
        prepare_condition = ExpressionAttributeCheck(
            expression=ExpressionTempVariableRef(
                variable=tmp_metaclass, source_ref=source_ref
            ),
            attribute_name="__prepare__",
            source_ref=source_ref,
        )

    statements += (
        makeStatementAssignmentVariable(
            variable=tmp_metaclass,
            source=makeExpressionSelectMetaclass(
                metaclass=ExpressionConditional(
                    condition=ExpressionDictOperationIn(
                        key=makeConstantRefNode(
                            constant="metaclass",
                            source_ref=source_ref,
                            user_provided=True,
                        ),
                        dict_arg=ExpressionTempVariableRef(
                            variable=tmp_class_decl_dict, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    ),
                    expression_yes=ExpressionDictOperationGet2(
                        dict_arg=ExpressionTempVariableRef(
                            variable=tmp_class_decl_dict, source_ref=source_ref
                        ),
                        key=makeConstantRefNode(
                            constant="metaclass",
                            source_ref=source_ref,
                            user_provided=True,
                        ),
                        source_ref=source_ref,
                    ),
                    expression_no=unspecified_metaclass_expression,
                    source_ref=source_ref,
                ),
                bases=makeBasesRef(),
                source_ref=source_ref,
            ),
            source_ref=source_ref_orig,
        ),
        makeStatementConditional(
            condition=ExpressionDictOperationIn(
                key=makeConstantRefNode(
                    constant="metaclass", source_ref=source_ref, user_provided=True
                ),
                dict_arg=ExpressionTempVariableRef(
                    variable=tmp_class_decl_dict, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            no_branch=None,
            yes_branch=StatementDictOperationRemove(
                dict_arg=ExpressionTempVariableRef(
                    variable=tmp_class_decl_dict, source_ref=source_ref
                ),
                key=makeConstantRefNode(
                    constant="metaclass", source_ref=source_ref, user_provided=True
                ),
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        makeStatementConditional(
            condition=prepare_condition,
            yes_branch=call_prepare,
            no_branch=makeStatementAssignmentVariable(
                variable=tmp_prepared,
                source=makeConstantRefNode(
                    constant={}, source_ref=source_ref, user_provided=True
                ),
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        StatementAssignmentVariableName(
            provider=provider,
            variable_name=mangleName(node.name, provider),
            source=decorated_body,
            source_ref=source_ref,
        ),
    )

    if python_version >= 0x300:
        class_creation_function.qualname_setup = node.name, qualname_assign

    tmp_variables = [tmp_class_decl_dict, tmp_metaclass, tmp_prepared]
    if node.bases:
        tmp_variables.insert(0, tmp_bases)
        if needs_orig_bases:
            tmp_variables.insert(0, tmp_bases_orig)

    return makeTryFinallyReleaseStatement(
        provider=provider,
        tried=statements,
        variables=tmp_variables,
        source_ref=source_ref,
    )


# Note: This emulates "Python/bltinmodule.c/update_bases" function. We have it
# here, so we can hope to statically optimize it later on.
@once_decorator
def getClassBasesMroConversionHelper():
    helper_name = "_mro_entries_conversion"

    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("bases",),
            ps_pos_only_args=(),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
        ),
        inline_const_args=False,  # TODO: Allow this.
    )

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(
        temp_scope, "list", temp_type="object"
    )
    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "iter", temp_type="object"
    )
    tmp_item_variable = result.allocateTempVariable(
        temp_scope, "base", temp_type="object"
    )

    args_variable = result.getVariableForAssignment(variable_name="bases")

    non_type_case = makeStatementConditional(
        condition=ExpressionAttributeCheck(
            expression=ExpressionTempVariableRef(
                variable=tmp_item_variable, source_ref=internal_source_ref
            ),
            attribute_name="__mro_entries__",
            source_ref=internal_source_ref,
        ),
        yes_branch=StatementExpressionOnly(
            expression=ExpressionListOperationExtend(
                list_arg=ExpressionTempVariableRef(
                    variable=tmp_result_variable, source_ref=internal_source_ref
                ),
                value=makeExpressionCall(
                    called=makeExpressionAttributeLookup(
                        expression=ExpressionTempVariableRef(
                            variable=tmp_item_variable, source_ref=internal_source_ref
                        ),
                        attribute_name="__mro_entries__",
                        source_ref=internal_source_ref,
                    ),
                    args=makeExpressionMakeTuple(
                        elements=(
                            ExpressionVariableRef(
                                variable=args_variable, source_ref=internal_source_ref
                            ),
                        ),
                        source_ref=internal_source_ref,
                    ),
                    kw=None,
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        no_branch=StatementListOperationAppend(
            list_arg=ExpressionTempVariableRef(
                variable=tmp_result_variable, source_ref=internal_source_ref
            ),
            value=ExpressionTempVariableRef(
                variable=tmp_item_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
        source_ref=internal_source_ref,
    )

    type_case = StatementListOperationAppend(
        list_arg=ExpressionTempVariableRef(
            variable=tmp_result_variable, source_ref=internal_source_ref
        ),
        value=ExpressionTempVariableRef(
            variable=tmp_item_variable, source_ref=internal_source_ref
        ),
        source_ref=internal_source_ref,
    )

    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_item_variable,
                source=ExpressionBuiltinNext1(
                    value=ExpressionTempVariableRef(
                        variable=tmp_iter_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="StopIteration",
            handler_body=StatementLoopBreak(source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionTypeCheck(
                cls=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=type_case,
            no_branch=non_type_case,
            source_ref=internal_source_ref,
        ),
    )

    tried = makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionVariableRef(
                    variable=args_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_result_variable,
            source=makeConstantRefNode(constant=[], source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        StatementLoop(loop_body=loop_body, source_ref=internal_source_ref),
        StatementReturn(
            expression=ExpressionBuiltinTuple(
                value=ExpressionTempVariableRef(
                    variable=tmp_result_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyReleaseStatement(
                provider=result,
                tried=tried,
                variables=(
                    args_variable,
                    tmp_result_variable,
                    tmp_iter_variable,
                    tmp_item_variable,
                ),
                source_ref=internal_source_ref,
            )
        )
    )

    return result


def makeExpressionSelectMetaclass(metaclass, bases, source_ref):
    if isExperimental("select-metaclass-helper"):
        return makeExpressionFunctionCall(
            function=makeExpressionFunctionCreation(
                function_ref=ExpressionFunctionRef(
                    function_body=getClassSelectMetaClassHelper(),
                    source_ref=source_ref,
                ),
                defaults=(),
                kw_defaults=None,
                annotations=None,
                source_ref=source_ref,
            ),
            values=(metaclass, bases),
            source_ref=source_ref,
        )

    else:
        return ExpressionSelectMetaclass(
            metaclass=metaclass, bases=bases, source_ref=source_ref
        )


def _makeRaiseExceptionMetaclassConflict():
    return StatementRaiseException(
        exception_type=ExpressionBuiltinMakeException(
            exception_name="TypeError",
            args=(
                makeConstantRefNode(
                    constant="""\
metaclass conflict: the metaclass of a derived class must be a (non-strict) \
subclass of the metaclasses of all its bases""",
                    source_ref=internal_source_ref,
                ),
            ),
            for_raise=False,
            source_ref=internal_source_ref,
        ),
        exception_value=None,
        exception_trace=None,
        exception_cause=None,
        source_ref=internal_source_ref,
    )


# Note: This emulates selection of meta class based on base classes
@once_decorator
def getClassSelectMetaClassHelper():
    helper_name = "_select_metaclass"

    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=(
                "metaclass",
                "bases",
            ),
            ps_pos_only_args=(),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
        ),
        inline_const_args=False,  # TODO: Allow this.
    )

    metaclass_variable = result.getVariableForAssignment(variable_name="metaclass")
    bases_variable = result.getVariableForAssignment(variable_name="bases")

    temp_scope = None

    tmp_winner_variable = result.allocateTempVariable(
        temp_scope, "winner", temp_type="object"
    )
    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "iter", temp_type="object"
    )
    tmp_item_variable = result.allocateTempVariable(
        temp_scope, "base", temp_type="object"
    )
    tmp_item_type_variable = result.allocateTempVariable(
        temp_scope, "base_type", temp_type="object"
    )

    # For non-types, the metaclass cannot be overruled by bases.
    non_type_case = StatementReturn(
        expression=ExpressionVariableRef(
            variable=metaclass_variable, source_ref=internal_source_ref
        ),
        source_ref=internal_source_ref,
    )

    type_loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_item_variable,
                source=ExpressionBuiltinNext1(
                    value=ExpressionTempVariableRef(
                        variable=tmp_iter_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="StopIteration",
            handler_body=StatementLoopBreak(source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_item_type_variable,
            source=ExpressionBuiltinType1(
                value=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionSubtypeCheck(
                left=ExpressionTempVariableRef(
                    variable=tmp_winner_variable, source_ref=internal_source_ref
                ),
                right=ExpressionTempVariableRef(
                    variable=tmp_item_type_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=None,  # Ignore if current winner is already a subtype.
            no_branch=makeStatementConditional(
                condition=ExpressionSubtypeCheck(
                    left=ExpressionTempVariableRef(
                        variable=tmp_item_type_variable, source_ref=internal_source_ref
                    ),
                    right=ExpressionTempVariableRef(
                        variable=tmp_winner_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                yes_branch=makeStatementAssignmentVariable(
                    variable=tmp_winner_variable,
                    source=ExpressionTempVariableRef(
                        variable=tmp_item_type_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                no_branch=_makeRaiseExceptionMetaclassConflict(),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    type_case = makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=tmp_winner_variable,
            source=ExpressionVariableRef(
                variable=metaclass_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionVariableRef(
                    variable=bases_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        StatementLoop(loop_body=type_loop_body, source_ref=internal_source_ref),
        StatementReturn(
            expression=ExpressionTempVariableRef(
                variable=tmp_winner_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
    )

    tried = makeStatementConditional(
        condition=ExpressionTypeCheck(
            cls=ExpressionVariableRef(
                variable=metaclass_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
        yes_branch=type_case,
        no_branch=non_type_case,
        source_ref=internal_source_ref,
    )

    result.setChildBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyReleaseStatement(
                provider=result,
                tried=tried,
                variables=(
                    tmp_winner_variable,
                    tmp_iter_variable,
                    tmp_item_variable,
                    tmp_item_type_variable,
                ),
                source_ref=internal_source_ref,
            )
        )
    )

    return result


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
