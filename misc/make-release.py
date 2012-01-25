#!/usr/bin/env python
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

import os, sys, shutil, subprocess, tarfile

from optparse import OptionParser, OptionGroup

parser = OptionParser()

parser.add_option(
    "--use-as-ds-source",
    action  = "store",
    dest    = "ds_source",
    default = None,
    help    = """\
When given, use this as the source for the Debian package instead. Default %default."""
)

parser.add_option(
    "--no-check-debian-sid",
    action  = "store_false",
    dest    = "debian_sid",
    default = True,
    help    = """\
Check the created Debian package in a Debian Sid pbuilder. Default %default."""
)

parser.add_option(
    "--check-ubuntu-maverick",
    action  = "store_true",
    dest    = "ubuntu_maverick",
    default = False,
    help    = """\
Check the created Debian package in a Ubuntu Maveric pbuilder. Default %default."""
)

parser.add_option(
    "--check-ubuntu-natty",
    action  = "store_true",
    dest    = "ubuntu_natty",
    default = False,
    help    = """\
Check the created Debian package in a Ubuntu Natty pbuilder. Default %default."""
)

parser.add_option(
    "--check-ubuntu-oneiric",
    action  = "store_true",
    dest    = "ubuntu_oneiric",
    default = False,
    help    = """\
Check the created Debian package in a Ubuntu Oneiric pbuilder. Default %default."""
)

parser.add_option(
    "--check-ubuntu-precise",
    action  = "store_true",
    dest    = "ubuntu_precise",
    default = False,
    help    = """\
Check the created Debian package in a Ubuntu Precise pbuilder. Default %default."""
)

options, positional_args = parser.parse_args()

assert not positional_args, positional_args

def checkAtHome():
    assert os.path.isfile( "setup.py" ) and open( ".git/description" ).read().strip() == "Nuitka Staging"

checkAtHome()

nuitka_version = subprocess.check_output( "./bin/nuitka --version", shell = True ).strip()
branch_name = subprocess.check_output( "git name-rev --name-only HEAD".split() ).strip()

assert branch_name in ( b"master", b"develop", b"release/" + nuitka_version, b"hotfix/" + nuitka_version ), branch_name

shutil.rmtree( "dist", ignore_errors = True )
shutil.rmtree( "build", ignore_errors = True )

assert 0 == os.system( "python setup.py sdist --formats=bztar,gztar,zip" )

os.chdir( "dist" )

# Clean the stage for the debian package. The name "deb_dist" is what "py2dsc" uses for
# its output later on.

if os.path.exists( "deb_dist" ):
    shutil.rmtree( "deb_dist" )

# Provide a re-packed tar.gz for the Debian package as input.

# Create it as a "+ds" file, removing:
# - the benchmarks (too many sources, not useful to end users, potential license
#   issues)
# - the inline copy of scons (not wanted for Debian)

# Then run "py2dsc" on it.

for filename in os.listdir( "." ):
    if filename.endswith( ".tar.gz" ):
        new_name = filename[:-7] + "+ds.tar.gz"

        shutil.copy( filename, new_name )
        assert 0 == os.system( "gunzip " + new_name )
        assert 0 == os.system( "tar --wildcards --delete --file " + new_name[:-3] + " Nuitka*/tests/benchmarks Nuitka*/nuitka/build/inline_copy Nuitka*/*.pdf"  )
        assert 0 == os.system( "gzip -9 -n " + new_name[:-3] )

        assert 0 == os.system( "py2dsc " + new_name )

        # Fixup for py2dsc not taking our custom suffix into account, so we need to rename
        # it ourselves.
        before_deb_name = filename[:-7].lower().replace( "-", "_" )
        after_deb_name = before_deb_name.replace( "pre", "~pre" )

        assert 0 == os.system( "mv 'deb_dist/%s.orig.tar.gz' 'deb_dist/%s+ds.orig.tar.gz'" % ( before_deb_name, after_deb_name ) )

        # Remove the now useless input, py2dsc has copied it, and we don't publish it.
        os.unlink( new_name )

        if options.ds_source is not None:
            shutil.copyfile( options.ds_source, "deb_dist/%s+ds.orig.tar.gz" % after_deb_name )

        break
else:
    assert False

os.chdir( "deb_dist" )

# Assert that the unpacked directory is there and file it. Otherwise fail badly.
for entry in os.listdir( "." ):
    if os.path.isdir( entry ) and entry.startswith( "nuitka" ) and not entry.endswith( ".orig" ):
        break
else:
    assert False

# Import the "debian" directory from above. It's not in the original tar and overrides or
# extends what py2dsc does.
assert 0 == os.system( "rsync -a --exclude pbuilder-hookdir ../../debian/ %s/debian/" % entry )

assert 0 == os.system( "rm *.dsc *.debian.tar.gz" )

os.chdir( entry )

# Check for licenses and do not accept "UNKNOWN", because that means a proper license
# string is missing. Not the case for current Nuitka and it shall remain that way.
print( "Checking licenses... " )
for line in subprocess.check_output( "licensecheck -r .", shell = True ).strip().split( b"\n" ):
    assert b"UNKNOWN" not in line, line

# Build the debian package, but disable the running of tests, will be done later in the
# pbuilder test steps.
assert 0 == os.system( "debuild --set-envvar=NUITKA_SKIP_TESTS=1" )

os.chdir( "../../.." )

checkAtHome()

assert os.path.exists( "dist/deb_dist" )

# Check with pylint in pedantic mode and don't procede if there were any warnings
# given. Nuitka is lintian clean and shall remain that way.
assert 0 == os.system( "lintian --pedantic --fail-on-warnings dist/deb_dist/*.changes" )

os.system( "cp dist/deb_dist/*.deb dist/" )

# Build inside the pbuilder chroot, which should be an updated sid. The update is
# not done here. TODO: Add a time based check that e.g. runs it with --update at
# least every 24 hours or so.

basetgz_list = []

if options.debian_sid:
    basetgz_list.append( "base.tgz" )

if options.ubuntu_oneiric:
    basetgz_list.append( "oneiric.tgz" )

if options.ubuntu_maverick:
    basetgz_list.append( "maverick.tgz" )

if options.ubuntu_natty:
    basetgz_list.append( "natty.tgz" )

if options.ubuntu_precise:
    basetgz_list.append( "precise.tgz" )

for basetgz in basetgz_list:
    command = "sudo /usr/sbin/pbuilder --build --basetgz  /var/cache/pbuilder/%s --hookdir debian/pbuilder-hookdir dist/deb_dist/*.dsc" % basetgz

    assert 0 == os.system( command ), basetgz

for filename in os.listdir( "dist/deb_dist" ):
    if os.path.isdir( "dist/deb_dist/" + filename ):
        shutil.rmtree( "dist/deb_dist/" + filename )

# Build the Windows installer.
assert 0 == os.system( r"wine c:\\python27\\python.exe setup.py bdist_wininst --bitmap misc/Nuitka-Installer.bmp" )

# Sign the result files. The Debian binary package was copied here.
for filename in os.listdir( "dist" ):
    if os.path.isfile( "dist/" + filename ):
        assert 0 == os.system( "chmod 644 dist/" + filename )
        assert 0 == os.system( "gpg --local-user 0BCF7396 --detach-sign dist/" + filename )

# Cleanup the build directory, not needed.
shutil.rmtree( "build", ignore_errors = True )

print( "Finished." )
