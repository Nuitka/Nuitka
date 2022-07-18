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
""" For macOS application bundle creation

"""
import os

from nuitka import Options, OutputDirectories
from nuitka.containers.OrderedDicts import OrderedDict

from .FileOperations import copyFile, makePath, openTextFile
from .Images import convertImageToIconFormat


def createPlistInfoFile(logger, onefile):
    # Many details, pylint: disable=too-many-locals

    import plistlib

    if Options.isStandaloneMode():
        bundle_dir = os.path.dirname(OutputDirectories.getStandaloneDirectoryPath())
    else:
        bundle_dir = os.path.dirname(
            OutputDirectories.getResultRunFilename(onefile=onefile)
        )

    result_filename = OutputDirectories.getResultFullpath(onefile=onefile)
    app_name = Options.getMacOSAppName() or os.path.basename(result_filename)

    signed_app_name = Options.getMacOSSignedAppName() or app_name
    app_version = Options.getMacOSAppVersion() or "1.0"

    # TODO: We want an OrderedDict probably for stability.
    infos = OrderedDict(
        [
            ("CFBundleDisplayName", app_name),
            ("CFBundleName", app_name),
            ("CFBundleIdentifier", signed_app_name),
            ("CFBundleExecutable", app_name),
            ("CFBundleInfoDictionaryVersion", "6.0"),
            ("CFBundlePackageType", "APPL"),
            ("CFBundleShortVersionString", app_version),
        ]
    )

    icon_paths = Options.getIconPaths()

    if icon_paths:
        assert len(icon_paths) == 1
        icon_path = icon_paths[0]

        # Convert to single macOS .icns file if necessary
        if not icon_path.endswith(".icns"):
            logger.info(
                "File '%s' is not in macOS icon format, converting to it." % icon_path
            )

            icon_build_path = os.path.join(
                OutputDirectories.getSourceDirectoryPath(onefile=onefile),
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
                icon_filename=converted_icon_path,
            )
            icon_path = converted_icon_path

        icon_name = os.path.basename(icon_path)
        resources_dir = os.path.join(bundle_dir, "Resources")
        makePath(resources_dir)

        copyFile(icon_path, os.path.join(resources_dir, icon_name))

        infos["CFBundleIconFile"] = icon_name

    # Console mode, which is why we have to use bundle in the first place typically.
    if Options.shallDisableConsoleWindow():
        infos["NSHighResolutionCapable"] = True
    else:
        infos["LSBackgroundOnly"] = True

    for resource_name, resource_desc in Options.getMacOSAppProtectedResourcesAccesses():
        if resource_name in infos:
            logger.sysexit("Duplicate value for '%s' is not allowed." % resource_name)

        infos[resource_name] = resource_desc

    filename = os.path.join(bundle_dir, "Info.plist")

    if str is bytes:
        plist_contents = plistlib.writePlistToString(infos)
    else:
        plist_contents = plistlib.dumps(infos)

    with openTextFile(filename=filename, mode="wb") as plist_file:
        plist_file.write(plist_contents)
