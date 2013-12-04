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

from __future__ import print_function

import os, sys, subprocess, tempfile, atexit, shutil, re

# Make sure we flush after every print, the "-u" option does more than that
# and this is easy enough.
def my_print( *args, **kwargs ):
    print( *args, **kwargs )
    sys.stdout.flush()

def check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')

    process = subprocess.Popen( stdout = subprocess.PIPE, *popenargs, **kwargs )
    output, _unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError( retcode, cmd, output=output )
    return output

def setup( needs_io_encoding = False ):
    # Go its own directory, to have it easy with path knowledge.
    os.chdir(
        os.path.dirname(
            os.path.abspath( sys.modules[ "__main__" ].__file__ )
        )
    )

    if "PYTHON" not in os.environ:
        os.environ[ "PYTHON" ] = sys.executable

    if needs_io_encoding and "PYTHONIOENCODING" not in os.environ:
        os.environ[ "PYTHONIOENCODING" ] = "utf-8"

    version_output = check_output(
        [ os.environ[ "PYTHON" ], "--version" ],
        stderr = subprocess.STDOUT
    )

    global python_version
    python_version = version_output.split()[1]

    my_print( "Using concrete python", python_version )

    assert type( python_version ) is bytes

    return python_version

tmp_dir = None

def getTempDir():
    # Create a temporary directory to work in, automatically remove it in case
    # it is empty in the end.
    global tmp_dir

    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp(
            prefix = os.path.basename(
                os.path.dirname(
                    os.path.abspath( sys.modules[ "__main__" ].__file__ )
                )
            ) + "-",
            dir    = tempfile.gettempdir() if
                         not os.path.exists( "/var/tmp" ) else
                    "/var/tmp"
        )

        def removeTempDir():
            try:
                os.rmdir( tmp_dir )
            except OSError:
                pass

        atexit.register( removeTempDir )

    return tmp_dir

def convertUsing2to3( path ):
    filename = os.path.basename( path )

    new_path = os.path.join( getTempDir(), filename )
    shutil.copy( path, new_path )

    # On Windows, we cannot rely on 2to3 to be in the path.
    if os.name == "nt":
        command = [
            sys.executable,
            os.path.join(
                os.path.dirname( sys.executable ),
                "Tools/Scripts/2to3.py"
            )
        ]
    else:
        command = [ "2to3" ]

    command += [
        "-w",
        "-n",
        "--no-diffs",
        new_path
    ]

    check_output(
        command,
        stderr = open( os.devnull, "w" ),
    )

    return new_path

def decideFilenameVersionSkip( filename ):
    if filename.startswith( "run_" ):
        return False

    # Skip tests that require Python 2.7 at least.
    if filename.endswith( "27.py" ) and python_version.startswith( b"2.6" ):
        return False

    # Skip tests that require Python 3.2 at least.
    if filename.endswith( "32.py" ) and not python_version.startswith( b"3" ):
        return False

    # Skip tests that require Python 3.3 at least.
    if filename.endswith( "33.py" ) and not python_version.startswith( b"3.3" ):
        return False

    return True

def compareWithCPython( path, extra_flags, search_mode, needs_2to3 ):
    # Apply 2to3 conversion if necessary.
    if needs_2to3:
        path = convertUsing2to3( path )

    command = [
        sys.executable,
        os.path.join( "..", "..", "bin", "compare_with_cpython" ),
        path,
        "silent"
    ]
    command += extra_flags

    try:
        result = subprocess.call(
            command
        )
    except KeyboardInterrupt:
        result = 2

    if result != 0 and result != 2 and search_mode:
        my_print("Error exit!", result)
        sys.exit( result )

    if needs_2to3:
        os.unlink( path )

    if result == 2:
        sys.stderr.write( "Interruped, with CTRL-C\n" )
        sys.exit( 2 )

def hasDebugPython():
    global python_version

    # On Debian systems, these work.
    debug_python = os.path.join( "/usr/bin/", os.environ[ "PYTHON" ] + "-dbg" )
    if os.path.exists( debug_python ):
        return True

    # For self compiled Python, if it's the one also executing the runner, lets
    # use it.
    if sys.executable == os.environ[ "PYTHON" ] and \
       hasattr( sys, "gettotalrefcount" ):
        return True

    # Otherwise no.
    return False

def getRuntimeTraceOfLoadedFiles( path ):
    """ Returns the files loaded when executing a binary. """

    if os.name == "posix":
        args = (
            "strace",
            "-e", "file",
            "-s4096", # Some paths are truncated otherwise.
            path
        )

        process = subprocess.Popen(
            args   = args,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        stdout_strace, stderr_strace = process.communicate()

        result = []

        for line in stderr_strace.split("\n"):
            if not line:
                continue

            result.extend(
                os.path.abspath(match)
                for match in
                re.findall('"(.*?)"', line)
            )

    result = list(sorted(set(result)))

    return result
