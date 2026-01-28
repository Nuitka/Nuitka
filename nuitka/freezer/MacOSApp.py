#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""For macOS application bundle creation"""

import os

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.options.Options import (
    getLegalInformation,
    getMacOSAppConsoleMode,
    getMacOSAppName,
    getMacOSAppProtectedResourcesAccesses,
    getMacOSAppVersion,
    getMacOSIconPaths,
    getMacOSSignedAppName,
    isMacOSBackgroundApp,
    isMacOSUiElementApp,
    isStandaloneMode,
    shallMacOSProhibitMultipleInstances,
)
from nuitka.OutputDirectories import (
    getResultFullpath,
    getResultRunFilename,
    getSourceDirectoryPath,
    getStandaloneDirectoryPath,
)
from nuitka.Tracing import options_logger
from nuitka.utils.FileOperations import copyFile, makePath, openTextFile
from nuitka.utils.Images import convertImageToIconFormat

from .IncludedDataFiles import (
    addIncludedDataFile,
    makeIncludedGeneratedDataFile,
)


def _writePlist(filename, data):
    """Helper to write a plist file for macOS."""
    # Late import, not always used.
    import plistlib

    if str is bytes:
        plist_contents = plistlib.writePlistToString(data)
    else:
        plist_contents = plistlib.dumps(data)

    with openTextFile(filename=filename, mode="wb") as plist_file:
        plist_file.write(plist_contents)


def createPlistInfoFile(logger):
    # Many details, pylint: disable=too-many-locals
    if isStandaloneMode():
        bundle_dir = os.path.dirname(
            getStandaloneDirectoryPath(bundle=True, real=False)
        )
    else:
        bundle_dir = os.path.dirname(getResultRunFilename(onefile=False))

    result_filename = getResultFullpath(onefile=False, real=True)
    executable_name = os.path.basename(result_filename)
    app_name = getMacOSAppName() or executable_name
    signed_app_name = getMacOSSignedAppName() or app_name
    app_version = getMacOSAppVersion() or "1.0"

    infos = OrderedDict(
        [
            ("CFBundleDisplayName", app_name),
            ("CFBundleName", app_name),
            ("CFBundleIdentifier", signed_app_name),
            ("CFBundleExecutable", executable_name),
            ("CFBundleInfoDictionaryVersion", "6.0"),
            ("CFBundlePackageType", "APPL"),  # spell-checker: ignore appl
            ("CFBundleShortVersionString", app_version),
        ]
    )

    icon_paths = getMacOSIconPaths()

    if icon_paths:
        assert len(icon_paths) == 1
        icon_path = icon_paths[0]

        # Convert to single macOS .icns file if necessary
        # spell-checker: ignore icns
        if not icon_path.endswith(".icns"):
            logger.info(
                "File '%s' is not in macOS icon format, converting to it." % icon_path
            )

            icon_build_path = os.path.join(
                getSourceDirectoryPath(onefile=False, create=False),
                "icons",
            )
            makePath(icon_build_path)
            converted_icon_path = os.path.join(
                icon_build_path,
                "Icons.icns",
            )

            convertImageToIconFormat(
                logger=logger,
                image_filename=icon_path,
                converted_icon_filename=converted_icon_path,
            )
            icon_path = converted_icon_path

        icon_name = os.path.basename(icon_path)
        resources_dir = os.path.join(bundle_dir, "Resources")
        makePath(resources_dir)

        copyFile(icon_path, os.path.join(resources_dir, icon_name))

        infos["CFBundleIconFile"] = icon_name

    # Console mode, which is why we have to use bundle in the first place typically.
    if isMacOSBackgroundApp():
        infos["LSBackgroundOnly"] = True
    elif isMacOSUiElementApp():
        infos["LSUIElement"] = True  # spell-checker: ignore LSUI
    else:
        infos["NSHighResolutionCapable"] = True

    if shallMacOSProhibitMultipleInstances():
        infos["LSMultipleInstancesProhibited"] = True

    legal_text = getLegalInformation()

    if legal_text is not None:
        infos["NSHumanReadableCopyright"] = legal_text

    for (
        resource_name,
        resource_desc,
        _entitlement_name,
    ) in getMacOSAppProtectedResourcesAccesses():
        if resource_name in infos:
            return logger.sysexit(
                "Duplicate value for '%s' is not allowed." % resource_name
            )

        infos[resource_name] = resource_desc

    filename = os.path.join(bundle_dir, "Info.plist")

    _writePlist(filename, infos)


def createEntitlementsInfoFile():
    entitlements_dict = {}
    for (
        _protected_resource,
        _description,
        entitlement_name,
    ) in getMacOSAppProtectedResourcesAccesses():
        if type(entitlement_name) is tuple:
            for entitlement in entitlement_name:
                entitlements_dict[entitlement] = True
        elif type(entitlement_name) is str:
            entitlements_dict[entitlement_name] = True
        else:
            assert False, entitlement_name

    if not entitlements_dict:
        return None

    if entitlements_dict:
        entitlements_filename = os.path.join(
            getSourceDirectoryPath(onefile=False, create=False), "entitlements.plist"
        )

        _writePlist(entitlements_filename, entitlements_dict)

    return entitlements_filename


_macos_app_console_script = """
#!/bin/bash

# 1. Derive the binary name from this script's name
#    basename "$0" gets the filename (e.g., "MyApp" or "MyApp.sh")
SCRIPT_NAME=$(basename "$0")

# 2. Check execution context (GUI vs Terminal)
if [ ! -t 1 ]; then
    # CASE A: GUI Launch (Finder/Dock)
    # We are invisible. Re-launch THIS script inside Terminal.app.
    # "$0" ensures we re-run this exact script file.
    exec open -a Terminal "$0"
fi

# 3. CASE B: Terminal Launch
# We are now visible. Fix the environment.

#    Get the bundle directory (Contents/MacOS)
DIR=$(cd "$(dirname "$0")"; pwd)

#    Change Directory to the bundle so relative paths work
cd "$DIR"

#    "${variable%.sh}" strips the .sh suffix (if any exists)
#    So "MyApp.sh" becomes "MyApp", and "MyApp" stays "MyApp"
TARGET_BINARY="${SCRIPT_NAME%.sh}"

#    Execute the actual binary, passing along any arguments ("$@")
#    We use 'exec' so the binary takes over this process ID.
exec "./$TARGET_BINARY" "$@"
"""


def addIncludedDataFilesFromMacOSAppOptions():
    if getMacOSAppConsoleMode() == "force":
        result_filename = getResultFullpath(onefile=False, real=True)
        script_filename = os.path.basename(result_filename) + ".sh"

        addIncludedDataFile(
            makeIncludedGeneratedDataFile(
                data=_macos_app_console_script,
                dest_path=script_filename,
                reason="Required for macOS app force console mode.",
                tracer=options_logger,
                tags="script",
            )
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
