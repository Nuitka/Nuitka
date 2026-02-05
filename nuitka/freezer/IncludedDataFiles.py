#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Included data files for standalone mode.

This keeps track of data files for standalone mode. Do not should them for
DLLs or extension modules, these need to be seen by Nuitka as entry points
for dependency analysis.
"""

import fnmatch
import os

from nuitka import ModuleRegistry
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import locateModule
from nuitka.options.Options import (
    getOutputPath,
    getShallIncludeDataDirs,
    getShallIncludeDataFiles,
    getShallIncludeExternallyDataFilePatterns,
    getShallIncludePackageData,
    getShallIncludeRawDirs,
    getShallNotIncludeDataFilePatterns,
    isAcceleratedMode,
    isStandaloneMode,
    shallMakeModule,
)
from nuitka.OutputDirectories import getStandaloneDirectoryPath
from nuitka.plugins.Hooks import considerDataFiles, onDataFileTags
from nuitka.PythonFlavors import getSystemPrefixPath
from nuitka.PythonVersions import (
    getSitePackageCandidateNames,
    python_version_str,
)
from nuitka.Tracing import general, inclusion_logger, options_logger
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    areSamePaths,
    containsPathElements,
    copyFileWithPermissions,
    getFileContents,
    getFileList,
    getFilenameExtension,
    getFileSize,
    getNormalizedPath,
    isFilenameBelowPath,
    isLegalPath,
    isRelativePath,
    makePath,
    openTextFile,
    relpath,
    resolveShellPatternToFilenames,
)
from nuitka.utils.Importing import getExtensionModuleSuffixes
from nuitka.utils.Utils import getArchitecture, isAIX, isMacOS

data_file_tags = []


def addDataFileTags(pattern):
    """Add a data file tag pattern.

    Args:
        pattern: The pattern and tags in "pattern:tags" format.
    """
    assert ":" in pattern, pattern
    data_file_tags.append(pattern)


def getDataFileTags(dest_path):
    """Get the data file tags for a specific destination path.

    Args:
        dest_path: The destination path to check.

    Returns:
        OrderedSet of tags applicable to the path.
    """
    result = OrderedSet()

    for value in data_file_tags:
        pattern, tags = value.rsplit(":", 1)

        if fnmatch.fnmatch(dest_path, pattern):
            result.update(tags.split(","))

    return result


def hasDataFileTag(tag):
    """Check if a specific tag exists in any registered patterns.

    Args:
        tag: The tag to search for.

    Returns:
        bool: True if the tag is found, False otherwise.
    """
    for value in data_file_tags:
        _pattern, tags = value.rsplit(":", 1)

        if tag in tags:
            return True


def decodeDataFileTags(tags):
    """Convert tags argument to an OrderedSet.

    Notes:
        In many places, strings are accepted for tags, convert to OrderedSet
        for internal use.

    Args:
        tags: string (comma separated) or iterable of tags.

    Returns:
        OrderedSet of tags.
    """

    if type(tags) is str:
        tags = tags.split(",") if tags else ()

    return OrderedSet(tags)


class IncludedDataFile(object):
    """Details of an included data file.

    Notes:
        This class holds all information about a data file to be included in
        the standalone distribution.

    Args:
        kind: The kind of data file ("data_file" or "data_blob").
        source_path: The source path of the file (if kind is "data_file").
        dest_path: The destination path in the distribution.
        reason: The reason for inclusion.
        data: The binary data (if kind is "data_blob").
        tags: Tags associated with this file.
        tracer: The tracer to use for logging.
    """

    __slots__ = ("kind", "source_path", "dest_path", "reason", "data", "tags", "tracer")

    def __init__(self, kind, source_path, dest_path, reason, data, tags, tracer):
        tags_set = getDataFileTags(dest_path)

        current = dest_path
        while True:
            current = os.path.dirname(current)
            if not current:
                break

            tags_set.update(getDataFileTags(current))

        tags_set.update(decodeDataFileTags(tags))

        # Copy, unless specified otherwise.
        if not any(tag.startswith("embed-") for tag in tags_set):
            tags_set.add("copy")

        self.kind = kind
        self.source_path = source_path
        self.dest_path = getNormalizedPath(dest_path)

        is_legal, illegal_reason = isLegalPath(self.dest_path)
        if not is_legal:
            general.sysexit(
                "Error, cannot add data file with '%s' path, as '%s'"
                % (dest_path, illegal_reason)
            )

        self.reason = reason
        self.data = data
        self.tags = tags_set
        self.tracer = tracer

    def __repr__(self):
        return "<%s %s source '%s' dest '%s' reason '%s' tags '%s'>" % (
            self.__class__.__name__,
            self.kind,
            self.source_path,
            self.dest_path,
            self.reason,
            ",".join(self.tags),
        )

    def needsCopy(self):
        """Check if the file needs to be copied.

        Returns:
            bool: True if the file should be copied, False otherwise.
        """
        return "copy" in self.tags

    def getFileContents(self):
        """Get the contents of the data file.

        Returns:
            bytes: The content of the file.
        """
        if self.kind == "data_file":
            return getFileContents(filename=self.source_path, mode="rb")
        elif self.kind == "data_blob":
            return self.data
        else:
            assert False

    def getFileSize(self):
        """Get the size of the data file.

        Returns:
            int: The size of the file in bytes.
        """
        if self.kind == "data_file":
            return getFileSize(self.source_path)
        elif self.kind == "data_blob":
            return len(self.data)
        else:
            assert False


def makeIncludedEmptyDirectory(dest_path, reason, tracer, tags):
    """Create an included data file representing an empty directory.

    Args:
        dest_path: The destination path for the directory.
        reason: The reason for inclusion.
        tracer: The tracer to use for logging.
        tags: Tags associated with this directory.

    Returns:
        IncludedDataFile: The created data file object (using a marker file).
    """
    dest_path = os.path.join(dest_path, ".keep_dir.txt")

    return makeIncludedGeneratedDataFile(
        data="", dest_path=dest_path, reason=reason, tracer=tracer, tags=tags
    )


def makeIncludedDataFile(source_path, dest_path, reason, tracer, tags):
    """Create an included data file.

    Args:
        source_path: The source path of the file.
        dest_path: The destination path in the distribution.
        reason: The reason for inclusion.
        tracer: The tracer to use for logging.
        tags: Tags associated with this file.

    Returns:
        IncludedDataFile: The created data file object.
    """
    tags = decodeDataFileTags(tags)

    # Refuse directories, these must be kept distinct.
    if os.path.isdir(source_path):
        tracer.sysexit(
            "Error, cannot include directory '%s' as a data file. Data directories have their own options."
            % source_path
        )

    # In accelerated mode, data files can be everywhere, but they cannot
    # change place.
    if isAcceleratedMode():
        if "copy" in tags:
            if "package_data" not in tags and not areSamePaths(source_path, dest_path):
                tracer.sysexit(
                    "Error, cannot change paths for data files in accelerated mode from '%s' to '%s'."
                    % (source_path, dest_path)
                )
    else:
        if not isRelativePath(dest_path):
            tracer.sysexit(
                "Error, cannot use dest path '%s' outside of distribution." % dest_path
            )

    return IncludedDataFile(
        kind="data_file",
        source_path=source_path,
        dest_path=dest_path,
        data=None,
        reason=reason,
        tracer=tracer,
        tags=tags,
    )


# By default ignore all things that are code.
default_ignored_suffixes = (
    ".py",
    ".pyw",
    ".pyc",
    ".pyo",
    ".pyi",
    ".so",
    ".pyd",
    ".pyx",
    ".dll",
    ".dylib",
    ".exe",
    ".bin",
)

default_ignored_suffixes += getExtensionModuleSuffixes()

default_ignored_dirs = ("__pycache__",) + getSitePackageCandidateNames()

default_ignored_filenames = ("py.typed",)
if not isMacOS():
    default_ignored_filenames += (".DS_Store",)


def makeIncludedDataDirectory(
    source_path,
    dest_path,
    reason,
    tracer,
    tags,
    ignore_dirs=(),
    ignore_filenames=(),
    ignore_suffixes=(),
    only_suffixes=(),
    normalize=True,
    raw=False,
):
    """Create included data files from a directory.

    Args:
        source_path: The source directory path.
        dest_path: The destination path in the distribution.
        reason: The reason for inclusion.
        tracer: The tracer to use for logging.
        tags: Tags associated with these files.
        ignore_dirs: Directories to ignore.
        ignore_filenames: Filenames to ignore.
        ignore_suffixes: File suffixes to ignore.
        only_suffixes: Only include files with these suffixes.
        normalize: Whether to normalize paths.
        raw: Whether to include raw directory contents (ignores defaults).

    Yields:
        IncludedDataFile: Included data file objects found in the directory.
    """
    assert isRelativePath(dest_path), dest_path
    assert os.path.isdir(source_path), source_path

    ignore_dirs = tuple(ignore_dirs)
    if not raw:
        ignore_dirs += default_ignored_dirs

    ignore_filenames = tuple(ignore_filenames)
    if not raw:
        ignore_filenames += default_ignored_filenames

    ignore_suffixes = tuple(ignore_suffixes)
    if not raw:
        ignore_suffixes += default_ignored_suffixes

    for filename in getFileList(
        source_path,
        ignore_dirs=ignore_dirs,
        ignore_filenames=ignore_filenames,
        ignore_suffixes=ignore_suffixes,
        only_suffixes=only_suffixes,
        normalize=normalize,
    ):
        filename_relative = os.path.relpath(filename, source_path)

        filename_dest = os.path.join(dest_path, filename_relative)

        included_datafile = makeIncludedDataFile(
            source_path=filename,
            dest_path=filename_dest,
            reason=reason,
            tracer=tracer,
            tags=tags,
        )

        included_datafile.tags.add("raw-dir-contents" if raw else "data-dir-contents")

        yield included_datafile


def makeIncludedGeneratedDataFile(data, dest_path, reason, tracer, tags):
    """Create an included data file from generated data.

    Args:
        data: The binary data content.
        dest_path: The destination path in the distribution.
        reason: The reason for inclusion.
        tracer: The tracer to use for logging.
        tags: Tags associated with this file.

    Returns:
        IncludedDataFile: The created data file object.
    """
    assert isRelativePath(dest_path), dest_path

    if type(data) is str and str is not bytes:
        data = data.encode("utf8")

    assert type(data) is bytes, type(data)

    return IncludedDataFile(
        kind="data_blob",
        source_path=None,
        dest_path=dest_path,
        reason=reason,
        data=data,
        tracer=tracer,
        tags=tags,
    )


_included_data_files = []


def addIncludedDataFile(included_datafile):
    """Add a data file to the included list.

    Args:
        included_datafile: The IncludedDataFile object to add.
    """
    included_datafile.tags.update(getDataFileTags(included_datafile.dest_path))

    for external_datafile_pattern in getShallNotIncludeDataFilePatterns():
        if fnmatch.fnmatch(
            included_datafile.dest_path, external_datafile_pattern
        ) or isFilenameBelowPath(
            path=external_datafile_pattern, filename=included_datafile.dest_path
        ):
            included_datafile.tags.clear()
            included_datafile.tags.add("inhibit")

            return

    onDataFileTags(included_datafile)

    # TODO: Catch duplicates sooner.
    # for candidate in _included_data_files:
    #     if candidate.dest_path == included_datafile.dest_path:
    #         assert False, included_datafile

    if included_datafile.needsCopy():
        for external_datafile_pattern in getShallIncludeExternallyDataFilePatterns():
            if fnmatch.fnmatch(
                included_datafile.dest_path, external_datafile_pattern
            ) or isFilenameBelowPath(
                path=external_datafile_pattern, filename=included_datafile.dest_path
            ):
                included_datafile.tags.add("external")

                dest_path = getOutputPath(included_datafile.dest_path)

                if areSamePaths(dest_path, included_datafile.source_path):
                    inclusion_logger.sysexit(
                        """\
