#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" This test runner compiles all extension modules for standalone mode.

This is a test to reveal hidden dependencies on a system.

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

from nuitka.freezer.RuntimeTracing import getRuntimeTraceOfLoadedFiles
from nuitka.tools.testing.Common import (
    check_output,
    checkLoadedFileAccesses,
    checkSucceedsWithCPython,
    compileLibraryTest,
    createSearchMode,
    displayFileContents,
    displayFolderContents,
    displayRuntimeTraces,
    getTempDir,
    my_print,
    setup,
    test_logger,
)
from nuitka.utils.Execution import NuitkaCalledProcessError
from nuitka.utils.FileOperations import getFileContents, openTextFile
from nuitka.utils.ModuleNames import ModuleName


def displayError(dirname, filename):
    assert dirname is None

    dist_path = filename[:-3] + ".dist"
    displayFolderContents("dist folder", dist_path)

    inclusion_log_path = filename[:-3] + ".py.inclusion.log"
    displayFileContents("inclusion log", inclusion_log_path)


def main():
    setup(suite="extension_modules", needs_io_encoding=True)
    search_mode = createSearchMode()

    tmp_dir = getTempDir()

    done = set()

    def decide(root, filename):
        if os.path.sep + "Cython" + os.path.sep in root:
            return False

        if (
            root.endswith(os.path.sep + "matplotlib")
            or os.path.sep + "matplotlib" + os.path.sep in root
        ):
            return False

        if filename.endswith("linux-gnu_d.so"):
            return False

        if root.endswith(os.path.sep + "msgpack"):
            return False

        first_part = filename.split(".")[0]
        if first_part in done:
            return False
        done.add(first_part)

        return filename.endswith((".so", ".pyd")) and not filename.startswith(
            "libpython"
        )

    current_dir = os.path.normpath(os.getcwd())
    current_dir = os.path.normcase(current_dir)

    def action(stage_dir, root, path):
        command = [
            sys.executable,
            os.path.join("..", "..", "bin", "nuitka"),
            "--stand",
            "--run",
            "--output-dir=%s" % stage_dir,
            "--remove-output",
        ]

        filename = os.path.join(stage_dir, "importer.py")

        assert path.startswith(root)

        module_name = path[len(root) + 1 :]
        module_name = module_name.split(".")[0]
        module_name = module_name.replace(os.path.sep, ".")

        module_name = ModuleName(module_name)

        with openTextFile(filename, "w") as output:
            plugin_names = set(["pylint-warnings"])
            if module_name.hasNamespace("PySide2"):
                plugin_names.add("pyside2")
            elif module_name.hasNamespace("PySide6"):
                plugin_names.add("pyside2")
            elif module_name.hasNamespace("PyQt5"):
                plugin_names.add("pyqt5")
            else:
                # TODO: We do not have a noqt plugin yet.
                plugin_names.add("pyqt5")

            for plugin_name in plugin_names:
                output.write("# nuitka-project: --enable-plugin=%s\n" % plugin_name)

            # Make it an error to find unwanted bloat compiled in.
            output.write("# nuitka-project: --noinclude-default-mode=error\n")

            output.write("# nuitka-project: --standalone\n")

            output.write("import " + module_name.asString() + "\n")
            output.write("print('OK.')")

        command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

        command.append(filename)

        if checkSucceedsWithCPython(filename):
            try:
                output = check_output(command).splitlines()
            except NuitkaCalledProcessError as e:
                my_print("SCRIPT:", filename, style="blue")
                my_print(getFileContents(filename))

                test_logger.sysexit("Error with compilation: %s" % e)
            except Exception:  # only trying to check for no exception, pylint: disable=try-except-raise
                raise
            else:
                assert os.path.exists(filename[:-3] + ".dist")

                binary_filename = os.path.join(
                    filename[:-3] + ".dist",
                    "importer.exe" if os.name == "nt" else "importer",
                )
                loaded_filenames = getRuntimeTraceOfLoadedFiles(
                    logger=test_logger,
                    command=[binary_filename],
                )

                outside_accesses = checkLoadedFileAccesses(
                    loaded_filenames=loaded_filenames, current_dir=os.getcwd()
                )

                if outside_accesses:
                    displayError(None, filename)
                    displayRuntimeTraces(test_logger, binary_filename)

                    test_logger.warning(
                        "Should not access these file(s): '%r'." % outside_accesses
                    )

                    search_mode.onErrorDetected(1)

                if output[-1] != b"OK.":
                    my_print(" ".join(command))
                    my_print(filename)
                    my_print(output)
                    test_logger.sysexit("FAIL.")

                my_print("OK.")

                assert not outside_accesses, outside_accesses

                shutil.rmtree(filename[:-3] + ".dist")
        else:
            my_print("SKIP (does not work with CPython)")

    compileLibraryTest(
        search_mode=search_mode,
        stage_dir=os.path.join(tmp_dir, "compile_extensions"),
        decide=decide,
        action=action,
    )

    my_print("FINISHED, all extension modules compiled.")


if __name__ == "__main__":
    main()
