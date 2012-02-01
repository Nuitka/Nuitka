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

import os, subprocess

assert 0 == subprocess.call( "git submodule update misc/gist", shell = True )

for document in ( "README.txt", "Developer_Manual.rst", "Changelog.rst" ):
    assert 0 == subprocess.call(
        "rst2pdf %(document)s" % {
            "document" : document
        },
        shell = True
    )
    assert 0 == subprocess.call(
        "python ./misc/gist/rst2html.py %(document)s >%(doc_base)s.html" % {
            "document" : document,
            "doc_base" : document[:-4]
        },
        shell = True
    )

if not os.path.exists( "man" ):
    os.mkdir( "man" )

assert 0 == subprocess.call( "help2man -n 'the Python compiler' --no-discard-stderr --no-info --include doc/nuitka-man-include.txt ./bin/nuitka >doc/nuitka.1", shell = True )
assert 0 == subprocess.call( "help2man -n 'the Python compiler' --no-discard-stderr --no-info ./bin/nuitka-python >doc/nuitka-python.1", shell = True )

for manpage in ( "doc/nuitka.1", "doc/nuitka-python.1" ):
    manpage_contents = open( manpage ).readlines()
    new_contents = []
    mark = False

    for count, line in enumerate( manpage_contents ):
        if mark:
            line = ".SS " + line + ".BR\n"
            mark = False
        elif line == ".IP\n" and manpage_contents[ count + 1 ].endswith( ":\n" ):
            mark = True
            continue

        if line == r"\fB\-\-g\fR++\-only" + "\n":
            line = r"\fB\-\-g\++\-only\fR" + "\n"

        new_contents.append( line )

    open( manpage, "w" ).writelines( new_contents )

assert 0 == subprocess.call( "man2html doc/nuitka.1 >doc/man-nuitka.html", shell = True )
assert 0 == subprocess.call( "man2html doc/nuitka-python.1 >doc/man-nuitka-python.html", shell = True )

def getFile( filename ):
    return open( filename ).read()

contents = getFile( "doc/man-nuitka.html" )
new_contents = contents[ : contents.rfind( "<HR>" ) ] + contents[ contents.rfind( "</BODY>" ) : ]
assert new_contents != contents

open( "doc/man-nuitka.html", "w" ).write( new_contents )

contents = getFile( "doc/man-nuitka-python.html" )
new_contents = contents[ : contents.rfind( "<HR>" ) ] + contents[ contents.rfind( "</BODY>" ) : ]
assert new_contents != contents

open( "doc/man-nuitka-python.html", "w" ).write( new_contents )
