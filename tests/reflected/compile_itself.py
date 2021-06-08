#!/usr/bin/env python
#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" Test Nuitka compiling itself and compiling itself in compiled form again.

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

import difflib
import shutil
import subprocess
import time

from nuitka.tools.testing.Common import getTempDir, my_print, setup
from nuitka.utils.Execution import wrapCommandForDebuggerForSubprocess
from nuitka.utils.FileOperations import copyTree, listDir, removeDirectory
from nuitka.utils.Importing import getSharedLibrarySuffix

nuitka_main_path = os.path.join("..", "..", "bin", "nuitka")

tmp_dir = getTempDir()

# Cannot detect this more automatic, so we need to list them, avoiding
# the ones not needed.
PACKAGE_LIST = (
    "nuitka",
    "nuitka/nodes",
    "nuitka/specs",
    "nuitka/nodes/shapes",
    "nuitka/tree",
    "nuitka/importing",
    "nuitka/build",
    "nuitka/freezer",
    "nuitka/codegen",
    "nuitka/codegen/templates",
    "nuitka/codegen/c_types",
    "nuitka/optimizations",
    "nuitka/finalizations",
    "nuitka/plugins",
    "nuitka/plugins/standard",
    "nuitka/plugins/commercial",
    "nuitka/constants",
    "nuitka/containers",
    "nuitka/utils",
)

exe_suffix = ".exe" if os.name == "nt" else ".bin"


def readSource(filename):
    if str is bytes:
        return open(filename, "rb").read()
    else:
        return open(filename, "rb").read().decode("latin1")


def diffRecursive(dir1, dir2):
    # Complex in nature, pylint: disable=too-many-branches

    done = set()

    result = False

    for path1, filename in listDir(dir1):
        if "cache-" in path1:
            continue

        path2 = os.path.join(dir2, filename)

        done.add(path1)

        # Skip these binary files and scons build database of course.
        # TODO: Temporary ignore ".bin", until we have something better than marshal which behaves
        # differently in compiled Nuitka:
        if filename.endswith(
            (
                ".o",
                ".os",
                ".obj",
                ".dblite",
                ".tmp",
                ".sconsign",
                ".txt",
                ".bin",
                ".const",
                ".exp",
            )
        ):
            continue

        if not os.path.exists(path2):
            my_print("Only in %s: %s" % (dir1, filename))
            result = False
            continue

        if os.path.isdir(path1):
            r = diffRecursive(path1, path2)
            if r:
                result = True
        elif os.path.isfile(path1):
            fromdate = time.ctime(os.stat(path1).st_mtime)
            todate = time.ctime(os.stat(path2).st_mtime)

            diff = difflib.unified_diff(
                a=readSource(path1).splitlines(),
                b=readSource(path2).splitlines(),
                fromfile=path1,
                tofile=path2,
                fromfiledate=fromdate,
                tofiledate=todate,
                n=3,
            )

            diff_list = list(diff)

            if diff_list:
                for line in diff_list:
                    try:
                        my_print(line)
                    except UnicodeEncodeError:
                        my_print(repr(line))

                result = True
        else:
            assert False, path1

    for path1, filename in listDir(dir2):
        if "cache-" in path1:
            continue

        path2 = os.path.join(dir2, filename)

        if path1 in done:
            continue

        if not os.path.exists(path1):
            my_print("Only in %s: %s" % (dir2, filename))
            result = False
            continue

    return result


