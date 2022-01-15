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
from nuitka.utils.Download import getCachedDownloadedMinGW64
from nuitka.utils.FileOperations import openTextFile, putTextFileContents
from nuitka.utils.Utils import isMacOS, isWin32Windows

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
    setEnvironmentVariable,
)


def _detectWindowsSDK(env):
    # Check if there is a WindowsSDK installed.
    if env.msvc_mode or env.clangcl_mode:
        if "WindowsSDKVersion" not in env:
            if "WindowsSDKVersion" in os.environ:
                windows_sdk_version = os.environ["WindowsSDKVersion"].rstrip("\\")
            else:
                windows_sdk_version = None
        else:
            windows_sdk_version = env["WindowsSDKVersion"]

        if not windows_sdk_version:
            scons_logger.sysexit(
                "Error, the Windows SDK must be installed in Visual Studio."
            )

        scons_details_logger.info("Using Windows SDK '%s'." % windows_sdk_version)

        env.windows_sdk_version = tuple(int(x) for x in windows_sdk_version.split("."))


def _enableC11Settings(env):
    """Decide if C11 mode can be used and enable the C compile flags for it.

    Args:
        env - scons environment with compiler information

    Returns:
        bool - c11_mode flag
    """

    if env.clangcl_mode:
        c11_mode = True
    elif env.msvc_mode:
        # TODO: Make this experimental mode the default.
        c11_mode = (
            env.windows_sdk_version >= (10, 0, 19041, 0)
            and "msvc_c11" in env.experimental_flags
        )
    elif env.clang_mode:
        c11_mode = True
    elif env.gcc_mode and env.gcc_version >= (5,):
        c11_mode = True
    else:
        c11_mode = False

    if c11_mode:
        if env.gcc_mode:
            env.Append(CCFLAGS=["-std=c11"])
        elif env.msvc_mode:
            env.Append(CCFLAGS=["/std:c11"])

    if env.msvc_mode and c11_mode:
        # Windows SDK shows this even in non-debug mode in C11 mode.
        env.Append(CCFLAGS=["/wd5105"])

    scons_details_logger.info("Using C11 mode: %s" % c11_mode)

    env.c11_mode = c11_mode


def _enableLtoSettings(
    env,
    lto_mode,
    pgo_mode,
    job_count,
):
    # This is driven by branches on purpose and pylint: disable=too-many-branches,too-many-statements

    orig_lto_mode = lto_mode

    if lto_mode == "no":
        lto_mode = False
        reason = "disabled"
    elif lto_mode == "yes":
        lto_mode = True
        reason = "enabled"
    elif pgo_mode in ("use", "generate"):
        lto_mode = True
        reason = "PGO implies LTO"
    elif env.msvc_mode and getMsvcVersion(env) >= 14:
        lto_mode = True
        reason = "known to be supported"
    elif env.nuitka_python:
        lto_mode = True
        reason = "known to be supported (Nuitka-Python)"
    elif (
        env.debian_python
        and env.gcc_mode
        and not env.clang_mode
        and env.gcc_version >= (6,)
    ):
        lto_mode = True
        reason = "known to be supported (Debian)"
    elif env.gcc_mode and env.the_cc_name == "gnu-cc":
        lto_mode = True
        reason = "known to be supported (CondaCC)"
    elif env.mingw_mode and env.clang_mode:
        lto_mode = False
        reason = "known to not be supported (new MinGW64 Clang)"
    elif env.gcc_mode and env.mingw_mode and env.gcc_version >= (11, 2):
        lto_mode = True
        reason = "known to be supported (new MinGW64)"
    else:
        lto_mode = False
        reason = "not known to be supported"

    if lto_mode and env.gcc_mode and not env.clang_mode and env.gcc_version < (4, 6):
        scons_logger.warning(
            """\
The gcc compiler %s (version %s) doesn't have the sufficient \
version for lto mode (>= 4.6). Disabled."""
            % (env["CXX"], env["CXXVERSION"])
        )

        lto_mode = False
        reason = "gcc 4.6 is doesn't have good enough LTO support"

    if env.gcc_mode and lto_mode:
        env.Append(CCFLAGS=["-flto"])

        if env.clang_mode:
            env.Append(LINKFLAGS=["-flto"])
        else:
            env.Append(CCFLAGS=["-fuse-linker-plugin", "-fno-fat-lto-objects"])
            env.Append(LINKFLAGS=["-fuse-linker-plugin"])

            env.Append(LINKFLAGS=["-flto=%d" % job_count])

            # Need to tell the linker these things are OK.
            env.Append(LINKFLAGS=["-fpartial-inlining", "-freorder-functions"])

    # Tell compiler to use link time optimization for MSVC
    if env.msvc_mode and lto_mode:
        env.Append(CCFLAGS=["/GL"])

        if not env.clangcl_mode:
            env.Append(LINKFLAGS=["/LTCG"])

    if orig_lto_mode == "auto":
        scons_details_logger.info(
            "LTO mode auto was resolved to mode: '%s' (%s)."
            % ("yes" if lto_mode else "no", reason)
        )

    env.lto_mode = lto_mode

    # PGO configuration
    _enablePgoSettings(env, pgo_mode)


