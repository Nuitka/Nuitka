#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Utils for file and directory operations.

This provides enhanced and more error resilient forms of standard
stuff. It will also frequently add sorting for determism.

"""

from __future__ import print_function

import glob
import os
import shutil
import stat
import tempfile
import time
from contextlib import contextmanager

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    basestring,
)
from nuitka.PythonVersions import python_version
from nuitka.Tracing import my_print

from .Importing import importFromInlineCopy
from .ThreadedExecutor import RLock, getThreadIdent
from .Utils import getOS, isWin32Windows

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
        norm, and with it normalized, and turned absolute paths, it
        becomes a mere string compare after that.
        is no differences.
    """

    path1 = os.path.normcase(os.path.abspath(os.path.normpath(path1)))
    path2 = os.path.normcase(os.path.abspath(os.path.normpath(path2)))

    return path1 == path2


def haveSameFileContents(path1, path2):
    # Local import, to avoid this for normal use cases.
    import filecmp

    return filecmp.cmp(path1, path2)


def getFileSize(path):
    return os.path.getsize(path)


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
        if getOS() == "Windows":
            return os.path.abspath(path)
        raise


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
            os.makedirs(path)


def _getRealPathWindows(path):
    # Slow, because we are using an external process, we it's only for standalone and Python2,
    # which is slow already.
    import subprocess

    result = subprocess.check_output(
        """powershell -NoProfile "Get-Item '%s' | Select-Object -ExpandProperty Target" """
        % path
    )

    if str is not bytes:
        result = result.decode("utf8")

    return os.path.join(os.path.dirname(path), result.rstrip("\r\n"))


def getDirectoryRealPath(path):
    """Get os.path.realpath with Python2 and Windows symlink workaround applied.

    Args:
        path: path to get realpath of

    Returns:
        path with symlinks resolved

    Notes:
        Workaround for Windows symlink is applied.

    """
    path = os.path.realpath(path)

    # Attempt to resolve Windows symlinks on Python2
    if os.name == "nt" and not os.path.isdir(path):
        path = _getRealPathWindows(path)

    return path


def listDir(path):
    """Give a sorted listing of a path.

    Args:
        path: directory to create a listing from

    Returns:
        Sorted list of tuples of full filename, and basename of
        a directory.

    Notes:
        Typically the full name and the basename are both needed
        so this function simply does both, for ease of use on the
        calling side.

        This should be used, because it makes sure to resolve the
        symlinks to directories on Windows, that a naive "os.listdir"
        won't do by default.
    """
    real_path = getDirectoryRealPath(path)

    return sorted(
        [(os.path.join(path, filename), filename) for filename in os.listdir(real_path)]
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
        path: directory to create a recurseive listing from
        ignore_dirs: Don't descend into these directory, ignore them
        ignore_filenames: Ignore files named exactly like this
        ignore_suffixes: Don't return files with these suffixes
        only_suffixes: If not empty, limit returned files to these suffixes

    Returns:
        Sorted list of all filenames below that directory,
        relative to it.

    Notes:
        This function descends into directories, but does
        not follow symlinks.
    """
    # We work with a lot of details here, pylint: disable=too-many-locals

    result = []

    # Normalize ignoredirs for better matching.
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

        # Normalize filenames for better matching.
        filenames_normalized = [os.path.normcase(filename) for filename in filenames]
        for ignore_filename in ignore_filenames:
            if ignore_filename in filenames_normalized:
                filenames.remove(ignore_filename)

        for filename in filenames:
            if os.path.normcase(filename).endswith(ignore_suffixes):
                continue

            if only_suffixes and not os.path.normcase(filename).endswith(only_suffixes):
                continue

            fullname = os.path.join(root, filename)

            if normalize:
                fullname = os.path.normpath(fullname)

            result.append(fullname)

    return result


def getSubDirectories(path, ignore_dirs=()):
    """Get all directories below a given path.

    Args:
        path: directory to create a recurseive listing from

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
            result.append(os.path.join(root, dirname))

    result.sort()
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
        if os.path.islink(path) or os.path.isfile(path):
            try:
                os.unlink(path)
            except OSError:
                if must_exist:
                    raise
        elif must_exist:
            raise OSError("Does not exist", path)


def splitPath(path):
    """Split path, skipping empty elements."""
    return tuple(element for element in os.path.split(path) if element)


def hasFilenameExtension(path, extensions):
    """Has a filename one of the given extensions."""

    extension = os.path.splitext(os.path.normcase(path))[1]

    return extension in extensions


def removeDirectory(path, ignore_errors):
    """Remove a directory recursively.

    On Windows, it happens that operations fail, and succeed when reried,
    so added a retry and small delay, then another retry. Should make it
    much more stable during tests.

    All kinds of programs that scan files might cause this, but they do
    it hopefully only briefly.
    """

    def onError(func, path, exc_info):
        # Try again immediately, ignore what happened, pylint: disable=unused-argument
        try:
            func(path)
        except OSError:
            time.sleep(0.1)

        func(path)

    with withFileLock("removing directory %s" % path):
        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=False, onerror=onError)
            except OSError:
                if ignore_errors:
                    shutil.rmtree(path, ignore_errors=ignore_errors)
                else:
                    raise


