#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This contains the tuning of the compilers towards defined goals.

"""

import os
import re

from nuitka.Tracing import scons_details_logger, scons_logger
from nuitka.utils.Download import getCachedDownloadedMinGW64
from nuitka.utils.FileOperations import (
    getReportPath,
    openTextFile,
    putTextFileContents,
)
from nuitka.utils.Utils import (
    isFedoraBasedLinux,
    isMacOS,
    isPosixWindows,
    isWin32Windows,
)

from .SconsHacks import myDetectVersion
from .SconsUtils import (
    addBinaryBlobSection,
    addToPATH,
    createEnvironment,
    decideArchMismatch,
    getExecutablePath,
    getLinkerArch,
    getMsvcVersion,
    getMsvcVersionString,
    isClangName,
    isGccName,
    isZigName,
    raiseNoCompilerFoundErrorExit,
    setEnvironmentVariable,
)

# spell-checker: ignore LIBPATH,CPPDEFINES,CPPPATH,CXXVERSION,CCFLAGS,LINKFLAGS,CXXFLAGS
# spell-checker: ignore -flto,-fpartial-inlining,-freorder-functions,-defsym,-fprofile
# spell-checker: ignore -fwrapv,-Wunused,fcompare,-ftrack,-fvisibility,-municode,
# spell-checker: ignore -feliminate,noexecstack,implib
# spell-checker: ignore LTCG,GENPROFILE,USEPROFILE,CGTHREADS


def _detectWindowsSDK(env):
    # Caching
    if hasattr(env, "windows_sdk_version"):
        return env.windows_sdk_version

    # Check if there is a Windows SDK installed.
    if "WindowsSDKVersion" not in env:
        if "WindowsSDKVersion" in os.environ:
            windows_sdk_version = os.environ["WindowsSDKVersion"].rstrip("\\")
        else:
            windows_sdk_version = None
    else:
        windows_sdk_version = env["WindowsSDKVersion"]

    if windows_sdk_version:
        scons_details_logger.info("Using Windows SDK '%s'." % windows_sdk_version)

        env.windows_sdk_version = tuple(int(x) for x in windows_sdk_version.split("."))
    else:
        scons_logger.warning(
            """\
