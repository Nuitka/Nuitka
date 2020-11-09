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
from nuitka.Tracing import general, postprocessing_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getNullOutput
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    getFileList,
)
from nuitka.utils.Utils import getArchitecture, getOS


def packDistFolderToOnefile(dist_dir, binary_filename):
    """Pack distribution to onefile, i.e. a single file that is directly executable."""

    if getOS() == "Linux":
        packDistFolderToOnefileLinux(dist_dir, binary_filename)
    elif getOS() == "Windows":
        packDistFolderToOnefileWindows(dist_dir)
    else:
        general.warning("Onefile mode is not yet available on '%s'." % getOS())


def getAppImageToolPath():
    """Return the path of appimagetool (for Linux).

    Will prompt the user to download if not already cached in AppData
    directory for Nuitka.
    """

    appimagetool_url = (
        "https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-%s.AppImage"
        % getArchitecture()
    )

    return getCachedDownload(
        url=appimagetool_url,
        is_arch_specific=True,
        binary=appimagetool_url.rsplit("/", 1)[1],
        specifity=appimagetool_url.rsplit("/", 2)[1],
        message="""\
Nuitka will make use of AppImage (https://appimage.org/) tool
to combine Nuitka dist folder to onefile binary.""",
        reject="Nuitka does not work in --onefile on Linux without.",
        assume_yes_for_downloads=assumeYesForDownloads(),
    )


def packDistFolderToOnefileLinux(dist_dir, binary_filename):
    """Pack to onefile binary on Linux.

    Notes: This is mostly a wrapper around AppImage, which does all the heavy
    lifting.
    """

    # This might be possible to avoid being done with --runtime-file.
    apprun_filename = os.path.join(dist_dir, "AppRun")
    with open(apprun_filename, "w") as output_file:
        output_file.write(
            """\
#!/bin/sh
exec $APPDIR/%s $@"""
            % os.path.basename(binary_filename)
        )

    addFileExecutablePermission(apprun_filename)

    binary_basename = os.path.basename(getResultBasepath())

    icon_paths = getIconPaths()

    if not icon_paths:
        if os.path.exists("/usr/share/pixmaps/python.xpm"):
            icon_paths.append("/usr/share/pixmaps/python.xpm")

    if icon_paths:
        extension = os.path.splitext(icon_paths[0])[1].lower()

        shutil.copyfile(icon_paths[0], getResultBasepath() + extension)
    else:
        general.warning(
            "Cannot apply onefile unless icon file is specified. Yes, crazy."
        )
        return

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

    onefile_output_filename = getResultFullpath(onefile=True)

    # Starting the process while locked, so file handles are not duplicated.
    appimagetool_process = subprocess.Popen(
        (
            getAppImageToolPath(),
            dist_dir,
            "--comp",
            "xz",
            "-n",
            onefile_output_filename,
        ),
        shell=False,
        stderr=getNullOutput(),
        stdout=getNullOutput(),
    )

    # TODO: Exit code should be checked.
    result = appimagetool_process.wait()

    if not os.path.exists(onefile_output_filename):
        sys.exit(
            "Error, expected output file %s not created by AppImage."
            % onefile_output_filename
        )

    postprocessing_logger.info("Completed onefile execution.")

    assert result == 0, result


def _runOnefileScons(quiet):
    # Scons gets transported many details, that we express as variables, and
    # have checks for them, leading to many branches and statements,
    # pylint: disable=too-many-branches

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
    }

    # Ask Scons to cache on Windows, except where the directory is thrown
    # away. On non-Windows you can should use ccache instead.
    if not Options.isRemoveBuildDir() and getOS() == "Windows":
        options["cache_mode"] = "true"

    if Options.isLto():
        options["lto_mode"] = "true"

    if Options.shallDisableConsoleWindow():
        options["win_disable_console"] = "true"

    if Options.isShowScons():
        options["show_scons"] = "true"

    if Options.isMingw64():
        options["mingw_mode"] = "true"

    if Options.getMsvcVersion():
        msvc_version = Options.getMsvcVersion()

        msvc_version = msvc_version.replace("exp", "Exp")
        if "." not in msvc_version:
            msvc_version += ".0"

        options["msvc_version"] = msvc_version

    if getOS() == "Windows":
        options["noelf_mode"] = "true"

    if Options.isClang():
        options["clang_mode"] = "true"

    cpp_defines = Plugins.getPreprocessorSymbols()
    if cpp_defines:
        options["cpp_defines"] = ",".join(
            "%s%s%s" % (key, "=" if value else "", value or "")
            for key, value in cpp_defines.items()
        )

    link_libraries = Plugins.getExtraLinkLibraries()
    if link_libraries:
        options["link_libraries"] = ",".join(link_libraries)

    if Options.shallRunInDebugger():
        options["full_names"] = "true"

    if Options.assumeYesForDownloads():
        options["assume_yes_for_downloads"] = "true"

    result = SconsInterface.runScons(
        options=options, quiet=quiet, scons_filename="WindowsOnefile.scons"
    )

    # Exit if compilation failed.
    if not result:
        sys.exit("Error, one file bootstrap build for Windows failed.")


def packDistFolderToOnefileWindows(dist_dir):
    general.warning("Onefile mode is not yet working on '%s'." % getOS())

    try:
        from zstd import ZSTD_compress  # pylint: disable=I0021,import-error

        compress = 1 if Options.isExperimental("zstd") else 0
    except ImportError:
        general.warning(
            "Onefile mode cannot compress without 'zstd' module on '%s'." % getOS()
        )
        compress = 0

    # First need to create the binary, then append to it. For now, create as empty
    # then append

    postprocessing_logger.info(
        "Creating single file from dist folder, this may take a while."
    )

    onefile_output_filename = getResultFullpath(onefile=True)

    with open(onefile_output_filename, "wb"):
        pass

    _runOnefileScons(False)

    with open(onefile_output_filename, "ab") as output_file:
        start_pos = output_file.tell()

        output_file.write(b"KA")

        if compress:
            output_file.write(b"Y")
        else:
            output_file.write(b"X")

        for filename_full in getFileList(dist_dir):
            filename_relative = os.path.relpath(filename_full, dist_dir)

            if type(filename_relative) is not bytes:
                output_file.write(filename_relative.encode("utf8") + b"\0")
            else:
                output_file.write(filename_relative + b"\0")

            with open(filename_full, "rb") as input_file:
                if compress and Options.isExperimental("zstd"):
                    compressed = ZSTD_compress(input_file.read(), 9, getJobLimit())
                else:
                    compressed = input_file.read()

                output_file.write(struct.pack("q", len(compressed)))

                output_file.write(compressed)

        # Terminator empty filename.
        output_file.write(b"\0")

        output_file.write(struct.pack("q", start_pos))
