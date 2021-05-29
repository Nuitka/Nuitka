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
""" Pack distribution folders into a single file.

"""

import os
import shutil
import struct
import subprocess
import sys

from nuitka import Options, OutputDirectories
from nuitka.build import SconsInterface
from nuitka.Options import assumeYesForDownloads, getIconPaths, getJobLimit
from nuitka.OutputDirectories import getResultBasepath, getResultFullpath
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import (
    executePostProcessingResources,
    version_resources,
)
from nuitka.Tracing import general, postprocessing_logger, scons_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getNullInput, withEnvironmentVarsOverriden
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    getFileContents,
    getFileList,
    removeDirectory,
)
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import (
    getArchitecture,
    getOS,
    hasOnefileSupportedOS,
    isWin32Windows,
)


def packDistFolderToOnefile(dist_dir, binary_filename):
    """Pack distribution to onefile, i.e. a single file that is directly executable."""

    onefile_output_filename = getResultFullpath(onefile=True)

    if getOS() == "Windows" or Options.isExperimental("onefile-bootstrap"):
        packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir)
    elif getOS() == "Linux":
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
        "https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-%s.AppImage"
        % arch_name
    )

    return getCachedDownload(
        url=appimagetool_url,
        is_arch_specific=True,
        binary=appimagetool_url.rsplit("/", 1)[1],
        flatten=True,
        specifity=appimagetool_url.rsplit("/", 2)[1],
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
    with open(apprun_filename, "w") as output_file:
        output_file.write(
            """\
#!/bin/bash
exec -a $ARGV0 $APPDIR/%s $@"""
            % os.path.basename(binary_filename)
        )

    addFileExecutablePermission(apprun_filename)

    binary_basename = os.path.basename(getResultBasepath())

    icon_paths = getIconPaths()

    assert icon_paths
    extension = os.path.splitext(icon_paths[0])[1].lower()

    shutil.copyfile(icon_paths[0], getResultBasepath() + extension)

    with open(getResultBasepath() + ".desktop", "w") as output_file:
        output_file.write(
            """\
[Desktop Entry]
Name=%(binary_basename)s
Exec=%(binary_filename)s
Icon=%(binary_basename)s
Type=Application
Categories=Utility;"""
            % {
                "binary_basename": binary_basename,
                "binary_filename": os.path.basename(binary_filename),
            }
        )

    postprocessing_logger.info(
        "Creating single file from dist folder, this may take a while."
    )

    stdout_filename = binary_filename + ".appimage.stdout.txt"
    stderr_filename = binary_filename + ".appimage.stderr.txt"

    stdout_file = open(stdout_filename, "wb")
    stderr_file = open(stderr_filename, "wb")

    # Starting the process while locked, so file handles are not duplicated.
    appimagetool_process = subprocess.Popen(
        (
            _getAppImageToolPath(
                for_operation=True, assume_yes_for_downloads=assumeYesForDownloads()
            ),
            dist_dir,
            "--comp",
            "xz",
            "-n",
            onefile_output_filename,
        ),
        shell=False,
        stdin=getNullInput(),
        stdout=stdout_file,
        stderr=stderr_file,
    )

    result = appimagetool_process.wait()

    stdout_file.close()
    stderr_file.close()

    if not os.path.exists(onefile_output_filename):
        postprocessing_logger.sysexit(
            "Error, expected output file %r not created by AppImage, check its outputs %r and %r."
            % (onefile_output_filename, stdout_filename, stderr_filename)
        )

    if result != 0:
        # Useless now.
        os.unlink(onefile_output_filename)

        if b"Text file busy" in getFileContents(stderr_filename, mode="rb"):
            postprocessing_logger.sysexit(
                "Error, error exit from AppImage because target file is locked."
            )

        postprocessing_logger.sysexit(
            "Error, error exit from AppImage, check its outputs %r and %r."
            % (stdout_filename, stderr_filename)
        )

    os.unlink(stdout_filename)
    os.unlink(stderr_filename)

    postprocessing_logger.info("Completed onefile creation.")


def _runOnefileScons(quiet):

    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=True)
    SconsInterface.cleanSconsDirectory(source_dir)

    asBoolStr = SconsInterface.asBoolStr

    options = {
        "result_name": OutputDirectories.getResultBasepath(onefile=True),
        "result_exe": OutputDirectories.getResultFullpath(onefile=True),
        "source_dir": source_dir,
        "debug_mode": asBoolStr(Options.is_debug),
        "unstripped_mode": asBoolStr(Options.isUnstripped()),
        "experimental": ",".join(Options.getExperimentalIndications()),
        "trace_mode": asBoolStr(Options.shallTraceExecution()),
        "target_arch": getArchitecture(),
        "python_prefix": sys.prefix,
        "nuitka_src": SconsInterface.getSconsDataPath(),
        "compiled_exe": OutputDirectories.getResultFullpath(onefile=False),
    }

    SconsInterface.setCommonOptions(options)

    onefile_env_values = {}

    if Options.isWindowsOnefileTempDirMode() or getOS() != "Windows":
        onefile_env_values["ONEFILE_TEMP_SPEC"] = Options.getWindowsOnefileTempDirSpec(
            use_default=True
        )
    else:
        # Merge version information if possible, to avoid collisions, or deep nesting
        # in file system.
        product_version = version_resources["ProductVersion"]
        file_version = version_resources["FileVersion"]

        if product_version != file_version:
            effective_version = "%s-%s" % (product_version, file_version)
        else:
            effective_version = file_version

        onefile_env_values["ONEFILE_COMPANY"] = version_resources["CompanyName"]
        onefile_env_values["ONEFILE_PRODUCT"] = version_resources["ProductName"]
        onefile_env_values["ONEFILE_VERSION"] = effective_version

    with withEnvironmentVarsOverriden(onefile_env_values):
        result = SconsInterface.runScons(
            options=options, quiet=quiet, scons_filename="Onefile.scons"
        )

    # Exit if compilation failed.
    if not result:
        scons_logger.sysexit("Error, one file bootstrap build for Windows failed.")

    if Options.isRemoveBuildDir():
        general.info("Removing onefile build directory %r." % source_dir)

        removeDirectory(path=source_dir, ignore_errors=False)
        assert not os.path.exists(source_dir)
    else:
        general.info("Keeping onefile build directory %r." % source_dir)