Windows SDK must be installed in Visual Studio for it to \
be usable with Nuitka. Use the Visual Studio installer for \
adding it."""
        )

        env.windows_sdk_version = None

    return env.windows_sdk_version


_windows_sdk_c11_mode_min_version = (10, 0, 19041, 0)


def _enableC11Settings(env):
    """Decide if C11 mode can be used and enable the C compile flags for it.

    Args:
        env - scons environment with compiler information

    Returns:
        bool - c11_mode flag
    """

    if env.clangcl_mode:
        c11_mode = True
    elif (
        env.msvc_mode
        and env.windows_sdk_version >= _windows_sdk_c11_mode_min_version
        and getMsvcVersion(env) >= (14, 3)
    ):
        c11_mode = True
    elif env.clang_mode:
        c11_mode = True

        # For now, zig doesn't support C11 mode in the form needed by Nuitka
        if isZigName(env.the_cc_name):
            c11_mode = False
    elif env.gcc_mode and env.gcc_version >= (5,):
        c11_mode = True
    else:
        c11_mode = False

    if c11_mode:
        if env.gcc_mode:
            env.Append(CFLAGS=["-std=c11"])
        elif env.msvc_mode:
            env.Append(CFLAGS=["/std:c11"])

    if env.msvc_mode and c11_mode:
        # Windows SDK shows this even in non-debug mode in C11 mode.
        env.Append(CCFLAGS=["/wd5105", "/wd4391"])

    if not c11_mode:
        env.Append(CPPDEFINES=["_NUITKA_NON_C11_MODE"])

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
    elif env.msvc_mode and getMsvcVersion(env) >= (14,):
        lto_mode = True
        reason = "known to be supported"
    elif env.nuitka_python:
        lto_mode = True
        reason = "known to be supported (Nuitka-Python)"
    elif env.fedora_python:
        lto_mode = True
        reason = "known to be supported (Fedora Python)"
    elif env.arch_python:
        lto_mode = True
        reason = "known to be supported (Arch Python)"
    elif (
        env.debian_python
        and env.gcc_mode
        and not env.clang_mode
        and env.gcc_version >= (6,)
    ):
        lto_mode = True
        reason = "known to be supported (Debian)"
    elif env.gcc_mode and "gnu-cc" in env.the_cc_name and env.anaconda_python:
        lto_mode = False
        reason = "known to be not supported (CondaCC)"
    elif isMacOS() and env.gcc_mode and env.clang_mode:
        if env.debugger_mode:
            lto_mode = False
            reason = "must be disabled to see line numbers (macOS clang)"
        else:
            lto_mode = True
            reason = "known to be supported (macOS clang)"
    elif env.mingw_mode and env.clang_mode:
        lto_mode = False
        reason = "known to not be supported (new MinGW64 Clang)"
    elif env.gcc_mode and env.mingw_mode and env.gcc_version >= (11, 2):
        lto_mode = True
        reason = "known to be supported (new MinGW64)"
    else:
        lto_mode = False
        reason = "not known to be supported"

    # Do not default to LTO for large compilations, unless asked for it.
    module_count_threshold = 250
    if (
        orig_lto_mode == "auto"
        and lto_mode
        and env.module_count > module_count_threshold
        and not env.nuitka_python
    ):
        lto_mode = False
        reason = "might to be too slow %s (>= %d threshold), force with --lto=yes" % (
            env.module_count,
            module_count_threshold,
        )

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
        if env.clang_mode:
            env.Append(CCFLAGS=["-flto"])
            env.Append(LINKFLAGS=["-flto"])
        else:
            env.Append(CCFLAGS=["-flto=%d" % job_count])
            env.Append(LINKFLAGS=["-flto=%d" % job_count])

            env.Append(CCFLAGS=["-fuse-linker-plugin", "-fno-fat-lto-objects"])
            env.Append(LINKFLAGS=["-fuse-linker-plugin"])

            # Need to tell the linker these things are OK.
            env.Append(LINKFLAGS=["-fpartial-inlining", "-freorder-functions"])

            if env.mingw_mode and "MAKE" not in os.environ:
                setEnvironmentVariable(env, "MAKE", "mingw32-make.exe")

    # Tell compiler to use link time optimization for MSVC
    if env.msvc_mode and lto_mode:
        env.Append(CCFLAGS=["/GL"])

        if not env.clangcl_mode:
            env.Append(LINKFLAGS=["/LTCG"])

            if getMsvcVersion(env) >= (14, 3):
                env.Append(LINKFLAGS=["/CGTHREADS:%d" % job_count])

    if orig_lto_mode == "auto":
        scons_details_logger.info(
            "LTO mode auto was resolved to mode: '%s' (%s)."
            % ("yes" if lto_mode else "no", reason)
        )

    env.lto_mode = lto_mode
    env.orig_lto_mode = orig_lto_mode

    # PGO configuration
    _enablePgoSettings(env, pgo_mode)


_python311_min_msvc_version = (14, 3)


def checkWindowsCompilerFound(
    env, target_arch, clang_mode, msvc_version, assume_yes_for_downloads
):
    """Remove compiler of wrong arch or too old gcc and replace with downloaded winlibs gcc."""
    # Many cases to deal with, pylint: disable=too-many-branches,too-many-statements

    if os.name == "nt":
        # On Windows, in case MSVC was not found and not previously forced, use the
        # winlibs MinGW64 as a download, and use it as a fallback.
        compiler_path = getExecutablePath(env["CC"], env=env)

        scons_details_logger.info(
            "Checking usability of binary '%s' from environment '%s'."
            % (compiler_path, env["CC"])
        )

        # On MSYS2, cannot use the POSIX compiler, drop that even before we check arches, since that
        # will of course still match.
        if env.msys2_mingw_python and compiler_path.endswith("/usr/bin/gcc.exe"):
            compiler_path = None

        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            # The MSVC can only be used with an Windows SDK installed, and for 3.11 we need it
            # to be a least a minimum version.
            if (
                not isGccName(the_cc_name)
                and not isClangName(the_cc_name)
                and (
                    _detectWindowsSDK(env) is None
                    or (
                        env.python_version is not None
                        and env.python_version >= (3, 11)
                        and _detectWindowsSDK(env) < _windows_sdk_c11_mode_min_version
                    )
                )
            ):
                # This will trigger using it to use our own gcc in branch below.
                compiler_path = None
                env["CC"] = None

        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            if clang_mode and not isClangName(the_cc_name):
                # This will trigger using it to use our own clang in branch below.
                compiler_path = None
                env["CC"] = None

        # Drop wrong arch compiler, most often found by scans. There might be wrong gcc or cl on the PATH.
        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            decision, linker_arch, compiler_arch = decideArchMismatch(
                target_arch=target_arch,
                the_cc_name=the_cc_name,
                compiler_path=compiler_path,
            )

            if decision:
                scons_logger.info(
                    """\
