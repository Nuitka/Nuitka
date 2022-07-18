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
"""Bytes operation specs. """

from nuitka import Options

from .BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    BuiltinParameterSpecNoKeywords,
)


# TODO: Should be shared, this is duplicate for other types currently.
class MethodKeywordErrorCompatibilityMixin:
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


class BytesMethodSpecNoKeywords(
    MethodKeywordErrorCompatibilityMixin, BuiltinParameterSpecNoKeywords
):
    __slots__ = ()

    def __init__(
        self,
        name,
        arg_names=(),
        default_count=0,
    ):
        BuiltinParameterSpecNoKeywords.__init__(
            self,
            name="bytes." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=None,
            dict_star_arg=None,
            pos_only_args=(),
            kw_only_args=(),
        )


class BytesMethodSpec(BuiltinParameterSpec):
    __slots__ = ()

    def __init__(
        self,
        name,
        arg_names=(),
        default_count=0,
    ):
        BuiltinParameterSpec.__init__(
            self,
            name="bytes." + name,
            arg_names=arg_names,
            default_count=default_count,
            list_star_arg=None,
            dict_star_arg=None,
            pos_only_args=(),
            kw_only_args=(),
        )


# Python3 only, Python2 has no bytes
bytes_decode_spec = BytesMethodSpec(
    "decode", arg_names=("encoding", "errors"), default_count=2
)
