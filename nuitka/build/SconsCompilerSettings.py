#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This contains the tuning of the compilers towards defined goals.

"""

import os

from nuitka.Tracing import scons_logger
from nuitka.utils.Download import getCachedDownload

from .SconsHacks import myDetectVersion
from .SconsUtils import (
    addToPATH,
    createEnvironment,
    decideArchMismatch,
    getExecutablePath,
    isGccName,
)


def enableC11Settings(env, clangcl_mode, msvc_mode, clang_mode, gcc_mode, gcc_version):
    """Decide if C11 mode can be used and enable the C compile flags for it.

    Args:
        clangcl_mode - clangcl.exe is used
        msvc_mode - bool MSVC is used
        clang_mode - bool clang is used
        gcc_mode - bool gcc is used
        gcc_version - bool version of gcc used if gcc_mode is true

    Returns:
        bool - c11_mode flag
    """

    if clangcl_mode:
        c11_mode = True
    elif msvc_mode:
        c11_mode = False

        # TODO: Once it includes updated Windows SDK, we could use C11 mode with it.
        # float(env.get("MSVS_VERSION", "0")) >= 14.2
    elif clang_mode:
        c11_mode = True
    elif gcc_mode and gcc_version >= (5,):
        c11_mode = True
    else:
        c11_mode = False

    if c11_mode:
        if gcc_mode:
            env.Append(CCFLAGS=["-std=c11"])
        elif msvc_mode:
            env.Append(CCFLAGS=["/std:c11"])

    return c11_mode


def getDownloadedGccPath(target_arch, assume_yes_for_downloads):
    # Large URLs, pylint: disable=line-too-long

    if target_arch == "x86_64":
        url = "https://github.com/brechtsanders/winlibs_mingw/releases/download/10.2.0-11.0.0-8.0.0-r5/winlibs-x86_64-posix-seh-gcc-10.2.0-llvm-11.0.0-mingw-w64-8.0.0-r5.zip"
        binary = r"mingw64\bin\gcc.exe"
    else:
        url = "https://github.com/brechtsanders/winlibs_mingw/releases/download/10.2.0-11.0.0-8.0.0-r5/winlibs-i686-posix-dwarf-gcc-10.2.0-llvm-11.0.0-mingw-w64-8.0.0-r5.zip"
        binary = r"mingw32\bin\gcc.exe"

    gcc_binary = getCachedDownload(
        url=url,
        is_arch_specific=True,
        specifity=url.rsplit("/", 2)[1],
        binary=binary,
        flatten=False,
        message="Nuitka will use gcc from MinGW64 of winlibs to compile on Windows.",
        reject="Only this specific gcc is supported with Nuitka.",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    return gcc_binary


def checkWindowsCompilerFound(env, target_arch, assume_yes_for_downloads):
    """Remove compiler of wrong arch or too old gcc and replace with downloaded winlibs gcc."""

    if os.name == "nt":
        # On Windows, in case MSVC was not found and not previously forced, use the
        # winlibs MinGW64 as a download, and use it as a fallback.
        compiler_path = getExecutablePath(env["CC"], env=env)

        # Drop wrong arch compiler, most often found by scans. There might be wrong gcc or cl on the PATH.
        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            decision, linker_arch, compiler_arch = decideArchMismatch(
                target_arch=target_arch,
                mingw_mode=isGccName(the_cc_name),
                msvc_mode=not isGccName(the_cc_name),
                the_cc_name=the_cc_name,
                compiler_path=compiler_path,
            )

            if decision:
                # This will trigger using it to use our own gcc in branch below.
                compiler_path = None

                scons_logger.info(
                    "Mismatch between Python binary (%r -> %r) and C compiler (%r -> %r) arches, ignored!"
                    % (
                        os.environ["NUITKA_PYTHON_EXE_PATH"],
                        linker_arch,
                        compiler_path,
                        compiler_arch,
                    )
                )

        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            if isGccName(the_cc_name):
                gcc_version = myDetectVersion(env, compiler_path)

                min_version = (8,)
                if gcc_version is not None and gcc_version < min_version:
                    # This also will trigger using it to use our own gcc in branch below.
                    compiler_path = None

                    scons_logger.info(
                        "Too old gcc %r (%r < %r) ignored!"
                        % (compiler_path, gcc_version, min_version)
                    )

        if compiler_path is None:
            # This will succeed to find "gcc.exe" when conda install m2w64-gcc has
            # been done.
            compiler_path = getDownloadedGccPath(
                target_arch=target_arch,
                assume_yes_for_downloads=assume_yes_for_downloads,
            )
            addToPATH(env, os.path.dirname(compiler_path), prefix=True)

            env = createEnvironment(
                tools=["mingw"],
                mingw_mode=True,
                msvc_version=None,
                target_arch=target_arch,
            )

            env["CC"] = compiler_path

    return env
