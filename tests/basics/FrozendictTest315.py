#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Uses of the "frozendict" type that make it a constant of the compiled code."""


def isFrozendict(value):
    return type(value) is frozendict


def isFrozendictSubclassCheck(value):
    return isinstance(value, frozendict)


def isMapping(value):
    return isinstance(value, (dict, frozendict))


def matchKind(value):
    match value:
        case frozendict():
            return "frozendict"
        case dict():
            return "dict"
    return "other"


def makeFrozendict():
    return frozendict({"a": 1, "b": 2})


value = makeFrozendict()

print("type is frozendict:", isFrozendict(value), isFrozendict({"a": 1}))
print("isinstance:", isFrozendictSubclassCheck(value), isFrozendictSubclassCheck([]))
print("isinstance tuple:", isMapping(value), isMapping({}), isMapping([]))
print("match:", matchKind(value), matchKind({}), matchKind([]))
print("class compare:", value.__class__ == frozendict)
print("type name:", frozendict.__name__)
print("value:", value, len(value), value["b"])

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
