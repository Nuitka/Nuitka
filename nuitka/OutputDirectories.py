#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Directories and paths to for output of Nuitka.

There are two major outputs, the build directory *.build and for
standalone mode, the *.dist folder.

A bunch of functions here are supposed to get path resolution from
this.
"""

import os

from nuitka.Options import (
    getOutputFilename,
    getOutputFolderName,
    getOutputPath,
    getPgoExecutable,
    isOnefileMode,
    isStandaloneMode,
    shallCreateAppBundle,
    shallCreateScriptFileForExecution,
    shallMakeDll,
    shallMakeModule,
)
from nuitka.utils.FileOperations import (
    addFilenameExtension,
    changeFilenameExtension,
    getNormalizedPath,
    hasFilenameExtension,
    isFilesystemEncodable,
    makePath,
    putTextFileContents,
    removeDirectory,
    resetDirectory,
)
from nuitka.utils.Importing import getExtensionModuleSuffix
from nuitka.utils.SharedLibraries import getDllSuffix
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


# TODO: This is for compatibility for the hotfix, after Nuitka 2.8 release we can
# and should remove this.
def getSourceDirectoryPath(onefile=False, create=False):
    """Return path inside the build directory."""

    # Distinct build folders for onefile mode.
    if onefile:
        suffix = ".onefile-build"
    else:
        suffix = ".build"

    filename = os.path.basename(getTreeFilenameWithSuffix(_main_module, suffix))

    if isWin32Windows() and not isFilesystemEncodable(filename):
        filename = "_nuitka_temp" + suffix

    result = getOutputPath(path=filename)

    if create:
        makePath(result)

        git_ignore_filename = os.path.join(result, ".gitignore")

        if not os.path.exists(git_ignore_filename):
            putTextFileContents(filename=git_ignore_filename, contents="*")

    return result


def _getStandaloneDistSuffix(bundle):
    """Suffix to use for standalone distribution folder."""

    if bundle and shallCreateAppBundle() and not isOnefileMode():
        return ".app"
    else:
        return ".dist"


def _getActualOutputFolderName(bundle):
    dist_folder_name = getOutputFolderName()

    if dist_folder_name is None:
        dist_folder_name = os.path.basename(
            getTreeFilenameWithSuffix(_main_module, _getStandaloneDistSuffix(bundle))
        )
    else:
        # Add the suffix if not provided by the user
        standalone_dist_suffix = _getStandaloneDistSuffix(bundle)

        if not hasFilenameExtension(dist_folder_name, standalone_dist_suffix):
            dist_folder_name = changeFilenameExtension(
                dist_folder_name, standalone_dist_suffix
            )

    return dist_folder_name


def needsStandaloneDirectoryWorkaround():
    return isWin32Windows() and not isFilesystemEncodable(
        _getActualOutputFolderName(bundle=False)
    )


def getStandaloneDirectoryPath(bundle, real):
    assert isStandaloneMode()

    if needsStandaloneDirectoryWorkaround() and not real:
        dist_folder_name = "_nuitka_temp"
    else:
        dist_folder_name = _getActualOutputFolderName(bundle=bundle)

    result = getOutputPath(path=dist_folder_name)

    if bundle and shallCreateAppBundle() and not isOnefileMode():
        result = os.path.join(result, "Contents", "MacOS")

    return result


def initStandaloneDirectory(logger):
    """Reset the standalone directory, if it exists from a previous run."""
    standalone_dir = getStandaloneDirectoryPath(bundle=False, real=False)
    resetDirectory(
        path=standalone_dir,
        logger=logger,
        ignore_errors=True,
        extra_recommendation="Stop previous binary.",
    )

    standalone_dir_real = getStandaloneDirectoryPath(bundle=False, real=True)

    if standalone_dir != standalone_dir_real:
        removeDirectory(
            path=standalone_dir_real,
            logger=logger,
            ignore_errors=True,
            extra_recommendation="Stop previous binary.",
        )

        if shallCreateAppBundle():
            resetDirectory(
                path=changeFilenameExtension(standalone_dir_real, ".app"),
                logger=logger,
                ignore_errors=True,
                extra_recommendation=None,
            )


def renameStandaloneDirectory(dist_dir):
    if needsStandaloneDirectoryWorkaround():
        dist_dir_real = getStandaloneDirectoryPath(bundle=True, real=True)

        os.rename(dist_dir, dist_dir_real)
        dist_dir = dist_dir_real

    return dist_dir


def getResultBasePath(onefile=False, real=False):
    file_path = os.path.basename(getTreeFilenameWithSuffix(_main_module, ""))

    if isOnefileMode() and onefile:
        if shallCreateAppBundle():
            file_path = os.path.join(file_path + ".app", "Contents", "MacOS", file_path)

        return getOutputPath(path=file_path)
    elif isStandaloneMode() and not onefile:
        return os.path.join(
            getStandaloneDirectoryPath(bundle=True, real=real),
            file_path,
        )
    else:
        return getOutputPath(path=file_path)


def getResultFullpath(onefile, real):
    """Get the final output binary result full path."""

    result = getResultBasePath(onefile=onefile, real=real)

    if shallMakeModule():
        result += getExtensionModuleSuffix(preferred=True)
    elif shallMakeDll() and not onefile:
        # TODO: Could actually respect getOutputFilename() for DLLs, these don't
        # need to be named in a specific way.
        result += getDllSuffix()
    else:
        output_filename = getOutputFilename()

        if isOnefileMode() and output_filename is not None:
            if onefile:
                result = getOutputPath(output_filename)
            else:
                result = os.path.join(
                    getStandaloneDirectoryPath(bundle=True, real=real),
                    os.path.basename(output_filename),
                )
        elif isStandaloneMode() and output_filename is not None:
            result = os.path.join(
                getStandaloneDirectoryPath(bundle=True, real=real),
                os.path.basename(output_filename),
            )
        elif output_filename is not None:
            result = getOutputPath(output_filename)
        elif not isWin32OrPosixWindows() and not shallCreateAppBundle():
            result = addFilenameExtension(result, ".bin")

        if isWin32OrPosixWindows():
            result = addFilenameExtension(result, ".exe")

        if not isWin32OrPosixWindows() and isOnefileMode() and not onefile:
            result = addFilenameExtension(result, ".bin")

    return getNormalizedPath(result)


def getResultRunFilename(onefile):
    result = getResultFullpath(onefile=onefile, real=True)

    if shallCreateScriptFileForExecution():
        result = getResultBasePath(onefile=onefile) + (
            ".cmd" if isWin32Windows() else ".sh"
        )

    return result


def getTreeFilenameWithSuffix(module, suffix):
    return module.getOutputFilename() + suffix


def getPgoRunExecutable():
    return getPgoExecutable() or getResultRunFilename(onefile=False)


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