def checkWindowsCompilerFound(
    env, target_arch, clang_mode, msvc_version, assume_yes_for_downloads
):
    """Remove compiler of wrong arch or too old gcc and replace with downloaded winlibs gcc."""

    if os.name == "nt":
        # On Windows, in case MSVC was not found and not previously forced, use the
        # winlibs MinGW64 as a download, and use it as a fallback.
        compiler_path = getExecutablePath(env["CC"], env=env)

        scons_details_logger.info(
            "Checking usability of %r from %r" % (compiler_path, env["CC"])
        )

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
            if msvc_version == "latest":
                scons_logger.info(
                    "MSVC version resolved to %s." % getMsvcVersionString(env)
                )
            # Requested a specific MSVC version, check if that worked.
            elif msvc_version != getMsvcVersionString(env):
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

                min_version = (11, 2)
                if gcc_version is not None and (
                    gcc_version < min_version
                    or "force-winlibs-gcc" in env.experimental_flags
                ):
                    scons_logger.info(
                        "Too old gcc %r (%r < %r) ignored!"
                        % (compiler_path, gcc_version, min_version)
                    )

                    # This also will trigger using it to use our own gcc in branch below.
                    compiler_path = None
                    env["CC"] = None

        if compiler_path is None and msvc_version is None:
            scons_details_logger.info(
                "No usable C compiler, attempt fallback to winlibs gcc."
            )

            # This will download "gcc.exe" (and "clang.exe") when all others have been
            # rejected and MSVC is not enforced.
            compiler_path = getCachedDownloadedMinGW64(
                target_arch=target_arch,
                assume_yes_for_downloads=assume_yes_for_downloads,
            )
            addToPATH(env, os.path.dirname(compiler_path), prefix=True)

            env = createEnvironment(
                mingw_mode=True,
                msvc_version=None,
                target_arch=target_arch,
                experimental=env.experimental_flags,
            )

            if clang_mode:
                env["CC"] = os.path.join(os.path.dirname(compiler_path), "clang.exe")

        if env["CC"] is None:
            raiseNoCompilerFoundErrorExit()

    return env


def decideConstantsBlobResourceMode(env, module_mode):
    if "NUITKA_RESOURCE_MODE" in os.environ:
        resource_mode = os.environ["NUITKA_RESOURCE_MODE"]
        reason = "user provided"
    elif os.name == "nt":
        resource_mode = "win_resource"
        reason = "default for Windows"
    elif env.lto_mode and env.gcc_mode and not env.clang_mode:
        if module_mode:
            resource_mode = "code"
        else:
            resource_mode = "linker"

        reason = "default for lto gcc with --lto bugs for incbin"
    else:
        # All is done already, this is for most platforms.
        resource_mode = "incbin"
        reason = "default"

    return resource_mode, reason


