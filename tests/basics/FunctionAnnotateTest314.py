#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 function '__annotate__' behavior."""

import importlib
import importlib.metadata
import importlib.resources as _ir
import inspect
import io
import os
import os.path as _osp
from annotationlib import Format, call_annotate_function, get_annotations
from functools import singledispatch
from os.path import join as _osp_join
from typing import TypeVarTuple


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


def _opaque(value):
    return value


_Ts = TypeVarTuple("_Ts")
_op_true = _opaque(True)
_op_false = _opaque(False)
_op_num = _opaque(42)
_op_hex = _opaque("ff")
_op_float_str = _opaque("1.5")
_op_str = _opaque("hello_world")
_op_bytes = _opaque(b"hello_world")
_op_list = _opaque([1, 2, 3])
_op_dict = _opaque({"a": int, "b": str})
_op_char = _opaque("A")
_op_code = _opaque(65)


class _SuperBase:
    T = int


class _SuperSub(_SuperBase):
    T = str

    def method(self, x: super(_SuperSub, _SuperSub).T) -> list:
        def inner(y: super(_SuperSub, self).T):
            return y

        return inner


_inner_super_fn = _SuperSub().method(1)
print(
    "Super method annotations (method VALUE + inner VALUE/STRING):",
    displayDict(get_annotations(_SuperSub.method, format=Format.VALUE)),
    displayDict(get_annotations(_inner_super_fn, format=Format.VALUE)),
    displayDict(get_annotations(_inner_super_fn, format=Format.STRING)),
)


def _outsideSuperAnnotations(
    x: super(_SuperSub, _SuperSub).T,
    y: type(super(_SuperSub)),
):
    return (x, y)


print(
    "Outside super annotations (VALUE/STRING):",
    displayDict(get_annotations(_outsideSuperAnnotations, format=Format.VALUE)),
    displayDict(get_annotations(_outsideSuperAnnotations, format=Format.STRING)),
)


def _varCallHelper(*args, **kwargs):
    return (args, sorted(kwargs.items()))


def _builtinCallAnnotations1(
    a_getattr2: getattr(_attr_holder, _opaque("get")),
    a_getattr3: getattr(_attr_holder, _opaque("missing"), str),
    a_hasattr: hasattr(_attr_holder, _opaque("get")),
    a_isinstance: isinstance(_op_num, (int, str)),
    a_issubclass: issubclass(_opaque(bool), int),
    a_callable: callable(_opaque(len)),
    a_len: len(_op_list),
    a_int1: int(_opaque("42")),
    a_int2: int(_op_hex, 16),
    a_bool: bool(_op_num),
    a_float: float(_op_float_str),
    a_complex1: complex(_opaque(2)),
    a_complex2: complex(_opaque(2), _opaque(3)),
    a_bytes1: bytes(_opaque(3)),
    a_bytes2: bytes(_opaque("abc"), "utf-8"),
    a_bytes3: bytes(_opaque("abc"), "utf-8", "strict"),
    a_bytearray1: bytearray(_opaque(2)),
    a_bytearray2: bytearray(_opaque("abc"), "utf-8"),
    a_list: list(_opaque((1, 2))),
    a_tuple: tuple(_op_list),
    a_set: sorted(set(_opaque([2, 1, 2]))),
    a_range1: range(_opaque(4)),
    a_range2: range(_opaque(1), _opaque(4)),
    a_range3: range(_opaque(1), _opaque(6), _opaque(2)),
) -> type("DynAnnotType", (object,), {"tag": 7}).tag:
    return (
        a_getattr2,
        a_getattr3,
        a_hasattr,
        a_isinstance,
        a_issubclass,
        a_callable,
        a_len,
        a_int1,
        a_int2,
        a_bool,
        a_float,
        a_complex1,
        a_complex2,
        a_bytes1,
        a_bytes2,
        a_bytes3,
        a_bytearray1,
        a_bytearray2,
        a_list,
        a_tuple,
        a_set,
        a_range1,
        a_range2,
        a_range3,
    )


