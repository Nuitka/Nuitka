#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Pack distribution folders into a single file.

"""

import os
import subprocess
import sys

from nuitka import Options, OutputDirectories
from nuitka.build import SconsInterface
from nuitka.Options import (
    assumeYesForDownloads,
    getAppImageCompression,
    getIconPaths,
)
from nuitka.OutputDirectories import getResultBasepath, getResultFullpath
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import executePostProcessingResources
from nuitka.PythonVersions import python_version
from nuitka.Tracing import onefile_logger, postprocessing_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getNullInput, withEnvironmentVarsOverridden
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    areSamePaths,
    copyFile,
    deleteFile,
    getFileContents,
    openTextFile,
    putTextFileContents,
    removeDirectory,
)
from nuitka.utils.InstalledPythons import findInstalledPython
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Signing import addMacOSCodeSignature
from nuitka.utils.Utils import (
    getArchitecture,
    getOS,
    hasOnefileSupportedOS,
    isLinux,
    isMacOS,
    isWin32Windows,
)


def packDistFolderToOnefile(dist_dir, binary_filename):
    """Pack distribution to onefile, i.e. a single file that is directly executable."""

    onefile_output_filename = getResultFullpath(onefile=True)

    if getOS() == "Windows" or Options.isOnefileTempDirMode():
        packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir)
    elif isLinux():
        packDistFolderToOnefileLinux(onefile_output_filename, dist_dir, binary_filename)
    else:
        postprocessing_logger.sysexit(
            "Onefile mode is not yet available on %r." % getOS()
        )

    Plugins.onOnefileFinished(onefile_output_filename)


def _getAppImageToolPath(for_operation, assume_yes_for_downloads):
    """Return the path of appimagetool (for Linux).

    Will prompt the user to download if not already cached in AppData
    directory for Nuitka.
    """

    arch_name = getArchitecture()

    # Mismatch between Debian arch name and appimage arch naming.
    if arch_name == "armv7l":
        arch_name = "armhf"

    appimagetool_url = (
        "https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-%s.AppImage"
        % arch_name
    )

    return getCachedDownload(
        url=appimagetool_url,
        is_arch_specific=getArchitecture(),
        binary=appimagetool_url.rsplit("/", 1)[1],
        flatten=True,
        specificity=appimagetool_url.rsplit("/", 2)[1],
        message="""\
Nuitka will make use of AppImage (https://appimage.org/) tool
to combine Nuitka dist folder to onefile binary.""",
        reject="Nuitka does not work in --onefile on Linux without."
        if for_operation
        else None,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )


def packDistFolderToOnefileLinux(onefile_output_filename, dist_dir, binary_filename):
    """Pack to onefile binary on Linux.

    Notes: This is mostly a wrapper around AppImage, which does all the heavy
    lifting.
    """

    if not locateDLL("fuse"):
        postprocessing_logger.sysexit(
            """\
Error, the fuse library (libfuse.so.x from fuse2, *not* fuse3) must be installed
for onefile creation to work on Linux."""
        )

    # This might be possible to avoid being done with --runtime-file.
    apprun_filename = os.path.join(dist_dir, "AppRun")
    putTextFileContents(
        apprun_filename,
        contents="""\
#!/bin/bash
exec -a $ARGV0 $APPDIR/%s \"$@\""""
        % os.path.basename(binary_filename),
    )

    addFileExecutablePermission(apprun_filename)

    binary_basename = os.path.basename(getResultBasepath())

    icon_paths = getIconPaths()

    assert icon_paths
    extension = os.path.splitext(icon_paths[0])[1].lower()

    copyFile(icon_paths[0], getResultBasepath() + extension)

    putTextFileContents(
        getResultBasepath() + ".desktop",
        contents="""\
[Desktop Entry]
Name=%(binary_basename)s
Exec=%(binary_filename)s
Icon=%(binary_basename)s
Type=Application
Categories=Utility;"""
        % {
            "binary_basename": binary_basename,
            "binary_filename": os.path.basename(binary_filename),
        },
    )

    postprocessing_logger.info(
        "Creating single file from dist folder, this may take a while."
    )

    stdout_filename = binary_filename + ".appimage.stdout.txt"
    stderr_filename = binary_filename + ".appimage.stderr.txt"

    stdout_file = openTextFile(stdout_filename, "wb")
    stderr_file = openTextFile(stderr_filename, "wb")

    command = (
        _getAppImageToolPath(
            for_operation=True, assume_yes_for_downloads=assumeYesForDownloads()
        ),
        dist_dir,
        "--comp",
        getAppImageCompression(),
        "-n",
        onefile_output_filename,
    )

    stderr_file.write(b"Executed %r\n" % " ".join(command))

    # Starting the process while locked, so file handles are not duplicated, we
    # need fine grained control over process here, therefore we cannot use the
    # Execution.executeProcess() function without making it too complex and not
    # all Python versions allow using with, pylint: disable=consider-using-with
    # pylint: disable
    appimagetool_process = subprocess.Popen(
        command,
        shell=False,
        stdin=getNullInput(),
        stdout=stdout_file,
        stderr=stderr_file,
    )

    result = appimagetool_process.wait()

    stdout_file.close()
    stderr_file.close()

    if result != 0:
        # Useless result if there were errors, so now remove it.
        deleteFile(onefile_output_filename, must_exist=False)

        stderr = getFileContents(stderr_filename, mode="rb")

        if b"Text file busy" in stderr:
            postprocessing_logger.sysexit(
                "Error, error exit from AppImage because target file is locked."
            )

        if b"modprobe fuse" in stderr:
            postprocessing_logger.sysexit(
                "Error, error exit from AppImage because fuse kernel module was not loaded."
            )

        postprocessing_logger.sysexit(
            "Error, error exit from AppImage, check its outputs '%s' and '%s'."
            % (stdout_filename, stderr_filename)
        )

    if not os.path.exists(onefile_output_filename):
        postprocessing_logger.sysexit(
            "Error, expected output file %r not created by AppImage, check its outputs '%s' and '%s'."
            % (onefile_output_filename, stdout_filename, stderr_filename)
        )

    deleteFile(stdout_filename, must_exist=True)
    deleteFile(stderr_filename, must_exist=True)

    postprocessing_logger.info("Completed onefile creation.")


