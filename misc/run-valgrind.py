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

import commands
import os
import shutil
import subprocess
import sys
import tempfile

input_file = sys.argv[1]
nuitka_binary = os.environ.get(
    "NUITKA_BINARY",
    os.path.join(os.path.dirname(__file__), "../bin/nuitka")
)

basename = os.path.basename(input_file)

tempdir = tempfile.mkdtemp(
    prefix = basename + '-',
    dir    = None if not os.path.exists("/var/tmp") else "/var/tmp"
)

output_binary = os.path.join(
    tempdir,
    ( basename[:-3] if input_file.endswith(".py") else basename ) + ".exe"
)

os.environ[ "PYTHONHASHSEED" ] = '0'

# To make that python run well despite the "-S" flag for things that need site
# to expand sys.path.
os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)

os.system(
    "%s --exe --python-flag=-S --output-dir=%s %s %s %s" % (
        nuitka_binary,
        tempdir,
        "" if "number" in sys.argv else "--unstripped",
        os.environ.get("NUITKA_EXTRA_OPTIONS", ""),
        input_file
    )
)

if not os.path.exists(output_binary):
    sys.exit("Seeming failure of Nuitka to compile.")

log_base = basename[:-3] if input_file.endswith(".py") else basename
log_file = log_base + ".log"

sys.stdout.flush()

valgrind_options = "-q --tool=callgrind --callgrind-out-file=%s --zero-before=init__main__() --zero-before=init__main__" % log_file

subprocess.check_call(
    ["valgrind"] +
    valgrind_options.split() +
    [output_binary],
    stdout = open(os.devnull, 'w')
)

if "number" in sys.argv:
    for line in open(log_file):
        if line.startswith("summary:"):
            sizes = commands.getoutput("size '%s'" % output_binary).split('\n')[-1].replace('\t', "").split()

            print "SIZE=%d" % ( int(sizes[0]) + int(sizes[1]) )
            print "TICKS=%s" % line.split()[1]
            break
    else:
        assert False

    log_mem = log_base + ".mem"
    valgrind_options = "-q --tool=massif --massif-out-file=%s" % log_mem

    subprocess.check_call(
        ["valgrind"] +
        valgrind_options.split() +
        [output_binary],
        stdout = open(os.devnull, 'w')
    )

    max_mem = 0

    for line in open(log_mem):
        if line.startswith("mem_heap_B="):
            mem = int(line.split('=')[1])
            max_mem = max(mem, max_mem)

    print "MEM=%s" % max_mem

    shutil.rmtree(tempdir)
else:
    os.system("kcachegrind 2>/dev/null 1>/dev/null %s &" % log_file)
