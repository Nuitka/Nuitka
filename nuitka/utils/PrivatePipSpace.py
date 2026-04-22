#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for private pip space to download packages into."""

import os
import re
import subprocess
import sys

from nuitka.__past__ import total_ordering
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.PythonVersions import (
    getSitePackageCandidateNames,
    getSystemPrefixPath,
    python_version_str,
)

from .Download import getDownloadCacheDir, shouldDownload
from .Execution import (
    NuitkaCalledProcessError,
    check_output,
    getExecutablePath,
    getNullOutput,
    withEnvironmentPathAdded,
)
from .FileOperations import (
    areSamePaths,
    deleteFile,
    getFileContentByLine,
    getNormalizedPathJoin,
    putBinaryFileContents,
    withTemporaryFilename,
)
from .Hashing import HashCRC32
from .Importing import withTemporarySysPathExtension
from .Utils import getArchitecture, getOS, isWin32Windows


def getSystemPrefixExecutable():
    """Return the sys.executable of the system prefix, i.e. breaking out of virtualenv.

    See getSystemPrefixPath() for details.

    Returns:
        str - path to system executable
    """
    # Yes, we want and need it here, pylint: disable=protected-access
    if hasattr(sys, "_base_executable"):
        return sys._base_executable

    sys_prefix = getSystemPrefixPath()
    if sys_prefix == sys.prefix:
        return sys.executable

    if areSamePaths(sys_prefix, sys.prefix):
        return sys.executable

    # The "sys.executable" is a good guess for the name, but we might have to
    # look for "python" effectively.
    candidate_names = (
        os.path.basename(sys.executable),
        "python.exe" if os.name == "nt" else "python",
        "python%s" % python_version_str,
    )

    for candidate_name in candidate_names:
        if os.name == "nt":
            candidate = os.path.join(sys_prefix, candidate_name)
        else:
            candidate = os.path.join(sys_prefix, "bin", candidate_name)

        if os.path.exists(candidate):
            return candidate

    # Fallback to sys.executable, which is not correct if we are in a virtualenv
    # but the best we can do if we didn't find the system prefix one.
    return sys.executable


def _getCandidateBinPaths(logger, site_packages):
    """Get the candidate binary paths for the private pip space."""
    download_folder = getPrivatePipBaseFolder()

    candidate_bin_paths = [
        os.path.join(download_folder, "bin"),
        os.path.join(download_folder, "usr", "bin"),
        os.path.join(download_folder, "usr", "local", "bin"),
    ]

    if isWin32Windows():
        candidate_bin_paths.insert(0, os.path.join(download_folder, "Scripts"))

    if site_packages is None:
        site_packages = getPrivatePipSitePackagesDir(logger=logger)

    if site_packages:
        if isWin32Windows():
            candidate_bin_paths.insert(
                0,
                os.path.join(
                    os.path.dirname(os.path.dirname(site_packages)), "Scripts"
                ),
            )
        else:
            candidate_bin_paths.insert(
                0,
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(site_packages))),
                    "bin",
                ),
            )

    return candidate_bin_paths


def _checkPrivatePipBinaryPath(
    logger,
    binary_name,
    binary_path,
    version,
    dependencies,
    check_binary,
):
    """Check if a binary path is version compatible and usable."""

    with withPrivatePipSitePackagesPathAdded(logger=logger):
        if version is None:
            ok = True
            message = None
        else:
            ok, message = _checkRequiredVersion(
                logger=logger,
                tool=binary_name,
                tool_call=[binary_path],
                dependencies=dependencies,
            )

        if ok and check_binary is not None:
            ok, message = check_binary(
                logger=logger,
                binary_path=binary_path,
            )

    if not ok and logger is not None:
        logger.info(
            "Rejecting '%s' binary '%s' due to: %s"
            % (binary_name, binary_path, message)
        )

    return ok, message


