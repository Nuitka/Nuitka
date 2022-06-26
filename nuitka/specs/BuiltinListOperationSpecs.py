#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""List operation specs. """

from nuitka import Options

from .BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    BuiltinParameterSpecNoKeywords,
)

class ListMethodSpecNoKeywords(BuiltinParameterSpecNoKeywords):
    __slots__ = ()

    def __init__(
        self,
        name,
        arg_names=(),
        default_count=0,
    ):
        BuiltinParameterSpecNoKeywords.__init__(
            self,
            name="list." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=None,
            dict_star_arg=None,
            pos_only_args=(),
            kw_only_args=(),
        )


class ListMethodSpec(BuiltinParameterSpec):
    __slots__ = ()

    def __init__(
        self,
        name,
        arg_names=(),
        default_count=0,
        list_star_arg=None,
        dict_star_arg=None,
    ):
        BuiltinParameterSpec.__init__(
            self,
            name="list." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
            pos_only_args=(),
            kw_only_args=(),
        )


# Python3 only
list_clear_spec = ListMethodSpecNoKeywords("clear", arg_names=())

list_append_spec = ListMethodSpecNoKeywords("append", arg_names=("object",))
list_copy_spec = ListMethodSpecNoKeywords("copy", arg_names=())
list_count_spec = ListMethodSpecNoKeywords("count", arg_names=("value",))
list_extend_spec = ListMethodSpecNoKeywords("extend", arg_names=("iterable",))
list_index_spec = ListMethodSpecNoKeywords("index", arg_names=("value", "start", "stop"), default_count=2)
list_insert_spec = ListMethodSpecNoKeywords("insert", arg_names=("index", "object"))
list_pop_spec = ListMethodSpecNoKeywords("pop", arg_names=("index",), default_count=1)
list_remove_spec = ListMethodSpecNoKeywords("remove", arg_names=("value",))
list_reverse_spec = ListMethodSpecNoKeywords("reverse", arg_names=())

list_sort_spec = ListMethodSpec("sort", arg_names=("key", "reverse"), default_count=1)




















