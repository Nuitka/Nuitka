#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Unicode operation specs, Python2 only. """

from .BuiltinParameterSpecs import (
    BuiltinMethodParameterSpecBase,
    BuiltinMethodParameterSpecNoKeywordsBase,
)


class UnicodeMethodSpecNoKeywords(BuiltinMethodParameterSpecNoKeywordsBase):
    __slots__ = ()

    method_prefix = "unicode"


class UnicodeMethodSpec(BuiltinMethodParameterSpecBase):
    __slots__ = ()

    method_prefix = "unicode"


unicode_join_spec = UnicodeMethodSpecNoKeywords("join", arg_names=("iterable",))
unicode_partition_spec = UnicodeMethodSpecNoKeywords("partition", arg_names=("sep",))
unicode_rpartition_spec = UnicodeMethodSpecNoKeywords("rpartition", arg_names=("sep",))
unicode_strip_spec = UnicodeMethodSpecNoKeywords(
    "strip", arg_names=("chars",), default_count=1
)
unicode_lstrip_spec = UnicodeMethodSpecNoKeywords(
    "lstrip", arg_names=("chars",), default_count=1
)
unicode_rstrip_spec = UnicodeMethodSpecNoKeywords(
    "rstrip", arg_names=("chars",), default_count=1
)
unicode_find_spec = UnicodeMethodSpecNoKeywords(
    "find", arg_names=("sub", "start", "end"), default_count=2
)
unicode_rfind_spec = UnicodeMethodSpecNoKeywords(
    "rfind", arg_names=("sub", "start", "end"), default_count=2
)
unicode_index_spec = UnicodeMethodSpecNoKeywords(
    "index", arg_names=("sub", "start", "end"), default_count=2
)
unicode_rindex_spec = UnicodeMethodSpecNoKeywords(
    "rindex", arg_names=("sub", "start", "end"), default_count=2
)
unicode_split_spec = UnicodeMethodSpecNoKeywords(
    "split", arg_names=("sep", "maxsplit"), default_count=2
)
unicode_rsplit_spec = UnicodeMethodSpecNoKeywords(
    "rsplit", arg_names=("sep", "maxsplit"), default_count=2
)

unicode_startswith_spec = UnicodeMethodSpecNoKeywords(
    "startswith", arg_names=("prefix", "start", "end"), default_count=2
)
unicode_endswith_spec = UnicodeMethodSpecNoKeywords(
    "endswith", arg_names=("suffix", "start", "end"), default_count=2
)

unicode_replace_spec = UnicodeMethodSpecNoKeywords(
    "replace", arg_names=("old", "new", "count"), default_count=1
)

unicode_count_spec = UnicodeMethodSpecNoKeywords(
    "count", arg_names=("sub", "start", "end"), default_count=2
)

unicode_format_spec = UnicodeMethodSpec(
    "format", list_star_arg="args", dict_star_arg="pairs"
)

unicode_capitalize_spec = UnicodeMethodSpecNoKeywords("capitalize", arg_names=())
unicode_upper_spec = UnicodeMethodSpecNoKeywords("upper", arg_names=())
unicode_lower_spec = UnicodeMethodSpecNoKeywords("lower", arg_names=())
unicode_swapcase_spec = UnicodeMethodSpecNoKeywords("swapcase", arg_names=())
unicode_title_spec = UnicodeMethodSpecNoKeywords("title", arg_names=())
unicode_isalnum_spec = UnicodeMethodSpecNoKeywords("isalnum", arg_names=())
unicode_isalpha_spec = UnicodeMethodSpecNoKeywords("isalpha", arg_names=())
unicode_isdigit_spec = UnicodeMethodSpecNoKeywords("isdigit", arg_names=())
unicode_islower_spec = UnicodeMethodSpecNoKeywords("islower", arg_names=())
unicode_isupper_spec = UnicodeMethodSpecNoKeywords("isupper", arg_names=())
unicode_isspace_spec = UnicodeMethodSpecNoKeywords("isspace", arg_names=())
unicode_istitle_spec = UnicodeMethodSpecNoKeywords("istitle", arg_names=())

unicode_encode_spec = UnicodeMethodSpec(
    "encode", arg_names=("encoding", "errors"), default_count=2
)

unicode_expandtabs_spec = UnicodeMethodSpecNoKeywords(
    "expandtabs", arg_names=("tabsize",), default_count=1
)

unicode_center_spec = UnicodeMethodSpecNoKeywords(
    "center", arg_names=("width", "fillchar"), default_count=1
)
unicode_ljust_spec = UnicodeMethodSpecNoKeywords(
    "ljust", arg_names=("width", "fillchar"), default_count=1
)
unicode_rjust_spec = UnicodeMethodSpecNoKeywords(
    "rjust", arg_names=("width", "fillchar"), default_count=1
)
unicode_zfill_spec = UnicodeMethodSpecNoKeywords("zfill", arg_names=("width",))
unicode_translate_spec = UnicodeMethodSpecNoKeywords("translate", arg_names=("table",))
unicode_splitlines_spec = UnicodeMethodSpecNoKeywords(
    "splitlines", arg_names=("keepends"), default_count=1
)

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
