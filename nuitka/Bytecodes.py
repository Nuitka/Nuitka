#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Handle bytecode and compile source code to bytecode."""

import ast

from nuitka.PythonVersions import python_version
from nuitka.tree.TreeHelpers import getKind

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


def _removeLineNumbersFromTree(tree):
    for node in ast.walk(tree):
        if hasattr(node, "lineno"):
            node.lineno = 1

        if hasattr(node, "end_lineno"):
            node.end_lineno = 1

        if hasattr(node, "col_offset"):
            node.col_offset = 0

        if hasattr(node, "end_col_offset"):
            node.end_col_offset = 0


def compileSourceToBytecode(
    source_code, filename, remove_doc_strings, remove_asserts, remove_line_numbers
):
    """Compile given source code into bytecode.

    Args:
        source_code: Source code to compile.
        filename: Filename to use for the compilation.
        remove_doc_strings: Whether to remove docstrings from the source tree.
        remove_asserts: Whether to remove assertions from the compiled code.
        remove_line_numbers: Whether to normalize source line numbers to 1.
    """

    # Prepare compile call with AST tree.
    tree = ast.parse(source_code, filename)

    if remove_line_numbers:
        _removeLineNumbersFromTree(tree)

    # For Python2, we need to do this manually.
    remove_asserts_from_tree = remove_asserts and str is bytes

    if remove_doc_strings or remove_asserts_from_tree:
        # Module level docstring.
        if remove_doc_strings:
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
            if remove_doc_strings and isinstance(node, doc_having):
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
        optimize = 1 if remove_asserts else 0

        bytecode = compile(
            tree, filename=filename, mode="exec", dont_inherit=True, optimize=optimize
        )

    return bytecode


if python_version < 0x300:
    bytecode_header_size = 8
elif python_version < 0x370:
    # Python 3 added the source size to the pyc header.
    bytecode_header_size = 12
else:
    # Python 3.7 switched to the PEP 552 header layout.
    bytecode_header_size = 16


def loadCodeObjectData(bytecode_filename):
    """Load bytecode from a file."""

    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    with open(bytecode_filename, "rb") as f:
        return f.read()[bytecode_header_size:]


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
