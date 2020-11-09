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
""" Hacks for scons that we apply.

We blacklist some tools from the standard scan, there is e.g. no need to ask
what fortran version we have installed to compile with Nuitka.

Also we hack the gcc version detection to fix some bugs in it, and to avoid
scanning for g++ when we have a gcc installer, but only if that is not too
version.

"""


import os
import re
import subprocess

import SCons.Tool.gcc  # pylint: disable=import-error
from SCons.Script import Environment  # pylint: disable=import-error

from nuitka.Tracing import my_print

from .SconsUtils import decodeData, isGccName

# Cache for detected versions.
v_cache = {}

# Prevent these programs from being found, avoiding the burden of tool init.
blacklisted_tools = (
    "f95",
    "f90",
    "f77",
    "gfortran",
    "ifort",
    "javah",
    "tar",
    "dmd",
    "gdc",
    "flex",
    "bison",
    "ranlib",
    "ar",
    "ldc2",
    "pdflatex",
    "pdftex",
    "latex",
    "tex",
    "dvipdf",
    "dvips",
    "gs",
    "swig",
    "ifl",
    "rpcgen",
    "rpmbuild",
    "bk",
    "p4",
    "m4",
    "ml",
    "icc",
    "sccs",
    "rcs",
    "cvs",
    "as",
    "gas",
    "nasm",
)


# From gcc.py of Scons
def myDetectVersion(env, cc):
    """Return the version of the GNU compiler, or None if it is not a GNU compiler."""
    cc = env.subst(cc)
    if not cc:
        return None
    if found_gcc and cc == "g++":
        return None

    version = None

    clvar = tuple(SCons.Util.CLVar(cc))

    if clvar in v_cache:
        return v_cache[clvar]

    clvar0 = os.path.basename(clvar[0])

    if isGccName(clvar0) or "clang" in clvar0:
        command = list(clvar) + ["-dumpversion"]
    else:
        command = list(clvar) + ["--version"]

    # pipe = SCons.Action._subproc(env, SCons.Util.CLVar(cc) + ['-dumpversion'],
    pipe = SCons.Action._subproc(  # pylint: disable=protected-access
        env, command, stdin="devnull", stderr="devnull", stdout=subprocess.PIPE
    )

    line = pipe.stdout.readline()
    # Non-GNU compiler's output (like AIX xlc's) may exceed the stdout buffer:
    # So continue with reading to let the child process actually terminate.
    while pipe.stdout.readline():
        pass

    ret = pipe.wait()
    if ret != 0:
        return None

    if str is not bytes and type(line) is bytes:
        line = decodeData(line)

    line = line.strip()

    match = re.findall(r"[0-9]+(?:\.[0-9]+)+", line)
    if match:
        version = match[0]
    else:
        # gcc 8 or higher
        version = line.strip()

    version = tuple(int(part) for part in version.split("."))

    if show_scons_mode:
        my_print("Scons: CC %r version check gives %r from %r" % (cc, version, line))

    v_cache[clvar] = version
    return version


found_gcc = False


def myDetect(self, progs):
    # cache these, pylint: disable=global-statement
    global found_gcc

    # Don't even search a C++ compiler if we found a suitable C11 compiler.
    if found_gcc and ("g++" in progs or "c++" in progs):
        return None

    # Don't consider Fortran, tar, D, we don't need it.
    for blacklisted_tool in blacklisted_tools:
        if blacklisted_tool in progs:
            return None

    # For RHEL and EPEL to work, smuggle these names in.
    if "g++" in progs and os.name != "nt":
        progs += ["g++44", "eg++"]

    result = orig_detect(self, progs)

    # Special considerations for gcc.
    if result in ("gcc", "cc"):
        if not found_gcc:
            gcc_version = myDetectVersion(self, result)

            # Ignore gcc before gcc version 5, no C11 support. We will find the
            # C++ compiler of it though.
            if gcc_version < (5,):
                gcc_version = None

                progs = [
                    "gcc-6.5",
                    "gcc-6.3",
                    "gcc-6.1",
                    "gcc-5.5",
                    "gcc-5.3",
                    "gcc-5.1",
                ]

                result = orig_detect(self, progs)

                if result is not None:
                    gcc_version = myDetectVersion(self, result)

            if result is not None:
                found_gcc = True

    return result


# The original value will be used in our form.
orig_detect = Environment.Detect

show_scons_mode = None


def getEnhancedToolDetect(show_scons_mode):  # pylint: disable=redefined-outer-name
    globals()["show_scons_mode"] = show_scons_mode

    SCons.Tool.gcc.detect_version = myDetectVersion

    return myDetect


def makeGccUseLinkerFile(source_dir, source_files, env):
    tmp_linker_filename = os.path.join(source_dir, "@link_input.txt")

    env["LINKCOM"] = env["LINKCOM"].replace(
        "$SOURCES", "@%s" % env.get("ESCAPE", lambda x: x)(tmp_linker_filename)
    )

    with open(tmp_linker_filename, "w") as tmpfile:
        for filename in source_files:
            filename = ".".join(filename.split(".")[:-1]) + ".o"

            if os.name == "nt":
                filename = filename.replace(os.path.sep, "/")

            tmpfile.write('"%s"\n' % filename)

        tmpfile.write(env.subst("$SOURCES"))
