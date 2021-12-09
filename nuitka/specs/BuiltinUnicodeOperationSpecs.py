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
"""Unicode operation specs, Python2 only. """

from .BuiltinParameterSpecs import BuiltinParameterSpecNoKeywords


class UnicodeMethodSpec(BuiltinParameterSpecNoKeywords):
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
            name="unicode." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
            pos_only_args=pos_only_args,
            kw_only_args=kw_only_args,
        )


unicode_join_spec = UnicodeMethodSpec("join", arg_names=("iterable",))
unicode_partition_spec = UnicodeMethodSpec("partition", arg_names=("sep",))
unicode_rpartition_spec = UnicodeMethodSpec("rpartition", arg_names=("sep",))
unicode_strip_spec = UnicodeMethodSpec("strip", arg_names=("chars",), default_count=1)
unicode_lstrip_spec = UnicodeMethodSpec("lstrip", arg_names=("chars",), default_count=1)
unicode_rstrip_spec = UnicodeMethodSpec("rstrip", arg_names=("chars",), default_count=1)
unicode_find_spec = UnicodeMethodSpec(
    "find", arg_names=("sub", "start", "end"), default_count=2
)
unicode_rfind_spec = UnicodeMethodSpec(
    "rfind", arg_names=("sub", "start", "end"), default_count=2
)
unicode_index_spec = UnicodeMethodSpec(
    "index", arg_names=("sub", "start", "end"), default_count=2
)
unicode_rindex_spec = UnicodeMethodSpec(
    "rindex", arg_names=("sub", "start", "end"), default_count=2
)
unicode_split_spec = UnicodeMethodSpec(
    "split", arg_names=("sep", "maxsplit"), default_count=2
)
unicode_rsplit_spec = UnicodeMethodSpec(
    "rsplit", arg_names=("sep", "maxsplit"), default_count=2
)

unicode_startswith_spec = UnicodeMethodSpec(
    "startswith", arg_names=("prefix", "start", "end"), default_count=2
)
unicode_endswith_spec = UnicodeMethodSpec(
    "endswith", arg_names=("suffix", "start", "end"), default_count=2
)

unicode_replace_spec = UnicodeMethodSpec(
    "replace", arg_names=("old", "new", "count"), default_count=1
)


unicode_capitalize_spec = UnicodeMethodSpec("capitalize", arg_names=())
unicode_upper_spec = UnicodeMethodSpec("upper", arg_names=())
unicode_lower_spec = UnicodeMethodSpec("lower", arg_names=())
unicode_swapcase_spec = UnicodeMethodSpec("swapcase", arg_names=())
unicode_title_spec = UnicodeMethodSpec("title", arg_names=())
unicode_isalnum_spec = UnicodeMethodSpec("isalnum", arg_names=())
unicode_isalpha_spec = UnicodeMethodSpec("isalpha", arg_names=())
unicode_isdigit_spec = UnicodeMethodSpec("isdigit", arg_names=())
unicode_islower_spec = UnicodeMethodSpec("islower", arg_names=())
unicode_isupper_spec = UnicodeMethodSpec("isupper", arg_names=())
unicode_isspace_spec = UnicodeMethodSpec("isspace", arg_names=())
unicode_istitle_spec = UnicodeMethodSpec("istitle", arg_names=())
