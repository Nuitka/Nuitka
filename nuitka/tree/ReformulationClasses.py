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
""" Reformulation of classes

Consult the developmer manual for information. TODO: Add ability to sync source code
comments with developer manual sections.

"""

from nuitka.nodes.VariableRefNode import (
    CPythonExpressionTargetVariableRef,
    CPythonExpressionVariableRef,
    CPythonExpressionTempVariableRef,
    CPythonStatementTempBlock
)
from nuitka.nodes.ConstantRefNode import CPythonExpressionConstantRef
from nuitka.nodes.BuiltinReferenceNodes import CPythonExpressionBuiltinRef
from nuitka.nodes.ComparisonNode import CPythonExpressionComparison

from nuitka.nodes.CallNode import (
    CPythonExpressionCallNoKeywords,
    CPythonExpressionCall
)
from nuitka.nodes.TypeNode import CPythonExpressionBuiltinType1
from nuitka.nodes.AttributeNodes import (
    CPythonExpressionAttributeLookup,
    CPythonExpressionBuiltinHasattr
)
from nuitka.nodes.SubscriptNode import CPythonExpressionSubscriptLookup
from nuitka.nodes.FunctionNodes import (
    CPythonExpressionFunctionCreation,
    CPythonExpressionFunctionBody,
    CPythonExpressionFunctionCall,
    CPythonExpressionFunctionRef
)
from nuitka.nodes.ClassNodes import CPythonExpressionSelectMetaclass
from nuitka.nodes.ContainerMakingNodes import (
    CPythonExpressionKeyValuePair,
    CPythonExpressionMakeTuple,
    CPythonExpressionMakeDict
)
from nuitka.nodes.ContainerOperationNodes import (
    CPythonStatementDictOperationRemove,
    CPythonExpressionDictOperationGet
)
from nuitka.nodes.StatementNodes import CPythonStatementsSequence

from nuitka.nodes.ConditionalNodes import (
    CPythonExpressionConditional,
    CPythonStatementConditional
)
from nuitka.nodes.ReturnNode import CPythonStatementReturn
from nuitka.nodes.AssignNodes import CPythonStatementAssignmentVariable

from nuitka.nodes.GlobalsLocalsNodes import (
    CPythonStatementSetLocals,
    CPythonExpressionBuiltinLocals
)

from nuitka.nodes.ParameterSpec import ParameterSpec

from .Helpers import (
    makeStatementsSequence,
    buildStatementsNode,
    extractDocFromBody,
    buildNodeList,
    buildNode,
    getKind
)

from nuitka import Utils

# TODO: Once we start to modify these, we should make sure, the copy is not shared.
make_class_parameters = ParameterSpec(
    name          = "class",
    normal_args   = (),
    list_star_arg = None,
    dict_star_arg = None,
    default_count = 0,
    kw_only_args  = ()
)


