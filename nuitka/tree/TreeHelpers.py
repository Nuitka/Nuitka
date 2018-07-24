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
""" Helper functions for parsing the AST nodes and building the Nuitka node tree.

"""

import ast
from logging import warning

from nuitka import Constants, Options, Tracing
from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    ExpressionMakeList,
    ExpressionMakeSetLiteral,
    ExpressionMakeTuple
)
from nuitka.nodes.DictionaryNodes import (
    ExpressionKeyValuePair,
    ExpressionMakeDict
)
from nuitka.nodes.ExceptionNodes import StatementReraiseException
from nuitka.nodes.FrameNodes import (
    StatementsFrameAsyncgen,
    StatementsFrameCoroutine,
    StatementsFrameFunction,
    StatementsFrameGenerator,
    StatementsFrameModule
)
from nuitka.nodes.ImportNodes import ExpressionBuiltinImport
from nuitka.nodes.NodeBases import NodeBase
from nuitka.nodes.NodeMakingHelpers import mergeStatements
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.PythonVersions import (
    needsSetLiteralReverseInsertion,
    python_version
)


def dump(node):
    Tracing.printLine(ast.dump(node))


def getKind(node):
    return node.__class__.__name__.split('.')[-1]


def extractDocFromBody(node):
    body = node.body
    doc = None

    # Work around ast.get_docstring breakage.
    if node.body and \
       getKind(node.body[0]) == "Expr" and \
       getKind(node.body[0].value) == "Str":

        if "no_asserts" not in Options.getPythonFlags():
            doc = body[0].value.s

        body = body[1:]

    return body, doc


def parseSourceCodeToAst(source_code, filename, line_offset):
    # Workaround: ast.parse cannot cope with some situations where a file is not
    # terminated by a new line.
    if not source_code.endswith('\n'):
        source_code = source_code + '\n'

    body = ast.parse(source_code, filename)
    assert getKind(body) == "Module"

    if line_offset > 0:
        ast.increment_lineno(body, line_offset)

    return body


def detectFunctionBodyKind(nodes, start_value = None):
    # This is a complex mess, following the scope means a lot of checks need
    # to be done. pylint: disable=too-many-branches,too-many-statements

    indications = set()
    if start_value is not None:
        indications.add(start_value)

    flags = set()

    def _checkCoroutine(field):
        """ Check only for co-routine nature of the field and only update that.

        """
        # TODO: This is clumsy code, trying to achieve what non-local does for
        # Python2 as well.

        old = set(indications)
        indications.clear()

        _check(field)

        if "Coroutine" in indications:
            old.add("Coroutine")

        indications.clear()
        indications.update(old)
        del old

    def _check(node):
        node_class = node.__class__

        if node_class is ast.Yield:
            indications.add("Generator")
        elif python_version >= 300 and node_class is ast.YieldFrom:  # @UndefinedVariable
            indications.add("Generator")
        elif python_version >= 350 and node_class in (ast.Await, ast.AsyncWith):  # @UndefinedVariable
            indications.add("Coroutine")

        # Recurse to children, but do not cross scope boundary doing so.
        if node_class is ast.ClassDef:
            for name, field in ast.iter_fields(node):
                if name in ("name", "body"):
                    pass
                elif name in ("bases", "decorator_list", "keywords"):
                    for child in field:
                        _check(child)
                elif name == "starargs":
                    if field is not None:
                        _check(field)
                elif name == "kwargs":
                    if field is not None:
                        _check(field)
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class in (ast.FunctionDef, ast.Lambda) or \
             (python_version >= 350 and node_class is ast.AsyncFunctionDef):  # @UndefinedVariable
            for name, field in ast.iter_fields(node):
                if name in ("name", "body"):
                    pass
                elif name in ("bases", "decorator_list"):
                    for child in field:
                        _check(child)
                elif name == "args":
                    for child in field.defaults:
                        _check(child)

                    if python_version >= 300:
                        for child in node.args.kw_defaults:
                            if child is not None:
                                _check(child)

                        for child in node.args.args:
                            if child.annotation is not None:
                                _check(child.annotation)

                elif name == "returns":
                    if field is not None:
                        _check(field)
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class is ast.GeneratorExp:
            for name, field in ast.iter_fields(node):
                if name == "name":
                    pass
                elif name in ("body", "comparators", "elt"):
                    if python_version >= 370:
                        _checkCoroutine(field)
                elif name == "generators":
                    _check(field[0].iter)

                    # New syntax in 3.7 allows these to be present in functions not
                    # declared with "async def", so we need to check them.
                    if python_version >= 370:
                        for gen in field:
                            if gen.is_async:
                                indications.add("Coroutine")
                                break
                            elif _checkCoroutine(gen):
                                break
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class is ast.ListComp and python_version >= 300:
            for name, field in ast.iter_fields(node):
                if name in ("name", "body", "comparators"):
                    pass
                elif name == "generators":
                    _check(field[0].iter)
                elif name in("body", "elt"):
                    _check(field)
                else:
                    assert False, (name, field, ast.dump(node))
        elif python_version >= 270 and node_class is ast.SetComp:  # @UndefinedVariable
            for name, field in ast.iter_fields(node):
                if name in ("name", "body", "comparators", "elt"):
                    pass
                elif name == "generators":
                    _check(field[0].iter)
                else:
                    assert False, (name, field, ast.dump(node))
        elif python_version >= 270 and node_class is ast.DictComp:  # @UndefinedVariable
            for name, field in ast.iter_fields(node):
                if name in ("name", "body", "comparators", "key", "value"):
                    pass
                elif name == "generators":
                    _check(field[0].iter)
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class is ast.Name:
            if python_version >= 300 and node.id == "super":
                flags.add("has_super")
        elif python_version < 300 and node_class is ast.Exec:
            flags.add("has_exec")

            if node.globals is None:
                flags.add("has_unqualified_exec")

            for child in ast.iter_child_nodes(node):
                _check(child)
        elif python_version < 300 and node_class is ast.ImportFrom:
            for import_desc in node.names:
                if import_desc.name[0] == '*':
                    flags.add("has_exec")
            for child in ast.iter_child_nodes(node):
                _check(child)
        else:
            for child in ast.iter_child_nodes(node):
                _check(child)

    for node in nodes:
        _check(node)

    if indications:
        if "Coroutine" in indications and "Generator" in indications:
            function_kind = "Asyncgen"
        else:
            # If we found something, make sure we agree on all clues.
            assert len(indications) == 1, indications
            function_kind = indications.pop()
    else:
        function_kind = "Function"

    return function_kind, flags


