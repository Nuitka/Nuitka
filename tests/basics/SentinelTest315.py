#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for the Python 3.15 "sentinel" built-in."""

import copy
import pickle
import weakref

MISSING = sentinel("MISSING")
CUSTOM = sentinel("CUSTOM", repr="<custom>")
MODULE_VALUE = sentinel("MODULE_VALUE")


def make_function_sentinel():
    return sentinel("FUNCTION")


def make_default(value=sentinel("DEFAULT")):
    return value


class Container:
    VALUE = sentinel("CLASS")


comprehension_value = [sentinel("COMPREHENSION") for _ in range(1)][0]
alias = sentinel
alias_value = alias("ALIAS")

print("type:", type(MISSING) is sentinel, isinstance(MISSING, sentinel))
print("type name:", sentinel.__name__, type(sentinel).__name__)
print("name:", MISSING.__name__)
print("repr:", repr(MISSING), repr(CUSTOM), str(CUSTOM))
print("module:", MODULE_VALUE.__module__)
print("function module:", make_function_sentinel().__module__)
print("class module:", Container.VALUE.__module__)
print("comprehension module:", comprehension_value.__module__)
print("default module:", make_default().__module__)
print("alias module:", alias_value.__module__)

print("identity:", MISSING is MISSING, MISSING == MISSING)
other = sentinel("MISSING")
print("distinct:", MISSING is other, MISSING == other)
print("distinct calls:", sentinel("SAME") is not sentinel("SAME"))

print("truth:", bool(MISSING), not not MISSING)
print("direct truth:", bool(sentinel("DIRECT_TRUTH")))
print("hash:", hash(MISSING) == hash(MISSING))
print("attributes:", hasattr(MISSING, "__name__"), hasattr(MISSING, "__module__"))
print("direct attribute:", hasattr(sentinel("DIRECT_ATTRIBUTE"), "__name__"))
print("attributes missing:", hasattr(MISSING, "__len__"), hasattr(MISSING, "__iter__"))

print("copy:", copy.copy(MISSING) is MISSING, copy.deepcopy(MISSING) is MISSING)
print("reduce:", MISSING.__reduce__())

mutable_module = sentinel("MUTABLE_MODULE")
mutable_module.__module__ = "changed_module"
print("module mutation:", mutable_module.__module__)

try:
    MISSING.__name__ = "changed"
except AttributeError:
    print("name is read-only")

try:
    weakref.ref(MISSING)
except TypeError as e:
    print("weakref:", type(e).__name__)

try:

    class SentinelSubclass(sentinel):
        pass

except TypeError as e:
    print("subclass:", type(e).__name__)

print("pickle:", pickle.loads(pickle.dumps(MODULE_VALUE)) is MODULE_VALUE)

for label, make in (
    ("local", lambda: sentinel("LOCAL")),
    ("misnamed", lambda: sentinel("NOT_THE_ATTRIBUTE_NAME")),
):
    try:
        pickle.dumps(make())
    except Exception as e:
        print("pickle %s:" % label, type(e).__name__)

name = "DYNAMIC"
repr_value = "<dynamic>"
dynamic = sentinel(name, repr=repr_value)
print("dynamic:", dynamic.__name__, repr(dynamic))

nul_value = sentinel("a\0b", repr="r\0s")
print("embedded nul:", repr(nul_value.__name__), repr(repr(nul_value)))

for label, call in (
    ("bad name", lambda: sentinel(1)),
    ("bad repr", lambda: sentinel("X", repr=1)),
):
    try:
        call()
    except TypeError as e:
        print(label + ":", str(e))

print("union:", (sentinel("UNION") | int).__args__[1] is int)

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
