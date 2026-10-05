#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Hard import nodes registry.

This provides the registry for hard import nodes and builtin reference nodes.
"""

_hard_import_node_classes = {}
_builtin_ref_nodes = {}


def getHardImportNodeClasses():
    return _hard_import_node_classes


def addHardImportNodeClass(node_class, spec):
    _hard_import_node_classes[node_class] = spec


def getBuiltinRefNodes():
    return _builtin_ref_nodes


def getBuiltinRefNode(builtin_name):
    return _builtin_ref_nodes.get(builtin_name)


def addBuiltinRefNode(builtin_name, node_class):
    _builtin_ref_nodes[builtin_name] = node_class


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
