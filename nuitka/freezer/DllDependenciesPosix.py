#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""DLL dependency scan methods for POSIX (Linux, *BSD, MSYS2)."""

import os
import sys

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Execution import (
    check_output,
    executeProcess,
    getEnvironmentWithPathAdded,
)
from nuitka.utils.FileOperations import isFilenameBelowPath
from nuitka.utils.SharedLibraries import getSharedLibraryRPATHs
from nuitka.utils.Utils import (
    isAlpineLinux,
    isAndroidBasedLinux,
    isPosixWindows,
)

from .DllDependenciesCommon import getLdLibraryPath

# Detected Python rpath is cached.
_detected_python_rpaths = None

# Cached POSIX path for Windows SYSTEMROOT on Cygwin/MSYS2.
_posix_windows_system_root = None

# Cached ldd results.
ldd_result_cache = {}


def _getPosixWindowsSystemRoot():
    # singleton, pylint: disable=global-statement
    global _posix_windows_system_root

    if _posix_windows_system_root is None:
        windows_system_root = os.getenv("SYSTEMROOT") or os.getenv("WINDIR")
        assert windows_system_root, "Expected SYSTEMROOT or WINDIR on POSIX Windows."

        output = check_output(("cygpath", "-u", windows_system_root))
        if str is not bytes:
            output = output.decode("utf8", "replace")

        _posix_windows_system_root = os.path.normpath(output.strip()).lower()

    return _posix_windows_system_root


def _isWindowsSystemDll(filename):
    # Windows paths under Cygwin/MSYS2 are case-insensitive ('/c/Windows' vs
    # '/c/WINDOWS'), whereas POSIX 'isFilenameBelowPath' is case-sensitive.
    return isFilenameBelowPath(
        path=_getPosixWindowsSystemRoot(),
        filename=filename.lower(),
    )


def _resolveOriginValue(rpath, origin):
    rpath = rpath.replace("$ORIGIN", origin)
    rpath = os.path.normpath(os.path.join(origin, rpath))

    return rpath


def _runLddCommand(dll_filename, package_name, python_rpaths, original_dir):
    """Run 'ldd' with the package specific library path and check for failures.

    Args:
        dll_filename: The DLL to inspect.
        package_name: Name of the package the DLL belongs to.
        python_rpaths: RPATHs of the Python executable.
        original_dir: Directory of the original DLL file.

    Returns:
        Tuple of the process result and the filtered stderr output.
    """
    ld_library_paths = getLdLibraryPath(
        package_name=package_name,
        python_rpaths=python_rpaths,
        original_dir=original_dir,
    )

    if isPosixWindows():
        # Cygwin/MSYS2 'ldd' delegates DLL resolution to the Windows loader,
        # which searches 'PATH' rather than 'LD_LIBRARY_PATH'.
        env = getEnvironmentWithPathAdded("PATH", *ld_library_paths, prefix=True)
    else:
        env = getEnvironmentWithPathAdded("LD_LIBRARY_PATH", *ld_library_paths)

    process_result = executeProcess(
        command=("ldd", dll_filename),
        env=env,
    )

    # This warning is harmless, the DLL is still analyzed.
    stderr = b"\n".join(
        line
        for line in process_result.stderr.splitlines()
        if not line.startswith(
            b"ldd: warning: you do not have execution permission for"
        )
    )

    if process_result.exit_code != 0:
        error_output = stderr or process_result.stdout

        if str is not bytes:
            error_output = error_output.decode("utf8", "replace")

        return inclusion_logger.sysexit(
            "Error, 'ldd' failed with exit code %d for '%s':\n%s"
            % (process_result.exit_code, dll_filename, error_output)
        )

    return process_result, stderr