def _runOnefileScons(quiet, onefile_compression):

    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=True)
    SconsInterface.cleanSconsDirectory(source_dir)

    asBoolStr = SconsInterface.asBoolStr

    options = {
        "result_name": OutputDirectories.getResultBasepath(onefile=True),
        "result_exe": OutputDirectories.getResultFullpath(onefile=True),
        "source_dir": source_dir,
        "debug_mode": asBoolStr(Options.is_debug),
        "experimental": ",".join(Options.getExperimentalIndications()),
        "trace_mode": asBoolStr(Options.shallTraceExecution()),
        "target_arch": getArchitecture(),
        "python_prefix": sys.prefix,
        "nuitka_src": SconsInterface.getSconsDataPath(),
        "compiled_exe": OutputDirectories.getResultFullpath(onefile=False),
        "onefile_compression": asBoolStr(onefile_compression),
        "onefile_splash_screen": asBoolStr(
            Options.getWindowsSplashScreen() is not None
        ),
    }

    if Options.isClang():
        options["clang_mode"] = "true"

    env_values = SconsInterface.setCommonOptions(options)

    if Options.isOnefileTempDirMode():
        env_values["ONEFILE_TEMP_SPEC"] = Options.getOnefileTempDirSpec()

    with withEnvironmentVarsOverridden(env_values):
        result = SconsInterface.runScons(
            options=options, quiet=quiet, scons_filename="Onefile.scons"
        )

    # Exit if compilation failed.
    if not result:
        onefile_logger.sysexit("Error, onefile bootstrap binary build failed.")

    if Options.isRemoveBuildDir():
        onefile_logger.info("Removing onefile build directory %r." % source_dir)

        removeDirectory(path=source_dir, ignore_errors=False)
        assert not os.path.exists(source_dir)
    else:
        onefile_logger.info("Keeping onefile build directory %r." % source_dir)


def getCompressorPython():
    zstandard_supported_pythons = ("3.5", "3.6", "3.7", "3.8", "3.9", "3.10")

    compressor_python = findInstalledPython(
        python_versions=zstandard_supported_pythons,
        module_name="zstandard",
        module_version="0.15",
    )

    if compressor_python is None:
        if python_version < 0x350:
            onefile_logger.warning(
                "Onefile mode cannot compress without 'zstandard' module installed."
            )
        else:
            onefile_logger.warning(
                "Onefile mode cannot compress without 'zstandard' module installed on any Python >= 3.5."
            )

    return compressor_python


def runOnefileCompressor(
    compressor_python, dist_dir, onefile_output_filename, start_binary
):
    if compressor_python is None:
        from nuitka.tools.onefile_compressor.OnefileCompressor import (
            attachOnefilePayload,
        )

        attachOnefilePayload(
            dist_dir=dist_dir,
            onefile_output_filename=onefile_output_filename,
            start_binary=start_binary,
            expect_compression=False,
        )
    elif areSamePaths(compressor_python.getPythonExe(), sys.executable):
        from nuitka.tools.onefile_compressor.OnefileCompressor import (
            attachOnefilePayload,
        )

        attachOnefilePayload(
            dist_dir=dist_dir,
            onefile_output_filename=onefile_output_filename,
            start_binary=start_binary,
            expect_compression=True,
        )
    else:
        onefile_compressor_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "tools", "onefile_compressor")
        )

        mapping = {
            "NUITKA_PACKAGE_HOME": os.path.dirname(
                os.path.abspath(sys.modules["nuitka"].__path__[0])
            )
        }

        mapping["NUITKA_PROGRESS_BAR"] = "1" if Options.shallUseProgressBar() else "0"

        with withEnvironmentVarsOverridden(mapping):
            subprocess.check_call(
                [
                    compressor_python.getPythonExe(),
                    onefile_compressor_path,
                    dist_dir,
                    onefile_output_filename,
                    start_binary,
                    str(onefile_compressor_path is not None),
                ],
                shell=False,
            )


def packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir):
    postprocessing_logger.info(
        "Creating single file from dist folder, this may take a while."
    )

    onefile_logger.info("Running bootstrap binary compilation via Scons.")

    # Now need to append to payload it, potentially compressing it.
    compressor_python = getCompressorPython()

    # First need to create the bootstrap binary for unpacking.
    _runOnefileScons(
        quiet=not Options.isShowScons(),
        onefile_compression=compressor_python is not None,
    )

    if isWin32Windows():
        executePostProcessingResources(manifest=None, onefile=True)

    Plugins.onBootstrapBinary(onefile_output_filename)

    if isMacOS():
        addMacOSCodeSignature(filenames=[onefile_output_filename])

    runOnefileCompressor(
        compressor_python=compressor_python,
        dist_dir=dist_dir,
        onefile_output_filename=onefile_output_filename,
        start_binary=getResultFullpath(onefile=False),
    )


def checkOnefileReadiness(assume_yes_for_downloads):
    if isLinux():
        app_image_path = _getAppImageToolPath(
            for_operation=False, assume_yes_for_downloads=assume_yes_for_downloads
        )

        return app_image_path is not None
    else:
        return hasOnefileSupportedOS()
