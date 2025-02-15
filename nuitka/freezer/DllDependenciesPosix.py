#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""DLL dependency scan methods for POSIX (Linux, *BSD, MSYS2).

"""

import os
import sys

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Execution import executeProcess, withEnvironmentPathAdded
from nuitka.utils.SharedLibraries import getSharedLibraryRPATHs
from nuitka.utils.Utils import (
    isAlpineLinux,
    isAndroidBasedLinux,
    isPosixWindows,
)

from .DllDependenciesCommon import getLdLibraryPath

# Detected Python rpath is cached.
_detected_python_rpaths = None

# Cached ldd results.
ldd_result_cache = {}


def _resolveOriginValue(rpath, origin):
    rpath = rpath.replace("$ORIGIN", origin)
    rpath = os.path.normpath(os.path.join(origin, rpath))

    return rpath


def detectBinaryPathDLLsPosix(dll_filename, package_name, original_dir):
    # This is complex, as it also includes the caching mechanism
    # pylint: disable=too-many-branches,too-many-locals

    if ldd_result_cache.get(dll_filename):
        return ldd_result_cache[dll_filename]

    # Ask "ldd" about the libraries being used by the created binary, these
    # are the ones that interest us.

    # This is the rpath of the Python binary, which will be effective when
    # loading the other DLLs too. This happens at least for Python installs
    # on Travis. pylint: disable=global-statement
    global _detected_python_rpaths
    if _detected_python_rpaths is None and not isPosixWindows():
        _detected_python_rpaths = getSharedLibraryRPATHs(sys.executable)

        if os.path.islink(sys.executable):
            sys_executable = os.readlink(sys.executable)
        else:
            sys_executable = sys.executable

        sys_executable_dir = os.path.dirname(sys_executable)

        _detected_python_rpaths = [
            _resolveOriginValue(rpath=detected_python_rpath, origin=sys_executable_dir)
            for detected_python_rpath in _detected_python_rpaths
        ]

    python_rpaths = _detected_python_rpaths[:]

    if os.path.islink(dll_filename):
        link_target_path = os.path.dirname(os.path.realpath(dll_filename))
        python_rpaths.append(link_target_path)

    # TODO: Actually would be better to pass it as env to the created process instead.
    with withEnvironmentPathAdded(
        "LD_LIBRARY_PATH",
        *getLdLibraryPath(
            package_name=package_name,
            python_rpaths=python_rpaths,
            original_dir=original_dir,
        )
    ):
        # TODO: Check exit code, should never fail.
        stdout, stderr, _exit_code = executeProcess(command=("ldd", dll_filename))

    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if not line.startswith(
            b"ldd: warning: you do not have execution permission for"
        )
    )

    inclusion_logger.debug("ldd output for %s is:\n%s" % (dll_filename, stdout))

    if stderr:
        inclusion_logger.debug("ldd error for %s is:\n%s" % (dll_filename, stderr))

    result = OrderedSet()

    for line in stdout.split(b"\n"):
        if not line:
            continue

        if b"=>" not in line:
            continue

        part = line.split(b" => ", 2)[1]

        if b"(" in part:
            filename = part[: part.rfind(b"(") - 1]
        else:
            filename = part

        if not filename:
            continue

        if str is not bytes:
            filename = filename.decode("utf8")

        # Sometimes might use stuff not found or supplied by ldd itself.
        if filename in ("not found", "ldd"):
            continue

        # Normalize, sometimes the DLLs produce "something/../", this has
        # been seen with Qt at least.
        filename = os.path.normpath(filename)

        # Do not include kernel DLLs on the ignore list.
        filename_base = os.path.basename(filename)
        if any(
            filename_base == entry or filename_base.startswith(entry + ".")
            for entry in _linux_dll_ignore_list
        ):
            continue

        # Do not allow relative paths for shared libraries
        if not os.path.isabs(filename):
            inclusion_logger.sysexit(
                "Error: Found a dependency with a relative path. Was a dependency copied to dist early? "
                + filename
            )

        result.add(filename)

    ldd_result_cache[dll_filename] = result

    sub_result = OrderedSet(result)

    for sub_dll_filename in result:
        sub_result = sub_result.union(
            detectBinaryPathDLLsPosix(
                dll_filename=sub_dll_filename,
                package_name=package_name,
                original_dir=original_dir,
            )
        )

    return sub_result


_linux_dll_ignore_list = [
    # Do not include kernel / glibc specific libraries. This list has been
    # assembled by looking what are the most common .so files provided by
    # glibc packages from ArchLinux, Debian Stretch and CentOS.
    #
    # Online sources:
    #  - https://centos.pkgs.org/7/puias-computational-x86_64/glibc-aarch64-linux-gnu-2.24-2.sdl7.2.noarch.rpm.html
    #  - https://centos.pkgs.org/7/centos-x86_64/glibc-2.17-222.el7.x86_64.rpm.html
    #  - https://archlinux.pkgs.org/rolling/archlinux-core-x86_64/glibc-2.28-5-x86_64.pkg.tar.xz.html
    #  - https://packages.debian.org/stretch/amd64/libc6/filelist
    #
    # Note: This list may still be incomplete. Some additional libraries
    # might be provided by glibc - it may vary between the package versions
    # and between Linux distros. It might or might not be a problem in the
    # future, but it should be enough for now.
    "linux-vdso.so.1",
    "ld-linux-x86-64.so",
    "libc.so",
    "libpthread.so",
    "libm.so",
    "libdl.so",
    "libBrokenLocale.so",
    "libSegFault.so",
    "libanl.so",
    "libcidn.so",
    "libcrypt.so",
    "libmemusage.so",
    "libmvec.so",
    "libnsl.so",
    "libnss3.so",
    "libnssutil3.so",
    "libnss_compat.so",
    "libnss_db.so",
    "libnss_dns.so",
    "libnss_files.so",
    "libnss_hesiod.so",
    "libnss_nis.so",
    "libnss_nisplus.so",
    "libpcprofile.so",
    "libresolv.so",
    "librt.so",
    "libthread_db-1.0.so",
    "libthread_db.so",
    "libutil.so",
    # The C++ standard library can also be ABI specific, and can cause system
    # libraries like MESA to not load any drivers, so we exclude it too, and
    # it can be assumed to be installed everywhere anyway.
    "libstdc++.so",
    # The DRM layer should also be taken from the OS in question and won't
    # allow loading native drivers otherwise.
    "libdrm.so",
    # The zlib can be assumed to be everywhere, and outside dependencies
    # may actually load it.
    "libz.so",
]

if isAnacondaPython() or isAlpineLinux():
    # Anaconda has these with e.g. torchvision, and insists on them being very new,
    # so they have to be included.
    # Alpine linux does not include `libstdc++.so` by default.
    _linux_dll_ignore_list.remove("libstdc++.so")

if isAndroidBasedLinux():
    _linux_dll_ignore_list.remove("libz.so")

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
