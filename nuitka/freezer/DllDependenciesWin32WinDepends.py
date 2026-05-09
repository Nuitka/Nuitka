#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Interface to WinDepends on Windows."""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.options.Options import assumeYesForDownloads
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import (
    executeProcess,
    getExecutablePath,
    withEnvironmentPathAdded,
)
from nuitka.utils.FileOperations import (
    areSamePaths,
    deleteFile,
    getExternalUsePath,
    getNormalizedPath,
    getNormalizedPathJoin,
    isFilesystemEncodable,
    withFileLock,
)
from nuitka.utils.Json import loadJsonFromFilename
from nuitka.utils.Utils import getArchitecture

from .DllDependenciesCommon import (
    addMissingMsvcRedistDLL,
    attemptToFindNotFoundDLL,
    isMsvcRedistDllName,
    reportMissingMsvcRedistDLLs,
    shallIgnoreMissingDLL,
)

_win_depends_release = "2512-beta"
_win_depends_dotnet_runtime_name = "Microsoft.WindowsDesktop.App"
_win_depends_dotnet_runtime_major = "10"

_installed_dotnet_core_app_versions = None


def _isWinDependsSupportedArchitecture():
    if getArchitecture() == "x86_64":
        return True

    # This is what Windows actually used, spell-checker: ignore PROCESSOR_ARCHITEW6432
    return (
        os.getenv("PROCESSOR_ARCHITECTURE") == "AMD64"
        or os.getenv("PROCESSOR_ARCHITEW6432") == "AMD64"
    )


def _getInstalledDotNetCoreAppRuntimeVersions():
    global _installed_dotnet_core_app_versions  # singleton, pylint: disable=global-statement

    if _installed_dotnet_core_app_versions is not None:
        return _installed_dotnet_core_app_versions

    result = OrderedSet()

    dotnet_exe = getExecutablePath("dotnet")

    if dotnet_exe is not None:
        process_result = executeProcess(command=(dotnet_exe, "--list-runtimes"))

        if process_result.exit_code == 0:
            for line in _decodeWinDependsProcessOutput(process_result).splitlines():
                line = line.strip()

                if not line.startswith(_win_depends_dotnet_runtime_name + " "):
                    continue

                version = line[len(_win_depends_dotnet_runtime_name) + 1 :].split(
                    " ", 1
                )[0]

                if version:
                    result.add(version)

    program_files = os.getenv("ProgramFiles")

    if program_files is not None:
        dotnet_runtime_dir = getNormalizedPathJoin(
            program_files, "dotnet", "shared", _win_depends_dotnet_runtime_name
        )

        if os.path.isdir(dotnet_runtime_dir):
            for filename in os.listdir(dotnet_runtime_dir):
                fullpath = getNormalizedPathJoin(dotnet_runtime_dir, filename)

                if os.path.isdir(fullpath):
                    result.add(filename)

    _installed_dotnet_core_app_versions = tuple(result)

    return _installed_dotnet_core_app_versions


def _checkWinDependsDotNetRuntime():
    installed_versions = _getInstalledDotNetCoreAppRuntimeVersions()
    expected_prefix = _win_depends_dotnet_runtime_major + "."

    for installed_version in installed_versions:
        if installed_version.startswith(expected_prefix):
            return

    # spell-checker: ignore windepends,winget
    return inclusion_logger.sysexit(
        """\
Error, WinDepends release '%(release)s' requires %(runtime_name)s %(runtime_major)s.x \
on the build machine. Install the .NET %(runtime_major)s runtime, e.g. with \
'winget install -e --id Microsoft.DotNet.DesktopRuntime.%(runtime_major)s'."""
        % {
            "release": _win_depends_release,
            "runtime_name": _win_depends_dotnet_runtime_name,
            "runtime_major": _win_depends_dotnet_runtime_major,
        }
    )


def getWinDependsExePath():
    """Return the path of WinDepends.exe (for Windows).

    Will prompt the user to download if not already cached in AppData
    directory for Nuitka.
    """

    if not _isWinDependsSupportedArchitecture():
        return inclusion_logger.sysexit(
            "Error, WinDepends backend is currently only supported on x64 Windows."
        )

    _checkWinDependsDotNetRuntime()

    return getCachedDownload(
        name="WinDepends",
        url=(
            "https://github.com/hfiref0x/WinDepends/releases/download/"
            "%s/WinDepends_v1.0.0.2512_beta_snapshot.zip" % _win_depends_release
        ),
        is_arch_specific="x64",
        binary="WinDepends.exe",
        unzip=True,
        flatten=True,
        specificity=_win_depends_release,
        message="""\
Nuitka will make use of WinDepends (https://github.com/hfiref0x/WinDepends) tool
to analyze the dependencies of Python extension modules when using the
'--experimental=force-dependencies-windepends' backend.""",
        reject="Nuitka cannot use '--experimental=force-dependencies-windepends' without WinDepends.",
        assume_yes_for_downloads=assumeYesForDownloads(),
        download_ok=True,
    )