def _getPrivatePipBinaryPath(
    logger,
    binary_name,
    package_name,
    module_name,
    dependencies,
    check_binary,
    assume_yes_for_downloads,
    reject_message,
):
    """Get the path of a binary from the private pip space or globally.

    This first checks the system PATH for the binary. If found, it checks if its
    version and its dependencies' versions match the requirements. If they match,
    it returns the global binary.

    Otherwise, it downloads the package and its dependencies into the private pip
    space, verifies the installed binary there, and returns its path.
    """
    # Complex code, pylint: disable=too-many-locals

    version = getRequiredVersion(logger, package_name)

    candidate_bin_paths = _getCandidateBinPaths(logger=logger, site_packages=None)

    # Construct an extra_dir for search
    extra_dir = os.pathsep.join(candidate_bin_paths)

    binary_path = getExecutablePath(binary_name, extra_dir=extra_dir)
    force_package_update = False

    if binary_path is not None:
        ok, _message = _checkPrivatePipBinaryPath(
            logger=logger,
            binary_name=binary_name,
            binary_path=binary_path,
            version=version,
            dependencies=dependencies,
            check_binary=check_binary,
        )

        if ok:
            return binary_path, None, assume_yes_for_downloads

        force_package_update = True

    # Download, avoiding to use the result, which is the site-packages
    # folder
    site_packages_folder, assume_yes_for_downloads = tryDownloadPackageName(
        logger=logger,
        package_name=package_name,
        module_name=module_name,
        package_version=version,
        force_update=force_package_update,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )

    if site_packages_folder:
        for dep_package_name, dep_module_name, dep_reject_message in dependencies:
            _, assume_yes_for_downloads = tryDownloadPackageName(
                logger=logger,
                package_name=dep_package_name,
                module_name=dep_module_name,
                package_version=getRequiredVersion(logger, dep_package_name),
                force_update=force_package_update,
                assume_yes_for_downloads=assume_yes_for_downloads,
                reject_message=dep_reject_message,
            )

        # Check standard locations in the downloaded environment.
        for candidate in _getCandidateBinPaths(
            logger=logger, site_packages=site_packages_folder
        ):
            possible = os.path.join(candidate, binary_name)
            if isWin32Windows():
                possible += ".exe"

            if os.path.exists(possible):
                ok, _message = _checkPrivatePipBinaryPath(
                    logger=logger,
                    binary_name=binary_name,
                    binary_path=possible,
                    version=version,
                    dependencies=dependencies,
                    check_binary=check_binary,
                )

                if not ok:
                    continue

                return possible, site_packages_folder, assume_yes_for_downloads

    return None, site_packages_folder, assume_yes_for_downloads


def getPrivatePipBaseFolder():
    """Get the inline copy folder for a given name."""
    return os.path.join(
        getDownloadCacheDir(),
        "pip",
        "private-%s" % _getPrivatePipHash(),
    )


_private_pip_site_packages_dir = None


def getPrivatePipSitePackagesDir(logger):
    """Get the site-packages directory of the private pip space."""
    # We use the global statement to cache the result across calls.
    # pylint: disable=global-statement
    global _private_pip_site_packages_dir

    if _private_pip_site_packages_dir is None:
        download_folder = getPrivatePipBaseFolder()

        for root, dirnames, _filenames in os.walk(download_folder):
            found_candidate = None

            for candidate in getSitePackageCandidateNames():
                if candidate in dirnames:
                    # Unclear which one to use.
                    if found_candidate is not None:
                        return logger.sysexit(
                            "Scan for pip folder found multiple candidates: %s and %s."
                            % (found_candidate, candidate)
                        )

                    found_candidate = candidate

            if found_candidate:
                _private_pip_site_packages_dir = os.path.join(root, found_candidate)
                break

    return _private_pip_site_packages_dir


