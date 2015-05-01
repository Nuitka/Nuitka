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

""" Helper functions for parsing the AST nodes and building the Nuitka node tree.

"""

import ast
from logging import warning

from nuitka import Constants, Tracing
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerMakingNodes import (
    ExpressionKeyValuePair,
    ExpressionMakeDict,
    ExpressionMakeList,
    ExpressionMakeSet,
    ExpressionMakeTuple
)
from nuitka.nodes.NodeBases import NodeBase
from nuitka.nodes.StatementNodes import (
    StatementGeneratorEntry,
    StatementsFrame,
    StatementsSequence
)
from nuitka.nodes.TryFinallyNodes import (
    ExpressionTryFinally,
    StatementTryFinally
)


def dump(node):
    Tracing.printLine(ast.dump(node))


def getKind(node):
    return node.__class__.__name__.split('.')[-1]


def extractDocFromBody(node):
    # Work around ast.get_docstring breakage.
    if len(node.body) > 0 and getKind(node.body[0]) == "Expr" and getKind(node.body[0].value) == "Str":
        return node.body[1:], node.body[0].value.s
    else:
        return node.body, None


build_nodes_args3 = None
build_nodes_args2 = None
build_nodes_args1 = None

def setBuildingDispatchers(path_args3, path_args2, path_args1):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=W0603

    global build_nodes_args3, build_nodes_args2, build_nodes_args1

    build_nodes_args3 = path_args3
    build_nodes_args2 = path_args2
    build_nodes_args1 = path_args1


def buildNode(provider, node, source_ref, allow_none = False):
    if node is None and allow_none:
        return None

    try:
        kind = getKind(node)

        if hasattr(node, "lineno"):
            source_ref = source_ref.atLineNumber(node.lineno)
        else:
            source_ref = source_ref

        if kind in build_nodes_args3:
            result = build_nodes_args3[kind](
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind in build_nodes_args2:
            result = build_nodes_args2[kind](
                node       = node,
                source_ref = source_ref
            )
        elif kind in build_nodes_args1:
            result = build_nodes_args1[kind](
                source_ref = source_ref
            )
        elif kind == "Pass":
            result = None
        else:
            assert False, kind

        if result is None and allow_none:
            return None

        assert isinstance(result, NodeBase), result

        return result
    except SyntaxError:
        raise
    except:
        warning("Problem at '%s' with %s." % (source_ref, ast.dump(node)))
        raise


def buildNodeList(provider, nodes, source_ref, allow_none = False):
    if nodes is not None:
        result = []

        for node in nodes:
            if hasattr(node, "lineno"):
                node_source_ref = source_ref.atLineNumber(node.lineno)
            else:
                node_source_ref = source_ref

            entry = buildNode(provider, node, node_source_ref, allow_none)

            if entry is not None:
                result.append(entry)

        return result
    else:
        return []


def makeModuleFrame(module, statements, source_ref):
    assert module.isPythonModule()

    if module.isMainModule():
        code_name = "<module>"
    else:
        code_name = module.getName()

    return StatementsFrame(
        statements    = statements,
        guard_mode    = "once",
        var_names     = (),
        arg_count     = 0,
        kw_only_count = 0,
        code_name     = code_name,
        has_starlist  = False,
        has_stardict  = False,
        source_ref    = source_ref
    )


def buildStatementsNode(provider, nodes, source_ref, frame = False):
    # We are not creating empty statement sequences.
    if nodes is None:
        return None

    # Build as list of statements, throw away empty ones, and remove useless
    # nesting.
    statements = buildNodeList(provider, nodes, source_ref, allow_none = True)
    statements = mergeStatements(statements)

    # We are not creating empty statement sequences. Might be empty, because
    # e.g. a global node generates not really a statement, or pass statements.
    if not statements:
        return None

    # In case of a frame is desired, build it instead.
    if frame:
        if provider.isExpressionFunctionBody():
            parameters = provider.getParameters()

            arg_names     = parameters.getCoArgNames()
            kw_only_count = parameters.getKwOnlyParameterCount()
            code_name     = provider.getFunctionName()
            guard_mode    = "generator" if provider.isGenerator() else "full"
            has_starlist  = parameters.getStarListArgumentName() is not None
            has_stardict  = parameters.getStarDictArgumentName() is not None

            if provider.isGenerator():
                statements.insert(
                    0,
                    StatementGeneratorEntry(
                        source_ref = source_ref
                    )
                )

            return StatementsFrame(
                statements    = statements,
                guard_mode    = guard_mode,
                var_names     = arg_names,
                arg_count     = len(arg_names),
                kw_only_count = kw_only_count,
                code_name     = code_name,
                has_starlist  = has_starlist,
                has_stardict  = has_stardict,
                source_ref    = source_ref
            )
        else:
            return makeModuleFrame(
                module     = provider,
                statements = statements,
                source_ref = source_ref
            )
    else:
        return StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )


