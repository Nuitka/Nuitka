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
"""Str operation specs. """

from nuitka import Options
from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_int,
    tshape_list,
    tshape_str,
    tshape_tuple,
)

from .BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    BuiltinParameterSpecNoKeywords,
)


class MethodKeywordErrorCompatibilityMixin(object):
    def getKeywordRefusalText(self):
        if Options.is_full_compat:
            assert "." in self.name, self.name

            try:
                eval(  # These are harmless calls, pylint: disable=eval-used
                    "''.%s(x=1)" % self.name.split(".")[-1]
                )
            except TypeError as e:
                return str(e)
            else:
                assert False, self.name
        else:
            return "%s() takes no keyword arguments" % self.name


class StrMethodSpecNoKeywords(
    MethodKeywordErrorCompatibilityMixin, BuiltinParameterSpecNoKeywords
):
    __slots__ = ()

    def __init__(self, name, arg_names=(), default_count=0, type_shape=None):
        BuiltinParameterSpecNoKeywords.__init__(
            self,
            name="str." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=None,
            dict_star_arg=None,
            pos_only_args=(),
            kw_only_args=(),
            type_shape=type_shape,
        )


class StrMethodSpec(BuiltinParameterSpec):
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
            name="str." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=list_star_arg,
            dict_star_arg=dict_star_arg,
            pos_only_args=(),
            kw_only_args=(),
            type_shape=type_shape,
        )


str_join_spec = StrMethodSpecNoKeywords(
    "join", arg_names=("iterable",), type_shape=tshape_str
)
str_partition_spec = StrMethodSpecNoKeywords(
    "partition", arg_names=("sep",), type_shape=tshape_tuple
)
str_rpartition_spec = StrMethodSpecNoKeywords(
    "rpartition", arg_names=("sep",), type_shape=tshape_tuple
)
str_strip_spec = StrMethodSpecNoKeywords(
    "strip", arg_names=("chars",), default_count=1, type_shape=tshape_str
)
str_lstrip_spec = StrMethodSpecNoKeywords(
    "lstrip", arg_names=("chars",), default_count=1, type_shape=tshape_str
)
str_rstrip_spec = StrMethodSpecNoKeywords(
    "rstrip", arg_names=("chars",), default_count=1, type_shape=tshape_str
)
str_find_spec = StrMethodSpecNoKeywords(
    "find", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)
str_rfind_spec = StrMethodSpecNoKeywords(
    "rfind", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)
str_index_spec = StrMethodSpecNoKeywords(
    "index", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)
str_rindex_spec = StrMethodSpecNoKeywords(
    "rindex", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)

str_split_spec = (StrMethodSpecNoKeywords if str is bytes else StrMethodSpec)(
    "split", arg_names=("sep", "maxsplit"), default_count=2, type_shape=tshape_list
)
str_rsplit_spec = (StrMethodSpecNoKeywords if str is bytes else StrMethodSpec)(
    "rsplit", arg_names=("sep", "maxsplit"), default_count=2, type_shape=tshape_list
)

str_startswith_spec = StrMethodSpecNoKeywords(
    "startswith",
    arg_names=("prefix", "start", "end"),
    default_count=2,
    type_shape=tshape_bool,
)
str_endswith_spec = StrMethodSpecNoKeywords(
    "endswith",
    arg_names=("suffix", "start", "end"),
    default_count=2,
    type_shape=tshape_bool,
)

str_replace_spec = StrMethodSpecNoKeywords(
    "replace", arg_names=("old", "new", "count"), default_count=1, type_shape=tshape_str
)

str_count_spec = StrMethodSpecNoKeywords(
    "count", arg_names=("sub", "start", "end"), default_count=2, type_shape=tshape_int
)

str_format_spec = StrMethodSpec(
    "format", list_star_arg="args", dict_star_arg="pairs", type_shape=tshape_str
)

str_capitalize_spec = StrMethodSpecNoKeywords(
    "capitalize", arg_names=(), type_shape=tshape_str
)
str_upper_spec = StrMethodSpecNoKeywords("upper", arg_names=(), type_shape=tshape_str)
str_lower_spec = StrMethodSpecNoKeywords("lower", arg_names=(), type_shape=tshape_str)
str_swapcase_spec = StrMethodSpecNoKeywords(
    "swapcase", arg_names=(), type_shape=tshape_str
)
str_title_spec = StrMethodSpecNoKeywords("title", arg_names=(), type_shape=tshape_str)
str_isalnum_spec = StrMethodSpecNoKeywords(
    "isalnum", arg_names=(), type_shape=tshape_bool
)
str_isalpha_spec = StrMethodSpecNoKeywords(
    "isalpha", arg_names=(), type_shape=tshape_bool
)
str_isdigit_spec = StrMethodSpecNoKeywords(
    "isdigit", arg_names=(), type_shape=tshape_bool
)
str_islower_spec = StrMethodSpecNoKeywords(
    "islower", arg_names=(), type_shape=tshape_bool
)
str_isupper_spec = StrMethodSpecNoKeywords(
    "isupper", arg_names=(), type_shape=tshape_bool
)
str_isspace_spec = StrMethodSpecNoKeywords(
    "isspace", arg_names=(), type_shape=tshape_bool
)
str_istitle_spec = StrMethodSpecNoKeywords(
    "istitle", arg_names=(), type_shape=tshape_bool
)

str_encode_spec = StrMethodSpec(
    "encode",
    arg_names=("encoding", "errors"),
    default_count=2,
    # TODO: Resolve Python2/Python3 runtime differences
    #
    # type_shape=tshape_bytes
)

# Python2 only, Python3 this is in bytes
str_decode_spec = StrMethodSpec(
    "decode",
    arg_names=("encoding", "errors"),
    default_count=2
    # TODO: Resolve Python2/Python3 runtime differences
    #
    # type_shape=tshape_str_or_unicode
)

str_expandtabs_spec = (StrMethodSpecNoKeywords if str is bytes else StrMethodSpec)(
    "expandtabs", arg_names=("tabsize",), default_count=1, type_shape=tshape_str
)

str_center_spec = StrMethodSpecNoKeywords(
    "center", arg_names=("width", "fillchar"), default_count=1, type_shape=tshape_str
)
str_ljust_spec = StrMethodSpecNoKeywords(
    "ljust", arg_names=("width", "fillchar"), default_count=1, type_shape=tshape_str
)
str_rjust_spec = StrMethodSpecNoKeywords(
    "rjust", arg_names=("width", "fillchar"), default_count=1, type_shape=tshape_str
)
str_zfill_spec = StrMethodSpecNoKeywords(
    "zfill", arg_names=("width",), type_shape=tshape_str
)
str_translate_spec = StrMethodSpecNoKeywords(
    "translate", arg_names=("table",), type_shape=tshape_str
)
str_splitlines_spec = (StrMethodSpecNoKeywords if str is bytes else StrMethodSpec)(
    "splitlines", arg_names=("keepends"), default_count=1, type_shape=tshape_list
)
