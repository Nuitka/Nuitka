#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Included entry points for standalone mode.

This keeps track of entry points for standalone. These should be extension
modules, added by core code, the main binary, added by core code, and from
plugins in their getExtraDlls implementation, where they provide DLLs to be
added, and whose dependencies will also be included.
"""

import fnmatch
import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.options.Options import (
    getShallNotIncludeDllFilePatterns,
    isShowInclusion,
)
from nuitka.plugins.Hooks import onDllTags
from nuitka.Tracing import general, inclusion_logger
from nuitka.utils.FileOperations import (
    areSamePaths,
    getNormalizedPath,
    getReportPath,
    hasFilenameExtension,
    haveSameFileContents,
    isRelativePath,
)
from nuitka.utils.Importing import getExtensionModuleSuffix
from nuitka.utils.ModuleNames import ModuleName, checkModuleName
from nuitka.utils.SharedLibraries import getDLLVersion

dll_tags = []


def addDllTags(pattern):
    """Add a DLL tag pattern.

    Args:
        pattern: The pattern and tags in "pattern:tags" format.
    """
    assert ":" in pattern, pattern
    dll_tags.append(pattern)


def getDllTags(dest_path):
    """Get the DLL tags for a specific destination path.

    Args:
        dest_path: The destination path to check.

    Returns:
        OrderedSet of tags applicable to the path.
    """
    result = OrderedSet()
    result.add("copy")

    for value in dll_tags:
        pattern, tags = value.rsplit(":", 1)

        if fnmatch.fnmatch(dest_path, pattern):
            result.update(tags.split(","))

    return result


class IncludedEntryPoint(object):
    # We need all these attributes to track the entry point details.
    # pylint: disable=too-many-instance-attributes

    __slots__ = (
        "logger",
        "kind",
        "source_path",
        "dest_path",
        "module_name",
        "package_name",
        "executable",
        "reason",
        "tags",
    )

    def __init__(
        self,
        logger,
        kind,
        source_path,
        dest_path,
        module_name,
        package_name,
        executable,
        reason,
        tags,
    ):
        self.logger = logger
        self.kind = kind
        self.source_path = source_path
        self.dest_path = dest_path
        self.module_name = module_name
        self.package_name = package_name
        self.executable = executable
        self.reason = reason
        self.tags = OrderedSet(tags) if tags else OrderedSet()

        self.tags.update(getDllTags(dest_path))

    def __repr__(self):
        return """\
<IncludedEntryPoint \
kind=%s \
source_path=%s \
dest_path=%s \
module_name=%s \
package_name=%s \
executable=%s \
reason=%s \
tags=%s>""" % (
            self.kind,
            self.source_path,
            self.dest_path,
            self.module_name,
            self.package_name,
            self.executable,
            self.reason,
            self.tags,
        )


def _makeIncludedEntryPoint(
    logger,
    kind,
    source_path,
    dest_path,
    module_name,
    package_name,
    reason,
    executable,
    tags,
):
    if package_name is not None:
        package_name = ModuleName(package_name)

    assert type(executable) is bool, executable

    # Make sure outside code uses sane paths only.
    assert source_path == getNormalizedPath(source_path), source_path

    # Avoid obvious mistakes, these files won't be binaries or DLL ever, right?
    assert not hasFilenameExtension(path=source_path, extensions=(".qml", ".json"))

    return IncludedEntryPoint(
        logger=logger,
        kind=kind,
        source_path=source_path,
        dest_path=getNormalizedPath(dest_path),
        module_name=module_name,
        package_name=package_name,
        executable=executable,
        reason=reason,
        tags=tags,
    )


def _makeDllOrExeEntryPoint(
    logger,
    kind,
    source_path,
    dest_path,
    module_name,
    package_name,
    reason,
    executable,
    tags,
):
    assert type(dest_path) not in (tuple, list)
    assert type(source_path) not in (tuple, list)
    assert isRelativePath(dest_path), dest_path
    assert ".dist" not in dest_path, dest_path
    if module_name is not None:
        assert checkModuleName(module_name), module_name
        module_name = ModuleName(module_name)
    if package_name is not None:
        assert checkModuleName(package_name), package_name
        package_name = ModuleName(package_name)

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
        module_name=module_name,
        package_name=package_name,
        reason=reason,
        executable=executable,
        tags=tags,
    )


def makeExtensionModuleEntryPoint(
    logger, source_path, dest_path, module_name, package_name, reason, tags=None
):
    return _makeDllOrExeEntryPoint(
        logger=logger,
        kind="extension",
        source_path=source_path,
        dest_path=dest_path,
        module_name=module_name,
        package_name=package_name,
        reason=reason,
        executable=False,
        tags=tags,
    )


def makeDllEntryPoint(
    logger, source_path, dest_path, module_name, package_name, reason, tags=None
):
    return _makeDllOrExeEntryPoint(
        logger=logger,
        kind="dll",
        source_path=source_path,
        dest_path=dest_path,
        module_name=module_name,
        package_name=package_name,
        reason=reason,
        executable=False,
        tags=tags,
    )


def makeExeEntryPoint(
    logger, source_path, dest_path, module_name, package_name, reason, tags=None
):
    return _makeDllOrExeEntryPoint(
        logger=logger,
        kind="exe",
        source_path=source_path,
        dest_path=dest_path,
        module_name=module_name,
        package_name=package_name,
        reason=reason,
        executable=True,
        tags=tags,
    )


def makeMainExecutableEntryPoint(dest_path):
    return _makeDllOrExeEntryPoint(
        logger=general,
        kind="executable",
        source_path=dest_path,
        dest_path=os.path.basename(dest_path),
        module_name=None,
        package_name=None,
        reason="main binary",
        executable=True,
        tags=None,
    )


def _makeIgnoredEntryPoint(entry_point):
    return _makeDllOrExeEntryPoint(
        logger=entry_point.logger,
        kind=entry_point.kind + "_ignored",
        source_path=entry_point.source_path,
        dest_path=entry_point.dest_path,
        module_name=entry_point.module_name,
        package_name=entry_point.package_name,
        reason=entry_point.reason,
        executable=entry_point.executable,
        tags=entry_point.tags,
    )


standalone_entry_points = []


def _getTopLevelPackageName(package_name):
    if package_name is None:
        return None
    else:
        return package_name.getTopLevelPackageName()


def _warnNonIdenticalEntryPoints(entry_point1, entry_point2):
    # Well know cases, where they duplicate all the DLLs, seems to work well
    # enough to not report this. TODO: When we are adding to the report, it
    # ought to be still added. spell-checker: ignore scipy
    if frozenset(
        (
            _getTopLevelPackageName(entry_point1.package_name),
            _getTopLevelPackageName(entry_point2.package_name),
        )
    ) == frozenset(("numpy", "scipy")):
        return

    if frozenset(
        (
            _getTopLevelPackageName(entry_point1.package_name),
            _getTopLevelPackageName(entry_point2.package_name),
        )
    ) == frozenset(("av", "cv2")):
        return

    def _describe(entry_point):
        if entry_point.package_name:
            return "'%s' of package '%s'" % (
                entry_point.source_path,
                entry_point.package_name,
            )
        else:
            return "'%s'" % entry_point.source_path

    inclusion_logger.warning(
        """\
