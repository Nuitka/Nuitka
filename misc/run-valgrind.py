#!/usr/bin/env python
#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Run code with Nuitka compiled and put that through valgrind.

"""

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
)

# isort:start

import shutil
import tempfile

from nuitka.tools.testing.Valgrind import getBinarySizes, runValgrind

input_file = sys.argv[1]

nuitka_binary = os.environ.get(
    "NUITKA_BINARY", os.path.join(os.path.dirname(__file__), "../bin/nuitka")
)
nuitka_binary = os.path.normpath(nuitka_binary)

basename = os.path.basename(input_file)

tempdir = tempfile.mkdtemp(
    prefix=basename + "-", dir=None if not os.path.exists("/var/tmp") else "/var/tmp"
)

output_binary = os.path.join(
    tempdir, (basename[:-3] if input_file.endswith(".py") else basename) + ".bin"
)

os.environ["PYTHONHASHSEED"] = "0"

# To make that python run well despite the "-S" flag for things that need site
# to expand sys.path.
os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)

os.system(
    "%s %s --python-flag=-S --no-progress --output-dir=%s %s %s %s %s"
    % (
        sys.executable,
        nuitka_binary,
        tempdir,
        "--unstripped",
        "--quiet",
        os.environ.get("NUITKA_EXTRA_OPTIONS", ""),
        input_file,
    )
)

if not os.path.exists(output_binary):
    sys.exit("Seeming failure of Nuitka to compile, no %r." % output_binary)

log_base = basename[:-3] if input_file.endswith(".py") else basename

if "number" in sys.argv or "numbers" in sys.argv:
    log_file = log_base + ".log"
else:
    log_file = None

log_file = log_base + ".log"

sys.stdout.flush()


ticks = runValgrind(
    None, "callgrind", [output_binary], include_startup=False, save_logfilename=log_file
)

if "number" in sys.argv or "numbers" in sys.argv:
    sizes = getBinarySizes(output_binary)

    print("SIZE=%d" % (sizes[0] + sizes[1]))
    print("TICKS=%s" % ticks)
    print("BINARY=%s" % nuitka_binary)

    max_mem = runValgrind(None, "massif", [output_binary], include_startup=True)

    print("MEM=%s" % max_mem)

    shutil.rmtree(tempdir)
else:
    os.system("kcachegrind 2>/dev/null 1>/dev/null %s &" % log_file)