def executePASS1():
    my_print("PASS 1: Compiling from compiler running from .py files.")

    base_dir = os.path.join("..", "..")

    for package in PACKAGE_LIST:
        package = package.replace("/", os.path.sep)

        source_dir = os.path.join(base_dir, package)
        target_dir = package

        removeDirectory(path=target_dir, ignore_errors=False)

        os.mkdir(target_dir)

        for path, filename in listDir(target_dir):
            if filename.endswith(".so"):
                os.unlink(path)

        for path, filename in listDir(source_dir):
            if not filename.endswith(".py"):
                continue

            if filename.startswith(".#"):
                continue

            if filename != "__init__.py":
                my_print("Compiling '%s'." % path)

                command = [
                    os.environ["PYTHON"],
                    nuitka_main_path,
                    "--module",
                    "--nofollow-imports",
                    "--plugin-enable=pylint-warnings",
                    "--output-dir=%s" % target_dir,
                    "--no-pyi-file",
                    path,
                ]
                command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

                result = subprocess.call(command)

                if result != 0:
                    sys.exit(result)
            else:
                shutil.copyfile(path, os.path.join(target_dir, filename))

    my_print("Compiling '%s'." % nuitka_main_path)

    shutil.copyfile(nuitka_main_path, "nuitka-runner.py")

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--nofollow-imports",
        "--plugin-enable=pylint-warnings",
        "--output-dir=.",
        "--python-flag=-S",
        "nuitka-runner.py",
    ]
    command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

    my_print("Command: ", " ".join(command))
    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    shutil.move("nuitka-runner" + exe_suffix, "nuitka" + exe_suffix)

    scons_inline_copy_path = os.path.join(base_dir, "nuitka", "build", "inline_copy")

    if os.path.exists(scons_inline_copy_path):
        copyTree(scons_inline_copy_path, os.path.join("nuitka", "build", "inline_copy"))

    shutil.copyfile(
        os.path.join(base_dir, "nuitka", "build", "Backend.scons"),
        os.path.join("nuitka", "build", "Backend.scons"),
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


def compileAndCompareWith(nuitka):
    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = "0"

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
                my_print("Compiling '%s'." % path)

                target = filename.replace(".py", ".build")

                target_dir = os.path.join(tmp_dir, target)

                removeDirectory(path=target_dir, ignore_errors=False)

                command = [
                    nuitka,
                    "--module",
                    "--plugin-enable=pylint-warnings",
                    "--output-dir=%s" % tmp_dir,
                    "--no-pyi-file",
                    path,
                ]
                command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

                my_print("Command: ", " ".join(command))
                exit_nuitka = subprocess.call(command)

                # In case of segfault or assertion triggered, run in debugger.
                if exit_nuitka in (-11, -6) and sys.platform != "nt":
                    command2 = wrapCommandForDebuggerForSubprocess(*command)
                    subprocess.call(command2)

                if exit_nuitka != 0:
                    my_print("An error exit %s occurred, aborting." % exit_nuitka)
                    sys.exit(exit_nuitka)

                has_diff = diffRecursive(os.path.join(package, target), target_dir)

                if has_diff:
                    sys.exit("There were differences!")

                shutil.rmtree(target_dir)

                target_filename = filename.replace(
                    ".py", getSharedLibrarySuffix(preferred=True)
                )

                os.unlink(os.path.join(tmp_dir, target_filename))


def executePASS2():
    my_print("PASS 2: Compiling from compiler running from .exe and many .so files.")

    # Windows will load the compiled modules (pyd) only from PYTHONPATH, so we
    # have to add it.
    if os.name == "nt":
        os.environ["PYTHONPATH"] = ":".join(PACKAGE_LIST)

    compileAndCompareWith(os.path.join(".", "nuitka" + exe_suffix))

    # Undo the damage from above.
    if os.name == "nt":
        del os.environ["PYTHONPATH"]

    my_print("OK.")


def executePASS3():
    my_print("PASS 3: Compiling from compiler running from .py files to single .exe.")

    exe_path = os.path.join(tmp_dir, "nuitka" + exe_suffix)

    if os.path.exists(exe_path):
        os.unlink(exe_path)

    build_path = os.path.join(tmp_dir, "nuitka.build")

    if os.path.exists(build_path):
        shutil.rmtree(build_path)

    path = os.path.join("..", "..", "bin", "nuitka")

    my_print("Compiling '%s'." % path)

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        path,
        "--output-dir=%s" % tmp_dir,
        "--python-flag=-S",
        "--follow-imports",
        #        "--include-package=nuitka.plugins",
    ]

    my_print("Command: ", " ".join(command))
    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    shutil.rmtree(build_path)

    my_print("OK.")


def executePASS4():
    my_print("PASS 4: Compiling the compiler running from single exe.")

    exe_path = os.path.join(tmp_dir, "nuitka" + exe_suffix)

    compileAndCompareWith(exe_path)

    my_print("OK.")


def executePASS5():
    my_print("PASS 5: Compiling the compiler 'nuitka' package to single '.so' file.")

    path = os.path.join("..", "..", "nuitka")

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--plugin-enable=pylint-warnings",
        "--output-dir=%s" % tmp_dir,
        "--include-plugin-dir=%s" % path,
        "--nofollow-import-to=nuitka.build.inline_copy",
        "--nofollow-import-to=nuitka.build.include",
        "--nofollow-import-to=nuitka.build.static_src",
        "--module",
        path,
    ]

    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    os.unlink(os.path.join(tmp_dir, "nuitka" + getSharedLibrarySuffix(preferred=True)))
    os.unlink(os.path.join(tmp_dir, "nuitka.pyi"))
    shutil.rmtree(os.path.join(tmp_dir, "nuitka.build"))


def main():
    setup(needs_io_encoding=True)

    executePASS1()
    executePASS2()
    executePASS3()
    executePASS4()

    shutil.rmtree("nuitka")

    executePASS5()


if __name__ == "__main__":
    main()
