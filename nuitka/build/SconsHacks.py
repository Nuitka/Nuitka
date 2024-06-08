#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Hacks for scons that we apply.

We block some tools from the standard scan, there is e.g. no need to ask
what fortran version we have installed to compile with Nuitka.

Also we hack the gcc version detection to fix some bugs in it, and to avoid
scanning for g++ when we have a gcc installer, but only if that is not too
version.

"""

import os
import re

import SCons.Tool.gcc  # pylint: disable=I0021,import-error
from SCons.Script import Environment  # pylint: disable=I0021,import-error

from nuitka.Tracing import scons_details_logger
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import openTextFile
from nuitka.utils.Utils import isLinux, isMacOS

from .SconsUtils import decodeData, getExecutablePath, isGccName

# Cache for detected versions.
v_cache = {}

# Prevent these programs from being found, avoiding the burden of tool init.
_blocked_tools = (
    # TODO: Where the fallback is needed, g++ needs to scanned or else it
    # cannot be used.
    #    "g++",
    "c++",
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


def _myDetectVersion(cc):
    if isGccName(cc) or "clang" in cc:
        command = (
            cc,
            "-dumpversion",
            "-dumpfullversion",
        )
    else:
        command = (
            cc,
            "--version",
        )

    stdout, stderr, exit_code = executeProcess(command)

    if exit_code != 0:
        scons_details_logger.info(
            "Error, error exit from '%s' (%d) gave %r." % (command, exit_code, stderr)
        )
        return None

    line = stdout.splitlines()[0]

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

    return version


def myDetectVersion(env, cc):
    """Return the version of the GNU compiler, or None if it is not a GNU compiler."""
    cc = env.subst(cc)
    if not cc:
        return None
    if "++" in os.path.basename(cc):
        return None

    # Make path absolute, to improve cache hit rate.
    cc = getExecutablePath(cc, env)
    if cc is None:
        return None

    if cc not in v_cache:
        v_cache[cc] = _myDetectVersion(cc)

        scons_details_logger.info("CC '%s' version check gives %r" % (cc, v_cache[cc]))

    return v_cache[cc]


def myDetect(self, progs):
    # Don't consider Fortran, tar, D, c++, we don't need it. We do manual
    # fallback
    for blocked_tool in _blocked_tools:
        if blocked_tool in progs:
            return None

    # Note: Actually, with our inline copy, this is maybe not supposed to
    # happen a lot at all. It's a bit hard to pass debug flag to here, or
    # else we could assert it.
    # for p in progs:
    #     if p not in ("x86_64-conda-linux-gnu-gcc", "gcc", "cc", "g++"):
    #         assert False, p

    return orig_detect(self, progs)


# The original value will be used in our form.
orig_detect = Environment.Detect


def getEnhancedToolDetect():
    SCons.Tool.gcc.detect_version = myDetectVersion

    # Allow CondaCC to be detected if it is in PATH.
    if isLinux():
        SCons.Tool.gcc.compilers.insert(0, "x86_64-conda-linux-gnu-gcc")

    if isMacOS() and "CONDA_TOOLCHAIN_BUILD" in os.environ:
        SCons.Tool.gcc.compilers.insert(
            0, "%s-clang" % os.environ["CONDA_TOOLCHAIN_BUILD"]
        )

    return myDetect


def makeGccUseLinkerFile(source_files, module_mode, env):
    tmp_linker_filename = os.path.join(env.source_dir, "@link_input.txt")

    # Note: For Windows, it's done in mingw.py because of its use of
    # a class rather than a string here, that is not working for the
    # monkey patching.
    if type(env["SHLINKCOM"]) is str:
        env["SHLINKCOM"] = env["SHLINKCOM"].replace(
            "$SOURCES", "@%s" % env.get("ESCAPE", lambda x: x)(tmp_linker_filename)
        )

    env["LINKCOM"] = env["LINKCOM"].replace(
        "$SOURCES", "@%s" % env.get("ESCAPE", lambda x: x)(tmp_linker_filename)
    )

    with openTextFile(tmp_linker_filename, "w") as tmpfile:
        for filename in source_files:
            filename = ".".join(filename.split(".")[:-1]) + (
                ".os" if module_mode and os.name != "nt" else ".o"
            )

            if os.name == "nt":
                filename = filename.replace(os.path.sep, "/")

            tmpfile.write('"%s"\n' % filename)

        tmpfile.write(env.subst("$SOURCES"))


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
