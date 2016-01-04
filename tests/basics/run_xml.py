#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import os, sys, subprocess, tempfile, shutil

# Go its own directory, to have it easy with path knowledge.
nuitka1 = sys.argv[1]
nuitka2 = sys.argv[2]

search_mode = len(sys.argv) > 3 and sys.argv[3] == "search"
start_at = sys.argv[4] if len(sys.argv) > 4 else None

if start_at:
    active = False
else:
    active = True

def check_output(*popenargs, **kwargs):
    from subprocess import Popen, PIPE, CalledProcessError

    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")
    process = Popen(stdout = PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output = output)
    return output

my_dir = os.path.dirname(os.path.abspath(__file__))

for filename in sorted(os.listdir(my_dir)):
    if not filename.endswith(".py") or filename.startswith("run_"):
        continue

    path = os.path.relpath(os.path.join(my_dir, filename))

    if not active and start_at in (filename, path):
        active = True

    if active:
        # TODO: Reactivate Python3 support here.
        if False:
            new_path = os.path.join(tempfile.gettempdir(), filename)
            shutil.copy(path, new_path)

            path = new_path

            # On Windows, we cannot rely on 2to3 to be in the path.
            if os.name == "nt":
                command = sys.executable + ' ' + os.path.join(os.path.dirname(sys.executable), "Tools/Scripts/2to3.py")
            else:
                command = "2to3"

            result = subprocess.call(
                command + " -w -n --no-diffs " + path,
                stderr = open(os.devnull, 'w'),
                shell  = True
            )

        command = "%s %s '%s' '%s' %s" % (
            sys.executable,
            os.path.join(my_dir, "..", "..", "bin", "compare_with_xml"),
            nuitka1,
            nuitka2,
            path,
        )

        result = subprocess.call(
            command,
            shell = True
        )

        if result == 2:
            sys.stderr.write("Interrupted, with CTRL-C\n")
            sys.exit(2)

        if result != 0 and search_mode:
            print("Error exit!", result)
            sys.exit(result)
    else:
        print("Skipping", filename)