def mergeStatements(statements, allow_none = False):
    """ Helper function that merges nested statement sequences. """
    merged_statements = []

    for statement in statements:
        if statement is None and allow_none:
            pass
        elif statement.isStatement() or statement.isStatementsFrame():
            merged_statements.append(statement)
        elif statement.isStatementsSequence():
            merged_statements.extend(mergeStatements(statement.getStatements()))
        else:
            assert False, statement

    return merged_statements


def makeStatementsSequenceOrStatement(statements, source_ref):
    """ Make a statement sequence, but only if more than one statement

    Useful for when we can unroll constructs already here, but are not sure if
    we actually did that. This avoids the branch or the pollution of doing it
    always.
    """

    if len(statements) > 1:
        return StatementsSequence(
            statements = mergeStatements(statements),
            source_ref = source_ref
        )
    else:
        return statements[0]


def makeStatementsSequence(statements, allow_none, source_ref):
    if allow_none:
        statements = tuple(
            statement
            for statement in
            statements
            if statement is not None
        )

    if statements:
        return StatementsSequence(
            statements = mergeStatements(statements),
            source_ref = source_ref
        )
    else:
        return None


def makeStatementsSequenceFromStatement(statement):
    return StatementsSequence(
        statements = mergeStatements(
            (statement,)
        ),
        source_ref = statement.getSourceReference()
    )


def makeStatementsSequenceFromStatements(*statements):
    assert statements
    assert None not in statements

    return StatementsSequence(
        statements = statements,
        source_ref = statements[0].getSourceReference()
    )



def makeSequenceCreationOrConstant(sequence_kind, elements, source_ref):
    # Sequence creation. Tries to avoid creations with only constant
    # elements. Would be caught by optimization, but would be useless churn. For
    # mutable constants we cannot do it though.

    # Due to the many sequence types, there is a lot of cases here
    # pylint: disable=R0912

    for element in elements:
        if not element.isExpressionConstantRef():
            constant = False
            break
    else:
        constant = True

    sequence_kind = sequence_kind.upper()

    # Note: This would happen in optimization instead, but lets just do it
    # immediately to save some time.
    if constant:
        if sequence_kind == "TUPLE":
            const_type = tuple
        elif sequence_kind == "LIST":
            const_type = list
        elif sequence_kind == "SET":
            const_type = set
        else:
            assert False, sequence_kind

        result = ExpressionConstantRef(
            constant      = const_type(
                element.getConstant()
                for element in
                elements
            ),
            source_ref    = source_ref,
            user_provided = True
        )
    else:
        if sequence_kind == "TUPLE":
            result = ExpressionMakeTuple(
                elements   = elements,
                source_ref = source_ref
            )
        elif sequence_kind == "LIST":
            result = ExpressionMakeList(
                elements   = elements,
                source_ref = source_ref
            )
        elif sequence_kind == "SET":
            result = ExpressionMakeSet(
                elements   = elements,
                source_ref = source_ref
            )
        else:
            assert False, sequence_kind

    if elements:
        result.setCompatibleSourceReference(
            source_ref = elements[-1].getCompatibleSourceReference()
        )

    return result


