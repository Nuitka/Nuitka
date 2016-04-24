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
""" Profiling for Nuitka and CPython.

This provides the capability of comparing performance results of Nuitka and
CPython relatively to one another.
"""

from __future__ import print_function

import runpy
import sys
import tempfile

import vmprof  # @UnresolvedImport pylint: disable=F0401,I0021


def _namelen(e):
    if e.startswith("py:"):
        return len(e.split(':')[1])
    else:
        return len(e)

def show(stats):
    p = stats.top_profile()
    if not p:
        print("no stats")
        return

    p.sort(key = lambda x: x[1], reverse = True)
    top = p[0][1]

    max_len = max([_namelen(e[0]) for e in p])

    print(" vmprof output:")
    print(" %:      name:" + ' ' * (max_len - 3) + "location:")

    for k, v in p:
        v = "%.1f%%" % (float(v) / top * 100)
        if v == "0.0%":
            v = "<0.1%"
        if k.startswith("py:"):
            _, func_name, lineno, filename = k.split(':', 3)
            lineno = int(lineno)
            print(" %s %s %s:%d" % (v.ljust(7), func_name.ljust(max_len + 1), filename, lineno))
        else:
            print(" %s %s" % (v.ljust(7), k.ljust(max_len + 1)))


def main():
    with tempfile.NamedTemporaryFile() as prof_file:
        vmprof.enable(prof_file.fileno(), 0.001)

        try:
            program = sys.argv[1]
            del sys.argv[1]

#            sys.argv = [args.program] + args.args
            runpy.run_path(program, run_name = "__main__")
        except BaseException as e:
            if not isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
        vmprof.disable()

        stats = vmprof.read_profile(
            prof_file.name,
            virtual_only = True
        )

        show(stats)



main()
