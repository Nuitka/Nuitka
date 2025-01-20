#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Directories and paths to for output of Nuitka.

There are two major outputs, the build directory *.build and for
standalone mode, the *.dist folder.

A bunch of functions here are supposed to get path resolution from
this.
"""

import os

from nuitka import Options
from nuitka.utils.FileOperations import (
    addFilenameExtension,
    getNormalizedPath,
    makePath,
    putTextFileContents,
)
from nuitka.utils.Importing import getSharedLibrarySuffix
from nuitka.utils.Utils import isWin32OrPosixWindows, isWin32Windows

_main_module = None


def setMainModule(main_module):
    """Call this before using other methods of this module."""
    # Technically required.
    assert main_module.isCompiledPythonModule()

    # Singleton and to avoid passing this one all the time, pylint: disable=global-statement
    global _main_module
    _main_module = main_module


def hasMainModule():
    """For reporting to check if there is anything to talk about."""
    return _main_module is not None


def getMainModule():
    return _main_module


def getSourceDirectoryPath(onefile=False):
    """Return path inside the build directory."""

    # Distinct build folders for onefile mode.
    if onefile:
        suffix = ".onefile-build"
    else:
        suffix = ".build"

    result = Options.getOutputPath(
        path=os.path.basename(getTreeFilenameWithSuffix(_main_module, suffix))
    )

    makePath(result)

    git_ignore_filename = os.path.join(result, ".gitignore")

    if not os.path.exists(git_ignore_filename):
        putTextFileContents(filename=git_ignore_filename, contents="*")

    return result


def _getStandaloneDistSuffix(bundle):
    """Suffix to use for standalone distribution folder."""

    if bundle and Options.shallCreateAppBundle() and not Options.isOnefileMode():
        return ".app"
    else:
        return ".dist"


def getStandaloneDirectoryPath(bundle=True):
    assert Options.isStandaloneMode()

    result = Options.getOutputPath(
        path=os.path.basename(
            getTreeFilenameWithSuffix(_main_module, _getStandaloneDistSuffix(bundle))
        )
    )

    if bundle and Options.shallCreateAppBundle() and not Options.isOnefileMode():
        result = os.path.join(result, "Contents", "MacOS")

    return result


def getResultBasePath(onefile=False):
    if Options.isOnefileMode() and onefile:
        file_path = os.path.basename(getTreeFilenameWithSuffix(_main_module, ""))

        if Options.shallCreateAppBundle():
            file_path = os.path.join(file_path + ".app", "Contents", "MacOS", file_path)

        return Options.getOutputPath(path=file_path)
    elif Options.isStandaloneMode() and not onefile:
        return os.path.join(
            getStandaloneDirectoryPath(),
            os.path.basename(getTreeFilenameWithSuffix(_main_module, "")),
        )
    else:
        return Options.getOutputPath(
            path=os.path.basename(getTreeFilenameWithSuffix(_main_module, ""))
        )


def getResultFullpath(onefile):
    """Get the final output binary result full path."""

    result = getResultBasePath(onefile=onefile)

    if Options.shallMakeModule():
        result += getSharedLibrarySuffix(preferred=True)
    else:
        output_filename = Options.getOutputFilename()

        if Options.isOnefileMode() and output_filename is not None:
            if onefile:
                result = Options.getOutputPath(output_filename)
            else:
                result = os.path.join(
                    getStandaloneDirectoryPath(),
                    os.path.basename(output_filename),
                )
        elif Options.isStandaloneMode() and output_filename is not None:
            result = os.path.join(
                getStandaloneDirectoryPath(),
                os.path.basename(output_filename),
            )
        elif output_filename is not None:
            result = output_filename
        elif not isWin32OrPosixWindows() and not Options.shallCreateAppBundle():
            result = addFilenameExtension(result, ".bin")

        if isWin32OrPosixWindows():
            result = addFilenameExtension(result, ".exe")

        if not isWin32OrPosixWindows() and Options.isOnefileMode() and not onefile:
            result = addFilenameExtension(result, ".bin")

    return getNormalizedPath(result)


def getResultRunFilename(onefile):
    result = getResultFullpath(onefile=onefile)

    if Options.shallCreateScriptFileForExecution():
        result = getResultBasePath(onefile=onefile) + (
            ".cmd" if isWin32Windows() else ".sh"
        )

    return result


def getTreeFilenameWithSuffix(module, suffix):
    return module.getOutputFilename() + suffix


def getPgoRunExecutable():
    return Options.getPgoExecutable() or getResultRunFilename(onefile=False)


def getPgoRunInputFilename():
    return getPgoRunExecutable() + ".nuitka-pgo"


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
