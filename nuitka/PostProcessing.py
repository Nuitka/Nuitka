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
""" Postprocessing tasks for create binaries or modules.

"""

import ctypes
import os
import shutil
import sys

from nuitka import Options, OutputDirectories
from nuitka.build.DataComposerInterface import getConstantBlobFilename
from nuitka.PythonVersions import (
    getPythonABI,
    getTargetPythonDLLPath,
    python_version,
    python_version_str,
)
from nuitka.Tracing import postprocessing_logger
from nuitka.utils.FileOperations import (
    getFileContents,
    removeFileExecutablePermission,
)
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    callInstallNameToolAddRPath,
)
from nuitka.utils.Utils import getOS, isWin32Windows
from nuitka.utils.WindowsResources import (
    RT_GROUP_ICON,
    RT_ICON,
    RT_RCDATA,
    addResourceToFile,
    addVersionInfoResource,
    convertStructureToBytes,
    copyResourcesFromFileToFile,
    getDefaultWindowsExecutableManifest,
    getWindowsExecutableManifest,
)


class IconDirectoryHeader(ctypes.Structure):
    _fields_ = [
        ("reserved", ctypes.c_short),
        ("type", ctypes.c_short),
        ("count", ctypes.c_short),
    ]


class IconDirectoryEntry(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_char),
        ("height", ctypes.c_char),
        ("colors", ctypes.c_char),
        ("reserved", ctypes.c_char),
        ("planes", ctypes.c_short),
        ("bit_count", ctypes.c_short),
        ("image_size", ctypes.c_int),
        ("image_offset", ctypes.c_int),
    ]


class IconGroupDirectoryEntry(ctypes.Structure):
    _fields_ = (
        ("width", ctypes.c_char),
        ("height", ctypes.c_char),
        ("colors", ctypes.c_char),
        ("reserved", ctypes.c_char),
        ("planes", ctypes.c_short),
        ("bit_count", ctypes.c_short),
        ("image_size", ctypes.c_int),
        ("id", ctypes.c_int),
    )


def readFromFile(readable, c_struct):
    """ Read ctypes structures from input. """

    result = c_struct()
    chunk = readable.read(ctypes.sizeof(result))
    ctypes.memmove(ctypes.byref(result), chunk, ctypes.sizeof(result))
    return result


def addWindowsIconFromIcons():
    icon_group = 1
    image_id = 1
    images = []

    result_filename = OutputDirectories.getResultFullpath()

    for icon_path in Options.getIconPaths():
        with open(icon_path, "rb") as icon_file:
            # Read header and icon entries.
            header = readFromFile(icon_file, IconDirectoryHeader)
            icons = [
                readFromFile(icon_file, IconDirectoryEntry)
                for icon in range(header.count)
            ]

            # Image data are to be scanned from places specified icon entries
            for icon in icons:
                icon_file.seek(icon.image_offset, 0)
                images.append(icon_file.read(icon.image_size))

        parts = [convertStructureToBytes(header)]

        for icon in icons:
            parts.append(
                convertStructureToBytes(
                    IconGroupDirectoryEntry(
                        width=icon.width,
                        height=icon.height,
                        colors=icon.colors,
                        reserved=icon.reserved,
                        planes=icon.planes,
                        bit_count=icon.bit_count,
                        image_size=icon.image_size,
                        id=image_id,
                    )
                )
            )

            image_id += 1

        addResourceToFile(
            target_filename=result_filename,
            data=b"".join(parts),
            resource_kind=RT_GROUP_ICON,
            lang_id=0,
            res_name=icon_group,
            logger=postprocessing_logger,
        )

    for count, image in enumerate(images, 1):
        addResourceToFile(
            target_filename=result_filename,
            data=image,
            resource_kind=RT_ICON,
            lang_id=0,
            res_name=count,
            logger=postprocessing_logger,
        )


version_resources = {}


def executePostProcessing():
    # These is a bunch of stuff to consider, pylint: disable=too-many-branches

    result_filename = OutputDirectories.getResultFullpath()

    if not os.path.exists(result_filename):
        postprocessing_logger.sysexit(
            "Error, scons failed to create the expected file %r. " % result_filename
        )

    if isWin32Windows():
        if not Options.shallMakeModule():
            needs_manifest = False
            manifest = None

            if python_version < 0x300:
                # Copy the Windows manifest from the CPython binary to the created
                # executable, so it finds "MSCRT.DLL". This is needed for Python2
                # only, for Python3 newer MSVC doesn't hide the C runtime.
                manifest = getWindowsExecutableManifest(sys.executable)

                if manifest is not None:
                    needs_manifest = True

            if (
                Options.shallAskForWindowsAdminRights()
                or Options.shallAskForWindowsUIAccessRights()
            ):
                needs_manifest = True

                if manifest is None:
                    manifest = getDefaultWindowsExecutableManifest()

                if Options.shallAskForWindowsAdminRights():
                    manifest.addUacAdmin()

                if Options.shallAskForWindowsUIAccessRights():
                    manifest.addUacUiAccess()

            if needs_manifest:
                manifest.addResourceToFile(
                    result_filename, logger=postprocessing_logger
                )

        if (
            Options.getWindowsVersionInfoStrings()
            or Options.getWindowsProductVersion()
            or Options.getWindowsFileVersion()
        ):
            version_resources.update(
                addVersionInfoResource(
                    string_values=Options.getWindowsVersionInfoStrings(),
                    product_version=Options.getWindowsProductVersion(),
                    file_version=Options.getWindowsFileVersion(),
                    file_date=(0, 0),
                    is_exe=not Options.shallMakeModule(),
                    result_filename=result_filename,
                    logger=postprocessing_logger,
                )
            )

        source_dir = OutputDirectories.getSourceDirectoryPath()

        # Attach the binary blob as a Windows resource.
        addResourceToFile(
            target_filename=result_filename,
            data=getFileContents(getConstantBlobFilename(source_dir), "rb"),
            resource_kind=RT_RCDATA,
            res_name=3,
            lang_id=0,
            logger=postprocessing_logger,
        )

        # Attach icons from template file if given.
        template_exe = Options.getWindowsIconExecutablePath()
        if template_exe is not None:
            res_copied = copyResourcesFromFileToFile(
                template_exe,
                target_filename=result_filename,
                resource_kinds=(RT_ICON, RT_GROUP_ICON),
            )

            if res_copied == 0:
                postprocessing_logger.warning(
                    "The specified icon template executable %r didn't contain anything to copy."
                    % template_exe
                )
            else:
                postprocessing_logger.warning(
                    "Copied %d icon resources from %r." % (res_copied, template_exe)
                )
        else:
            addWindowsIconFromIcons()

    # On macOS, we update the executable path for searching the "libpython"
    # library.
    if (
        getOS() == "Darwin"
        and not Options.shallMakeModule()
        and not Options.shallUseStaticLibPython()
    ):
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
        removeFileExecutablePermission(result_filename)

    if isWin32Windows() and Options.shallMakeModule():
        candidate = os.path.join(
            os.path.dirname(result_filename),
            "lib" + os.path.basename(result_filename)[:-4] + ".a",
        )

        if os.path.exists(candidate):
            os.unlink(candidate)

    if isWin32Windows() and Options.shallTreatUninstalledPython():
        shutil.copy(getTargetPythonDLLPath(), os.path.dirname(result_filename) or ".")