def withPrivatePipSitePackagesPathAdded(logger):
    """Context manager to add private pip site-packages to PYTHONPATH."""
    return withEnvironmentPathAdded(
        "PYTHONPATH", getPrivatePipSitePackagesDir(logger=logger), prefix=True
    )


def _isPackageInstalled(site_packages_folder, package_name, package_version):
    """Check if a package is installed in the given site-packages folder."""
    if package_version is None:
        return True

    # Basic check for dist-info specific to version
    dist_info_name = "%s-%s" % (
        package_name.replace("-", "_"),
        package_version,
    )

    dist_info_path = getNormalizedPathJoin(
        site_packages_folder,
        "%s.dist-info" % dist_info_name,
    )
    egg_info_path = getNormalizedPathJoin(
        site_packages_folder,
        "%s.egg-info" % dist_info_name,
    )

    if not os.path.isdir(dist_info_path) and not os.path.isdir(egg_info_path):
        return False
    else:
        # Metadata found, but check for conflicts with other versions,
        # e.g. when an upgrade was done, but not fully clean.
        for filename in os.listdir(site_packages_folder):
            if (
                filename.startswith(package_name + "-")
                and (filename.endswith(".dist-info") or filename.endswith(".egg-info"))
                and filename != os.path.basename(dist_info_path)
                and filename != os.path.basename(egg_info_path)
            ):
                return False

    return True


def tryDownloadPackageName(
    logger,
    package_name,
    module_name,
    package_version,
    force_update,
    assume_yes_for_downloads,
    reject_message,
):
    """Try to download a package from the private pip space."""
    download_folder = getPrivatePipBaseFolder()

    site_packages_folder = getPrivatePipSitePackagesDir(logger=logger)

    if site_packages_folder is not None and not force_update:
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            # If version is specified, check if it looks installed.
            if _isPackageInstalled(
                site_packages_folder=site_packages_folder,
                package_name=package_name,
                package_version=package_version,
            ):
                return (
                    site_packages_folder,
                    assume_yes_for_downloads,
                )

    if not _checkPackageConstraint(logger, package_name):
        return None, assume_yes_for_downloads

    if shouldDownload(
        message="Nuitka depends on '%s' to compile code, it is recommended."
        % package_name,
        reject_message=reject_message,
        assume_yes_for_downloads=assume_yes_for_downloads,
        download_ok=True,
    ):
        assume_yes_for_downloads = True

        if package_version is not None:
            package_spec = "%s==%s" % (package_name, package_version)
        else:
            package_spec = package_name

        command = (
            getSystemPrefixExecutable(),
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--disable-pip-version-check",
            "--ignore-installed",
            "--upgrade",
            "--root",
            download_folder,
            "--prefix",
            ".",
            package_spec,
        )

        interactive = sys.stdout.isatty()

        with getNullOutput() as null_output:
            exit_code = subprocess.call(
                command,
                shell=False,
                stdout=None if interactive else null_output,
                stderr=None if interactive else null_output,
            )

        if exit_code != 0:
            return None, assume_yes_for_downloads

        if site_packages_folder is None:
            site_packages_folder = getPrivatePipSitePackagesDir(logger=logger)

        if site_packages_folder is None or not _isPackageInstalled(
            site_packages_folder=site_packages_folder,
            package_name=package_name,
            package_version=package_version,
        ):
            return logger.sysexit(
                "Error, failed to download package %r into private pip space."
                % package_name
            )

    if site_packages_folder is not None:
        return (
            site_packages_folder,
            assume_yes_for_downloads,
        )

    return None, assume_yes_for_downloads


def _evaluateConstraint(logger, constraint, package_name):
    """Evaluate a package constraint."""
    try:
        # We trust the file content, pylint: disable=eval-used
        return eval(
            constraint,
            {
                "python_version": _PythonVersion(python_version_str),
                "os": os,
                "sys": sys,
            },
        )
    except Exception as e:  # pylint: disable=broad-except
        return logger.sysexit(
            "Error, checking constraint %r for package %r gave error: %r"
            % (constraint, package_name, e)
        )


