#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node children checkers.

The role of checkers is to make sure that node children have specific value
types only.

"""

def checkStatementsSequenceOrNone(value):
    assert value is None or value.kind == "STATEMENTS_SEQUENCE", value

    return value

def checkStatementsSequence(value):
    assert value is not None and value.kind == "STATEMENTS_SEQUENCE", value

    return value
