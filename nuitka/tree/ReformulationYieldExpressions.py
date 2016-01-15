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
""" Reformulation of "yield" and "yield from" expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

import ast

from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.YieldNodes import ExpressionYield, ExpressionYieldFrom
from nuitka.PythonVersions import python_version
from nuitka.tree import SyntaxErrors

from .Helpers import buildNode


def _checkInsideGenerator(provider, node, source_ref):
    if provider.isCompiledPythonModule():
        SyntaxErrors.raiseSyntaxError(
            "'yield' outside function",
            source_ref,
            None if python_version < 300 else node.col_offset
        )

    if provider.isExpressionCoroutineObjectBody():
        SyntaxErrors.raiseSyntaxError(
            "'%s' inside async function" % (
                "yield" if node.__class__ is ast.Yield else "yield from",
            ),
            source_ref,
            node.col_offset+3
        )

    assert provider.isExpressionGeneratorObjectBody(), provider


def buildYieldNode(provider, node, source_ref):
    _checkInsideGenerator(provider, node, source_ref)

    if node.value is not None:
        return ExpressionYield(
            expression = buildNode(provider, node.value, source_ref),
            source_ref = source_ref
        )
    else:
        return ExpressionYield(
            expression = ExpressionConstantRef(
                constant      = None,
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref = source_ref
        )


def buildYieldFromNode(provider, node, source_ref):
    assert python_version >= 330

    _checkInsideGenerator(provider, node, source_ref)

    return ExpressionYieldFrom(
        expression = buildNode(provider, node.value, source_ref),
        source_ref = source_ref
    )
