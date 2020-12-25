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

from nuitka.utils.Download import getCachedDownload


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
