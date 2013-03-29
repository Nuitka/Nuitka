#!/usr/bin/env python
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

import os, sys, shutil, subprocess

assert os.path.isfile( "setup.py" ) and open( ".git/description" ).read().strip() == "Nuitka Staging"

nuitka_version = subprocess.check_output( "./bin/nuitka --version", shell = True ).strip()
branch_name = subprocess.check_output( "git name-rev --name-only HEAD".split() ).strip()

assert branch_name in ( b"master", b"develop", b"release/" + nuitka_version, b"hotfix/" + nuitka_version ), branch_name

assert 0 == os.system( "rsync -rvlpt --exclude=deb_dist dist/ root@nuitka.net:/var/www/releases/" )

assert 0 == os.system( "scp README.pdf Changelog.pdf Developer_Manual.pdf doc/man-nuitka.html doc/man-nuitka-python.html root@nuitka.net:/var/www/doc/" )

# Upload only stable releases to OpenSUSE Build Service: TODO: Not yet there.
if branch_name.startswith( "release" ) or branch_name == "master":
    # Cleanup the osc directory.
    shutil.rmtree( "osc", ignore_errors = True )

    os.makedirs( "osc" )
    os.system( "cd osc && osc init home:kayhayen Nuitka && osc repairwc && cp ../dist/Nuitka-*.tar.gz . && cp ../misc/nuitka.spec . && cp ../misc/nuitka-python3 . && cp ../misc/nuitka-rpmlintrc . && osc addremove && echo 'New release' >ci_message && osc ci --file ci_message" )

    # Cleanup the osc directory.
    shutil.rmtree( "osc", ignore_errors = True )
