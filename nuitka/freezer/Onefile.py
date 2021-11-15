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
from contextlib import contextmanager

from nuitka import Options, OutputDirectories
from nuitka.build import SconsInterface
from nuitka.Options import assumeYesForDownloads, getIconPaths
from nuitka.OutputDirectories import getResultBasepath, getResultFullpath
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import (
    executePostProcessingResources,
    version_resources,
)
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.PythonVersions import python_version
from nuitka.Tracing import onefile_logger, postprocessing_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getNullInput, withEnvironmentVarsOverriden
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    deleteFile,
    getFileContents,
    getFileList,
    openTextFile,
    putTextFileContents,
    removeDirectory,
)
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import (
    getArchitecture,
    getOS,
    hasOnefileSupportedOS,
    isLinux,
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

    shutil.copyfile(icon_paths[0], getResultBasepath() + extension)

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

    # Starting the process while locked, so file handles are not duplicated, we
    # need fine grained control over process here, therefore we cannot use the
    # Execution.executeProcess() function without making it too complex and not
    # all Python versions allow using with, pylint: disable=consider-using-with
    # pylint: disable
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
        "unstripped_mode": asBoolStr(Options.isUnstripped()),
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

    SconsInterface.setCommonOptions(options)

    onefile_env_values = {}

    if Options.isOnefileTempDirMode():
        onefile_env_values["ONEFILE_TEMP_SPEC"] = Options.getOnefileTempDirSpec(
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
        onefile_logger.sysexit("Error, onefile bootstrap binary build failed.")

    if Options.isRemoveBuildDir():
        onefile_logger.info("Removing onefile build directory %r." % source_dir)

        removeDirectory(path=source_dir, ignore_errors=False)
        assert not os.path.exists(source_dir)
    else:
        onefile_logger.info("Keeping onefile build directory %r." % source_dir)


def _pickCompressor():
    try:
        from zstandard import ZstdCompressor  # pylint: disable=I0021,import-error
    except ImportError:
        if python_version < 0x350:
            onefile_logger.info(
                "Onefile compression is not supported before Python 3.5 at this time."
            )
        else:
            onefile_logger.warning(
                "Onefile mode cannot compress without 'zstandard' module installed."
            )
    else:
        cctx = ZstdCompressor(level=22)

        @contextmanager
        def useCompressedFile(output_file):
            with cctx.stream_writer(output_file, closefd=False) as compressed_file:
                yield compressed_file

        onefile_logger.info("Using compression for onefile payload.")

        return b"Y", useCompressedFile

    # By default use the same file handle that does not compress.
    @contextmanager
    def useSameFile(output_file):
        yield output_file

    return b"X", useSameFile


def packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir):
    # Dealing with details, pylint: disable=too-many-locals

    postprocessing_logger.info(
        "Creating single file from dist folder, this may take a while."
    )

    onefile_logger.info("Running bootstrap binary compilation via Scons.")

    # Now need to append to payload it, potentially compressing it.
    compression_indicator, compressor = _pickCompressor()

    # First need to create the bootstrap binary for unpacking.
    _runOnefileScons(
        quiet=not Options.isShowScons(),
        onefile_compression=compression_indicator == b"Y",
    )

    if isWin32Windows():
        executePostProcessingResources(manifest=None, onefile=True)

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

        if isWin32Windows():
            filename_encoding = "utf-16le"
        else:
            filename_encoding = "utf8"

        payload_size = 0

        setupProgressBar(
            stage="Onefile Payload",
            unit="module",
            total=len(file_list),
        )

        with compressor(output_file) as compressed_file:

            # TODO: Use progress bar here.
            for filename_full in file_list:
                filename_relative = os.path.relpath(filename_full, dist_dir)

                reportProgressBar(
                    item=filename_relative,
                    update=False,
                )

                filename_encoded = (filename_relative + "\0").encode(filename_encoding)

                compressed_file.write(filename_encoded)
                payload_size += len(filename_encoded)

                with open(filename_full, "rb") as input_file:
                    input_file.seek(0, 2)
                    input_size = input_file.tell()
                    input_file.seek(0, 0)

                    compressed_file.write(struct.pack("Q", input_size))
                    shutil.copyfileobj(input_file, compressed_file)

                    payload_size += input_size + 8

                reportProgressBar(
                    item=filename_relative,
                    update=True,
                )

            # Using empty filename as a terminator.
            filename_encoded = "\0".encode(filename_encoding)
            compressed_file.write(filename_encoded)
            payload_size += len(filename_encoded)

            compressed_size = compressed_file.tell()

        if compression_indicator == b"Y":
            onefile_logger.info(
                "Onefile payload compression ratio (%.2f%%) size %d to %d."
                % (
                    (float(compressed_size) / payload_size) * 100,
                    payload_size,
                    compressed_size,
                )
            )

        # add padding to have the start position at a double world boundary
        # this is needed on windows so that a possible certificate immediately
        # follows the start position
        pad = output_file.tell() % 8
        if pad != 0:
            output_file.write(bytes(8 - pad))
        output_file.write(struct.pack("Q", start_pos))

    closeProgressBar()


def checkOnefileReadiness(assume_yes_for_downloads):
    if isLinux():
        app_image_path = _getAppImageToolPath(
            for_operation=False, assume_yes_for_downloads=assume_yes_for_downloads
        )

        return app_image_path is not None
    else:
        return hasOnefileSupportedOS()
