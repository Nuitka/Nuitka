#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Scons interface.

Interaction with scons. Find the binary, and run it with a set of given
options.

"""

from nuitka import Options, Tracing, Utils

import os, sys

def getSconsDataPath():
    return Utils.dirname( __file__ )

def getSconsInlinePath():
    return Utils.joinpath( getSconsDataPath(), "inline_copy" )

def getSconsBinaryPath():
    if Utils.isFile( "/usr/bin/scons" ):
        return "/usr/bin/scons"
    else:
        return Utils.joinpath( getSconsInlinePath(), "bin", "scons.py" )

def runScons( options, quiet ):
    # For the scons file to find the static C++ files and include path. The
    # scons file is unable to use __file__ for the task.
    os.environ[ "NUITKA_SCONS" ] = getSconsDataPath()

    if os.name == "nt":
        # On Windows this Scons variable must be set by us.
        os.environ[ "SCONS_LIB_DIR" ] = Utils.joinpath(
            getSconsInlinePath(),
            "lib",
            "scons-2.0.1"
        )

        # Also, for MinGW we can avoid the user having to add the path if he
        # used the default path or installed it on the same drive by appending
        # to the PATH variable before executing scons.
        os.environ[ "PATH" ] += r";\MinGW\bin;C:\MinGW\bin"

    # Scons is Python2 only, so we need to make the system find a suitable
    # Python binary.
    if Utils.python_version < 300:
        python_exe = sys.executable
    elif os.name == "nt":
        if os.path.exists( r"c:\Python27\python.exe" ):
            python_exe = r"c:\Python27\python.exe"
        elif os.path.exists( r"c:\Python26\python.exe" ):
            python_exe = r"c:\Python26\python.exe"
        else:
            sys.exit( """\
Error, need to find Python2 executable under C:\\Python26 or \
C:\\Python27 to execute scons which is not Python3 compatible.""" )
    else:
        python_exe = "python"

    scons_command = """%(python)s %(binary)s %(quiet)s --warn=no-deprecated \
-f %(scons_file)s --jobs %(job_limit)d %(options)s""" % {
        "python"     : python_exe,
        "binary"     : getSconsBinaryPath(),
        "quiet"      : "--quiet" if quiet else "",
        "scons_file" : Utils.joinpath( getSconsDataPath(), "SingleExe.scons" ),
        "job_limit"  : Options.getJobLimit(),
        "options"    : " ".join(
            "%s=%s" % ( key, value )
            for key, value in
            options.items()
        )
    }

    if Options.isShowScons():
        Tracing.printLine( "Scons command:", scons_command )

    return 0 == os.system( scons_command )
