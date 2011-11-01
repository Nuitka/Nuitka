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
from setuptools import setup, find_packages

version_line, = [
    line
    for line in
    open( "nuitka/Options.py" )
    if line.startswith( "Nuitka V" )
]

version = version_line.split( "V" )[1].strip()

import sys
if sys.argv[1:] != [ "sdist", "--formats=gztar,bztar,zip" ]:
   sys.exit( "Error, only sdist target is currently working." )

setup(
    name     = "Nuitka",
    version  = version,
    packages = find_packages(),
    scripts  = [ 'bin/Nuitka.py', "bin/Python" ],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = [ 'docutils>=0.3' ],

    package_data = {
        # Include extra files
        '': ['*.txt', '*.rst', '*.cpp', '*.hpp', '*.ui' ],
    },

    # metadata for upload to PyPI
    author       = "Kay Hayen",
    author_email = "kayhayen@gmx.de",

    description = "Nuitka - Python compiler",

    license = "GPLv3",

    keywords = "compiler",

    url = "http://nuitka.net",

    # could also include long_description, download_url, classifiers, etc.
)
