#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Handling of macOS frameworks in standalone mode."""

import os

from nuitka.Tracing import inclusion_logger
from nuitka.utils.FileOperations import (
    areSamePaths,
    deleteFile,
    doesFileStartWithBytes,
    getFileList,
    getNormalizedPathJoin,
    getSubDirectories,
    isLink,
    listDir,
    relpath,
    removeDirectory,
)
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    getSharedLibraryRPATHs,
)

_mach_o_binary_magic_numbers = (
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
    b"\xca\xfe\xba\xbf",
    b"\xbf\xba\xfe\xca",
)


def _isMachOBinary(filename):
    """Check if a file is a Mach-O binary.

    Args:
        filename: The file to check.

    Returns:
        bool: True if the file starts with a Mach-O magic number.
    """
    return doesFileStartWithBytes(filename, _mach_o_binary_magic_numbers)


def _removeMacOSFrameworkBundlePath(path):
    if isLink(path) or os.path.isfile(path):
        deleteFile(path, must_exist=False)
    elif os.path.isdir(path):
        removeDirectory(
            path=path,
            logger=inclusion_logger,
            ignore_errors=False,
            extra_recommendation=None,
        )


def _makeMacOSFrameworkBundleSymlink(link_path, link_target):
    if isLink(link_path) and os.readlink(link_path) == link_target:
        return

    if os.path.exists(link_path) or isLink(link_path):
        _removeMacOSFrameworkBundlePath(link_path)

    os.symlink(link_target, link_path)


def _detectMacOSFrameworkCurrentVersion(framework_path):
    framework_name = os.path.basename(framework_path)[: -len(".framework")]
    versions_dir = getNormalizedPathJoin(framework_path, "Versions")

    if not os.path.isdir(versions_dir):
        return None, None

    version_candidates = []

    for version_path, version_name in listDir(versions_dir):
        if version_name == "Current":
            continue

        if not os.path.isdir(version_path):
            continue

        if _isMacOSFrameworkVersionPath(version_path, framework_name):
            version_candidates.append((version_name, version_path))

    if not version_candidates:
        return None, None

    current_path = getNormalizedPathJoin(versions_dir, "Current")

    if isLink(current_path):
        current_target_path = getNormalizedPathJoin(
            versions_dir, os.readlink(current_path)
        )

        for version_name, version_path in version_candidates:
            if areSamePaths(version_path, current_target_path):
                return version_name, version_path

    return version_candidates[0]


def getMacOSFrameworkVersionDir(framework_path):
    """Get the version directory name of a framework bundle.

    Args:
        framework_path: Path of the framework directory.

    Returns:
        str or None: The version directory name, or None if not found.
    """
    version_name, _version_path = _detectMacOSFrameworkCurrentVersion(
        framework_path=framework_path
    )

    return version_name


def _isMacOSFrameworkVersionPath(path, framework_name):
    framework_binary_path = getNormalizedPathJoin(path, framework_name)

    return os.path.isfile(framework_binary_path) and _isMachOBinary(
        framework_binary_path
    )


def _fixMacOSFrameworkHelperRPATHs(framework_path, version_path):
    """Fix rpaths of helper executables below a framework version directory.

    Notes:
        When root level directories of a framework are moved below the version
        directory during inclusion, the relative rpaths of helper executables
        inside them no longer match their original depth. Add an rpath to the
        framework parent directory, where the sibling frameworks are located.

    Args:
        framework_path: Path of the framework directory.
        version_path: Path of the version directory inside the framework.

    Returns:
        None
    """
    helpers_path = getNormalizedPathJoin(version_path, "Helpers")

    if not os.path.isdir(helpers_path):
        return

    # If the framework has a root level "Helpers" directory, then its layout
    # was not changed, and the existing rpaths still work.
    if os.path.exists(getNormalizedPathJoin(framework_path, "Helpers")):
        return

    framework_parent_path = os.path.dirname(framework_path)

    for filename in getFileList(helpers_path):
        filename_dir = os.path.dirname(filename)

        if os.path.basename(filename_dir) != "MacOS":
            continue

        if os.path.basename(os.path.dirname(filename_dir)) != "Contents":
            continue

        if isLink(filename) or not os.path.isfile(filename):
            continue

        if not _isMachOBinary(filename):
            continue

        rpath = "@loader_path/" + relpath(framework_parent_path, start=filename_dir)

        if rpath in getSharedLibraryRPATHs(filename):
            continue

        callInstallNameTool(
            filename=filename,
            mapping=(),
            id_path=None,
            rpath=rpath,
        )


def _normalizeMacOSFrameworkBundleLayout(framework_path):
    framework_name = os.path.basename(framework_path)[: -len(".framework")]

    version_name, version_path = _detectMacOSFrameworkCurrentVersion(
        framework_path=framework_path
    )

    if version_name is None:
        return

    top_level_code_signature_path = getNormalizedPathJoin(
        framework_path, "_CodeSignature"
    )

    if os.path.isdir(top_level_code_signature_path):
        _removeMacOSFrameworkBundlePath(top_level_code_signature_path)

    versions_dir = getNormalizedPathJoin(framework_path, "Versions")

    for version_entry_path, version_entry_name in listDir(versions_dir):
        if version_entry_name == "Current":
            continue

        if _isMacOSFrameworkVersionPath(version_entry_path, framework_name):
            continue

        _removeMacOSFrameworkBundlePath(version_entry_path)

    _fixMacOSFrameworkHelperRPATHs(
        framework_path=framework_path, version_path=version_path
    )

    _makeMacOSFrameworkBundleSymlink(
        link_path=getNormalizedPathJoin(versions_dir, "Current"),
        link_target=version_name,
    )

    versioned_binary_path = getNormalizedPathJoin(version_path, framework_name)

    if os.path.exists(versioned_binary_path):
        _makeMacOSFrameworkBundleSymlink(
            link_path=getNormalizedPathJoin(framework_path, framework_name),
            link_target=getNormalizedPathJoin("Versions", "Current", framework_name),
        )

    for entry_path, entry_name in listDir(version_path):
        if entry_name == "_CodeSignature":
            continue

        if os.path.isdir(entry_path):
            _makeMacOSFrameworkBundleSymlink(
                link_path=getNormalizedPathJoin(framework_path, entry_name),
                link_target=getNormalizedPathJoin("Versions", "Current", entry_name),
            )


def normalizeMacOSFrameworkBundleLayouts(frameworks_dir):
    """Normalize the layout of macOS frameworks in an app bundle.

    Args:
        frameworks_dir: Path of the directory containing the frameworks.

    Returns:
        tuple: Paths of the normalized frameworks.
    """
    if not os.path.isdir(frameworks_dir):
        return ()

    framework_paths = [
        sub_directory
        for sub_directory in getSubDirectories(frameworks_dir)
        if sub_directory.endswith(".framework")
    ]

    for framework_path in framework_paths:
        _normalizeMacOSFrameworkBundleLayout(framework_path=framework_path)

    return tuple(framework_paths)


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
