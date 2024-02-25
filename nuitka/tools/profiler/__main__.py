#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Profiling for Nuitka and CPython.

This provides the capability of comparing performance results of Nuitka and
CPython relatively to one another.
"""

# Note: This is currently severely broken.

import runpy
import sys
import tempfile

from nuitka.Tracing import my_print


def _namelen(e):
    if e.startswith("py:"):
        return len(e.split(":")[1])
    else:
        return len(e)


def show(stats):
    p = stats.top_profile()
    if not p:
        my_print("no stats")
        return

    p.sort(key=lambda x: x[1], reverse=True)
    top = p[0][1]

    max_len = max(_namelen(e[0]) for e in p)

    my_print(" vmprof output:")
    my_print(" %:      name:" + " " * (max_len - 3) + "location:")

    for k, v in p:
        v = "%.1f%%" % (float(v) / top * 100)
        if v == "0.0%":
            v = "<0.1%"
        if k.startswith("py:"):
            _, func_name, lineno, filename = k.split(":", 3)
            lineno = int(lineno)
            my_print(
                " %s %s %s:%d"
                % (v.ljust(7), func_name.ljust(max_len + 1), filename, lineno)
            )
        else:
            my_print(" %s %s" % (v.ljust(7), k.ljust(max_len + 1)))


def main():
    import vmprof  # pylint: disable=I0021,import-error

    with tempfile.NamedTemporaryFile() as prof_file:
        vmprof.enable(prof_file.fileno(), 0.001)

        try:
            program = sys.argv[1]
            del sys.argv[1]

            #            sys.argv = [args.program] + args.args
            runpy.run_path(program, run_name="__main__")
        except (KeyboardInterrupt, SystemExit):
            pass

        vmprof.disable()

        stats = vmprof.read_profile(prof_file.name)

        show(stats)


if __name__ == "__main__":
    main()

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
