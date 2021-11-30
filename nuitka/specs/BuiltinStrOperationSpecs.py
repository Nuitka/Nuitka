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


# str_upper_spec = StrMethodSpec("upper")

str_join_spec = StrMethodSpec("join", arg_names=("iterable",))
str_partition_spec = StrMethodSpec("partition", arg_names=("sep",))
str_rpartition_spec = StrMethodSpec("rpartition", arg_names=("sep",))
str_strip_spec = StrMethodSpec("strip", arg_names=("chars",), default_count=1)
str_lstrip_spec = StrMethodSpec("lstrip", arg_names=("chars",), default_count=1)
str_rstrip_spec = StrMethodSpec("rstrip", arg_names=("chars",), default_count=1)
