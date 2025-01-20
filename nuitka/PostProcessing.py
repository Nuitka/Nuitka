#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Postprocessing tasks for create binaries or modules.

"""

import ctypes
import os
import sys

from nuitka import Options, OutputDirectories
from nuitka.build.DataComposerInterface import getConstantBlobFilename
from nuitka.ModuleRegistry import getImportedModuleNames
from nuitka.PythonFlavors import isSelfCompiledPythonUninstalled
from nuitka.PythonVersions import getTargetPythonDLLPath, python_version
from nuitka.Tracing import postprocessing_logger
from nuitka.utils.Execution import wrapCommandForDebuggerForExec
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    getFileContents,
    getFileSize,
    hasFilenameExtension,
    makeFilesystemEncodable,
    makePath,
    putTextFileContents,
    removeFileExecutablePermission,
)
from nuitka.utils.Images import convertImageToIconFormat
from nuitka.utils.Importing import importFromInlineCopy
from nuitka.utils.MacOSApp import createPlistInfoFile
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    cleanupHeaderForAndroid,
    getOtoolDependencyOutput,
    parseOtoolListingOutput,
)
from nuitka.utils.Utils import isAndroidBasedLinux, isMacOS, isWin32Windows
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
    # Make sure the don't have padding issues.
    _pack_ = 2

    _fields_ = (
        ("width", ctypes.c_char),
        ("height", ctypes.c_char),
        ("colors", ctypes.c_char),
        ("reserved", ctypes.c_char),
        ("planes", ctypes.c_short),
        ("bit_count", ctypes.c_short),
        ("image_size", ctypes.c_int),
        ("id", ctypes.c_short),
    )


def readFromFile(readable, c_struct):
    """Read ctypes structures from input."""

    result = c_struct()
    chunk = readable.read(ctypes.sizeof(result))
    ctypes.memmove(ctypes.byref(result), chunk, ctypes.sizeof(result))
    return result


def _addWindowsIconFromIcons(onefile):
    # Relatively detailed handling, pylint: disable=too-many-locals

    icon_group = 1
    image_id = 1
    images = []

    result_filename = OutputDirectories.getResultFullpath(onefile=onefile)

    for icon_spec in Options.getWindowsIconPaths():
        if "#" in icon_spec:
            icon_path, icon_index = icon_spec.rsplit("#", 1)
            icon_index = int(icon_index)
        else:
            icon_path = icon_spec
            icon_index = None

        if not hasFilenameExtension(icon_path, ".ico"):
            postprocessing_logger.info(
                "File '%s' is not in Windows icon format, converting to it." % icon_path
            )

            if icon_index is not None:
                postprocessing_logger.sysexit(
                    "Cannot specify indexes with non-ico format files in '%s'."
                    % icon_spec
                )

            icon_build_path = os.path.join(
                OutputDirectories.getSourceDirectoryPath(onefile=onefile),
                "icons",
            )
            makePath(icon_build_path)
            converted_icon_path = os.path.join(
                icon_build_path,
                "icon-%d.ico" % image_id,
            )

            convertImageToIconFormat(
                logger=postprocessing_logger,
                image_filename=icon_spec,
                converted_icon_filename=converted_icon_path,
            )

            icon_path = converted_icon_path

        with open(icon_path, "rb") as icon_file:
            # Read header and icon entries.
            header = readFromFile(icon_file, IconDirectoryHeader)
            icons = [
                readFromFile(icon_file, IconDirectoryEntry)
                for _i in range(header.count)
            ]

            if icon_index is not None:
                if icon_index > len(icons):
                    postprocessing_logger.sysexit(
                        "Error, referenced icon index %d in file '%s' with only %d icons."
                        % (icon_index, icon_path, len(icons))
                    )

                icons[:] = icons[icon_index : icon_index + 1]

            postprocessing_logger.info(
                "Adding %d icon(s) from icon file '%s'." % (len(icons), icon_spec)
            )

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


def createScriptFileForExecution(result_filename):
    script_filename = OutputDirectories.getResultRunFilename(onefile=False)

    # TODO: This is probably a prefix kind that should be used more often, e.g.
    # in reporting.
    if isSelfCompiledPythonUninstalled():
        sys_prefix = os.path.dirname(sys.executable)
    else:
        sys_prefix = sys.prefix

    python_home = makeFilesystemEncodable(sys_prefix)
    python_path = os.pathsep.join(makeFilesystemEncodable(e) for e in sys.path)

    debugger_call = (
        (" ".join(wrapCommandForDebuggerForExec(command=())) + " ")
        if Options.shallRunInDebugger()
        else ""
    )
    exe_filename = os.path.basename(makeFilesystemEncodable(result_filename))

    if isWin32Windows():
        script_contents = """
