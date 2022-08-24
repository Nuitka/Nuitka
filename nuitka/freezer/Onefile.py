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
    getAutoUpdateUrlSpec,
    getOnefileTempDirSpec,
    isOnefileTempDirMode,
)
from nuitka.OutputDirectories import getResultFullpath
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import executePostProcessingResources
from nuitka.PythonVersions import python_version
from nuitka.Tracing import onefile_logger, postprocessing_logger
from nuitka.utils.Execution import withEnvironmentVarsOverridden
from nuitka.utils.FileOperations import areSamePaths, removeDirectory
from nuitka.utils.InstalledPythons import findInstalledPython
from nuitka.utils.Signing import addMacOSCodeSignature
from nuitka.utils.Utils import getArchitecture, isMacOS, isWin32Windows


def packDistFolderToOnefile(dist_dir):
    """Pack distribution to onefile, i.e. a single file that is directly executable."""

    onefile_output_filename = getResultFullpath(onefile=True)

    packDistFolderToOnefileBootstrap(onefile_output_filename, dist_dir)

    Plugins.onOnefileFinished(onefile_output_filename)


def _runOnefileScons(quiet, onefile_compression):
    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=True)
    SconsInterface.cleanSconsDirectory(source_dir)

    asBoolStr = SconsInterface.asBoolStr

    options = {
        "result_name": OutputDirectories.getResultBasePath(onefile=True),
        "result_exe": OutputDirectories.getResultFullpath(onefile=True),
        "source_dir": source_dir,
        "debug_mode": asBoolStr(Options.is_debug),
        "experimental": ",".join(Options.getExperimentalIndications()),
        "trace_mode": asBoolStr(Options.shallTraceExecution()),
        "target_arch": getArchitecture(),
        "python_prefix": sys.prefix,
        "nuitka_src": SconsInterface.getSconsDataPath(),
        "compiled_exe": OutputDirectories.getResultFullpath(onefile=False),
        "onefile_splash_screen": asBoolStr(
            Options.getWindowsSplashScreen() is not None
        ),
    }

    if Options.isClang():
        options["clang_mode"] = "true"

    env_values = SconsInterface.setCommonOptions(options)

    env_values["_NUITKA_ONEFILE_TEMP_SPEC"] = getOnefileTempDirSpec()
    env_values["_NUITKA_ONEFILE_TEMP"] = "1" if isOnefileTempDirMode() else "0"
    env_values["_NUITKA_ONEFILE_COMPRESSION"] = "1" if onefile_compression else "0"

    env_values["_NUITKA_ONEFILE_AUTO_UPDATE_URL_SPEC"] = getAutoUpdateUrlSpec() or ""

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
                "Onefile mode cannot compress without 'zstandard' module installed on another Python >= 3.5 on your system."
            )
        else:
            onefile_logger.warning(
                "Onefile mode cannot compress without 'zstandard' module installed."
            )

    return compressor_python


def runOnefileCompressor(
    compressor_python, dist_dir, onefile_output_filename, start_binary
):
    file_checksums = not isOnefileTempDirMode()

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
            file_checksums=file_checksums,
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
                    onefile_output_filename,
                    start_binary,
                    str(file_checksums),
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
