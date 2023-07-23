#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""DLL dependency scan methods for macOS. """

import os
import re
import sys

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Errors import NuitkaForbiddenDLLEncounter
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonFlavors import isAnacondaPython, isNuitkaPython
from nuitka.PythonVersions import python_version
from nuitka.Tracing import inclusion_logger
from nuitka.utils.FileOperations import areSamePaths, isFilenameBelowPath
from nuitka.utils.Importing import getSharedLibrarySuffixes
from nuitka.utils.Json import loadJsonFromFilename
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    getOtoolDependencyOutput,
    getOtoolListing,
)

from .DllDependenciesCommon import getLdLibraryPath

# Detected Python rpath is cached.
_detected_python_rpaths = None


def _detectPythonRpaths():
    result = []

    if isAnacondaPython() and "CONDA_PREFIX" in os.environ:
        candidate = os.path.normpath(os.path.join(os.environ["CONDA_PREFIX"], "lib"))

        if os.path.isdir(candidate):
            result.append(candidate)

    if isAnacondaPython() and "CONDA_PYTHON_EXE" in os.environ:
        candidate = os.path.normpath(
            os.path.join(os.path.dirname(os.environ["CONDA_PYTHON_EXE"]), "..", "lib")
        )

        if os.path.isdir(candidate):
            result.append(candidate)

    return tuple(result)


def detectBinaryPathDLLsMacOS(
    original_dir, binary_filename, package_name, keep_unresolved, recursive
):
    assert os.path.exists(binary_filename), binary_filename

    # This is for Anaconda, which puts required libraries of packages in this folder.
    # do it only once, pylint: disable=global-statement
    global _detected_python_rpaths
    if _detected_python_rpaths is None:
        _detected_python_rpaths = _detectPythonRpaths()

    package_specific_dirs = getLdLibraryPath(
        package_name=package_name,
        python_rpaths=_detected_python_rpaths,
        original_dir=original_dir,
    )

    # This is recursive potentially and might add more and more.
    stdout = getOtoolDependencyOutput(
        filename=binary_filename,
        package_specific_dirs=package_specific_dirs,
    )
    paths = _parseOtoolListingOutput(stdout)

    had_self, resolved_result = _resolveBinaryPathDLLsMacOS(
        original_dir=original_dir,
        binary_filename=binary_filename,
        paths=paths,
        package_specific_dirs=package_specific_dirs,
        package_name=package_name,
    )

    if recursive:
        merged_result = OrderedDict(resolved_result)

        for sub_dll_filename in resolved_result:
            _, sub_result = detectBinaryPathDLLsMacOS(
                original_dir=os.path.dirname(sub_dll_filename),
                binary_filename=sub_dll_filename,
                package_name=package_name,
                recursive=True,
                keep_unresolved=True,
            )

            merged_result.update(sub_result)

        resolved_result = merged_result

    if keep_unresolved:
        return had_self, resolved_result
    else:
        return OrderedSet(resolved_result)


def _parseOtoolListingOutput(output):
    paths = OrderedSet()

    for line in output.split(b"\n")[1:]:
        if str is not bytes:
            line = line.decode("utf8")

        if not line:
            continue

        filename = line.split(" (", 1)[0].strip()

        # Ignore dependency from system paths.
        if not isFilenameBelowPath(
            path=(
                "/usr/lib/",
                "/System/Library/Frameworks/",
                "/System/Library/PrivateFrameworks/",
            ),
            filename=filename,
        ):
            paths.add(filename)

    return paths


