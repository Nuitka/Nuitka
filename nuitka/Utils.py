#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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

def basename( path ):
    return os.path.basename( path )

def dirname( path ):
    return os.path.dirname( path )

def getExtension( path ):
    return os.path.splitext( path )[1]

def isFile( path ):
    return os.path.isfile( path )

def isDir( path ):
    return os.path.isdir( path )

def getCoreCount():
    cpu_count = 0

    # Try to sum up the CPU cores, if the kernel shows them, pylint: disable=W0702
    try:
        # Try to get the number of logical processors
        cpu_count = open( "/proc/cpuinfo" ).read().count( "processor\t:" )
    except:
        pass

    if not cpu_count:
        # false alarm, no re-import, just a function level import to avoid it unless it is
        # absolutely necessary, pylint: disable=W0404

        import multiprocessing
        cpu_count = multiprocessing.cpu_count()

    return cpu_count
