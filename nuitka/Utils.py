#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Utility module.

Here the small things for file/dir names, Python version, CPU counting, etc. that
fit nowhere else and don't deserve their own names.

"""

import sys, os

def getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 100 + major * 10 + minor

def relpath( path ):
    return os.path.relpath( path )

def abspath( path ):
    return os.path.abspath( path )

def joinpath( *parts ):
    return os.path.join( *parts )

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
