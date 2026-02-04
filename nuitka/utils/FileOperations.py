#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utils for file and directory operations.

This provides enhanced and more error resilient forms of standard
stuff. It will also frequently add sorting for determinism.

"""

from __future__ import print_function

import codecs
import errno
import fnmatch
import glob
import os
import pickle
import shutil
import stat
import sys
import tempfile
import time
import unicodedata
from contextlib import contextmanager

from nuitka.__past__ import (  # pylint: disable=redefined-builtin
    FileNotFoundError,
    PermissionError,
    basestring,
    unicode,
)
from nuitka.Errors import NuitkaFilenameError
from nuitka.PythonVersions import python_version
from nuitka.Tracing import general, my_print, options_logger, queryUser

from .Hashing import Hash
from .Importing import importFromInlineCopy
from .ThreadedExecutor import RLock, getThreadIdent
from .Utils import (
    decoratorRetries,
    isLinux,
    isMacOS,
    isWin32OrPosixWindows,
    isWin32Windows,
    raiseWindowsError,
)

# Locking seems to be only required for Windows mostly, but we can keep
# it for all.
file_lock = RLock()

# Use this in case of dead locks or even to see file operations being done.
_lock_tracing = False


@contextmanager
def withFileLock(reason="unknown"):
    """Acquire file handling lock.

    Args:
        reason: What is being done.

    Notes: This is most relevant for Windows, but prevents concurrent access
    from threads generally, which could lead to observing half ready things.
    """

    if _lock_tracing:
        my_print(getThreadIdent(), "Want file lock for %s" % reason)
    file_lock.acquire()
    if _lock_tracing:
        my_print(getThreadIdent(), "Acquired file lock for %s" % reason)
    yield
    if _lock_tracing:
        my_print(getThreadIdent(), "Released file lock for %s" % reason)
    file_lock.release()


@contextmanager
def withTemporaryDirectory(
    logger,
    prefix=None,
    suffix=None,
    directory=None,
    ignore_errors=False,
    extra_recommendation=None,
):
    """Create a temporary directory and remove it afterwards.

    Args:
        logger: Logger to use for error reporting.
        prefix: Prefix of the directory name.
        suffix: Suffix of the directory name.
        directory: Directory where to create it.
        ignore_errors: Ignore errors when removing the directory.
        extra_recommendation: Recommendation what to do if removal fails.

    Yields:
        The path of the temporary directory.
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=directory)

    try:
        yield temp_dir
    finally:
        removeDirectory(
            temp_dir,
            logger=logger,
            ignore_errors=ignore_errors,
            extra_recommendation=extra_recommendation,
        )


def areSamePaths(path1, path2):
    """Decide if two paths the same.

    Args:
        path1: First path
        path2: Second path

    Returns:
        Boolean value indicating if the two paths point to the
        same path.

    Notes:

        Case differences ignored on platforms where that is the
        norm, and with it normalized, and turned absolute paths, and
        even short paths, it then becomes a mere string compare after that.
    """

    if path1 == path2:
        return True

    path1 = os.path.abspath(getNormalizedPath(path1))
    path2 = os.path.abspath(getNormalizedPath(path2))

    if path1 == path2:
        return True

    exists1 = os.path.exists(path1)
    exists2 = os.path.exists(path2)

    if exists1 != exists2:
        return False

    if exists1 and exists2:
        path1 = getExternalUsePath(path1)
        path2 = getExternalUsePath(path2)

    path1 = os.path.normcase(path1)
    path2 = os.path.normcase(path2)

    return path1 == path2


def areInSamePaths(path1, path2):
    """Decide if two paths are in the same directory

    Args:
        path1: First path
        path2: Second path

    Returns:
        Boolean value indicating if the two paths point into the
        same directory."""
    return areSamePaths(os.path.dirname(path1), os.path.dirname(path2))


def haveSameFileContents(path1, path2):
    """Check if two files have the same contents.

    Args:
        path1: First path
        path2: Second path

    Returns:
        bool: True if files have same content.
    """
    # Local import, to avoid this for normal use cases.
    import filecmp

    return filecmp.cmp(path1, path2)


def getFileSize(path):
    """Get the size of a file.

    Args:
        path: File path

    Returns:
        int: File size in bytes.
    """
    return os.path.getsize(path)


def getFileModificationTime(path):
    """Get the modification time of a file.

    Args:
        path: File path

    Returns:
        float: File modification time.
    """
    return os.stat(path).st_mtime


def relpath(path, start="."):
    """Make it a relative path, if possible.

    Args:
        path: path to work on
        start: where to start from, defaults to current directory

    Returns:
        Changed path, pointing to the same path relative to current
        directory if possible.

    Notes:
        On Windows, a relative path is not possible across device
        names, therefore it may have to return the absolute path
        instead.
    """
    if start == ".":
        start = os.curdir

    try:
        return os.path.relpath(path, start)
    except ValueError:
        # On Windows, paths on different devices prevent it to work. Use that
        # full path then.
        if isWin32OrPosixWindows():
            return os.path.abspath(path)
        raise


def isRelativePath(path):
    """Check if a path is relative.

    Args:
        path: Path to check

    Returns:
        bool: True if path is relative.
    """
    if os.path.isabs(path):
        return False
    if path.startswith((".." + os.path.sep, "../")):
        return False

    return True


def cheapCopyFile(source_path, dest_path):
    makeContainingPath(dest_path)

    if isWin32Windows():
        # Windows has symlinks these days, but they do not integrate well
        # with Python2 at least. So make a copy in any case.
        deleteFile(dest_path, must_exist=False)
        copyFile(source_path, dest_path)
    else:
        # Relative paths work badly for links. Creating them relative is
        # not worth the effort.
        src = os.path.abspath(source_path)

        try:
            link_target = os.readlink(dest_path)

            # If it's already a proper link, do nothing then.
            if link_target == src:
                return

            deleteFile(dest_path, must_exist=True)
        except OSError as _e:
            # Broken links work like that, remove them, so we can replace
            # them.
            try:
                deleteFile(dest_path, must_exist=False)
            except OSError:
                pass

        try:
            os.symlink(src, dest_path)
        except OSError:
            copyFile(src, dest_path)


