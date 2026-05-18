#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 function '__annotate__' behavior."""

from functools import singledispatch


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


def annotationCacheTest(_x: int):
    pass


if annotationCacheTest.__annotations__:
    pass

annotationCacheTest.__annotate__ = None
annotationCacheTest.__annotations__["cached"] = 9
print(
    "Annotation cache after clearing __annotate__:",
    displayDict(annotationCacheTest.__annotations__),
)


@singledispatch
def singledispatchTest(_value):
    return "default"


@singledispatchTest.register
def _(value: int):
    return "int"


print(
    "singledispatch register with annotation:",
    singledispatchTest(1),
    singledispatchTest("x"),
)


# Test class-level deferred annotations


class TestClassAnnotations:
    x: int = 1
    y: str

    def method(self, a: int) -> str:
        return str(a)


print(
    "Class annotations:",
    displayDict(TestClassAnnotations.__annotations__),
)
print("Class annotation attribute x:", TestClassAnnotations.x)
print(
    "Class annotation method result:",
    TestClassAnnotations().method(42),
)


class TestNoClassAnnotations:
    z = 42

    def method(self, a: int) -> str:
        return str(a)


print(
    "Class annotations (no class-level):",
    displayDict(TestNoClassAnnotations.__annotations__),
)
print("Class attribute z:", TestNoClassAnnotations.z)


class TestParent:
    parent_attr: str = "hello"


class TestChild(TestParent):
    child_attr: int = 10


print(
    "Child annotations:",
    displayDict(TestChild.__annotations__),
)
print("Child attr:", TestChild.child_attr)
print("Parent attr:", TestChild.parent_attr)

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