@contextmanager
def withTemporaryFile(suffix="", mode="w", delete=True):
    with tempfile.NamedTemporaryFile(
        suffix=suffix, mode=mode, delete=delete
    ) as temp_file:
        yield temp_file


def getFileContentByLine(filename, mode="r", encoding=None):
    # We read the whole, to keep lock times minimal. We only deal with small
    # files like this normally.
    return getFileContents(filename, mode, encoding=encoding).splitlines()


def getFileContents(filename, mode="r", encoding=None):
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
            return f.read()


def openTextFile(filename, mode, encoding=None):
    if encoding is not None:
        import codecs

        return codecs.open(filename, mode, encoding=encoding)
    else:
        return open(filename, mode)


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
            print(contents, file=output_file)
        else:
            for line in contents:
                print(line, file=output_file)

    with withFileLock("writing file %s" % filename):
        with openTextFile(filename, "w", encoding=encoding) as output_file:
            _writeContents(output_file)


@contextmanager
def withPreserveFileMode(filename):
    old_mode = os.stat(filename).st_mode
    yield
    os.chmod(filename, old_mode)


@contextmanager
def withMadeWritableFileMode(filename):
    with withPreserveFileMode(filename):
        os.chmod(filename, int("644", 8))
        yield


def removeFileExecutablePermission(filename):
    old_stat = os.stat(filename)

    mode = old_stat.st_mode
    mode &= ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if mode != old_stat.st_mode:
        os.chmod(filename, mode)


def addFileExecutablePermission(filename):
    old_stat = os.stat(filename)

    mode = old_stat.st_mode
    mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

    if mode != old_stat.st_mode:
        os.chmod(filename, mode)


def renameFile(source_filename, dest_filename):
    # There is no way to safely update a file on Windows, but lets
    # try on Linux at least.
    old_stat = os.stat(source_filename)

    try:
        os.rename(source_filename, dest_filename)
    except OSError:
        shutil.copyfile(source_filename, dest_filename)
        os.unlink(source_filename)

    os.chmod(dest_filename, old_stat.st_mode)


def copyTree(source_path, dest_path):
    """Copy whole directory tree, preserving attributes.

    Args:
        source_path: where to copy from
        dest_path: where to copy to, may already exist

    Notes:
        This must be used over `shutil.copytree` which as troubles
        with existing directories.
    """

    # False alarm on travis, pylint: disable=I0021,import-error,no-name-in-module
    from distutils.dir_util import copy_tree

    return copy_tree(source_path, dest_path)


def getWindowsDrive(path):
    """Windows drive for a given path."""

    drive, _ = os.path.splitdrive(os.path.abspath(path))
    return os.path.normcase(drive)


def isPathBelow(path, filename):
    path = os.path.abspath(path)
    filename = os.path.abspath(filename)

    if isWin32Windows():
        if getWindowsDrive(path) != getWindowsDrive(filename):
            return False

    return os.path.relpath(filename, path).split(os.path.sep)[0] != ".."


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
    GetShortPathNameW.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD,
    ]
    GetShortPathNameW.restype = ctypes.wintypes.DWORD

    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = GetShortPathNameW(
            os.path.abspath(filename), output_buf, output_buf_size
        )

        if needed == 0:
            # Windows only code, pylint: disable=I0021,undefined-variable

            raise WindowsError(
                ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError())
            )

        if output_buf_size >= needed:
            # Short paths should be ASCII. Don't return unicode without a need,
            # as e.g. Scons hates that in environment variables.
            if str is bytes:
                return output_buf.value.encode("utf8")
            else:
                return output_buf.value
        else:
            output_buf_size = needed


def getExternalUsePath(filename, only_dirname=False):
    """Gets the externally usable absolute path for a given relative path.

    Args:
        filename - filename, potentially relative
    Returns:
        Path that is a absolute and (on Windows) short filename pointing at the same file.
    Notes:
        This is only os.path.abspath except on Windows, where is coverts
        to a short path too.
    """

    filename = os.path.abspath(filename)

    if os.name == "nt":
        if only_dirname:
            dirname = getWindowsShortPathName(os.path.dirname(filename))
            assert os.path.exists(dirname)
            filename = os.path.join(dirname, os.path.basename(filename))
        else:
            filename = getWindowsShortPathName(filename)

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

        filename = os.path.join(os.path.dirname(filename), link_target)
        is_link = True

    return is_link, filename


def replaceFileAtomic(source_path, dest_path):
    """
    Move ``src`` to ``dst``. If ``dst`` exists, it will be silently
    overwritten.

    Both paths must reside on the same filesystem for the operation to be
    atomic.
    """

    if python_version >= 0x300:
        os.replace(source_path, dest_path)
    else:
        importFromInlineCopy("atomicwrites", must_exist=True).replace_atomic(
            source_path, dest_path
        )


def resolveShellPatternToFilenames(pattern):
    """Resolve shell pattern to filenames.

    Args:
        pattern - str

    Returns:
        list - filenames that matched.
    """

    result = glob.glob(pattern)
    result.sort()
    return result


@contextmanager
def withDirectoryChange(path, allow_none=False):
    """Change current directory temporarily in a context."""

    if path is not None or not allow_none:
        old_cwd = os.getcwd()
        os.chdir(path)

    yield

    if path is not None or not allow_none:
        os.chdir(old_cwd)
