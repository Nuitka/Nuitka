#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Pack distribution folders into a single file."""

import os
import subprocess
import sys

from nuitka.build.SconsInterface import (
    asBoolStr,
    cleanSconsDirectory,
    getCommonSconsOptions,
    provideStaticSourceFilesOnefile,
    runScons,
)
from nuitka.options.Options import (
    getJobLimit,
    getOnefileTempDirSpec,
    getProgressBar,
    getWindowsSplashScreen,
    isLowMemory,
    isOnefileTempDirMode,
    isRemoveBuildDir,
    shallDisableCompressionCacheUsage,
    shallNotCompressOnefile,
    shallOnefileAsArchive,
    shallTraceExecution,
)
from nuitka.OutputDirectories import getResultFullpath, getSourceDirectoryPath
from nuitka.plugins.Hooks import (
    getBuildDefinitions,
    onBootstrapBinary,
    onGeneratedSourceCode,
    onOnefileFinished,
    writeExtraCodeFiles,
)
from nuitka.PostProcessing import executePostProcessingResources
from nuitka.PythonVersions import (
    getZstandardSupportingVersions,
    python_version,
)
from nuitka.States import states
from nuitka.Tracing import onefile_logger, postprocessing_logger
from nuitka.utils.Execution import withEnvironmentVarsOverridden
from nuitka.utils.FileOperations import (
    areSamePaths,
    getExternalUsePath,
    getFileContents,
    removeDirectory,
)
from nuitka.utils.InstalledPythons import findInstalledPython
from nuitka.utils.SharedLibraries import cleanupHeaderForAndroid
from nuitka.utils.Signing import addMacOSCodeSignature
from nuitka.utils.Utils import (
    isAndroidBasedLinux,
    isMacOS,
    isWin32OrPosixWindows,
    isWin32Windows,
)
from nuitka.utils.WindowsResources import RT_RCDATA, addResourceToFile

from .DllDependenciesWin32 import shallIncludeWindowsRuntimeDLLs


def packDistFolderToOnefile(dist_dir):
    """Pack distribution to onefile, i.e. a single file that is directly executable."""

    onefile_output_filename = getResultFullpath(onefile=True, real=True)
    start_binary = getResultFullpath(onefile=False, real=True)

    packDistFolderToOnefileBootstrap(
        onefile_output_filename=onefile_output_filename,
        dist_dir=dist_dir,
        start_binary=start_binary,
    )

    onOnefileFinished(onefile_output_filename)


def _runOnefileScons(onefile_compression, onefile_archive):
    scons_options, env_values = getCommonSconsOptions()

    source_dir = getSourceDirectoryPath(onefile=True, create=False)

    # Let plugins do their thing for onefile mode too.
    writeExtraCodeFiles(onefile=True)
    provideStaticSourceFilesOnefile(source_dir=source_dir)
    onGeneratedSourceCode(source_dir=source_dir, onefile=True)

    scons_options["result_exe"] = getResultFullpath(onefile=True, real=False)
    scons_options["source_dir"] = source_dir
    scons_options["debug_mode"] = asBoolStr(states.is_debug)
    scons_options["trace_mode"] = asBoolStr(shallTraceExecution())
    scons_options["onefile_splash_screen"] = asBoolStr(
        getWindowsSplashScreen() is not None
    )
    if isWin32Windows() and shallIncludeWindowsRuntimeDLLs():
        scons_options["onefile_windows_static_runtime"] = asBoolStr(True)

    env_values["_NUITKA_ONEFILE_TEMP_SPEC"] = getOnefileTempDirSpec()
    env_values["_NUITKA_ONEFILE_COMPRESSION_BOOL"] = "1" if onefile_compression else "0"
    env_values["_NUITKA_ONEFILE_ARCHIVE_BOOL"] = "1" if onefile_archive else "0"

    # Allow plugins to build definitions.
    env_values.update(getBuildDefinitions())

    result = runScons(
        scons_options=scons_options,
        env_values=env_values,
        scons_filename="Onefile.scons",
    )

    # Exit if compilation failed.
    if not result:
        onefile_logger.sysexit("Error, onefile bootstrap binary build failed.")


_compressor_python = None


