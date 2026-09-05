#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 deferred annotations with constants and calls."""

from typing import Annotated, Callable, Optional, Tuple, TypedDict


def displayDict(d):
    result = "{"
    first = True
    for key, value in sorted(d.items()):
        if not first:
            result += ","

        result += "%s: %s" % (repr(key), repr(value))
        first = False
    result += "}"

    return result


def makeMeta(**kwargs):
    return tuple(sorted(kwargs.items()))


# The whole annotations dictionary is compile time constant here, which is the
# only shape that reaches the constant path rather than the expression one.
def plainTupleOfTypes(a: (int, str), b: float = 1.0) -> (str, bytes):
    return a, b


# Special float values have no literals in Python source, "repr" renders them
# as the bare names "inf" and "nan", which the constant path must re-wrap.
def specialFloats(a: 1e400, b: -1e400, c: float("nan"), d: 2.5) -> (float, float):
    return a, b, c, d


class Kwargs(TypedDict, total=False):
    items: Tuple["Later", ...]
    fn: Callable[..., "Later"]
    opt: Optional["Later"]
    meta: Annotated[int, makeMeta(strict=True)]


class Holder:
    tup: Tuple[int, ...]
    cb: Callable[..., int]
    pair: (int, str)


class Later:
    pass


print("TypedDict:", displayDict(Kwargs.__annotations__))
print("Class:", displayDict(Holder.__annotations__))
print("Function:", displayDict(plainTupleOfTypes.__annotations__))
print("Special floats:", displayDict(specialFloats.__annotations__))

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