Ignoring non-identical DLLs for %s, %s different from %s. Using first one and hoping for the best."""
        % (entry_point1.dest_path, _describe(entry_point1), _describe(entry_point2))
    )


def addIncludedEntryPoint(entry_point):
    # Checking here if user or DLL version conflicts require it to be ignored,
    # which has a couple of decisions to make, pylint: disable=too-many-branches

    # Allow configured tags to be applied to it
    entry_point.tags.update(getDllTags(entry_point.dest_path))

    # Allow plugins to tag it
    onDllTags(entry_point)

    for count, standalone_entry_point in enumerate(standalone_entry_points):
        if standalone_entry_point.kind.endswith("_ignored"):
            continue

        if areSamePaths(entry_point.dest_path, standalone_entry_point.dest_path):
            if areSamePaths(
                entry_point.source_path, standalone_entry_point.source_path
            ):
                if (
                    standalone_entry_point.kind == "extension"
                    and entry_point.kind == "dll"
                ):
                    entry_point = _makeIgnoredEntryPoint(entry_point)
                    break

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


def addMainEntryPoint(binary_filename):
    entry_point = makeMainExecutableEntryPoint(binary_filename)

    standalone_entry_points.insert(0, entry_point)

    return entry_point


def addExtensionModuleEntryPoint(module):
    dest_path = module.getFullName().asPath()

    if module.isExtensionModulePackage():
        dest_path = os.path.join(dest_path, "__init__")

    dest_path += getExtensionModuleSuffix(preferred=False)

    entry_point = makeExtensionModuleEntryPoint(
        logger=general,
        source_path=module.getFilename(),
        dest_path=dest_path,
        module_name=module.getFullName(),
        package_name=module.getFullName().getPackageName(),
        reason=(
            "required extension module for CPython library startup"
            if module.isTechnical()
            else "used extension module"
        ),
    )

    onDllTags(entry_point)

    standalone_entry_points.append(entry_point)


def getIncludedExtensionModule(source_path):
    for standalone_entry_point in standalone_entry_points:
        if standalone_entry_point.kind == "extension":
            if source_path == standalone_entry_point.source_path:
                return standalone_entry_point

    for standalone_entry_point in standalone_entry_points:
        if standalone_entry_point.kind == "extension":
            if areSamePaths(source_path, standalone_entry_point.source_path):
                return standalone_entry_point

    return None


def getStandaloneEntryPoints():
    return tuple(standalone_entry_points)


def getStandaloneEntryPointForSourceFile(source_path, package_name):
    for standalone_entry_point in standalone_entry_points:
        if standalone_entry_point.package_name == package_name and areSamePaths(
            standalone_entry_point.source_path, source_path
        ):
            return standalone_entry_point


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