def _pickCompressor():
    if Options.isExperimental("zstd"):
        try:
            from zstd import ZSTD_compress  # pylint: disable=I0021,import-error
        except ImportError:
            general.warning(
                "Onefile mode cannot compress without 'zstd' module on '%s'." % getOS()
            )
        else:
            return b"Y", lambda data: ZSTD_compress(data, 9, getJobLimit())
    else:
        return b"X", lambda data: data


def packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir):
    postprocessing_logger.info(
        "Creating single file from dist folder, this may take a while."
    )

    general.info("Running bootstrap binary compilation via Scons.")

    # First need to create the bootstrap binary for unpacking.
    _runOnefileScons(quiet=not Options.isShowScons())

    if isWin32Windows():
        executePostProcessingResources(manifest=None, onefile=True)

    # Now need to append to payload it, potentially compressing it.
    compression_indicator, compressor = _pickCompressor()

    with open(onefile_output_filename, "ab") as output_file:
        # Seeking to end of file seems necessary on Python2 at least, maybe it's
        # just that tell reports wrong value initially.
        output_file.seek(0, 2)

        start_pos = output_file.tell()

        output_file.write(b"KA" + compression_indicator)

        # Move the binary to start immediately to the start position
        start_binary = getResultFullpath(onefile=False)
        file_list = getFileList(dist_dir, normalize=False)
        file_list.remove(start_binary)
        file_list.insert(0, start_binary)

        for filename_full in file_list:
            filename_relative = os.path.relpath(filename_full, dist_dir)

            if isWin32Windows():
                filename_encoded = filename_relative.encode("utf-16le") + b"\0\0"
            else:
                filename_encoded = filename_relative.encode("utf8") + b"\0"

            output_file.write(filename_encoded)

            with open(filename_full, "rb") as input_file:
                compressed = compressor(input_file.read())

                output_file.write(struct.pack("Q", len(compressed)))
                output_file.write(compressed)

        # Using empty filename as a terminator.
        output_file.write(b"\0\0")

        output_file.write(struct.pack("Q", start_pos))


def checkOnefileReadiness(assume_yes_for_downloads):
    if getOS() == "Linux":
        app_image_path = _getAppImageToolPath(
            for_operation=False, assume_yes_for_downloads=assume_yes_for_downloads
        )

        return app_image_path is not None
    else:
        return hasOnefileSupportedOS()
