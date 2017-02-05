#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.utils.Utils import getOS


def areSamePaths(path1, path2):
    path1 = os.path.normcase(os.path.abspath(os.path.normpath(path1)))
    path2 = os.path.normcase(os.path.abspath(os.path.normpath(path2)))

    return path1 == path2


def relpath(path):
    """ Relative path, if possible. """

    try:
        return os.path.relpath(path)
    except ValueError:
        # On Windows, paths on different devices prevent it to work. Use that
        # full path then.
        if getOS() == "Windows":
            return os.path.abspath(path)
        raise


def makePath(path):
    """ Create a directory if it doesn'T exist."""

    if not os.path.isdir(path):
        os.makedirs(path)


def listDir(path):
    """ Give a sorted path, base filename pairs of a directory."""

    return sorted(
        [
            (
                os.path.join(path, filename),
                filename
            )
            for filename in
            os.listdir(path)
        ]
    )


def getFileList(path):
    for root, _dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(root, filename)



def getSubDirectories(path):
    result = []

    for root, dirnames, _filenames in os.walk(path):
        for dirname in dirnames:
            result.append(
                os.path.join(root, dirname)
            )

    result.sort()
    return result


def deleteFile(path, must_exist):
    if must_exist or os.path.isfile(path):
        os.unlink(path)


def splitPath(path):
    """ Split path, skipping empty elements. """
    return tuple(
        element
        for element in
        os.path.split(path)
        if element
    )


def hasFilenameExtension(path, extensions):
    extension = os.path.splitext(os.path.normcase(path))[1]

    return extension in extensions

def removeDirectory(path, ignore_errors):
    shutil.rmtree(path, ignore_errors)
