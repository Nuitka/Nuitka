#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Generate Nuitka CPython offset JSON specialized mappings."""

import os
import re
import sys

from nuitka.build.AdaptPythonHeaderFiles import isOffsetsJsonOutdated
from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.Basics import goHome
from nuitka.Tracing import tools_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Download import withUrlOpen
from nuitka.utils.Execution import callProcess, executeProcess
from nuitka.utils.FileOperations import removeDirectory
from nuitka.utils.Utils import getArchitecture, getOS, isMacOS, isWin32Windows


def getInstalledOffsetsJsonPath(python_version, has_gil):
    """
    Return the source distribution bundled JSON storage path resolving strictly against this module.
    The resulting JSON files are permanently checked into version control to cache C struct offsets.
    """
    gil_str = "gil" if has_gil else "no-gil"
    filename = "offsets_%s-%s-%s-%s.json" % (
        python_version,
        getOS(),
        getArchitecture(),
        gil_str,
    )
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "build",
        "python_internal_offset",
        filename,
    )


def convertPythonMinorVersionToTuple(v):
    """Convert version strings like '3.13.1' into tuples (3, 13, 1) for precise sorting."""
    assert v.count(".") == 2, v
    return tuple(int(x) for x in v.split("."))


def _getPythonOrgMinorVersions(target_version):
    """
    Scrape the python.org FTP to discover all historically available micro-versions.
    This acts as a completeness backstop because sometimes package managers
    (like uv) do not immediately mirror or cache every single active micro-release.
    """
    tools_logger.info(
        "Querying python.org FTP to ensure latest stable micro-versions...",
        style="tool-progress",
    )

    pattern = re.compile(r'<a href="(%s.\d+)/">' % re.escape(target_version))

    try:
        with withUrlOpen("https://www.python.org/ftp/python/") as response:
            content = response.read().decode("utf8")
    except Exception as e:  # pylint: disable=broad-exception-caught
        return tools_logger.sysexit("Failed to fetch versions from python.org: %s" % e)

    found_versions = set(pattern.findall(content))

    if not found_versions:
        return tools_logger.sysexit(
            "No Python versions found for %s on Python.org." % target_version,
        )

    return found_versions


def _getUvPythonMinorVersions(target_version):
    """
    Exploit 'uv' to list all micro-releases it can natively pull for the target minor.
    Because uv provides an extremely fast, centralized pool of precompiled pythons,
    we prefer mapping as many of these as we can.
    """
    tools_logger.info(
        "Querying uv-Python to get available versions...",
        style="tool-progress",
    )

    found_versions = set()
    result = executeProcess(
        [
            sys.executable,
            "-m",
            "uv",
            "python",
            "list",
            "--only-downloads",
            "--all-versions",
        ]
    )

    if result.exit_code != 0:
        return tools_logger.sysexit("Could not list python versions via uv.")

    output = result.stdout
    if str is not bytes and type(output) is bytes:
        output = output.decode("utf8")

    pattern = re.compile(
        r"cpython-(%s(?:\.\d+)*)-(?:windows|linux|macos)" % re.escape(target_version)
    )
    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            found_versions.add(match.group(1))

    return found_versions


def _getUvPythonBinaryForMinorPythonVersion(python_version_full):
    """
    Install a specific micro-version using 'uv' and return the absolute path to the binary.
    Avoiding manual source compilation speeds up offset generation pipelines by hours,
    which is critical for matrix CI testing.
    """
    tools_logger.info("=> Attempting installation via uv...", style="tool-progress")
    exit_code = callProcess(
        [sys.executable, "-m", "uv", "python", "install", python_version_full]
    )

    if exit_code != 0:
        tools_logger.warning("=> Failed to push installation through uv!")
        return None

    result = executeProcess(
        [sys.executable, "-m", "uv", "python", "find", python_version_full]
    )

    if result.exit_code == 0:
        output = result.stdout
        if str is not bytes and type(output) is bytes:
            output = output.decode("utf8")
        return output.strip()

    return None


def _getPlatformPythonBuildScriptAndExeName():
    """
    Fallback compilation lookup. If precompiled binaries are unavailable (unsupported OS/Arch),
    we must compile CPython entirely from source. This returns the native bootstrap script.
    """
    if isWin32Windows():
        return "compile-python-for-nuitka-windows.cmd", "python.exe"
    elif isMacOS():
        return "compile-python-for-nuitka-mac.sh", os.path.join("bin", "python3")
    else:
        return "compile-python-for-nuitka-linux.sh", os.path.join("bin", "python3")


def _detectAvailablePythonMinorVersions(target_version):
    """
    Unify and sort the combined availability of 'uv' packages and python.org archives,
    ensuring Nuitka extracts offsets for the absolute maximum surface area of releases.
    """
    found_versions = _getUvPythonMinorVersions(
        target_version
    ) | _getPythonOrgMinorVersions(target_version)

    sorted_versions = tuple(
        sorted(found_versions, key=convertPythonMinorVersionToTuple)
    )
    tools_logger.info(
        "Found Python versions: %s" % ", ".join(sorted_versions), style="tool-info"
    )

    return sorted_versions


