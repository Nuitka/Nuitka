#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Runner for Windows installer tests.

Tests option validation, script generation, and rejection paths for the
--windows-create-installer feature.
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

from nuitka.tools.testing.Common import createSearchMode, my_print, setup
from nuitka.utils.FileOperations import getFileContents

_nuitka_bin = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "nuitka")

_scratch_dir = os.path.join(
    os.path.dirname(__file__), "..", "scratch", "installer_test"
)

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

    installer_build_dir = None

    for entry in os.listdir(_scratch_dir):
        if entry.endswith(".installer-build"):
            installer_build_dir = os.path.join(_scratch_dir, entry)
            break

    assert installer_build_dir is not None, "no .installer-build directory found"

    nsi_path = os.path.join(installer_build_dir, "installer.nsi")
    content = getFileContents(filename=nsi_path, encoding="utf8")

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


def main():
    setup(suite="installer", needs_io_encoding=True)

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
