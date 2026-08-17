#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""AppImage backend for Linux installer creation.

Creates an AppImage from the compiled dist folder or onefile binary using
the ``appimagetool`` utility. The AppDir is assembled from the existing
payload, a generated AppRun script, and the desktop file and icon already
produced by ``LinuxApp.py``. The tool is looked up from an explicit path,
then ``PATH``, and as a last resort from a cached download of the official
upstream release. It is not redistributed or mirrored by Nuitka; the
download is cached locally for the user only.
"""

import os
import stat
import subprocess

from nuitka.freezer.LinuxApp import createLinuxAppFiles
from nuitka.options.Options import assumeYesForDownloads
from nuitka.Tracing import installer_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import (
    check_output,
    executeToolChecked,
    getExecutablePath,
)
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    changeFilenameExtension,
    copyFile,
    copyTree,
    deleteFile,
    makePath,
    renameFile,
)
from nuitka.utils.Utils import getArchitecture

_appimagetool_version = "continuous"
_appimagetool_detected_version = None


def getAppImageToolVersion():
    """*str*, the detected appimagetool version, or the download version."""
    if _appimagetool_detected_version is not None:
        return _appimagetool_detected_version

    return _appimagetool_version


_appimagetool_download_url = (
    "https://github.com/AppImage/AppImageKit/releases/download/"
    "%(version)s/appimagetool-%(arch)s.AppImage"
    % {"version": _appimagetool_version, "arch": getArchitecture()}
)


def _getAppImageToolPath(installer_tool_path):
    """Locate the ``appimagetool`` binary to use.

    Notes:
        Lookup order is the explicitly given path, then ``PATH``, then a
        cached download of the official upstream release into the standard
        Nuitka tool cache.
    """
    # Singleton, pylint: disable=global-statement
    global _appimagetool_detected_version

    if installer_tool_path is not None:
        tool_path = getExecutablePath("appimagetool", installer_tool_path)

        if tool_path is None:
            return installer_logger.sysexit(
                "Error, appimagetool binary '%s' as given with "
                "'--linux-installer-appimagetool-path' does not exist."
                % installer_tool_path
            )
    else:
        tool_path = getExecutablePath("appimagetool")

        if tool_path is None:
            tool_path = getCachedDownload(
                name="appimagetool",
                url=_appimagetool_download_url,
                is_arch_specific=getArchitecture(),
                specificity=_appimagetool_version,
                binary=os.path.basename(_appimagetool_download_url),
                unzip=False,
                flatten=False,
                message="""\
Nuitka will download appimagetool from the official upstream release to \
create the Linux installer, it will be cached for future use.""",
                reject="Error, appimagetool is required to create a Linux installer.",
                assume_yes_for_downloads=assumeYesForDownloads(),
                download_ok=True,
            )

            if tool_path is not None:
                addFileExecutablePermission(tool_path)

        if tool_path is None:
            return None

    if _appimagetool_detected_version is None:
        version_output = check_output(
            [tool_path, "--version"], stderr=subprocess.STDOUT
        )

        if str is not bytes:
            version_output = version_output.decode("utf8")

        _appimagetool_detected_version = version_output.strip()

    return tool_path


_SELF_DIR = '$(dirname "$(readlink -f "$0")")'


def _makeAppRunScript(appdir, main_binary_name):
    apprun_path = os.path.join(appdir, "AppRun")

    with open(apprun_path, "w", encoding="utf8") as f:
        f.write("""\
#!/bin/sh
SELF="%s"
exec "$SELF"/"%s" "$@"
""" % (_SELF_DIR, main_binary_name))

    os.chmod(
        apprun_path,
        stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
    )


def _populateAppDir(appdir, payload_dir, main_binary_name, external_files):
    createLinuxAppFiles(logger=installer_logger, onefile=False)

    for item in os.listdir(payload_dir):
        src = os.path.join(payload_dir, item)
        dst = os.path.join(appdir, item)

        if os.path.isdir(src) and not os.path.islink(src):
            if item != "__pycache__":
                copyTree(src, dst)
        else:
            copyFile(src, dst)

    for external_file in external_files:
        src = os.path.join(payload_dir, external_file)
        dst = os.path.join(appdir, os.path.basename(external_file))

        copyFile(src, dst)

    _makeAppRunScript(appdir, main_binary_name)

    main_binary_path = os.path.join(appdir, main_binary_name)

    if os.path.isfile(main_binary_path):
        addFileExecutablePermission(main_binary_path)

    for entry in os.listdir(appdir):
        if entry.endswith(".metainfo.xml"):
            metainfo_src = os.path.join(appdir, entry)
            metainfo_dir = os.path.join(appdir, "usr", "share", "metainfo")
            metainfo_dst = os.path.join(
                metainfo_dir, entry.replace(".metainfo.xml", ".appdata.xml")
            )
            makePath(metainfo_dir)
            renameFile(metainfo_src, metainfo_dst)

            break


def createAppImage(  # pylint: disable=unused-argument
    product_name,
    product_version,
    company_name,
    file_description,
    output_filename,
    payload_dir,
    payload_filename,
    main_binary_name,
    external_files,
    installer_tool_path,
):
    """Create an AppImage from the compiled payload.

    Notes:
        Product metadata fields are passed in for interface consistency
        with other backends but are currently unused; the desktop file
        and metainfo carry this information instead. The
        ``payload_filename`` parameter is kept for future onefile
        support and is currently unused.

    Returns:
        Filename of the created AppImage artifact, or exits on failure.
    """
    appimage_tool_path = _getAppImageToolPath(installer_tool_path)

    if appimage_tool_path is None:
        return installer_logger.sysexit(
            "Error, cannot find 'appimagetool'. Install it or use "
            "'--linux-installer-appimagetool-path' to specify its location."
        )

    if not os.path.isdir(payload_dir):
        return installer_logger.sysexit(
            "Error, AppImage creation currently requires standalone mode "
            "(not onefile)."
        )

    appdir = changeFilenameExtension(payload_dir, ".installer-build")
    makePath(appdir)

    _populateAppDir(appdir, payload_dir, main_binary_name, external_files)

    if output_filename is not None:
        output_filename = changeFilenameExtension(output_filename, ".AppImage")
    else:
        output_filename = changeFilenameExtension(payload_dir, ".AppImage")

    deleteFile(output_filename, must_exist=False)

    installer_logger.info("Creating AppImage '%s'..." % output_filename)

    command = [appimage_tool_path, "--no-appstream", appdir, output_filename]

    executeToolChecked(
        logger=installer_logger,
        command=command,
        absence_message="Cannot find 'appimagetool' needed to create an AppImage.",
        stderr_is_fatal=False,
    )

    if not os.path.isfile(output_filename):
        return installer_logger.sysexit(
            "Error, failed to create AppImage '%s'." % output_filename
        )

    installer_logger.info("Created AppImage: '%s'." % output_filename)

    return output_filename


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
