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

import sys, os

if not hasattr( sys, "version_info" ) or sys.version_info < (2, 6, 0, 'final'):
    raise SystemExit( "Nuitka requires Python 2.6 or later.")

if sys.version_info[0] >= 3:
    raise SystemExit( "Nuitka is not currently ported to 3.x, please help." )

scripts = [ "bin/Nuitka.py", "bin/Python" ]

if os.name == 'nt':
    scripts.append( 'misc/Nuitka.bat' )

def detectVersion():
    version_line, = [
        line
        for line in
        open( "nuitka/Options.py" )
        if line.startswith( "Nuitka V" )
    ]

    return version_line.split( "V" )[1].strip()

version = detectVersion()

# py2exe needs to be installed to work
try:
    import py2exe
    py2exeloaded = True
except ImportError:
    py2exeloaded = False

extra = {}

if py2exeloaded:
    extra['console'] = [
        {
            'script'          : 'Nuitka.py',
            'copyright'       : 'Copyright (C) 2011 Kay Hayen',
            'product_version' : version
        }
    ]


def find_packages():
    result = []

    for root, _dirnames, filenames in os.walk( "nuitka" ):
        if "__init__.py" not in filenames:
            continue

        result.append( root.replace( os.path.sep, "." ) )

    return result

package = find_packages()

from distutils.core import setup, Command, Extension

# TODO: Temporary only, until we have functional installation.
import sys
if sys.argv[1:] != [ "sdist", "--formats=gztar,bztar,zip" ]:
    sys.exit( "Error, only 'sdist --formats=gztar,bztar,zip' is currently working." )

setup(
    name     = "Nuitka",
    license  = "GPLv3",
    version  = version,
    packages = find_packages(),
    scripts  = scripts,

    package_data = {
        # Include extra files
        '': ['*.txt', '*.rst', '*.cpp', '*.hpp', '*.ui' ],
    },

    # metadata for upload to PyPI
    author       = "Kay Hayen",
    author_email = "kayhayen@gmx.de",
    url          = "http://nuitka.net",
    description  = "Python compiler with full language support and CPython compatibility",

    keywords     = "compiler,python,nuitka",
)