def getCompressorPython():
    # User may disable it.
    if shallNotCompressOnefile():
        return None

    global _compressor_python  # singleton, pylint: disable=global-statement

    if _compressor_python is None:
        _compressor_python = findInstalledPython(
            python_versions=getZstandardSupportingVersions(),
            module_name="zstandard",
            module_version="0.15",
        )

        if _compressor_python is None:
            if python_version < 0x350:
                onefile_logger.warning(
                    """\
Onefile mode cannot compress without 'zstandard' module installed on \
another discoverable Python >= 3.5 on your system."""
                )
            else:
                onefile_logger.warning(
                    """\
Onefile mode cannot compress without 'zstandard' package installed."""
                )

    return _compressor_python


def runOnefileCompressor(
    compressor_python, dist_dir, onefile_output_filename, start_binary
):
    file_checksums = not isOnefileTempDirMode()
    win_path_sep = isWin32OrPosixWindows()

    if compressor_python is None or areSamePaths(
        compressor_python.getPythonExe(), sys.executable
    ):
        from nuitka.tools.onefile_compressor.OnefileCompressor import (
            attachOnefilePayload,
        )

        attachOnefilePayload(
            dist_dir=dist_dir,
            onefile_output_filename=onefile_output_filename,
            start_binary=start_binary,
            expect_compression=compressor_python is not None,
            as_archive=shallOnefileAsArchive(),
            use_compression_cache=not shallDisableCompressionCacheUsage(),
            file_checksums=file_checksums,
            win_path_sep=win_path_sep,
            low_memory=isLowMemory(),
            job_limit=getJobLimit(),
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

        mapping["NUITKA_PROGRESS_BAR"] = getProgressBar()

        onefile_logger.info(
            "Using external Python '%s' to compress the payload."
            % compressor_python.getPythonExe()
        )

        with withEnvironmentVarsOverridden(mapping):
            subprocess.check_call(
                [
                    compressor_python.getPythonExe(),
                    onefile_compressor_path,
                    dist_dir,
                    getExternalUsePath(onefile_output_filename, only_dirname=True),
                    start_binary,
                    str(file_checksums),
                    str(win_path_sep),
                    str(isLowMemory()),
                    str(shallOnefileAsArchive()),
                    str(not shallDisableCompressionCacheUsage()),
                    str(getJobLimit()),
                ],
                shell=False,
            )


def packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir, start_binary):
    onefile_logger.info("Creating single file from dist folder, this may take a while.")

    onefile_logger.info("Running bootstrap binary compilation via Scons.")

    # Cleanup first.
    source_dir = getSourceDirectoryPath(onefile=True, create=True)
    cleanSconsDirectory(source_dir)

    # Used only in some configurations
    onefile_payload_filename = os.path.join(source_dir, "__payload.bin")

    # Now need to append to payload it, potentially compressing it.
    compressor_python = getCompressorPython()

    # Decide if we need the payload during build already, or if it should be
    # attached.
    payload_used_in_build = isMacOS()

    if payload_used_in_build:
        runOnefileCompressor(
            compressor_python=compressor_python,
            dist_dir=dist_dir,
            onefile_output_filename=onefile_payload_filename,
            start_binary=start_binary,
        )

    # Create the bootstrap binary for unpacking.
    _runOnefileScons(
        onefile_compression=compressor_python is not None,
        onefile_archive=shallOnefileAsArchive(),
    )

    if isWin32Windows():
        executePostProcessingResources(
            result_filename=onefile_output_filename, manifest=None, onefile=True
        )

    if isAndroidBasedLinux():
        cleanupHeaderForAndroid(onefile_output_filename)

    onBootstrapBinary(onefile_output_filename)

    if isMacOS():
        addMacOSCodeSignature(
            filenames=[onefile_output_filename], entitlements_filename=None
        )
        assert payload_used_in_build

    if not payload_used_in_build:
        runOnefileCompressor(
            compressor_python=compressor_python,
            dist_dir=dist_dir,
            onefile_output_filename=(
                onefile_payload_filename
                if isWin32Windows()
                else onefile_output_filename
            ),
            start_binary=start_binary,
        )

        if isWin32Windows():
            addResourceToFile(
                target_filename=onefile_output_filename,
                data=getFileContents(onefile_payload_filename, mode="rb"),
                resource_kind=RT_RCDATA,
                lang_id=0,
                res_name=27,
                logger=postprocessing_logger,
            )

    if isRemoveBuildDir():
        onefile_logger.info("Removing onefile build directory '%s'." % source_dir)

        removeDirectory(
            path=source_dir,
            logger=onefile_logger,
            ignore_errors=False,
            extra_recommendation=None,
        )
        assert not os.path.exists(source_dir)
    else:
        onefile_logger.info("Keeping onefile build directory '%s'." % source_dir)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
