#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for private pip space to download packages into."""

import os
import subprocess
import sys

from nuitka.PythonVersions import (
    getSitePackageCandidateNames,
    python_version_str,
)

from .Download import getDownloadCacheDir, shouldDownload
from .Execution import (
    NuitkaCalledProcessError,
    check_output,
    getExecutablePath,
    withEnvironmentPathAdded,
)
from .FileOperations import getFileContentByLine, getNormalizedPathJoin
from .Utils import getArchitecture, getOS


def _getCandidateBinPaths(site_packages):
    download_folder = getPrivatePipBaseFolder()

    candidate_bin_paths = [
        os.path.join(download_folder, "bin"),
        os.path.join(download_folder, "usr", "bin"),
        os.path.join(download_folder, "usr", "local", "bin"),
    ]

    if os.name == "nt":
        candidate_bin_paths.insert(0, os.path.join(download_folder, "Scripts"))

    if site_packages is None:
        site_packages = getPrivatePipSitePackagesDir()

    if site_packages:
        if os.name == "nt":
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


def _getPrivatePipBinaryPath(
    logger, binary_name, package_name, module_name, version, assume_yes_for_downloads
):
    candidate_bin_paths = _getCandidateBinPaths(site_packages=None)

    # Construct an extra_dir for search
    extra_dir = os.pathsep.join(candidate_bin_paths)

    binary_path = getExecutablePath(binary_name, extra_dir=extra_dir)

    if binary_path is not None:
        if version is None:
            return binary_path, None

        with withPrivatePipSitePackagesPathAdded():
            ok, _message = _checkRequiredVersion(
                logger=logger, tool=binary_name, tool_call=[binary_path]
            )
        if ok:
            return binary_path, None

    # Download, avoiding to use the result, which is the site-packages
    # folder
    site_packages_folder = tryDownloadPackageName(
        package_name,
        module_name,
        version,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    if site_packages_folder:
        # Check standard locations in the downloaded environment.
        for candidate in _getCandidateBinPaths(site_packages=site_packages_folder):
            possible = os.path.join(candidate, binary_name)
            if os.name == "nt":
                possible += ".exe"

            if os.path.exists(possible):
                if version is not None:
                    with withPrivatePipSitePackagesPathAdded():
                        ok, _message = _checkRequiredVersion(
                            logger=logger, tool=binary_name, tool_call=[possible]
                        )
                    if not ok:
                        continue

                return possible, site_packages_folder

    return None, site_packages_folder


def getPrivatePipBaseFolder():
    """Get the inline copy folder for a given name."""
    return os.path.join(
        getDownloadCacheDir(),
        "pip-private-%s-%s-%s" % (python_version_str, getOS(), getArchitecture()),
    )


_private_pip_site_packages_dir = None


def getPrivatePipSitePackagesDir():
    # We use the global statement to cache the result across calls.
    # pylint: disable=global-statement
    global _private_pip_site_packages_dir

    if _private_pip_site_packages_dir:
        return _private_pip_site_packages_dir

    download_folder = getPrivatePipBaseFolder()

    for root, dirnames, _filenames in os.walk(download_folder):
        found_candidate = None
        for candidate in getSitePackageCandidateNames():
            if candidate in dirnames:
                # Unclear which one to use.
                if found_candidate is not None:
                    return

                found_candidate = candidate

        if found_candidate:
            _private_pip_site_packages_dir = os.path.join(root, found_candidate)
            return _private_pip_site_packages_dir

    return None


def withPrivatePipSitePackagesPathAdded():
    return withEnvironmentPathAdded(
        "PYTHONPATH", getPrivatePipSitePackagesDir(), prefix=True
    )


def tryDownloadPackageName(
    package_name, module_name, package_version, assume_yes_for_downloads
):
    download_folder = getPrivatePipBaseFolder()

    site_packages_folder = getPrivatePipSitePackagesDir()

    if site_packages_folder is not None:
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder

    if shouldDownload(
        message="Nuitka depends on '%s' to compile code, it is recommended."
        % package_name,
        reject="Nuitka needs to use '%s'." % package_name,
        assume_yes_for_downloads=assume_yes_for_downloads,
        download_ok=True,
    ):
        if package_version is not None:
            package_spec = "%s==%s" % (package_name, package_version)
        else:
            package_spec = package_name

        exit_code = subprocess.call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-warn-script-location",
                "--disable-pip-version-check",
                "--ignore-installed",
                "--root",
                download_folder,
                package_spec,
            ],
            shell=False,
        )

        if exit_code != 0:
            return None

        if site_packages_folder is None:
            site_packages_folder = getPrivatePipSitePackagesDir()

    if site_packages_folder is not None:
        candidate = getNormalizedPathJoin(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder


def getPrivatePackage(
    package_name,
    module_name,
    package_version,
    submodule_names,
    assume_yes_for_downloads,
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
        site_packages_folder = tryDownloadPackageName(
            package_name=package_name,
            module_name=module_name.split(".")[0],
            package_version=package_version,
            assume_yes_for_downloads=assume_yes_for_downloads,
        )

        if site_packages_folder:
            from .Importing import withTemporarySysPathExtension

            with withTemporarySysPathExtension([site_packages_folder]):
                module = __import__(module_name, fromlist=["*"])

                if submodule_names:
                    for submodule_name in submodule_names:
                        __import__(module_name + "." + submodule_name)

            return module

        return None


def getZigBinaryPath(logger, assume_yes_for_downloads):
    # spell-checker: ignore ziglang

    zig_exe_path, site_packages_folder = _getPrivatePipBinaryPath(
        logger=logger,
        binary_name="zig",
        package_name="ziglang",
        module_name="ziglang",
        version=None,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    if zig_exe_path:
        return zig_exe_path

    if site_packages_folder:
        zig_exe_path = getNormalizedPathJoin(site_packages_folder, "ziglang", "zig")

        if os.name == "nt":
            zig_exe_path += ".exe"

        if os.path.exists(zig_exe_path):
            return zig_exe_path

    return None


def getClangFormatBinaryPath(logger, assume_yes_for_downloads):
    return _getPrivatePipBinaryPath(
        logger=logger,
        binary_name="clang-format",
        package_name="clang-format",
        module_name="clang_format",
        version="21.1.0",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )[0]


def getBlackBinaryPath(logger, assume_yes_for_downloads):
    return _getPrivatePipBinaryPath(
        logger=logger,
        binary_name="black",
        package_name="black",
        module_name="black",
        version="25.12.0",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )[0]


def getIsortBinaryPath(logger, assume_yes_for_downloads):
    return _getPrivatePipBinaryPath(
        logger=logger,
        binary_name="isort",
        package_name="isort",
        module_name="isort",
        version="5.13.2",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )[0]


def getMdformatBinaryPath(logger, assume_yes_for_downloads):
    mdformat_path, site_packages_folder = _getPrivatePipBinaryPath(
        logger=logger,
        binary_name="mdformat",
        package_name="mdformat",
        module_name="mdformat",
        version="0.7.16",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    if mdformat_path and site_packages_folder:
        tryDownloadPackageName(
            package_name="mdformat-gfm",
            module_name="mdformat_gfm",
            package_version="0.3.5",
            assume_yes_for_downloads=assume_yes_for_downloads,
        )
        tryDownloadPackageName(
            package_name="mdformat-frontmatter",
            module_name="mdformat_frontmatter",
            package_version="2.0.1",
            assume_yes_for_downloads=assume_yes_for_downloads,
        )
        tryDownloadPackageName(
            package_name="mdformat-footnote",
            module_name="mdformat_footnote",
            package_version="0.1.1",
            assume_yes_for_downloads=assume_yes_for_downloads,
        )

    return mdformat_path


def getRstfmtBinaryPath(logger, assume_yes_for_downloads):
    return _getPrivatePipBinaryPath(
        logger=logger,
        binary_name="rstfmt",
        package_name="rstfmt",
        module_name="rstfmt",
        version="0.0.14",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )[0]


def _getRequirementsContentsByLine():
    """Get the contents of requirements-private.txt as a list of lines."""
    return getFileContentByLine(
        os.path.join(os.path.dirname(__file__), "requirements-private.txt")
    )


def _getRequiredVersion(logger, tool):
    """Get the required version of a tool from requirements-private.txt."""
    for line in _getRequirementsContentsByLine():
        if line.startswith(tool + " =="):
            return line.split()[2]

    return logger.sysexit(
        "Error, cannot find %r in 'requirements-private.txt' file." % tool
    )


def _checkRequiredVersion(logger, tool, tool_call):
    required_version = _getRequiredVersion(logger=logger, tool=tool)

    tool_call = list(tool_call) + ["--version"]

    try:
        version_output = check_output(tool_call)
    except NuitkaCalledProcessError as e:
        return False, "failed to execute: %s" % e.stderr

    if str is not bytes:
        version_output = version_output.decode("utf8")

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
        return False, "Error, couldn't determine version output of '%s' ('%s')" % (
            tool,
            " ".join(tool_call),
        )

    message = "Version of '%s' via '%s' is required to be %r and not %r." % (
        tool,
        " ".join(tool_call),
        required_version,
        actual_version,
    )

    return required_version == actual_version, message


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
