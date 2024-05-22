#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Handle bytecode and compile source code to bytecode. """

import ast

from nuitka.Options import hasPythonFlagNoAsserts, hasPythonFlagNoDocStrings
from nuitka.tree.TreeHelpers import getKind
from nuitka.utils.Utils import withNoSyntaxWarning

doc_having = tuple(
    getattr(ast, candidate)
    for candidate in ("FunctionDef", "ClassDef", "AsyncFunctionDef")
    if hasattr(ast, candidate)
)


def _removeDocFromBody(node):
    if node.body and getKind(node.body[0]) == "Expr":
        if getKind(node.body[0].value) == "Str":  # python3.7 or earlier
            node.body[0].value.s = ""
        elif getKind(node.body[0].value) == "Constant":  # python3.8
            node.body[0].value.value = ""


def compileSourceToBytecode(source_code, filename):
    """Compile given source code into bytecode."""

    with withNoSyntaxWarning():
        # Prepare compile call with AST tree.
        tree = ast.parse(source_code, filename)

    # Do we need to remove doc strings.
    remove_doc_strings_from_tree = hasPythonFlagNoDocStrings()

    # For Python2, we need to do this manually.
    remove_asserts_from_tree = hasPythonFlagNoAsserts() and str is bytes

    if remove_doc_strings_from_tree or remove_asserts_from_tree:
        # Module level docstring.
        if remove_doc_strings_from_tree:
            _removeDocFromBody(tree)

        for node in ast.walk(tree):
            if remove_asserts_from_tree:
                node_type = type(node)

                if node_type is ast.Name:
                    if node.id == "__debug__":
                        node.id = "False"

                elif node_type is ast.Assert:
                    # Cannot really remove the assertion node easily, lets just replace it with
                    # "assert 1" and remove the assert msg. Probably not worth more effort for
                    # Python2 at this time.
                    node.test = ast.Num()
                    node.test.n = 1
                    node.test.lineno = node.lineno
                    node.test.col_offset = node.col_offset
                    node.msg = None

            # Check if it's a docstring having node type.
            if remove_doc_strings_from_tree and isinstance(node, doc_having):
                _removeDocFromBody(node)

    if str is bytes:
        bytecode = compile(
            tree,
            filename=filename,
            mode="exec",
            dont_inherit=True,
        )
    else:
        # Let the handling of __debug__ happen within compile built-in.
        optimize = 0
        if hasPythonFlagNoAsserts():
            optimize = 1

        bytecode = compile(
            tree, filename=filename, mode="exec", dont_inherit=True, optimize=optimize
        )

    return bytecode


def loadCodeObjectData(bytecode_filename):
    """Load bytecode from a file."""

    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    with open(bytecode_filename, "rb") as f:
        return f.read()[8 if str is bytes else 16 :]


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