Mismatch between Python binary ('%s' -> '%s') and \
C compiler ('%s' -> '%s') arches, that compiler is ignored!"""
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
                    "Failed to find requested MSVC version ('%s' != '%s')."
                    % (msvc_version, getMsvcVersionString(env))
                )

                # This will trigger error exit in branch below.
                compiler_path = None
                env["CC"] = None

        # For Python3.11
        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            # The MSVC can only be used with an Windows SDK installed, and for 3.11 we need it
            # to be a least a minimum version.
            if (
                # This is actually OK to use like this, pylint: disable=bad-chained-comparison
                not isGccName(the_cc_name)
                and None is not env.python_version >= (3, 11)
                and getMsvcVersion(env) < _python311_min_msvc_version
            ):
                scons_logger.info(
                    """\
For Python version %s MSVC %s or later is required, not %s which is too old."""
                    % (
                        ".".join(str(d) for d in env.python_version),
                        ".".join(str(d) for d in _python311_min_msvc_version),
                        getMsvcVersionString(env),
                    )
                )

                # This will trigger error exit in branch below.
                compiler_path = None
                env["CC"] = None

        if compiler_path is not None:
            the_cc_name = os.path.basename(compiler_path)

            if isGccName(the_cc_name):
                if "force-accept-windows-gcc" not in env.experimental_flags:
                    scons_logger.info(
                        "Non downloaded winlibs-gcc '%s' is being ignored, Nuitka is very dependent on the precise one."
                        % (compiler_path,)
                    )

                    # This also will trigger using it to use our own gcc in branch below.
                    compiler_path = None
                    env["CC"] = None

        if compiler_path is None and msvc_version is None:
            scons_details_logger.info(
                "No usable C compiler, attempt fallback to winlibs gcc or clang."
            )

            # This will download "gcc.exe" (and "clang.exe") when all others have been
            # rejected and MSVC is not enforced.
            compiler_path = getCachedDownloadedMinGW64(
                target_arch=target_arch,
                assume_yes_for_downloads=assume_yes_for_downloads,
            )

            if compiler_path is not None:
                addToPATH(env, os.path.dirname(compiler_path), prefix=True)

                env = createEnvironment(
                    mingw_mode=True,
                    msvc_version=None,
                    target_arch=target_arch,
                    experimental=env.experimental_flags,
                    no_deployment=env.no_deployment_flags,
                    debug_modes=env.debug_modes_flags,
                )

                if clang_mode:
                    env["CC"] = os.path.join(
                        os.path.dirname(compiler_path), "clang.exe"
                    )

        if env["CC"] is None:
            raiseNoCompilerFoundErrorExit()

    return env


def decideConstantsBlobResourceMode(env, module_mode):
    if "NUITKA_RESOURCE_MODE" in os.environ:
        resource_mode = os.environ["NUITKA_RESOURCE_MODE"]
        reason = "user provided"
    elif isWin32Windows():
        resource_mode = "win_resource"
        reason = "default for Windows"
    elif isPosixWindows():
        resource_mode = "linker"
        reason = "default MSYS2 Posix"
    elif isMacOS():
        resource_mode = "mac_section"
        reason = "default for macOS"
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


def addConstantBlobFile(env, blob_filename, resource_desc, target_arch):
    resource_mode, reason = resource_desc

    assert blob_filename.endswith(".bin"), blob_filename

    scons_details_logger.info(
        "Using resource mode: '%s' (%s)." % (resource_mode, reason)
    )

    if resource_mode == "win_resource":
        # On Windows constants can be accessed as a resource by Nuitka at run time afterwards.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_RESOURCE"])
    elif resource_mode == "mac_section":
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_MACOS_SECTION"])

        addBinaryBlobSection(
            env=env,
            blob_filename=blob_filename,
            section_name=os.path.basename(blob_filename)[:-4].lstrip("_"),
        )
    elif resource_mode == "incbin":
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_INCBIN"])

        constants_generated_filename = os.path.join(
            env.source_dir, "__constants_data.c"
        )

        putTextFileContents(
            constants_generated_filename,
            contents=r"""