def _getLddDirectDependencies(dll_filename, package_name, original_dir):
    """Get the direct dependencies of a DLL, using cached 'ldd' results.

    Args:
        dll_filename: The DLL to inspect.
        package_name: Name of the package the DLL belongs to.
        original_dir: Directory of the original DLL file.

    Returns:
        OrderedSet of absolute dependency filenames, not including transitive
        dependencies.
    """
    # Many details to check, pylint: disable=too-many-branches

    # The 'ldd' result depends on the 'LD_LIBRARY_PATH' built from the package
    # name and original directory, so both are part of the cache key.
    cache_key = (dll_filename, package_name, original_dir)

    if cache_key in ldd_result_cache:
        return ldd_result_cache[cache_key]

    # Ask "ldd" about the libraries being used by the created binary, these
    # are the ones that interest us.

    # This is the rpath of the Python binary, which will be effective when
    # loading the other DLLs too. This happens at least for Python installs
    # on Travis. pylint: disable=global-statement
    global _detected_python_rpaths
    if _detected_python_rpaths is None:
        if isPosixWindows():
            _detected_python_rpaths = []
        else:
            _detected_python_rpaths = getSharedLibraryRPATHs(
                sys.executable,
                elements=True,
            )

            sys_executable_dir = os.path.dirname(os.path.realpath(sys.executable))

            _detected_python_rpaths = [
                _resolveOriginValue(
                    rpath=detected_python_rpath, origin=sys_executable_dir
                )
                for detected_python_rpath in _detected_python_rpaths
            ]

    python_rpaths = _detected_python_rpaths[:]

    if os.path.islink(dll_filename):
        link_target_path = os.path.dirname(os.path.realpath(dll_filename))
        python_rpaths.append(link_target_path)

    process_result, stderr = _runLddCommand(
        dll_filename=dll_filename,
        package_name=package_name,
        python_rpaths=python_rpaths,
        original_dir=original_dir,
    )

    inclusion_logger.debug(
        "ldd output for %s is:\n%s"
        % (
            dll_filename,
            process_result.stdout,
        )
    )

    if stderr:
        inclusion_logger.debug("ldd error for %s is:\n%s" % (dll_filename, stderr))

    result_set = OrderedSet()

    for line in process_result.stdout.split(b"\n"):
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

        # Do not include Windows OS DLLs resolved by Cygwin/MSYS2 'ldd'.
        if isPosixWindows() and _isWindowsSystemDll(filename):
            continue

        # Do not include kernel DLLs on the ignore list.
        filename_base = os.path.basename(filename)
        if any(
            filename_base == entry or filename_base.startswith(entry + ".")
            for entry in _linux_dll_ignore_list
        ):
            continue

        # Do not allow relative paths for shared libraries
        if not os.path.isabs(filename):
            return inclusion_logger.sysexit(
                "Error: Found a dependency with a relative path. Was a dependency copied to dist early? "
                + filename
            )

        result_set.add(filename)

    ldd_result_cache[cache_key] = result_set

    return result_set


def _detectBinaryPathDLLsPosixRecursive(
    dll_filename, package_name, original_dir, recursive_dlls
):
    if dll_filename in recursive_dlls:
        return OrderedSet()

    recursive_dlls.add(dll_filename)

    result_set = _getLddDirectDependencies(
        dll_filename=dll_filename,
        package_name=package_name,
        original_dir=original_dir,
    )

    complete_result = OrderedSet(result_set)

    for sub_dll_filename in result_set:
        complete_result.update(
            _detectBinaryPathDLLsPosixRecursive(
                dll_filename=sub_dll_filename,
                package_name=package_name,
                original_dir=original_dir,
                recursive_dlls=recursive_dlls,
            )
        )

    return complete_result


def detectBinaryPathDLLsPosix(dll_filename, package_name, original_dir):
    """Detect all DLLs used by a DLL, including transitive dependencies.

    Args:
        dll_filename: The DLL to inspect.
        package_name: Name of the package the DLL belongs to.
        original_dir: Directory of the original DLL file.

    Returns:
        OrderedSet of absolute dependency filenames.
    """
    return _detectBinaryPathDLLsPosixRecursive(
        dll_filename=dll_filename,
        package_name=package_name,
        original_dir=original_dir,
        recursive_dlls=OrderedSet(),
    )


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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