def makeDictCreationOrConstant(keys, values, lazy_order, source_ref):
    # Create dictionary node. Tries to avoid it for constant values that are not
    # mutable.

    assert len(keys) == len(values)
    for key, value in zip(keys, values):
        if not key.isExpressionConstantRef():
            constant = False
            break

        if not value.isExpressionConstantRef():
            constant = False
            break
    else:
        constant = True

    # Note: This would happen in optimization instead, but lets just do it
    # immediately to save some time.
    if constant:
        # Unless told otherwise, create the dictionary in its full size, so
        # that no growing occurs and the constant becomes as similar as possible
        # before being marshaled.
        result = ExpressionConstantRef(
            constant      = Constants.createConstantDict(
                lazy_order = not lazy_order,
                keys       = [
                    key.getConstant()
                    for key in
                    keys
                ],
                values     = [
                    value.getConstant()
                    for value in
                    values
                ]
            ),
            source_ref    = source_ref,
            user_provided = True
        )
    else:
        result = ExpressionMakeDict(
            pairs      = [
                ExpressionKeyValuePair(
                    key        = key,
                    value      = value,
                    source_ref = key.getSourceReference()
                )
                for key, value in
                zip(keys, values)
            ],
            lazy_order = lazy_order,
            source_ref = source_ref
        )

    if values:
        result.setCompatibleSourceReference(
            source_ref = values[-1].getCompatibleSourceReference()
        )

    return result


def makeTryFinallyStatement(tried, final, source_ref):
    if type(tried) in (tuple, list):
        tried = StatementsSequence(
            statements = tried,
            source_ref = source_ref
        )
    if type(final) in (tuple, list):
        final = StatementsSequence(
            statements = final,
            source_ref = source_ref
        )

    if tried is not None and not tried.isStatementsSequence():
        tried = makeStatementsSequenceFromStatement(tried)
    if final is not None and not final.isStatementsSequence():
        final = makeStatementsSequenceFromStatement(final)

    return StatementTryFinally(
        tried      = tried,
        final      = final,
        public_exc = False,
        source_ref = source_ref
    )


def makeTryFinallyExpression(expression, tried, final, source_ref):
    if type(tried) in (tuple, list):
        tried = StatementsSequence(
            statements = tried,
            source_ref = source_ref
        )
    if type(final) in (tuple, list):
        final = StatementsSequence(
            statements = final,
            source_ref = source_ref
        )

    if tried is not None and not tried.isStatementsSequence():
        tried = makeStatementsSequenceFromStatement(tried)
    if final is not None and not final.isStatementsSequence():
        final = makeStatementsSequenceFromStatement(final)

    return ExpressionTryFinally(
        expression = expression,
        tried      = tried,
        final      = final,
        source_ref = source_ref
    )


def mangleName(variable_name, owner):
    if not variable_name.startswith("__") or variable_name.endswith("__"):
        return variable_name
    else:
        # The mangling of function variable names depends on being inside a
        # class.
        class_container = owner.getContainingClassDictCreation()

        if class_container is None:
            return variable_name
        else:
            return "_%s%s" % (
                class_container.getName().lstrip('_'),
                variable_name
            )


build_contexts = [None]

def pushBuildContext(value):
    build_contexts.append(value)

def popBuildContext():
    del build_contexts[-1]

def getBuildContext():
    return build_contexts[-1]

indicator_variables = [Ellipsis]

def getIndicatorVariables():
    return indicator_variables

def popIndicatorVariable():
    result = indicator_variables[-1]
    del indicator_variables[-1]
    return result

def pushIndicatorVariable(indicator_variable):
    indicator_variables.append(indicator_variable)


later = []

def wrapTryFinallyLater(node, final):
    later.append(
        (node, final)
    )

def applyLaterWrappers():
    for node, final in later:
        parent = node.getParent()

        # Skip over nodes, that current have a difficulty with being wrapped
        # TODO: This must not be necessary, and is a broken thing then, if one
        # node, must have a child of specific kind.
        while parent.isExpressionKeyValuePair():
            parent = parent.getParent()

        if parent.isExpression():
            # Replacement wrapper node, with no expression initially, to not
            # reparent already.
            new_node = makeTryFinallyExpression(
                expression = None, # see below
                tried      = None,
                final      = final,
                source_ref = final.getSourceReference()
            )
            parent.replaceWith(new_node)
            new_node.setExpression(parent)

            assert parent.parent.isExpressionTryFinally()
        elif parent.isStatement():
            # Replacement wrapper node, with no "tried" block initially, to not
            # have to re-parent already.
            new_node = makeTryFinallyStatement(
                tried      = None, # see below
                final      = final,
                source_ref = final.getSourceReference()
            )
            parent.replaceWith(new_node)
            new_node.setBlockTry(
                makeStatementsSequenceFromStatement(parent)
            )
        else:
            assert False, parent

    del later[:]