def addConstantBlobFile(env, resource_desc, source_dir, target_arch):
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

        putTextFileContents(
            constants_generated_filename,
            contents="""\
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
""",
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
                % getLinkerArch(target_arch=target_arch, mingw_mode=env.mingw_mode),
                "-Wl,-defsym",
                "-Wl,%sconstant_bin_data=_binary_%s___constants_bin_start"
                % (
                    "_" if env.mingw_mode else "",
                    "".join(re.sub("[^a-zA-Z0-9_]", "_", c) for c in source_dir),
                ),
            ]
        )
    elif resource_mode == "code":
        # Indicate "code" resource mode.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_CODE"])

        constants_generated_filename = os.path.join(source_dir, "__constants_data.c")

        def writeConstantsDataSource():
            with openTextFile(constants_generated_filename, "w") as output:
                if not env.c11_mode:
                    output.write('extern "C" {')

                output.write(
                    """
// Constant data for the program.
#if !defined(_NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS)
const
#endif
unsigned char constant_bin_data[] =\n{\n
"""
                )

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

                if not env.c11_mode:
                    output.write("}")

        writeConstantsDataSource()
    else:
        scons_logger.sysexit(
            "Error, illegal resource mode %r specified" % resource_mode
        )


def enableWindowsStackSize(env, target_arch):
    # Stack size 4MB or 8MB, we might need more than the default 1MB.
    if target_arch == "x86_64":
        stack_size = 1024 * 1204 * 8
    else:
        stack_size = 1024 * 1204 * 4

    if env.msvc_mode:
        env.Append(LINKFLAGS=["/STACK:%d" % stack_size])

    if env.mingw_mode:
        env.Append(LINKFLAGS=["-Wl,--stack,%d" % stack_size])


