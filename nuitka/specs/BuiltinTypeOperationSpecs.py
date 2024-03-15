#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Type operation specs. """

from .BuiltinParameterSpecs import BuiltinMethodParameterSpecBase


class TypeMethodSpec(BuiltinMethodParameterSpecBase):
    """Method spec of exactly the `type` built-in value/type."""

    __slots__ = ()

    method_prefix = "type"


type___prepare___spec = TypeMethodSpec(
    name="__prepare__", list_star_arg="args", dict_star_arg="kwargs"
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
