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
""" Postprocessing tasks for create binaries or modules.

"""

import os
import stat
import sys

from nuitka import Options
from nuitka.PythonVersions import python_version
from nuitka.utils.Utils import isWin32Windows
from nuitka.utils.WindowsResources import RT_MANIFEST, copyResourcesFromFileToFile


def executePostProcessing(result_filename):

    # Copy the Windows manifest from the CPython binary to the created
    # executable, so it finds "MSCRT.DLL". This is needed for Python2
    # only, for Python3 newer MSVC doesn't hide the C runtime.
    if python_version < 300:
        if isWin32Windows() and not Options.shallMakeModule():
            copyResourcesFromFileToFile(sys.executable, result_filename, RT_MANIFEST)

    # Modules should not be executable, but Scons creates them like it, fix
    # it up here.
    if not isWin32Windows() and Options.shallMakeModule():
        old_stat = os.stat(result_filename)

        mode = old_stat.st_mode
        mode &= ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if mode != old_stat.st_mode:
            os.chmod(result_filename, mode)