def _decodeWinDependsProcessOutput(process_result):
    stdout = process_result.stdout
    stderr = process_result.stderr

    if type(stdout) is bytes:
        stdout = stdout.decode("utf8", "replace")

    if type(stderr) is bytes:
        stderr = stderr.decode("utf8", "replace")

    output = "\n".join(
        part.strip() for part in (stdout, stderr) if part and part.strip()
    )

    return output


def _parseWinDependsOutputData(output_filename, binary_filename):
    data = loadJsonFromFilename(output_filename)

    if type(data) is not dict:
        return inclusion_logger.sysexit(
            "Error, WinDepends failed to produce valid JSON output for binary '%s'."
            % binary_filename
        )

    modules = data.get("Modules")

    if type(modules) is not list:
        return inclusion_logger.sysexit(
            "Error, WinDepends failed to produce expected JSON output for binary '%s'."
            % binary_filename
        )

    return modules


def _handleMissingWinDependsModule(dll_filename):
    dll_name = os.path.basename(dll_filename).lower()

    if isMsvcRedistDllName(dll_name):
        addMissingMsvcRedistDLL(dll_name)

    if dll_name.startswith("python") and dll_name.endswith(".dll"):
        return attemptToFindNotFoundDLL(dll_name)

    return None


def _handleWinDependsModuleData(module_data, binary_filename, result):
    dll_filename = module_data.get("FileName")

    if not dll_filename:
        return

    if module_data.get("FileNotFound", False):
        dll_filename = _handleMissingWinDependsModule(dll_filename)

        if dll_filename is None:
            return

    dll_filename = os.path.normcase(os.path.abspath(dll_filename))
    dll_name = os.path.basename(dll_filename).lower()

    if areSamePaths(dll_filename, binary_filename):
        return

    if shallIgnoreMissingDLL(dll_name):
        return

    assert os.path.isfile(dll_filename), dll_filename

    result.add(getNormalizedPath(dll_filename))


def _parseWinDependsOutput(output_filename, binary_filename):
    modules = _parseWinDependsOutputData(
        output_filename=output_filename, binary_filename=binary_filename
    )

    result = OrderedSet()

    for module_data in modules:
        if type(module_data) is dict:
            _handleWinDependsModuleData(
                module_data=module_data,
                binary_filename=binary_filename,
                result=result,
            )

    return result


def detectDLLsWithWinDepends(binary_filename, source_dir, scan_dirs):
    source_dir = getExternalUsePath(source_dir)
    temp_base_name = os.path.basename(binary_filename)

    if not isFilesystemEncodable(temp_base_name):
        temp_base_name = "win_depends"

    output_filename = getNormalizedPathJoin(
        source_dir, temp_base_name + ".windepends.json"
    )

    deleteFile(output_filename, must_exist=False)

    with withFileLock("Finding out WinDepends path for %s" % binary_filename):
        windepends_exe = getWinDependsExePath()

    scan_path = list(getExternalUsePath(dirname) for dirname in scan_dirs)

    with withEnvironmentPathAdded("PATH", *scan_path, prefix=True):
        process_result = executeProcess(
            command=(
                windepends_exe,
                getExternalUsePath(binary_filename),
                "-o",
                output_filename,
                "-f",
                "json",
                "-q",
                "--no-exports",
                "--no-imports",
            ),
            external_cwd=True,
        )

    if not os.path.exists(output_filename):
        output = _decodeWinDependsProcessOutput(process_result)

        if "You must install or update .NET to run this application." in output:
            return inclusion_logger.sysexit("""\
Error, WinDepends requires the .NET 10 runtime on the build machine, \
but the downloaded WinDepends release could not be started.

%s""" % output)

        if output:
            output = "\n\n" + output

        return inclusion_logger.sysexit(
            "Error, 'WinDepends.exe' failed to produce expected output for binary '%s'.%s"
            % (binary_filename, output)
        )

    result = _parseWinDependsOutput(
        output_filename=output_filename, binary_filename=binary_filename
    )

    deleteFile(output_filename, must_exist=True)

    reportMissingMsvcRedistDLLs()

    return result


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