print(
    "Builtin call annotations 1 (VALUE):",
    displayDict(get_annotations(_builtinCallAnnotations1, format=Format.VALUE)),
)
print(
    "Builtin call annotations 1 (STRING):",
    displayDict(get_annotations(_builtinCallAnnotations1, format=Format.STRING)),
)


def _builtinCallAnnotations2(
    b_next1: next(iter(_op_list)),
    b_next2: next(iter(_opaque(())), float),
    b_any: any(_opaque([0, 1])),
    b_all: all(_op_list),
    b_sum1: sum(_op_list),
    b_sum2: sum(_op_list, 10),
    b_ord: ord(_op_char),
    b_chr: chr(_op_code),
    b_bin: bin(_op_num),
    b_oct: oct(_op_num),
    b_hex: hex(_op_num),
    b_id_is_int: isinstance(id(_op_str), int),
    b_hash: hash(_op_num),
    b_divmod: divmod(_op_num, 5),
    b_pow3: pow(_opaque(2), _opaque(5), _opaque(3)),
    b_round1: round(_opaque(3.6)),
    b_round2: round(_opaque(3.14159), 2),
    b_enum: list(enumerate(_opaque(["x", "y"]), 1)),
    b_zip: list(zip(_opaque([1, 2]), _opaque(["a", "b"]), strict=True)),
    b_rev: list(reversed(_op_list)),
    b_sorted: sorted(_opaque([3, 1, 2]), reverse=True),
    b_memview: bytes(memoryview(_op_bytes)),
    b_exc_val: ValueError("bad"),
    b_exc_imp: (
        ImportError("imp", name="pkg", path="/p").name,
        ImportError("imp", name="pkg", path="/p").path,
    ),
    b_exc_attr: AttributeError("ae", name="attr_x").name,
    b_exc_name: NameError("ne", name="var_y").name,
):
    return (
        b_next1,
        b_next2,
        b_any,
        b_all,
        b_sum1,
        b_sum2,
        b_ord,
        b_chr,
        b_bin,
        b_oct,
        b_hex,
        b_id_is_int,
        b_hash,
        b_divmod,
        b_pow3,
        b_round1,
        b_round2,
        b_enum,
        b_zip,
        b_rev,
        b_sorted,
        b_memview,
        b_exc_val,
        b_exc_imp,
        b_exc_attr,
        b_exc_name,
    )


print(
    "Builtin call annotations 2 (VALUE):",
    displayDict(get_annotations(_builtinCallAnnotations2, format=Format.VALUE)),
)
print(
    "Builtin call annotations 2 (STRING):",
    displayDict(get_annotations(_builtinCallAnnotations2, format=Format.STRING)),
)


def _unpackAndVarCallAnnotations(
    u_list: [*_Ts],
    u_tuple: (*_Ts,),
    u_set: {*_Ts},
    u_dict: {**_op_dict, "c": float},
    u_call: _varCallHelper(1, *_op_list, k=2),
    *args: *_Ts,
) -> tuple[int, *_Ts, str]:
    return (u_list, u_tuple, u_set, u_dict, u_call, args)


def _starKwargsCallAnnotation(
    u_call_kw: _varCallHelper(1, *_op_list, k=2, **_op_dict),
):
    return u_call_kw


print(
    "Unpack and var-call annotations (VALUE):",
    displayDict(get_annotations(_unpackAndVarCallAnnotations, format=Format.VALUE)),
    displayDict(get_annotations(_starKwargsCallAnnotation, format=Format.VALUE)),
)
print(
    "Unpack and var-call annotations (STRING):",
    displayDict(get_annotations(_unpackAndVarCallAnnotations, format=Format.STRING)),
)


def _forwardUnpackAnnotations(*args: *_UndefinedTuple) -> tuple[int, *_UndefinedTuple]:
    return args


