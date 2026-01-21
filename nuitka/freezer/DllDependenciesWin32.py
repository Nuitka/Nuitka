#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""DLL dependency scan methods for Win32 Windows.

Note: MSYS2, aka POSIX Windows is dealt with in the "DllDependenciesPosix" module.
"""

import os
import sys

from nuitka.__past__ import iterItems
from nuitka.build.SconsUtils import readSconsReport
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.options.Options import (
    getMsvcVersion,
    getWindowsRuntimeDllsInclusionOption,
    isExperimental,
    isShowProgress,
)
from nuitka.plugins.Hooks import getPluginsCacheContributionValues
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.PythonVersions import getSystemPrefixPath
from nuitka.Tracing import inclusion_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Execution import executeToolChecked
from nuitka.utils.FileOperations import (
    areSamePaths,
    getDirectoryRealPath,
    getFileContentByLine,
    getNormalizedPathJoin,
    getSubDirectoriesWithDlls,
    isFilenameBelowPath,
    isFilenameSameAsOrBelowPath,
    listDir,
    listDllFilesFromDirectory,
    makePath,
    putTextFileContents,
    resolveShellPatternToFilenames,
    withFileLock,
)
from nuitka.utils.Hashing import Hash
from nuitka.utils.Json import loadJsonFromFilename
from nuitka.utils.SharedLibraries import getPEFileUsedDllNames, getPyWin32Dir
from nuitka.utils.Utils import getArchitecture, isWin32Windows
from nuitka.Version import version_string

from .DependsExe import detectDLLsWithDependencyWalker
from .DllDependenciesCommon import getPackageSpecificDLLDirectories

_msvc_redist_path = None

_arch_redist_folder_map = {
    "x86_64": "x64",
    "arm64": "arm64",
    "x86": "x86",
}


def _getVswherePath():
    # The program name is from the installer, spell-checker: ignore vswhere
    for candidate in ("ProgramFiles(x86)", "ProgramFiles"):
        program_files_dir = os.getenv(candidate)

        if program_files_dir is not None:
            candidate = os.path.join(
                program_files_dir,
                "Microsoft Visual Studio",
                "Installer",
                "vswhere.exe",
            )

            if os.path.exists(candidate):
                return candidate

    return None


def _getSconsMsvcCacheValue(key):
    msvc_config_cache_dir = getCacheDir("scons-msvc-config")

    if not os.path.isdir(msvc_config_cache_dir):
        return None

    # We might have multiple versions, we want the one that was used or the latest.
    msvc_version = getMsvcVersion()

    config_files = resolveShellPatternToFilenames(
        os.path.join(msvc_config_cache_dir, "content-*.json")
    )

    def _getMsvcVersionFromFilename(filename):
        # filename is .../content-14.3.json
        return os.path.basename(filename)[8:-5]

    config_files = [
        filename
        for filename in config_files
        if all(
            part.isdigit() for part in _getMsvcVersionFromFilename(filename).split(".")
        )
    ]

    if not config_files:
        return None

    # Filter for specific version if provided and valid, otherwise use what is found.
    if msvc_version is not None:
        preferred_config_files = [
            filename
            for filename in config_files
            if _getMsvcVersionFromFilename(filename) == msvc_version
        ]

        if preferred_config_files:
            config_files = preferred_config_files

    def _getSortKey(filename):
        return tuple(
            int(part) for part in _getMsvcVersionFromFilename(filename).split(".")
        )

    config_files.sort(key=_getSortKey, reverse=True)

    # Iterate and look for key
    for filename in config_files:
        data = loadJsonFromFilename(filename)

        if data:
            for entry in data:
                # The value is in the data dictionary of the cache entry.
                if key in entry["data"]:
                    return entry["data"][key]

    return None


def _getMSVCRedistPath(logger):
    """Determine the path to the MSVC redistributable directory.

    Args:
        logger: Tracer for logging actions.

    Returns:
        str: Path to the MSVC redistributable directory specific to the architecture and version, or None if not found.
    """
    # Try to get the path from Scons, which will have it if it used a MSVC to
    # compile previously.
    vs_path = None

    # spell-checker: ignore VCINSTALLDIR
    vc_install_dir = _getSconsMsvcCacheValue("VCINSTALLDIR")
    if vc_install_dir:
        if type(vc_install_dir) is list and vc_install_dir:
            vc_install_dir = vc_install_dir[0]

        vs_path = getNormalizedPathJoin(vc_install_dir, "..")

    # Otherwise ask for a MSVC installation path.
    if vs_path is None:
        vswhere_path = _getVswherePath()

        if vswhere_path is None:
            return None

        command = (
            vswhere_path,
            "-latest",
            "-property",
            "installationPath",
            "-products",
            "*",
            "-prerelease",
        )

        vs_path = executeToolChecked(
            logger=logger,
            command=command,
            absence_message="requiring vswhere for redist discovery",
            decoding=True,
        ).strip()

    redist_base_path = os.path.join(vs_path, "VC", "Redist", "MSVC")

    if not os.path.exists(redist_base_path):
        return None

    version_folders = []

    for fullpath, filename in listDir(redist_base_path):
        if not os.path.isdir(fullpath):
            continue

        try:
            version_tuple = tuple(int(x) for x in filename.split("."))
        except ValueError:
            continue

        version_folders.append((version_tuple, filename))

    if not version_folders:
        return None

    _latest_version_tuple, latest_version = max(version_folders)

    arch_folder = _arch_redist_folder_map.get(getArchitecture())

    final_path = getNormalizedPathJoin(redist_base_path, latest_version, arch_folder)

    if os.path.exists(final_path):
        return final_path

    return None


def getMSVCRedistPath(logger):
    """Get the MSVC redistributable path with caching.

    Args:
        logger: Tracer for logging actions.

    Returns:
        str | None: Path to the MSVC redistributable directory or None.
    """
    global _msvc_redist_path  # singleton, pylint: disable=global-statement

    if _msvc_redist_path is False:
        # Cached error path, didn't find it.
        return None
    elif _msvc_redist_path is None:
        if isWin32Windows():
            _msvc_redist_path = _getMSVCRedistPath(logger=logger)

            # Don't retry if it fails.
            if _msvc_redist_path is None:
                _msvc_redist_path = False
                return None

    return _msvc_redist_path


_scan_dir_cache = {}


def detectDLLsWithPEFile(binary_filename, scan_dirs):
    """Detect DLLs used by a binary using pefile.

    Args:
        binary_filename: The binary to check.
        scan_dirs: Directories to search for DLLs.

    Returns:
        OrderedSet: Set of found DLL filenames.
    """
    pe_dll_names = getPEFileUsedDllNames(binary_filename)

    result = OrderedSet()

    # Get DLL imports from PE file
    for dll_name in pe_dll_names:
        dll_name = dll_name.lower()

        # Search DLL path from scan dirs
        for scan_dir in scan_dirs:
            dll_filename = os.path.normcase(
                os.path.abspath(getNormalizedPathJoin(scan_dir, dll_name))
            )

            if os.path.isfile(dll_filename):
                result.add(dll_filename)

                break
        else:
            if dll_name.startswith("API-MS-WIN-") or dll_name.startswith("EXT-MS-WIN-"):
                continue

            # Ignore this runtime DLL of Python2, will be coming via manifest.
            # spell-checker: ignore msvcr90
            if dll_name == "msvcr90.dll":
                continue

            # Ignore API DLLs, they can come in from PATH, but we do not want to
            # include them.
            if dll_name.startswith("api-ms-win-"):
                continue

            # Ignore UCRT runtime, this must come from OS, spell-checker: ignore ucrtbase
            if dll_name == "ucrtbase.dll":
                continue

    return result


def detectBinaryPathDLLsWin32(
    is_main_executable,
    source_dir,
    original_dir,
    binary_filename,
    package_name,
    use_path,
    use_cache,
    update_cache,
):
    """Detect DLLs used by a binary on Windows.

    Args:
        is_main_executable: Whether this is the main executable (e.g. for caching).
        source_dir: The source directory (for caching context).
        original_dir: The directory of the binary.
        binary_filename: The binary filename.
        package_name: The package name if applicable.
        use_path: Whether to use PATH.
        use_cache: Whether to use caching.
        update_cache: Whether to update the cache.

    Returns:
        OrderedSet: Set of found DLL filenames.
    """
    # Caching and tracing cause too many branches, pylint: disable=too-many-branches

    # For ARM64 and on user request, we can use "pefile" for dependency detection.
    dependency_tool = (
        "pefile"
        if (getArchitecture() == "arm64" or isExperimental("force-dependencies-pefile"))
        else "depends.exe"
    )

    # This is the caching mechanism and plugin handling for DLL imports.
    if use_cache or update_cache:

        cache_filename = _getCacheFilename(
            dependency_tool=dependency_tool,
            is_main_executable=is_main_executable,
            source_dir=source_dir,
            original_dir=original_dir,
            binary_filename=binary_filename,
            package_name=package_name,
            use_path=use_path,
        )

        if use_cache:
            with withFileLock():
                if not os.path.exists(cache_filename):
                    use_cache = False

                    if isShowProgress():
                        inclusion_logger.info(
                            "Cache for dependencies of '%s' file '%s' does not exist."
                            % (binary_filename, cache_filename)
                        )

        if use_cache:
            result = OrderedSet()

            for line in getFileContentByLine(cache_filename):
                filename = line.strip()

                # Detect files that have become missing by ignoring the cache.
                if not os.path.exists(filename):
                    if isShowProgress():
                        inclusion_logger.info(
                            "Cache for dependencies of '%s' contains non-existent file '%s', ignoring."
                            % (binary_filename, filename)
                        )

                    break

                result.add(line)
            else:
                return result

    if isShowProgress():
        inclusion_logger.info("Analyzing dependencies of '%s'." % binary_filename)

    scan_dirs = _getScanDirectories(
        package_name=package_name,
        original_dir=original_dir,
        use_path=use_path,
    )

    if dependency_tool == "depends.exe":
        result = detectDLLsWithDependencyWalker(
            binary_filename=binary_filename,
            source_dir=source_dir,
            scan_dirs=scan_dirs,
        )
    else:
        result = detectDLLsWithPEFile(
            binary_filename=binary_filename,
            scan_dirs=scan_dirs,
        )

    if update_cache:
        if isShowProgress():
            inclusion_logger.info(
                "Writing cache for dependencies of '%s' to '%s', ignoring."
                % (binary_filename, cache_filename)
            )

        putTextFileContents(filename=cache_filename, contents=result)

    return result


_path_contributions = {}


def _getPathContribution(use_path):
    """Contributions from PATH environment variable.

    These are ignored if use_path is False, but for
    Anaconda we need to keep those elements pointing
    to inside of it.
    """
    if use_path not in _path_contributions:
        _path_contributions[use_path] = OrderedSet()

        for path_dir in os.environ["PATH"].split(";"):
            if not os.path.isdir(path_dir):
                continue

            # spell-checker: ignore SYSTEMROOT
            if areSamePaths(path_dir, getNormalizedPathJoin(os.environ["SYSTEMROOT"])):
                continue
            if areSamePaths(
                path_dir, getNormalizedPathJoin(os.environ["SYSTEMROOT"], "System32")
            ):
                continue
            if areSamePaths(
                path_dir, getNormalizedPathJoin(os.environ["SYSTEMROOT"], "SysWOW64")
            ):
                continue

            # For Anaconda, we cannot ignore PATH on its inside.
            if not use_path:
                if not isAnacondaPython() or not isFilenameSameAsOrBelowPath(
                    filename=path_dir,
                    path=(
                        getSystemPrefixPath(),
                        sys.prefix,
                    ),
                ):
                    continue

            _path_contributions[use_path].add(path_dir)

    return _path_contributions[use_path]


def shallIncludeVCRedistDLL(dll_filename):
    """Check if a DLL from the VC redistributable should be included.

    Args:
        dll_filename (str): The filename of the DLL to check.

    Returns:
        bool: True if it is a VC redist DLL and inclusion is enabled, False otherwise.
    """

    vc_redist_path = getMSVCRedistPath(logger=inclusion_logger)
    if vc_redist_path is None:
        return False

    if isFilenameBelowPath(path=vc_redist_path, filename=dll_filename):
        return shallIncludeWindowsRuntimeDLLs()

    return True


_include_windows_runtime_dlls = None


def shallIncludeWindowsRuntimeDLLs():
    """Check if Windows Runtime DLLs should be included based on configuration.

    Returns:
        bool: True if they should be included, False otherwise.

    Notes:
        This makes the decision based on the command line option ``--include-windows-runtime-dlls``
        and the presence of the files.
    """
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _include_windows_runtime_dlls

    if _include_windows_runtime_dlls is not None:
        return _include_windows_runtime_dlls

    option_value = getWindowsRuntimeDllsInclusionOption()

    if option_value == "no":
        result = False
    elif option_value == "yes":
        msvc_redist_path = getMSVCRedistPath(logger=inclusion_logger)

        if msvc_redist_path is None:
            inclusion_logger.sysexit(
                """\
