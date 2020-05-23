#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
stuff. It will also frequently add sorting.

"""

import os
import shutil
import tempfile
import time
from contextlib import contextmanager

from nuitka.Tracing import my_print

from .ThreadedExecutor import RLock, getThreadIdent
from .Utils import getOS

# Locking seems to be only required for Windows mostly, but we can keep
# it for all.
file_lock = None

# Use this in case of dead locks or even to see file operations being done.
_lock_tracing = False


@contextmanager
def withFileLock(reason="unknown"):
    # This is a singleton, pylint: disable=global-statement
    global file_lock

    if file_lock is None:
        file_lock = RLock()

    if _lock_tracing:
        my_print(getThreadIdent(), "Want file lock for %s" % reason)
    file_lock.acquire()
    if _lock_tracing:
        my_print(getThreadIdent(), "Acquired file lock for %s" % reason)
    yield
    if _lock_tracing:
        my_print(getThreadIdent(), "Released file lock for %s" % reason)
    if file_lock is not None:
        file_lock.release()


def areSamePaths(path1, path2):
    """ Decide if two paths the same.

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


def relpath(path, start="."):
    """ Make it a relative path, if possible.

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
    """ Create a directory if it doesn't exist.

    Args:
        path: path to create as a directory

    Notes:
        This also is thread safe on Windows, i.e. no race is
        possible.

    """

    with withFileLock("creating directory %s" % path):
        if not os.path.isdir(path):
            os.makedirs(path)


def listDir(path):
    """ Give a sorted listing of a path.

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

    return sorted(
        [
            (os.path.join(path, filename), filename)
            for filename in os.listdir(os.path.realpath(path))
        ]
    )


def getFileList(path, ignore_dirs=(), ignore_suffixes=()):
    """ Get all files below a given path.

    Args:
        path: directory to create a recurseive listing from
        ignore_dirs: Don't descend into these directory, ignore them
        ignore_suffixes: Don't return files with these suffixes


    Returns:
        Sorted list of all filenames below that directory,
        relative to it.

    Notes:
        This function descends into directories, but does
        not follow symlinks.
    """
    result = []

    for root, dirnames, filenames in os.walk(path):
        dirnames.sort()
        filenames.sort()

        for dirname in ignore_dirs:
            if dirname in dirnames:
                dirnames.remove(dirname)

        for filename in filenames:
            if filename.endswith(ignore_suffixes):
                continue

            result.append(os.path.normpath(os.path.join(root, filename)))

    return result


def getSubDirectories(path):
    """ Get all directories below a given path.

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

    for root, dirnames, _filenames in os.walk(path):
        dirnames.sort()

        for dirname in dirnames:
            result.append(os.path.join(root, dirname))

    result.sort()
    return result


def deleteFile(path, must_exist):
    """ Delete a file, potentially making sure it exists.

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
    """ Split path, skipping empty elements. """
    return tuple(element for element in os.path.split(path) if element)


def hasFilenameExtension(path, extensions):
    extension = os.path.splitext(os.path.normcase(path))[1]

    return extension in extensions


def removeDirectory(path, ignore_errors):
    """ Remove a directory recursively.

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
    with withFileLock("reading file %s" % filename):
        if encoding is not None:
            import codecs

            with codecs.open(filename, mode, encoding=encoding) as f:
                return f.read()
        else:
            with open(filename, mode) as f:
                return f.read()


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
    """ Copy whole directory tree, preserving attributes.

    Args:
        source_path: where to copy from
        dest_path: where to copy to, may already exist

    Notes:
        This must be used over `shutil.copytree` which as troubles
        with existing directories.
    """

    # False alarm on travis, pylint: disable=I0021,import-error,no-name-in-module
    from distutils.dir_util import copy_tree

    copy_tree(source_path, dest_path)


def isPathBelow(path, filename):
    path = os.path.abspath(path)
    filename = os.path.abspath(filename)

    return os.path.relpath(filename, path)[:3].split(os.path.sep) != ".."


def getWindowsShortPathName(filename):
    """ Gets the short path name of a given long path.

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
        needed = GetShortPathNameW(filename, output_buf, output_buf_size)

        if needed == 0:
            # Windows only code, pylint: disable=I0021,undefined-variable

            raise WindowsError(
                ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError())
            )

        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def getExternalUsePath(filename, only_dirname=False):
    """ Gets the externally usable absolute path for a given relative path.

    Args:
        filename - filename, potentially relative
    Returns:
        Path that is a absolute and (on Windows) short filename pointing at the same file.
    Notes:
        Except on Windows, this is merely os.path.abspath, there is coverts
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