Error, when asking to copy files external data, you cannot output to\
same directory and need to use '--output-dir' option."""
                    )

    _included_data_files.append(included_datafile)


def getIncludedDataFiles():
    """Get all included data files.

    Returns:
        list: List of IncludedDataFile objects.
    """
    return _included_data_files


def _addIncludedDataFilesFromFileOptions():
    # Many different option variants, pylint: disable=too-many-branches

    for pattern, source_path, dest_path, arg in getShallIncludeDataFiles():
        filenames = resolveShellPatternToFilenames(pattern)

        count = 0
        for filename in filenames:
            file_reason = "specified data file '%s' on command line" % arg

            if source_path is None:
                rel_path = dest_path

                if rel_path.endswith(("/", os.path.sep)):
                    rel_path = os.path.join(rel_path, os.path.basename(filename))
            else:
                rel_path = os.path.join(dest_path, relpath(filename, source_path))

            rel_path = os.path.normpath(rel_path)

            if containsPathElements(rel_path, default_ignored_dirs):
                continue

            if os.path.basename(rel_path) in default_ignored_filenames:
                continue

            yield makeIncludedDataFile(
                filename, rel_path, file_reason, tracer=options_logger, tags="user"
            )

            count += 1

        if count == 0:
            options_logger.warning(
                "No matching data file to be included for '%s'." % pattern
            )

    for source_path, dest_path in getShallIncludeDataDirs():
        count = 0

        for included_datafile in makeIncludedDataDirectory(
            source_path=source_path,
            dest_path=os.path.normpath(dest_path),
            reason="specified data dir '%s' on command line" % source_path,
            tracer=options_logger,
            tags="user",
        ):
            yield included_datafile

            count += 1

        if count == 0:
            options_logger.warning("No data files in directory '%s'." % source_path)

    for source_path, dest_path in getShallIncludeRawDirs():
        count = 0

        for included_datafile in makeIncludedDataDirectory(
            source_path=source_path,
            dest_path=os.path.normpath(dest_path),
            reason="specified raw dir '%s' on command line" % source_path,
            tracer=options_logger,
            tags="user",
            raw=True,
        ):
            yield included_datafile

            count += 1

        if count == 0:
            options_logger.warning("No files in raw directory '%s.'" % source_path)


def addIncludedDataFilesFromFlavor():
    """Add data files required by the Python flavor/OS.

    Notes:
        Example: AIX requires libpython embedded.
    """
    if isAIX():
        # On AIX, the Python DLL is hidden in an archive.
        filename = "libpython%s.a" % python_version_str
        system_prefix = getSystemPrefixPath()

        if getArchitecture() == "64":
            lib_part = "lib64"
        else:
            return inclusion_logger.sysexit(
                """\
