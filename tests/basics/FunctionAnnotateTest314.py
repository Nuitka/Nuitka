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


class _AttrHolder:
    get = "custom_get"
    replace = "custom_replace"
    __prepare__ = "custom_prepare"


_attr_holder = _AttrHolder()
_known_dict = {"k": 1}
_known_list = [1, 2]
_known_str = "abc"
_known_bytes = b"xyz"
_num = 42
_width = 5
_non_ascii = "\xe9"


def _attributeLookupAnnotations(
    fixed_get: _attr_holder.get,
    fixed_replace: _attr_holder.replace,
    special_prepare: _attr_holder.__prepare__,
    dict_get: _known_dict.get,
    dict_items: _known_dict.items,
    dict_fromkeys: dict.fromkeys,
    list_append: _known_list.append,
    str_replace: _known_str.replace,
    str_format: _known_str.format,
    bytes_decode: _known_bytes.decode,
    type_prepare: type.__prepare__,
    cond_get: (_attr_holder if _flag else _known_dict).get,
):
    return (
        fixed_get,
        fixed_replace,
        special_prepare,
        dict_get,
        dict_items,
        dict_fromkeys,
        list_append,
        str_replace,
        str_format,
        bytes_decode,
        type_prepare,
        cond_get,
    )


print(
    "Attribute lookup annotations (VALUE):",
    [
        (
            key,
            type(value).__name__,
            value if isinstance(value, str) else value.__qualname__,
        )
        for key, value in sorted(
            get_annotations(_attributeLookupAnnotations, format=Format.VALUE).items()
        )
    ],
)
print(
    "Attribute lookup annotations (STRING):",
    displayDict(get_annotations(_attributeLookupAnnotations, format=Format.STRING)),
)


def _fstringAnnotations(
    multi: f"val={_num}, str={_known_str}",
    conversions: f"s={_num!s} r={_known_str!r} a={_non_ascii!a}",
    single_plain: f"{_num}",
    single_s: f"{_num!s}",
    single_r: f"{_known_str!r}",
    single_a: f"{_non_ascii!a}",
    static_spec: f"{_num:05d}",
    nested_spec: f"{_num:>{_width}}",
    brace_spec: f"{_known_str:{'{'}<5}",
    literal_braces: f"{{lit}}={_num}",
    dict_in_fstring: f"{ {'a': _num}['a'] }",
    cond_in_fstring: f"pick={_num if _flag else 0}",
):
    return (
        multi,
        conversions,
        single_plain,
        single_s,
        single_r,
        single_a,
        static_spec,
        nested_spec,
        brace_spec,
        literal_braces,
        dict_in_fstring,
        cond_in_fstring,
    )


print(
    "f-string annotations (VALUE):",
    displayDict(get_annotations(_fstringAnnotations, format=Format.VALUE)),
)

try:
    get_annotations(_fstringAnnotations, format=Format.STRING)
except TypeError as exc:
    print("f-string annotations (STRING) TypeError:", exc)


def _stringBuiltinCallAnnotations(
    call_str1: str(_num),
    call_str2: str(_known_bytes, "ascii"),
    call_str3: str(_known_bytes, errors="ignore"),
    call_ascii: ascii(_non_ascii),
    call_format: format(_num, "04d"),
):
    return (call_str1, call_str2, call_str3, call_ascii, call_format)


print(
    "String builtin call annotations (VALUE):",
    displayDict(get_annotations(_stringBuiltinCallAnnotations, format=Format.VALUE)),
)
print(
    "String builtin call annotations (STRING):",
    displayDict(get_annotations(_stringBuiltinCallAnnotations, format=Format.STRING)),
)


# Shadow hard and ordinary builtin names at module level (kept at end of file).
vars = int
dir = str
locals = float
eval = bytes
exec = tuple
super = list
format = dict
ascii = frozenset


def _shadowedModuleBuiltinAnnotations(
    a: vars,
    b: dir,
    c: locals,
    d: eval,
    e: exec,
    g: super,
    h: format,
    i: ascii,
) -> f"{_num}/{_non_ascii!a}":
    return (a, b, c, d, e, g, h, i)


print(
    "Shadowed module builtin annotations (VALUE):",
    displayDict(
        get_annotations(_shadowedModuleBuiltinAnnotations, format=Format.VALUE)
    ),
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
