#!/usr/bin/env python
#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
#     This is to reserve my ability to re-license the code at a later time to
#     the PSF. With this version of Nuitka, using it for a Closed Source and
#     distributing the binary only is not allowed.
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

import os, sys, shutil, subprocess, tarfile

def checkAtHome():
    assert os.path.isfile( "setup.py" ) and open( ".git/description" ).read().strip() == "Nuitka Staging"

checkAtHome()

branch_name = subprocess.check_output( "git name-rev --name-only HEAD".split() ).strip()

assert branch_name in ( b"master", b"develop" ), branch_name

shutil.rmtree( "dist", ignore_errors = True )
shutil.rmtree( "build", ignore_errors = True )

assert 0 == os.system( "python setup.py sdist --formats=bztar,gztar,zip" )

os.chdir( "dist" )

if os.path.exists( "deb_dist" ):
    shutil.rmtree( "deb_dist" )

for filename in os.listdir( "." ):
    if filename.endswith( ".tar.gz" ):
        new_name = filename[:-7] + "+ds.tar.gz"

        # Create a +ds file, removing:

        # - the benchmarks (too many sources, not useful to end users, potential license
        #   issues)
        # - the inline copy of scons (not wanted for Debian)
        shutil.copy( filename, new_name )
        assert 0 == os.system( "gunzip " + new_name )
        assert 0 == os.system( "tar --wildcards --delete --file " + new_name[:-3] + " Nuitka*/tests/benchmarks Nuitka*/nuitka/build/inline_copy"  )
        assert 0 == os.system( "gzip -9 -n " + new_name[:-3] )

        assert 0 == os.system( "py2dsc " + new_name )

        # Fixup for py2dsc not taking our custom suffix into account, so we need to rename
        # it ourselves.
        before_deb_name = filename[:-7].lower().replace( "-", "_" )
        after_deb_name = before_deb_name.replace( "pre", "~pre" )

        assert 0 == os.system( "mv 'deb_dist/%s.orig.tar.gz' 'deb_dist/%s+ds.orig.tar.gz'" % ( before_deb_name, after_deb_name ) )

        break
else:
    assert False



os.chdir( "deb_dist" )

for entry in os.listdir( "." ):
    if os.path.isdir( entry ) and entry.startswith( "nuitka" ) and not entry.endswith( ".orig" ):
        break
else:
    assert False

assert 0 == os.system( "rsync -a ../../debian/ %s/debian/" % entry )

assert 0 == os.system( "rm *.dsc *.debian.tar.gz" )

os.chdir( entry )

print( "Checking licenses... " )
for line in subprocess.check_output( "licensecheck -r .", shell = True ).strip().split( b"\n" ):
    assert b"UNKNOWN" not in line, line


assert 0 == os.system( "debuild --set-envvar=NUITKA_SKIP_TESTS=1" )

os.chdir( "../../.." )

checkAtHome()

assert 0 == os.system( "sudo /usr/sbin/pbuilder --build dist/deb_dist/*.dsc" )

assert 0 == os.system( "lintian --pedantic --fail-on-warnings dist/deb_dist/*.changes" )

os.system( "cp dist/deb_dist/*.deb dist/" )

assert os.path.exists( "dist/deb_dist" )

for filename in os.listdir( "dist/deb_dist" ):
    if os.path.isdir( "dist/deb_dist/" + filename ):
        shutil.rmtree( "dist/deb_dist/" + filename )

assert 0 == os.system( r"wine c:\\python27\\python.exe setup.py bdist_wininst --bitmap misc/Nuitka-Installer.bmp" )


for filename in os.listdir( "dist" ):
    if os.path.isfile( "dist/" + filename ):
        assert 0 == os.system( "chmod 644 dist/" + filename )
        assert 0 == os.system( "gpg --local-user 0BCF7396 --detach-sign dist/" + filename )

shutil.rmtree( "build", ignore_errors = True )

print( "Finished." )
