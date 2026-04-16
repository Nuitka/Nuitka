#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Nuitka compiling itself and compiling itself in compiled form again.

This should not only give no errors, but the same source for modules being
compiled when Nuitka is running compiled and uncompiled, so we can discover
changes in order of execution in this test.
"""

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

import shutil
import subprocess

from nuitka.reports.CompilationReportReader import (
    getCompilationOutputBinary,
    parseCompilationReport,
)
from nuitka.tools.Basics import addPYTHONPATH
from nuitka.tools.testing.Common import (
    getPythonSysPath,
    getTempDir,
    my_print,
    setup,
    test_logger,
    withPythonPathChange,
)
from nuitka.utils.Diffs import compareDirectories
from nuitka.utils.Execution import wrapCommandForDebuggerForSubprocess
from nuitka.utils.FileOperations import (
    copyTree,
    deleteFile,
    getFileList,
    getSubDirectories,
    listDir,
    removeDirectory,
)
from nuitka.utils.Importing import getExtensionModuleSuffix
from nuitka.Version import getCommercialVersion

nuitka_main_path = os.path.join("..", "..", "bin", "nuitka")

tmp_dir = getTempDir()

# Cannot detect this more automatic, so we need to list them, avoiding
# the ones not needed.
PACKAGE_LIST = [
    "nuitka",
    "nuitka/build",
    "nuitka/code_generation",
    "nuitka/code_generation/c_types",
    "nuitka/code_generation/templates",
    "nuitka/containers",
    "nuitka/finalizations",
    "nuitka/freezer",
    "nuitka/importing",
    "nuitka/nodes",
    "nuitka/nodes/shapes",
    "nuitka/optimizations",
    "nuitka/options",
    "nuitka/pgo",
    "nuitka/plugins",
    "nuitka/plugins/commercial",
    "nuitka/plugins/standard",
    "nuitka/reports",
    "nuitka/specs",
    "nuitka/tree",
    "nuitka/format",
    "nuitka/package_config",
    "nuitka/utils",
]

if not getCommercialVersion():
    PACKAGE_LIST.remove("nuitka/plugins/commercial")

exe_suffix = ".exe" if os.name == "nt" else ".bin"


def _traceCompilation(path, pass_number):
    test_logger.info("Compiling '%s' (PASS %d)." % (path, pass_number))


def executePASS1():
    test_logger.info(
        "PASS 1: Compiling to many compiled modules from compiler running from .py files."
    )

    base_dir = os.path.join("..", "..")

    for package in PACKAGE_LIST:
        package = package.replace("/", os.path.sep)

        source_dir = os.path.join(base_dir, package)
        target_dir = package

        removeDirectory(
            path=target_dir,
            logger=test_logger,
            ignore_errors=False,
            extra_recommendation=None,
        )

        os.mkdir(target_dir)

        for path, filename in listDir(target_dir):
            if filename.endswith((".so", ".dylib")):
                os.unlink(path)

        for path, filename in listDir(source_dir):
            if not filename.endswith(".py"):
                continue

            if filename.startswith(".#"):
                continue

            if filename != "__init__.py":
                _traceCompilation(path=path, pass_number=1)

                command = [
                    os.environ["PYTHON"],
                    nuitka_main_path,
                    "--mode=module",
                    "--nofollow-imports",
                    "--output-dir=%s" % target_dir,
                    "--no-pyi-file",
                    path,
                ]
                command += os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

                my_print("Command: ", " ".join(command))

                result = subprocess.call(command)

                if result != 0:
                    sys.exit(result)
            else:
                shutil.copyfile(path, os.path.join(target_dir, filename))

    _traceCompilation(path=nuitka_main_path, pass_number=1)

    shutil.copyfile(nuitka_main_path, "nuitka-runner.py")

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--nofollow-imports",
        "--output-dir=.",
        "--python-flag=no_site",
        "--main=nuitka-runner.py",
        "--main=nuitka/tools/data_composer/DataComposer.py",
    ]
    command += os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

    my_print("Command: ", " ".join(command))
    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    shutil.move("nuitka-runner" + exe_suffix, "nuitka" + exe_suffix)

    scons_inline_copy_path = os.path.join(base_dir, "nuitka", "build", "inline_copy")

    if os.path.exists(scons_inline_copy_path):
        copyTree(scons_inline_copy_path, os.path.join("nuitka", "build", "inline_copy"))

    # Copy required data files.
    for filename in (
        "nuitka/build/Backend.scons",
        "nuitka/plugins/standard/standard.nuitka-package.config.yml",
        "nuitka/plugins/standard/stdlib3.nuitka-package.config.yml",
        "nuitka/plugins/standard/stdlib2.nuitka-package.config.yml",
    ):
        shutil.copyfile(
            os.path.join(base_dir, filename),
            filename,
        )

    copyTree(
        os.path.join(base_dir, "nuitka", "code_generation", "templates_c"),
        os.path.join("nuitka", "code_generation", "templates_c"),
    )

    copyTree(
        os.path.join(base_dir, "nuitka", "build", "static_src"),
        os.path.join("nuitka", "build", "static_src"),
    )
    copyTree(
        os.path.join(base_dir, "nuitka", "build", "include"),
        os.path.join("nuitka", "build", "include"),
    )

    # The data composer tool, use it by source.
    copyTree(
        os.path.join(base_dir, "nuitka", "tools"),
        os.path.join("nuitka", "tools"),
    )

    test_logger.info("OK.")


def compileAndCompareWith(nuitka, pass_number):
    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = "0"
    if "PYTHON_FROZEN_MODULES" not in os.environ:
        os.environ["PYTHON_FROZEN_MODULES"] = "off"

    base_dir = os.path.join("..", "..")

    for package in PACKAGE_LIST:
        package = package.replace("/", os.path.sep)

        source_dir = os.path.join(base_dir, package)

        for path, filename in listDir(source_dir):
            if not filename.endswith(".py"):
                continue

            if filename.startswith(".#"):
                continue

            path = os.path.join(source_dir, filename)

            if filename != "__init__.py":
                _traceCompilation(path=path, pass_number=pass_number)

                target = filename.replace(".py", ".build")

                target_dir = os.path.join(tmp_dir, target)

                removeDirectory(
                    logger=test_logger,
                    path=target_dir,
                    ignore_errors=False,
                    extra_recommendation=None,
                )

                command = [
                    nuitka,
                    "--mode=module",
                    "--output-dir=%s" % tmp_dir,
                    "--no-pyi-file",
                    "--nofollow-imports",
                    path,
                ]
                command += os.getenv("NUITKA_EXTRA_OPTIONS", "").split()

                my_print("Command: ", " ".join(command))
                exit_nuitka = subprocess.call(command)

                # In case of segfault or assertion triggered, run in debugger.
                if exit_nuitka in (-11, -6) and sys.platform != "nt":
                    command2 = wrapCommandForDebuggerForSubprocess(
                        command=command, debugger=os.getenv("NUITKA_DEBUGGER_CHOICE")
                    )
                    subprocess.call(command2)

                if exit_nuitka != 0:
                    my_print("An error exit %s occurred, aborting." % exit_nuitka)
                    sys.exit(exit_nuitka)

                has_diff = compareDirectories(
                    logger=test_logger,
                    my_print=my_print,
                    dir1=os.path.join(package, target),
                    dir2=target_dir,
                    ignore_suffixes=(
                        ".o",
                        ".os",
                        ".obj",
                        ".dblite",  # spell-checker: ignore dblite
                        ".tmp",
                        ".sconsign",  # spell-checker: ignore sconsign
                        ".txt",
                        ".bin",
                        ".const",
                        ".exp",
                        ".scons",
                    ),
                    ignore_substrings=(
                        "cache-",
                        "scons-debug",
                    ),
                )

                if has_diff:
                    sys.exit("There were differences!")

                shutil.rmtree(target_dir)

                for preferred in (True, False):
                    target_filename = filename.replace(
                        ".py", getExtensionModuleSuffix(preferred=preferred)
                    )

                    deleteFile(
                        path=os.path.join(tmp_dir, target_filename), must_exist=False
                    )


def executePASS2():
    test_logger.info(
        "PASS 2: Compiling from compiler running from entry '.exe' and many extension files."
    )

    with withPythonPathChange(getPythonSysPath()):
        # Windows will load the compiled modules (pyd) only from PYTHONPATH, so we
        # have to add it.
        if os.name == "nt":
            addPYTHONPATH(PACKAGE_LIST)

        compileAndCompareWith(
            nuitka=os.path.join(".", "nuitka" + exe_suffix), pass_number=2
        )

    # Cleanup, removing files that will otherwise confuse PASS3.
    for filename in getFileList("nuitka", only_suffixes=(".so", ".pyd")):
        deleteFile(filename, must_exist=True)
    for filename in getSubDirectories("nuitka"):
        if filename.endswith(".build"):
            removeDirectory(
                filename,
                logger=test_logger,
                ignore_errors=False,
                extra_recommendation=None,
            )

    test_logger.info("OK.")


def executePASS3():
    test_logger.info(
        "PASS 3: Compiling from compiler running from .py files to single .exe."
    )

    exe_path = os.path.join(tmp_dir, "nuitka-runner" + exe_suffix)

    if os.path.exists(exe_path):
        os.unlink(exe_path)

    build_path = os.path.join(tmp_dir, "nuitka-runner.build")

    if os.path.exists(build_path):
        shutil.rmtree(build_path)

    path = os.path.join("..", "..", "bin", "nuitka")

    _traceCompilation(path=path, pass_number=3)

    with withPythonPathChange(os.path.join("..", "..")):
        command = [
            os.environ["PYTHON"],
            nuitka_main_path,
            "--output-dir=%s" % tmp_dir,
            "--python-flag=-S",
            "--follow-imports",
            "--include-package=nuitka.plugins.standard",
            "--nofollow-import-to=*-postLoad",
            "--nofollow-import-to=SCons",
            "--nofollow-import-to=pip",
            "--report=compilation-report-pass3.xml",
            "--main=nuitka-runner.py",
            "--main=nuitka/tools/data_composer/DataComposer.py",
        ]

        my_print("Command: ", " ".join(command))
        result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    shutil.rmtree(build_path)

    test_logger.info("OK.")


def executePASS4():
    test_logger.info("PASS 4: Compiling the compiler running from single exe.")

    compilation_report = parseCompilationReport("compilation-report-pass3.xml")

    exe_path = getCompilationOutputBinary(
        compilation_report=compilation_report,
        prefixes=(("${cwd}", os.getcwd()),),
    )

    with withPythonPathChange(os.path.join("..", "..")):
        compileAndCompareWith(exe_path, pass_number=4)

    test_logger.info("OK.")


def executePASS5():
    my_print(
        "PASS 5: Compiling the compiler 'nuitka' package to single extension module."
    )

    path = os.path.join("..", "..", "nuitka")

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--output-dir=%s" % tmp_dir,
        "--include-plugin-dir=%s" % path,
        "--nofollow-import-to=nuitka.build.inline_copy",
        "--nofollow-import-to=nuitka.build.include",
        "--nofollow-import-to=nuitka.build.static_src",
        "--nofollow-import-to=nuitka.tools",
        "--mode=module",
        path,
    ]

    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    for preferred in (True, False):
        candidate = "nuitka" + getExtensionModuleSuffix(preferred=preferred)

        deleteFile(candidate, must_exist=False)

    os.unlink(os.path.join(tmp_dir, "nuitka.pyi"))
    shutil.rmtree(os.path.join(tmp_dir, "nuitka.build"))


def main():
    setup(needs_io_encoding=True)

    executePASS1()
    executePASS2()
    executePASS3()
    executePASS4()
    executePASS5()


if __name__ == "__main__":
    main()

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
