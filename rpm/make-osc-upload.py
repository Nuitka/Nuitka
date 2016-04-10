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

nuitka_version = subprocess.check_output(
    "./bin/nuitka --version", shell = True
).strip()
branch_name = subprocess.check_output(
    "git name-rev --name-only HEAD".split()
).strip()

assert branch_name in (
    b"master",
    b"develop",
    b'factory',
    b"release/" + nuitka_version,
    b"hotfix/" + nuitka_version
), branch_name

shutil.rmtree("dist", ignore_errors = True)
shutil.rmtree("build", ignore_errors = True)

assert 0 == os.system("misc/make-doc.py")
assert 0 == os.system("python setup.py sdist --formats=gztar")

# Upload stable releases to OpenSUSE Build Service:
if branch_name.startswith("release") or \
   branch_name.startswith("hotfix") or \
   branch_name == "master":
    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors = True)
    os.makedirs("osc")

    # Stage the "osc" checkout from the ground up.
    assert 0 == os.system("cd osc && osc init home:kayhayen Nuitka && osc repairwc && cp ../dist/Nuitka-*.tar.gz . && sed -e s/VERSION/%s/ ../rpm/nuitka.spec >./nuitka.spec && cp ../rpm/nuitka-run3 . && cp ../rpm/nuitka-rpmlintrc . && osc addremove && echo 'New release' >ci_message && osc ci --file ci_message" % nuitka_version)

    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors = True)
elif branch_name == "develop":
    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors = True)
    os.makedirs("osc")

    # Stage the "osc" checkout from the ground up, but path the RPM spec to say
    # it is nuitks-unstable package.
    assert 0 == os.system("cd osc && osc init home:kayhayen Nuitka-Unstable && osc repairwc && cp ../dist/Nuitka-*.tar.gz . && sed -e s/VERSION/%s/ ../rpm/nuitka.spec >./nuitka-unstable.spec && sed -i nuitka-unstable.spec -e 's/Name: *nuitka/Name:           nuitka-unstable/' && cp ../rpm/nuitka-run3 . && cp ../rpm/nuitka-rpmlintrc . && osc addremove && echo 'New release' >ci_message && osc ci --file ci_message" % nuitka_version)

    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors = True)
elif branch_name == "factory":
    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors = True)
    os.makedirs("osc")

    # Stage the "osc" checkout from the ground up, but path the RPM spec to say
    # it is nuitks-unstable package.
    assert 0 == os.system("cd osc && osc init home:kayhayen Nuitka-experimental && osc repairwc && cp ../dist/Nuitka-*.tar.gz . && sed -e s/VERSION/%s/ ../rpm/nuitka.spec >./nuitka-experimental.spec && sed -i nuitka-experimental.spec -e 's/Name: *nuitka/Name:           nuitka-experimental/' && cp ../rpm/nuitka-run3 . && cp ../rpm/nuitka-rpmlintrc . && osc addremove && echo 'New release' >ci_message && osc ci --file ci_message" % nuitka_version)

    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors = True)
else:
    sys.exit("Skipping OSC for branch '%s'" % branch_name)
