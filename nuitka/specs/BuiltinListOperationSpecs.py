#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_int_or_long,
    tshape_list,
    tshape_none,
)

from .BuiltinParameterSpecs import (
    BuiltinMethodParameterSpecBase,
    BuiltinMethodParameterSpecNoKeywordsBase,
)


class ListMethodSpecNoKeywords(BuiltinMethodParameterSpecNoKeywordsBase):
    __slots__ = ()

    method_prefix = "list"


class ListMethodSpec(BuiltinMethodParameterSpecBase):
    __slots__ = ()

    method_prefix = "list"


# Python3 only
list_clear_spec = ListMethodSpecNoKeywords(
    "clear", arg_names=(), type_shape=tshape_none
)

list_append_spec = ListMethodSpecNoKeywords(
    "append", arg_names=("item",), type_shape=tshape_none
)
list_copy_spec = ListMethodSpecNoKeywords("copy", arg_names=(), type_shape=tshape_list)
list_count_spec = ListMethodSpecNoKeywords(
    "count", arg_names=("value",), type_shape=tshape_int_or_long
)
list_extend_spec = ListMethodSpecNoKeywords(
    "extend", arg_names=("value",), type_shape=tshape_none
)
list_index_spec = ListMethodSpecNoKeywords(
    "index",
    arg_names=("value", "start", "stop"),
    default_count=2,
    type_shape=tshape_int_or_long,
)
list_insert_spec = ListMethodSpecNoKeywords(
    "insert", arg_names=("index", "item"), type_shape=tshape_none
)
list_pop_spec = ListMethodSpecNoKeywords("pop", arg_names=("index",), default_count=1)
list_remove_spec = ListMethodSpecNoKeywords(
    "remove", arg_names=("value",), type_shape=tshape_none
)
list_reverse_spec = ListMethodSpecNoKeywords(
    "reverse", arg_names=(), type_shape=tshape_none
)

# TODO: Version dependent with keyword only args in Python3
# list_sort_spec = ListMethodSpec(
#     "sort", arg_names=("key", "reverse"), default_count=2, type_shape=tshape_none
# )
