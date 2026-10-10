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


def makeMutableFrozendict():
    return frozendict({"items": [1, 2]})


def makeNestedFrozendict():
    return (frozendict({"items": [1]}), 2)


def unpackFrozendict(key_a, key_b):
    key1, key2 = frozendict({key_a: 1, key_b: 2})
    return key1, key2


value = makeFrozendict()

print("type is frozendict:", isFrozendict(value), isFrozendict({"a": 1}))
print("isinstance:", isFrozendictSubclassCheck(value), isFrozendictSubclassCheck([]))
print("isinstance tuple:", isMapping(value), isMapping({}), isMapping([]))
print("match:", matchKind(value), matchKind({}), matchKind([]))
print("class compare:", value.__class__ == frozendict)
print("type name:", frozendict.__name__)
print("value:", value, len(value), value["b"])
print("iterate:", sorted(value), sorted(iter(value)))
print("next:", next(iter(value)), next(iter(frozendict({"z": 0}))))
print("contains:", "a" in value, "c" in value)
print("methods:", sorted(value.keys()), value.get("a"), value.get("c", 42))
print("copy:", value.copy() == value, type(value.copy()) is frozendict)
print("fromkeys:", frozendict.fromkeys(("x", "y"), 0))
print("or:", value | {"c": 3}, value | frozendict({"c": 3}))
print("empty:", frozendict(), bool(frozendict()), bool(value))
print("equal:", value == frozendict({"a": 1, "b": 2}))
print("hash:", hash(value) == hash(frozendict({"a": 1, "b": 2})))

try:
    hash(frozendict({"items": []}))
except TypeError as e:
    print("unhashable:", type(e).__name__)

mutable = makeMutableFrozendict()
mutable["items"].append(3)
print("deep copy:", mutable, makeMutableFrozendict())

nested = makeNestedFrozendict()
nested[0]["items"].append(3)
print("nested deep copy:", nested, makeNestedFrozendict())

print("kwargs:", (lambda **kw: sorted(kw.items()))(**frozendict({"a": 1, "b": 2})))
print("dict:", dict(value), {key: value[key] for key in sorted(value)})
print("mapping format:", "%(a)s-%(b)s" % value)
print("unpack:", unpackFrozendict("x", "y"))

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