_fwd_unpack = get_annotations(_forwardUnpackAnnotations, format=Format.FORWARDREF)
print(
    "Forward unpack annotations (FORWARDREF/STRING):",
    repr(_fwd_unpack["args"].__forward_arg__),
    len(_fwd_unpack["return"].__args__),
    displayDict(get_annotations(_forwardUnpackAnnotations, format=Format.STRING)),
)


def _containerAndStrBytesOpAnnotations(
    d_get2: {"k": _op_str}.get("k"),
    d_get3: {"k": _op_str}.get("z", int),
    d_in: "k" in {"k": _op_str},
    d_notin: "z" not in {"k": _op_str},
    d_copy: {"k": _op_str}.copy(),
    d_keys: list({"k": _op_str}.keys()),
    d_vals: list({"k": _op_str}.values()),
    d_items: list({"k": _op_str}.items()),
    d_fromkeys: dict.fromkeys([_op_char], int),
    l_count: [_op_char, "B"].count("A"),
    l_index: [_op_char, "B"].index("B"),
    s_split: ("pre_" + str(_op_str)).split("_", 1),
    s_strip: ("__" + str(_op_str) + "__").strip("_"),
    s_join: "-".join([str(_op_char), "Z"]),
    s_replace: ("pre_" + str(_op_str)).replace("_", "-", 1),
    s_encode: ("pre_" + str(_op_char)).encode("ascii"),
    s_format: "{0}:{k}".format(_op_char, k=_op_num),
    s_upper: ("pre_" + str(_op_str)).upper(),
    s_starts: ("pre_" + str(_op_str)).startswith("pre_"),
    b_decode: (b"pre_" + bytes(_op_bytes)).decode("ascii"),
    b_split: (b"pre_" + bytes(_op_bytes)).split(b"_", 1),
    b_strip: (b"__" + bytes(_op_bytes) + b"__").strip(b"_"),
    b_join: b"-".join([bytes(_op_bytes), b"end"]),
    b_replace: (b"pre_" + bytes(_op_bytes)).replace(b"_", b"-", 1),
) -> NotImplemented:
    return (
        d_get2,
        d_get3,
        d_in,
        d_notin,
        d_copy,
        d_keys,
        d_vals,
        d_items,
        d_fromkeys,
        l_count,
        l_index,
        s_split,
        s_strip,
        s_join,
        s_replace,
        s_encode,
        s_format,
        s_upper,
        s_starts,
        b_decode,
        b_split,
        b_strip,
        b_join,
        b_replace,
    )


print(
    "Container/str/bytes op annotations (VALUE):",
    displayDict(
        get_annotations(_containerAndStrBytesOpAnnotations, format=Format.VALUE)
    ),
)


def _containerAndStrBytesStringAnnotations(
    d_get: _op_dict.get("a", int),
    l_idx: _op_list.index(2),
    s_split: _op_str.split("_", 1),
    s_rep: _op_str.replace("_", "-"),
    b_dec: _op_bytes.decode("ascii"),
    b_split: _op_bytes.split(b"_"),
) -> NotImplemented:
    return (d_get, l_idx, s_split, s_rep, b_dec, b_split)


print(
    "Container/str/bytes op annotations (STRING):",
    displayDict(
        get_annotations(_containerAndStrBytesStringAnnotations, format=Format.STRING)
    ),
)


def _hardImportAnnotations(
    p_dirname: _osp.dirname(_opaque("dir/leaf")),
    p_basename: _osp.basename(_opaque("dir/leaf")),
    p_normpath: _osp.normpath(_opaque("dir//leaf")),
    p_isabs: _osp.isabs(_opaque("/abs/path")),
    p_exists: _osp.exists(_opaque(".")),
    p_from_join: _osp_join(_opaque("x"), "y"),
    m_import: importlib.import_module(_opaque("math")).__name__,
    m_meta_ver: callable(importlib.metadata.version),
    m_res_files: callable(_ir.files),
):
    return (
        p_dirname,
        p_basename,
        p_normpath,
        p_isabs,
        p_exists,
        p_from_join,
        m_import,
        m_meta_ver,
        m_res_files,
    )


