#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Utility module.

Here the small things for file/dir names, Python version, CPU counting,
memory usage, etc. that fit nowhere else and don't deserve their own names.

"""

import os
import subprocess
import sys

from nuitka.PythonVersions import python_version


def getOS():
    if os.name == "nt":
        return "Windows"
    elif os.name == "posix":
        return os.uname()[0]  # @UndefinedVariable
    else:
        assert False, os.name


def getArchitecture():
    if getOS() == "Windows":
        if "AMD64" in sys.version:
            return "x86_64"
        else:
            return "x86"
    else:
        return os.uname()[4]  # @UndefinedVariable


def relpath(path):
    try:
        return os.path.relpath(path)
    except ValueError:
        # On Windows, paths on different devices prevent it to work. Use that
        # full path then.
        if getOS() == "Windows":
            return os.path.abspath(path)
        raise


def abspath(path):
    return os.path.abspath(path)


def isAbsolutePath(path):
    return os.path.isabs(path)


def joinpath(*parts):
    return os.path.join(*parts)


def splitpath(path):
    return tuple(
        element
        for element in
        os.path.split(path)
        if element
    )


def basename(path):
    return os.path.basename(path)


def dirname(path):
    return os.path.dirname(path)


def normpath(path):
    return os.path.normpath(path)


def realpath(path):
    return os.path.realpath(path)


def normcase(path):
    return os.path.normcase(path)


def getExtension(path):
    return os.path.splitext(path)[1]


def isFile(path):
    return os.path.isfile(path)


def isDir(path):
    return os.path.isdir(path)


def isLink(path):
    return os.path.islink(path)


def areSamePaths(path1, path2):
    path1 = normcase(abspath(normpath(path1)))
    path2 = normcase(abspath(normpath(path2)))

    return path1 == path2


def readLink(path):
    return os.readlink(path)  # @UndefinedVariable


def listDir(path):
    """ Give a sorted path, base filename pairs of a directory."""

    return sorted(
        [
            (
                joinpath(path, filename),
                filename
            )
            for filename in
            os.listdir(path)
        ]
    )


def getFileList(path):
    for root, _dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield joinpath(root, filename)


def deleteFile(path, must_exist):
    if must_exist or isFile(path):
        os.unlink(path)


def makePath(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def getCoreCount():
    cpu_count = 0

    # Try to sum up the CPU cores, if the kernel shows them.
    try:
        # Try to get the number of logical processors
        with open("/proc/cpuinfo") as cpuinfo_file:
            cpu_count = cpuinfo_file.read().count("processor\t:")
    except IOError:
        pass

    if not cpu_count:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()

    return cpu_count


def callExec(args):
    """ Do exec in a portable way preserving exit code.

        On Windows, unfortunately there is no real exec, so we have to spawn
        a new process instead.
    """

    # On Windows os.execl does not work properly
    if getOS() != "Windows":
        # The star arguments is the API of execl
        os.execl(*args)
    else:
        args = list(args)
        del args[1]

        try:
            sys.exit(
                subprocess.call(args)
            )
        except KeyboardInterrupt:
            # There was a more relevant stack trace already, so abort this
            # right here, pylint: disable=W0212
            os._exit(2)


def encodeNonAscii(var_name):
    """ Encode variable name that is potentially not ASCII to ASCII only.

        For Python3, unicode identifiers can be used, but these are not
        possible in C++03, so we need to replace them.
    """
    if python_version < 300:
        return var_name
    else:
        # Using a escaping here, because that makes it safe in terms of not
        # to occur in the encoding escape sequence for unicode use.
        var_name = var_name.replace("$$", "$_$")

        var_name = var_name.encode("ascii", "xmlcharrefreplace")
        var_name = var_name.decode("ascii")

        return var_name.replace("&#", "$$").replace(';', "")


def isExecutableCommand(command):
    path = os.environ["PATH"]

    suffixes = (".exe",) if getOS() == "Windows" else ("",)

    for part in path.split(os.pathsep):
        if not part:
            continue

        for suffix in suffixes:
            if isFile(joinpath(part, command + suffix)):
                return True

    return False
