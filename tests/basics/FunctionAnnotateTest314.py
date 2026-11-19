#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 function '__annotate__' behavior."""

import io
from annotationlib import Format, call_annotate_function, get_annotations
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
    z: io.BytesIO

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
print(
    "Class annotations by calling the function:",
    displayDict(
        call_annotate_function(
            TestClassAnnotations.__annotate__, format=Format.FORWARDREF
        )
    ),
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


class TestClassAnnotationsForward:
    attribute: Later

    class Later:
        pass


print(
    "Class annotations with forward reference:",
    displayDict(TestClassAnnotationsForward.__annotations__),
)


class TestClassAnnotationsTypeParams[T]:
    attribute: Later

    class Later:
        pass


print(
    "Class annotations with type parameters and forward reference:",
    displayDict(TestClassAnnotationsTypeParams.__annotations__),
)


class TestMethodAnnotationsForward:
    def method(self, value: Later) -> Later:
        return value

    class Later:
        pass


print(
    "Method annotations with forward reference:",
    displayDict(TestMethodAnnotationsForward.method.__annotations__),
)


class _Box:
    def __class_getitem__(cls, item):
        return (cls, item)


class _AltBox:
    def __class_getitem__(cls, item):
        return (cls, item)


_flag = True
_false_flag = False
_key_type = int
_val_type = str


def _precedenceAndDictAnnotations(
    sub_cond: (_Box if _flag else _AltBox)[int],
    sub_bitor: (_key_type | _val_type).__args__,
    int_attr_call: (1).bit_length(),
    neg_int_attr_call: (-1).bit_length(),
    neg_pow: (-2) ** _key_type,
    bool_or_and: (_false_flag or _flag) and _key_type,
    cond_nested: (int if _flag else str) if _false_flag else bytes,
    cmp_nested: (_key_type == _val_type) == _flag,
    dict_non_const_keys: {int: str, io.BytesIO: _val_type},
    slice_sub: _Box[1:_key_type, 2:3],
) -> {str: (_Box if _flag else _AltBox)[int]}:
    return (
        sub_cond,
        sub_bitor,
        int_attr_call,
        neg_int_attr_call,
        neg_pow,
        bool_or_and,
        cond_nested,
        cmp_nested,
        dict_non_const_keys,
        slice_sub,
    )


print(
    "Format.STRING precedence and dict annotations:",
    displayDict(get_annotations(_precedenceAndDictAnnotations, format=Format.STRING)),
)

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
