#!/usr/bin/env python
#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Softwar where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

from __future__ import print_function


import os, sys, subprocess, tempfile, shutil

try:
    import lxml.etree
except ImportError:
    sys.exit( "Error, no 'lxml' module installed, cannot run XML based tests." )

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

def checkSequence( statements ):
    for statement in module_statements:
        kind = getKind( statement )

        if kind == "Print":
            print_args = getRole( statement, "values" )

            if len( print_args ) != 1:
                sys.exit( "Error, print with more than one argument." )

            print_arg = print_args[0]

            if getKind( print_arg ) != "ConstantRef":
                sys.exit( "Error, print of non-constant %s." % getKind( print_arg ) )
        else:
            sys.exit( "Error, non-print statement of unknown kind '%s'." % kind )


for filename in sorted( os.listdir( "." ) ):
    if not filename.endswith( ".py" ) or filename.startswith( "run_" ):
        continue

    # Skip tests that require Python 2.7 at least.
    if filename.endswith( "27.py" ) and python_version.startswith( b"2.6" ):
        continue

    path = filename

    if not active and start_at in ( filename, path ):
        active = True


    extra_flags = [ "expect_success" ]

    if active:
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


        print( "Consider", path, end = " " )

        command = "%s %s --dump-xml %s" % (
            os.environ[ "PYTHON" ],
            os.path.join( "..", "..", "bin", "nuitka" ),
            path
        )

        result = subprocess.check_output(
            command,
            shell = True
        )

        root = lxml.etree.fromstring( result )
        module_body  = root[0]
        module_statements_sequence = module_body[ 0 ]

        assert len( module_statements_sequence ) == 1
        module_statements = iter( module_statements_sequence ).next()

        def getKind( node ):
            result = node.attrib[ "kind" ]

            result = result.replace( "Statements", "" )
            result = result.replace( "Statement", "" )
            result = result.replace( "Expression", "" )

            return result

        def getRole( node, role ):
            for child in node:
                if child.tag == "role" and child.attrib[ "name" ] == role:
                    return child
            else:
                return None

        checkSequence( module_statements )


        # TODO: Detect the exception from above
        if False and result == 2:
            sys.stderr.write( "Interruped, with CTRL-C\n" )
            sys.exit( 2 )


        # TODO: Detect error case
        if False and result != 0 and search_mode:
            print( "Error exit!", result )
            sys.exit( result )


        print( "OK." )

    else:
        print("Skipping", filename)
