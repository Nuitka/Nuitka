#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
"""Str operation specs. """

from .BuiltinParameterSpecs import BuiltinParameterSpecNoKeywords


class StrMethodSpec(BuiltinParameterSpecNoKeywords):
    __slots__ = ()

    def __init__(
        self,
        name,
        arg_names=(),
        default_count=0,
        list_star_arg=None,
        dict_star_arg=None,
        pos_only_args=(),
        kw_only_args=(),
    ):
        BuiltinParameterSpecNoKeywords.__init__(
            self,
            name="str." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
            pos_only_args=pos_only_args,
            kw_only_args=kw_only_args,
        )


str_join_spec = StrMethodSpec("join", arg_names=("iterable",))
str_partition_spec = StrMethodSpec("partition", arg_names=("sep",))
str_rpartition_spec = StrMethodSpec("rpartition", arg_names=("sep",))
str_strip_spec = StrMethodSpec("strip", arg_names=("chars",), default_count=1)
str_lstrip_spec = StrMethodSpec("lstrip", arg_names=("chars",), default_count=1)
str_rstrip_spec = StrMethodSpec("rstrip", arg_names=("chars",), default_count=1)
str_find_spec = StrMethodSpec(
    "find", arg_names=("sub", "start", "end"), default_count=2
)
str_rfind_spec = StrMethodSpec(
    "rfind", arg_names=("sub", "start", "end"), default_count=2
)
str_index_spec = StrMethodSpec(
    "index", arg_names=("sub", "start", "end"), default_count=2
)
str_rindex_spec = StrMethodSpec(
    "rindex", arg_names=("sub", "start", "end"), default_count=2
)

str_split_spec = StrMethodSpec("split", arg_names=("sep", "maxsplit"), default_count=2)
str_rsplit_spec = StrMethodSpec(
    "rsplit", arg_names=("sep", "maxsplit"), default_count=2
)

str_startswith_spec = StrMethodSpec(
    "startswith", arg_names=("prefix", "start", "end"), default_count=2
)
str_endswith_spec = StrMethodSpec(
    "endswith", arg_names=("suffix", "start", "end"), default_count=2
)

str_replace_spec = StrMethodSpec(
    "replace", arg_names=("old", "new", "count"), default_count=1
)

str_capitalize_spec = StrMethodSpec("capitalize", arg_names=())
str_upper_spec = StrMethodSpec("upper", arg_names=())
str_lower_spec = StrMethodSpec("lower", arg_names=())
str_swapcase_spec = StrMethodSpec("swapcase", arg_names=())
str_title_spec = StrMethodSpec("title", arg_names=())
str_isalnum_spec = StrMethodSpec("isalnum", arg_names=())
str_isalpha_spec = StrMethodSpec("isalpha", arg_names=())
str_isdigit_spec = StrMethodSpec("isdigit", arg_names=())
str_islower_spec = StrMethodSpec("islower", arg_names=())
str_isupper_spec = StrMethodSpec("isupper", arg_names=())
str_isspace_spec = StrMethodSpec("isspace", arg_names=())
str_istitle_spec = StrMethodSpec("istitle", arg_names=())
