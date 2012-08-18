#!/usr/bin/env python
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

import os, sys

assert os.path.isfile( "setup.py" ) and open( ".git/description" ).read().strip() == "Nuitka Staging"

assert 0 == os.system( "rsync -rvlpt --exclude=deb_dist dist/ root@nuitka.net:/var/www/releases/" )

assert 0 == os.system( "scp README.pdf Changelog.pdf Developer_Manual.pdf doc/man-nuitka.html doc/man-nuitka-python.html root@nuitka.net:/var/www/doc/" )
