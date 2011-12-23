#!/usr/bin/env python
#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
#

import os, sys, commands, subprocess

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

python_version = commands.getoutput( os.environ[ "PYTHON" ] + " --version" ).split()[1]

print "Using concrete python", python_version

for filename in sorted( os.listdir( "." ) ):
    if not os.path.isdir( filename ) or filename.endswith( ".build" ):
        continue

    path = os.path.relpath( filename )

    if not active and start_at in ( filename, path ):
        active = True

    if active:
        extra_flags = ""

        os.environ[ "PYTHONPATH" ] = os.path.abspath( filename )

        if filename == "syntax_errors":
            os.environ[ "NUITKA_EXTRA_OPTIONS" ] = "--recurse-all --execute-with-pythonpath"
        else:
            os.environ[ "NUITKA_EXTRA_OPTIONS" ] = "--recurse-all"

        print "Consider: ", path

        result = subprocess.call(
            "compare_with_cpython %s/*Main.py silent %s" % (
                filename,
                extra_flags
            ),
            shell = True
        )

        if result == 2:
            sys.stderr.write( "Interruped, with CTRL-C\n" )
            sys.exit( 2 )

        if result != 0 and search_mode:
            sys.exit( result )

    else:
        print "Skipping", filename
