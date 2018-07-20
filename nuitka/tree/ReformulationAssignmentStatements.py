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
""" Reformulation of assignment statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementAssignmentVariableName,
    StatementDelVariable,
    StatementDelVariableName,
    StatementReleaseVariable
)
from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeLookup,
    StatementAssignmentAttribute,
    StatementDelAttribute
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinIterForUnpack,
    StatementSpecialUnpackCheck
)
from nuitka.nodes.BuiltinLenNodes import ExpressionBuiltinLen
from nuitka.nodes.BuiltinNextNodes import ExpressionSpecialUnpack
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinList
from nuitka.nodes.ComparisonNodes import ExpressionComparison
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantEllipsisRef
from nuitka.nodes.ContainerOperationNodes import ExpressionListOperationPop
from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionExpressionFromTemplate
)
from nuitka.nodes.OperatorNodes import (
    makeBinaryOperationNode,
    makeExpressionOperationBinaryInplace
)
from nuitka.nodes.SliceNodes import (
    ExpressionBuiltinSlice,
    ExpressionSliceLookup,
    StatementAssignmentSlice,
    StatementDelSlice
)
from nuitka.nodes.SubscriptNodes import (
    ExpressionSubscriptLookup,
    StatementAssignmentSubscript,
    StatementDelSubscript
)
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableLocalNameRef,
    ExpressionVariableNameRef
)
from nuitka.PythonVersions import python_version

from .ReformulationImportStatements import getFutureSpec
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .SyntaxErrors import raiseSyntaxError
from .TreeHelpers import (
    buildNode,
    getKind,
    makeConstantRefNode,
    makeSequenceCreationOrConstant,
    makeStatementsSequence,
    makeStatementsSequenceFromStatements,
    makeStatementsSequenceOrStatement,
    mangleName
)


def buildExtSliceNode(provider, node, source_ref):
    elements = []

    for dim in node.slice.dims:
        dim_kind = getKind(dim)

        if dim_kind == "Slice":
            lower = buildNode(provider, dim.lower, source_ref, True)
            upper = buildNode(provider, dim.upper, source_ref, True)
            step = buildNode(provider, dim.step, source_ref, True)

            element = ExpressionBuiltinSlice(
                start      = lower,
                stop       = upper,
                step       = step,
                source_ref = source_ref
            )
        elif dim_kind == "Ellipsis":
            element = ExpressionConstantEllipsisRef(
                source_ref    = source_ref,
                user_provided = True
            )
        elif dim_kind == "Index":
            element = buildNode(
                provider   = provider,
                node       = dim.value,
                source_ref = source_ref
            )
        else:
            assert False, dim

        elements.append(element)

    return makeSequenceCreationOrConstant(
        sequence_kind = "tuple",
        elements      = elements,
        source_ref    = source_ref
    )


def buildAssignmentStatementsFromDecoded(provider, kind, detail, source,
                                         source_ref):
    # This is using many variable names on purpose, so as to give names to the
    # unpacked detail values, and has many branches due to the many cases
    # dealt with, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    if kind == "Name":
        return StatementAssignmentVariableName(
            provider      = provider,
            variable_name = detail,
            source        = source,
            source_ref    = source_ref
        )
    elif kind == "Attribute":
        lookup_source, attribute_name = detail

        return StatementAssignmentAttribute(
            expression     = lookup_source,
            attribute_name = attribute_name,
            source         = source,
            source_ref     = source_ref
        )
    elif kind == "Subscript":
        subscribed, subscript = detail

        return StatementAssignmentSubscript(
            expression = subscribed,
            subscript  = subscript,
            source     = source,
            source_ref = source_ref
        )
    elif kind == "Slice":
        lookup_source, lower, upper = detail

        # For Python3 there is no slicing operation, this is always done
        # with subscript using a slice object. For Python2, it is only done
        # if no "step" is provided.
        use_sliceobj = python_version >= 300

        if use_sliceobj:
            return StatementAssignmentSubscript(
                expression = lookup_source,
                source     = source,
                subscript  = ExpressionBuiltinSlice(
                    start      = lower,
                    stop       = upper,
                    step       = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )

        else:
            return StatementAssignmentSlice(
                expression = lookup_source,
                lower      = lower,
                upper      = upper,
                source     = source,
                source_ref = source_ref
            )
    elif kind == "Tuple":
        temp_scope = provider.allocateTempScope("tuple_unpack")

        source_iter_var = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "source_iter"
        )

        element_vars = [
            provider.allocateTempVariable(
                temp_scope = temp_scope,
                name       = "element_%d" % (
                    element_index + 1
                )
            )
            for element_index in
            range(len(detail))
        ]

        starred_list_var = None
        starred_index = None

        statements = []

        for element_index, element in enumerate(detail):
            if element[0] == "Starred":
                if starred_index is not None:
                    raiseSyntaxError(
                        "two starred expressions in assignment",
                        source_ref.atColumnNumber(0)
                    )

                starred_index = element_index

        for element_index, element in enumerate(detail):
            element_var = element_vars[element_index]

            if starred_list_var is not None:
                statements.insert(
                    starred_index+1,
                    StatementAssignmentVariable(
                        variable   = element_var,
                        source     = ExpressionListOperationPop(
                            list_arg   = ExpressionTempVariableRef(
                                variable   = starred_list_var,
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    )
                )
            elif element[0] != "Starred":
                statements.append(
                    StatementAssignmentVariable(
                        variable   = element_var,
                        source     = ExpressionSpecialUnpack(
                            value      = ExpressionTempVariableRef(
                                variable   = source_iter_var,
                                source_ref = source_ref
                            ),
                            count      = element_index + 1,
                            expected   = starred_index or len(detail),
                            starred    = starred_index is not None,

                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    )
                )
            else:
                assert starred_index == element_index
                starred_list_var = element_var

                statements.append(
                    StatementAssignmentVariable(
                        variable   = element_var,
                        source     = ExpressionBuiltinList(
                            value      = ExpressionTempVariableRef(
                                variable   = source_iter_var,
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    )
                )

        if starred_list_var is None:
            statements.append(
                StatementSpecialUnpackCheck(
                    iterator   = ExpressionTempVariableRef(
                        variable   = source_iter_var,
                        source_ref = source_ref
                    ),
                    count      = len(detail),
                    source_ref = source_ref
                )
            )
        else:
            statements.insert(
                starred_index+1,
                makeStatementConditional(
                    condition  = ExpressionComparison(
                        comparator = "Lt",
                        left       = ExpressionBuiltinLen(
                            value      = ExpressionTempVariableRef(
                                variable   = starred_list_var,
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        right      = makeConstantRefNode(
                            constant   = len(statements)-starred_index-1,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref

                    ),
                    yes_branch = makeRaiseExceptionExpressionFromTemplate(
                        exception_type = "ValueError",
                        template       = """\
