#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Upload the packaging results and/or push branches.

"""

import os
import sys

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought be there.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

# isort:start

from nuitka.tools.release.Release import checkAtHome, checkBranchName
from nuitka.utils.Execution import check_output

checkAtHome()

nuitka_version = check_output(
    "%s ./bin/nuitka --version" % sys.executable, shell=True
).strip()

branch_name = checkBranchName()

if branch_name == "factory":
    for remote in "origin", "github":
        assert (
            os.system(
                "git push --recurse-submodules=no --force-with-lease %s factory"
                % remote
            )
            == 0
        )

    sys.exit(0)

assert (
    os.system(
        "rsync -rvlpt --exclude=deb_dist dist/ root@ssh.nuitka.net:/var/www/releases/"
    )
    == 0
)

for filename in ("README.pdf", "Changelog.pdf", "Developer_Manual.pdf"):
    assert os.system("rsync %s root@ssh.nuitka.net:/var/www/doc/" % filename) == 0

# Upload only stable and develop releases to OpenSUSE Build Service:
if branch_name.startswith("release") or branch_name == "main":
    pass
elif branch_name == "develop":
    for remote in "origin", "github":
        assert (
            os.system(
                "git push --recurse-submodules=no --tags --force-with-lease %s develop"
                % remote
            )
            == 0
        )
        assert os.system("git push %s main" % remote) == 0
else:
    sys.stdout.write("Skipping for branch '%s'" % branch_name)