print(
    "Hard import annotations (VALUE):",
    displayDict(get_annotations(_hardImportAnnotations, format=Format.VALUE)),
)
print(
    "Hard import annotations (STRING):",
    displayDict(get_annotations(_hardImportAnnotations, format=Format.STRING)),
)


def _moduleAttrAnnotations(
    p_os_join: os.path.join(_opaque("dir"), "leaf"),
    dunder_name: __name__,
    dunder_pkg: __package__,
    dunder_spec: __spec__,
    dunder_loader: __loader__ is not None,
    dunder_file: bool(__file__),
):
    return (
        p_os_join,
        dunder_name,
        dunder_pkg,
        dunder_spec,
        dunder_loader,
        dunder_file,
    )


print(
    "Module attr annotations (VALUE):",
    displayDict(get_annotations(_moduleAttrAnnotations, format=Format.VALUE)),
)


_side_log = []


def _raiseInElseAnnotation(
    x: int if _op_true else (_side_log.append("else_hit"), 1 / 0)[-1],
):
    return x


def _raiseInIfAnnotation(
    x: (_side_log.append("if_hit"), 1 / 0)[-1] if _op_true else int,
):
    return x


print(
    "Raise branch annotation (STRING, no side effects):",
    displayDict(get_annotations(_raiseInElseAnnotation, format=Format.STRING)),
    _side_log,
)
try:
    get_annotations(_raiseInIfAnnotation, format=Format.VALUE)
except ZeroDivisionError as exc:
    print("Raise branch annotation (VALUE) ZeroDivisionError:", exc, _side_log)


def _lambdaAnnotations(
    l_empty: lambda: 1,
    l_pos_only: lambda a, b=1, /: (a, b),
    l_pos_and_normal: lambda a=1, /, b=2: (a, b),
    l_full: lambda a, b=1, *args, c, d=2, **kw: (a, b, args, c, d, sorted(kw.items())),
    l_kw_only_bare: lambda a, *, b=1, c: (a, b, c),
    l_kw_only_no_defaults: lambda *, x, y: (x, y),
    l_dynamic_defaults: lambda a=_op_num, *, b=_op_str: a + len(b),
    l_varargs_only: lambda *args, **kw: (args, sorted(kw.items())),
):
    return (
        l_empty,
        l_pos_only,
        l_pos_and_normal,
        l_full,
        l_kw_only_bare,
        l_kw_only_no_defaults,
        l_dynamic_defaults,
        l_varargs_only,
    )


_lambda_annots = get_annotations(_lambdaAnnotations, format=Format.VALUE)
print(
    "Lambda annotation signatures (VALUE):",
    displayDict(
        {
            key: (
                str(inspect.signature(fn)),
                fn.__defaults__,
                fn.__kwdefaults__,
                fn.__code__.co_posonlyargcount,
                fn.__code__.co_argcount,
                fn.__code__.co_kwonlyargcount,
                bool(fn.__code__.co_flags & inspect.CO_VARARGS),
                bool(fn.__code__.co_flags & inspect.CO_VARKEYWORDS),
            )
            for key, fn in _lambda_annots.items()
        }
    ),
)
print(
    "Lambda annotation calls:",
    _lambda_annots["l_empty"](),
    _lambda_annots["l_pos_only"](10),
    _lambda_annots["l_pos_and_normal"](),
    _lambda_annots["l_pos_and_normal"](3, b=4),
    _lambda_annots["l_full"](1, 2, 3, 4, c=5, extra=6),
    _lambda_annots["l_kw_only_bare"](7, c=8),
    _lambda_annots["l_kw_only_no_defaults"](x=1, y=2),
    _lambda_annots["l_dynamic_defaults"](),
    _lambda_annots["l_varargs_only"](1, 2, z=3),
)
try:
    _lambda_annots["l_pos_only"](a=1)
except TypeError as exc:
    print("Lambda pos-only TypeError:", type(exc).__name__)


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