def _processPythonVersion(python_version_full, options):
    """
    Core orchestration driver for a single micro-version.

    1. Validates if the existing JSON statically checks out to be up-to-date.
    2. Uses 'uv' to provision a pre-built python executable.
    3. Falls back to a heavy CPython source compilation if uv fails.
    4. Recursively invokes Nuitka inside that isolated Python environment
       (--devel-generate-python-internal-offsets) so it can natively build
       and run the specialized C inspection binary locally.
    """
    tools_logger.info(
        "Processing Python %s" % python_version_full, style="tool-progress"
    )

    parts = convertPythonMinorVersionToTuple(python_version_full)
    major = parts[0]
    minor = parts[1]

    json_path = getInstalledOffsetsJsonPath(python_version_full, has_gil=True)

    if isOffsetsJsonOutdated(json_path, "%s.%s" % (major, minor)):
        if options.check:
            tools_logger.warning(
                "=> ERROR: --check mode enabled and mapping for %s is missing!"
                % python_version_full
            )
            return False

        tools_logger.info(
            "=> JSON offset data is missing or outdated.", style="tool-info"
        )
    else:
        tools_logger.info(
            "=> JSON offsets for %s are already up-to-date and complete. Skipping."
            % python_version_full,
            style="tool-success",
        )
        return True

    exe_path_out = _getUvPythonBinaryForMinorPythonVersion(python_version_full)

    if not exe_path_out:
        cache_key = "%s_%s_%s" % (
            getArchitecture(),
            getOS(),
            python_version_full,
        )
        if major > 3 or (major == 3 and minor >= 13):
            cache_key += "_gil"

        python_cache_dir = os.path.join(
            getCacheDir("cpython_source_builds", create=True), cache_key
        )
        script_name, exe_name = _getPlatformPythonBuildScriptAndExeName()

        exe_path_out = os.path.join(python_cache_dir, exe_name)

        if not os.path.exists(exe_path_out):
            tools_logger.info(
                "=> Falling back to native compilation via Python.org source archive!",
                style="tool-fallback",
            )
            compile_cmd = os.path.join("bin", script_name)
            tools_logger.info(
                "=> Launching build sequence. Warning: This takes significant time.",
                style="tool-heavy",
            )

            exit_code = callProcess(
                [
                    compile_cmd,
                    "--version",
                    python_version_full,
                    "--prefix",
                    python_cache_dir,
                    "--cleanup",
                ]
            )

            if exit_code != 0:
                tools_logger.warning(
                    "=> ERROR: Source compilation fallback failed for %s!"
                    % python_version_full
                )
                return False

            assert os.path.exists(exe_path_out), exe_path_out

    if exe_path_out and os.path.exists(exe_path_out):
        tools_logger.info(
            "=> Launching Nuitka offset generation using runtime: %s" % exe_path_out,
            style="tool-progress",
        )
        exit_code = callProcess(
            [
                exe_path_out,
                "-m",
                "nuitka",
                "--devel-generate-python-internal-offsets",
            ]
        )
        if exit_code != 0:
            tools_logger.warning(
                "=> ERROR: Offset generation aborted natively for %s!"
                % python_version_full
            )
            return False

        tools_logger.info(
            "=> Successfully updated offsets for %s" % python_version_full,
            style="tool-success",
        )
    else:
        tools_logger.warning("=> FATAL: Could not locate Python executable!")
        return False

    return True


def _parseOptions():
    parser = makeOptionsParser(
        usage="Usage: %prog [options] [python_version]",
        epilog="Generate or update CPython internal structure information as offset JSON file.",
    )

    parser.add_option(
        "--check",
        action="store_true",
        dest="check",
        default=False,
        help="Only verify that JSONs strictly exist, failing if any releases are missing.",
    )

    parser.add_option(
        "--clean-cache",
        action="store_true",
        dest="clean_cache",
        default=False,
        help="Remove cached python source builds before compilation.",
    )

    options, args = parser.parse_args()

    if args:
        target_version = args[0]
    else:
        target_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])

    if not re.match(r"^3\.\d+$", target_version):
        return tools_logger.sysexit(
            "Error, target version must be of the form '3.x', e.g. '3.13'."
        )

    return options, target_version


def main():
    goHome()

    options, target_version = _parseOptions()

    if options.clean_cache:
        tools_logger.info("Cleaning entire Python source builds cache...")

        removeDirectory(
            path=getCacheDir("cpython_source_builds"),
            logger=tools_logger,
            ignore_errors=True,
            extra_recommendation=None,
        )

    missing_versions = []

    for python_version_full in _detectAvailablePythonMinorVersions(target_version):
        if not _processPythonVersion(python_version_full, options):
            missing_versions.append(python_version_full)

    if missing_versions:
        return tools_logger.sysexit(
            "FATAL: Processing failed or mapped versions missing for: %s"
            % ", ".join(missing_versions)
        )

    if options.check:
        tools_logger.info(
            "All expected micro-versions are natively matched in the workspace keys.",
            style="tool-success",
        )
    else:
        tools_logger.info("Extraction pass natively completed!", style="tool-success")


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