not enough values to unpack (expected at least %d, got %%d)""" % (len(statements) - 1),
                        template_args  = makeBinaryOperationNode(
                            operator   = "Add",
                            left       = ExpressionBuiltinLen(
                                value      = ExpressionTempVariableRef(
                                    variable   = starred_list_var,
                                    source_ref = source_ref
                                ),
                                source_ref = source_ref
                            ),
                            right      = makeConstantRefNode(
                                constant   = starred_index,
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref     = source_ref
                    ).asStatement(),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )

        if python_version >= 370:
            iter_creation_class = ExpressionBuiltinIterForUnpack
        else:
            iter_creation_class = ExpressionBuiltinIter1

        statements = [
            StatementAssignmentVariable(
                variable   = source_iter_var,
                source     = iter_creation_class(
                    value      = source,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            makeTryFinallyStatement(
                provider   = provider,
                tried      = statements,
                final      = (
                    StatementReleaseVariable(
                        variable   = source_iter_var,
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            )
        ]

        # When all is done, copy over to the actual assignment targets, starred
        # or not makes no difference here anymore.
        for element_index, element in enumerate(detail):
            if element[0] == "Starred":
                element = element[1]

            element_var = element_vars[element_index]

            statements.append(
                buildAssignmentStatementsFromDecoded(
                    provider   = provider,
                    kind       = element[0],
                    detail     = element[1],
                    source     = ExpressionTempVariableRef(
                        variable   = element_var,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            )

            # Need to release temporary variables right after successful
            # usage.
            statements.append(
                StatementDelVariable(
                    variable   = element_var,
                    tolerant   = True,
                    source_ref = source_ref,
                )
            )

        final_statements = []

        for element_var in element_vars:
            final_statements.append(
                StatementReleaseVariable(
                    variable   = element_var,
                    source_ref = source_ref,
                )
            )

        return makeTryFinallyStatement(
            provider   = provider,
            tried      = statements,
            final      = final_statements,
            source_ref = source_ref
        )
    elif kind == "Starred":
        raiseSyntaxError(
            "starred assignment target must be in a list or tuple",
            source_ref.atColumnNumber(0)
        )
    else:
        assert False, (kind, source_ref, detail)


def buildAssignmentStatements(provider, node, source, source_ref,
                              allow_none = False, temp_provider = None):
    if node is None and allow_none:
        return None

    if temp_provider is None:
        temp_provider = provider

    kind, detail = decodeAssignTarget(
        provider   = provider,
        node       = node,
        source_ref = source_ref
    )

    return buildAssignmentStatementsFromDecoded(
        provider   = provider,
        kind       = kind,
        detail     = detail,
        source     = source,
        source_ref = source_ref
    )


def decodeAssignTarget(provider, node, source_ref, allow_none = False):
    # Many cases to deal with, because of the different assign targets,
    # pylint: disable=too-many-branches,too-many-return-statements

    if node is None and allow_none:
        return None

    if type(node) is str:
        return "Name", mangleName(node, provider)

    kind = getKind(node)

    if hasattr(node, "ctx"):
        assert getKind(node.ctx) in ("Store", "Del")

    if kind == "Name":
        return kind, mangleName(node.id, provider)
    elif kind == "Attribute":
        return kind, (
            buildNode(provider, node.value, source_ref),
            node.attr
        )
    elif kind == "Subscript":
        slice_kind = getKind(node.slice)

        if slice_kind == "Index":
            return "Subscript", (
                buildNode(provider, node.value, source_ref),
                buildNode(provider, node.slice.value, source_ref)
            )
        elif slice_kind == "Slice":
            lower = buildNode(provider, node.slice.lower, source_ref, True)
            upper = buildNode(provider, node.slice.upper, source_ref, True)

            if node.slice.step is not None:
                step = buildNode(provider, node.slice.step, source_ref)

                return "Subscript", (
                    buildNode(provider, node.value, source_ref),
                    ExpressionBuiltinSlice(
                        start      = lower,
                        stop       = upper,
                        step       = step,
                        source_ref = source_ref
                    )
                )
            else:
                return "Slice", (
                    buildNode(provider, node.value, source_ref),
                    lower,
                    upper
                )
        elif slice_kind == "ExtSlice":
            return "Subscript", (
                buildNode(provider, node.value, source_ref),
                buildExtSliceNode(provider, node, source_ref)
            )
        elif slice_kind == "Ellipsis":
            return "Subscript", (
                buildNode(provider, node.value, source_ref),
                ExpressionConstantEllipsisRef(
                    source_ref = source_ref
                )
            )
        else:
            assert False, slice_kind
    elif kind in ("Tuple", "List"):
        return "Tuple", tuple(
            decodeAssignTarget(
                provider   = provider,
                node       = sub_node,
                source_ref = source_ref,
                allow_none = False
            )
            for sub_node in
            node.elts
        )
    elif kind == "Starred":
        return "Starred", decodeAssignTarget(
            provider   = provider,
            node       = node.value,
            source_ref = source_ref,
            allow_none = False
        )
    else:
        assert False, (source_ref, kind)


def buildAssignNode(provider, node, source_ref):
    assert len(node.targets) >= 1, source_ref

    # Evaluate the right hand side first, so it can get names provided
    # before the left hand side exists.
    source = buildNode(provider, node.value, source_ref)

    if len(node.targets) == 1:
        # Simple assignment case, one source, one target.

        return buildAssignmentStatements(
            provider   = provider,
            node       = node.targets[0],
            source     = source,
            source_ref = source_ref
        )
    else:
        # Complex assignment case, one source, but multiple targets. We keep the
        # source in a temporary variable, and then assign from it multiple
        # times.

        temp_scope = provider.allocateTempScope("assign_unpack")

        tmp_source = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "assign_source"
        )

        statements = [
            StatementAssignmentVariable(
                variable   = tmp_source,
                source     = source,
                source_ref = source_ref
            )
        ]

        for target in node.targets:
            statements.append(
                buildAssignmentStatements(
                    provider   = provider,
                    node       = target,
                    source     = ExpressionTempVariableRef(
                        variable   = tmp_source,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            )

        return makeTryFinallyStatement(
            provider   = provider,
            tried      = statements,
            final      = StatementReleaseVariable(
                variable   = tmp_source,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )


def buildAnnAssignNode(provider, node, source_ref):
    """ Python3.6 annotation assignment.

    """
    # There are cases to deal with here, pylint: disable=too-many-branches

    if provider.isCompiledPythonModule() or provider.isExpressionClassBody():
        provider.markAsNeedsAnnotationsDictionary()

    # Evaluate the right hand side first, so it can get names provided
    # before the left hand side exists.
    statements = []

    if node.value is not None:
        source = buildNode(provider, node.value, source_ref)

        statements.append(
            buildAssignmentStatements(
                provider   = provider,
                node       = node.target,
                source     = source,
                source_ref = source_ref
            )
        )

        # Only name referencing annotations are effective right now.
        if statements[-1].isStatementAssignmentVariableName():
            variable_name = statements[-1].getVariableName()
        else:
            variable_name = None
    else:
        # Only name referencing annotations are effective right now.
        kind, detail = decodeAssignTarget(
            provider   = provider,
            node       = node.target,
            source_ref = source_ref
        )

        if kind == "Name":
            variable_name = detail
        else:
            variable_name = None

    # Only annotations for modules and classes are really made, for functions
    # they are ignored like comments.
    if variable_name is not None:
        if provider.isExpressionFunctionBody():
            if node.simple:
                provider.getVariableForAssignment(variable_name)
        else:
            annotation = buildNode(provider, node.annotation, source_ref)

            # TODO: As CPython core considers this implementation detail, and it seems
            # mostly useless to support having this as a closure taken name after a
            # __del__ on annotations, we might do this except in full compat mode. It
            # will produce only noise for all annotations in classes otherwise.
            if python_version < 370:
                ref_class = ExpressionVariableLocalNameRef
            else:
                ref_class = ExpressionVariableNameRef

            statements.append(
                StatementAssignmentSubscript(
                    expression = ref_class(
                        provider      = provider,
                        variable_name = "__annotations__",
                        source_ref    = source_ref
                    ),
                    subscript  = makeConstantRefNode(
                        constant   = variable_name,
                        source_ref = source_ref
                    ),
                    source     = annotation,
                    source_ref = source_ref
                )
            )

    return makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )


def buildDeleteStatementFromDecoded(provider, kind, detail, source_ref):
    if kind in ("Name", "Name_Exception"):
        # Note: Name_Exception is a "del" for exception handlers that doesn't
        # insist on the variable being defined, user code may do it too, and
        # that will be fine, so make that tolerant.
        return StatementDelVariableName(
            provider      = provider,
            variable_name = detail,
            tolerant      = kind == "Name_Exception",
            source_ref    = source_ref
        )
    elif kind == "Attribute":
        lookup_source, attribute_name = detail

        return StatementDelAttribute(
            expression     = lookup_source,
            attribute_name = attribute_name,
            source_ref     = source_ref
        )
    elif kind == "Subscript":
        subscribed, subscript = detail

        return StatementDelSubscript(
            expression = subscribed,
            subscript  = subscript,
            source_ref = source_ref
        )
    elif kind == "Slice":
        lookup_source, lower, upper = detail

        use_sliceobj = python_version >= 300

        if use_sliceobj:
            return StatementDelSubscript(
                expression = lookup_source,
                subscript  = ExpressionBuiltinSlice(
                    start      = lower,
                    stop       = upper,
                    step       = None,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            return StatementDelSlice(
                expression = lookup_source,
                lower      = lower,
                upper      = upper,
                source_ref = source_ref
            )
    elif kind == "Tuple":
        result = []

        for sub_node in detail:
            result.append(
                buildDeleteStatementFromDecoded(
                    provider   = provider,
                    kind       = sub_node[0],
                    detail     = sub_node[1],
                    source_ref = source_ref
                )
            )

        return makeStatementsSequenceOrStatement(
            statements = result,
            source_ref = source_ref
        )
    else:
        assert False, (kind, detail, source_ref)


def buildDeleteNode(provider, node, source_ref):
    # Build "del" statements.

    # Note: Each delete is sequential. It can succeed, and the failure of a
    # later one does not prevent the former to succeed. We can therefore have a
    # simple sequence of "del" statements that each only delete one thing
    # therefore. In output tree "del" therefore only ever has single arguments.

    statements = []

    for target in node.targets:
        kind, detail = decodeAssignTarget(
            provider   = provider,
            node       = target,
            source_ref = source_ref
        )

        statements.append(
            buildDeleteStatementFromDecoded(
                provider   = provider,
                kind       = kind,
                detail     = detail,
                source_ref = source_ref
            )
        )

    return makeStatementsSequenceOrStatement(
        statements = statements,
        source_ref = source_ref
    )


def _buildInplaceAssignVariableNode(provider, variable_name, operator,
                                    expression, source_ref):
    inplace_node = makeExpressionOperationBinaryInplace(
        operator   = operator,
        left       = ExpressionVariableNameRef(
            provider      = provider,
            variable_name = variable_name,
            source_ref    = source_ref
        ),
        right      = expression,
        source_ref = source_ref
    )

    inplace_node.markAsInplaceSuspect()

    return (
        StatementAssignmentVariableName(
            provider      = provider,
            variable_name = variable_name,
            source        = inplace_node,
            source_ref    = source_ref
        ),
    )


def _buildInplaceAssignAttributeNode(provider, lookup_source, attribute_name,
                                     tmp_variable1, tmp_variable2, operator,
                                     expression, source_ref):
    # First assign the target value to a temporary variable.
    preserve_to_tmp = StatementAssignmentVariable(
        variable   = tmp_variable1,
        source     = ExpressionAttributeLookup(
            source         = lookup_source.makeClone(),
            attribute_name = attribute_name,
            source_ref     = source_ref
        ),
        source_ref = source_ref
    )

    # Second assign the in-place result to a temporary variable
    inplace_to_tmp = StatementAssignmentVariable(
        variable   = tmp_variable2,
        source     = makeExpressionOperationBinaryInplace(
            operator   = operator,
            left       = ExpressionTempVariableRef(
                variable   = tmp_variable1,
                source_ref = source_ref
            ),
            right      = expression,
            source_ref = source_ref
        ),
        source_ref = source_ref
    )

    # Third, copy it back.
    copy_back_from_tmp = makeTryFinallyStatement(
        provider   = provider,
        tried      = StatementAssignmentAttribute(
            expression     = lookup_source.makeClone(),
            attribute_name = attribute_name,
            source         = ExpressionTempVariableRef(
                variable   = tmp_variable2,
                source_ref = source_ref
            ),
            source_ref     = source_ref
        ),
        final      = StatementReleaseVariable(
            variable   = tmp_variable2,
            source_ref = source_ref
        ),
        source_ref = source_ref
    )

    return (
        preserve_to_tmp,
        # making sure the above temporary variable is deleted in any case.
        makeTryFinallyStatement(
            provider   = provider,
            tried      = (
                inplace_to_tmp,
                copy_back_from_tmp,
            ),
            final      = StatementReleaseVariable(
                variable   = tmp_variable1,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )


def _buildInplaceAssignSubscriptNode(provider, subscribed, subscript,
                                     tmp_variable1, tmp_variable2, operator,
                                     expression, source_ref):
    # First assign the subscribed value to a temporary variable.
    preserve_to_tmp1 = StatementAssignmentVariable(
        variable   = tmp_variable1,
        source     = subscribed,
        source_ref = source_ref
    )
    # Second assign the subscript value to a temporary variable
    preserve_to_tmp2  = StatementAssignmentVariable(
        variable   = tmp_variable2,
        source     = subscript,
        source_ref = source_ref
    )

    execute_in_place = StatementAssignmentSubscript(
        expression = ExpressionTempVariableRef(
            variable   = tmp_variable1,
            source_ref = source_ref
        ),
        subscript  = ExpressionTempVariableRef(
            variable   = tmp_variable2,
            source_ref = source_ref
        ),
        source     = makeExpressionOperationBinaryInplace(
            operator   = operator,
            left       = ExpressionSubscriptLookup(
                subscribed = ExpressionTempVariableRef(
                    variable   = tmp_variable1,
                    source_ref = source_ref
                ),
                subscript  = ExpressionTempVariableRef(
                    variable   = tmp_variable2,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            right      = expression,
            source_ref = source_ref
        ),
        source_ref = source_ref
    )

    # Note: No copy back is happening, for subscripts that is implied.

    return (
        preserve_to_tmp1,
        makeTryFinallyStatement(
            provider   = provider,
            tried      = (
                preserve_to_tmp2,
                execute_in_place,
            ),
            final      = (
                StatementReleaseVariable(
                    variable   = tmp_variable1,
                    source_ref = source_ref
                ),
                StatementReleaseVariable(
                    variable   = tmp_variable2,
                    source_ref = source_ref
                )
            ),
            source_ref = source_ref
        )
    )


def _buildInplaceAssignSliceNode(provider, lookup_source, lower, upper,
                                 tmp_variable1, tmp_variable2, tmp_variable3,
                                 operator, expression, source_ref):

    # Due to the 3 inputs, which we need to also put into temporary variables,
    # there are too many variables here, but they are needed.
    # pylint: disable=too-many-locals

    # First assign the target value, lower and upper to temporary variables.
    copy_to_tmp = StatementAssignmentVariable(
        variable   = tmp_variable1,
        source     = lookup_source,
        source_ref = source_ref
    )

    final_statements = [
        StatementReleaseVariable(
            variable   = tmp_variable1,
            source_ref = source_ref
        )
    ]
    statements = []

    if lower is not None:
        statements.append(
            StatementAssignmentVariable(
                variable   = tmp_variable2,
                source     = lower,
                source_ref = source_ref
            )
        )
        final_statements.append(
            StatementReleaseVariable(
                variable   = tmp_variable2,
                source_ref = source_ref
            )
        )

        lower_ref1 = ExpressionTempVariableRef(
            variable   = tmp_variable2,
            source_ref = source_ref
        )
        lower_ref2 = ExpressionTempVariableRef(
            variable   = tmp_variable2,
            source_ref = source_ref
        )
    else:
        assert tmp_variable2 is None

        lower_ref1 = lower_ref2 = None

    if upper is not None:
        statements.append(
            StatementAssignmentVariable(
                variable   = tmp_variable3,
                source     = upper,
                source_ref = source_ref
            )
        )
        final_statements.append(
            StatementReleaseVariable(
                variable   = tmp_variable3,
                source_ref = source_ref
            )
        )

        upper_ref1 = ExpressionTempVariableRef(
            variable   = tmp_variable3,
            source_ref = source_ref
        )
        upper_ref2 = ExpressionTempVariableRef(
            variable   = tmp_variable3,
            source_ref = source_ref
        )
    else:
        assert tmp_variable3 is None

        upper_ref1 = upper_ref2 = None

    use_sliceobj = python_version >= 300

        # Second assign the in-place result over the original value.
    if use_sliceobj:
        statements.append(
            StatementAssignmentSubscript(
                expression = ExpressionTempVariableRef(
                    variable   = tmp_variable1,
                    source_ref = source_ref
                ),
                subscript  = ExpressionBuiltinSlice(
                    start      = lower_ref1,
                    stop       = upper_ref1,
                    step       = None,
                    source_ref = source_ref
                ),
                source     = makeExpressionOperationBinaryInplace(
                    operator   = operator,
                    left       = ExpressionSubscriptLookup(
                        subscribed = ExpressionTempVariableRef(
                            variable   = tmp_variable1,
                            source_ref = source_ref
                        ),
                        subscript  = ExpressionBuiltinSlice(
                            start      = lower_ref2,
                            stop       = upper_ref2,
                            step       = None,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    right      = expression,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )
    else:
        statements.append(
            StatementAssignmentSlice(
                expression = ExpressionTempVariableRef(
                    variable   = tmp_variable1,
                    source_ref = source_ref
                ),
                lower      = lower_ref1,
                upper      = upper_ref1,
                source     = makeExpressionOperationBinaryInplace(
                    operator   = operator,
                    left       = ExpressionSliceLookup(
                        expression = ExpressionTempVariableRef(
                            variable   = tmp_variable1,
                            source_ref = source_ref
                        ),
                        lower      = lower_ref2,
                        upper      = upper_ref2,
                        source_ref = source_ref
                    ),
                    right      = expression,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

    return (
        copy_to_tmp,
        makeTryFinallyStatement(
            provider   = provider,
            tried      = statements,
            final      = final_statements,
            source_ref = source_ref
        )
    )


def buildInplaceAssignNode(provider, node, source_ref):
    # There are many inplace assignment variables, and the detail is unpacked
    # into names, so we end up with a lot of variables, which is on purpose,
    # pylint: disable=too-many-locals

    operator = getKind(node.op)

    if operator == "Div" and getFutureSpec().isFutureDivision():
        operator = "TrueDiv"

    operator = 'I' + operator

    expression = buildNode(provider, node.value, source_ref)

    kind, detail = decodeAssignTarget(
        provider   = provider,
        node       = node.target,
        source_ref = source_ref
    )

    if kind == "Name":
        statements = _buildInplaceAssignVariableNode(
            provider      = provider,
            variable_name = detail,
            operator      = operator,
            expression    = expression,
            source_ref    = source_ref
        )
    elif kind == "Attribute":
        lookup_source, attribute_name = detail

        temp_scope = provider.allocateTempScope("inplace_assign_attr")

        tmp_variable1 = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "start"
        )
        tmp_variable2 = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "end"
        )

        statements = _buildInplaceAssignAttributeNode(
            provider       = provider,
            lookup_source  = lookup_source,
            attribute_name = attribute_name,
            tmp_variable1  = tmp_variable1,
            tmp_variable2  = tmp_variable2,
            operator       = operator,
            expression     = expression,
            source_ref     = source_ref
        )
    elif kind == "Subscript":
        subscribed, subscript = detail

        temp_scope = provider.allocateTempScope("inplace_assign_subscr")

        tmp_variable1 = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "target"
        )
        tmp_variable2 = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "subscript"
        )

        statements = _buildInplaceAssignSubscriptNode(
            provider      = provider,
            subscribed    = subscribed,
            subscript     = subscript,
            tmp_variable1 = tmp_variable1,
            tmp_variable2 = tmp_variable2,
            operator      = operator,
            expression    = expression,
            source_ref    = source_ref
        )
    elif kind == "Slice":
        lookup_source, lower, upper = detail

        temp_scope = provider.allocateTempScope("inplace_assign_slice")

        tmp_variable1 = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "target"
        )
        if lower is not None:
            tmp_variable2 = provider.allocateTempVariable(
                temp_scope = temp_scope,
                name       = "lower"
            )
        else:
            tmp_variable2 = None

        if upper is not None:
            tmp_variable3 = provider.allocateTempVariable(
                temp_scope = temp_scope,
                name       = "upper"
            )
        else:
            tmp_variable3 = None

        statements = _buildInplaceAssignSliceNode(
            provider      = provider,
            lookup_source = lookup_source,
            lower         = lower,
            upper         = upper,
            tmp_variable1 = tmp_variable1,
            tmp_variable2 = tmp_variable2,
            tmp_variable3 = tmp_variable3,
            operator      = operator,
            expression    = expression,
            source_ref    = source_ref
        )
    else:
        assert False, kind

    return makeStatementsSequenceFromStatements(
        *statements
    )