build_nodes_args3 = None
build_nodes_args2 = None
build_nodes_args1 = None

def setBuildingDispatchers(path_args3, path_args2, path_args1):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=global-statement

    global build_nodes_args3, build_nodes_args2, build_nodes_args1

    build_nodes_args3 = path_args3
    build_nodes_args2 = path_args2
    build_nodes_args1 = path_args1


def buildNode(provider, node, source_ref, allow_none = False):
    if node is None and allow_none:
        return None

    # Just to disable the warning in the default handler below, we
    # catch some and re-raise instantly, pylint: disable=try-except-raise

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
            assert False, ast.dump(node)

        if result is None and allow_none:
            return None

        assert isinstance(result, NodeBase), result

        return result
    except SyntaxError:
        raise
    except RuntimeError:
        # Very likely the stack overflow, which we will turn into too complex
        # code exception, don't warn about it with a code dump then.
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
    assert module.isCompiledPythonModule()

    if Options.isFullCompat():
        code_name = "<module>"
    else:
        if module.isMainModule():
            code_name = "<module>"
        else:
            code_name = "<module %s>" % module.getFullName()

    return StatementsFrameModule(
        statements  = statements,
        code_object = CodeObjectSpec(
            co_name           = code_name,
            co_kind           = "Module",
            co_varnames       = (),
            co_argcount       = 0,
            co_kwonlyargcount = 0,
            co_has_starlist   = False,
            co_has_stardict   = False,
            co_filename       = module.getRunTimeFilename(),
            co_lineno         = source_ref.getLineNumber(),
            future_spec       = module.getFutureSpec()
        ),
        source_ref  = source_ref
    )


def buildStatementsNode(provider, nodes, source_ref):
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
    else:
        return StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )


def buildFrameNode(provider, nodes, code_object, source_ref):
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

    if provider.isExpressionOutlineFunction():
        provider = provider.getParentVariableProvider()

    if provider.isExpressionFunctionBody() or \
       provider.isExpressionClassBody():
        result = StatementsFrameFunction(
            statements  = statements,
            code_object = code_object,
            source_ref  = source_ref
        )
    elif provider.isExpressionGeneratorObjectBody():
        result = StatementsFrameGenerator(
            statements  = statements,
            code_object = code_object,
            source_ref  = source_ref
        )
    elif provider.isExpressionCoroutineObjectBody():
        result = StatementsFrameCoroutine(
            statements  = statements,
            code_object = code_object,
            source_ref  = source_ref
        )
    elif provider.isExpressionAsyncgenObjectBody():
        result = StatementsFrameAsyncgen(
            statements  = statements,
            code_object = code_object,
            source_ref  = source_ref
        )
    else:
        assert False, provider

    return result


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

    statements = mergeStatements(statements, allow_none = False)

    return StatementsSequence(
        statements = statements,
        source_ref = statements[0].getSourceReference()
    )


