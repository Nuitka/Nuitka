#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""For macOS application bundle creation"""

import os

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.options.Options import (
    getLegalInformation,
    getMacOSAppName,
    getMacOSAppProtectedResourcesAccesses,
    getMacOSAppVersion,
    getMacOSConsoleMode,
    getMacOSIconPaths,
    getMacOSSignedAppName,
    isMacOSBackgroundApp,
    isMacOSUiElementApp,
    isOnefileMode,
    isStandaloneMode,
    shallMacOSProhibitMultipleInstances,
)
from nuitka.OutputDirectories import (
    getResultFullpath,
    getResultRunFilename,
    getSourceDirectoryPath,
    getStandaloneDirectoryPath,
)
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    copyFile,
    makePath,
    openTextFile,
    putTextFileContents,
)
from nuitka.utils.Images import convertImageToIconFormat


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


def createPlistInfoFile(logger, onefile, force_console):
    # Many details, pylint: disable=too-many-branches,too-many-locals
    if isStandaloneMode():
        bundle_dir = os.path.dirname(
            getStandaloneDirectoryPath(bundle=True, real=False)
        )
    else:
        bundle_dir = os.path.dirname(getResultRunFilename(onefile=onefile))

    result_filename = getResultFullpath(onefile=onefile, real=True)
    app_name = getMacOSAppName() or os.path.basename(result_filename)

    if force_console:
        script_filename = result_filename + ".sh"

        putTextFileContents(
            filename=script_filename,
            contents=_macos_app_console_script,
        )
        addFileExecutablePermission(script_filename)

        executable_name = os.path.basename(script_filename)
    else:
        executable_name = os.path.basename(
            getResultFullpath(onefile=isOnefileMode(), real=True)
        )

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
                getSourceDirectoryPath(onefile=onefile, create=False),
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


_terminal_launcher_script_template = """\
#!/bin/bash
NUITKA_BINARY='%s'

# Check if stdout is associated with a terminal
if [ ! -t 1 ]; then
    # Launched via GUI (Finder/Dock) - relaunch in Terminal
    exec open -a Terminal "$0"
fi

# Running in Terminal - change to bundle directory and exec binary
DIR=$(cd "$(dirname "$0")"; pwd)
cd "$DIR"
exec "./${NUITKA_BINARY}_bin"
"""


def createTerminalLauncherScript(macos_dir, binary_name):
    """Create a shell script that launches the binary in Terminal if needed.

    When a macOS app bundle is launched from Finder (not from Terminal), stdin/stdout
    are not connected to a terminal. This script detects that and relaunches the app
    in Terminal.app, then execs the actual binary.

    Args:
        macos_dir: Path to the Contents/MacOS directory in the app bundle.
        binary_name: The original name of the binary (will be used for launcher).
    """
    script_content = _terminal_launcher_script_template % binary_name

    script_path = os.path.join(macos_dir, binary_name)

    with openTextFile(filename=script_path, mode="w") as script_file:
        script_file.write(script_content)

    # Make the script executable
    os.chmod(script_path, 0o755)


def createEntitlementsInfoFile():
    entitlements_dict = {}
    for (
        _protected_resource,
        _description,
        entitlement_name,
    ) in getMacOSAppProtectedResourcesAccesses():
        entitlements_dict[entitlement_name] = True

    if not entitlements_dict:
        return None

    if entitlements_dict:
        entitlements_filename = os.path.join(
            getSourceDirectoryPath(onefile=False, create=False), "entitlements.plist"
        )

        _writePlist(entitlements_filename, entitlements_dict)

    return entitlements_filename


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
