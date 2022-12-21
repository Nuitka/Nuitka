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
"""Bytes operation specs.

Python3 only, Python2 has no bytes, but only str
"""

from nuitka import Options
from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytes,
    tshape_int,
    tshape_list,
    tshape_str,
    tshape_tuple,
)

from .BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    BuiltinParameterSpecNoKeywords,
)


# TODO: Should be shared, this is duplicate for other types currently.
class MethodKeywordErrorCompatibilityMixin(object):
    def getKeywordRefusalText(self):
        if Options.is_full_compat:
            assert "." in self.name, self.name

            try:
                eval(  # These are harmless calls, pylint: disable=eval-used
                    "b''.%s(x=1)" % self.name.split(".")[-1]
                )
            except TypeError as e:
                return str(e)
            else:
                assert False, self.name
        else:
            return "%s() takes no keyword arguments" % self.name


class BytesMethodSpecNoKeywords(
    MethodKeywordErrorCompatibilityMixin, BuiltinParameterSpecNoKeywords
):
    __slots__ = ()

    def __init__(self, name, arg_names=(), default_count=0, type_shape=None):
        BuiltinParameterSpecNoKeywords.__init__(
            self,
            name="bytes." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=None,
            dict_star_arg=None,
            pos_only_args=(),
            kw_only_args=(),
            type_shape=type_shape,
        )


class BytesMethodSpec(BuiltinParameterSpec):
    __slots__ = ()

    def __init__(
        self,
        name,
        arg_names=(),
        default_count=0,
        list_star_arg=None,
        dict_star_arg=None,
        type_shape=None,
    ):
        BuiltinParameterSpec.__init__(
            self,
            name="bytes." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
            pos_only_args=(),
            kw_only_args=(),
            type_shape=type_shape,
        )


bytes_decode_spec = BytesMethodSpec(
    "decode", arg_names=("encoding", "errors"), default_count=2, type_shape=tshape_str
)

bytes_join_spec = BytesMethodSpecNoKeywords(
    "join", arg_names=("iterable",), type_shape=tshape_bytes
)
bytes_partition_spec = BytesMethodSpecNoKeywords(
    "partition", arg_names=("sep",), type_shape=tshape_tuple
)
bytes_rpartition_spec = BytesMethodSpecNoKeywords(
    "rpartition", arg_names=("sep",), type_shape=tshape_tuple
)
bytes_strip_spec = BytesMethodSpecNoKeywords(
    "strip", arg_names=("chars",), default_count=1, type_shape=tshape_bytes
)
bytes_lstrip_spec = BytesMethodSpecNoKeywords(
    "lstrip", arg_names=("chars",), default_count=1, type_shape=tshape_bytes
)
bytes_rstrip_spec = BytesMethodSpecNoKeywords(
    "rstrip", arg_names=("chars",), default_count=1, type_shape=tshape_bytes
)
bytes_find_spec = BytesMethodSpecNoKeywords(
    "find", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)
bytes_rfind_spec = BytesMethodSpecNoKeywords(
    "rfind", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)
bytes_index_spec = BytesMethodSpecNoKeywords(
    "index", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)
bytes_rindex_spec = BytesMethodSpecNoKeywords(
    "rindex", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)

bytes_split_spec = BytesMethodSpec(
    "split", arg_names=("sep", "maxsplit"), default_count=2, type_shape=tshape_list
)
bytes_rsplit_spec = BytesMethodSpec(
    "rsplit", arg_names=("sep", "maxsplit"), default_count=2, type_shape=tshape_list
)

bytes_startswith_spec = BytesMethodSpecNoKeywords(
    "startswith",
    arg_names=("prefix", "start", "end"),
    default_count=2,
    type_shape=tshape_bool,
)
bytes_endswith_spec = BytesMethodSpecNoKeywords(
    "endswith",
    arg_names=("suffix", "start", "end"),
    default_count=2,
    type_shape=tshape_bool,
)

bytes_replace_spec = BytesMethodSpecNoKeywords(
    "replace",
    arg_names=("old", "new", "count"),
    default_count=1,
    type_shape=tshape_bytes,
)

bytes_count_spec = BytesMethodSpecNoKeywords(
    "count", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)

bytes_capitalize_spec = BytesMethodSpecNoKeywords(
    "capitalize", arg_names=(), type_shape=tshape_bytes
)
bytes_upper_spec = BytesMethodSpecNoKeywords(
    "upper", arg_names=(), type_shape=tshape_bytes
)
bytes_lower_spec = BytesMethodSpecNoKeywords(
    "lower", arg_names=(), type_shape=tshape_bytes
)
bytes_swapcase_spec = BytesMethodSpecNoKeywords(
    "swapcase", arg_names=(), type_shape=tshape_bytes
)
bytes_title_spec = BytesMethodSpecNoKeywords(
    "title", arg_names=(), type_shape=tshape_bytes
)
bytes_isalnum_spec = BytesMethodSpecNoKeywords(
    "isalnum", arg_names=(), type_shape=tshape_bool
)
bytes_isalpha_spec = BytesMethodSpecNoKeywords(
    "isalpha", arg_names=(), type_shape=tshape_bool
)
bytes_isdigit_spec = BytesMethodSpecNoKeywords(
    "isdigit", arg_names=(), type_shape=tshape_bool
)
bytes_islower_spec = BytesMethodSpecNoKeywords(
    "islower", arg_names=(), type_shape=tshape_bool
)
bytes_isupper_spec = BytesMethodSpecNoKeywords(
    "isupper", arg_names=(), type_shape=tshape_bool
)
bytes_isspace_spec = BytesMethodSpecNoKeywords(
    "isspace", arg_names=(), type_shape=tshape_bool
)
bytes_istitle_spec = BytesMethodSpecNoKeywords(
    "istitle", arg_names=(), type_shape=tshape_bool
)

# Python2 only, Python3 this is in bytes
bytes_decode_spec = BytesMethodSpec(
    "decode", arg_names=("encoding", "errors"), default_count=2, type_shape=tshape_str
)

bytes_expandtabs_spec = BytesMethodSpec(
    "expandtabs", arg_names=("tabsize",), default_count=1, type_shape=tshape_bytes
)

bytes_center_spec = BytesMethodSpecNoKeywords(
    "center", arg_names=("width", "fillchar"), default_count=1, type_shape=tshape_bytes
)
bytes_ljust_spec = BytesMethodSpecNoKeywords(
    "ljust", arg_names=("width", "fillchar"), default_count=1, type_shape=tshape_bytes
)
bytes_rjust_spec = BytesMethodSpecNoKeywords(
    "rjust", arg_names=("width", "fillchar"), default_count=1, type_shape=tshape_bytes
)
bytes_zfill_spec = BytesMethodSpecNoKeywords(
    "zfill", arg_names=("width",), type_shape=tshape_bytes
)
bytes_translate_spec = BytesMethodSpecNoKeywords(
    "translate", arg_names=("table", "delete"), default_count=1, type_shape=tshape_bytes
)
bytes_splitlines_spec = BytesMethodSpec(
    "splitlines", arg_names=("keepends"), default_count=1, type_shape=tshape_list
)
