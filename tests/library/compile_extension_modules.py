#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os, sys, tempfile, shutil

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )
)

from nuitka.tools.testing.Common import (
    setup,
    my_print,
    createSearchMode,
    compileLibraryTest,
    check_output,
    checkSucceedsWithCPython,
    getRuntimeTraceOfLoadedFiles,
    checkRuntimeLoadedFilesForOutsideAccesses
)

setup(needs_io_encoding = True)
search_mode = createSearchMode()

tmp_dir = tempfile.gettempdir()

# Try to avoid RAM disk /tmp and use the disk one instead.
if tmp_dir == "/tmp" and os.path.exists("/var/tmp"):
    tmp_dir = "/var/tmp"

blacklist = (
    "__phello__.foo.py", # Triggers error for "." in module name
    "idnadata"           # Avoid too complex code for main program.
)

done = set()

def decide(root, filename):
    if os.path.sep + "Cython" + os.path.sep in root:
        return False

    if root.endswith(os.path.sep + "matplotlib") or \
       os.path.sep + "matplotlib" + os.path.sep in root:
        return False

    if filename.endswith("linux-gnu_d.so"):
        return False

    if root.endswith(os.path.sep + "msgpack"):
        return False

    first_part = filename.split(".")[0]
    if first_part in done:
        return False
    done.add(first_part)

    return filename.endswith((".so", ".pyd")) and \
           not filename.startswith("libpython")


current_dir = os.path.normpath(os.getcwd())
current_dir = os.path.normcase(current_dir)

def action(stage_dir, root, path):
    command = [
        sys.executable,
        os.path.join(
            "..",
            "..",
            "bin",
            "nuitka"
        ),
        "--stand",
        "--run",
        "--output-dir",
        stage_dir,
        "--remove-output",
        "--plugin-enable=pylint-warnings"
    ]

    filename = os.path.join(stage_dir, "importer.py")

    assert path.startswith(root)

    module_name = path[len(root)+1:]
    module_name = module_name.split(".")[0]
    module_name = module_name.replace(os.path.sep, ".")

    with open(filename, "w") as output:
        output.write("import " + module_name + "\n")
        output.write("print('OK')")

    command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

    command.append(filename)

    if checkSucceedsWithCPython(filename):
        try:
            output = check_output(command).splitlines()
        except Exception:
            raise
        else:
            assert os.path.exists(filename[:-3] + ".dist")

            loaded_filenames = getRuntimeTraceOfLoadedFiles(
                path = os.path.join(
                    filename[:-3] + ".dist",
                     "importer.exe"
                )
            )

            outside_accesses = checkRuntimeLoadedFilesForOutsideAccesses(
                loaded_filenames,
                [
                    filename[:-3] + ".dist",
                    current_dir,
                    os.path.expanduser("~/.config")
                ]
            )

            if output[-1] != b"OK":
                sys.exit("FAIL")

            my_print("OK")

            assert not outside_accesses, outside_accesses

            shutil.rmtree(filename[:-3] + ".dist")
    else:
        my_print("SKIP (does not work with CPython)")


compileLibraryTest(
    search_mode = search_mode,
    stage_dir   = os.path.join(tmp_dir, "compile_extensions"),
    decide      = decide,
    action      = action
)

my_print("FINISHED, all extension modules compiled.")