def _checkPackageConstraint(logger, package_name):
    """Check if a package constraint is met."""
    # Make sure we have the constraints loaded.
    _parseRequirements(logger)

    constraints = _private_pip_constraints.get(package_name)

    if not constraints:
        return True

    for constraint in constraints:
        if _evaluateConstraint(logger, constraint, package_name):
            return True

    return False


def getPrivatePackage(
    logger,
    package_name,
    module_name,
    package_version,
    submodule_names,
    assume_yes_for_downloads,
    reject_message,
):
    """Get a package from the private pip space or globally.

    Args:
        package_name: name of the package to download
        module_name: name of the module to import
        package_version: version of the package to download
        submodule_names: tuple of submodule names to import before returning
        assume_yes_for_downloads: if tools should be downloaded automatically

    Returns:
        module: the imported module or None if not found
    """
    try:
        module = __import__(module_name, fromlist=["*"])

        if submodule_names:
            for submodule_name in submodule_names:
                __import__(module_name + "." + submodule_name)

        return module
    except ImportError:
        site_packages_folder, _assume_yes_for_downloads = tryDownloadPackageName(
            logger=logger,
            package_name=package_name,
            module_name=module_name.split(".")[0],
            package_version=package_version,
            force_update=False,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message=reject_message,
        )

        if site_packages_folder:
            with withTemporarySysPathExtension([site_packages_folder]):
                module = __import__(module_name, fromlist=["*"])

                if submodule_names:
                    for submodule_name in submodule_names:
                        __import__(module_name + "." + submodule_name)

            return module

        return None


def getZigBinaryPath(logger, assume_yes_for_downloads, reject_message):
    """Get the path of the Zig binary from the private pip space."""
    # spell-checker: ignore ziglang

    site_packages_folder, _assume_yes_for_downloads = tryDownloadPackageName(
        logger=logger,
        package_name="ziglang",
        module_name="ziglang",
        package_version=None,
        force_update=False,
        assume_yes_for_downloads=assume_yes_for_downloads,
        reject_message=reject_message,
    )

    # The "ziglang" package puts a "python-zig.exe" in the scripts folder, and
    # not found due to mismatch, but the actual "zig.exe" is in the site-packages
    # folder.
    if site_packages_folder:
        zig_exe_path = getNormalizedPathJoin(site_packages_folder, "ziglang", "zig")

        if isWin32Windows():
            zig_exe_path += ".exe"

        if os.path.exists(zig_exe_path):
            return zig_exe_path

    return None


def getClangFormatBinaryPath(logger, assume_yes_for_downloads, reject_message):
    """Get the path of the clang-format binary from the private pip space."""
    binary_path, _site_packages_folder, _assume_yes_for_downloads = (
        _getPrivatePipBinaryPath(
            logger=logger,
            binary_name="clang-format",
            package_name="clang-format",
            module_name="clang_format",
            dependencies=(),
            check_binary=None,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message=reject_message,
        )
    )
    return binary_path


def getBlackBinaryPath(logger, assume_yes_for_downloads):
    """Get the path of the black binary from the private pip space."""
    binary_path, _site_packages_folder, _assume_yes_for_downloads = (
        _getPrivatePipBinaryPath(
            logger=logger,
            binary_name="black",
            package_name="black",
            module_name="black",
            dependencies=(),
            check_binary=None,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message="Python formatting needs to use 'black'.",
        )
    )
    return binary_path


def getIsortBinaryPath(logger, assume_yes_for_downloads):
    """Get the path of the isort binary from the private pip space."""
    binary_path, _site_packages_folder, _assume_yes_for_downloads = (
        _getPrivatePipBinaryPath(
            logger=logger,
            binary_name="isort",
            package_name="isort",
            module_name="isort",
            dependencies=(),
            check_binary=None,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message="Python formatting needs to use 'isort'.",
        )
    )
    return binary_path


