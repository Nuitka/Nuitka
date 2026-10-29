#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Slices as dictionary and set keys, these are hashable for Python 3.12 or higher,
if their values are hashable."""

from __future__ import print_function


def report(name, func, *args):
    try:
        result = func(*args)
    except TypeError as e:
        print(name, "TypeError:", e)
    else:
        print(name, repr(result))


def reportExceptionType(name, func, *args):
    # The messages of "dict" methods for unhashable keys differ with Python
    # 3.14 at this time, so only the exception type is checked for these.
    try:
        result = func(*args)
    except TypeError:
        print(name, "TypeError")
    else:
        print(name, repr(result))


def dictLiteral():
    return {slice(1, 2): 1}


def dictLiteralFromVariable():
    key = slice(1, 2)
    return {key: 1}


def dictLiteralTupleKey():
    return {(1, slice(1, 2)): 1}


def dictLiteralFrozensetTupleKey():
    return {(frozenset([1]), slice(1, 2)): 1}


def dictLiteralDynamic(value):
    return {slice(value, 2): 1}


def dictGet():
    return {}.get(slice(1, 2))


def dictGetDynamic(value):
    return {}.get(slice(value))


def dictContains():
    return slice(1, 2) in {}


def dictSubscriptStore():
    d = {}
    d[slice(1, 2)] = 3
    return d


def setLiteral():
    return {slice(1, 2)}


def setContains():
    return slice(1, 2) in set()


def hashCall():
    return hash(slice(1, 2)) == hash(slice(1, 2))


def dictLiteralUnhashableValue():
    result = {slice([]): 1}
    return result


def dictGetUnhashableValue():
    return {}.get(slice([1], 2))


def dictContainsUnhashableValue():
    return slice(1, {}) in {}


def dictGetUnhashableValueDynamic(value):
    return {}.get(slice(1, [value]))


def hashCallUnhashableValue():
    return hash(slice([]))


report("dict literal:", dictLiteral)
report("dict literal from variable:", dictLiteralFromVariable)
report("dict literal tuple key:", dictLiteralTupleKey)
report("dict literal frozenset tuple key:", dictLiteralFrozensetTupleKey)
report("dict literal dynamic:", dictLiteralDynamic, 1)
report("dict get:", dictGet)
report("dict get dynamic:", dictGetDynamic, 1)
report("dict contains:", dictContains)
report("dict subscript store:", dictSubscriptStore)
report("set literal:", setLiteral)
report("set contains:", setContains)
report("hash call:", hashCall)
report("dict literal unhashable value:", dictLiteralUnhashableValue)
reportExceptionType("dict get unhashable value:", dictGetUnhashableValue)
report("dict contains unhashable value:", dictContainsUnhashableValue)
reportExceptionType(
    "dict get unhashable value dynamic:", dictGetUnhashableValueDynamic, 1
)
report("hash call unhashable value:", hashCallUnhashableValue)

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
