#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Included data files for standalone mode.

This keeps track of data files for standalone mode. Do not should them for
DLLs or extension modules, these need to be seen by Nuitka as entry points
for dependency analysis.
"""

import fnmatch
import os

from nuitka.containers.odict import OrderedDict
from nuitka.containers.oset import OrderedSet
from nuitka.Options import (
    getShallIncludeDataDirs,
    getShallIncludeDataFiles,
    getShallIncludePackageData,
    getShallNotIncludeDataFilePatterns,
    isStandaloneMode,
    shallMakeModule,
)
from nuitka.OutputDirectories import getStandaloneDirectoryPath
from nuitka.Tracing import options_logger
from nuitka.utils.FileOperations import (
    copyFileWithPermissions,
    getFileContents,
    getFileList,
    isRelativePath,
    makePath,
    putTextFileContents,
    relpath,
    resolveShellPatternToFilenames,
)
from nuitka.utils.Importing import getSharedLibrarySuffixes

data_file_tags = []


def addDataFileTags(pattern):
    data_file_tags.append(pattern)


def getDataFileTags(dest_path):
    result = OrderedSet()

    for value in data_file_tags:
        pattern, tags = value.rsplit(":", 1)

        if fnmatch.fnmatch(dest_path, pattern):
            result.update(tags.split(","))

    return result


def _decodeTags(tags):
    if type(tags) is str:
        tags = tags.split(",") if tags else ()

    return OrderedSet(tags)


class IncludedDataFile(object):
    __slots__ = ("kind", "source_path", "dest_path", "reason", "data", "tags", "tracer")

    def __init__(self, kind, source_path, dest_path, reason, data, tags, tracer):
        tags_set = getDataFileTags(dest_path)
        tags_set.update(_decodeTags(tags))

        # Copy, unless specified otherwise.
        if not any(tag.startswith("embed-") for tag in tags_set):
            tags_set.add("copy")

        self.kind = kind
        self.source_path = source_path
        self.dest_path = dest_path
        self.reason = reason
        self.data = data
        self.tags = tags_set
        self.tracer = tracer

    def needsCopy(self):
        return "copy" in self.tags

    def getFileContents(self):
        if self.kind == "data_file":
            return getFileContents(filename=self.source_path, mode="rb")
        elif self.kind == "data_blob":
            return self.data
        else:
            assert False


def makeIncludedEmptyDirectories(source_path, dest_paths, reason, tracer, tags):
    for dest_path in dest_paths:
        assert not os.path.isabs(dest_path)

    # Require that to not be empty.
    assert dest_paths

    return IncludedDataFile(
        kind="empty_dirs",
        source_path=source_path,
        dest_path=dest_paths,
        data=None,
        reason=reason,
        tracer=tracer,
        tags=tags,
    )


def makeIncludedDataFile(source_path, dest_path, reason, tracer, tags):
    assert isRelativePath(dest_path), dest_path

    return IncludedDataFile(
        kind="data_file",
        source_path=source_path,
        dest_path=dest_path,
        data=None,
        reason=reason,
        tracer=tracer,
        tags=tags,
    )


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
):
    assert isRelativePath(dest_path), dest_path
    assert os.path.isdir(source_path), source_path

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

        included_datafile.tags.add("data_dir_content")

        yield included_datafile


def makeIncludedGeneratedDataFile(data, dest_path, reason, tracer, tags):
    assert isRelativePath(dest_path), dest_path

    return IncludedDataFile(
        kind="data_blob",
        source_path=None,
        dest_path=dest_path,
        reason=reason,
        data=data,
        tracer=tracer,
        tags=tags,
    )


included_datafiles = []


def addIncludedDataFile(included_datafile):
    included_datafile.tags.update(getDataFileTags(included_datafile.dest_path))

    included_datafiles.append(included_datafile)


def getIncludedDataFiles():
    return included_datafiles


def _addIncludedDataFilesFromFileOptions():
    for pattern, src, dest, arg in getShallIncludeDataFiles():
        filenames = resolveShellPatternToFilenames(pattern)

        if not filenames:
            options_logger.warning(
                "No matching data file to be included for '%s'." % pattern
            )

        for filename in filenames:
            file_reason = "specified data file '%s' on command line" % arg

            if src is None:
                rel_path = dest

                if rel_path.endswith(("/", os.path.sep)):
                    rel_path = os.path.join(rel_path, os.path.basename(filename))
            else:
                rel_path = os.path.join(dest, relpath(filename, src))

            yield makeIncludedDataFile(
                filename, rel_path, file_reason, tracer=options_logger, tags="user"
            )

    for src, dest in getShallIncludeDataDirs():
        filenames = getFileList(src)

        if not filenames:
            options_logger.warning("No files in directory '%s.'" % src)

        for filename in filenames:
            relative_filename = relpath(filename, src)

            file_reason = "specified data dir %r on command line" % src

            rel_path = os.path.join(dest, relative_filename)

            yield makeIncludedDataFile(
                filename, rel_path, file_reason, tracer=options_logger, tags="user"
            )


def addIncludedDataFilesFromFileOptions():
    """Early data files, from user options that work with file system."""

    for included_datafile in _addIncludedDataFilesFromFileOptions():
        addIncludedDataFile(included_datafile)


def makeIncludedPackageDataFiles(
    tracer, package_name, package_directory, pattern, reason, tags
):
    tags = _decodeTags(tags)
    tags.add("package_data")

    pkg_filenames = getFileList(
        package_directory,
        ignore_dirs=("__pycache__",),
        ignore_suffixes=(".py", ".pyw", ".pyc", ".pyo", ".dll")
        + getSharedLibrarySuffixes(),
    )

    if pkg_filenames:
        file_reason = "package '%s' %s" % (package_name, reason)

        for pkg_filename in pkg_filenames:
            rel_path = os.path.join(
                package_name.asPath(),
                os.path.relpath(pkg_filename, package_directory),
            )

            if pattern and not fnmatch.fnmatch(rel_path, pattern):
                continue

            yield makeIncludedDataFile(
                source_path=pkg_filename,
                dest_path=rel_path,
                reason=file_reason,
                tracer=tracer,
                tags=tags,
            )


def addIncludedDataFilesFromPackageOptions():
    """Late data files, from plugins and user options that work with packages"""
    # Cyclic dependency
    from nuitka import ModuleRegistry

    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonPackage() or module.isUncompiledPythonPackage():
            package_name = module.getFullName()

            match, reason = package_name.matchesToShellPatterns(
                patterns=getShallIncludePackageData()
            )

            if match:
                package_directory = module.getCompileTimeDirectory()

                for included_datafile in makeIncludedPackageDataFiles(
                    tracer=options_logger,
                    package_name=package_name,
                    package_directory=package_directory,
                    pattern=None,
                    reason=reason,
                    tags="user",
                ):
                    addIncludedDataFile(included_datafile)

    # Circular dependency
    from nuitka.plugins.Plugins import Plugins

    # Plugins provide per module through this.
    for module in ModuleRegistry.getDoneModules():
        for included_datafile in Plugins.considerDataFiles(module=module):
            addIncludedDataFile(included_datafile)

    for included_datafile in getIncludedDataFiles():
        for noinclude_datafile_pattern in getShallNotIncludeDataFilePatterns():
            if fnmatch.fnmatch(included_datafile.dest_path, noinclude_datafile_pattern):
                included_datafile.tags.add("inhibit")
                included_datafile.tags.remove("copy")
                break
        else:
            Plugins.onDataFileTags(
                included_datafile,
            )


_data_file_traces = OrderedDict()


def _reportDataFiles():
    for key in _data_file_traces:
        count = len(_data_file_traces[key])
        tracer, reason = key

        # Avoid being too noisy, maybe add a control for increasing this.
        if count > 10:
            tracer.info("Included %d data files due to %s." % (count, reason))
        else:
            for kind, dest_path in _data_file_traces[key]:
                if kind == "empty_dirs":
                    tracer.info(
                        "Included empty directories '%s' due to %s."
                        % (
                            ",".join(dest_path),
                            reason,
                        )
                    )
                elif kind == "data_blob":
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


def _handleDataFile(included_datafile):
    """Handle a data file."""
    tracer = included_datafile.tracer

    if not isinstance(included_datafile, IncludedDataFile):
        tracer.sysexit("Error, can only accept 'IncludedData*' objects from plugins.")

    if not isStandaloneMode():
        tracer.sysexit(
            "Error, package data files are only included in standalone or onefile mode."
        )

    dist_dir = getStandaloneDirectoryPath()

    key = tracer, included_datafile.reason
    if key not in _data_file_traces:
        _data_file_traces[key] = []

    _data_file_traces[key].append((included_datafile.kind, included_datafile.dest_path))

    if included_datafile.kind == "empty_dirs":
        for sub_dir in included_datafile.dest_path:
            created_dir = os.path.join(dist_dir, sub_dir)

            makePath(created_dir)
            putTextFileContents(
                filename=os.path.join(created_dir, ".keep_dir.txt"), contents=""
            )
    elif included_datafile.kind == "data_blob":
        dest_path = os.path.join(dist_dir, included_datafile.dest_path)
        makePath(os.path.dirname(dest_path))

        putTextFileContents(filename=dest_path, contents=included_datafile.data)
    elif included_datafile.kind == "data_file":
        dest_path = os.path.join(dist_dir, included_datafile.dest_path)

        makePath(os.path.dirname(dest_path))
        copyFileWithPermissions(
            source_path=included_datafile.source_path, dest_path=dest_path
        )
    else:
        assert False, included_datafile


def copyDataFiles():
    """Copy the data files needed for standalone distribution.

    Notes:
        This is for data files only, not DLLs or even extension modules,
        those must be registered as entry points, and would not go through
        necessary handling if provided like this.
    """

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

            _handleDataFile(
                included_datafile,
            )

    _reportDataFiles()