#define INCBIN_PREFIX
#define INCBIN_STYLE INCBIN_STYLE_SNAKE
#define INCBIN_LOCAL
#ifdef _NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS
#define INCBIN_OUTPUT_SECTION ".data"
#endif

#include "nuitka/incbin.h"

INCBIN(constant_bin, "%(blob_filename)s");

unsigned char const *getConstantsBlobData(void) {
    return constant_bin_data;
}
"""
            % {"blob_filename": blob_filename},
        )

    elif resource_mode == "linker":
        # Indicate "linker" resource mode.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_LINKER"])

        # For MinGW the symbol name to be used is more low level.
        constant_bin_link_name = "constant_bin_data"
        if env.mingw_mode:
            constant_bin_link_name = "_" + constant_bin_link_name

        env.Append(
            LINKFLAGS=[
                "-Wl,-b",
                "-Wl,binary",
                "-Wl,%s" % blob_filename,
                "-Wl,-b",
                "-Wl,%s"
                % getLinkerArch(
                    target_arch=target_arch,
                    mingw_mode=env.mingw_mode or isPosixWindows(),
                ),
                "-Wl,-defsym",
                "-Wl,%s=_binary_%s___constants_bin_start"
                % (
                    constant_bin_link_name,
                    "".join(re.sub("[^a-zA-Z0-9_]", "_", c) for c in env.source_dir),
                ),
            ]
        )
    elif resource_mode == "code":
        # Indicate "code" resource mode.
        env.Append(CPPDEFINES=["_NUITKA_CONSTANTS_FROM_CODE"])

        constants_generated_filename = os.path.join(
            env.source_dir, "__constants_data.c"
        )

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

                with open(blob_filename, "rb") as f:
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
            "Error, illegal resource mode '%s' specified" % resource_mode
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


def setupCCompiler(env, lto_mode, pgo_mode, job_count, onefile_compile):
    # This is driven by many branches on purpose and has a lot of things
    # to deal with for LTO checks and flags, pylint: disable=too-many-branches,too-many-statements

    # Enable LTO for compiler.
    _enableLtoSettings(
        env=env,
        lto_mode=lto_mode,
        pgo_mode=pgo_mode,
        job_count=job_count,
    )

    _enableC11Settings(env)

    if env.gcc_mode:
        # Support for gcc and clang, restricting visibility as much as possible.
        env.Append(CCFLAGS=["-fvisibility=hidden"])

        if not env.c11_mode:
            env.Append(CXXFLAGS=["-fvisibility-inlines-hidden"])

        if isWin32Windows() and hasattr(env, "source_dir"):
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

        # gcc compiler cf_protection option
        if env.cf_protection != "auto":
            env.Append(CCFLAGS=["-fcf-protection=%s" % env.cf_protection])
    # Support for clang.
    if "clang" in env.the_cc_name:
        env.Append(CCFLAGS=["-w"])
        env.Append(CPPDEFINES=["_XOPEN_SOURCE"])

        # Don't export anything by default, this should create smaller executables.
        env.Append(CCFLAGS=["-fvisibility=hidden", "-fvisibility-inlines-hidden"])

        if env.debug_mode and "allow-c-warnings" not in env.experimental_flags:
            env.Append(CCFLAGS=["-Wunused-but-set-variable"])

    # Support for macOS standalone to run on older OS versions.
    if isMacOS():
        setEnvironmentVariable(env, "MACOSX_DEPLOYMENT_TARGET", env.macos_min_version)

        target_flag = "--target=%s-macos%s" % (
            env.macos_target_arch,
            env.macos_min_version,
        )

        env.Append(CCFLAGS=[target_flag])
        env.Append(LINKFLAGS=[target_flag])

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
                    (
                        "-O3"
                        if env.nuitka_python
                        or os.name == "nt"
                        or not env.static_libpython
                        else "-O2"
                    )
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
                    (
                        "-O3"
                        if env.nuitka_python
                        or os.name == "nt"
                        or not env.static_libpython
                        else "-O2"
                    )
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

    _enableDebugSystemSettings(env, job_count=job_count)

    if env.gcc_mode and not env.noelf_mode:
        env.Append(LINKFLAGS=["-z", "noexecstack"])

    # For MinGW64 we need to tell the subsystem to target as well as to
    # automatically import everything used.
    if env.mingw_mode:
        if not env.clang_mode:
            env.Append(LINKFLAGS=["-Wl,--enable-auto-import"])

    # Even if console is forced, for Win32 it means to specify Windows
    # subsystem, we can still attach or create.
    if env.console_mode in ("attach", "disable"):
        if env.mingw_mode:
            env.Append(LINKFLAGS=["-Wl,--subsystem,windows"])
            env.Append(CPPDEFINES=["_NUITKA_WINMAIN_ENTRY_POINT"])
        elif env.msvc_mode:
            env.Append(LINKFLAGS=["/SUBSYSTEM:windows"])
            env.Append(CPPDEFINES=["_NUITKA_WINMAIN_ENTRY_POINT"])

    if env.console_mode == "attach" and os.name == "nt":
        env.Append(CPPDEFINES=["_NUITKA_ATTACH_CONSOLE_WINDOW"])

    if env.console_mode == "hide" and os.name == "nt":
        env.Append(CPPDEFINES=["_NUITKA_HIDE_CONSOLE_WINDOW"])
        env.Append(LIBS=["User32"])

    # Avoid dependency on MinGW libraries, spell-checker: ignore libgcc
    if env.mingw_mode and not env.clang_mode:
        env.Append(LINKFLAGS=["-static-libgcc"])

    # MinGW64 for 64 bits needs this due to CPython bugs.
    if env.mingw_mode and env.target_arch == "x86_64" and env.python_version < (3, 12):
        env.Append(CPPDEFINES=["MS_WIN64"])

    # For shell API usage to lookup app folders we need this. Note that on Windows ARM
    # we didn't manage to have a "shell32.lib" that is not considered corrupt, so we
    # have to do this.
    if env.msvc_mode and env.target_arch != "arm64":
        env.Append(LIBS=["Shell32"])

    # Since Fedora 36, the system Python will not link otherwise.
    if isFedoraBasedLinux():
        env.Append(CCFLAGS=["-fPIC"])

    # We use zlib for crc32 functionality
    zlib_inline_copy_dir = os.path.join(env.nuitka_src, "inline_copy", "zlib")
    if os.path.exists(os.path.join(zlib_inline_copy_dir, "crc32.c")):
        env.Append(
            CPPPATH=[
                zlib_inline_copy_dir,
            ],
        )
    else:
        # TODO: Should only happen for official Debian packages, and there we
        # can use the zlib static linking maybe, but for onefile it's not easy
        # to get it, so just use slow checksum for now.
        if onefile_compile:
            env.Append(CPPDEFINES=["_NUITKA_USE_OWN_CRC32"])
        else:
            env.Append(CPPDEFINES=["_NUITKA_USE_SYSTEM_CRC32"])
            env.Append(LIBS="z")


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


def _enableDebugSystemSettings(env, job_count):
    if env.unstripped_mode:
        # Use debug format, so we get good tracebacks from it.
        if env.gcc_mode:
            env.Append(LINKFLAGS=["-g"])
            env.Append(CCFLAGS=["-g"])

            if not env.clang_mode:
                env.Append(CCFLAGS=["-feliminate-unused-debug-types"])
        elif env.msvc_mode:
            env.Append(CCFLAGS=["/Z7"])

            # Higher MSVC versions need this for parallel compilation
            if job_count > 1 and getMsvcVersion(env) >= (11,):
                env.Append(CCFLAGS=["/FS"])

            env.Append(LINKFLAGS=["/DEBUG"])
    else:
        if env.gcc_mode:
            if isMacOS():
                env.Append(LINKFLAGS=["-Wno-deprecated-declarations"])
            elif not env.clang_mode:
                env.Append(LINKFLAGS=["-s"])


def switchFromGccToGpp(env):
    if not env.gcc_mode or env.clang_mode:
        env.gcc_version = None
        return

    the_compiler = getExecutablePath(env.the_compiler, env)

    if the_compiler is None:
        return

    env.gcc_version = myDetectVersion(env, the_compiler)

    if env.gcc_version is None:
        scons_logger.sysexit(
            """\
