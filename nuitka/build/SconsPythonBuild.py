#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Helper functions for the Python build related scons files."""

import os

from nuitka.Tracing import scons_logger
from nuitka.utils.Utils import isLinux, isMacOS

from .SconsUtils import getArgumentDefaulted, getArgumentRequired, isGccName

# spell-checker: ignore cppdefines,cpppath,linkflags,libpath


def _addPythonIncludePaths(env):
    python_include_paths = []

    adapted_python_header_files_dir = getArgumentDefaulted(
        "adapted_python_header_files_dir", ""
    )
    if adapted_python_header_files_dir:
        python_include_paths.append(adapted_python_header_files_dir)
        env.Append(CPPDEFINES=["_NUITKA_ADAPTED_PYTHON_HEADERS"])

    python_include_path = getArgumentRequired("python_include_path")
    python_include_paths.append(python_include_path)

    if env.python_version >= (3, 13):
        # spell-checker: ignore mimalloc
        python_include_paths.append(
            os.path.join(python_include_path, "internal", "mimalloc")
        )

    if env.self_compiled_python_uninstalled:
        python_include_paths.append(env.python_prefix_external)

    env.Append(CPPPATH=python_include_paths)


def _addPythonWarningSettings(env):
    if env.debug_mode:
        if env.gcc_mode:
            env.Append(
                CCFLAGS=[
                    # Unfortunately Py_INCREF(Py_False) triggers aliasing warnings,
                    # which are unfounded, so disable them.
                    "-Wno-error=strict-aliasing",
                    "-Wno-strict-aliasing",
                    # At least for self-compiled Python3.2, and MinGW this happens
                    # and has little use anyway.
                    "-Wno-error=format",
                    "-Wno-format",
                ]
            )

            if isGccName(env.the_cc_name):
                # Some Linux distro hardening injects "-Werror=format-security",
                # which would otherwise conflict with disabling format warnings.
                # spell-checker: ignore Werror
                env.Append(
                    CCFLAGS=[
                        "-Wno-error=format-security",
                    ]
                )

        elif env.msvc_mode:
            # Disable warnings that system headers already show.
            env.Append(
                CCFLAGS=[
                    "/W4",
                    "/wd4505",
                    "/wd4127",
                    "/wd4100",
                    "/wd4702",
                    "/wd4189",
                    "/wd4211",
                    "/wd4115",
                ]
            )

            # Disable warnings, that CPython headers already show.
            if env.python_version >= (3,):
                env.Append(CCFLAGS=["/wd4512", "/wd4510", "/wd4610"])

            if env.python_version >= (3, 13):
                env.Append(CCFLAGS=["/wd4324"])

            # We use null arrays in our structure Python declarations, which C11 does
            # not really allow, but should work.
            env.Append(CCFLAGS=["/wd4200"])

            # Do not show deprecation warnings, we will use methods for as long
            # as they work.
            env.Append(CCFLAGS=["/wd4996"])


def applyPythonBuildSettings(env):
    _addPythonIncludePaths(env)
    _addPythonWarningSettings(env)

    if env.monolithpy:
        env.Append(CPPDEFINES=["_MONOLITHPY"])

    if env.static_libpython:
        env.Append(CPPDEFINES=["_NUITKA_STATIC_LIBPYTHON"])

    if env.python_debug:
        env.Append(CPPDEFINES=["Py_DEBUG", "Py_NO_LINK_LIB"])

    if not env.gil_mode:
        env.Append(CPPDEFINES="Py_GIL_DISABLED")

    # We need "dl" in accelerated mode.
    if isLinux():
        env.Append(LIBS=["dl"])

    if not env.msvc_mode:
        env.Append(LIBS=["m"])

    if env.static_libpython:
        env.Append(CPPDEFINES=["Py_NO_ENABLE_SHARED"])

    if env.msvc_mode and (env.module_mode or env.dll_mode):
        # Make sure we handle import library on our own and put it into the
        # build directory, spell-checker: ignore IMPLIB
        env.no_import_lib = True
        env.Append(
            LINKFLAGS=[
                "/IMPLIB:%s" % os.path.join(env.source_dir, "import.lib"),
            ]
        )
    else:
        env.no_import_lib = False

    if env.deployment_mode:
        env.Append(CPPDEFINES=["_NUITKA_DEPLOYMENT_MODE"])

    if env.frozen_modules:
        env.Append(CPPDEFINES=["_NUITKA_FROZEN=%d" % env.frozen_modules])


def addWin32PythonLib(env):
    # Make sure to locate the Python link library from multiple potential
    # locations (installed vs. self-built).
    if env.msys2_mingw_python:
        win_lib_name = "libpython" + env.python_abi_version + ".dll.a"
        win_lib_filename = win_lib_name
    elif env.python_debug:
        win_lib_name = "python" + env.python_abi_version.replace(".", "") + "_d"
        win_lib_filename = win_lib_name + ".lib"
    else:
        win_lib_name = "python" + env.python_abi_version.replace(".", "")
        win_lib_filename = win_lib_name + ".lib"

    if env.python_version >= (3,):
        pc_build_dir = (
            "PCBuild\\amd64" if env.target_arch == "x86_64" else "PCBuild\\win32"
        )
    else:
        pc_build_dir = "PCBuild"

    for candidate in ("libs", "lib", pc_build_dir):
        win_lib_path = os.path.join(env.python_prefix_external, candidate)

        if os.path.exists(os.path.join(win_lib_path, win_lib_filename)):
            break
    else:
        scons_logger.sysexit(
            "Error, cannot find link library '%s' file." % win_lib_filename
        )

    env.Append(LIBPATH=[win_lib_path])
    env.Append(LIBS=[win_lib_name])


def addPythonHaclLib(env, link_module_libs):
    if env.static_libpython and not isMacOS():
        if env.python_version >= (3, 14):
            # Not practical anymore, to build it ourselves.
            hacl_version = None
        elif env.python_version >= (3, 12):
            hacl_version = "hacl_312"
        else:
            hacl_version = None

        if hacl_version is not None:
            env.Append(
                CPPPATH=[
                    os.path.join(
                        env.nuitka_src,
                        "inline_copy",
                        "python_hacl",
                        hacl_version,
                    ),
                    os.path.join(
                        env.nuitka_src,
                        "inline_copy",
                        "python_hacl",
                        hacl_version,
                        "include",
                    ),
                ]
            )

            env.Append(CPPDEFINES=["_NUITKA_INLINE_COPY_HACL"])

            # env.Append(CPPDEFINES=["HACL_CAN_COMPILE_VEC128"])
            env.Append(CPPDEFINES=["HACL_CAN_COMPILE_VEC256"])

    # Remove it from static link libraries unconditionally - libHacl_Hash_SHA2
    # is an internal CPython build artifact, never shipped as a standalone .a file.
    link_module_libs = [
        link_module_lib
        for link_module_lib in link_module_libs
        if "libHacl_Hash_SHA2" not in link_module_lib
    ]

    return link_module_libs


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
