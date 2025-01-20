#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Dictionary operation specs. """

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_dict,
    tshape_list,
    tshape_none,
    tshape_tuple,
)

from .BuiltinParameterSpecs import (
    BuiltinMethodParameterSpecBase,
    BuiltinParameterSpecSinglePosArgStarDictArgs,
)


class DictMethodSpec(BuiltinMethodParameterSpecBase):
    __slots__ = ()

    method_prefix = "dict"


dict_copy_spec = DictMethodSpec("copy", type_shape=tshape_dict)
dict_clear_spec = DictMethodSpec("clear", type_shape=tshape_none)

# items is the Python2 variant, iteritems is the Python3 variant of items
dict_items_spec = DictMethodSpec("items", type_shape=tshape_list)
dict_iteritems_spec = DictMethodSpec("iteritems")
dict_viewitems_spec = DictMethodSpec("viewitems")

# keys is the Python2 variant, iterkeys is the Python3 variant of keys
dict_keys_spec = DictMethodSpec("keys", type_shape=tshape_list)
dict_iterkeys_spec = DictMethodSpec("iterkeys")
dict_viewkeys_spec = DictMethodSpec("viewkeys")

# values is the Python2 variant, itervalues is the Python3 variant of keys
dict_values_spec = DictMethodSpec("values", type_shape=tshape_list)
dict_itervalues_spec = DictMethodSpec("itervalues")
dict_viewvalues_spec = DictMethodSpec("viewvalues")

dict_get_spec = DictMethodSpec("get", arg_names=("key", "default"), default_count=1)

dict_has_key_spec = DictMethodSpec(
    "has_key", arg_names=("key",), type_shape=tshape_bool
)

dict_setdefault_spec = DictMethodSpec(
    "setdefault", arg_names=("key", "default"), default_count=1
)

dict_pop_spec = DictMethodSpec("pop", arg_names=("key", "default"), default_count=1)

dict_popitem_spec = DictMethodSpec("popitem", type_shape=tshape_tuple)

dict_update_spec = BuiltinParameterSpecSinglePosArgStarDictArgs(
    "dict.update",
    list_star_arg="iterable",
    dict_star_arg="pairs",
    type_shape=tshape_none,
)

dict_fromkeys_spec = DictMethodSpec(
    "fromkeys", arg_names=("iterable", "value"), default_count=1, type_shape=tshape_dict
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