Error, failed to detect gcc version of backend compiler '%s'.
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
        if env.python_version < (3, 11):
            scons_logger.info(
                "The provided gcc is too old, switching to its g++ instead.",
                mnemonic="too-old-gcc",
            )

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
        else:
            scons_logger.sysexit(
                "Error, your gcc is too old for C11 support, install a newer one.",
                mnemonic="too-old-gcc",
            )


def reportCCompiler(env, context, output_func):
    cc_output = env.the_cc_name

    if env.the_cc_name == "cl":
        cc_output = "%s %s" % (env.the_cc_name, getMsvcVersionString(env))
    elif isGccName(env.the_cc_name):
        if env.gcc_version is None:
            env.gcc_version = myDetectVersion(env, env.the_compiler)

        cc_output = "%s %s" % (
            env.the_cc_name,
            ".".join(str(d) for d in env.gcc_version),
        )
    elif isClangName(env.the_cc_name):
        clang_version = myDetectVersion(env, env.the_cc_name)
        if clang_version is None:
            clang_version = "not found"
        else:
            clang_version = ".".join(str(d) for d in clang_version)

        cc_output = "%s %s" % (
            env.the_cc_name,
            clang_version,
        )
    else:
        cc_output = env.the_cc_name

    output_func(
        "%s C compiler: %s (%s)."
        % (context, getReportPath(env.the_compiler), cc_output)
    )


