#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import csv
import StringIO
import subprocess
import sys

print("Querying openSUSE build service status of Nuitka packages.")

osc_cmd = [
    "osc",
    "pr",
    "-c",
    "home:kayhayen"
]

process = subprocess.Popen(
    args   = osc_cmd,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE
)

stdout_osc, _stderr_osc = process.communicate()
exit_osc = process.returncode

assert exit_osc == 0, _stderr_osc

# print(stdout_osc)

csvfile = StringIO.StringIO(stdout_osc)
osc_reader = csv.reader(csvfile, delimiter = ';')

osc_reader = iter(osc_reader)

bad = ("failed", "unresolvable", "broken", "blocked", "disabled")

titles = osc_reader.next()[1:]
row1 = osc_reader.next()
row2 = osc_reader.next()

problems = []

for count, title in enumerate(titles):
    status = row1[count+1]

    # print(row1[0], title, ":", status)

    if status in bad:
        problems.append(
            (row1[0], title, status)
        )

for count, title in enumerate(titles):
    status = row2[count+1]

    # print(row2[0], title, ":", status)

    if status in bad:
        problems.append(
            (row2[0], title, status)
        )

if problems:
    print("There are problems with:")
    print('\n'.join("%s: %s (%s)" % problem for problem in problems))

    sys.exit(1)
else:
    print("Looks good.")
    sys.exit(0)
