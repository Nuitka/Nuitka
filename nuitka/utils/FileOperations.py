#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ThreadedExecutor import Lock
from .Utils import getOS

# Locking seems to be only required for Windows currently, expressed that in the
# lock name.
file_lock = None


@contextmanager
def _with_file_Lock():
    # This is a singleton, pylint: disable=global-statement
    global file_lock

    if file_lock is None:
        file_lock = Lock()

    file_lock.acquire()
    yield
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


def relpath(path):
    """ Make it a relative path, if possible.

    Args:
        path: path to work on

    Returns:
        Changed path, pointing to the same path relative to current
        directory if possible.

    Notes:
        On Windows, a relative path is not possible across device
        names, therefore it may have to return the absolute path
        instead.
    """

    try:
        return os.path.relpath(path)
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

    with _with_file_Lock():
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
    """

    return sorted(
        [(os.path.join(path, filename), filename) for filename in os.listdir(path)]
    )


def getFileList(path):
    """ Get all files below a given path.

    Args:
        path: directory to create a recurseive listing from

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

        for filename in filenames:
            result.append(os.path.join(root, filename))

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
    with _with_file_Lock():
        if must_exist or os.path.isfile(path):
            os.unlink(path)


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

    with _with_file_Lock():
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


def getFileContentByLine(filename, mode="r"):
    with open(filename, mode) as f:
        return f.readlines()


def getFileContents(filename):
    with open(filename, "r") as f:
        return f.read()


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

    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW  # @UndefinedVariable
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
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed
