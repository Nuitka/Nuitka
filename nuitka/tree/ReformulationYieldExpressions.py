#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of "yield" and "yield from" expressions.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

import ast

from nuitka.nodes.ConstantRefNodes import ExpressionConstantNoneRef
from nuitka.nodes.CoroutineNodes import ExpressionAsyncWait
from nuitka.nodes.YieldNodes import (
    ExpressionYield,
    ExpressionYieldFrom,
    ExpressionYieldFromAwaitable,
)
from nuitka.PythonVersions import python_version

from .SyntaxErrors import raiseSyntaxError
from .TreeHelpers import buildNode


def _getErrorMessageYieldFromOutsideFunction():
    # Need to use "exec" to detect the syntax error, pylint: disable=W0122

    try:
        exec("""yield from ()""")
    except SyntaxError as e:
        if "yield from" in str(e):
            return "yield from"
        else:
            return "yield"


def _checkInsideGenerator(construct_name, provider, node, source_ref):

    if provider.isCompiledPythonModule():
        # Bug compatibility
        if construct_name == "yield from":
            construct_error_name = _getErrorMessageYieldFromOutsideFunction()
        else:
            construct_error_name = construct_name

        raiseSyntaxError(
            "'%s' outside function" % construct_error_name,
            source_ref.atColumnNumber(node.col_offset),
        )

    # This yield is forbidden in 3.5, but allowed in 3.6, but "yield from"
    # is neither.
    if provider.isExpressionAsyncgenObjectBody() and construct_name == "yield from":
        raiseSyntaxError(
            "'%s' inside async function"
            % ("yield" if node.__class__ is ast.Yield else "yield from",),
            source_ref.atColumnNumber(node.col_offset),
        )

    if (
        python_version >= 0x380
        and provider.isExpressionGeneratorObjectBody()
        and provider.name == "<genexpr>"
        and construct_name != "await"
    ):
        raiseSyntaxError(
            "'%s' inside generator expression"
            % ("yield" if node.__class__ is ast.Yield else "yield from",),
            provider.getSourceReference(),
        )

    while provider.isExpressionOutlineFunction():
        provider = provider.getParentVariableProvider()

    assert (
        provider.isExpressionGeneratorObjectBody()
        or provider.isExpressionAsyncgenObjectBody()
        or provider.isExpressionCoroutineObjectBody()
    ), provider


def buildYieldNode(provider, node, source_ref):
    _checkInsideGenerator("yield", provider, node, source_ref)

    if node.value is not None:
        return ExpressionYield(
            expression=buildNode(provider, node.value, source_ref),
            source_ref=source_ref,
        )
    else:
        return ExpressionYield(
            expression=ExpressionConstantNoneRef(source_ref=source_ref),
            source_ref=source_ref,
        )


def buildYieldFromNode(provider, node, source_ref):
    assert python_version >= 0x300

    _checkInsideGenerator("yield from", provider, node, source_ref)

    return ExpressionYieldFrom(
        expression=buildNode(provider, node.value, source_ref), source_ref=source_ref
    )


def buildAwaitNode(provider, node, source_ref):
    _checkInsideGenerator("await", provider, node, source_ref)

    return ExpressionYieldFromAwaitable(
        expression=ExpressionAsyncWait(
            expression=buildNode(provider, node.value, source_ref),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


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
