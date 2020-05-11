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
""" Directories and paths to for output of Nuitka.

There are two major outputs, the build directory *.build and for
standalone mode, the *.dist folder.

A bunch of functions here are supposed to get path resolution from
this.
"""

import os

from nuitka import Options
from nuitka.utils import FileOperations, Utils

_main_module = None


def setMainModule(main_module):
    """ Call this before using other methods of this module.

    """
    # Technically required.
    assert main_module.isCompiledPythonModule()

    # Singleton and to avoid passing this one all the time, pylint: disable=global-statement
    global _main_module
    _main_module = main_module


def getSourceDirectoryPath():
    """ Return path inside the build directory.

    """

    result = Options.getOutputPath(
        path=os.path.basename(getTreeFilenameWithSuffix(_main_module, ".build"))
    )

    FileOperations.makePath(result)

    return result


def getStandaloneDirectoryPath():
    return Options.getOutputPath(
        path=os.path.basename(getTreeFilenameWithSuffix(_main_module, ".dist"))
    )


def getResultBasepath():
    if Options.isStandaloneMode():
        return os.path.join(
            getStandaloneDirectoryPath(),
            os.path.basename(getTreeFilenameWithSuffix(_main_module, "")),
        )
    else:
        return Options.getOutputPath(
            path=os.path.basename(getTreeFilenameWithSuffix(_main_module, ""))
        )


def getResultFullpath():
    """ Get the final output binary result full path.

    """

    result = getResultBasepath()

    if Options.shallMakeModule():
        result += Utils.getSharedLibrarySuffix()
    else:
        if Options.getOutputFilename() is not None:
            result = Options.getOutputFilename()
        elif Utils.getOS() == "Windows":
            result += ".exe"
        elif not Options.isStandaloneMode():
            result += ".bin"

    return result


def getTreeFilenameWithSuffix(module, suffix):
    return module.getOutputFilename() + suffix
