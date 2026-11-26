#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Runner for installer tests.

Tests option validation, script generation, installer icon conversion, and
rejection paths for the --windows-create-installer feature, as well as icon
reuse for the macOS DMG installer.
"""

import os
import subprocess
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.installer.MacOSDmg import getCreateDmgPath
from nuitka.tools.testing.Common import (
    createSearchMode,
    my_print,
    reportSkip,
    setup,
)
from nuitka.Tracing import installer_logger
from nuitka.utils.FileOperations import (
    addFileExecutablePermission,
    getFileContents,
    getNormalizedPathJoin,
    makePath,
    putTextFileContents,
)
from nuitka.utils.Images import convertImageToIconFormat
from nuitka.utils.Utils import isMacOS, isWin32Windows

_nuitka_bin = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "nuitka")

_scratch_dir = getNormalizedPathJoin(
    os.path.dirname(__file__), "..", "scratch", "installer_test"
)

# Image in PNG format, to test the conversion to the ICO format that NSIS
# requires for the installer icon.
_png_icon_path = getNormalizedPathJoin(
    os.path.dirname(__file__),
    "..",
    "..",
    "doc",
    "images",
    "Nuitka-Logo-Symbol.png",
)

_ico_icon_path = os.path.join(_scratch_dir, "nuitka-icon.ico")

_tests = []

_BASE_VALID_ARGS = [
    "--mode=standalone",
    "--windows-create-installer",
    "--product-name=InstalledNuitkaTestApp",
    "--product-version=1.0",
    "--company-name=Nuitka-Test",
    "--windows-installer-mode=user",
    "hello.py",
]


def register(name):
    def deco(func):
        _tests.append((name, func))
        return func

    return deco


def _invokeNuitka(search_mode, args, expected_exit_code):
    cmd = [sys.executable, _nuitka_bin] + args
    # pylint: disable=consider-using-with
    process = subprocess.Popen(
        cmd,
        cwd=_scratch_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, _stderr = process.communicate()
    exit_code = process.poll()
    stdout = stdout.decode("utf8", errors="replace")

    if exit_code != expected_exit_code:
        search_mode.onErrorDetected(
            "Unexpected exit %d (expected %d)" % (exit_code, expected_exit_code)
        )

    return stdout


def _checkOutput(search_mode, stdout, needle):
    if needle not in stdout:
        search_mode.onErrorDetected("Expected substring not found: %s" % needle)


def _prepareScratchDir():
    makePath(_scratch_dir)

    putTextFileContents(
        filename=os.path.join(_scratch_dir, "hello.py"),
        contents="print('Hello installer')\n",
        encoding="utf8",
    )
    putTextFileContents(
        filename=os.path.join(_scratch_dir, "license.txt"),
        contents="Installer test license.\n",
        encoding="utf8",
    )


def _getInstallerScriptContent():
    build_dirs = [
        os.path.join(_scratch_dir, entry)
        for entry in os.listdir(_scratch_dir)
        if entry.endswith(".installer-build")
    ]

    assert build_dirs, "no .installer-build directory found"

    return getFileContents(
        filename=os.path.join(max(build_dirs, key=os.path.getmtime), "installer.nsi"),
        encoding="utf8",
    )


def _getInstallerIconPath():
    for line in _getInstallerScriptContent().splitlines():
        if line.startswith("!define MUI_ICON "):
            parts = line.split('"')

            if len(parts) == 3:
                return parts[1]

            return None

    return None


def _checkInstallerIcon(search_mode, must_not_contain):
    icon_path = _getInstallerIconPath()

    if icon_path is None:
        search_mode.onErrorDetected("no 'MUI_ICON' definition in the installer script")
    elif must_not_contain is not None and must_not_contain in icon_path:
        search_mode.onErrorDetected(
            "installer icon path contains %r: %s" % (must_not_contain, icon_path)
        )
    elif not icon_path.lower().endswith(".ico"):
        search_mode.onErrorDetected(
            "installer icon is not in ICO format: %s" % icon_path
        )
    elif not os.path.isfile(icon_path):
        search_mode.onErrorDetected(
            "installer icon file does not exist: %s" % icon_path
        )


def _getIcoIconPath():
    """Convert the repository PNG image to an ICO file, once.

    Returns:
        Filename of the converted icon.
    """
    if not os.path.isfile(_ico_icon_path):
        convertImageToIconFormat(
            logger=installer_logger,
            image_filename=_png_icon_path,
            converted_icon_filename=_ico_icon_path,
        )

    return _ico_icon_path


def _shallSkipIconTest(test_name):
    if not isWin32Windows():
        reportSkip("Not on Windows", ".", test_name)
        return True

    try:
        import imageio  # pylint: disable=I0021,import-error,unused-import
    except ImportError:
        reportSkip("'imageio' is not installed", ".", test_name)
        return True

    return False


def _shallSkipDmgIconTest(test_name):
    if not isMacOS():
        reportSkip("Not on macOS", ".", test_name)
        return True

    if getCreateDmgPath() is None:
        reportSkip("'create-dmg' is not installed", ".", test_name)
        return True

    try:
        import imageio  # pylint: disable=I0021,import-error,unused-import
    except ImportError:
        reportSkip("'imageio' is not installed", ".", test_name)
        return True

    return False


def _getCreateDmgWrapperDir():
    create_dmg_path = getCreateDmgPath()
    wrapper_dir = os.path.join(_scratch_dir, "create-dmg-wrapper")
    makePath(wrapper_dir)

    wrapper_path = os.path.join(wrapper_dir, "create-dmg")
    putTextFileContents(
        filename=wrapper_path,
        # Finder automation is unavailable in headless test environments.
        contents='#!/bin/bash\nexec "%s" --sandbox-safe "$@"\n' % create_dmg_path,
        encoding="utf8",
    )
    addFileExecutablePermission(wrapper_path)

    return wrapper_dir


def _mountDmg(dmg_path):
    # pylint: disable=consider-using-with
    process = subprocess.Popen(
        ("hdiutil", "attach", "-nobrowse", "-readonly", dmg_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, _stderr = process.communicate()

    if process.poll() != 0:
        return None

    for line in stdout.decode("utf8", errors="replace").splitlines():
        parts = line.split("\t")

        if len(parts) >= 3 and parts[-1].startswith("/Volumes/"):
            return parts[-1]

    return None


def _checkDmgVolumeIcon(search_mode, dmg_path):
    if not os.path.isfile(dmg_path):
        search_mode.onErrorDetected("DMG file does not exist: %s" % dmg_path)
        return

    mount_path = _mountDmg(dmg_path)

    if mount_path is None:
        search_mode.onErrorDetected("Could not mount DMG file: %s" % dmg_path)
        return

    try:
        volume_icon_path = os.path.join(mount_path, ".VolumeIcon.icns")
        bundle_icon_path = os.path.join(
            mount_path, "hello.app", "Contents", "Resources", "Icons.icns"
        )

        if not os.path.isfile(volume_icon_path):
            search_mode.onErrorDetected("DMG has no '.VolumeIcon.icns' file")
        elif not os.path.isfile(bundle_icon_path):
            search_mode.onErrorDetected("DMG app bundle has no 'Icons.icns' file")
        else:
            volume_icon = getFileContents(filename=volume_icon_path, mode="rb")

            if volume_icon[:4] != b"icns":
                search_mode.onErrorDetected("DMG volume icon is not an ICNS file")
            elif volume_icon != getFileContents(filename=bundle_icon_path, mode="rb"):
                search_mode.onErrorDetected(
                    "DMG volume icon differs from the app bundle icon"
                )
    finally:
        subprocess.call(("hdiutil", "detach", mount_path))


@register("reject_missing_product_name")
def reject_missing_product_name(search_mode):
    args = [a for a in _BASE_VALID_ARGS if not a.startswith("--product-name")]
    _invokeNuitka(search_mode, args, expected_exit_code=1)


@register("reject_missing_product_version")
def reject_missing_product_version(search_mode):
    args = [a for a in _BASE_VALID_ARGS if not a.startswith("--product-version")]
    _invokeNuitka(search_mode, args, expected_exit_code=1)


@register("reject_missing_company_name")
def reject_missing_company_name(search_mode):
    args = [a for a in _BASE_VALID_ARGS if not a.startswith("--company-name")]
    _invokeNuitka(search_mode, args, expected_exit_code=1)


@register("reject_accelerated")
def reject_accelerated(search_mode):
    args = [
        "--mode=accelerated",
        "--windows-create-installer",
        "--product-name=InstalledNuitkaTestApp",
        "--product-version=1.0",
        "--company-name=Nuitka-Test",
        "hello.py",
    ]
    _invokeNuitka(search_mode, args, expected_exit_code=1)


@register("reject_bad_shortcuts")
def reject_bad_shortcuts(search_mode):
    args = _BASE_VALID_ARGS + ["--windows-installer-shortcuts=desktop,taskbar"]
    stdout = _invokeNuitka(search_mode, args, expected_exit_code=2)
    _checkOutput(search_mode, stdout, "invalid choice")


@register("reject_bad_mode")
def reject_bad_mode(search_mode):
    args = [a for a in _BASE_VALID_ARGS if not a.startswith("--windows-installer-mode")]
    args.append("--windows-installer-mode=admin")
    _invokeNuitka(search_mode, args, expected_exit_code=2)


@register("generate_nsi")
def generate_nsi(search_mode):
    license_path = os.path.join(_scratch_dir, "license.txt")

    args = _BASE_VALID_ARGS + [
        "--windows-installer-shortcuts=desktop,start-menu",
        "--windows-installer-license-file=%s" % license_path,
        "--windows-installer-output=test-output-setup.exe",
    ]
    _invokeNuitka(search_mode, args, expected_exit_code=0)

    content = _getInstallerScriptContent()

    checks = [
        'Name "InstalledNuitkaTestApp"',
        'ProductName" "InstalledNuitkaTestApp"',
        'CompanyName" "Nuitka-Test"',
        'FileVersion" "1.0"',
        'ProductVersion" "1.0"',
        "Desktop Shortcut",
        "Start Menu Shortcut",
        "MultiUser",
    ]
    for check in checks:
        if check not in content:
            search_mode.onErrorDetected("expected token not found: %s" % check)


@register("generate_nsi_icon_conversion")
def generate_nsi_icon_conversion(search_mode):
    if _shallSkipIconTest("generate_nsi_icon_conversion"):
        return

    args = _BASE_VALID_ARGS + ["--windows-icon-from-ico=%s" % _png_icon_path]
    _invokeNuitka(search_mode, args, expected_exit_code=0)

    _checkInstallerIcon(search_mode, must_not_contain=None)


@register("generate_nsi_icon_index")
def generate_nsi_icon_index(search_mode):
    if _shallSkipIconTest("generate_nsi_icon_index"):
        return

    args = _BASE_VALID_ARGS + ["--windows-icon-from-ico=%s#0" % _getIcoIconPath()]
    _invokeNuitka(search_mode, args, expected_exit_code=0)

    _checkInstallerIcon(search_mode, must_not_contain="#")


@register("generate_dmg_icon_conversion")
def generate_dmg_icon_conversion(search_mode):
    if _shallSkipDmgIconTest("generate_dmg_icon_conversion"):
        return

    args = [
        "--mode=app",
        "--macos-create-installer",
        "--macos-installer-output=test-output.dmg",
        "--macos-app-icon=%s" % _png_icon_path,
        "hello.py",
    ]

    wrapper_dir = _getCreateDmgWrapperDir()
    old_path = os.environ.get("PATH", "")

    os.environ["PATH"] = wrapper_dir + os.pathsep + old_path
    try:
        _invokeNuitka(search_mode, args, expected_exit_code=0)
    finally:
        os.environ["PATH"] = old_path

    _checkDmgVolumeIcon(
        search_mode, dmg_path=os.path.join(_scratch_dir, "test-output.dmg")
    )


def main():
    setup(suite="installer", needs_io_encoding=True)

    _prepareScratchDir()

    search_mode = createSearchMode()

    for test_name, test_func in _tests:
        active = search_mode.consider(dirname=None, filename=test_name)

        if not active:
            continue

        my_print("Running installer test:", test_name)

        test_func(search_mode)

    search_mode.finish()


if __name__ == "__main__":
    main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