@echo off
rem This script was created by Nuitka to execute '%(exe_filename)s' with Python DLL being found.
set PATH=%(dll_directory)s;%%PATH%%
set PYTHONHOME=%(python_home)s
set NUITKA_PYTHONPATH=%(python_path)s
%(debugger_call)s"%%~dp0%(exe_filename)s" %%*
""" % {
            "debugger_call": debugger_call,
            "dll_directory": makeFilesystemEncodable(
                os.path.dirname(getTargetPythonDLLPath())
            ),
            "python_home": python_home,
            "python_path": python_path,
            "exe_filename": exe_filename,
        }
    else:
        # TODO: Setting PYTHONPATH should not be needed, but it fails to work
        # unlike on Windows for unknown reasons.

        script_contents = """\
#!/bin/sh
# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPT_PATH=$(dirname "$SCRIPT")

PYTHONHOME=%(python_home)s
export PYTHONHOME
NUITKA_PYTHONPATH="%(python_path)s"
export NUITKA_PYTHONPATH
PYTHONPATH="%(python_path)s"
export PYTHONPATH

%(debugger_call)s"$SCRIPT_PATH/%(exe_filename)s" $@

""" % {
            "debugger_call": debugger_call,
            "python_home": python_home,
            "python_path": python_path,
            "exe_filename": exe_filename,
        }

    putTextFileContents(script_filename, script_contents)

    if not isWin32Windows():
        addFileExecutablePermission(script_filename)


def executePostProcessingResources(manifest, onefile):
    """Adding Windows resources to the binary.

    Used for both onefile and not onefile binary, potentially two times.
    """
    result_filename = OutputDirectories.getResultFullpath(onefile=onefile)

    if manifest is None:
        manifest = getDefaultWindowsExecutableManifest()

    if Options.shallAskForWindowsAdminRights():
        manifest.addUacAdmin()

    if Options.shallAskForWindowsUIAccessRights():
        manifest.addUacUiAccess()

    manifest.addResourceToFile(result_filename, logger=postprocessing_logger)

    if (
        Options.getWindowsVersionInfoStrings()
        or Options.getProductVersionTuple()
        or Options.getFileVersionTuple()
    ):
        addVersionInfoResource(
            string_values=Options.getWindowsVersionInfoStrings(),
            product_version=Options.getProductVersionTuple(),
            file_version=Options.getFileVersionTuple(),
            file_date=(0, 0),
            is_exe=not Options.shallMakeModule(),
            result_filename=result_filename,
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
                "The specified icon template executable '%s' didn't contain anything to copy."
                % template_exe
            )
        else:
            postprocessing_logger.warning(
                "Copied %d icon resources from '%s'." % (res_copied, template_exe)
            )
    else:
        _addWindowsIconFromIcons(onefile=onefile)

    splash_screen_filename = Options.getWindowsSplashScreen()
    if splash_screen_filename is not None:
        splash_data = getFileContents(splash_screen_filename, mode="rb")

        addResourceToFile(
            target_filename=result_filename,
            data=splash_data,
            resource_kind=RT_RCDATA,
            lang_id=0,
            res_name=28,
            logger=postprocessing_logger,
        )


def executePostProcessing():
    """Postprocessing of the resulting binary.

    These are in part required steps, not usable after failure.
    """

    # Lots of cases to deal with,
    # pylint: disable=too-many-branches,too-many-statements

    result_filename = OutputDirectories.getResultFullpath(onefile=False)

    if isWin32Windows():
        if not Options.shallMakeModule():
            if python_version < 0x300:
                # Copy the Windows manifest from the CPython binary to the created
                # executable, so it finds "MSCRT.DLL". This is needed for Python2
                # only, for Python3 newer MSVC doesn't hide the C runtime.
                manifest = getWindowsExecutableManifest(sys.executable)
            else:
                manifest = None

            executePostProcessingResources(manifest=manifest, onefile=False)

        source_dir = OutputDirectories.getSourceDirectoryPath()

        # Attach the binary blob as a Windows resource.
        addResourceToFile(
            target_filename=result_filename,
            data=getFileContents(getConstantBlobFilename(source_dir), mode="rb"),
            resource_kind=RT_RCDATA,
            res_name=3,
            lang_id=0,
            logger=postprocessing_logger,
        )

    # On macOS, we update the executable path for searching the "libpython"
    # library.
    if (
        isMacOS()
        and not Options.shallMakeModule()
        and not Options.shallUseStaticLibPython()
    ):
        for dependency in parseOtoolListingOutput(
            getOtoolDependencyOutput(result_filename, [])
        ):
            if os.path.basename(dependency).lower().startswith(("python", "libpython")):
                python_dll_filename = dependency
                break
        else:
            postprocessing_logger.sysexit(
                """
