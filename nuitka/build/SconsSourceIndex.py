#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Source files index handling for Scons builds."""

import os

from nuitka.Tracing import general, scons_logger
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    getFileContentByLine,
    getFilenameExtension,
    getNormalizedPathJoin,
    getWindowsShortPathName,
    hasFilenameExtension,
    isFilesystemEncodable,
    listDir,
    putTextFileContents,
    replaceFileAtomic,
)
from nuitka.utils.Utils import isWin32Windows


def getSourceFilesIndexFilename(source_dir):
    return getNormalizedPathJoin(source_dir, "source_files_index.txt")


def _getSourceDirFilenames(source_dir):
    for full_filename, filename_base in listDir(source_dir):
        if not hasFilenameExtension(filename_base, (".c", ".cpp", ".h")):
            continue

        if filename_base.endswith(".c"):
            cpp_filename = changeFilenameExtension(full_filename, ".cpp")

            if os.path.exists(cpp_filename):
                general.sysexit(
                    "Error, source directory '%s' contains both '%s' and '%s'."
                    % (source_dir, filename_base, os.path.basename(cpp_filename))
                )

        yield filename_base


def createSourceFilesIndex(source_dir):
    """Create the authoritative source and header file index for the Scons build.

    Notes:
        Plugins may reorder lines in this file before Scons runs.
    """
    index_filenames = []

    for sub_dirname in (None, "plugins", "static_src"):
        if sub_dirname is None:
            dirname = source_dir
            index_prefix = None
        else:
            dirname = getNormalizedPathJoin(source_dir, sub_dirname)
            index_prefix = sub_dirname

        if sub_dirname == "plugins" and not os.path.exists(dirname):
            continue

        for filename in _getSourceDirFilenames(dirname):
            if index_prefix is None:
                index_filenames.append(filename)
            else:
                index_filenames.append(index_prefix + "/" + filename)

    putTextFileContents(
        getSourceFilesIndexFilename(source_dir),
        index_filenames,
        encoding="utf8",
    )


def _makeSourceFilenameFileSystemEncodable(filename):
    filename_base = os.path.basename(filename)

    if isWin32Windows() and not isFilesystemEncodable(filename_base):
        filename = getWindowsShortPathName(filename)

        # Avoid ".C" suffixes, that MinGW64 wouldn't recognize.
        filename = changeFilenameExtension(
            filename, getFilenameExtension(filename).lower()
        )

    return filename


def _renameSourceFile(source_filename, target_filename, index_filename):
    try:
        replaceFileAtomic(source_filename, target_filename)
    except OSError as e:
        scons_logger.sysexit(
            "Error, source files index '%s' failed to rename C file '%s' to '%s': %s"
            % (index_filename, source_filename, target_filename, e)
        )


def _resolveSourceFilenameForC11(source_filename, index_filename, filename):
    if os.path.exists(source_filename):
        return _makeSourceFilenameFileSystemEncodable(source_filename)

    return scons_logger.sysexit(
        "Error, source files index '%s' lists file '%s', but it does not exist."
        % (index_filename, filename)
    )


def _resolveSourceFilenameForNonC11C(source_filename, index_filename, filename):
    cpp_filename = source_filename + "pp"

    if os.path.exists(source_filename):
        _renameSourceFile(
            source_filename=source_filename,
            target_filename=cpp_filename,
            index_filename=index_filename,
        )

        return _makeSourceFilenameFileSystemEncodable(cpp_filename)

    if os.path.exists(cpp_filename):
        return _makeSourceFilenameFileSystemEncodable(cpp_filename)

    return scons_logger.sysexit(
        "Error, source files index '%s' lists file '%s', but neither it nor its C++ rename result '%s' exists."
        % (index_filename, filename, os.path.basename(cpp_filename))
    )


def _resolveSourceFilenameForNonC11Cpp(source_filename, index_filename, filename):
    if os.path.exists(source_filename):
        return _makeSourceFilenameFileSystemEncodable(source_filename)

    c_filename = changeFilenameExtension(source_filename, ".c")

    if os.path.exists(c_filename):
        _renameSourceFile(
            source_filename=c_filename,
            target_filename=source_filename,
            index_filename=index_filename,
        )

        return _makeSourceFilenameFileSystemEncodable(source_filename)

    return scons_logger.sysexit(
        "Error, source files index '%s' lists file '%s', but neither it nor the C source file '%s' exists."
        % (index_filename, filename, os.path.basename(c_filename))
    )


def _resolveSourceFilenameFromIndex(env, source_dir, index_filename, filename):
    """Resolve an indexed source filename, renaming '.c' files to '.cpp' in non-C11 mode."""
    source_filename = getNormalizedPathJoin(source_dir, filename)

    if not hasFilenameExtension(source_filename, (".c", ".cpp")):
        return scons_logger.sysexit(
            "Error, source files index '%s' contains non C/C++ file '%s'."
            % (index_filename, filename)
        )

    if env.c11_mode:
        return _resolveSourceFilenameForC11(
            source_filename=source_filename,
            index_filename=index_filename,
            filename=filename,
        )

    if hasFilenameExtension(source_filename, ".c"):
        return _resolveSourceFilenameForNonC11C(
            source_filename=source_filename,
            index_filename=index_filename,
            filename=filename,
        )

    return _resolveSourceFilenameForNonC11Cpp(
        source_filename=source_filename,
        index_filename=index_filename,
        filename=filename,
    )


def getSourceFilenamesFromIndex(env, source_dir):
    """Resolve source filenames in index order and append header directories to 'CPPPATH'.

    Notes:
        Appends files from 'env.generated_source_filenames' created during Scons
        setup, without scanning 'source_dir'.
    """
    index_filename = getSourceFilesIndexFilename(source_dir)

    if not os.path.exists(index_filename):
        return scons_logger.sysexit(
            "Error, source files index '%s' does not exist." % index_filename
        )

    result = []
    header_dirnames = []

    index_filenames = getFileContentByLine(index_filename, encoding="utf8")

    for filename in env.generated_source_filenames:
        if filename not in index_filenames:
            index_filenames.append(filename)

    for filename in index_filenames:
        if hasFilenameExtension(filename, ".h"):
            header_dirname = os.path.dirname(
                getNormalizedPathJoin(source_dir, filename)
            )

            if header_dirname not in header_dirnames:
                header_dirnames.append(header_dirname)

            continue

        result.append(
            _resolveSourceFilenameFromIndex(
                env=env,
                source_dir=source_dir,
                index_filename=index_filename,
                filename=filename,
            )
        )

    if not result:
        return scons_logger.sysexit(
            "Error, source files index '%s' contains no source files." % index_filename
        )

    if header_dirnames:
        env.Append(CPPPATH=header_dirnames)

    return result


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
