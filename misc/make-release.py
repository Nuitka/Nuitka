#!/usr/bin/python
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

import os, sys, shutil

assert os.path.isfile( "setup.py" ) and open( ".git/description" ).read().strip() == "Nuitka Staging"

shutil.rmtree( "dist", ignore_errors = True )
shutil.rmtree( "build", ignore_errors = True )

assert 0 == os.system( "python setup.py sdist --formats=bztar,gztar,zip" )

os.chdir( "dist" )

assert 0 == os.system( "py2dsc *.tar.gz" )

os.chdir( "deb_dist" )

for entry in os.listdir( "." ):
    if os.path.isdir( entry ) and entry.startswith( "nuitka" ) and not entry.endswith( ".orig" ):
        break
else:
    assert False

print "Found", entry

assert 0 == os.system( "rsync -a ../../debian/ %s/debian/" % entry )

assert 0 == os.system( "rm *.dsc *.debian.tar.gz" )

os.chdir( entry )

# 1. Remove the inline copy of Scons. On Debian there is a dependency.
shutil.rmtree( "nuitka/build/inline_copy", False )

# 2. Remove the sys.path tricks from Nuitka binary.
lines = open( "bin/nuitka" ).readlines()
inside = False
output = open( "bin/nuitka", "wb" )

for line in lines:
    if "LIBDIR trick start" in line:
        inside = True

    if not inside:
        output.write( line )

    if "LIBDIR trick end" in line:
        inside = False

output.close()

assert 0 == os.system( "EDITOR='cat </dev/null' dpkg-source --commit . remove-sys-path-trick" )

assert 0 == os.system( "debuild" )

os.chdir( "../../.." )

assert os.path.isfile( "setup.py" ) and open( ".git/description" ).read().strip() == "Nuitka Staging"

os.system( "mv dist/deb_dist/*.deb dist/" )

shutil.rmtree( "dist/deb_dist" )

# assert 0 == os.system( "wine python.exe setup.py bdist_wininst" )