Error, change Nuitka code to define the path of the '%s' \
file in the Python installation '%s'."""
                % (filename, system_prefix)
            )

        filename_full = os.path.join(system_prefix, lib_part, filename)

        if not os.path.exists(filename_full):
            return inclusion_logger.sysexit(
                "Error, the defined path of the '%s' file in the Python installation '%s' is wrong."
                % (filename_full, system_prefix)
            )

        addIncludedDataFile(
            makeIncludedDataFile(
                source_path=filename_full,
                dest_path=filename,
                reason="Required Python DLL",
                tracer=inclusion_logger,
                tags="flavor",
            )
        )


def addIncludedDataFilesFromFileOptions():
    """Early data files, from user options that work with file system.

    Notes:
        These are processed early as they come from direct file/directory
        arguments.
    """

    for included_datafile in _addIncludedDataFilesFromFileOptions():
        addIncludedDataFile(included_datafile)


def scanIncludedPackageDataFiles(package_directory, pattern):
    """Scan a package directory for data files matching a pattern.

    Args:
        package_directory: The directory of the package to scan.
        pattern: The filename pattern to match.

    Returns:
        list: List of matching filenames.
    """
    ignore_suffixes = default_ignored_suffixes

    if pattern is not None:
        pattern_extension = getFilenameExtension(pattern)

        ignore_suffixes = tuple(
            ignore_suffix
            for ignore_suffix in ignore_suffixes
            if ignore_suffix != pattern_extension
        )

    result = []

    for pkg_filename in getFileList(
        package_directory,
        ignore_dirs=default_ignored_dirs,
        ignore_suffixes=ignore_suffixes,
        ignore_filenames=default_ignored_filenames,
    ):
        rel_path = os.path.relpath(pkg_filename, package_directory)

        if pattern and not fnmatch.fnmatch(rel_path, pattern):
            continue

        result.append(pkg_filename)

    return result


def makeIncludedPackageDataFiles(
    tracer, package_name, package_directory, pattern, reason, tags
):
    """Create included data files for a package.

    Args:
        tracer: The tracer to use for logging.
        package_name: The name of the package.
        package_directory: The directory of the package.
        pattern: The filename pattern to search for.
        reason: The reason for inclusion.
        tags: Tags associated with these files.

    Yields:
        IncludedDataFile: Included data file objects found.
    """
    tags = decodeDataFileTags(tags)
    tags.add("package_data")

    file_reason = "package '%s' %s" % (package_name, reason)

    for pkg_filename in scanIncludedPackageDataFiles(package_directory, pattern):
        rel_path = os.path.relpath(pkg_filename, package_directory)

        yield makeIncludedDataFile(
            source_path=pkg_filename,
            dest_path=os.path.join(package_name.asPath(), rel_path),
            reason=file_reason,
            tracer=tracer,
            tags=tags,
        )


def addIncludedDataFilesFromPlugins():
    """Add included data files from plugins.

    Notes:
        Plugins can yield included data files via the considerDataFiles hook.
    """
    # Plugins provide per module through this.
    for module in ModuleRegistry.getDoneModules():
        for included_datafile in considerDataFiles(module=module):
            addIncludedDataFile(included_datafile)


def addIncludedDataFilesFromPackageOptions():
    """Late data files, from plugins and user options that work with packages.

    Notes:
        These are processed after modules are located.
    """

    for package_name, filename_pattern in getShallIncludePackageData():
        package_name, package_directory, _module_kind, _finding = locateModule(
            module_name=package_name,
            parent_package=None,
            level=0,
        )

        if package_directory is None:
            options_logger.warning(
                "Failed to locate package directory of '%s'." % package_name.asString()
            )
            continue

        if os.path.isfile(package_directory):
            options_logger.sysexit(
                "Error, '%s' is a module not a package, cannot have package data."
                % package_name
            )

        # TODO: Maybe warn about packages that have no data files found.

        for included_datafile in makeIncludedPackageDataFiles(
            tracer=options_logger,
            package_name=package_name,
            package_directory=package_directory,
            pattern=filename_pattern,
            reason="package data",
            tags="user",
        ):
            addIncludedDataFile(included_datafile)


_data_file_traces = OrderedDict()


def _reportDataFiles():
    """Report (log) the included data files summary."""
    for key in _data_file_traces:
        count = len(_data_file_traces[key])
        tracer, reason = key

        # Avoid being too noisy, maybe add a control for increasing this.
        if count > 10:
            tracer.info("Included %d data files due to %s." % (count, reason))
        else:
            for kind, dest_path in _data_file_traces[key]:
                if kind == "data_blob":
                    tracer.info(
                        "Included data file '%s' due to %s."
                        % (
                            dest_path,
                            reason,
                        )
                    )
                elif kind == "data_file":
                    tracer.info(
                        "Included data file '%s' due to %s."
                        % (
                            dest_path,
                            reason,
                        )
                    )
                else:
                    assert False

    # Release the memory
    _data_file_traces.clear()


def _checkPathConflict(dest_path, standalone_entry_points):
    """Check for conflicts with standalone entry points.

    Args:
        dest_path: The destination path to check.
        standalone_entry_points: List of standalone entry points.
    """
    assert getNormalizedPath(dest_path) == dest_path

    while dest_path:
        for standalone_entry_point in standalone_entry_points:
            if dest_path == standalone_entry_point.dest_path:
                options_logger.sysexit(
                    """\
