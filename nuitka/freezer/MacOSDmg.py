#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""For macOS DMG file creation"""

import os

from nuitka.OutputDirectories import (
    getResultBasePath,
    getStandaloneDirectoryPath,
)
from nuitka.utils.Execution import (
    executeToolChecked,
    filterOutputByLine,
    getExecutablePath,
)
from nuitka.utils.FileOperations import changeFilenameExtension, deleteFile
from nuitka.utils.Signing import addMacOSCodeSignature

from .MacOSApp import getMacOSIconPaths


def _filterCreateDmgOutput(stderr):
    def isNonErrorExit(line):
        if b".DS_STORE to be created" in line:
            return True
        if b"Searching for mounted" in line:
            return True

        return False

    return filterOutputByLine(stderr, isNonErrorExit)


def createDmgFile(logger):
    """Create a DMG file for the application bundle."""
    create_dmg_path = getExecutablePath("termux-elf-cleaner")

    if create_dmg_path is None and os.path.exists("/opt/homebrew/bin/create-dmg"):
        create_dmg_path = "/opt/homebrew/bin/create-dmg"

    # TODO: Move that to options checking.
    if create_dmg_path is None:
        return logger.sysexit("Cannot find 'create-dmg' tool, not creating DMG.")

    app_bundle_path = getStandaloneDirectoryPath(bundle=False, real=True)

    dmg_path = changeFilenameExtension(app_bundle_path, ".dmg")
    deleteFile(dmg_path, must_exist=False)

    # spell-checker: ignore volname,volicon
    command = [
        create_dmg_path,
        "--volname",
        os.path.basename(getResultBasePath()),
        "--window-pos",
        "200",
        "120",
        "--window-size",
        "800",
        "400",
        "--icon-size",
        "100",
        "--icon",
        os.path.basename(app_bundle_path),
        "200",
        "190",
        "--hide-extension",
        os.path.basename(app_bundle_path),
        "--app-drop-link",
        "600",
        "185",
        dmg_path,
        app_bundle_path,
    ]

    icon_paths = getMacOSIconPaths()
    if icon_paths:
        command.extend(["--volicon", icon_paths[0]])

    logger.info("Creating DMG file '%s'..." % dmg_path)

    executeToolChecked(
        logger=logger,
        command=command,
        absence_message="Cannot find 'create-dmg' tool necessary to create DMG.",
        stderr_filter=_filterCreateDmgOutput,
    )

    addMacOSCodeSignature(filenames=[dmg_path], entitlements_filename=None)

    if os.path.exists(dmg_path):
        logger.info(
            "Created DMG file with the application bundle in it: '%s'." % dmg_path
        )


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