Error, cannot find Windows Runtime DLLs to include, but '--include-windows-runtime-dlls=yes' \
make sure to install Visual Studio as that is the only provider of those DLLs with license \
terms that allow redistribution."""
            )
        result = True
    else:
        msvc_redist_path = getMSVCRedistPath(logger=inclusion_logger)

        if msvc_redist_path is None:
            inclusion_logger.warning(
                """\
Cannot find Windows Runtime DLLs to include, requiring them \
to be installed on target systems."""
            )
            result = False
        else:
            inclusion_logger.info(
                """\
Including Windows Runtime DLLs, which increases distribution  \
size. Use '--include-windows-runtime-dlls=no' to disable, or \
make explicit with '--include-windows-runtime-dlls=yes'."""
            )
            result = True

    _include_windows_runtime_dlls = result
    return result


def _getScanDirectories(package_name, original_dir, use_path):
    """Get directories to scan for DLLs.

    Args:
        package_name: The package name if applicable.
        original_dir: The directory of the binary.
        use_path: Whether to included PATH directories.

    Returns:
        list: List of directory paths to scan.
    """
    # TODO: Move PyWin32 specific stuff to yaml dll section

    cache_key = package_name, original_dir

    if cache_key in _scan_dir_cache:
        return _scan_dir_cache[cache_key]

    scan_dirs = [os.path.dirname(sys.executable), getSystemPrefixPath()]

    # Add the VCRedist path to the list of directories to search if it exists
    msvc_redist_path = getMSVCRedistPath(logger=inclusion_logger)
    if msvc_redist_path is not None:
        scan_dirs.extend(getSubDirectoriesWithDlls(msvc_redist_path))

    if package_name is not None:
        scan_dirs.extend(
            getPackageSpecificDLLDirectories(
                package_name=package_name,
                consider_plugins=False,
            )
        )

    if original_dir is not None:
        scan_dirs.append(original_dir)
        scan_dirs.extend(getSubDirectoriesWithDlls(original_dir))

    if package_name is not None and package_name.isBelowNamespace("win32com"):
        py_win32_dir = getPyWin32Dir()

        if py_win32_dir is not None:
            scan_dirs.append(py_win32_dir)

    scan_dirs.extend(_getPathContribution(use_path=use_path))

    result = []

    # Remove directories that hold no DLLs.
    for scan_dir in scan_dirs:
        scan_dir = getDirectoryRealPath(scan_dir)

        # Not a directory, or no DLLs, or not accessible, no use.
        try:
            if not os.path.isdir(scan_dir) or not any(
                listDllFilesFromDirectory(scan_dir)
            ):
                continue
        except OSError:
            continue

        result.append(os.path.realpath(scan_dir))

    _scan_dir_cache[cache_key] = result
    return result


def _getCacheFilename(
    dependency_tool,
    is_main_executable,
    source_dir,
    original_dir,
    binary_filename,
    package_name,
    use_path,
):
    original_filename = getNormalizedPathJoin(
        original_dir, os.path.basename(binary_filename)
    )

    hash_value = Hash()

    if is_main_executable:
        # Normalize main program name for caching as well, but need to use the
        # scons information to distinguish different compilers, so we use
        # different libs there.
        hash_value.updateFromValues(
            "".join(
                key + value
                for key, value in iterItems(readSconsReport(source_dir=source_dir))
                # Ignore values, that are variable per compilation.
                if key not in ("CLCACHE_STATS", "CCACHE_LOGFILE", "CCACHE_DIR")
            )
        )
    else:
        hash_value.updateFromValues(original_filename)
        hash_value.updateFromFile(filename=original_filename)

    # Have different values for different Python major versions.
    hash_value.updateFromValues(sys.version, sys.executable)

    # Plugins may change their influence.
    hash_value.updateFromValues(*getPluginsCacheContributionValues(package_name))

    # Take Nuitka version into account as well, ought to catch code changes.
    hash_value.updateFromValues(version_string)

    # Using PATH or not, should also be considered different.
    if use_path:
        hash_value.updateFromValues(os.getenv("PATH"))

    cache_dir = getNormalizedPathJoin(
        getCacheDir("library_dependencies"), dependency_tool
    )
    makePath(cache_dir)

    return getNormalizedPathJoin(cache_dir, hash_value.asHexDigest())


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
