#!/usr/bin/python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

        user_parts = values[0][1].split(os.path.sep)
        used_parts = (values[1][1] or "").split(os.path.sep)

        ignore_it = False
        for ignored in "containers", "tools", "utils":
            if ignored in user_parts:
                ignore_it = True
                break
            if ignored in used_parts:
                ignore_it = True
                break

        if ignore_it:
            continue

        if values[1][1] in ("os.py", "re.py", "math", "signal", "sys",
                            "logging", "timeit.py", "tempfile.py", "glob.py",
                            "appdirs.py", "ast.py", "tokenize.py", "runpy.py",
                            "imp", "multiprocessing", "threading.py",
                            "shutil.py", "contextlib.py", "exceptions",
                            "functools.py", "types.py", "subprocess.py",
                            "optparse.py", "operator", "ctypes/wintypes.py",
                            "sysconfig.py", "xml/etree/ElementTree.py",
                            "lxml/etree.so", "warnings.py", "StringIO.py",
                            "cStringIO", "urllib.py", "ctypes", "marshal",
                            "struct.py", "abc.py", "hashlib.py", "copy.py",
                            "collections.py", "itertools", "zipfile.py",
                            "distutils/command/build.py", "filecmp.py",
                            "distutils/command/install.py", "fnmatch.py",
                            "wheel/bdist_wheel.py", "traceback.py", "inspect.py",
                            "PyQt5/QtCore.x86_64-linux-gnu.so", "difflib.py",
                            "PyQt5/QtGui.x86_64-linux-gnu.so", "PyQt5/uic",
                            "_ctypes.x86_64-linux-gnu.so", "baron/parser.py",
                            "linecache.py",
                            ):
            continue

        if os.path.isdir(values[0][1]):
            continue

        assert "python2.7" not in (values[1][0] or "").split(os.path.sep), (line, user_parts)


        print >>temp_out, line
        print(line)

temp_out.close()

dot_graph = subprocess.check_output(["sfood-graph"], stdin = open(tempfile1))
os.unlink(tempfile1)

temp_out = open(tempfile1, "wb")
temp_out.write(dot_graph)
temp_out.close()

dot_graph = subprocess.call(["dot", "-Tsvg"], stdin = open(tempfile1), stdout = open("nuitka-dependencies.svg", "wb"))

os.unlink(tempfile1)

subprocess.check_call(["inkscape", "nuitka-dependencies.svg"])
