#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import re

from nuitka.Tracing import scons_details_logger, scons_logger
from nuitka.utils.Download import getCachedDownload

from .DataComposerInterface import getConstantBlobFilename
from .SconsHacks import myDetectVersion
from .SconsUtils import (
    addToPATH,
    createEnvironment,
    decideArchMismatch,
    getExecutablePath,
    getLinkerArch,
    getMsvcVersion,
    getMsvcVersionString,
    isGccName,
    raiseNoCompilerFoundErrorExit,
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


def enableLtoSettings(env, lto_mode, msvc_mode):
    if msvc_mode and not lto_mode and getMsvcVersion(env) >= 14:
        lto_mode = True

    # Tell compiler to use link time optimization for MSVC
    if msvc_mode and lto_mode:
        env.Append(CCFLAGS=["/GL"])
        env.Append(LINKFLAGS=["/LTCG"])

    return lto_mode


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


def checkWindowsCompilerFound(env, target_arch, msvc_version, assume_yes_for_downloads):
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
                scons_logger.info(
                    "Mismatch between Python binary (%r -> %r) and C compiler (%r -> %r) arches, ignored!"
                    % (
                        os.environ["NUITKA_PYTHON_EXE_PATH"],
                        linker_arch,
                        compiler_path,
                        compiler_arch,
                    )
                )

                # This will trigger using it to use our own gcc in branch below.
                compiler_path = None
                env["CC"] = None

        if compiler_path is not None and msvc_version is not None:
            # Requested a specific MSVC version, check if that worked.
            if msvc_version != getMsvcVersionString(env):
                scons_logger.info(
                    "Failed to find requested MSVC version (%r != %r)."
                    % (msvc_version, getMsvcVersionString(env))
                )

                # This will trigger error exit in branch below.
                compiler_path = None
                env["CC"] = None

        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            if isGccName(the_cc_name):
                gcc_version = myDetectVersion(env, compiler_path)

                min_version = (8,)
                if gcc_version is not None and gcc_version < min_version:
                    scons_logger.info(
                        "Too old gcc %r (%r < %r) ignored!"
                        % (compiler_path, gcc_version, min_version)
                    )

                    # This also will trigger using it to use our own gcc in branch below.
                    compiler_path = None
                    env["CC"] = None

        if compiler_path is None and msvc_version is None:
            # This will succeed to find "gcc.exe" when conda install m2w64-gcc has
            # been done.
            compiler_path = getDownloadedGccPath(
                target_arch=target_arch,
                assume_yes_for_downloads=assume_yes_for_downloads,
            )
            addToPATH(env, os.path.dirname(compiler_path), prefix=True)

            env = createEnvironment(
                mingw_mode=True,
                msvc_version=None,
                target_arch=target_arch,
            )

            env["CC"] = compiler_path

        if env["CC"] is None:
            raiseNoCompilerFoundErrorExit()

    return env


def decideConstantsBlobResourceMode(gcc_mode, clang_mode, lto_mode):
    if "NUITKA_RESOURCE_MODE" in os.environ:
        resource_mode = os.environ["NUITKA_RESOURCE_MODE"]
        reason = "user provided"
    elif os.name == "nt":
        resource_mode = "win_resource"
        reason = "default for Windows"
    elif lto_mode and gcc_mode and not clang_mode:
        resource_mode = "linker"
        reason = "default for lto gcc with --lto bugs for incbin"
    else:
        # All is done already, this is for most platforms.
        resource_mode = "incbin"
        reason = "default"

    return resource_mode, reason


def addConstantBlobFile(
    env, resource_desc, source_dir, c11_mode, mingw_mode, target_arch
):
    resource_mode, reason = resource_desc

    constants_bin_filename = getConstantBlobFilename(source_dir)

    scons_details_logger.info(
        "Using resource mode: '%s' (%s)." % (resource_mode, reason)
    )

    if resource_mode == "win_resource":
        # On Windows constants can be accessed as a resource by Nuitka runtime afterwards.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_RESOURCE"])
    elif resource_mode == "incbin":
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_INCBIN"])

        constants_generated_filename = os.path.join(source_dir, "__constants_data.c")

        with open(constants_generated_filename, "w") as output:
            output.write(
                """
#define INCBIN_PREFIX
#define INCBIN_STYLE INCBIN_STYLE_SNAKE
#define INCBIN_LOCAL
#ifdef _NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS
#define INCBIN_OUTPUT_SECTION ".data"
#endif

#include "nuitka/incbin.h"

INCBIN(constant_bin, "__constants.bin");

unsigned char const *getConstantsBlobData() {
    return constant_bin_data;
}
"""
            )

    elif resource_mode == "linker":
        # Indicate "linker" resource mode.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_LINKER"])

        env.Append(
            LINKFLAGS=[
                "-Wl,-b",
                "-Wl,binary",
                "-Wl,%s" % constants_bin_filename,
                "-Wl,-b",
                "-Wl,%s"
                % getLinkerArch(target_arch=target_arch, mingw_mode=mingw_mode),
                "-Wl,-defsym",
                "-Wl,%sconstant_bin_data=_binary_%s___constants_bin_start"
                % (
                    "_" if mingw_mode else "",
                    "".join(re.sub("[^a-zA-Z0-9_]", "_", c) for c in source_dir),
                ),
            ]
        )
    elif resource_mode == "code":
        # Indicate "code" resource mode.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_CODE"])

        constants_generated_filename = os.path.join(source_dir, "__constants_data.c")

        def writeConstantsDataSource():
            with open(constants_generated_filename, "w") as output:
                if not c11_mode:
                    output.write('extern "C" ')

                output.write("const unsigned char constant_bin_data[] =\n{\n")

                with open(constants_bin_filename, "rb") as f:
                    content = f.read()
                for count, stream_byte in enumerate(content):
                    if count % 16 == 0:
                        if count > 0:
                            output.write("\n")

                        output.write("   ")

                    if str is bytes:
                        stream_byte = ord(stream_byte)

                    output.write(" 0x%02x," % stream_byte)

                output.write("\n};\n")

        writeConstantsDataSource()
    else:
        scons_logger.sysexit(
            "Error, illegal resource mode %r specified" % resource_mode
        )


def enableWindowsStackSize(env, msvc_mode, mingw_mode, target_arch):
    # Stack size 4MB or 8MB, we might need more than the default 1MB.
    if target_arch == "x86_64":
        stack_size = 1024 * 1204 * 8
    else:
        stack_size = 1024 * 1204 * 4

    if msvc_mode:
        env.Append(LINKFLAGS=["/STACK:%d" % stack_size])

    if mingw_mode:
        env.Append(LINKFLAGS=["-Wl,--stack,%d" % stack_size])


def enableExperimentalSettings(env, experimental_flags):
    for experimental_flag in experimental_flags:
        if experimental_flag:
            if "=" in experimental_flag:
                experiment, value = experimental_flag.split("=", 1)
            else:
                experiment = experimental_flag
                value = None

            # Allowing for nice names on command line, but using identifiers for C.
            experiment = experiment.upper().replace("-", "_")

            if value:
                env.Append(CPPDEFINES=[("_NUITKA_EXPERIMENTAL_%s" % experiment, value)])
            else:
                env.Append(CPPDEFINES=["_NUITKA_EXPERIMENTAL_%s" % experiment])
