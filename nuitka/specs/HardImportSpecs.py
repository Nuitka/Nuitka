#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Hard import specs.

Centralized here for code generation purposes. When a spec gets added here,
it automatically creates a reference node and a base class for the call node
to use.
"""

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytes,
    tshape_dict,
    tshape_str,
)

from .BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    BuiltinParameterSpecNoKeywords,
)

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
importlib_resources_backport_read_binary_spec = BuiltinParameterSpec(
    "importlib_resources.read_binary",
    ("package", "resource"),
    default_count=0,
    type_shape=tshape_bytes,
)
importlib_resources_read_text_since_313_spec = BuiltinParameterSpec(
    "importlib.resources.read_text",
    ("package",),
    list_star_arg="resources",
    kw_only_args=("encoding", "errors"),
    default_count=2,
    type_shape=tshape_str,
)
importlib_resources_read_text_before_313_spec = BuiltinParameterSpec(
    "importlib.resources.read_text",
    ("package", "resource", "encoding", "errors"),
    default_count=2,
    type_shape=tshape_str,
)
importlib_resources_backport_read_text_spec = BuiltinParameterSpec(
    "importlib_resources.read_text",
    ("package", "resource", "encoding", "errors"),
    default_count=2,
    type_shape=tshape_str,
)
importlib_resources_files_spec = BuiltinParameterSpec(
    "importlib.resources.files",
    ("package",),
    default_count=0,
)
importlib_resources_backport_files_spec = BuiltinParameterSpec(
    "importlib_resources.files",
    ("package",),
    default_count=0,
)


# os functions:
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
os_path_dirname_spec = BuiltinParameterSpec("os.path.dirname", ("p",), default_count=0)
os_path_normpath_spec = BuiltinParameterSpec(
    "os.path.normpath", ("path",), default_count=0
)
os_path_abspath_spec = BuiltinParameterSpec(
    "os.path.abspath", ("path",), default_count=0
)
os_path_isabs_spec = BuiltinParameterSpec(
    "os.path.isabs", ("s",), default_count=0, type_shape=tshape_bool
)

os_listdir_spec = BuiltinParameterSpec("os.listdir", ("path",), default_count=1)

os_stat_spec = BuiltinParameterSpec(
    "os.stat", ("path",), kw_only_args=("dir_fd", "follow_symlinks"), default_count=2
)
os_lstat_spec = BuiltinParameterSpec(
    "os.lstat", ("path",), kw_only_args=("dir_fd",), default_count=1
)

ctypes_cdll_since_38_spec = BuiltinParameterSpec(
    "ctypes.CDLL",
    (
        "name",
        "mode",
        "handle",
        "use_errno",
        "use_last_error",
        "winmode",  # spell-checker: ignore winmode
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
        "use_last_error",
    ),
    default_count=4,
)

sys_exit_spec = BuiltinParameterSpecNoKeywords(
    "sys.exit", ("exit_code",), default_count=1
)

# Tensorflow

tensorflow_function_spec = BuiltinParameterSpec(
    "tensorflow.function",
    (
        "func",
        "input_signature",
        "autograph",
        "jit_compile",
        "reduce_retracing",
        "experimental_implements",
        "experimental_autograph_options",
        "experimental_attributes",
        "experimental_relax_shapes",
        "experimental_compile",
        "experimental_follow_type_hints",
    ),
    default_count=11,
)

# networkx.utils.decorators

# TODO: Disabled for now, keyword only arguments and star list argument are
# having ordering issues for call matching and code generation.

# networkx_argmap_spec = BuiltinParameterSpec(
#     "networkx.utils.decorators.argmap",
#     ("func",),
#     default_count=1,
#     list_star_arg="args",
#     kw_only_args=("try_finally",),
# )

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