Error, expected 'libpython dependency not found. Please report the bug."""
            )

        python_lib_path = os.path.dirname(python_dll_filename)
        python_dll_path = python_dll_filename

        if not os.path.exists(python_lib_path):
            python_lib_path = os.path.join(sys.prefix, "lib")
            python_dll_path = os.path.join(
                python_lib_path, os.path.basename(python_dll_filename)
            )

        # Note: For CPython, and potentially others, the rpath for the Python
        # library needs to be set, so it will be detected as a dependency
        # without tricks.
        callInstallNameTool(
            filename=result_filename,
            mapping=(
                (
                    python_dll_filename,
                    python_dll_path,
                ),
            ),
            id_path=None,
            rpath=python_lib_path,
        )

    if Options.shallCreateAppBundle():
        createPlistInfoFile(logger=postprocessing_logger, onefile=False)

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

    if isAndroidBasedLinux():
        cleanupHeaderForAndroid(result_filename)

    # Might have to create a CMD file, potentially with debugger run.
    if Options.shallCreateScriptFileForExecution():
        createScriptFileForExecution(result_filename=result_filename)

    # Create a ".pyi" file for created modules
    if Options.shallMakeModule() and Options.shallCreatePyiFile():
        if Options.shallCreatePyiFileContainStubs():
            if python_version >= 0x300:
                stubgen = importFromInlineCopy("stubgen", must_exist=False)
                stubgen_reason = "Stubs included by default"
            else:
                stubgen = None
                stubgen_reason = "Python2 is not supported for stubs"
        else:
            stubgen = None
            stubgen_reason = "Stubs were disabled"

        imported_module_names = getImportedModuleNames()

        contents = """\
# This file was generated by Nuitka
"""

        if stubgen is not None:
            try:
                stubs = stubgen.generate_stub_from_source(
                    source_code=OutputDirectories.getMainModule().getSourceCode(),
                    output_file_path=None,
                    text_only=True,
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                postprocessing_logger.warning(
                    "Stub generation with stubgen failed due to: '%s'. Please report the module code in an issue report."
                    % (str(e))
                )

                if Options.is_debug:
                    raise

                stubs = None
                stubgen_reason = (
                    "Stub generation failed due to error, please report the issue."
                )
        else:
            stubs = None

        stubs = "# %s\n%s" % (stubgen_reason, "" if stubs is None else stubs)

        contents += "\n" + stubs + "\n"

        contents += "__name__ = ..."

        imported_module_names = getImportedModuleNames()

        # Meaningless, TODO: Potentially others could be listed here too.
        if "__future__" in imported_module_names:
            imported_module_names.remove("__future__")

        contents += "\n" * 4

        if imported_module_names:
            contents += "# Modules used internally, to allow implicit dependencies to be seen:\n"
            contents += "\n".join(
                "import %s" % module_name for module_name in getImportedModuleNames()
            )
        else:
            contents += (
                "# No other modules used internally, no implicit dependencies.\n"
            )

        pyi_filename = OutputDirectories.getResultBasePath() + ".pyi"
        putTextFileContents(pyi_filename, contents, encoding="utf-8")

    if isWin32Windows() and getFileSize(result_filename) > 2**30 * 1.8:
        postprocessing_logger.warning(
            """\
The created compiled binary is larger than 1.8GB and therefore may not be
executable by Windows due to its limitations."""
        )


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