def setupCCompiler(env, lto_mode, pgo_mode, job_count):
    # This is driven by many branches on purpose and has a lot of things
    # to deal with for LTO checks and flags, pylint: disable=too-many-branches,too-many-statements

    # Enable LTO for compiler.
    _enableLtoSettings(
        env=env,
        lto_mode=lto_mode,
        pgo_mode=pgo_mode,
        job_count=job_count,
    )

    _detectWindowsSDK(env)
    _enableC11Settings(env)

    if env.gcc_mode:
        # Support for gcc and clang, restricting visibility as much as possible.
        env.Append(CCFLAGS=["-fvisibility=hidden"])

        if not env.c11_mode:
            env.Append(CXXFLAGS=["-fvisibility-inlines-hidden"])

        if isWin32Windows():
            # On Windows, exporting to DLL need to be controlled.
            env.Append(LINKFLAGS=["-Wl,--exclude-all-symbols"])

            # Make sure we handle import library on our own and put it into the
            # build directory.
            env.Append(
                LINKFLAGS=[
                    "-Wl,--out-implib,%s" % os.path.join(env.source_dir, "import.lib")
                ]
            )

        # Make it clear how to handle integer overflows, namely by wrapping around
        # to negative values.
        env.Append(CCFLAGS=["-fwrapv"])

        if not env.low_memory:
            # Avoid IO for compilation as much as possible, this should make the
            # compilation more memory hungry, but also faster.
            env.Append(CCFLAGS="-pipe")

    # Support for clang.
    if "clang" in env.the_cc_name:
        env.Append(CCFLAGS=["-w"])
        env.Append(CPPDEFINES=["_XOPEN_SOURCE"])

        # Don't export anything by default, this should create smaller executables.
        env.Append(CCFLAGS=["-fvisibility=hidden", "-fvisibility-inlines-hidden"])

        if env.debug_mode:
            env.Append(CCFLAGS=["-Wunused-but-set-variable"])

    # Support for macOS standalone backporting.
    if isMacOS() and env.macos_minversion:
        setEnvironmentVariable(env, "MACOSX_DEPLOYMENT_TARGET", env.macos_minversion)

    # The 32 bits MinGW does not default for API level properly, so help it.
    if env.mingw_mode:
        # Windows XP
        env.Append(CPPDEFINES=["_WIN32_WINNT=0x0501"])

    # Unicode entry points for programs.
    if env.mingw_mode:
        env.Append(LINKFLAGS=["-municode"])

    # Detect the gcc version
    if env.gcc_version is None and env.gcc_mode and not env.clang_mode:
        env.gcc_version = myDetectVersion(env, env.the_compiler)

    # Older g++ complains about aliasing with Py_True and Py_False, but we don't
    # care.
    if env.gcc_mode and not env.clang_mode and env.gcc_version < (4, 5):
        env.Append(CCFLAGS=["-fno-strict-aliasing"])

    # For gcc 4.6 or higher, there are some new interesting functions.
    if env.gcc_mode and not env.clang_mode and env.gcc_version >= (4, 6):
        env.Append(CCFLAGS=["-fpartial-inlining"])

        if env.debug_mode:
            env.Append(CCFLAGS=["-Wunused-but-set-variable"])

    # Save some memory for gcc by not tracing macro code locations at all.
    if (
        not env.debug_mode
        and env.gcc_mode
        and not env.clang_mode
        and env.gcc_version >= (5,)
    ):
        env.Append(CCFLAGS=["-ftrack-macro-expansion=0"])

    # We don't care about deprecations.
    if env.gcc_mode and not env.clang_mode:
        env.Append(CCFLAGS=["-Wno-deprecated-declarations"])

    # The var-tracking does not scale, disable it. Should we really need it, we
    # can enable it. TODO: Does this cause a performance loss?
    if env.gcc_mode and not env.clang_mode:
        env.Append(CCFLAGS=["-fno-var-tracking"])

    # For large files, these can issue warnings about disabling
    # itself, while we do not need it really.
    if env.gcc_mode and not env.clang_mode and env.gcc_version >= (6,):
        env.Append(CCFLAGS=["-Wno-misleading-indentation"])

    # Disable output of notes, e.g. on struct alignment layout changes for
    # some arches, we don't care.
    if env.gcc_mode and not env.clang_mode:
        env.Append(CCFLAGS=["-fcompare-debug-second"])

    # Prevent using LTO when told not to use it, causes errors with some
    # static link libraries.
    if (
        env.gcc_mode
        and not env.clang_mode
        and env.static_libpython
        and not env.lto_mode
    ):
        env.Append(CCFLAGS=["-fno-lto"])
        env.Append(LINKFLAGS=["-fno-lto"])

    # Set optimization level for gcc and clang in LTO mode
    if env.gcc_mode and env.lto_mode:
        if env.debug_mode:
            env.Append(LINKFLAGS=["-Og"])
        else:
            # For LTO with static libpython combined, there are crashes with Python core
            # being inlined, so we must refrain from that. On Windows there is no such
            # thing, and Nuitka-Python is not affected.
            env.Append(
                LINKFLAGS=[
                    "-O3"
                    if env.nuitka_python or os.name == "nt" or not env.static_libpython
                    else "-O2"
                ]
            )

    # When debugging, optimize less than when optimizing, when not remove
    # assertions.
    if env.debug_mode:
        if env.clang_mode or (env.gcc_mode and env.gcc_version >= (4, 8)):
            env.Append(CCFLAGS=["-Og"])
        elif env.gcc_mode:
            env.Append(CCFLAGS=["-O1"])
        elif env.msvc_mode:
            env.Append(CCFLAGS=["-O2"])
    else:
        if env.gcc_mode:
            env.Append(
                CCFLAGS=[
                    "-O3"
                    if env.nuitka_python or os.name == "nt" or not env.static_libpython
                    else "-O2"
                ]
            )
        elif env.msvc_mode:
            env.Append(
                CCFLAGS=[
                    "/Ox",  # Enable most speed optimization
                    "/GF",  # Eliminate duplicate strings.
                    "/Gy",  # Function level object storage, to allow removing unused ones
                ]
            )

        env.Append(CPPDEFINES=["__NUITKA_NO_ASSERT__"])


