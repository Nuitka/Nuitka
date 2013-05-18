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
""" Utility module.

Here the small things for file/dir names, Python version, CPU counting,
etc. that fit nowhere else and don't deserve their own names.

"""

import sys, os

def _getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 100 + major * 10 + minor

python_version = _getPythonVersion()

def relpath( path ):
    return os.path.relpath( path )

def abspath( path ):
    return os.path.abspath( path )

def joinpath( *parts ):
    return os.path.join( *parts )

def splitpath( path ):
    return tuple( element for element in os.path.split( path ) if element )

def basename( path ):
    return os.path.basename( path )

def dirname( path ):
    return os.path.dirname( path )

def normpath( path ):
    return os.path.normpath( path )

def normcase( path ):
    return os.path.normcase( path )

def getExtension( path ):
    return os.path.splitext( path )[1]

def isFile( path ):
    return os.path.isfile( path )

def isDir( path ):
    return os.path.isdir( path )

def listDir( path ):
    """ Give a sorted path, basename pairs of a directory."""

    return sorted(
        [
            ( joinpath( path, filename ), filename )
            for filename in
            os.listdir( path )
        ]
    )

def deleteFile( path, must_exist ):
    if must_exist or isFile( path ):
        os.unlink( path )

def makePath( path ):
    os.makedirs( path )

def getCoreCount():
    cpu_count = 0

    # Try to sum up the CPU cores, if the kernel shows them, pylint: disable=W0702
    try:
        # Try to get the number of logical processors
        with open( "/proc/cpuinfo" ) as cpuinfo_file:
            cpu_count = cpuinfo_file.read().count( "processor\t:" )
    except:
        pass

    if not cpu_count:
        # false alarm, no re-import, just a function level import to avoid it unless it is
        # absolutely necessary, pylint: disable=W0404

        import multiprocessing
        cpu_count = multiprocessing.cpu_count()

    return cpu_count
