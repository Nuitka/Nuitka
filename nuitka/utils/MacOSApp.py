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
""" For macOS application bundle creation

"""
import os

from nuitka import Options, OutputDirectories

from .FileOperations import openTextFile


def createPlistInfoFile():
    import plistlib

    if Options.isStandaloneMode():
        bundle_dir = os.path.dirname(OutputDirectories.getStandaloneDirectoryPath())
    else:
        bundle_dir = os.path.dirname(
            OutputDirectories.getResultRunFilename(onefile=False)
        )

    result_filename = OutputDirectories.getResultFullpath(onefile=False)
    app_name = Options.getMacOSAppName() or os.path.basename(result_filename)

    signed_app_name = Options.getMacOSSignedAppName() or app_name

    # TODO: We want an OrderedDict probably for stability.
    infos = {
        "CFBundleDisplayName": app_name,
        "CFBundleName": app_name,
        "CFBundleIdentifier": signed_app_name,
        "CFBundleExecutable": app_name,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundlePackageType": "APPL",
        # TODO: Make this an option too.
        "CFBundleShortVersionString": "1.0.0",
    }

    icon_paths = Options.getIconPaths()

    if icon_paths:
        # TODO: Convert/merge to single macOS .icns file if necessary
        infos["CFBundleIconFile"] = os.path.basename(icon_paths[0])

    # Console mode, which is why we have to use bundle in the first place typically.
    if Options.shallDisableConsoleWindow():
        infos["NSHighResolutionCapable"] = True
    else:
        infos["LSBackgroundOnly"] = True

    filename = os.path.join(bundle_dir, "Info.plist")

    if str is bytes:
        plist_contents = plistlib.writePlistToString(infos)
    else:
        plist_contents = plistlib.dumps(infos)

    with openTextFile(filename=filename, mode="wb") as plist_file:
        plist_file.write(plist_contents)
