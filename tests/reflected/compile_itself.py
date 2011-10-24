#!/usr/bin/python
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

import os, sys, shutil, tempfile, time, difflib

# Go its own directory, to have it easy with path knowledge.
os.chdir( os.path.dirname( os.path.abspath( __file__ ) ) )

tmp_dir = tempfile.gettempdir()

os.environ[ "PYTHONPATH_BAK" ] = os.environ[ "PYTHONPATH" ]

# Could detect this more automatic.
PACKAGE_LIST = (
    'nuitka',
    'nuitka/nodes',
    'nuitka/codegen',
    'nuitka/codegen/templates',
    'nuitka/transform',
    'nuitka/transform/optimizations',
    'nuitka/transform/finalizations',
)

def diffRecursive( dir1, dir2 ):
    done = set()

    for filename in os.listdir( dir1 ):
        path1 = dir1 + os.path.sep + filename
        path2 = dir2 + os.path.sep + filename

        if not os.path.exists( path2 ):
            sys.exit( "Only in %s: %s" % ( dir1, filename ))

        if os.path.isdir( path1 ):
            diffRecursive( path1, path2 )
        elif os.path.isfile( path1 ):
            fromdate = time.ctime( os.stat( path1 ).st_mtime )
            todate = time.ctime( os.stat( path2 ).st_mtime )

            diff = difflib.unified_diff(
                open( path1 ).readlines(),
                open( path2 ).readlines(),
                path1,
                path2,
                fromdate,
                todate,
                n=3
            )

            result = list( diff )

            if result:
                for line in result:
                    print line

                sys.exit( 1 )
        else:
            assert False, path1

        done.add( path1 )

    for filename in os.listdir( dir2 ):
        path1 = dir1 + os.path.sep + filename
        path2 = dir2 + os.path.sep + filename

        if path1 in done:
            continue

        if not os.path.exists( dir1 + os.path.sep + filename ):
            sys.exit( "Only in %s: %s" % ( dir2, filename ))

def executePASS1():
    print "PASS 1: Compiling from compiler running from .py files."

    for package in PACKAGE_LIST:
        package = package.replace( "/", os.path.sep )

        source_dir = ".." + os.path.sep + ".." + os.path.sep + package
        target_dir = package

        if os.path.exists( target_dir ):
            shutil.rmtree( target_dir )

        os.mkdir( target_dir )

        for filename in os.listdir( target_dir ):
            if filename.endswith( ".so" ):
                path = target_dir + os.path.sep + ".so"

                os.unlink( path )

        for filename in sorted( os.listdir( source_dir ) ):
            if not filename.endswith( ".py" ):
                continue

            path = source_dir + os.path.sep + filename

            if filename != "__init__.py":
                print "Compiling", path

                result = os.system(
                    "Nuitka.py %s --output-dir %s %s" % (
                        path,
                        target_dir,
                        os.environ.get( "NUITKA_EXTRA_OPTIONS", "" )
                    )
                )

                if result != 0:
                    sys.exit( result )
            else:
                shutil.copyfile( path, target_dir + os.path.sep + filename )


    path = ".." + os.path.sep + ".." + os.path.sep + "bin" + os.path.sep + "Nuitka.py"

    print "Compiling", path

    result = os.system(
        "Nuitka.py %s --exe --output-dir %s %s" % (
            path,
            ".",
            os.environ.get( "NUITKA_EXTRA_OPTIONS", "" )
        )
    )

    if result != 0:
        sys.exit( result )

def compileAndCompareWith( nuitka ):
    for package in PACKAGE_LIST:
        package = package.replace( "/", os.path.sep )

        source_dir = ".." + os.path.sep + ".." + os.path.sep + package

        for filename in sorted( os.listdir( source_dir ) ):
            if not filename.endswith( ".py" ):
                continue

            path = source_dir + os.path.sep + filename

            if filename != "__init__.py":
                print "Compiling", path

                target = filename.replace( ".py", ".build" )

                target_dir = tmp_dir + os.path.sep + target

                if os.path.exists( target_dir ):
                    shutil.rmtree( target_dir )

                result = os.system(
                    "%s %s --output-dir %s %s" % (
                        nuitka,
                        path,
                        tmp_dir,
                        os.environ.get( "NUITKA_EXTRA_OPTIONS", "" )
                    )
                )

                if result != 0:
                    sys.exit( result )

                diffRecursive( package + os.path.sep + target, target_dir )

                shutil.rmtree( target_dir )

def executePASS2():
    print "PASS 2: Compiling from compiler running from .exe and many .so files."

    os.environ[ "PYTHONPATH" ] = "."
    compileAndCompareWith( "." + os.path.sep + "Nuitka.exe" )

    print "OK."

def executePASS3():
    print "PASS 3: Compiling from compiler running from .py files to single .exe."

    if os.path.exists( tmp_dir + os.path.sep + "Nuitka.exe" ):
        os.unlink( tmp_dir + os.path.sep + "Nuitka.exe" )

    if os.path.exists( tmp_dir + os.path.sep + "Nuitka.build" ):
        shutil.rmtree( tmp_dir + os.path.sep + "Nuitka.build" )

    os.environ[ "PYTHONPATH" ] = os.environ[ "PYTHONPATH_BAK" ]

    path = ".." + os.path.sep + ".." + os.path.sep + "bin" + os.path.sep + "Nuitka.py"

    print "Compiling", path
    result = os.system(
        "Nuitka.py %s --output-dir %s --exe --deep" % (
            path,
            tmp_dir
        )
    )

    if result != 0:
        sys.exit( result )

    shutil.rmtree( tmp_dir + os.path.sep + "Nuitka.build" )

    print "OK."

def executePASS4():
    print "PASS 4: Compiling the compiler running from single exe"

    os.environ[ "PYTHONPATH" ] = "."
    compileAndCompareWith( tmp_dir + os.path.sep + "Nuitka.exe" )

    print "OK."

executePASS1()
executePASS2()
executePASS3()
executePASS4()

shutil.rmtree( "nuitka" )
