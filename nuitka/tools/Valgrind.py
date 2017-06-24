#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

import subprocess
import sys

from nuitka.Tracing import my_print
from nuitka.utils.FileOperations import withTemporaryFilename


def runValgrind(descr, args):
    if descr:
        my_print(descr, file = sys.stderr, end = "... ")

    with withTemporaryFilename() as log_file:
        valgrind_options = "-q --tool=callgrind --callgrind-out-file=%s" % log_file

        command = ["valgrind"] + valgrind_options.split() + list(args)

        process = subprocess.Popen(
            args   = command,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        _stdout_valgrind, stderr_valgrind = process.communicate()
        exit_valgrind = process.returncode

        assert exit_valgrind == 0, stderr_valgrind
        my_print("OK", file = sys.stderr)
        for line in open(log_file):
            if line.startswith("summary:"):
                return int(line.split()[1])

        sys.exit("Error, didn't parse Valgrind log file successfully.")
