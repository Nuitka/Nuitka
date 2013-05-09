#!/usr/bin/env python
#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
os.chdir( os.path.dirname( os.path.abspath( __file__ ) ) )

search_mode = len( sys.argv ) > 1 and sys.argv[1] == "search"

start_at = sys.argv[2] if len( sys.argv ) > 2 else None

if start_at:
    active = False
else:
    active = True

if "PYTHON" not in os.environ:
    os.environ[ "PYTHON" ] = sys.executable

if "PYTHONIOENCODING" not in os.environ:
    os.environ[ "PYTHONIOENCODING" ] = "utf-8"

def check_output(*popenargs, **kwargs):
    from subprocess import Popen, PIPE, CalledProcessError

    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = Popen(stdout=PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output=output)
    return output

version_output = check_output(
    [ os.environ[ "PYTHON" ], "--version" ],
    stderr = subprocess.STDOUT
)

python_version = version_output.split()[1]

os.environ[ "PYTHONPATH" ] = os.getcwd()

print( "Using concrete python", python_version )

for filename in sorted( os.listdir( "." ) ):
    if not filename.endswith( ".py" ) or filename.startswith( "run_" ):
        continue

    # Skip tests that require Python 2.7 at least.
    if filename.endswith( "27.py" ) and python_version.startswith( b"2.6" ):
        continue

    # Skip tests that require Python 3.2 at least.
    if filename.endswith( "32.py" ) and not python_version.startswith( b"3" ):
        continue

    # The overflow functions test gives syntax error on Python 3.x and can be ignored.
    if filename == "OverflowFunctions.py" and python_version.startswith( b"3" ):
        continue

    path = filename

    if not active and start_at in ( filename, path ):
        active = True

    extra_flags = [ "expect_success", "remove_output" ]

    if active:
        if filename in ( "Referencing.py", "Referencing32.py" ):
            debug_python = os.environ[ "PYTHON" ]
            if not debug_python.endswith( "-dbg" ):
                debug_python += "-dbg"

            if os.name == "nt" or "--windows-target" in os.environ.get( "NUITKA_EXTRA_OPTIONS", "" ):
                print( "Skip reference count test, CPython debug not on Windows." )
                continue

            if not os.path.exists( os.path.join( "/usr/bin", debug_python ) ):
                print( "Skip reference count test, CPython debug version not found." )
                continue

            extra_flags.append( "ignore_stderr" )
            extra_flags.append( "python_debug" )

        if filename == "OrderChecks.py":
            extra_flags.append( "ignore_stderr" )

        assert type( python_version ) is bytes

        if python_version.startswith( b"3.3" ) and filename in ( "ParameterErrors.py", "ParameterErrors32.py" ):
            print( "Skip parameter errors test", filename, "not yet compatible." )
            continue

        # Apply 2to3 conversion if necessary.
        if python_version.startswith( b"3" ) and not filename.endswith( "32.py" ):
            new_path = os.path.join( tempfile.gettempdir(), filename )
            shutil.copy( path, new_path )

            path = new_path

            # On Windows, we cannot rely on 2to3 to be in the path.
            if os.name == "nt":
               command = sys.executable + " " + os.path.join( os.path.dirname( sys.executable ), "Tools/Scripts/2to3.py" )
            else:
               command = "2to3"

            result = subprocess.call(
                command + " -w -n --no-diffs " + path,
                stderr = open( os.devnull, "w" ),
                shell  = True
            )

        command = "%s %s %s silent %s" % (
            sys.executable,
            os.path.join( "..", "..", "bin", "compare_with_cpython" ),
            path,
            " ".join( extra_flags )
        )

        result = subprocess.call(
            command,
            shell = True
        )

        if result == 2:
            sys.stderr.write( "Interruped, with CTRL-C\n" )
            sys.exit( 2 )

        if result != 0 and search_mode:
            print("Error exit!", result)
            sys.exit( result )

        if python_version.startswith( b"3" ) and not filename.endswith( "32.py" ):
            os.unlink( new_path )
    else:
        print("Skipping", filename)