def _checkMdformatUsability(logger, binary_path):
    """Check if mdformat can format a minimal markdown file."""

    with withTemporaryFilename(suffix=".md") as temp_filename:
        try:
            putBinaryFileContents(temp_filename, b"# smoke\n")
            check_output([binary_path, "--check", temp_filename], logger=logger)
        except NuitkaCalledProcessError as e:
            stderr = e.stderr

            if str is not bytes and stderr is not None:
                stderr = stderr.decode("utf8", "ignore")

            return (
                False,
                "failed to format a test file: %s" % (stderr or e),
            )
        finally:
            deleteFile(temp_filename, must_exist=False)

    return True, None


def getMdformatBinaryPath(logger, assume_yes_for_downloads):
    """Get the path of the mdformat binary from the private pip space."""

    dependencies = (
        (
            "mdformat-gfm",
            "mdformat_gfm",
            "Markdown formatting needs to use 'mdformat-gfm'.",
        ),
        (
            "mdformat-frontmatter",
            "mdformat_frontmatter",
            "Markdown formatting needs to use 'mdformat-frontmatter'.",
        ),
        (
            "mdformat-footnote",
            "mdformat_footnote",
            "Markdown formatting needs to use 'mdformat-footnote'.",
        ),
    )

    mdformat_path, _site_packages_folder, _assume_yes_for_downloads = (
        _getPrivatePipBinaryPath(
            logger=logger,
            binary_name="mdformat",
            package_name="mdformat",
            module_name="mdformat",
            dependencies=dependencies,
            check_binary=_checkMdformatUsability,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message="Markdown formatting needs to use 'mdformat'.",
        )
    )

    return mdformat_path


def getRstfmtBinaryPath(logger, assume_yes_for_downloads):
    """Get the path of the rstfmt binary from the private pip space."""
    binary_path, _site_packages_folder, _assume_yes_for_downloads = (
        _getPrivatePipBinaryPath(
            logger=logger,
            binary_name="rstfmt",
            package_name="rstfmt",
            module_name="rstfmt",
            dependencies=(),
            check_binary=None,
            assume_yes_for_downloads=assume_yes_for_downloads,
            reject_message="ReStructuredText formatting needs to use 'rstfmt'.",
        )
    )
    return binary_path


@total_ordering
class _PythonVersion(object):
    def __init__(self, version_str):
        self.version = tuple(int(x) for x in version_str.split("."))

    @staticmethod
    def _makeTuple(other):
        if str is not bytes and isinstance(other, (str, bytes)):
            return tuple(int(x) for x in other.split("."))
        return other

    def __eq__(self, other):
        return self.version == self._makeTuple(other)

    def __lt__(self, other):
        return self.version < self._makeTuple(other)


_private_pip_requirements = None
_private_pip_constraints = None


def _parseRequirements(logger):
    """Parse the requirements-private.txt file."""
    # We use the global statement to cache the result across calls.
    # pylint: disable=global-statement
    global _private_pip_requirements, _private_pip_constraints

    if _private_pip_requirements is None:
        _private_pip_requirements = OrderedDict()
        _private_pip_constraints = OrderedDict()

        for line in getFileContentByLine(
            os.path.join(os.path.dirname(__file__), "requirements-private.txt")
        ):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = re.split(r"\s*;\s*", line, maxsplit=1)

            if len(parts) > 1:
                tool_part = parts[0]
                constraint_part = parts[1]
            else:
                tool_part = line
                constraint_part = None

            if "==" in tool_part:
                tool_name = tool_part.split("==")[0].strip()
            else:
                for other_comparison in (">=", "<=", ">", "<", "~="):
                    if other_comparison in tool_part:
                        msg = (
                            """\
Error, invalid requirement format in 'requirements-private.txt' line %r, only '==' is allowed."""
                            % line
                        )

                        return logger.sysexit(msg)

                tool_name = tool_part.strip()

            if tool_name not in _private_pip_requirements:
                _private_pip_requirements[tool_name] = []
                _private_pip_constraints[tool_name] = []

            _private_pip_requirements[tool_name].append(line)
            if constraint_part is not None:
                _private_pip_constraints[tool_name].append(constraint_part)

    return _private_pip_requirements