def _resolveBinaryPathDLLsMacOS(
    original_dir, binary_filename, paths, package_specific_dirs, package_name
):
    # Quite a few variations to consider
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    had_self = False

    result = OrderedDict()

    rpaths = _detectBinaryRPathsMacOS(original_dir, binary_filename)
    rpaths.update(package_specific_dirs)

    for path in paths:
        if path.startswith("@rpath/"):
            # Resolve rpath to just the ones given, first match.
            for rpath in rpaths:
                if os.path.exists(os.path.join(rpath, path[7:])):
                    resolved_path = os.path.normpath(os.path.join(rpath, path[7:]))
                    break
            else:
                # This is only a guess, might be missing package specific directories.
                resolved_path = os.path.normpath(os.path.join(original_dir, path[7:]))
        elif path.startswith("@loader_path/"):
            resolved_path = os.path.normpath(os.path.join(original_dir, path[13:]))
        elif os.path.basename(path) == os.path.basename(binary_filename):
            # We ignore the references to itself coming from the library id.
            continue
        elif isNuitkaPython() and not os.path.isabs(path) and not os.path.exists(path):
            # Although Nuitka Python statically links all packages, some of them
            # have proprietary dependencies that cannot be statically built and
            # must instead be linked to the python executable. Due to how the
            # python executable is linked, we end up with relative paths to
            # dependencies, so we need to scan the Nuitka Python library
            # directories for a matching dll.
            link_data = loadJsonFromFilename(os.path.join(sys.prefix, "link.json"))
            for library_dir in link_data["library_dirs"]:
                candidate = os.path.join(library_dir, path)
                if os.path.exists(candidate):
                    resolved_path = os.path.normpath(candidate)
                    break
        else:
            resolved_path = path

        # Some extension modules seem to reference themselves a wrong name,
        # duplicating their module name into the filename, but that does
        # not exist.
        if not os.path.exists(resolved_path) and package_name is not None:
            parts = os.path.basename(resolved_path).split(".")

            if parts[0] == package_name.asString():
                resolved_path = os.path.join(
                    os.path.dirname(resolved_path), ".".join(parts[1:])
                )

        # Some extension modules seem to reference themselves by a different
        # extension module name, so use that if it exists.
        if not os.path.exists(resolved_path) and python_version >= 0x300:
            so_suffixes = getSharedLibrarySuffixes()[:-1]

            specific_suffix = so_suffixes[0]
            abi_suffix = so_suffixes[1]

            if resolved_path.endswith(specific_suffix):
                candidate = resolved_path[: -len(specific_suffix)] + abi_suffix
            elif resolved_path.endswith(abi_suffix):
                candidate = resolved_path[: -len(specific_suffix)] + abi_suffix
            else:
                candidate = None

            if candidate is not None and os.path.exists(candidate):
                resolved_path = candidate

        # Sometimes self-dependencies are on a numbered version, but deployed is
        # one version without it. The macOS just ignores that, and so we do.
        if not os.path.exists(resolved_path):
            match = re.match(r"^(.*)\.\d+\.dylib$", resolved_path)

            if match:
                candidate = match.group(1) + ".dylib"

                if os.path.exists(candidate):
                    resolved_path = candidate
                else:
                    candidate = os.path.join(original_dir, os.path.basename(candidate))

                    if os.path.exists(candidate):
                        resolved_path = candidate

        if not os.path.exists(resolved_path):
            acceptable, plugin_name = Plugins.isAcceptableMissingDLL(
                package_name=package_name,
                filename=binary_filename,
            )

            # TODO: Missing DLLs that are accepted, are not really forbidden, we
            # should instead acknowledge them as missing, and treat that properly
            # in using code.
            if acceptable is True:
                raise NuitkaForbiddenDLLEncounter(binary_filename, plugin_name)

            if not path.startswith(("@", "/")):
                continue

            inclusion_logger.sysexit(
                "Error, failed to find path %s (resolved DLL to %s) for %s from '%s', please report the bug."
                % (path, resolved_path, binary_filename, package_name)
            )

        # Some libraries depend on themselves.
        if areSamePaths(binary_filename, resolved_path):
            had_self = True
            continue

        result[resolved_path] = path

    return had_self, result


def _detectBinaryRPathsMacOS(original_dir, binary_filename):
    stdout = getOtoolListing(binary_filename)

    lines = stdout.split(b"\n")

    result = OrderedSet()
    result.add(original_dir)

    for i, line in enumerate(lines):
        if line.endswith(b"cmd LC_RPATH"):
            line = lines[i + 2]
            if str is not bytes:
                line = line.decode("utf8")

            line = line.split("path ", 1)[1]
            line = line.split(" (offset", 1)[0]

            if line.startswith("@loader_path"):
                line = os.path.join(original_dir, line[13:])
            elif line.startswith("@executable_path"):
                continue

            result.add(line)

    return result


def fixupBinaryDLLPathsMacOS(
    binary_filename, package_name, original_location, standalone_entry_points
):
    """For macOS, the binary needs to be told to use relative DLL paths"""
    try:
        had_self, rpath_map = detectBinaryPathDLLsMacOS(
            original_dir=os.path.dirname(original_location),
            binary_filename=original_location,
            package_name=package_name,
            keep_unresolved=True,
            recursive=False,
        )
    except NuitkaForbiddenDLLEncounter:
        inclusion_logger.info("Not copying forbidden DLL '%s'." % binary_filename)
    else:
        mapping = []

        for resolved_filename, rpath_filename in rpath_map.items():
            for standalone_entry_point in standalone_entry_points:
                if resolved_filename == standalone_entry_point.source_path:
                    dist_path = standalone_entry_point.dest_path
                    break
            else:
                dist_path = None

            if dist_path is None:
                inclusion_logger.sysexit(
                    """\
    Error, problem with dependency scan of '%s' with '%s' please report the bug."""
                    % (original_location, rpath_filename)
                )

            mapping.append((rpath_filename, "@executable_path/" + dist_path))

        if mapping or had_self:
            callInstallNameTool(
                filename=binary_filename,
                mapping=mapping,
                id_path=os.path.basename(binary_filename) if had_self else None,
                rpath=None,
            )
