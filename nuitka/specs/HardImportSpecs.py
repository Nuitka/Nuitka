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
""" Hard import specs.

Centralized here for code generation purposes. When a spec gets added here,
it automatically creates a reference node and a base class for the call node
to use.
"""

from .BuiltinParameterSpecs import BuiltinParameterSpec

pkg_resources_iter_entry_points_spec = BuiltinParameterSpec(
    "pkg_resources.iter_entry_points", ("group", "name"), default_count=1
)
pkg_resources_get_distribution_spec = BuiltinParameterSpec(
    "pkg_resources.get_distribution", ("dist",), default_count=0
)
pkg_resources_require_spec = BuiltinParameterSpec(
    "pkg_resources.require", (), default_count=0, list_star_arg="requirements"
)

importlib_metadata_distribution_spec = BuiltinParameterSpec(
    "importlib.metadata.distribution", ("distribution_name",), default_count=0
)
importlib_metadata_backport_distribution_spec = BuiltinParameterSpec(
    "importlib_metadata.distribution", ("distribution_name",), default_count=0
)
importlib_metadata_version_spec = BuiltinParameterSpec(
    "importlib.metadata.version", ("distribution_name",), default_count=0
)
importlib_metadata_backport_version_spec = BuiltinParameterSpec(
    "importlib_metadata.version", ("distribution_name",), default_count=0
)
importlib_metadata_metadata_spec = BuiltinParameterSpec(
    "importlib.metadata.metadata", ("distribution_name",), default_count=0
)
importlib_metadata_backport_metadata_spec = BuiltinParameterSpec(
    "importlib_metadata.metadata", ("distribution_name",), default_count=0
)
