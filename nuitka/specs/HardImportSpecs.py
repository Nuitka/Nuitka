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

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bytes,
    tshape_dict,
    tshape_str,
)

from .BuiltinParameterSpecs import BuiltinParameterSpec

# Metadata:

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

importlib_metadata_entry_points_before_310_spec = BuiltinParameterSpec(
    "importlib.metadata.entry_points", (), default_count=0, type_shape=tshape_dict
)
importlib_metadata_entry_points_since_310_spec = BuiltinParameterSpec(
    "importlib.metadata.entry_points", (), default_count=0, dict_star_arg="params"
)
importlib_metadata_backport_entry_points_spec = BuiltinParameterSpec(
    "importlib_metadata.entry_points", (), default_count=0, dict_star_arg="params"
)

# TODO: Once we have selectable group under control, we can do this too.
# importlib_metadata_backport_entry_points_spec = BuiltinParameterSpec(
#    "importlib_metadata.entry_points", (), default_count=0, type_shape=tshape_dict
# )

# Resources:

pkgutil_get_data_spec = BuiltinParameterSpec(
    "pkgutil.get_data", ("package", "resource"), default_count=0
)
pkg_resources_resource_string_spec = BuiltinParameterSpec(
    "pkg_resources.resource_string",
    ("package_or_requirement", "resource_name"),
    default_count=0,
)
pkg_resources_resource_stream_spec = BuiltinParameterSpec(
    "pkg_resources.resource_stream",
    ("package_or_requirement", "resource_name"),
    default_count=0,
)
importlib_resources_read_binary_spec = BuiltinParameterSpec(
    "importlib.resources.read_binary",
    ("package", "resource"),
    default_count=0,
    type_shape=tshape_bytes,
)
importlib_resources_read_text_spec = BuiltinParameterSpec(
    "importlib.resources.read_text",
    ("package", "resource", "encoding", "errors"),
    default_count=2,
    type_shape=tshape_str,
)

# os/sys functions:
os_uname_spec = BuiltinParameterSpec(
    "os.uname",
    (),
    default_count=0,
)

os_path_exists_spec = BuiltinParameterSpec("os.path.exists", ("path",), default_count=0)
os_path_isfile_spec = BuiltinParameterSpec("os.path.isfile", ("path",), default_count=0)
os_path_isdir_spec = BuiltinParameterSpec("os.path.isdir", ("path",), default_count=0)
os_path_basename_spec = BuiltinParameterSpec(
    "os.path.basename", ("p",), default_count=0
)

os_listdir_spec = BuiltinParameterSpec("os.listdir", ("path",), default_count=1)

ctypes_cdll_since_38_spec = BuiltinParameterSpec(
    "ctypes.CDLL",
    (
        "name",
        "mode",
        "handle",
        "use_errno",
        "use_lasterror",
        "winmode",
    ),
    default_count=5,
)

ctypes_cdll_before_38_spec = BuiltinParameterSpec(
    "ctypes.CDLL",
    (
        "name",
        "mode",
        "handle",
        "use_errno",
        "use_lasterror",
    ),
    default_count=4,
)
