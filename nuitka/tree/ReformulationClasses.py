#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of Python2 class statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinAnonymousRef
from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.ClassNodes import ExpressionClassDictBody
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ConditionalNodes import ExpressionConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    makeExpressionMakeTuple,
    makeExpressionMakeTupleOrConstant,
)
from nuitka.nodes.DictionaryNodes import (
    ExpressionDictOperationGet2,
    ExpressionDictOperationIn,
)
from nuitka.nodes.GlobalsLocalsNodes import ExpressionBuiltinLocalsRef
from nuitka.nodes.LocalsDictNodes import (
    StatementReleaseLocals,
    StatementSetLocalsDictionary,
)
from nuitka.nodes.ModuleAttributeNodes import ExpressionModuleAttributeNameRef
from nuitka.nodes.NodeMakingHelpers import mergeStatements
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.SubscriptNodes import makeExpressionIndexLookup
from nuitka.nodes.TryNodes import StatementTry
from nuitka.nodes.TypeNodes import ExpressionBuiltinType1
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableNameNodes import (
    ExpressionVariableNameRef,
    StatementAssignmentVariableName,
)
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version

from .ReformulationClasses3 import buildClassNode3
from .ReformulationTryFinallyStatements import (
    makeTryFinallyReleaseStatement,
    makeTryFinallyStatement,
)
from .TreeHelpers import (
    buildFrameNode,
    buildNodeTuple,
    extractDocFromBody,
    getKind,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    mangleName,
)