Error, data file to be placed in distribution as '%s' conflicts with %s '%s'."""
                    % (
                        dest_path,
                        standalone_entry_point.kind,
                        standalone_entry_point.dest_path,
                    )
                )
        dest_path = os.path.dirname(dest_path)


def _handleDataFile(included_datafile, standalone_entry_points):
    """Handle a single data file, writing or copying it.

    Args:
        included_datafile: The IncludedDataFile object.
        standalone_entry_points: List of standalone entry points to check conflicts against.

    Returns:
        tuple: (external, dest_path) where external is bool.
    """
    tracer = included_datafile.tracer

    if not isinstance(included_datafile, IncludedDataFile):
        tracer.sysexit("Error, can only accept 'IncludedData*' objects from ")

    if not isStandaloneMode():
        tracer.sysexit(
            "Error, package data files are only included in standalone or onefile mode."
        )

    key = tracer, included_datafile.reason
    if key not in _data_file_traces:
        _data_file_traces[key] = []

    _data_file_traces[key].append((included_datafile.kind, included_datafile.dest_path))

    dist_dir = getStandaloneDirectoryPath(bundle=True, real=False)

    if "external" in included_datafile.tags:
        dest_path = getOutputPath(included_datafile.dest_path)
        external = True
    else:
        _checkPathConflict(included_datafile.dest_path, standalone_entry_points)
        dest_path = os.path.join(dist_dir, included_datafile.dest_path)
        external = False

    if included_datafile.kind == "data_blob":
        makePath(os.path.dirname(dest_path))

        with openTextFile(filename=dest_path, mode="wb") as output_file:
            output_file.write(included_datafile.data)

        if "script" in included_datafile.tags:
            addFileExecutablePermission(dest_path)

    elif included_datafile.kind == "data_file":
        makePath(os.path.dirname(dest_path))

        copyFileWithPermissions(
            source_path=included_datafile.source_path,
            dest_path=dest_path,
            target_dir=dist_dir,
        )
    else:
        assert False, included_datafile

    return external, dest_path


def copyDataFiles(standalone_entry_points):
    """Copy the data files needed for standalone distribution.

    Notes:
        This is for data files only, not DLLs or even extension modules,
        those must be registered as entry points, and would not go through
        necessary handling if provided like this.

    Args:
        standalone_entry_points: List of standalone entry points available.

    Returns:
        list: List of paths to the copied data files.
    """

    data_file_paths = []

    for included_datafile in getIncludedDataFiles():
        # TODO: directories should be resolved to files.
        if included_datafile.needsCopy():
            if shallMakeModule():
                options_logger.sysexit(
                    """\
Error, data files for modules must be done via wheels, or commercial plugins \
'--embed-*' options. Not done for '%s'."""
                    % included_datafile.dest_path
                )
            elif not isStandaloneMode():
                options_logger.sysexit(
                    """\
Error, data files cannot be included in accelerated mode unless using commercial \
plugins '--embed-*' options. Not done for '%s'."""
                    % included_datafile.dest_path
                )

            external, data_file_path = _handleDataFile(
                included_datafile=included_datafile,
                standalone_entry_points=standalone_entry_points,
            )

            if not external:
                data_file_paths.append(data_file_path)

    _reportDataFiles()

    return data_file_paths


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
