#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reformulation of 'yield', 'yield from', and 'await' expressions."""

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
    # pylint: disable=W0122

    try:
        exec("""yield from ()""")
    except SyntaxError as e:
        if "yield from" in str(e):
            return "yield from"
        else:
            return "yield"


_comprehension_error_names = {
    "listcomp": "list comprehension",
    "setcontraction": "set comprehension",
    "dictcontraction": "dict comprehension",
}


def _checkInsideGenerator(construct_name, provider, node, source_ref):
    while provider.isExpressionOutlineFunction():
        if python_version >= 0x380 and construct_name != "await":
            comprehension_name = _comprehension_error_names.get(provider.getName())

            if comprehension_name is not None:
                raiseSyntaxError(
                    "'yield' inside %s" % comprehension_name,
                    (
                        provider.getSourceReference()
                        if python_version < 0x3A0
                        else source_ref.atColumnNumber(node.col_offset + 1)
                    ),
                )

        provider = provider.getParentVariableProvider()

    if provider.isCompiledPythonModule() or provider.isExpressionClassBodyBase():
        # Match CPython's exact SyntaxError wording, which varies across versions.
        if construct_name == "yield from":
            construct_error_name = _getErrorMessageYieldFromOutsideFunction()
        else:
            construct_error_name = construct_name

        raiseSyntaxError(
            "'%s' outside function" % construct_error_name,
            source_ref.atColumnNumber(node.col_offset),
        )

    if (
        python_version >= 0x380
        and (
            provider.isExpressionGeneratorObjectBody()
            or provider.isExpressionAsyncgenObjectBody()
        )
        and provider.name == "<genexpr>"
        and construct_name != "await"
    ):
        raiseSyntaxError(
            "'yield' inside generator expression",
            (
                provider.getSourceReference()
                if python_version < 0x3A0
                else source_ref.atColumnNumber(node.col_offset + 1)
            ),
        )

    # PEP 525 allows "yield" in async functions (3.6+), while "yield from"
    # remains a SyntaxError rejected after parsing.
    if provider.isExpressionAsyncgenObjectBody() and construct_name == "yield from":
        raiseSyntaxError(
            "'%s' inside async function"
            % ("yield" if node.__class__ is ast.Yield else "yield from",),
            source_ref.atColumnNumber(node.col_offset),
        )

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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
