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
""" Reformulation of sequence creations.

Sequences might be directly translated to constants, or they might become
nodes that build tuples, lists, or sets.

For Python3.5, unpacking can happen while creating sequences, these are
being re-formulated to an internal function.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinNext1
)
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinTuple
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.ContainerOperationNodes import (
    ExpressionListOperationExtend,
    ExpressionSetOperationUpdate
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.ParameterSpecs import ParameterSpec
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef
)
from nuitka.PythonVersions import python_version

from . import SyntaxErrors
from .Helpers import (
    buildNode,
    buildNodeList,
    getKind,
    makeSequenceCreationOrConstant,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements
)
from .InternalModule import (
    getInternalModule,
    internal_source_ref,
    once_decorator
)
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def buildSequenceCreationNode(provider, node, source_ref):
    if python_version >= 300:
        for element in node.elts:
            if getKind(element) == "Starred":
                if python_version < 350:
                    SyntaxErrors.raiseSyntaxError(
                        reason     = """\
can use starred expression only as assignment target""",
                        source_ref = source_ref,
                        col_offset = element.col_offset
                    )
                else:
                    return _buildSequenceUnpacking(
                        provider   = provider,
                        node       = node,
                        source_ref = source_ref
                    )

    return makeSequenceCreationOrConstant(
        sequence_kind = getKind(node).upper(),
        elements      = buildNodeList(provider, node.elts, source_ref),
        source_ref    = source_ref
    )



@once_decorator
def getListUnpackingHelper():
    helper_name = "_unpack_list"

    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = (),
            list_star_arg = "args",
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        flags      = set(),
        source_ref = internal_source_ref
    )

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(temp_scope, "list")
    tmp_iter_variable = result.allocateTempVariable(temp_scope, "iter")
    tmp_item_variable = result.allocateTempVariable(temp_scope, "keys")

    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried          = StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_item_variable,
                    source_ref = internal_source_ref
                ),
                source       = ExpressionBuiltinNext1(
                    value      = ExpressionTempVariableRef(
                        variable   = tmp_iter_variable,
                        source_ref = internal_source_ref
                    ),
                    source_ref = internal_source_ref
                ),
                source_ref   = internal_source_ref
            ),
            exception_name = "StopIteration",
            handler_body   = StatementLoopBreak(
                source_ref = internal_source_ref
            ),
            source_ref     = internal_source_ref
        ),
        StatementExpressionOnly(
            expression = ExpressionListOperationExtend(
                list_arg   = ExpressionTempVariableRef(
                    variable   = tmp_result_variable,
                    source_ref = internal_source_ref
                ),
                value      = ExpressionTempVariableRef(
                    variable   = tmp_item_variable,
                    source_ref = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        )
    )

    args_variable = result.getVariableForAssignment(
        variable_name = "args"
    )

    final = (
        StatementReleaseVariable(
            variable   = tmp_result_variable,
            source_ref = internal_source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_iter_variable,
            source_ref = internal_source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_item_variable,
            source_ref = internal_source_ref
        ),
    )

    tried = makeStatementsSequenceFromStatements(
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable,
                source_ref = internal_source_ref
            ),
            source       = ExpressionBuiltinIter1(
                value      = ExpressionVariableRef(
                    variable_name = "args",
                    variable      = args_variable,
                    source_ref    = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            source_ref   = internal_source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_result_variable,
                source_ref = internal_source_ref
            ),
            source       = ExpressionConstantRef(
                constant   = [],
                source_ref = internal_source_ref
            ),
            source_ref   = internal_source_ref
        ),
        StatementLoop(
            body       = loop_body,
            source_ref = internal_source_ref
        ),
        StatementReturn(
            expression = ExpressionTempVariableRef(
                variable   = tmp_result_variable,
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        )
    )

    result.setBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyStatement(
                provider   = result,
                tried      = tried,
                final      = final,
                source_ref = internal_source_ref
            )
        )
    )

    return result


@once_decorator
def getSetUnpackingHelper():
    helper_name = "_unpack_set"

    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = (),
            list_star_arg = "args",
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        flags      = set(),
        source_ref = internal_source_ref
    )

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(temp_scope, "set")
    tmp_iter_variable = result.allocateTempVariable(temp_scope, "iter")
    tmp_item_variable = result.allocateTempVariable(temp_scope, "keys")

    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried          = StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_item_variable,
                    source_ref = internal_source_ref
                ),
                source       = ExpressionBuiltinNext1(
                    value      = ExpressionTempVariableRef(
                        variable   = tmp_iter_variable,
                        source_ref = internal_source_ref
                    ),
                    source_ref = internal_source_ref
                ),
                source_ref   = internal_source_ref
            ),
            exception_name = "StopIteration",
            handler_body   = StatementLoopBreak(
                source_ref = internal_source_ref
            ),
            source_ref     = internal_source_ref
        ),
        StatementExpressionOnly(
            expression = ExpressionSetOperationUpdate(
                set_arg    = ExpressionTempVariableRef(
                    variable   = tmp_result_variable,
                    source_ref = internal_source_ref
                ),
                value      = ExpressionTempVariableRef(
                    variable   = tmp_item_variable,
                    source_ref = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        )
    )

    args_variable = result.getVariableForAssignment(
        variable_name = "args"
    )

    final = (
        StatementReleaseVariable(
            variable   = tmp_result_variable,
            source_ref = internal_source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_iter_variable,
            source_ref = internal_source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_item_variable,
            source_ref = internal_source_ref
        ),
    )

    tried = makeStatementsSequenceFromStatements(
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable,
                source_ref = internal_source_ref
            ),
            source       = ExpressionBuiltinIter1(
                value      = ExpressionVariableRef(
                    variable_name = "args",
                    variable      = args_variable,
                    source_ref    = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            source_ref   = internal_source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_result_variable,
                source_ref = internal_source_ref
            ),
            source       = ExpressionConstantRef(
                constant   = set(),
                source_ref = internal_source_ref
            ),
            source_ref   = internal_source_ref
        ),
        StatementLoop(
            body       = loop_body,
            source_ref = internal_source_ref
        ),
        StatementReturn(
            expression = ExpressionTempVariableRef(
                variable   = tmp_result_variable,
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        )
    )

    result.setBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyStatement(
                provider   = result,
                tried      = tried,
                final      = final,
                source_ref = internal_source_ref
            )
        )
    )

    return result


def buildListUnpacking(provider, elements, source_ref):
    helper_args = []

    for element in elements:

        # TODO: We could be a lot cleverer about the tuples for non-starred
        # arguments, but lets get this to work first.
        if getKind(element) == "Starred":
            helper_args.append(
                buildNode(provider, element.value, source_ref),
            )
        else:
            helper_args.append(
                ExpressionMakeTuple(
                    elements   = (
                        buildNode(provider, element, source_ref),
                    ),
                    source_ref = source_ref
                )
            )

    result = ExpressionFunctionCall(
        function   = ExpressionFunctionCreation(
            function_ref = ExpressionFunctionRef(
                function_body = getListUnpackingHelper(),
                source_ref    = source_ref
            ),
            code_object  = None,
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (
            ExpressionMakeTuple(
                helper_args,
                source_ref
            ),
        ),
        source_ref = source_ref,
    )

    result.setCompatibleSourceReference(helper_args[-1].getCompatibleSourceReference())

    return result


def _buildTupleUnpacking(provider, elements, source_ref):
    return ExpressionBuiltinTuple(
        value      = buildListUnpacking(provider, elements, source_ref),
        source_ref = source_ref
    )


def _buildSetUnpacking(provider, elements, source_ref):
    helper_args = []

    for element in elements:

        # TODO: We could be a lot cleverer about the tuples for non-starred
        # arguments, but lets get this to work first.
        if getKind(element) == "Starred":
            helper_args.append(
                buildNode(provider, element.value, source_ref),
            )
        else:
            helper_args.append(
                ExpressionMakeTuple(
                    elements   = (
                        buildNode(provider, element, source_ref),
                    ),
                    source_ref = source_ref
                )
            )

    result = ExpressionFunctionCall(
        function   = ExpressionFunctionCreation(
            function_ref = ExpressionFunctionRef(
                function_body = getSetUnpackingHelper(),
                source_ref    = source_ref
            ),
            code_object  = None,
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (
            ExpressionMakeTuple(
                helper_args,
                source_ref
            ),
        ),
        source_ref = source_ref,
    )

    result.setCompatibleSourceReference(helper_args[-1].getCompatibleSourceReference())

    return result

def _buildSequenceUnpacking(provider, node, source_ref):
    kind = getKind(node)

    if kind == "List":
        return buildListUnpacking(provider, node.elts, source_ref)
    elif kind == "Tuple":
        return _buildTupleUnpacking(provider, node.elts, source_ref)
    elif kind == "Set":
        return _buildSetUnpacking(provider, node.elts, source_ref)
    else:
        assert False, kind
