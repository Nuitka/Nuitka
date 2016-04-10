#!/usr/bin/python
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

import os
import re
import subprocess
import sys
import tempfile

_handle, tempfile1 = tempfile.mkstemp()

temp_out = open(tempfile1, "wb")

for line in subprocess.check_output(["sfood", "nuitka"]).split('\n'):
    if line:
        values = list(eval(line))

        if values[0][1] in ("nuitka/oset.py", "nuitka/odict.py"):
            continue

        if values[1][1] in ("nuitka/oset.py", "nuitka/odict.py", "os.py", "re.py", "math", "signal", "sys"):
            continue

        if os.path.isdir(values[0][1]):
            continue

        print >>temp_out, line

temp_out.close()

dot_graph = subprocess.check_output(["sfood-graph"], stdin = open(tempfile1))
os.unlink(tempfile1)

temp_out = open(tempfile1, "wb")
temp_out.write(dot_graph)
temp_out.close()

dot_graph = subprocess.call(["dot", "-Tsvg"], stdin = open(tempfile1), stdout = open("nuitka-dependencies.svg", "wb"))

os.unlink(tempfile1)

subprocess.check_call(["inkscape", "nuitka-dependencies.svg"])
