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
""" Included entry points for standalone mode.

This keeps track of entry points for standalone. These should be extension
modules, added by core code, the main binary, added by core code, and from
plugins in their getExtraDlls implementation, where they provide DLLs to be
added, and whose dependencies will also be included.
"""

import collections
import fnmatch
import os

from nuitka.Options import getShallNotIncludeDllFilePatterns, isShowInclusion
from nuitka.Tracing import general, inclusion_logger
from nuitka.utils.FileOperations import (
    areSamePaths,
    getReportPath,
    hasFilenameExtension,
    haveSameFileContents,
    isRelativePath,
)
from nuitka.utils.Importing import getSharedLibrarySuffix
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import getDLLVersion

IncludedEntryPoint = collections.namedtuple(
    "IncludedEntryPoint",
    (
        "logger",
        "kind",
        "source_path",
        "dest_path",
        "package_name",
        "executable",
        "reason",
    ),
)


# Since inheritance is not a thing with namedtuple, have factory functions
def _makeIncludedEntryPoint(
    logger, kind, source_path, dest_path, package_name, reason, executable
):
    if package_name is not None:
        package_name = ModuleName(package_name)

    assert type(executable) is bool, executable

    # Make sure outside code uses sane paths only.
    assert source_path == os.path.normpath(source_path), source_path

    # Avoid obvious mistakes, these files won't be binaries or DLL ever, right?
    assert not hasFilenameExtension(path=source_path, extensions=(".qml", ".json"))

    return IncludedEntryPoint(
        logger,
        kind,
        source_path,
        os.path.normpath(dest_path),
        package_name,
        executable,
        reason,
    )


def _makeDllOrExeEntryPoint(
    logger, kind, source_path, dest_path, package_name, reason, executable
):
    assert type(dest_path) not in (tuple, list)
    assert type(source_path) not in (tuple, list)
    assert isRelativePath(dest_path), dest_path
    assert ".dist" not in dest_path, dest_path

    if not os.path.isfile(source_path):
        logger.sysexit(
            "Error, attempting to include file '%s' (%s) that does not exist."
            % (getReportPath(source_path), reason)
        )

    return _makeIncludedEntryPoint(
        logger=logger,
        kind=kind,
        source_path=source_path,
        dest_path=dest_path,
        package_name=package_name,
        reason=reason,
        executable=executable,
    )


def makeExtensionModuleEntryPoint(logger, source_path, dest_path, package_name, reason):
    return _makeDllOrExeEntryPoint(
        logger=logger,
        kind="extension",
        source_path=source_path,
        dest_path=dest_path,
        package_name=package_name,
        reason=reason,
        executable=False,
    )


def makeDllEntryPoint(logger, source_path, dest_path, package_name, reason):
    return _makeDllOrExeEntryPoint(
        logger=logger,
        kind="dll",
        source_path=source_path,
        dest_path=dest_path,
        package_name=package_name,
        reason=reason,
        executable=False,
    )


def makeExeEntryPoint(logger, source_path, dest_path, package_name, reason):
    return _makeDllOrExeEntryPoint(
        logger=logger,
        kind="exe",
        source_path=source_path,
        dest_path=dest_path,
        package_name=package_name,
        reason=reason,
        executable=True,
    )


def makeMainExecutableEntryPoint(dest_path):
    return _makeDllOrExeEntryPoint(
        logger=general,
        kind="executable",
        source_path=dest_path,
        dest_path=os.path.basename(dest_path),
        package_name=None,
        reason="main binary",
        executable=True,
    )


def _makeIgnoredEntryPoint(entry_point):
    return _makeDllOrExeEntryPoint(
        logger=entry_point.logger,
        kind=entry_point.kind + "_ignored",
        source_path=entry_point.source_path,
        dest_path=entry_point.dest_path,
        package_name=entry_point.package_name,
        reason=entry_point.reason,
        executable=entry_point.executable,
    )


