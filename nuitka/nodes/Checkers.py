#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Node children checkers.

The role of checkers is to make sure that node children have specific value
types only.

"""


def checkStatementsSequenceOrNone(value):
    if value is not None:
        assert value.kind == "STATEMENTS_SEQUENCE", value

        if not value.subnode_statements:
            return None

    return value


def checkStatementsSequence(value):
    assert value is not None and value.kind == "STATEMENTS_SEQUENCE", value

    return value


def convertNoneConstantToNone(node):
    if node is None or node.isExpressionConstantNoneRef():
        return None
    else:
        return node


def convertEmptyStrConstantToNone(node):
    if node is None or node.isExpressionConstantStrEmptyRef():
        return None
    else:
        return node


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
