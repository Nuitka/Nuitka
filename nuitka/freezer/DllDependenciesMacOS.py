#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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
from nuitka.utils.FileOperations import (
    areSamePaths,
    changeFilenameExtension,
    getReportPath,
    isFilenameBelowPath,
)
from nuitka.utils.Importing import getExtensionModuleSuffixes
from nuitka.utils.Json import loadJsonFromFilename
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    getOtoolDependencyOutput,
    getOtoolListing,
    parseOtoolListingOutput,
)
from nuitka.utils.Utils import getArchitecture

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

    return tuple(set(result))


def detectBinaryPathDLLsMacOS(
    original_dir,
    binary_filename,
    package_name,
    keep_unresolved,
    recursive,
    recursive_dlls=None,
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

        # For recursive DLL detection, cycle may exist, so we keep track of what
        # was seen so far.
        if recursive_dlls is None:
            recursive_dlls = set([binary_filename])
        else:
            recursive_dlls = set(recursive_dlls)
            recursive_dlls.add(binary_filename)

        for sub_dll_filename in resolved_result:
            if sub_dll_filename in recursive_dlls:
                continue

            _, sub_result = detectBinaryPathDLLsMacOS(
                original_dir=os.path.dirname(sub_dll_filename),
                binary_filename=sub_dll_filename,
                package_name=package_name,
                keep_unresolved=True,
                recursive=True,
                recursive_dlls=recursive_dlls,
            )

            merged_result.update(sub_result)

        resolved_result = merged_result

    if keep_unresolved:
        return had_self, resolved_result
    else:
        return OrderedSet(resolved_result)


def _parseOtoolListingOutput(output):
    result = OrderedSet()

    for filename in parseOtoolListingOutput(output):
        # Ignore dependency from system paths.
        if not isFilenameBelowPath(
            path=(
                "/usr/lib/",
                "/System/Library/Frameworks/",
                "/System/Library/PrivateFrameworks/",
            ),
            filename=filename,
        ):
            result.add(filename)

    return result


def _getNonVersionedDllFilenames2(filename):
    yield filename

    if filename.endswith(".dylib"):
        if getArchitecture() == "arm64":
            yield filename[:-6] + "_arm64.dylib"
        else:
            yield filename[:-6] + "_x86_64.dylib"

    match = re.match(r"^(.*?)(\.\d+)+\.dylib$", filename)

    if match:
        yield match.group(1) + ".dylib"

        # TODO: The versioned filename, might do the same, and so could the
        # "x86_64" specific DLL be a thing too, but we should have actual
        # examples to be sure they are covered with tests.
        if getArchitecture() == "arm64":
            yield match.group(1) + "_arm64.dylib"
        else:
            yield match.group(1) + "_x86_64.dylib"

    if filename.endswith(".so"):
        yield changeFilenameExtension(filename, ".dylib")


def _getNonVersionedDllFilenames(dll_filename, package_name):
    for filename in _getNonVersionedDllFilenames2(dll_filename):
        yield filename

    # Some build systems, internally prefix DLLs with package names, attempt
    # those removed as well.
    if package_name is not None:
        package_prefix = package_name.asString() + "."

        if os.path.basename(dll_filename).startswith(package_prefix):
            dll_filename = os.path.join(
                os.path.dirname(dll_filename),
                os.path.basename(dll_filename)[len(package_prefix) :],
            )

            for filename in _getNonVersionedDllFilenames2(dll_filename):
                yield filename


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
            library_name = path[7:]

            for rpath in rpaths:
                if os.path.exists(os.path.join(rpath, library_name)):
                    resolved_path = os.path.normpath(os.path.join(rpath, path[7:]))
                    break
            else:
                # These have become virtual in later macOS, spell-checker: ignore libz
                if library_name in ("libc++.1.dylib", "libz.1.dylib"):
                    continue

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
        # extension module name, so use that if it exists, and some versioned
        # DLL dependencies do not matter.
        if python_version >= 0x300:
            so_suffixes = getExtensionModuleSuffixes()[:-1]

            specific_suffix = so_suffixes[0]
            abi_suffix = so_suffixes[1]

            for resolved_path_candidate in _getNonVersionedDllFilenames(
                dll_filename=resolved_path, package_name=package_name
            ):
                if os.path.exists(resolved_path_candidate):
                    resolved_path = resolved_path_candidate
                    break

                if resolved_path_candidate.endswith(specific_suffix):
                    candidate = (
                        resolved_path_candidate[: -len(specific_suffix)] + abi_suffix
                    )
                elif resolved_path_candidate.endswith(abi_suffix):
                    candidate = (
                        resolved_path_candidate[: -len(specific_suffix)] + abi_suffix
                    )
                else:
                    candidate = None

                if candidate is not None and os.path.exists(candidate):
                    resolved_path = candidate
                    break

        # Sometimes self-dependencies are on a numbered version, but deployed is
        # one version without it. Also be tolerant about changing suffixes
        # internally. The macOS just ignores that, and so we do.
        if not os.path.exists(resolved_path):
            if os.path.basename(resolved_path) == os.path.basename(binary_filename):
                resolved_path = binary_filename
            else:
                for suffix1, suffix2 in (
                    (".dylib", ".dylib"),
                    (".so", ".so"),
                    (".dylib", ".so"),
                    (".so", ".dylib"),
                ):
                    pattern = r"^(.*?)(\.\d+)*%s$" % re.escape(suffix1)

                    match = re.match(pattern, resolved_path)

                    if match:
                        candidate = match.group(1) + suffix2

                        if os.path.exists(candidate):
                            resolved_path = candidate
                        else:
                            candidate = os.path.join(
                                original_dir, os.path.basename(candidate)
                            )

                            if os.path.exists(candidate):
                                resolved_path = candidate
                            elif os.path.basename(candidate) == os.path.basename(
                                binary_filename
                            ):
                                # Versioned dependency on itself in non-existent path.
                                resolved_path = binary_filename

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

            # We check both the user and the used DLL if they are listed. This
            # might be a form of bug hiding, that the later is not sufficient,
            # that we should address later.
            acceptable, plugin_name = Plugins.isAcceptableMissingDLL(
                package_name=package_name,
                filename=resolved_path,
            )

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
    stdout = getOtoolListing(filename=binary_filename, cached=True)

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
                    % (getReportPath(original_location), rpath_filename)
                )

            mapping.append((rpath_filename, "@executable_path/" + dist_path))

        if mapping or had_self:
            callInstallNameTool(
                filename=binary_filename,
                mapping=mapping,
                id_path=os.path.basename(binary_filename) if had_self else None,
                rpath=None,
            )


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
