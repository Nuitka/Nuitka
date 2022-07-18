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
"""Dictionary operation specs. """

from .BuiltinParameterSpecs import (
    BuiltinParameterSpecNoKeywords,
    BuiltinParameterSpecSinglePosArgStarDictArgs,
)


class DictMethodSpec(BuiltinParameterSpecNoKeywords):
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
            name="dict." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
            pos_only_args=pos_only_args,
            kw_only_args=kw_only_args,
        )


dict_copy_spec = DictMethodSpec("copy")
dict_clear_spec = DictMethodSpec("clear")

dict_items_spec = DictMethodSpec("items")
dict_iteritems_spec = DictMethodSpec("iteritems")
dict_viewitems_spec = DictMethodSpec("viewitems")

dict_keys_spec = DictMethodSpec("keys")
dict_iterkeys_spec = DictMethodSpec("iterkeys")
dict_viewkeys_spec = DictMethodSpec("viewkeys")

dict_values_spec = DictMethodSpec("values")
dict_itervalues_spec = DictMethodSpec("itervalues")
dict_viewvalues_spec = DictMethodSpec("viewvalues")

dict_get_spec = DictMethodSpec("get", arg_names=("key", "default"), default_count=1)

dict_has_key_spec = DictMethodSpec("has_key", arg_names=("key",))

dict_setdefault_spec = DictMethodSpec(
    "setdefault", arg_names=("key", "default"), default_count=1
)

dict_pop_spec = DictMethodSpec("pop", arg_names=("key", "default"), default_count=1)

dict_popitem_spec = DictMethodSpec("popitem")

dict_update_spec = BuiltinParameterSpecSinglePosArgStarDictArgs(
    "dict.update", list_star_arg="iterable", dict_star_arg="pairs"
)