def _buildClassNode3( provider, node, source_ref ):
    # Many variables, due to the huge re-formulation that is going on here, which just has
    # the complexity, pylint: disable=R0914

    # This function is the Python3 special case with special re-formulation as according
    # to developer manual.
    class_statements, class_doc = extractDocFromBody( node )

    # The result will be a temp block that holds the temporary variables.
    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_bases = result.getTempVariable( "bases" )
    tmp_class_decl_dict = result.getTempVariable( "class_decl_dict" )
    tmp_metaclass = result.getTempVariable( "metaclass" )
    tmp_prepared = result.getTempVariable( "prepared" )

    class_creation_function = CPythonExpressionFunctionBody(
        provider   = provider,
        is_class   = True,
        parameters = make_class_parameters,
        name       = node.name,
        doc        = class_doc,
        source_ref = source_ref
    )

    # Hack:
    class_creation_function.parent = provider

    body = buildStatementsNode(
        provider   = class_creation_function,
        nodes      = class_statements,
        frame      = True,
        source_ref = source_ref
    )

    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref.atInternal()

    statements = [
        CPythonStatementSetLocals(
            new_locals = CPythonExpressionTempVariableRef(
                variable   = tmp_prepared.makeReference( result ),
                source_ref = source_ref
            ),
            source_ref = source_ref.atInternal()
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTargetVariableRef(
                variable_name = "__module__",
                source_ref    = source_ref
            ),
            source        = CPythonExpressionConstantRef(
                constant   = provider.getParentModule().getName(),
                source_ref = source_ref
            ),
            source_ref   = source_ref.atInternal()
        )
    ]

    if class_doc is not None:
        statements.append(
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTargetVariableRef(
                    variable_name = "__doc__",
                    source_ref    = source_ref
                ),
                source        = CPythonExpressionConstantRef(
                    constant   = class_doc,
                    source_ref = source_ref
                ),
                source_ref   = source_ref.atInternal()
            )
        )

    statements += [
        body,
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTargetVariableRef(
                variable_name = "__class__",
                source_ref    = source_ref
            ),
            source       = CPythonExpressionCall(
                called     = CPythonExpressionTempVariableRef(
                    variable   = tmp_metaclass.makeReference( result ),
                    source_ref = source_ref
                ),
                args       = CPythonExpressionMakeTuple(
                    elements   = (
                        CPythonExpressionConstantRef(
                            constant   = node.name,
                            source_ref = source_ref
                        ),
                        CPythonExpressionTempVariableRef(
                            variable   = tmp_bases.makeReference( result ),
                            source_ref = source_ref
                        ),
                        CPythonExpressionBuiltinLocals(
                            source_ref = source_ref
                        )
                    ),
                    source_ref = source_ref
                ),
                kw         = CPythonExpressionTempVariableRef(
                    variable   = tmp_class_decl_dict.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref   = source_ref.atInternal()
        ),
        CPythonStatementReturn(
            expression = CPythonExpressionVariableRef(
                variable_name = "__class__",
                source_ref    = source_ref
            ),
            source_ref = source_ref.atInternal()
        )
    ]

    body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    # The class body is basically a function that implicitely, at the end returns its
    # locals and cannot have other return statements contained.

    class_creation_function.setBody( body )

    # The class body is basically a function that implicitely, at the end returns its
    # created class and cannot have other return statements contained.

    decorated_body = CPythonExpressionFunctionCall(
        function   = CPythonExpressionFunctionCreation(
            function_ref = CPythonExpressionFunctionRef(
                function_body = class_creation_function,
                source_ref    = source_ref
            ),
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (),
        source_ref = source_ref
    )

    for decorator in buildNodeList( provider, reversed( node.decorator_list ), source_ref ):
        decorated_body = CPythonExpressionCallNoKeywords(
            called     = decorator,
            args       = CPythonExpressionMakeTuple(
                elements   = ( decorated_body, ),
                source_ref = source_ref
            ),
            source_ref = decorator.getSourceReference()
        )

    statements = [
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_bases.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionMakeTuple(
                elements   = buildNodeList( provider, node.bases, source_ref ),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_class_decl_dict.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionMakeDict(
                pairs      = [
                    CPythonExpressionKeyValuePair(
                        key        = CPythonExpressionConstantRef(
                            constant   = keyword.arg,
                            source_ref = source_ref
                        ),
                        value      = buildNode( provider, keyword.value, source_ref ),
                        source_ref = source_ref
                    )
                    for keyword in
                    node.keywords
                ],
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_metaclass.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionSelectMetaclass(
                metaclass = CPythonExpressionConditional(
                    condition = CPythonExpressionComparison(
                        comparator = "In",
                        left       = CPythonExpressionConstantRef(
                            constant   = "metaclass",
                            source_ref = source_ref
                        ),
                        right      = CPythonExpressionTempVariableRef(
                            variable   = tmp_class_decl_dict.makeReference( result ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_expression = CPythonExpressionDictOperationGet(
                        dicte      = CPythonExpressionTempVariableRef(
                            variable   = tmp_class_decl_dict.makeReference( result ),
                            source_ref = source_ref
                        ),
                        key        = CPythonExpressionConstantRef(
                            constant   = "metaclass",
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    no_expression  = CPythonExpressionConditional(
                        condition      = CPythonExpressionTempVariableRef(
                            variable   = tmp_bases.makeReference( result ),
                            source_ref = source_ref
                        ),
                        no_expression  = CPythonExpressionBuiltinRef(
                            builtin_name = "type",
                            source_ref   = source_ref
                        ),
                        yes_expression = CPythonExpressionBuiltinType1(
                            value      = CPythonExpressionSubscriptLookup(
                                expression = CPythonExpressionTempVariableRef(
                                    variable   = tmp_bases.makeReference( result ),
                                    source_ref = source_ref
                                ),
                                subscript  = CPythonExpressionConstantRef(
                                    constant   = 0,
                                    source_ref = source_ref
                                ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref     = source_ref
                    ),
                    source_ref     = source_ref
                ),
                bases     = CPythonExpressionTempVariableRef(
                    variable   = tmp_bases.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        CPythonStatementConditional(
            condition  = CPythonExpressionComparison(
                comparator = "In",
                left       = CPythonExpressionConstantRef(
                    constant   = "metaclass",
                    source_ref = source_ref
                ),
                right      = CPythonExpressionTempVariableRef(
                    variable   = tmp_class_decl_dict.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            no_branch  = None,
            yes_branch = CPythonStatementsSequence(
                statements = (
                    CPythonStatementDictOperationRemove(
                        dicte = CPythonExpressionTempVariableRef(
                            variable   = tmp_class_decl_dict.makeReference( result ),
                            source_ref = source_ref
                        ),
                        key   = CPythonExpressionConstantRef(
                            constant   = "metaclass",
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_prepared.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionConditional(
                condition = CPythonExpressionBuiltinHasattr(
                    object     = CPythonExpressionTempVariableRef(
                        variable   = tmp_metaclass.makeReference( result ),
                        source_ref = source_ref
                    ),
                    name       = CPythonExpressionConstantRef(
                        constant   = "__prepare__",
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                no_expression = CPythonExpressionConstantRef(
                    constant   = {},
                    source_ref = source_ref
                ),
                yes_expression = CPythonExpressionCall(
                    called     = CPythonExpressionAttributeLookup(
                        expression     = CPythonExpressionTempVariableRef(
                            variable   = tmp_metaclass.makeReference( result ),
                            source_ref = source_ref
                        ),
                        attribute_name = "__prepare__",
                        source_ref     = source_ref
                    ),
                    args       = CPythonExpressionMakeTuple(
                        elements   = (
                            CPythonExpressionConstantRef(
                                constant = node.name,
                                source_ref     = source_ref
                            ),
                            CPythonExpressionTempVariableRef(
                                variable   = tmp_bases.makeReference( result ),
                                source_ref = source_ref
                            )
                        ),
                        source_ref = source_ref
                    ),
                    kw         = CPythonExpressionTempVariableRef(
                        variable   = tmp_class_decl_dict.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTargetVariableRef(
                variable_name = node.name,
                source_ref    = source_ref
            ),
            source     = decorated_body,
            source_ref = source_ref
        )
    ]

    result.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result


def _buildClassNode2( provider, node, source_ref ):
    class_statements, class_doc = extractDocFromBody( node )

    # This function is the Python3 special case with special re-formulation as according
    # to developer manual.

    # The result will be a temp block that holds the temporary variables.
    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_bases = result.getTempVariable( "bases" )
    tmp_class_dict = result.getTempVariable( "class_dict" )
    tmp_metaclass = result.getTempVariable( "metaclass" )
    tmp_class = result.getTempVariable( "class" )

    class_creation_function = CPythonExpressionFunctionBody(
        provider   = provider,
        is_class   = True,
        parameters = make_class_parameters,
        name       = node.name,
        doc        = class_doc,
        source_ref = source_ref
    )

    body = buildStatementsNode(
        provider   = class_creation_function,
        nodes      = class_statements,
        frame      = True,
        source_ref = source_ref
    )

    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref.atInternal()

    # The class body is basically a function that implicitely, at the end returns its
    # locals and cannot have other return statements contained, and starts out with a
    # variables "__module__" and potentially "__doc__" set.
    statements = [
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTargetVariableRef(
                variable_name = "__module__",
                source_ref    = source_ref
            ),
            source        = CPythonExpressionConstantRef(
                constant   = provider.getParentModule().getName(),
                source_ref = source_ref
            ),
            source_ref   = source_ref.atInternal()
        )
    ]

    if class_doc is not None:
        statements.append(
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTargetVariableRef(
                    variable_name = "__doc__",
                    source_ref    = source_ref
                ),
                source        = CPythonExpressionConstantRef(
                    constant   = class_doc,
                    source_ref = source_ref
                ),
                source_ref   = source_ref.atInternal()
            )
        )

    statements += [
        body,
        CPythonStatementReturn(
            expression = CPythonExpressionBuiltinLocals(
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

    # The class body is basically a function that implicitely, at the end returns its
    # locals and cannot have other return statements contained.

    class_creation_function.setBody( body )

    statements = [
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_bases.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionMakeTuple(
                elements   = buildNodeList( provider, node.bases, source_ref ),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_class_dict.makeReference( result ),
                source_ref = source_ref
            ),
            source       =   CPythonExpressionFunctionCall(
                function = CPythonExpressionFunctionCreation(
                    function_ref = CPythonExpressionFunctionRef(
                        function_body = class_creation_function,
                        source_ref    = source_ref
                    ),
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
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_metaclass.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionConditional(
                condition =  CPythonExpressionComparison(
                    comparator = "In",
                    left       = CPythonExpressionConstantRef(
                        constant   = "__metaclass__",
                        source_ref = source_ref
                    ),
                    right      = CPythonExpressionTempVariableRef(
                        variable   = tmp_class_dict.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_expression = CPythonExpressionDictOperationGet(
                    dicte = CPythonExpressionTempVariableRef(
                        variable   = tmp_class_dict.makeReference( result ),
                        source_ref = source_ref
                    ),
                    key   = CPythonExpressionConstantRef(
                        constant   = "__metaclass__",
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                no_expression = CPythonExpressionSelectMetaclass(
                    metaclass = None,
                    bases     = CPythonExpressionTempVariableRef(
                        variable   = tmp_bases.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_class.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionCallNoKeywords(
                called         = CPythonExpressionTempVariableRef(
                    variable   = tmp_metaclass.makeReference( result ),
                    source_ref = source_ref
                ),
                args           = CPythonExpressionMakeTuple(
                    elements   = (
                        CPythonExpressionConstantRef(
                            constant = node.name,
                            source_ref     = source_ref
                        ),
                        CPythonExpressionTempVariableRef(
                            variable   = tmp_bases.makeReference( result ),
                            source_ref = source_ref
                        ),
                        CPythonExpressionTempVariableRef(
                            variable   = tmp_class_dict.makeReference( result ),
                            source_ref = source_ref
                        )
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    ]

    for decorator in buildNodeList( provider, reversed( node.decorator_list ), source_ref ):
        statements.append(
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_class.makeReference( result ),
                    source_ref = source_ref
                ),
                source       = CPythonExpressionCallNoKeywords(
                    called     = decorator,
                    args       = CPythonExpressionMakeTuple(
                        elements  = (
                            CPythonExpressionTempVariableRef(
                                variable   = tmp_class.makeReference( result ),
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
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTargetVariableRef(
                variable_name = node.name,
                source_ref    = source_ref
            ),
            source     = CPythonExpressionTempVariableRef(
                variable   = tmp_class.makeReference( result ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result

def buildClassNode( provider, node, source_ref ):
    assert getKind( node ) == "ClassDef"

    # Python3 and Python3 are similar, but fundamentally different, so handle them in
    # dedicated code.

    if Utils.python_version >= 300:
        return _buildClassNode3( provider, node, source_ref )
    else:
        return _buildClassNode2( provider, node, source_ref )
