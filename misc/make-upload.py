#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import shutil
import subprocess
import sys

assert os.path.isfile("setup.py") and open(".git/description").read().strip() == "Nuitka Staging"

nuitka_version = subprocess.check_output("./bin/nuitka --version", shell = True).strip()
branch_name = subprocess.check_output("git name-rev --name-only HEAD".split()).strip()

assert branch_name in (b"master", b"develop", b"release/" + nuitka_version, b"hotfix/" +nuitka_version), branch_name

assert 0 == os.system("rsync -rvlpt --exclude=deb_dist dist/ root@nuitka.net:/var/www/releases/")

for filename in ("README.pdf", "Changelog.pdf", "Developer_Manual.pdf"):
    assert 0 == os.system("rsync %s root@nuitka.net:/var/www/doc/" % filename)

# Upload only stable releases to OpenSUSE Build Service:
if branch_name.startswith("release") or branch_name == "master":
    pass
elif branch_name == "develop":
    for remote in "origin", "bitbucket", "github", "gitlab":
        assert 0 == os.system("git push --tags -f %s develop" % remote)
        assert 0 == os.system("git push %s master" % remote)
else:
    sys.stdout.write("Skipping for branch '%s'" % branch_name)
