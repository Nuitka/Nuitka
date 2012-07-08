#!/usr/bin/env python
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
    os.environ[ "PYTHON" ] = "python"

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

    # The overflow functions test gives syntax error on Python 3.x and can be ignored.
    if filename == "OverflowFunctions.py" and python_version.startswith( b"3" ):
        continue

    path = filename

    if not active and start_at in ( filename, path ):
        active = True


    extra_flags = [ "expect_success" ]

    if filename == "Referencing.py":
        if not os.path.exists( "/usr/bin/" + os.environ[ "PYTHON" ] + "-dbg" ):
            print( "Skip reference count test, CPython debug version not found." )
            continue

        extra_flags.append( "ignore_stderr" )
        extra_flags.append( "python_debug" )

    if active:
        # Temporary measure, until Python3 is better supported, disable some tests, so
        # this can be used to monitor the success of existing ones and have no regression for it.
        if os.environ[ "PYTHON" ] == "python3.2" and filename[:-3] in ( "ExecEval", "Unicode", ):
            print( "Skipping malfunctional test", filename )
            continue

        # Apply 2to3 conversion if necessary.
        assert type( python_version ) is bytes

        if python_version.startswith( b"3" ):
            new_path = os.path.join( tempfile.gettempdir(), filename )
            shutil.copy( path, new_path )

            path = new_path

            # No idea how to make this portable to Windows, but we can delay it until
            # Python3 is fully functional under Linux first.
            result = subprocess.call(
                "2to3 -w -n --no-diffs " + path,
                stderr = open( "/dev/null", "w" ),
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

        if python_version.startswith( b"3" ):
            os.unlink( new_path )
    else:
        print("Skipping", filename)