def _enablePgoSettings(env, pgo_mode):
    if pgo_mode == "no":
        env.progressbar_name = "Backend"
    elif pgo_mode == "python":
        env.progressbar_name = "Python Profile"
        env.Append(CPPDEFINES=["_NUITKA_PGO_PYTHON"])
    elif pgo_mode == "generate":
        env.progressbar_name = "Profile"
        env.Append(CPPDEFINES=["_NUITKA_PGO_GENERATE"])

        if env.gcc_mode:
            env.Append(CCFLAGS=["-fprofile-generate"])
            env.Append(LINKFLAGS=["-fprofile-generate"])
        elif env.msvc_mode:
            env.Append(CCFLAGS=["/GL"])
            env.Append(LINKFLAGS=["/GENPROFILE:EXACT"])
            if not env.clangcl_mode:
                env.Append(LINKFLAGS=["/LTCG"])

        else:
            scons_logger.sysexit(
                "Error, PGO not supported for '%s' compiler." % env.the_cc_name
            )
    elif pgo_mode == "use":
        env.progressbar_name = "Backend"

        env.Append(CPPDEFINES=["_NUITKA_PGO_USE"])

        if env.gcc_mode:
            env.Append(CCFLAGS=["-fprofile-use"])
            env.Append(LINKFLAGS=["-fprofile-use"])
        elif env.msvc_mode:
            env.Append(CCFLAGS=["/GL"])
            env.Append(
                LINKFLAGS=[
                    "/USEPROFILE",
                ]
            )
        else:
            scons_logger.sysexit(
                "Error, PGO not supported for '%s' compiler." % env.the_cc_name
            )
    else:
        assert False, env.pgo_mode

    env.pgo_mode = pgo_mode


def switchFromGccToGpp(env):
    if not env.gcc_mode or env.clang_mode:
        env.gcc_version = None
        return

    env.gcc_version = myDetectVersion(env, env.the_compiler)

    if env.gcc_version is None:
        scons_logger.sysexit(
            """\
Error, failed to detect gcc version of backend compiler %r.
"""
            % env.the_compiler
        )

    if "++" in env.the_cc_name:
        scons_logger.sysexit(
            """\
Error, compiler %s is apparently a C++ compiler, specify a C compiler instead.
"""
            % env.the_cc_name
        )

    # Enforce the minimum version, selecting a potentially existing g++-4.5
    # binary if it's not high enough. This is esp. useful under Debian which
    # allows all compiler to exist next to each other and where g++ might not be
    # good enough, but g++-4.5 would be.
    if env.gcc_version < (4, 4):
        scons_logger.sysexit(
            """\
The gcc compiler %s (version %s) doesn't have the sufficient \
version (>= 4.4)."""
            % (env.the_compiler, env.gcc_version)
        )

    # CondaCC or newer.
    if env.mingw_mode and env.gcc_version < (5, 3):
        scons_logger.sysexit(
            """\
The MinGW64 compiler %s (version %s) doesn't have the sufficient \
version (>= 5.3)."""
            % (env.the_compiler, env.gcc_version)
        )

    if env.gcc_version < (5,):
        scons_logger.info("The provided gcc is too old, switching to its g++ instead.")

        # Switch to g++ from gcc then if possible, when C11 mode is false.
        the_gpp_compiler = os.path.join(
            os.path.dirname(env.the_compiler),
            os.path.basename(env.the_compiler).replace("gcc", "g++"),
        )

        if getExecutablePath(the_gpp_compiler, env=env):
            env.the_compiler = the_gpp_compiler
            env.the_cc_name = env.the_cc_name.replace("gcc", "g++")
        else:
            scons_logger.sysexit(
                "Error, your gcc is too old for C11 support, and no related g++ to workaround that is found."
            )


def reportCCompiler(env, context):
    cc_output = env.the_cc_name

    if env.the_cc_name == "cl":
        cc_output = "%s %s" % (env.the_cc_name, getMsvcVersionString(env))
    else:
        cc_output = env.the_cc_name

    scons_logger.info(
        "%s C compiler: %s (%s)." % (context, env.the_compiler, cc_output)
    )