def _getPrivatePipHash():
    """Calculate the hash of the private pip space."""
    private_pip_hash = HashCRC32()
    private_pip_hash.updateFromValues(
        python_version_str,
        getOS(),
        getArchitecture(),
    )
    private_pip_hash.updateFromValues(_parseRequirements(logger=None))

    return private_pip_hash.asHexDigest()


def getRequiredVersion(logger, tool):
    """Get the required version of a tool from requirements-private.txt."""
    requirements = _parseRequirements(logger)

    if tool not in requirements:
        return logger.sysexit(
            "Error, cannot find %r in 'requirements-private.txt' file." % tool
        )

    for line in requirements[tool]:
        parts = re.split(r"\s*;\s*", line, maxsplit=1)

        if len(parts) > 1:
            constraint = parts[1]
            if not _evaluateConstraint(logger, constraint, tool):
                continue

        tool_part = parts[0]

        # TODO: This is not quite correct for all packages, but we only have equality
        # checks right now.
        if "==" in tool_part:
            return tool_part.split("==")[1].strip()
        else:
            return None

    return None


_check_required_version_cache = {}


def _checkRequiredVersion(logger, tool, tool_call, dependencies):
    """Check if the version of a tool matches the requirement."""

    # Complex code, pylint: disable=too-many-branches,too-many-locals
    required_version = getRequiredVersion(logger=logger, tool=tool)

    tool_call = tuple(list(tool_call) + ["--version"])

    if tool_call in _check_required_version_cache:
        return _check_required_version_cache[tool_call]

    try:
        version_output = check_output(tool_call)
    except NuitkaCalledProcessError as e:
        result = False, "failed to execute: %s" % e.stderr
        _check_required_version_cache[tool_call] = result
        return result

    if str is not bytes:
        version_output = version_output.decode("utf8")

    if dependencies:
        for dep_package_name, _dep_module_name, _dep_reject_message in dependencies:
            plugin_ver = getRequiredVersion(logger, dep_package_name)
            if plugin_ver:
                search_name_1 = dep_package_name
                search_name_2 = dep_package_name.replace("-", "_")

                if not any(
                    "%s %s" % (name, plugin_ver) in version_output
                    for name in (search_name_1, search_name_2)
                ):
                    result = (
                        False,
                        "Missing or mismatched dependency '%s %s' in '%s'."
                        % (dep_package_name, plugin_ver, tool),
                    )
                    _check_required_version_cache[tool_call] = result
                    return result

    actual_version = None
    for line in version_output.splitlines():
        line = line.strip()

        if line.startswith(
            ("black, ", "python -m black,", "__main__.py, ", "mdformat ")
        ):
            if "(" in line:
                line = line[: line.rfind("(")].strip()

            actual_version = line.split()[-1]
            break
        if line.startswith("VERSION "):
            actual_version = line.split()[-1]
            break
        # spell-checker: ignore rstfmt
        if line.startswith("rstfmt "):
            actual_version = line.split()[-1]
            break
        if line.startswith("clang-format version "):
            actual_version = line.split()[2]
            break

    if not actual_version:
        result = False, "Error, couldn't determine version output of '%s' ('%s')" % (
            tool,
            " ".join(tool_call),
        )
        _check_required_version_cache[tool_call] = result
        return result

    message = "Version of '%s' via '%s' is required to be %r and not %r." % (
        tool,
        " ".join(tool_call),
        required_version,
        actual_version,
    )

    result = required_version == actual_version, message
    _check_required_version_cache[tool_call] = result
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
