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
    if not os.path.isdir( filename ) or filename.endswith( ".build" ):
        continue

    path = os.path.relpath( filename )

    if not active and start_at in ( filename, path ):
        active = True

    if active:
        if filename not in ( "module_exits", "package_missing_init" ):
            extra_flags = [ "expect_success" ]
        else:
            extra_flags = [ "expect_failure" ]

        if filename == "package_missing_init":
            extra_flags.append( "ignore_stderr" )

        os.environ[ "PYTHONPATH" ] = os.path.abspath( filename )

        if filename == "syntax_errors":
            os.environ[ "NUITKA_EXTRA_OPTIONS" ] = "--recurse-all --execute-with-pythonpath"
        elif filename == "plugin_import":
            os.environ[ "NUITKA_EXTRA_OPTIONS" ] = "--recurse-all --recurse-directory=%s/some_package" % filename
        else:
            os.environ[ "NUITKA_EXTRA_OPTIONS" ] = "--recurse-all"

        print( "Consider output of recursively compiled program:", path )
        sys.stdout.flush()

        for filename_main in os.listdir( filename ):
            if filename_main.endswith( "Main.py" ):
                break
        else:
            assert False, filename

        result = subprocess.call(
            "%s %s %s silent %s" % (
                sys.executable,
                os.path.join( "..", "..", "bin", "compare_with_cpython" ),
                os.path.join( filename, filename_main ),
                " ".join( extra_flags )
            ),
            shell = True
        )

        if result == 2:
            sys.stderr.write( "Interruped, with CTRL-C\n" )
            sys.exit( 2 )

        if result != 0 and search_mode:
            print( "Error exit!", result )
            sys.exit( result )
    else:
        print( "Skipping", filename )
