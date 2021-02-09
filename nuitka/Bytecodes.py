#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Handle bytecode and compile source code to bytecode. """

import ast

from nuitka.Options import getPythonFlags
from nuitka.tree.TreeHelpers import getKind

doc_having = tuple(
    getattr(ast, cand)
    for cand in ("FunctionDef", "ClassDef", "AsyncFunctionDef")
    if hasattr(ast, cand)
)


def _removeDocFromBody(node):
    if node.body and getKind(node.body[0]) == "Expr":
        if getKind(node.body[0].value) == "Str":  # python3.7 or earlier
            node.body[0].value.s = ""
        elif getKind(node.body[0].value) == "Constant":  # python3.8
            node.body[0].value.value = ""


def compileSourceToBytecode(source_code, filename):
    """ Compile given source code into bytecode. """

    if "no_docstrings" in getPythonFlags():
        tree = ast.parse(source_code, filename)

        _removeDocFromBody(tree)

        for node in ast.walk(tree):
            # Check if it's a documented thing.
            if not isinstance(node, doc_having):
                continue

            _removeDocFromBody(node)

        bytecode = compile(
            tree,
            filename=filename,
            mode="exec",
            dont_inherit=True,
        )

    else:
        bytecode = compile(
            source_code,
            filename=filename,
            mode="exec",
            dont_inherit=True,
        )

    return bytecode
