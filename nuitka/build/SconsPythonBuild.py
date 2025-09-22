#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Helper functions for the Python build related scons files.

"""

import os

from nuitka.Tracing import scons_logger
from nuitka.utils.Utils import isLinux, isMacOS

# spell-checker: ignore ccversion,cflags,ccflags,werror,cppdefines,cpppath,
# spell-checker: ignore linkflags,libpath,libflags


def _detectPythonHeaderPath(env):
    if os.name == "nt":

        candidates = [
            # On Windows, the CPython official installation layout is relatively fixed,
            os.path.join(env.python_prefix_external, "include"),
            # On MSYS2 with MinGW64 Python, it is also the other form.
            os.path.join(
                env.python_prefix_external, "include", "python" + env.python_abi_version
            ),
            # For self-built Python on Windows, need to also add the "PC" directory,
            # that a normal install won't have.
            os.path.join(env.python_prefix_external, "PC"),
        ]
    else:
        # The python header path is a combination of python version and debug
        # indication, we make sure the headers are found by adding it to the C
        # include path.

        candidates = [
            os.path.join(
                env.python_prefix_external, "include", "python" + env.python_abi_version
            ),
            # CPython source code checkout
            os.path.join(env.python_prefix_external, "Include"),
            # Haiku specific paths:
            os.path.join(
                env.python_prefix_external,
                "develop/headers",
                "python" + env.python_abi_version,
            ),
        ]

        # Not all Python versions, have the ABI version to use for the debug version.
        if env.python_debug and "d" in env.python_abi_version:
            candidates.append(
                os.path.join(
                    env.python_prefix_external,
                    "include",
                    "python" + env.python_abi_version.replace("d", ""),
                )
            )

    for candidate in candidates:
        if os.path.exists(os.path.join(candidate, "Python.h")):
            yield candidate
            break
    else:
        if os.name == "nt":
            scons_logger.sysexit(
                """\
Error, you seem to be using the unsupported embeddable CPython distribution \
use a full Python instead.""",
                exit_code=27,  # Fatal error exit for scons
            )
        else:
            scons_logger.sysexit(
                """\
Error, no 'Python.h' %s headers can be found at '%s', dependency \
not satisfied!"""
                % ("debug" if env.python_debug else "development", candidates),
                exit_code=27,  # Fatal error exit for scons
            )

    if env.python_version >= (3, 13):
        # spell-checker: ignore mimalloc
        yield os.path.join(candidate, "internal", "mimalloc")

    if env.self_compiled_python_uninstalled:
        yield env.python_prefix_external


def applyPythonBuildSettings(env):
    env.Append(CPPPATH=list(_detectPythonHeaderPath(env)))

    if env.nuitka_python:
        env.Append(CPPDEFINES=["_NUITKA_PYTHON"])

    if env.static_libpython:
        env.Append(CPPDEFINES=["_NUITKA_STATIC_LIBPYTHON"])

    if env.python_debug:
        env.Append(CPPDEFINES=["Py_DEBUG"])

    if not env.gil_mode:
        env.Append(CPPDEFINES="Py_GIL_DISABLED")

    # We need "dl" in accelerated mode.
    if isLinux():
        env.Append(LIBS=["dl"])

    if not env.msvc_mode:
        env.Append(LIBS=["m"])

    if env.static_libpython:
        env.Append(CPPDEFINES=["Py_NO_ENABLE_SHARED"])


def addWin32PythonLib(env):
    # Make sure to locate the Python link library from multiple potential
    # locations (installed vs. self-built).
    if env.python_debug:
        win_lib_name = "python" + env.python_abi_version.replace(".", "") + "_d"
    else:
        win_lib_name = "python" + env.python_abi_version.replace(".", "")

    if env.python_version >= (3,):
        pc_build_dir = (
            "PCBuild/amd64" if env.target_arch == "x86_64" else "PCBuild/win32"
        )
    else:
        pc_build_dir = "PCBuild"

    for candidate in ("libs", pc_build_dir):
        win_lib_path = os.path.join(env.python_prefix_external, candidate)

        if os.path.exists(os.path.join(win_lib_path, win_lib_name + ".lib")):
            break
    else:
        scons_logger.sysexit("Error, cannot find '%s.lib' file." % win_lib_name)

    env.Append(LIBPATH=[win_lib_path])
    env.Append(LIBS=[win_lib_name])


def addPythonHaclLib(env, link_module_libs):
    if env.static_libpython and not isMacOS():
        if env.python_version >= (3, 14):
            hacl_version = "hacl_314"
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

        # Remove it from static link libraries as well, if present, so far they are
        # bugs and do not exist.
        link_module_libs = [
            link_module_lib
            for link_module_lib in link_module_libs
            if "libHacl_Hash_SHA2" not in link_module_lib
        ]


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
