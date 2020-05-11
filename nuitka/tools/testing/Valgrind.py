#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Valgrind tool usage.

We are using it for benchmarking purposes, as it's an analysis tool at the
same time and gives deterministic results.
"""

import shutil
import subprocess
import sys

from nuitka.Tracing import my_print
from nuitka.utils.Execution import check_output
from nuitka.utils.FileOperations import getFileContentByLine, withTemporaryFile


def runValgrind(descr, tool, args, include_startup, save_logfilename=None):
    if descr:
        my_print(descr, tool, file=sys.stderr, end="... ")

    with withTemporaryFile() as log_file:
        log_filename = log_file.name

        command = ["valgrind", "-q"]

        if tool == "callgrind":
            command += ("--tool=callgrind", "--callgrind-out-file=%s" % log_filename)
        elif tool == "massif":
            command += ("--tool=massif", "--massif-out-file=%s" % log_filename)
        else:
            sys.exit("Error, no support for tool '%s' yet." % tool)

        # Do not count things before main module starts its work.
        if not include_startup:
            command += (
                "--zero-before=init__main__()",
                "--zero-before=init__main__",
                "--zero-before=PyInit___main__",
                "--zero-before=PyInit___main__()",
            )

        command.extend(args)

        process = subprocess.Popen(
            args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        _stdout_valgrind, stderr_valgrind = process.communicate()
        exit_valgrind = process.returncode

        assert exit_valgrind == 0, stderr_valgrind
        if descr:
            my_print("OK", file=sys.stderr)

        if save_logfilename is not None:
            shutil.copyfile(log_filename, save_logfilename)

        max_mem = None

        for line in getFileContentByLine(log_filename):
            if tool == "callgrind" and line.startswith("summary:"):
                return int(line.split()[1])
            elif tool == "massif" and line.startswith("mem_heap_B="):
                mem = int(line.split("=")[1])

                if max_mem is None:
                    max_mem = 0

                max_mem = max(mem, max_mem)

        if tool == "massif" and max_mem is not None:
            return max_mem

        sys.exit("Error, didn't parse Valgrind log file successfully.")


def getBinarySizes(filename):
    command = ["size", filename]
    sizes = check_output(command).strip()
    sizes = sizes.split(b"\n")[-1].replace(b"\t", b"").split()

    return int(sizes[0]), int(sizes[1])