def buildClassNode2(provider, node, source_ref):
    # This function is the Python2 special case with special re-formulation as
    # according to Developer Manual, and it's very detailed, pylint: disable=too-many-locals

    # First, allow plugins to modify the code if they want to.
    Plugins.onClassBodyParsing(provider=provider, class_name=node.name, node=node)

    class_statement_nodes, class_doc = extractDocFromBody(node)

    function_body = ExpressionClassDictBody(
        provider=provider, name=node.name, doc=class_doc, source_ref=source_ref
    )

    parent_module = provider.getParentModule()

    code_object = CodeObjectSpec(
        co_name=node.name,
        co_qualname=provider.getChildQualname(node.name),
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
        provider=function_body,
        nodes=class_statement_nodes,
        code_object=code_object,
        source_ref=source_ref,
    )

    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref.atInternal()

    locals_scope = function_body.getLocalsScope()

    # The class body is basically a function that implicitly, at the end
    # returns its locals and cannot have other return statements contained, and
    # starts out with a variables "__module__" and potentially "__doc__" set.
    statements = [
        StatementSetLocalsDictionary(locals_scope=locals_scope, source_ref=source_ref),
        StatementAssignmentVariableName(
            provider=function_body,
            variable_name="__module__",
            source=ExpressionModuleAttributeNameRef(
                variable=provider.getParentModule().getVariableForReference("__name__"),
                source_ref=source_ref,
            ),
            source_ref=source_ref.atInternal(),
        ),
    ]

    if class_doc is not None:
        statements.append(
            StatementAssignmentVariableName(
                provider=function_body,
                variable_name="__doc__",
                source=makeConstantRefNode(
                    constant=class_doc, source_ref=source_ref, user_provided=True
                ),
                source_ref=source_ref.atInternal(),
            )
        )

    statements += (
        body,
        StatementReturn(
            expression=ExpressionBuiltinLocalsRef(
                locals_scope=locals_scope, source_ref=source_ref
            ),
            source_ref=source_ref,
        ),
    )

    body = makeStatementsSequenceFromStatement(
        statement=makeTryFinallyStatement(
            provider=function_body,
            tried=mergeStatements(statements, True),
            final=StatementReleaseLocals(
                locals_scope=locals_scope, source_ref=source_ref
            ),
            source_ref=source_ref,
        )
    )

    # The class body is basically a function that implicitly, at the end
    # returns its locals and cannot have other return statements contained.

    function_body.setChildBody(body)

    temp_scope = provider.allocateTempScope("class_creation")

    tmp_bases = provider.allocateTempVariable(temp_scope, "bases", temp_type="object")
    tmp_class_dict = provider.allocateTempVariable(
        temp_scope, "class_dict", temp_type="object"
    )
    tmp_metaclass = provider.allocateTempVariable(
        temp_scope, "metaclass", temp_type="object"
    )
    tmp_class = provider.allocateTempVariable(temp_scope, "class", temp_type="object")

    select_metaclass = ExpressionOutlineBody(
        provider=provider, name="select_metaclass", body=None, source_ref=source_ref
    )

    if node.bases:
        tmp_base = select_metaclass.allocateTempVariable(
            temp_scope=None, name="base", temp_type="object"
        )

        statements = (
            makeStatementAssignmentVariable(
                variable=tmp_base,
                source=makeExpressionIndexLookup(
                    expression=ExpressionTempVariableRef(
                        variable=tmp_bases, source_ref=source_ref
                    ),
                    index_value=0,
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            ),
            makeTryFinallyReleaseStatement(
                provider,
                tried=StatementTry(
                    tried=makeStatementsSequenceFromStatement(
                        statement=StatementReturn(
                            expression=makeExpressionAttributeLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_base, source_ref=source_ref
                                ),
                                attribute_name="__class__",
                                source_ref=source_ref,
                            ),
                            source_ref=source_ref,
                        )
                    ),
                    except_handler=makeStatementsSequenceFromStatement(
                        statement=StatementReturn(
                            expression=ExpressionBuiltinType1(
                                value=ExpressionTempVariableRef(
                                    variable=tmp_base, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            source_ref=source_ref,
                        )
                    ),
                    break_handler=None,
                    continue_handler=None,
                    return_handler=None,
                    source_ref=source_ref,
                ),
                variables=(tmp_base,),
                source_ref=source_ref,
            ),
        )
    else:
        statements = (
            StatementTry(
                tried=makeStatementsSequenceFromStatement(
                    statement=StatementReturn(
                        # TODO: Should avoid checking __builtins__ for this.
                        expression=ExpressionVariableNameRef(
                            variable_name="__metaclass__",
                            provider=parent_module,
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    )
                ),
                except_handler=makeStatementsSequenceFromStatement(
                    statement=StatementReturn(
                        expression=ExpressionBuiltinAnonymousRef(
                            builtin_name="classobj", source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    )
                ),
                break_handler=None,
                continue_handler=None,
                return_handler=None,
                source_ref=source_ref,
            ),
        )

    select_metaclass.setChildBody(
        makeStatementsSequence(
            statements=statements, allow_none=False, source_ref=source_ref
        )
    )

    statements = [
        makeStatementAssignmentVariable(
            variable=tmp_bases,
            source=makeExpressionMakeTupleOrConstant(
                elements=buildNodeTuple(
                    provider=provider, nodes=node.bases, source_ref=source_ref
                ),
                user_provided=True,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_class_dict, source=function_body, source_ref=source_ref
        ),
        makeStatementAssignmentVariable(
            variable=tmp_metaclass,
            source=ExpressionConditional(
                condition=ExpressionDictOperationIn(
                    key=makeConstantRefNode(
                        constant="__metaclass__",
                        source_ref=source_ref,
                        user_provided=True,
                    ),
                    dict_arg=ExpressionTempVariableRef(
                        variable=tmp_class_dict, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                expression_yes=ExpressionDictOperationGet2(
                    dict_arg=ExpressionTempVariableRef(
                        variable=tmp_class_dict, source_ref=source_ref
                    ),
                    key=makeConstantRefNode(
                        constant="__metaclass__",
                        source_ref=source_ref,
                        user_provided=True,
                    ),
                    source_ref=source_ref,
                ),
                expression_no=select_metaclass,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_class,
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
                        ExpressionTempVariableRef(
                            variable=tmp_bases, source_ref=source_ref
                        ),
                        ExpressionTempVariableRef(
                            variable=tmp_class_dict, source_ref=source_ref
                        ),
                    ),
                    source_ref=source_ref,
                ),
                kw=None,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
    ]

    for decorator in buildNodeTuple(
        provider, reversed(node.decorator_list), source_ref
    ):
        statements.append(
            makeStatementAssignmentVariable(
                variable=tmp_class,
                source=makeExpressionCall(
                    called=decorator,
                    args=makeExpressionMakeTuple(
                        elements=(
                            ExpressionTempVariableRef(
                                variable=tmp_class, source_ref=source_ref
                            ),
                        ),
                        source_ref=source_ref,
                    ),
                    kw=None,
                    source_ref=decorator.getSourceReference(),
                ),
                source_ref=decorator.getSourceReference(),
            )
        )

    statements.append(
        StatementAssignmentVariableName(
            provider=provider,
            variable_name=mangleName(node.name, provider),
            source=ExpressionTempVariableRef(variable=tmp_class, source_ref=source_ref),
            source_ref=source_ref,
        )
    )

    return makeTryFinallyReleaseStatement(
        provider=function_body,
        tried=statements,
        variables=(tmp_class, tmp_bases, tmp_class_dict, tmp_metaclass),
        source_ref=source_ref,
    )


def buildClassNode(provider, node, source_ref):
    assert getKind(node) == "ClassDef"

    # There appears to be a inconsistency with the top level line number
    # not being the one really the class has, if there are bases, and a
    # decorator.
    if node.bases:
        source_ref = source_ref.atLineNumber(node.bases[-1].lineno)

    # Python2 and Python3 are similar, but fundamentally different, so handle
    # them in dedicated code.
    if python_version < 0x300:
        return buildClassNode2(provider, node, source_ref)
    else:
        return buildClassNode3(provider, node, source_ref)


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
