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
import subprocess
import sys

from nuitka.Options import assumeYesForDownloads, getIconPaths
from nuitka.OutputDirectories import getResultBasepath, getResultFullpath
from nuitka.Tracing import general, postprocessing_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getNullOutput
from nuitka.utils.FileOperations import addFileExecutablePermission
from nuitka.utils.Utils import getArchitecture, getOS


def packDistFolderToOnefile(dist_dir, binary_filename):
    """Pack distribution to onefile, i.e. a single file that is directly executable."""

    if getOS() == "Linux":
        packDistFolderToOnefileLinux(dist_dir, binary_filename)
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