def makeSequenceCreationOrConstant(sequence_kind, elements, source_ref):
    # Sequence creation. Tries to avoid creations with only constant
    # elements. Would be caught by optimization, but would be useless churn. For
    # mutable constants we cannot do it though.

    # Due to the many sequence types, there is a lot of cases here
    # pylint: disable=too-many-branches

    for element in elements:
        if not element.isExpressionConstantRef():
            constant = False
            break
    else:
        constant = True

    sequence_kind = sequence_kind.lower()

    # Note: This would happen in optimization instead, but lets just do it
    # immediately to save some time.
    if constant:
        if sequence_kind == "tuple":
            const_type = tuple
        elif sequence_kind == "list":
            const_type = list
        elif sequence_kind == "set":
            const_type = set

            if needsSetLiteralReverseInsertion():
                elements = tuple(reversed(elements))
        else:
            assert False, sequence_kind

        result = makeConstantRefNode(
            constant      = const_type(
                element.getConstant()
                for element in
                elements
            ),
            source_ref    = source_ref,
            user_provided = True
        )
    else:
        if sequence_kind == "tuple":
            result = ExpressionMakeTuple(
                elements   = elements,
                source_ref = source_ref
            )
        elif sequence_kind == "list":
            result = ExpressionMakeList(
                elements   = elements,
                source_ref = source_ref
            )
        elif sequence_kind == "set":
            result = ExpressionMakeSetLiteral(
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


def makeDictCreationOrConstant(keys, values, source_ref):
    # Create dictionary node. Tries to avoid it for constant values that are not
    # mutable.

    assert len(keys) == len(values)
    for key, value in zip(keys, values):
        if not key.isExpressionConstantRef() or not key.isKnownToBeHashable():
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
        result = makeConstantRefNode(
            constant      = Constants.createConstantDict(
                keys   = [
                    key.getConstant()
                    for key in
                    keys
                ],
                values = [
                    value.getConstant()
                    for value in
                    values
                ]
            ),
            user_provided = True,
            source_ref    = source_ref
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
            source_ref = source_ref
        )

    if values:
        result.setCompatibleSourceReference(
            source_ref = values[-1].getCompatibleSourceReference()
        )

    return result


def makeDictCreationOrConstant2(keys, values, source_ref):
    # Create dictionary node. Tries to avoid it for constant values that are not
    # mutable. Keys are strings.

    assert len(keys) == len(values)
    for value in values:
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
        result = makeConstantRefNode(
            constant      = Constants.createConstantDict(
                keys   = keys,
                values = [
                    value.getConstant()
                    for value in
                    values
                ]
            ),
            user_provided = True,
            source_ref    = source_ref
        )
    else:
        result = ExpressionMakeDict(
            pairs      = [
                ExpressionKeyValuePair(
                    key        = makeConstantRefNode(
                        constant      = key,
                        source_ref    = value.getSourceReference(),
                        user_provided = True
                    ),
                    value      = value,
                    source_ref = value.getSourceReference()
                )
                for key, value in
                zip(keys, values)
            ],
            source_ref = source_ref
        )

    if values:
        result.setCompatibleSourceReference(
            source_ref = values[-1].getCompatibleSourceReference()
        )

    return result


def getStatementsAppended(statement_sequence, statements):
    return makeStatementsSequence(
        statements = (statement_sequence, statements),
        allow_none = False,
        source_ref = statement_sequence.getSourceReference()
    )


def getStatementsPrepended(statement_sequence, statements):
    return makeStatementsSequence(
        statements = (statements, statement_sequence),
        allow_none = False,
        source_ref = statement_sequence.getSourceReference()
    )


def makeReraiseExceptionStatement(source_ref):
    # TODO: Remove the statement sequence packaging and have users do it themselves
    # in factory functions instead.

    return StatementsSequence(
        statements = (
            StatementReraiseException(
                source_ref = source_ref
            ),
        ),
        source_ref = source_ref
    )


def makeAbsoluteImportNode(module_name, source_ref):
    return ExpressionBuiltinImport(
        name        = makeConstantRefNode(module_name, source_ref, True),
        globals_arg = None,
        locals_arg  = None,
        fromlist    = None,
        level       = makeConstantRefNode(0, source_ref, True),
        source_ref  = source_ref
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


def makeCallNode(called, *args, **kwargs):
    source_ref = args[-1]

    if len(args) > 1:
        args = makeSequenceCreationOrConstant(
            sequence_kind = "tuple",
            elements      = args[:-1],
            source_ref    = source_ref
        )
    else:
        args = None

    if kwargs:
        kwargs = makeDictCreationOrConstant2(
            keys       = tuple(kwargs.keys()),
            values     = tuple(kwargs.values()),
            source_ref = source_ref
        )
    else:
        kwargs = None

    return makeExpressionCall(
        called     = called,
        args       = args,
        kw         = kwargs,
        source_ref = source_ref
    )


build_contexts = [None]

def pushBuildContext(value):
    build_contexts.append(value)

def popBuildContext():
    del build_contexts[-1]

def getBuildContext():
    return build_contexts[-1]
