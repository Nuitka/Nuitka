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
""" Postprocessing tasks for create binaries or modules.

"""

import os
import shutil
import stat
import sys

from nuitka import Options
from nuitka.codegen import ConstantCodes
from nuitka.PythonVersions import (
    getPythonABI,
    getTargetPythonDLLPath,
    python_version,
)
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    callInstallNameToolAddRPath,
)
from nuitka.utils.Utils import getOS, isWin32Windows
from nuitka.utils.WindowsResources import (
    RT_MANIFEST,
    RT_RCDATA,
    addResourceToFile,
    copyResourcesFromFileToFile,
)


def executePostProcessing(result_filename):
    if not os.path.exists(result_filename):
        sys.exit(
            "Error, scons failed to create the expected file '%s'. " % result_filename
        )

    if isWin32Windows():
        # Copy the Windows manifest from the CPython binary to the created
        # executable, so it finds "MSCRT.DLL". This is needed for Python2
        # only, for Python3 newer MSVC doesn't hide the C runtime.
        if python_version < 300 and not Options.shallMakeModule():
            copyResourcesFromFileToFile(
                sys.executable,
                target_filename=result_filename,
                resource_kind=RT_MANIFEST,
            )

        assert os.path.exists(result_filename)

        # Attach the binary blob as a Windows resource.
        addResourceToFile(
            target_filename=result_filename,
            data=ConstantCodes.stream_data.getBytes(),
            resource_kind=RT_RCDATA,
            res_name=3,
            lang_id=0,
        )

    # On macOS, we update the executable path for searching the "libpython"
    # library.
    if (
        getOS() == "Darwin"
        and not Options.shallMakeModule()
        and not Options.shallUseStaticLibPython()
    ):
        python_version_str = ".".join(str(s) for s in sys.version_info[0:2])
        python_abi_version = python_version_str + getPythonABI()
        python_dll_filename = "libpython" + python_abi_version + ".dylib"
        python_lib_path = os.path.join(sys.prefix, "lib")

        if os.path.exists(os.path.join(sys.prefix, "conda-meta")):
            callInstallNameToolAddRPath(result_filename, python_lib_path)

        callInstallNameTool(
            filename=result_filename,
            mapping=(
                (
                    python_dll_filename,
                    os.path.join(python_lib_path, python_dll_filename),
                ),
            ),
        )

    # Modules should not be executable, but Scons creates them like it, fix
    # it up here.
    if not isWin32Windows() and Options.shallMakeModule():
        old_stat = os.stat(result_filename)

        mode = old_stat.st_mode
        mode &= ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if mode != old_stat.st_mode:
            os.chmod(result_filename, mode)

    if isWin32Windows() and Options.shallMakeModule():
        candidate = os.path.join(
            os.path.dirname(result_filename),
            "lib" + os.path.basename(result_filename)[:-4] + ".a",
        )

        if os.path.exists(candidate):
            os.unlink(candidate)

    if isWin32Windows() and Options.shallTreatUninstalledPython():
        shutil.copy(getTargetPythonDLLPath(), os.path.dirname(result_filename) or ".")
