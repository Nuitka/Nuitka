#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""AST to source code conversion with support for older Python versions."""

import ast


def unparseNode(node, logger):
    """Convert an AST node back to source code.

    Args:
        node: The AST node to convert.
        logger: Logger to report errors with.

    Returns:
        str - source code representation of the node.
    """
    if hasattr(ast, "unparse"):
        return ast.unparse(node)

    from nuitka.utils.InlineCopies import importFromInlineCopy

    stubgen = importFromInlineCopy("stubgen", must_exist=False)

    if stubgen is None:
        return logger.sysexit("""\
Error, cannot convert AST to source code, the 'stubgen' inline copy with \
'astunparse' is missing.""")

    # The inline stubgen copy provides the astunparse fallback there.
    return stubgen._ast_unparse(node).strip()  # pylint: disable=protected-access


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