def makePath(path):
    """Create a directory if it doesn't exist.

    Args:
        path: path to create as a directory

    Notes:
        This also is thread safe on Windows, i.e. no race is
        possible.

    """

    with withFileLock("creating directory %s" % path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError:
                if not os.path.exists(path):
                    raise


def makeContainingPath(filename):
    """Create the directory for containing a file if it doesn't exist.

    Args:
        filename: Path to the file.
    """
    target_dir = os.path.dirname(filename)

    if not os.path.isdir(target_dir):
        makePath(target_dir)


def isPathExecutable(path):
    """Check if the given path is executable.

    Args:
        path: Path to check.

    Returns:
        bool: True if executable.
    """
    return os.path.isfile(path) and os.access(path, os.X_OK)


def hasDirectoryContents(path):
    """Check if a directory has contents.

    Args:
        path: directory to check

    Returns:
        bool: True if directory exists and has contents, False otherwise.
    """
    if not os.path.isdir(path):
        return False

    if python_version >= 0x350:
        try:
            scan = os.scandir(path)
            result = next(scan, None) is not None
        except OSError:
            return False

        if python_version >= 0x360:
            scan.close()

        return result
    else:
        try:
            return bool(os.listdir(path))
        except OSError:
            return False


# Make sure we don't repeat this too much.
_real_path_windows_cache = {}
_powershell_path = None


def _getRealPathWindows(path):
    # Slow on Python2, because we are using an external process.
    # Singleton, pylint: disable=global-statement
    global _powershell_path
    if _powershell_path is None:
        from .Execution import getExecutablePath

        _powershell_path = getExecutablePath("powershell")

        # Try to find it only once, otherwise ignore its absence, symlinks are not
        # that important.
        if _powershell_path is None:
            _powershell_path = False

    if path not in _real_path_windows_cache:
        if _powershell_path:
            from .Execution import check_output

            result = check_output(
                [
                    _powershell_path,
                    "-NoProfile",
                    'Get-Item "%s" | Select-Object -ExpandProperty Target' % path,
                ],
                shell=False,
            )

            if str is not bytes:
                result = result.decode("utf8")

            if result.startswith("UNC\\"):
                # Avoid network mounts being converted to UNC shared paths by newer
                # Python versions, many tools won't work with those.
                _real_path_windows_cache[path] = path
            else:
                _real_path_windows_cache[path] = getNormalizedPathJoin(
                    os.path.dirname(path), result.rstrip("\r\n")
                )
        else:
            _real_path_windows_cache[path] = path

    return _real_path_windows_cache[path]


def getDirectoryRealPath(path):
    """Get os.path.realpath with Python2 and Windows symlink workaround applied.

    Args:
        path: path to get realpath of

    Returns:
        path with symlinks resolved

    Notes:
        Workaround for Windows symlink is applied. This function is not recursive
        at all with older Python, i.e. only the last part, the directory itself
        is being resolved there.

    """
    path = os.path.realpath(path)

    # Attempt to resolve Windows symlinks older Python
    if os.name == "nt":
        if os.path.islink(path) or (not os.path.isdir(path) and os.path.exists(path)):
            path = _getRealPathWindows(path)

    return path


def _restoreWindowsPath(orig_path, path):
    if path.startswith("\\\\"):
        drive, _remaining_path = os.path.splitdrive(orig_path)

        if drive and not drive.startswith("\\\\"):
            drive_real_path = os.path.realpath(drive + "\\")
            assert path.startswith(drive_real_path)

            path = drive + "\\" + path[len(drive_real_path) :]
    else:
        path = path.strip(os.path.sep)

        if os.path.sep in path:
            dirname = os.path.dirname(path)
            filename = os.path.basename(path)

            if dirname:
                dirname = getDirectoryRealPath(dirname)

                # Drive letters do not get slashes from 'os.path.join', so
                # we inject this here and normalize the path afterwards to
                # remove any duplication added.
                if os.path.sep not in dirname:
                    dirname = dirname + os.path.sep

                path = getNormalizedPathJoin(dirname, filename)

    return path


def getFilenameRealPath(path):
    """Get os.path.realpath with Python2 and Windows symlink workaround applied.

    Args:
        path: path to get realpath of

    Returns:
        path with symlinks resolved

    Notes:
        Workaround for Windows symlinks are applied, this works recursive and
        assumes that the path given itself is a file and not a directory, and
        doesn't handle file symlinks at the end on older Python currently, but
        we shouldn't deal with those.
    """
    orig_path = path
    path = os.path.realpath(path)

    # Avoid network mounts being converted to UNC shared paths by newer
    # Python versions, many tools won't work with those.
    if os.name == "nt":
        path = _restoreWindowsPath(orig_path=orig_path, path=path)

    return path


def listDir(path):
    """Give a sorted listing of a path.

    Args:
        path: directory to create a listing from

    Returns:
        Sorted list of tuples of full filename, and basename of
        files in that directory.

    Notes:
        Typically the full name and the basename are both needed
        so this function simply does both, for ease of use on the
        calling side.

        This should be used, because it makes sure to resolve the
        symlinks to directories on Windows, that a naive 'os.listdir'
        won't do by default.
    """
    real_path = getDirectoryRealPath(path)

    # The 'os.listdir' output needs to be unicode paths, or else it can be unusable
    # for Python2 on Windows at least. We try to go back on the result.
    if str is bytes and type(real_path) is str:
        real_path = unicode(real_path)

    def _tryEncodeToFilesystemEncoding(value):
        try:
            return encodeToFilesystemEncoding(value)
        except UnicodeEncodeError:
            return value

    return sorted(
        (
            _tryEncodeToFilesystemEncoding(getNormalizedPathJoin(path, filename)),
            _tryEncodeToFilesystemEncoding(filename),
        )
        for filename in os.listdir(real_path)
    )


def getFileList(
    path,
    ignore_dirs=(),
    ignore_filenames=(),
    ignore_suffixes=(),
    only_suffixes=(),
    normalize=True,
):
    """Get all files below a given path.

    Args:
        path: directory to create a recursive listing from
        ignore_dirs: Don't descend into these directory, ignore them
        ignore_filenames: Ignore files named exactly like this
        ignore_suffixes: Don't return files with these suffixes
        only_suffixes: If not empty, limit returned files to these suffixes

    Returns:
        Sorted list of all filenames below that directory,
        include the path given.

    Notes:
        This function descends into directories, but does
        not follow symlinks.
    """
    # We work with a lot of details here
    result = []

    # Normalize "ignore_dirs" for better matching.
    ignore_dirs = [os.path.normcase(ignore_dir) for ignore_dir in ignore_dirs]
    ignore_filenames = [
        os.path.normcase(ignore_filename) for ignore_filename in ignore_filenames
    ]

    for root, dirnames, filenames in os.walk(path):
        dirnames.sort()
        filenames.sort()

        # Normalize dirnames for better matching.
        dirnames_normalized = [os.path.normcase(dirname) for dirname in dirnames]
        for ignore_dir in ignore_dirs:
            if ignore_dir in dirnames_normalized:
                dirnames.remove(ignore_dir)

        # Compare to normalized filenames for better matching.
        filenames = [
            filename
            for filename in filenames
            if os.path.normcase(filename) not in ignore_filenames
        ]

        for filename in filenames:
            if os.path.normcase(filename).endswith(ignore_suffixes):
                continue

            if only_suffixes and not os.path.normcase(filename).endswith(only_suffixes):
                continue

            fullname = getNormalizedPathJoin(root, filename)

            if normalize:
                fullname = getNormalizedPath(fullname)

            result.append(fullname)

    return result


def getSubDirectories(path, ignore_dirs=()):
    """Get all directories below a given path.

    Args:
        path: directory to create a recursive listing from
        ignore_dirs: directories named that like will be ignored

    Returns:
        Sorted list of all directories below that directory,
        relative to it.

    Notes:
        This function descends into directories, but does
        not follow symlinks.
    """

    result = []

    ignore_dirs = [os.path.normcase(ignore_dir) for ignore_dir in ignore_dirs]

    for root, dirnames, _filenames in os.walk(path):
        # Normalize dirnames for better matching.
        dirnames_normalized = [os.path.normcase(dirname) for dirname in dirnames]
        for ignore_dir in ignore_dirs:
            if ignore_dir in dirnames_normalized:
                dirnames.remove(ignore_dir)

        dirnames.sort()

        for dirname in dirnames:
            result.append(getNormalizedPathJoin(root, dirname))

    result.sort()
    return result


def getDllBasename(path):
    """Get the basename of a DLL file, stripping version and extension.

    Args:
        path: Path to DLL file.

    Returns:
        str or None: Basename of DLL or None if not a DLL.
    """
    compare_path = os.path.normcase(path)

    for suffix in (".dll", ".so", ".dylib"):
        if compare_path.endswith(suffix):
            return path[: -len(suffix)]

    # Linux is not case sensitive, but lets still do it properly, sometimes, it
    # is done macOS too. So we split on the normcase, but only to find out what
    # is going on there.
    if ".so." in compare_path:
        return path[: len(compare_path.split(".so.")[0])]

    return None


def listDllFilesFromDirectory(path, prefix=None, suffixes=None):
    """Give a sorted listing of DLLs filenames in a path.

    Args:
        path: directory to create a DLL listing from
        prefix: shell pattern to match filename start against, can be None
        suffixes: shell patch to match filename end against, defaults to all platform ones

    Returns:
        Sorted list of tuples of full filename, and basename of
        DLLs in that directory.

    Notes:
        Typically the full name and the basename are both needed
        so this function simply does both, for ease of use on the
        calling side.
    """

    # Accept None value as well.
    prefix = prefix or ""

    suffixes = suffixes or ("dll", "so.*", "so", "dylib")

    pattern_list = [prefix + "*." + suffix for suffix in suffixes]

    for fullpath, filename in listDir(path):
        for pattern in pattern_list:
            if fnmatch.fnmatch(filename, pattern):
                yield fullpath, filename
                break


def listExeFilesFromDirectory(path, prefix=None, suffixes=None):
    """Give a sorted listing of EXE filenames in a path.

    Args:
        path: directory to create a DLL listing from
        prefix: shell pattern to match filename start against, can be None
        suffixes: shell patch to match filename end against, can be None

    Returns:
        Sorted list of tuples of full filename, and basename of
        DLLs in that directory.

    Notes:
        Typically the full name and the basename are both needed
        so this function simply does both, for ease of use on the
        calling side.
    """

    # Accept None value as well.
    prefix = prefix or ""

    # On Windows, we check exe suffixes, on other platforms we shell all filenames,
    # matching the prefix, but they have to the executable bit set.
    if not suffixes and isWin32OrPosixWindows():
        suffixes = ("exe", "bin")

    if suffixes:
        pattern_list = [prefix + "*." + suffix for suffix in suffixes]
    else:
        pattern_list = [prefix + "*"]

    for fullpath, filename in listDir(path):
        for pattern in pattern_list:
            if fnmatch.fnmatch(filename, pattern):
                if not isWin32OrPosixWindows() and not os.access(fullpath, os.X_OK):
                    continue

                yield fullpath, filename
                break


def getSubDirectoriesWithDlls(path):
    """Get all directories below a given path.

    Args:
        path: directory to create a recursive listing from

    Returns:
        Sorted tuple of all directories below that directory,
        relative to it, that contain DLL files.

    Notes:
        This function descends into directories, but does
        not follow symlinks.
    """

    result = set()

    for dll_sub_directory in _getSubDirectoriesWithDlls(path):
        result.add(dll_sub_directory)

    return tuple(sorted(result))


def _getSubDirectoriesWithDlls(path):
    for sub_directory in getSubDirectories(path=path, ignore_dirs=("__pycache__",)):
        if any(listDllFilesFromDirectory(sub_directory)) or _isMacOSFramework(
            sub_directory
        ):
            yield sub_directory

            candidate = os.path.dirname(sub_directory)

            # Should be string identical, no normalization in is done in "getSubDirectories"
            while candidate != path:
                yield candidate
                candidate = os.path.dirname(candidate)


def _isMacOSFramework(path):
    """Decide if a folder is a framework folder."""
    return isMacOS() and os.path.isdir(path) and path.endswith(".framework")


def isLink(path):
    """Check if a path is a symbolic link (or junction on Windows).

    Args:
        path: Path to check.

    Returns:
        bool: True if path is a link.
    """
    result = os.path.islink(path)

    # Special handling for Junctions.
    if not result and isWin32Windows():
        import ctypes.wintypes

        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
        GetFileAttributesW.restype = ctypes.wintypes.DWORD
        GetFileAttributesW.argtypes = (ctypes.wintypes.LPCWSTR,)

        INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
        FILE_ATTRIBUTE_REPARSE_POINT = 0x00400

        result = GetFileAttributesW(path)

        if result != INVALID_FILE_ATTRIBUTES:
            result = bool(result & FILE_ATTRIBUTE_REPARSE_POINT)

    return result


def deleteFile(path, must_exist):
    """Delete a file, potentially making sure it exists.

    Args:
        path: file to delete

    Notes:
        This also is thread safe on Windows, i.e. no race is
        possible.
    """
    with withFileLock("deleting file %s" % path):
        if isLink(path) or os.path.isfile(path):
            try:
                os.unlink(path)
            except OSError:
                if must_exist:
                    raise
        elif must_exist:
            raise OSError("Does not exist", path)


def searchPrefixPath(path, element):
    """Search element and return prefix in path, if any.

    Args:
        path: Path to search in.
        element: Element to search for.

    Returns:
         str or None: Prefix path if found, None otherwise.
    """

    while path:
        if os.path.normcase(os.path.basename(path)) == os.path.normcase(element):
            return path

        new_path = os.path.dirname(path)
        if new_path == path:
            break
        path = new_path

    return None


def getFilenameExtension(path):
    """Get the filename extension (dot included)

    Note: The extension is case normalized, i.e. it may actually be ".TXT"
    rather than ".txt", use "changeFilenameExtension" if you want to replace
    it with something else.

    Note: For checks on extension, use hasFilenameExtension instead.
    """
    return os.path.splitext(os.path.normcase(path))[1]


def changeFilenameExtension(path, extension):
    """Change the filename extension.

    Args:
        path: Path to change.
        extension: New extension (including dot).

    Returns:
        str: Path with new extension.
    """

    is_legal, illegal_reason = isLegalPath(path)
    if not is_legal:
        raise NuitkaFilenameError(illegal_reason)

    result = os.path.splitext(path)[0] + extension

    is_legal, illegal_reason = isLegalPath(result)
    if not is_legal:
        raise NuitkaFilenameError(illegal_reason)

    return result


def switchFilenameExtension(path, old_extension, new_extension):
    """Switch the filename extension specified to another one.

    Args:
        path: Path to check.
        old_extension: Extension expected.
        new_extension: Extension to switch to.

    Returns:
        str: Path with switched extension.
    """
    assert path.endswith(old_extension)
    return path[: -len(old_extension)] + new_extension


def hasFilenameExtension(path, extensions):
    """Has a filename one of the given extensions.

    Note: The extensions should be normalized, i.e. lower case and will match other
    cases where the file system does that on a platform. Also they include a dot,
    e.g. ".qml" is a good value.
    """

    extension = getFilenameExtension(path)

    if isinstance(extensions, basestring):
        return extension == extensions
    else:
        return extension in extensions


def addFilenameExtension(path, extension):
    """Add an extension to a filename if it doesn't already have it.

    Args:
        path: Path to add extension to.
        extension: Extension to add (including dot).

    Returns:
        str: Path with extension added if missing.
    """
    if not hasFilenameExtension(path, extension):
        path += extension

    return path


def removeDirectory(path, logger, ignore_errors, extra_recommendation):
    """Remove a directory recursively.

    On Windows, it happens that operations fail, and succeed when retried,
    so added a retry and small delay, then another retry. Should make it
    much more stable during tests.

    All kinds of programs that scan files might cause this, but they do
    it hopefully only briefly.
    """

    with withFileLock("removing directory %s" % path):
        if os.path.exists(path):

            @decoratorRetries(
                logger=logger,
                purpose="delete '%s'" % path,
                consequence="the path is not fully removed",
                extra_recommendation=extra_recommendation,
            )
            def _removeDirectory():
                def onError(func, path, exc_info):
                    # Record what happened what happened, pylint: disable=unused-argument
                    last_error.append((func, path))

                previous_error = []

                # Try deleting while ignoring errors first.
                while True:
                    last_error = []
                    shutil.rmtree(path, ignore_errors=False, onerror=onError)

                    # onError as a side effect, modifies last_error
                    if previous_error == last_error:
                        break

                    previous_error = list(last_error)
                    time.sleep(0.2)

                # If it still exists, try one more time, this time not ignoring errors.
                if os.path.exists(path):
                    try:
                        shutil.rmtree(path, ignore_errors=ignore_errors)
                    except OSError:
                        if not ignore_errors:
                            raise

            _removeDirectory()


def resetDirectory(path, logger, ignore_errors, extra_recommendation):
    """Reset a directory, removing it if it exists and recreating it empty.

    Args:
        path: Path to reset.
        logger: Logger for output.
        ignore_errors: Whether to ignore errors during removal.
        extra_recommendation: Recommendation message for errors.
    """
    removeDirectory(
        path=path,
        logger=logger,
        ignore_errors=ignore_errors,
        extra_recommendation=extra_recommendation,
    )
    makePath(path)


@contextmanager
def withTemporaryFile(prefix="", suffix="", mode="w", delete=True, temp_path=None):
    """Provide a temporary file opened and potentially deleted.

    Args:
        prefix: Filename prefix.
        suffix: Filename suffix.
        mode: Open mode.
        delete: Whether to delete the file on exit.
        temp_path: Directory for temporary file.

    Yields:
        file: The temporary file object.
    """
    with tempfile.NamedTemporaryFile(
        prefix=prefix, suffix=suffix, mode=mode, delete=delete, dir=temp_path
    ) as temp_file:
        yield temp_file


@contextmanager
def withTemporaryFilename(prefix="", suffix="", temp_path=None):
    """Provide a temporary filename.

    Args:
        prefix: Filename prefix.
        suffix: Filename suffix.
        temp_path: Directory for temporary file.

    Yields:
        str: The temporary filename.
    """
    with tempfile.NamedTemporaryFile(
        prefix=prefix,
        suffix=suffix,
        mode="wb",
        delete=False,
        dir=temp_path,
    ) as temp_file:
        filename = temp_file.name
        temp_file.close()
        deleteFile(filename, must_exist=True)

        yield filename


def getFileContentByLine(filename, mode="r", encoding=None, errors=None):
    """Get the contents of a file as lines.

    Args:
        filename: str with the file to be read
        mode: "r" for str, "rb" for bytes result
        encoding: optional encoding to used when reading the file, e.g. "utf8"
        errors: optional error handler decoding the content, as defined in `codecs`

    Returns:
        list: List of lines.
    """
    # We read the whole, to keep lock times minimal. We only deal with small
    # files like this normally.
    return getFileContents(
        filename, mode, encoding=encoding, errors=errors
    ).splitlines()


def getFileContents(filename, mode="r", encoding=None, errors=None):
    """Get the contents of a file.

    Args:
        filename: str with the file to be read
        mode: "r" for str, "rb" for bytes result
        encoding: optional encoding to used when reading the file, e.g. "utf8"
        errors: optional error handler decoding the content, as defined in `codecs`

    Returns:
        str or bytes - depending on mode.

    """

    with withFileLock("reading file %s" % filename):
        with openTextFile(filename, mode, encoding=encoding, errors=errors) as f:
            return f.read()


def getFileFirstLine(filename, mode="r", encoding=None):
    """Get the contents of a file.

    Args:
        filename: str with the file to be read
        mode: "r" for str, "rb" for bytes result
        encoding: optional encoding to used when reading the file, e.g. "utf8"

    Returns:
        str or bytes - depending on mode.

    """

    with withFileLock("reading file %s" % filename):
        with openTextFile(filename, mode, encoding=encoding) as f:
            return f.readline()


def openTextFile(filename, mode, encoding=None, errors=None):
    """Open a text file with proper handling.

    Args:
        filename: Path to file.
        mode: Open mode.
        encoding: Encoding to use.
        errors: Error handling.

    Returns:
        file: Opened file object.
    """
    # Do not attempt to create files with what we consider
    # illegal filenames.
    if "w" in mode:
        is_legal, illegal_reason = isLegalPath(filename)
        if not is_legal:
            raise NuitkaFilenameError(illegal_reason)

    # Doesn't exist anymore for Python3.7 or later.
    if python_version >= 0x370:
        mode = mode.replace("U", "")

    return codecs.open(filename, mode, encoding=encoding, errors=errors)


def putTextFileContents(filename, contents, encoding=None):
    """Write a text file from given contents.

    Args:
        filename: str with the file to be created
        contents: str or iterable of strings with what should be written into the file
        encoding: optional encoding to used when writing the file

    Returns:
        None
    """

    def _writeContents(output_file):
        if isinstance(contents, basestring):
            print(contents, file=output_file, end="")
        else:
            for line in contents:
                print(line, file=output_file)

    with withFileLock("writing file %s" % filename):
        with openTextFile(filename, "w", encoding=encoding) as output_file:
            _writeContents(output_file)


def putBinaryFileContents(filename, contents):
    """Write a binary file from given contents.

    Args:
        filename: str with the file to be created
        contents: bytes that should be written into the file

    Returns:
        None
    """

    with withFileLock("writing file %s" % filename):
        with openTextFile(filename, "wb") as output_file:
            output_file.write(contents)


def changeTextFileContents(filename, contents, encoding=None, compare_only=False):
    """Write a text file from given contents.

    Args:
        filename: str with the file to be created or updated
        contents: str
        encoding: optional encoding to used when writing the file

    Returns:
        change indication for existing file if any
    """

    if (
        not os.path.isfile(filename)
        or getFileContents(filename, encoding=encoding) != contents
    ):
        if not compare_only:
            putTextFileContents(filename, contents, encoding=encoding)

        return True
    else:
        return False


@contextmanager
def withPreserveFileMode(filenames):
    """Context manager to preserve file modes.

    Args:
        filenames: Single filename or list of filenames.
    """
    if isinstance(filenames, basestring):
        filenames = [filenames]

    old_modes = {}
    for filename in filenames:
        if os.path.exists(filename):
            old_modes[filename] = os.stat(filename).st_mode

    yield

    for filename in filenames:
        if filename in old_modes and os.path.exists(filename):
            os.chmod(filename, old_modes[filename])


@contextmanager
def withMadeWritableFileMode(filenames):
    """Context manager to make files writable temporarily.

    Args:
        filenames: Single filename or list of filenames.
    """
    if isinstance(filenames, basestring):
        filenames = [filenames]

    with withPreserveFileMode(filenames):
        for filename in filenames:
            os.chmod(filename, int("644", 8))

        yield


def removeFileExecutablePermission(filename):
    """Remove executable permission from a file.

    Args:
        filename: Path to file.
    """
    old_stat = os.stat(filename)

    mode = old_stat.st_mode
    mode &= ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if mode != old_stat.st_mode:
        os.chmod(filename, mode)


def addFileExecutablePermission(filename):
    """Add executable permission to a file.

    Args:
        filename: Path to file.
    """
    old_stat = os.stat(filename)

    mode = old_stat.st_mode
    mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

    if mode != old_stat.st_mode:
        os.chmod(filename, mode)


def renameFile(source_filename, dest_filename):
    """Rename a file, with failover to copy+delete on Windows.

    Args:
        source_filename: Source path.
        dest_filename: Destination path.
    """
    # There is no way to safely update a file on Windows, but lets
    # try on Linux at least.
    old_stat = os.stat(source_filename)

    try:
        os.rename(source_filename, dest_filename)
    except OSError:
        copyFile(source_filename, dest_filename)
        os.unlink(source_filename)

    os.chmod(dest_filename, old_stat.st_mode)


def copyTree(source_path, dest_path):
    """Copy whole directory tree, preserving attributes.

    Args:
        source_path: where to copy from
        dest_path: where to copy to, may already exist

    Notes:
        This must be used over 'shutil.copytree' which has troubles
        with existing directories on some Python versions.
    """
    if python_version >= 0x380:
        # Python 3.8+ has dirs_exist_ok
        return shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
    else:

        from distutils.dir_util import (  # Older Python only, pylint: disable=I0021,import-error
            copy_tree,
        )

        return copy_tree(source_path, dest_path)


def resolveSymlink(path):
    """Resolve a symlink, to a relative path.

    Args:
        path: Path to symlink.

    Returns:
        str: Relative path to link target.
    """
    link_source_abs = os.path.abspath(path)
    link_target_abs = os.path.abspath(
        getNormalizedPathJoin(os.path.dirname(path), os.readlink(path))
    )
    link_target_rel = relpath(link_target_abs, os.path.dirname(link_source_abs))

    return link_target_rel


def copyFileWithPermissions(source_path, dest_path, target_dir):
    """Improved version of 'shutil.copy2' for putting things to dist folder.

    File systems might not allow to transfer extended attributes, which we then
    ignore and only copy permissions.

    Args:
        source_path: Source file.
        dest_path: Destination file.
        target_dir: Target directory (to check for symlink containment).
    """

    if os.path.islink(source_path) and not isWin32Windows():
        link_target_rel = resolveSymlink(source_path)

        if isFilenameBelowPath(
            path=target_dir,
            filename=getNormalizedPathJoin(os.path.dirname(dest_path), link_target_rel),
        ):
            os.symlink(link_target_rel, dest_path)
            return

    try:
        shutil.copy2(
            source_path,
            dest_path,
        )
    except PermissionError as e:
        if e.errno != errno.EACCES:
            raise

        source_mode = os.stat(source_path).st_mode
        shutil.copy(source_path, dest_path)
        os.chmod(dest_path, source_mode)


def copyFile(source_path, dest_path):
    """Improved version of 'shutil.copy'.

    This handles errors with a chance to correct them, e.g. on Windows, files
    might be locked by running program or virus checkers.

    Args:
        source_path: Source file.
        dest_path: Destination file.
    """

    while 1:
        try:
            shutil.copyfile(source_path, dest_path)
        except PermissionError as e:
            if e.errno != errno.EACCES:
                raise

            general.warning("Problem copying file %s:" % e)

            if (
                queryUser(
                    "Retry?",
                    choices=("yes", "no"),
                    default="yes",
                    default_non_interactive="no",
                )
                == "yes"
            ):
                continue

            raise

        break


def getWindowsDrive(path):
    """Windows drive for a given path.

    Args:
        path: Path to check.

    Returns:
        str: Drive letter with colon, normalized.
    """

    drive, _ = os.path.splitdrive(os.path.abspath(path))
    return os.path.normcase(drive)


def isFilenameBelowPath(path, filename, consider_short=True):
    """Is a filename inside of a given directory path.

    Args:
        path: Location to be below (can be tuple/list of paths).
        filename: Candidate being checked.
        consider_short: Whether to consider short paths on Windows.

    Returns:
        bool: True if filename is below path.
    """
    if type(path) in (tuple, list):
        for p in path:
            if isFilenameBelowPath(
                path=p, filename=filename, consider_short=consider_short
            ):
                return True

        return False

    path = os.path.abspath(path)
    filename = os.path.abspath(filename)

    if isWin32Windows():
        if getWindowsDrive(path) != getWindowsDrive(filename):
            return False

    result = os.path.relpath(filename, path).split(os.path.sep, 1)[0] != ".."

    if not result and consider_short:
        if os.path.exists(filename) and os.path.exists(path):
            filename = getExternalUsePath(filename)
            path = getExternalUsePath(path)

            if isWin32Windows():
                if getWindowsDrive(path) != getWindowsDrive(filename):
                    return False

            result = os.path.relpath(filename, path).split(os.path.sep, 1)[0] != ".."

    return result


def isFilenameSameAsOrBelowPath(path, filename):
    """Is a filename inside of a given directory path or the same path as that directory."""
    if type(path) in (tuple, list):
        return any(isFilenameSameAsOrBelowPath(path=p, filename=filename) for p in path)

    return isFilenameBelowPath(path, filename) or areSamePaths(path, filename)


def getWindowsShortPathName(filename):
    """Gets the short path name of a given long path.

    Args:
        filename - long Windows filename
    Returns:
        Path that is a short filename pointing at the same file.
    Notes:
        Originally from http://stackoverflow.com/a/23598461/200291
    """
    import ctypes.wintypes

    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    GetShortPathNameW.argtypes = (
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD,
    )
    GetShortPathNameW.restype = ctypes.wintypes.DWORD

    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = GetShortPathNameW(
            os.path.abspath(filename), output_buf, output_buf_size
        )

        if needed == 0:
            # Windows only code, pylint: disable=I0021,undefined-variable

            # Permission denied.
            if ctypes.GetLastError() == 5:
                return filename

            raiseWindowsError("getWindowsShortPathName for %s" % filename)
        if output_buf_size >= needed:
            # Short paths should be ASCII. Don't return unicode without a need,
            # as e.g. Scons hates that in environment variables.
            if str is bytes:
                return output_buf.value.encode("utf8")
            else:
                return output_buf.value
        else:
            output_buf_size = needed


def getWindowsLongPathName(filename):
    """Gets the long path name of a given long path.

    Args:
        filename - short Windows filename
    Returns:
        Path that is a long filename pointing at the same file.
    """
    import ctypes.wintypes

    GetLongPathNameW = ctypes.windll.kernel32.GetLongPathNameW
    GetLongPathNameW.argtypes = (
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD,
    )
    GetLongPathNameW.restype = ctypes.wintypes.DWORD

    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = GetLongPathNameW(
            getNormalizedPath(os.path.abspath(filename)), output_buf, output_buf_size
        )

        if needed == 0:
            # Windows only code, pylint: disable=I0021,undefined-variable

            # Permission denied.
            if ctypes.GetLastError() == 5:
                return filename

            raiseWindowsError("getWindowsLongPathName for '%s'" % filename)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


_external_use_path_cache = {}


def getExternalUsePath(filename, only_dirname=False):
    """Gets the externally usable absolute path for a given relative path.

    Args:
        filename - filename, potentially relative
    Returns:
        Path that is a absolute and (on Windows) short filename pointing at the same file.
    Notes:
        This is only 'os.path.abspath' except on Windows, where is converts
        to a short path too.
    """

    filename = os.path.abspath(filename)
    key = filename, only_dirname

    if key not in _external_use_path_cache:
        if os.name == "nt":
            filename = getFilenameRealPath(filename)

            if only_dirname:
                dirname = getWindowsShortPathName(os.path.dirname(filename))
                assert os.path.exists(dirname)
                filename = getNormalizedPathJoin(dirname, os.path.basename(filename))
            else:
                filename = getWindowsShortPathName(filename)

            # Cache result
            _external_use_path_cache[key] = filename

            # Looking the resolved path up again should give same result immediately.
            key = filename, only_dirname
            _external_use_path_cache[key] = filename
        else:
            _external_use_path_cache[key] = filename

    return _external_use_path_cache[key]


_report_path_cache = {}


def getReportSourceReference(source_ref):
    """Convert a source ref into a path suitable for user output.

    Args:
        source_ref: Source reference object.

    Returns:
        str: String representation for reporting.
    """
    return "%s:%s" % (
        getReportPath(source_ref.getFilename()),
        source_ref.getLineNumber(),
    )


def getReportPath(filename, prefixes=()):
    """Convert filename into a path suitable for reporting, avoiding home directory paths.

    Args:
        filename: Path to convert.
        prefixes: Optional prefixes to relativize against.

    Returns:
        str: Path suitable for reporting.
    """
    key = filename, tuple(prefixes)

    if key not in _report_path_cache:
        _report_path_cache[key] = _getReportPath(filename, prefixes)

    return _report_path_cache[key]


def isNonLocalPath(path):
    """Tell if a path is potentially outside of current directory.

    This is not reliable and mainly for reporting purposes to identify paths
    work looking to abbreviate.

    Args:
        path: Path to check.

    Returns:
        bool: True if path is likely non-local.
    """
    return path.startswith("..") or os.path.isabs(path)


def _getReportPath(filename, prefixes):
    if os.path.isabs(os.path.expanduser(filename)):
        prefixes = list(prefixes)
        prefixes.append(
            ("~", os.path.expanduser("~")),
        )

        abs_filename = os.path.abspath(os.path.expanduser(filename))

        for prefix_name, prefix_path in prefixes:
            if isFilenameBelowPath(
                path=prefix_path, filename=abs_filename, consider_short=False
            ):
                return getNormalizedPathJoin(
                    prefix_name, relpath(path=abs_filename, start=prefix_path)
                )

            if isFilenameBelowPath(
                path=prefix_path, filename=abs_filename, consider_short=True
            ):
                return getNormalizedPathJoin(
                    prefix_name,
                    relpath(path=abs_filename, start=getExternalUsePath(prefix_path)),
                )

    if isWin32Windows():
        try:
            old_filename = filename

            filename = getWindowsLongPathName(filename)
        except FileNotFoundError:
            dirname = os.path.dirname(filename)

            if dirname:
                try:
                    dirname = getWindowsLongPathName(dirname)
                except FileNotFoundError:
                    pass
                else:
                    filename = getNormalizedPathJoin(
                        dirname, os.path.basename(filename)
                    )
        else:
            if old_filename != filename:
                return _getReportPath(filename, prefixes)

    return filename


def getLinkTarget(filename):
    """Return the path a link is pointing too, if any.

    Args:
        filename - check this path, need not be a filename

    Returns:
        (bool, link_target) - first value indicates if it is a link, second the link target

    Notes:
        This follows symlinks to the very end.
    """
    is_link = False
    while os.path.exists(filename) and os.path.islink(filename):
        link_target = os.readlink(filename)

        filename = getNormalizedPathJoin(os.path.dirname(filename), link_target)
        is_link = True

    return is_link, filename


# Late import and optional to be there.
atomicwrites = None


def replaceFileAtomic(source_path, dest_path):
    """
    Move ``src`` to ``dst``. If ``dst`` exists, it will be silently
    overwritten.

    Both paths must reside on the same filesystem for the operation to be
    atomic.

    spellchecker: ignore atomicwrites
    """

    if python_version >= 0x300:
        os.replace(source_path, dest_path)
    else:
        global atomicwrites  # singleton, pylint: disable=global-statement

        if atomicwrites is None:
            atomicwrites = importFromInlineCopy("atomicwrites", must_exist=True)

        atomicwrites.replace_atomic(source_path, dest_path)


def resolveShellPatternToFilenames(pattern):
    """Resolve shell pattern to filenames.

    Args:
        pattern - str

    Returns:
        list - filenames that matched.
    """

    if "**" in pattern:
        if python_version >= 0x350:
            result = glob.glob(pattern, recursive=True)
        else:
            glob2 = importFromInlineCopy("glob2", must_exist=False)

            if glob2 is None:
                options_logger.sysexit(
                    "Using pattern with '**' is not supported before Python 3.5 unless glob2 is installed."
                )

            result = glob2.glob(pattern)
    else:
        result = glob.glob(pattern)

    result = [os.path.normpath(filename) for filename in result]
    result.sort()
    return result


@contextmanager
def withDirectoryChange(path, allow_none=False):
    """Change current directory temporarily in a context.

    Args:
        path: Director to be currently in.
        allow_none: If None is passed, do nothing associated with this.
    """

    # spell-checker: ignore chdir

    if path is not None or not allow_none:
        old_cwd = os.getcwd()
        os.chdir(path)

    yield

    if path is not None or not allow_none:
        os.chdir(old_cwd)


def containsPathElements(path, elements):
    """Test if a path contains any unwanted elements.

    Args:
        path: directory path to check
        elements: iterable of elements that must not be in the path

    Returns:
        bool - True if any of elements is part of the path name
    """

    elements = tuple(os.path.normcase(element) for element in elements)
    path = os.path.normpath(path)

    parts = os.path.normpath(path).split(os.path.sep)

    return any(element in parts for element in elements)


def syncFileOutput(file_handle):
    """Synchronize a file contents to disk

    On this, this not only flushes, but calls "syncfs" to make sure things work
    properly.

    # spell-checker: ignore syncfs
    """

    file_handle.flush()

    if isLinux():
        import ctypes

        try:
            libc = ctypes.CDLL("libc.so.6")
        except OSError:
            # We cannot do it easily for this Linux apparently.
            return

        try:
            libc.syncfs(file_handle.fileno())
        except AttributeError:
            # Too old to have "syncfs" available.
            return


def isFilesystemEncodable(filename):
    """Decide if a filename is safe for use as a file system path with tools."""
    if os.name == "nt" and type(filename) is unicode:
        value = (
            unicodedata.normalize("NFKD", filename)
            .encode("ascii", "ignore")
            .decode("ascii")
        )

        return value == filename
    else:
        return True


def makeFilesystemEncodable(filename):
    """Make a filename safe for filesystem usage.

    Args:
        filename: Path to make safe.

    Returns:
        str: Safe filename (short path on Windows if necessary).
    """
    if not os.path.isabs(filename):
        filename = os.path.abspath(filename)

    if not isFilesystemEncodable(filename):
        filename = getExternalUsePath(filename)

    return filename


def openPickleFile(filename, mode, protocol=-1):
    """Open a pickle file with proper handling.

    Args:
        filename: Path to pickle file.
        mode: Open mode.
        protocol: Pickle protocol version.

    Returns:
        tuple: (file_handle, pickler)
    """
    file_handle = openTextFile(filename, mode)

    if python_version < 0x300:
        return file_handle, pickle.Pickler(file_handle, protocol)
    else:
        return file_handle, pickle._Pickler(  # pylint: disable=protected-access
            file_handle, protocol
        )


def isLegalPath(path):
    """Check if a path is legal on the current platform.

    Args:
        path: Path to check.

    Returns:
        tuple: (bool, str or None) - (is_legal, illegal_reason)
    """
    illegal_suffixes = "/\\"
    illegal_chars = "\0"

    if path == "":
        return False, "is empty"

    if isWin32Windows():
        illegal_chars += r'*"/<>:|?'

        illegal_chars += "".join(chr(x) for x in range(1, 32))
        illegal_suffixes += " ."

    if isMacOS():
        illegal_chars += ":"

    for pos, c in enumerate(path):
        if c == ":" and pos == 1 and isWin32Windows():
            continue

        if c in illegal_chars:
            return False, "contains illegal character %r" % c

    for illegal_suffix in illegal_suffixes:
        if path.endswith(illegal_suffix):
            return False, "contains illegal suffix %r" % illegal_suffix

        for part in path.split(os.path.sep):
            if part in (".", ".."):
                continue

            if part.endswith(illegal_suffix):
                return False, "contains illegal suffix %r in path part %r" % (
                    illegal_suffix,
                    part,
                )

            part_length = len(part)
            if part_length > 255:
                return False, "contains too long (%d) name part %r" % (
                    part_length,
                    part,
                )

    return True, None


def getParentDirectories(path):
    """Get all parent directories of a path in descending order.

    Args:
        path: Path to start from.

    Yields:
        str: Parent directory paths.
    """

    while 1:
        old_path = path
        path = os.path.dirname(path)

        if not path or path == old_path:
            return

        yield path


def getNormalizedPath(path):
    """Return normalized path that is also a native path, i.e. only legal characters.

    Needed, because MSYS2 likes to keep "/" in normalized paths.
    """
    path = os.path.normpath(path)
    if isWin32Windows():
        path = path.replace("/", "\\")

    return path


def getUserInputNormalizedPath(path):
    result = getNormalizedPath(path)

    if isMacOS():
        result = os.path.expanduser(result)

    return result


def getNormalizedPathJoin(*paths):
    """Return join of path elements as a normalized path that is also a native path,
       i.e. only legal characters.

    Needed, because MSYS2 likes to keep "/" in normalized paths.
    """
    return getNormalizedPath(os.path.join(*paths))


def getFileContentsHash(filename, as_string=True, line_filter=None):
    """Get the hash of a file's content.

    Args:
        filename: Path to file.
        as_string: Return as string (hex digest) or bytes (digest).
        line_filter: Optional filter function for lines.

    Returns:
        str or bytes: Hash result.
    """
    result = Hash()
    result.updateFromFile(filename=filename, line_filter=line_filter)

    if as_string:
        return result.asHexDigest()
    else:
        return result.asDigest()


def encodeToFilesystemEncoding(path):
    """Encode a path to filesystem encoding.

    Args:
        path: Path to encode.

    Returns:
        Encoded path (bytes on Python 2, str on Python 3).

    Raises:
        UnicodeEncodeError: If the path cannot be encoded in the filesystem encoding.
    """
    if str is bytes and type(path) is unicode:
        # spell-checker: ignore getfilesystemencoding
        return path.encode(sys.getfilesystemencoding() or "utf8")

    return path


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