standalone_entry_points = []


def _warnNonIdenticalEntryPoints(entry_point1, entry_point2):
    inclusion_logger.warning(
        """\
Ignoring non-identical DLLs for '%s', '%s' different from '%s'. Using first one and hoping for the best."""
        % (entry_point1.dest_path, entry_point1.source_path, entry_point2.source_path)
    )


def addIncludedEntryPoint(entry_point):
    # Checking here if user or DLL version conflicts require it to be ignored,
    # which has a couple of decisions to make, pylint: disable=too-many-branches

    for count, standalone_entry_point in enumerate(standalone_entry_points):
        if standalone_entry_point.kind.endswith("_ignored"):
            continue

        if areSamePaths(entry_point.dest_path, standalone_entry_point.dest_path):
            if areSamePaths(
                entry_point.source_path, standalone_entry_point.source_path
            ):
                return

            if isShowInclusion():
                inclusion_logger.info(
                    """Colliding DLL names for %s, checking identity of \
'%s' <-> '%s'."""
                    % (
                        entry_point.dest_path,
                        entry_point.source_path,
                        standalone_entry_point.source_path,
                    )
                )

            # Check that if a DLL has the same name, if it's identical, then it's easy, we just
            # want to remember, therefore we convert to an ignored type.
            if haveSameFileContents(
                entry_point.source_path, standalone_entry_point.source_path
            ):
                entry_point = _makeIgnoredEntryPoint(entry_point)
                break

            # For Win32 and macOS, we can check out file versions.
            old_dll_version = getDLLVersion(standalone_entry_point.source_path)
            new_dll_version = getDLLVersion(entry_point.source_path)

            # No version information for both, warn and ignore the new one.
            if old_dll_version is None and new_dll_version is None:
                _warnNonIdenticalEntryPoints(standalone_entry_point, entry_point)

                entry_point = _makeIgnoredEntryPoint(entry_point)
                break

            # The newly found one has version information, ignore old one
            if old_dll_version is None and new_dll_version is not None:
                standalone_entry_points[count] = _makeIgnoredEntryPoint(
                    standalone_entry_point
                )
                break

            # The old one has version information, but the new one does not, ignore new one
            if old_dll_version is not None and new_dll_version is None:
                entry_point = _makeIgnoredEntryPoint(entry_point)
                break

            # The old one has lower version, ignore it.s
            if old_dll_version < new_dll_version:
                standalone_entry_points[count] = _makeIgnoredEntryPoint(
                    standalone_entry_point
                )
                break

            # The old one has same or higher version, prefer it.
            if old_dll_version >= new_dll_version:
                entry_point = _makeIgnoredEntryPoint(entry_point)
                break

            # Ought to be impossible to get here.
            assert False, (old_dll_version, new_dll_version)

    if not entry_point.kind.endswith("_ignored"):
        for noinclude_dll_pattern in getShallNotIncludeDllFilePatterns():
            if fnmatch.fnmatch(entry_point.dest_path, noinclude_dll_pattern):
                entry_point = _makeIgnoredEntryPoint(entry_point)

    standalone_entry_points.append(entry_point)


def addIncludedEntryPoints(entry_points):
    for entry_point in entry_points:
        addIncludedEntryPoint(entry_point)


def setMainEntryPoint(binary_filename):
    entry_point = makeMainExecutableEntryPoint(binary_filename)

    standalone_entry_points.insert(0, entry_point)


def addExtensionModuleEntryPoint(module):
    standalone_entry_points.append(
        makeExtensionModuleEntryPoint(
            logger=general,
            source_path=module.getFilename(),
            dest_path=module.getFullName().asPath()
            + getSharedLibrarySuffix(preferred=False),
            package_name=module.getFullName().getPackageName(),
            # TODO: Which module(s) us it?
            reason="used extension module",
        )
    )


def getStandaloneEntryPoints():
    return tuple(standalone_entry_points)
