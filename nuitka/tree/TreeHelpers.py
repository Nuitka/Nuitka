#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Helper functions for parsing the AST nodes and building the Nuitka node tree.

"""

import __future__

import ast

from nuitka import Constants, Options
from nuitka.Errors import CodeTooComplexCode
from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import makeExpressionMakeTupleOrConstant
from nuitka.nodes.DictionaryNodes import makeExpressionMakeDict
from nuitka.nodes.ExceptionNodes import StatementReraiseException
from nuitka.nodes.FrameNodes import (
    StatementsFrameAsyncgen,
    StatementsFrameClass,
    StatementsFrameCoroutine,
    StatementsFrameFunction,
    StatementsFrameGenerator,
    StatementsFrameModule,
)
from nuitka.nodes.KeyValuePairNodes import (
    makeKeyValuePairExpressionsFromKwArgs,
)
from nuitka.nodes.NodeBases import NodeBase
from nuitka.nodes.NodeMakingHelpers import mergeStatements
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.PythonVersions import python_version
from nuitka.Tracing import optimization_logger, printLine


def dump(node):
    printLine(ast.dump(node))


def getKind(node):
    return node.__class__.__name__.rsplit(".", 1)[-1]


def extractDocFromBody(node):
    body = node.body
    doc = None

    # Work around "ast.get_docstring" breakage.
    if body and getKind(body[0]) == "Expr":
        if getKind(body[0].value) == "Str":  # python3.7 or earlier
            doc = body[0].value.s
            body = body[1:]
        elif getKind(body[0].value) == "Constant":  # python3.8
            # Only strings should be used, but all other constants can immediately be ignored,
            # it seems that e.g. Ellipsis is common.
            if type(body[0].value.value) is str:
                doc = body[0].value.value
            body = body[1:]

        if Options.hasPythonFlagNoDocStrings():
            doc = None

    if doc is not None and python_version >= 0x3D0:
        doc = doc.lstrip()

    return body, doc


def parseSourceCodeToAst(source_code, module_name, filename, line_offset):
    # Workaround: ast.parse cannot cope with some situations where a file is not
    # terminated by a new line.
    if not source_code.endswith("\n"):
        source_code = source_code + "\n"

    try:
        body = ast.parse(source_code, filename)
    except RuntimeError as e:
        if "maximum recursion depth" in e.args[0]:
            raise CodeTooComplexCode(module_name, filename)

        raise

    assert getKind(body) == "Module"

    if line_offset > 0:
        ast.increment_lineno(body, line_offset)

    return body


def detectFunctionBodyKind(nodes, start_value=None):
    # This is a complex mess, following the scope means a lot of checks need
    # to be done. pylint: disable=too-many-branches,too-many-statements

    indications = set()
    if start_value is not None:
        indications.add(start_value)

    flags = set()

    def _checkCoroutine(field):
        """Check only for co-routine nature of the field and only update that."""
        # TODO: This is clumsy code, trying to achieve what non-local does for
        # Python2 as well.

        old = set(indications)
        indications.clear()

        _check(field)

        if "Coroutine" in indications:
            old.add("Coroutine")

        indications.clear()
        indications.update(old)

    def _check(node):
        node_class = node.__class__

        if node_class is ast.Yield:
            indications.add("Generator")
        elif python_version >= 0x300 and node_class is ast.YieldFrom:
            indications.add("Generator")
        elif python_version >= 0x350 and node_class in (ast.Await, ast.AsyncWith):
            indications.add("Coroutine")

        # Recurse to children, but do not cross scope boundary doing so.
        if node_class is ast.ClassDef:
            for name, field in ast.iter_fields(node):
                if name in ("name", "body"):
                    pass
                elif name in ("bases", "decorator_list", "keywords", "type_params"):
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
        elif node_class in (ast.FunctionDef, ast.Lambda) or (
            python_version >= 0x350 and node_class is ast.AsyncFunctionDef
        ):
            for name, field in ast.iter_fields(node):
                if name in ("name", "body"):
                    pass
                elif name in ("bases", "decorator_list", "type_params"):
                    for child in field:
                        _check(child)
                elif name == "args":
                    for child in field.defaults:
                        _check(child)

                    if python_version >= 0x300:
                        for child in node.args.kw_defaults:
                            if child is not None:
                                _check(child)

                        for child in node.args.args:
                            if child.annotation is not None:
                                _check(child.annotation)

                elif name == "returns":
                    if field is not None:
                        _check(field)
                elif name == "type_comment":
                    # Python3.8: We don't have structure here.
                    assert field is None or type(field) is str
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class is ast.GeneratorExp:
            for name, field in ast.iter_fields(node):
                if name == "name":
                    pass
                elif name in ("body", "comparators", "elt"):
                    if python_version >= 0x370:
                        _checkCoroutine(field)
                elif name == "generators":
                    _check(field[0].iter)

                    # New syntax in 3.7 allows these to be present in functions not
                    # declared with "async def", so we need to check them, but
                    # only if top level.
                    if python_version >= 0x370 and node in nodes:
                        for gen in field:
                            if gen.is_async:
                                indications.add("Coroutine")
                                break

                            if _checkCoroutine(gen):
                                break
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class is ast.ListComp and python_version >= 0x300:
            for name, field in ast.iter_fields(node):
                if name in ("name", "body", "comparators"):
                    pass
                elif name == "generators":
                    if python_version < 0x3B0:
                        _check(field[0].iter)
                    else:
                        _check(field[0])
                elif name in ("body", "elt"):
                    _check(field)
                else:
                    assert False, (name, field, ast.dump(node))
        elif python_version >= 0x270 and node_class is ast.SetComp:
            for name, field in ast.iter_fields(node):
                if name in ("name", "body", "comparators", "elt"):
                    pass
                elif name == "generators":
                    _check(field[0].iter)
                else:
                    assert False, (name, field, ast.dump(node))
        elif python_version >= 0x270 and node_class is ast.DictComp:
            for name, field in ast.iter_fields(node):
                if name in ("name", "body", "comparators", "key", "value"):
                    pass
                elif name == "generators":
                    _check(field[0].iter)
                else:
                    assert False, (name, field, ast.dump(node))
        elif python_version >= 0x370 and node_class is ast.comprehension:
            for name, field in ast.iter_fields(node):
                if name in ("name", "target"):
                    pass
                elif name == "iter":
                    # Top level comprehension iterators do not influence those.
                    if node not in nodes:
                        _check(field)
                elif name == "ifs":
                    for child in field:
                        _check(child)
                elif name == "is_async":
                    if field:
                        indications.add("Coroutine")
                else:
                    assert False, (name, field, ast.dump(node))
        elif node_class is ast.Name:
            if python_version >= 0x300 and node.id == "super":
                flags.add("has_super")
        elif python_version < 0x300 and node_class is ast.Exec:
            flags.add("has_exec")

            if node.globals is None:
                flags.add("has_unqualified_exec")

            for child in ast.iter_child_nodes(node):
                _check(child)
        elif python_version < 0x300 and node_class is ast.ImportFrom:
            for import_desc in node.names:
                if import_desc.name[0] == "*":
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


def buildNode(provider, node, source_ref, allow_none=False):
    # too many exception handlers, pylint: disable=too-many-branches

    if node is None and allow_none:
        return None

    try:
        kind = getKind(node)

        if hasattr(node, "lineno"):
            source_ref = source_ref.atLineNumber(node.lineno)

        if kind in build_nodes_args3:
            result = build_nodes_args3[kind](
                provider=provider, node=node, source_ref=source_ref
            )
        elif kind in build_nodes_args2:
            result = build_nodes_args2[kind](node=node, source_ref=source_ref)
        elif kind in build_nodes_args1:
            result = build_nodes_args1[kind](source_ref=source_ref)
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
    except KeyboardInterrupt:
        # User interrupting is not a problem with the source, but tell where
        # we got interrupted.
        optimization_logger.info("Interrupted at '%s'." % source_ref)
        raise
    except SystemExit:
        optimization_logger.warning("Problem at '%s'." % source_ref.getAsString())
        raise
    except:
        optimization_logger.warning(
            "Problem at '%s' with %s." % (source_ref.getAsString(), ast.dump(node))
        )
        raise


def buildNodeList(provider, nodes, source_ref, allow_none=False):
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


def buildNodeTuple(provider, nodes, source_ref, allow_none=False):
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

        return tuple(result)
    else:
        return ()


_host_node = None


def buildAnnotationNode(provider, node, source_ref):
    if (
        python_version >= 0x370
        and provider.getParentModule().getFutureSpec().isFutureAnnotations()
    ):
        # Using global value for cache, to avoid creating it over and over,
        # avoiding the pylint: disable=global-statement
        global _host_node

        if _host_node is None:
            _host_node = ast.parse("x:1")

        _host_node.body[0].annotation = node

        r = compile(
            _host_node,
            "<annotations>",
            "exec",
            __future__.CO_FUTURE_ANNOTATIONS,
            dont_inherit=True,
        )

        # Using exec here, to compile the ast node tree back to string,
        # there is no accessible "ast.unparse", and this works as a hack
        # to convert our node to a string annotation, pylint: disable=exec-used
        m = {}
        exec(r, m)

        value = m["__annotations__"]["x"]

        if Options.is_debug and python_version >= 0x390:
            # TODO: In Python3.9+, we should only use ast.unparse
            assert value == ast.unparse(node)

        return makeConstantRefNode(constant=value, source_ref=source_ref)

    return buildNode(provider, node, source_ref)


def makeModuleFrame(module, statements, source_ref):
    assert module.isCompiledPythonModule()

    if Options.is_full_compat:
        co_name = "<module>"
    else:
        if module.isMainModule():
            co_name = "<module>"
        else:
            co_name = "<module %s>" % module.getFullName()

    return StatementsFrameModule(
        statements=tuple(statements),
        code_object=CodeObjectSpec(
            co_name=co_name,
            co_qualname=co_name,
            co_kind="Module",
            co_varnames=(),
            co_freevars=(),
            co_argcount=0,
            co_posonlyargcount=0,
            co_kwonlyargcount=0,
            co_has_starlist=False,
            co_has_stardict=False,
            co_filename=module.getRunTimeFilename(),
            co_lineno=source_ref.getLineNumber(),
            future_spec=module.getFutureSpec(),
        ),
        owner_code_name=module.getCodeName(),
        source_ref=source_ref,
    )


def buildStatementsNode(provider, nodes, source_ref):
    # We are not creating empty statement sequences.
    if nodes is None:
        return None

    # Build as list of statements, throw away empty ones, and remove useless
    # nesting.
    statements = buildNodeList(provider, nodes, source_ref, allow_none=True)
    statements = mergeStatements(statements)

    # We are not creating empty statement sequences. Might be empty, because
    # e.g. a global node generates not really a statement, or pass statements.
    if not statements:
        return None
    else:
        return StatementsSequence(statements=statements, source_ref=source_ref)


def buildFrameNode(provider, nodes, code_object, source_ref):
    # We are not creating empty statement sequences.
    if nodes is None:
        return None

    # Build as list of statements, throw away empty ones, and remove useless
    # nesting.
    statements = buildNodeList(provider, nodes, source_ref, allow_none=True)
    statements = mergeStatements(statements)

    # We are not creating empty statement sequences. Might be empty, because
    # e.g. a global node generates not really a statement, or pass statements.
    if not statements:
        return None

    if provider.isExpressionOutlineFunction():
        provider = provider.getParentVariableProvider()

    if provider.isExpressionFunctionBody():
        result = StatementsFrameFunction(
            statements=statements,
            code_object=code_object,
            owner_code_name=provider.getCodeName(),
            source_ref=source_ref,
        )
    elif provider.isExpressionClassBodyBase():
        result = StatementsFrameClass(
            statements=statements,
            code_object=code_object,
            owner_code_name=provider.getCodeName(),
            locals_scope=provider.getLocalsScope(),
            source_ref=source_ref,
        )
    elif provider.isExpressionGeneratorObjectBody():
        result = StatementsFrameGenerator(
            statements=statements,
            code_object=code_object,
            owner_code_name=provider.getCodeName(),
            source_ref=source_ref,
        )
    elif provider.isExpressionCoroutineObjectBody():
        result = StatementsFrameCoroutine(
            statements=statements,
            code_object=code_object,
            owner_code_name=provider.getCodeName(),
            source_ref=source_ref,
        )
    elif provider.isExpressionAsyncgenObjectBody():
        result = StatementsFrameAsyncgen(
            statements=statements,
            code_object=code_object,
            owner_code_name=provider.getCodeName(),
            source_ref=source_ref,
        )
    else:
        assert False, provider

    return result


def makeStatementsSequenceOrStatement(statements, source_ref):
    """Make a statement sequence, but only if more than one statement

    Useful for when we can unroll constructs already here, but are not sure if
    we actually did that. This avoids the branch or the pollution of doing it
    always.
    """

    if len(statements) > 1:
        return StatementsSequence(
            statements=mergeStatements(statements), source_ref=source_ref
        )
    else:
        return statements[0]


def makeStatementsSequence(statements, allow_none, source_ref):
    if allow_none:
        statements = tuple(
            statement for statement in statements if statement is not None
        )

    if statements:
        return StatementsSequence(
            statements=mergeStatements(statements, allow_none=allow_none),
            source_ref=source_ref,
        )
    else:
        return None


def makeStatementsSequenceFromStatement(statement):
    return StatementsSequence(
        statements=mergeStatements((statement,)),
        source_ref=statement.getSourceReference(),
    )


def makeStatementsSequenceFromStatements(*statements):
    assert statements
    assert None not in statements

    statements = mergeStatements(statements, allow_none=False)

    return StatementsSequence(
        statements=statements, source_ref=statements[0].getSourceReference()
    )


def makeDictCreationOrConstant2(keys, values, source_ref):
    # Create dictionary node. Tries to avoid it for constant values that are not
    # mutable. Keys are Python strings here.

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
            constant=Constants.createConstantDict(
                keys=keys, values=[value.getCompileTimeConstant() for value in values]
            ),
            user_provided=True,
            source_ref=source_ref,
        )
    else:
        result = makeExpressionMakeDict(
            pairs=makeKeyValuePairExpressionsFromKwArgs(zip(keys, values)),
            source_ref=source_ref,
        )

    if values:
        result.setCompatibleSourceReference(
            source_ref=values[-1].getCompatibleSourceReference()
        )

    return result


def getStatementsAppended(statement_sequence, statements):
    return makeStatementsSequence(
        statements=(statement_sequence, statements),
        allow_none=False,
        source_ref=statement_sequence.getSourceReference(),
    )


def getStatementsPrepended(statement_sequence, statements):
    return makeStatementsSequence(
        statements=(statements, statement_sequence),
        allow_none=False,
        source_ref=statement_sequence.getSourceReference(),
    )


def makeReraiseExceptionStatement(source_ref):
    return StatementReraiseException(source_ref=source_ref)


def mangleName(name, owner):
    """Mangle names with leading "__" for usage in a class owner.

    Notes: The is the private name handling for Python classes.
    """

    if not name.startswith("__") or name.endswith("__"):
        return name
    else:
        # The mangling of function variable names depends on being inside a
        # class.
        class_container = owner.getContainingClassDictCreation()

        if class_container is None:
            return name
        else:
            return "_%s%s" % (class_container.getName().lstrip("_"), name)


def makeCallNode(called, *args, **kwargs):
    source_ref = args[-1]

    if len(args) > 1:
        args = makeExpressionMakeTupleOrConstant(
            elements=args[:-1], user_provided=True, source_ref=source_ref
        )
    else:
        args = None

    if kwargs:
        kwargs = makeDictCreationOrConstant2(
            keys=tuple(kwargs.keys()),
            values=tuple(kwargs.values()),
            source_ref=source_ref,
        )
    else:
        kwargs = None

    return makeExpressionCall(
        called=called, args=args, kw=kwargs, source_ref=source_ref
    )


build_contexts = [None]


def pushBuildContext(value):
    build_contexts.append(value)


def popBuildContext():
    del build_contexts[-1]


def getBuildContext():
    return build_contexts[-1]


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
