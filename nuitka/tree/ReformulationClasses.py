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
""" Reformulation of class statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTargetVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeLookup,
    ExpressionBuiltinHasattr
)
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinRef
from nuitka.nodes.CallNodes import ExpressionCall, ExpressionCallNoKeywords
from nuitka.nodes.ClassNodes import (
    ExpressionClassBody,
    ExpressionSelectMetaclass
)
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIn
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    StatementConditional
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.DictionaryNodes import (
    ExpressionDictOperationGet,
    StatementDictOperationRemove
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionQualnameRef,
    ExpressionFunctionRef
)
from nuitka.nodes.GlobalsLocalsNodes import (
    ExpressionBuiltinLocals,
    StatementSetLocals
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.SubscriptNodes import ExpressionSubscriptLookup
from nuitka.nodes.TypeNodes import ExpressionBuiltinType1
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef
)
from nuitka.PythonVersions import python_version

from .Helpers import (
    buildNode,
    buildNodeList,
    buildStatementsNode,
    extractDocFromBody,
    getKind,
    makeDictCreationOrConstant,
    makeSequenceCreationOrConstant,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement
)
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def _buildClassNode3(provider, node, source_ref):
    # Many variables, due to the huge re-formulation that is going on here,
    # which just has the complexity, pylint: disable=R0914

    # This function is the Python3 special case with special re-formulation as
    # according to developer manual.
    class_statement_nodes, class_doc = extractDocFromBody(node)

    # We need a scope for the temporary variables, and they might be closured.
    temp_scope = provider.allocateTempScope(
        name          = "class_creation",
        allow_closure = True
    )

    tmp_bases = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "bases"
    )
    tmp_class_decl_dict = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "class_decl_dict"
    )
    tmp_metaclass = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "metaclass"
    )
    tmp_prepared = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "prepared"
    )

    class_creation_function = ExpressionClassBody(
        provider   = provider,
        name       = node.name,
        doc        = class_doc,
        flags      = set(),
        source_ref = source_ref
    )

    if python_version >= 340 and False: # TODO: Temporarily reverted:
        tmp_class = class_creation_function.allocateTempVariable(
            temp_scope = None,
            name       = "__class__"
        )

        class_target_variable_ref = ExpressionTargetTempVariableRef(
            variable   = tmp_class,
            source_ref = source_ref
        )
        class_variable_ref = ExpressionTempVariableRef(
            variable   = tmp_class,
            source_ref = source_ref
        )
    else:
        class_variable = class_creation_function.getVariableForAssignment(
            "__class__"
        )

        class_target_variable_ref = ExpressionTargetVariableRef(
            variable_name = "__class__",
            variable      = class_variable,
            source_ref    = source_ref
        )
        class_variable_ref = ExpressionVariableRef(
            variable_name = "__class__",
            variable      = class_variable,
            source_ref    = source_ref
        )

    code_object = CodeObjectSpec(
        code_name     = node.name,
        code_kind     = "Class",
        arg_names     = (),
        kw_only_count = 0,
        has_starlist  = False,
        has_stardict  = False
    )

    body = buildStatementsNode(
        provider    = class_creation_function,
        nodes       = class_statement_nodes,
        code_object = code_object,
        source_ref  = source_ref
    )

    source_ref_orig = source_ref

    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref

    module_variable = class_creation_function.getVariableForAssignment(
        "__module__"
    )

    statements = [
        StatementSetLocals(
            new_locals = ExpressionTempVariableRef(
                variable   = tmp_prepared,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetVariableRef(
                variable_name = "__module__",
                variable      = module_variable,
                source_ref    = source_ref
            ),
            source       = ExpressionConstantRef(
                constant      = provider.getParentModule().getFullName(),
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref   = source_ref
        )
    ]

    if class_doc is not None:
        doc_variable = class_creation_function.getVariableForAssignment(
            "__doc__"
        )

        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__doc__",
                    variable      = doc_variable,
                    source_ref    = source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = class_doc,
                    source_ref    = source_ref,
                    user_provided = True
                ),
                source_ref   = source_ref
            )
        )

    # The "__qualname__" attribute is new in Python 3.3.
    if python_version >= 330:
        qualname = class_creation_function.getFunctionQualname()
        qualname_variable = class_creation_function.getVariableForAssignment(
            "__qualname__"
        )

        if python_version < 340:
            qualname_ref = ExpressionConstantRef(
                constant      = qualname,
                source_ref    = source_ref,
                user_provided = True
            )
        else:
            qualname_ref = ExpressionFunctionQualnameRef(
                function_body = class_creation_function,
                source_ref    = source_ref,
            )

        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__qualname__",
                    variable      = qualname_variable,
                    source_ref    = source_ref
                ),
                source       = qualname_ref,
                source_ref   = source_ref
            )
        )

        if python_version >= 340:
            qualname_assign = statements[-1]

    statements += [
        body,
        StatementAssignmentVariable(
            variable_ref = class_target_variable_ref,
            source       = ExpressionCall(
                called     = ExpressionTempVariableRef(
                    variable   = tmp_metaclass,
                    source_ref = source_ref
                ),
                args       = makeSequenceCreationOrConstant(
                    sequence_kind = "tuple",
                    elements      = (
                        ExpressionConstantRef(
                            constant      = node.name,
                            source_ref    = source_ref,
                            user_provided = True
                        ),
                        ExpressionTempVariableRef(
                            variable   = tmp_bases,
                            source_ref = source_ref
                        ),
                        ExpressionBuiltinLocals(
                            source_ref = source_ref
                        )
                    ),
                    source_ref    = source_ref
                ),
                kw         = ExpressionTempVariableRef(
                    variable   = tmp_class_decl_dict,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementReturn(
            expression = class_variable_ref,
            source_ref = source_ref
        )
    ]

    body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    # The class body is basically a function that implicitly, at the end
    # returns its locals and cannot have other return statements contained.

    class_creation_function.setBody(body)

    class_creation_function.registerProvidedVariable(tmp_bases)
    class_creation_function.registerProvidedVariable(tmp_class_decl_dict)
    class_creation_function.registerProvidedVariable(tmp_metaclass)
    class_creation_function.registerProvidedVariable(tmp_prepared)

    # The class body is basically a function that implicitly, at the end
    # returns its created class and cannot have other return statements
    # contained.

    decorated_body = ExpressionFunctionCall(
        function   = ExpressionFunctionCreation(
            function_ref = ExpressionFunctionRef(
                function_body = class_creation_function,
                source_ref    = source_ref
            ),
            code_object  = code_object,
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (),
        source_ref = source_ref
    )

    for decorator in buildNodeList(
            provider,
            reversed(node.decorator_list),
            source_ref
        ):
        decorated_body = ExpressionCallNoKeywords(
            called     = decorator,
            args       = ExpressionMakeTuple(
                elements   = (
                    decorated_body,
                ),
                source_ref = source_ref
            ),
            source_ref = decorator.getSourceReference()
        )

    statements = (
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_bases,
                source_ref = source_ref
            ),
            source       = makeSequenceCreationOrConstant(
                sequence_kind = "tuple",
                elements      = buildNodeList(
                    provider, node.bases, source_ref
                ),
                source_ref    = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_class_decl_dict,
                source_ref = source_ref
            ),
            source       = makeDictCreationOrConstant(
                keys       = [
                    ExpressionConstantRef(
                        constant      = keyword.arg,
                        source_ref    = source_ref,
                        user_provided = True
                    )
                    for keyword in
                    node.keywords
                ],
                values     = [
                    buildNode(provider, keyword.value, source_ref)
                    for keyword in
                    node.keywords
                ],
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_metaclass,
                source_ref = source_ref
            ),
            source       = ExpressionSelectMetaclass(
                metaclass  = ExpressionConditional(
                    condition      = ExpressionComparisonIn(
                        left       = ExpressionConstantRef(
                            constant      = "metaclass",
                            source_ref    = source_ref,
                            user_provided = True
                        ),
                        right      = ExpressionTempVariableRef(
                            variable   = tmp_class_decl_dict,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    expression_yes = ExpressionDictOperationGet(
                        dict_arg   = ExpressionTempVariableRef(
                            variable   = tmp_class_decl_dict,
                            source_ref = source_ref
                        ),
                        key        = ExpressionConstantRef(
                            constant      = "metaclass",
                            source_ref    = source_ref,
                            user_provided = True
                        ),
                        source_ref = source_ref
                    ),
                    expression_no  = ExpressionConditional(
                        condition      = ExpressionTempVariableRef(
                            variable   = tmp_bases,
                            source_ref = source_ref
                        ),
                        expression_no  = ExpressionBuiltinRef(
                            builtin_name = "type",
                            source_ref   = source_ref
                        ),
                        expression_yes = ExpressionBuiltinType1(
                            value      = ExpressionSubscriptLookup(
                                subscribed = ExpressionTempVariableRef(
                                    variable   = tmp_bases,
                                    source_ref = source_ref
                                ),
                                subscript  = ExpressionConstantRef(
                                    constant      = 0,
                                    source_ref    = source_ref,
                                    user_provided = True
                                ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref     = source_ref
                    ),
                    source_ref     = source_ref
                ),
                bases      = ExpressionTempVariableRef(
                    variable   = tmp_bases,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref   = source_ref_orig
        ),
        StatementConditional(
            condition  = ExpressionComparisonIn(
                left       = ExpressionConstantRef(
                    constant      = "metaclass",
                    source_ref    = source_ref,
                    user_provided = True
                ),
                right      = ExpressionTempVariableRef(
                    variable   = tmp_class_decl_dict,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            no_branch  = None,
            yes_branch = makeStatementsSequenceFromStatement(
                statement = StatementDictOperationRemove(
                    dict_arg   = ExpressionTempVariableRef(
                        variable   = tmp_class_decl_dict,
                        source_ref = source_ref
                    ),
                    key        = ExpressionConstantRef(
                        constant      = "metaclass",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    source_ref = source_ref
                )
            ),
            source_ref = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_prepared,
                source_ref = source_ref
            ),
            source       = ExpressionConditional(
                condition      = ExpressionBuiltinHasattr( # pylint: disable=E1120,E1123
                    object     = ExpressionTempVariableRef(
                        variable   = tmp_metaclass,
                        source_ref = source_ref
                    ),
                    name       = ExpressionConstantRef(
                        constant      = "__prepare__",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    source_ref = source_ref
                ),
                expression_no  = ExpressionConstantRef(
                    constant      = {},
                    source_ref    = source_ref,
                    user_provided = True
                ),
                expression_yes = ExpressionCall(
                    called     = ExpressionAttributeLookup(
                        source         = ExpressionTempVariableRef(
                            variable   = tmp_metaclass,
                            source_ref = source_ref
                        ),
                        attribute_name = "__prepare__",
                        source_ref     = source_ref
                    ),
                    args       = ExpressionMakeTuple(
                        elements   = (
                            ExpressionConstantRef(
                                constant      = node.name,
                                source_ref    = source_ref,
                                user_provided = True
                            ),
                            ExpressionTempVariableRef(
                                variable   = tmp_bases,
                                source_ref = source_ref
                            )
                        ),
                        source_ref = source_ref
                    ),
                    kw         = ExpressionTempVariableRef(
                        variable   = tmp_class_decl_dict,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                source_ref     = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetVariableRef(
                variable_name = node.name,
                source_ref    = source_ref
            ),
            source       = decorated_body,
            source_ref   = source_ref
        ),
    )

    if python_version >= 340:
        class_assign = statements[-1]

        class_creation_function.qualname_setup = class_assign, qualname_assign

    final = (
        StatementReleaseVariable(
            variable   = tmp_bases,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_class_decl_dict,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_metaclass,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_prepared,
            source_ref = source_ref
        )
    )

    return makeTryFinallyStatement(
        provider   = provider,
        tried      = statements,
        final      = final,
        source_ref = source_ref
    )


def _buildClassNode2(provider, node, source_ref):
    # This function is the Python2 special case with special re-formulation as
    # according to developer manual, and it's very detailed, pylint: disable=R0914
    class_statement_nodes, class_doc = extractDocFromBody(node)

    function_body = ExpressionClassBody(
        provider   = provider,
        name       = node.name,
        doc        = class_doc,
        flags      = set(),
        source_ref = source_ref
    )

    code_object = CodeObjectSpec(
        code_name     = node.name,
        code_kind     = "Class",
        arg_names     = (),
        kw_only_count = 0,
        has_starlist  = False,
        has_stardict  = False
    )

    body = buildStatementsNode(
        provider    = function_body,
        nodes       = class_statement_nodes,
        code_object = code_object,
        source_ref  = source_ref
    )
    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref.atInternal()

    # The class body is basically a function that implicitly, at the end
    # returns its locals and cannot have other return statements contained, and
    # starts out with a variables "__module__" and potentially "__doc__" set.
    statements = [
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetVariableRef(
                variable_name = "__module__",
                source_ref    = source_ref
            ),
            source       = ExpressionConstantRef(
                constant      = provider.getParentModule().getFullName(),
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref   = source_ref.atInternal()
        )
    ]

    if class_doc is not None:
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__doc__",
                    source_ref    = source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = class_doc,
                    source_ref    = source_ref,
                    user_provided = True
                ),
                source_ref   = source_ref.atInternal()
            )
        )

    statements += [
        body,
        StatementReturn(
            expression = ExpressionBuiltinLocals(
                source_ref = source_ref
            ),
            source_ref = source_ref.atInternal()
        )
    ]

    body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    # The class body is basically a function that implicitly, at the end
    # returns its locals and cannot have other return statements contained.

    function_body.setBody(body)

    temp_scope = provider.allocateTempScope("class_creation")

    tmp_bases = provider.allocateTempVariable(temp_scope, "bases")
    tmp_class_dict = provider.allocateTempVariable(temp_scope, "class_dict")
    tmp_metaclass = provider.allocateTempVariable(temp_scope, "metaclass")
    tmp_class = provider.allocateTempVariable(temp_scope, "class")

    statements = [
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_bases,
                source_ref = source_ref
            ),
            source       = makeSequenceCreationOrConstant(
                sequence_kind = "tuple",
                elements      = buildNodeList(
                    provider, node.bases, source_ref
                ),
                source_ref    = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_class_dict,
                source_ref = source_ref
            ),
            source       =   ExpressionFunctionCall(
                function   = ExpressionFunctionCreation(
                    function_ref = ExpressionFunctionRef(
                        function_body = function_body,
                        source_ref    = source_ref
                    ),
                    code_object  = None,
                    defaults     = (),
                    kw_defaults  = None,
                    annotations  = None,
                    source_ref   = source_ref
                ),
                values     = (),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_metaclass,
                source_ref = source_ref
            ),
            source       = ExpressionConditional(
                condition      =  ExpressionComparisonIn(
                    left       = ExpressionConstantRef(
                        constant      = "__metaclass__",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    right      = ExpressionTempVariableRef(
                        variable   = tmp_class_dict,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                expression_yes = ExpressionDictOperationGet(
                    dict_arg   = ExpressionTempVariableRef(
                        variable   = tmp_class_dict,
                        source_ref = source_ref
                    ),
                    key        = ExpressionConstantRef(
                        constant      = "__metaclass__",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    source_ref = source_ref
                ),
                expression_no  = ExpressionSelectMetaclass(
                    metaclass  = None,
                    bases      = ExpressionTempVariableRef(
                        variable   = tmp_bases,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                source_ref     = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_class,
                source_ref = source_ref
            ),
            source       = ExpressionCallNoKeywords(
                called     = ExpressionTempVariableRef(
                    variable   = tmp_metaclass,
                    source_ref = source_ref
                ),
                args       = ExpressionMakeTuple(
                    elements   = (
                        ExpressionConstantRef(
                            constant      = node.name,
                            source_ref    = source_ref,
                            user_provided = True
                        ),
                        ExpressionTempVariableRef(
                            variable   = tmp_bases,
                            source_ref = source_ref
                        ),
                        ExpressionTempVariableRef(
                            variable   = tmp_class_dict,
                            source_ref = source_ref
                        )
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
    ]

    for decorator in buildNodeList(
            provider,
            reversed(node.decorator_list),
            source_ref
        ):
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_class,
                    source_ref = source_ref
                ),
                source       = ExpressionCallNoKeywords(
                    called     = decorator,
                    args       = ExpressionMakeTuple(
                        elements   = (
                            ExpressionTempVariableRef(
                                variable   = tmp_class,
                                source_ref = source_ref
                            ),
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = decorator.getSourceReference()
                ),
                source_ref   = decorator.getSourceReference()
            )
        )

    statements.append(
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetVariableRef(
                variable_name = node.name,
                source_ref    = source_ref
            ),
            source       = ExpressionTempVariableRef(
                variable   = tmp_class,
                source_ref = source_ref
            ),
            source_ref   = source_ref
        )
    )

    final = (
        StatementReleaseVariable(
            variable   = tmp_class,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_bases,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_class_dict,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_metaclass,
            source_ref = source_ref
        )
    )

    return makeTryFinallyStatement(
        provider   = function_body,
        tried      = statements,
        final      = final,
        source_ref = source_ref
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
    if python_version < 300:
        return _buildClassNode2(provider, node, source_ref)
    else:
        return _buildClassNode3(provider, node, source_ref)