def importEnvironmentVariableSettings(env):
    """Import typical environment variables that compilation should use."""
    # spell-checker: ignore cppflags,cflags,ccflags,cxxflags,ldflags

    # Outside compiler settings are respected.
    if "CPPFLAGS" in os.environ:
        scons_logger.info(
            "Scons: Inherited CPPFLAGS='%s' variable." % os.environ["CPPFLAGS"]
        )
        env.Append(CPPFLAGS=os.environ["CPPFLAGS"].split())
    if "CFLAGS" in os.environ:
        scons_logger.info("Inherited CFLAGS='%s' variable." % os.environ["CFLAGS"])
        env.Append(CCFLAGS=os.environ["CFLAGS"].split())
    if "CCFLAGS" in os.environ:
        scons_logger.info("Inherited CCFLAGS='%s' variable." % os.environ["CCFLAGS"])
        env.Append(CCFLAGS=os.environ["CCFLAGS"].split())
    if "CXXFLAGS" in os.environ:
        scons_logger.info(
            "Scons: Inherited CXXFLAGS='%s' variable." % os.environ["CXXFLAGS"]
        )
        env.Append(CXXFLAGS=os.environ["CXXFLAGS"].split())

    # Outside linker flags are respected.
    if "LDFLAGS" in os.environ:
        scons_logger.info(
            "Scons: Inherited LDFLAGS='%s' variable." % os.environ["LDFLAGS"]
        )
        env.Append(LINKFLAGS=os.environ["LDFLAGS"].split())


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
