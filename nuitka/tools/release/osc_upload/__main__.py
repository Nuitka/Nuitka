#!/usr/bin/env python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" OpenSUSE Build Service (OSC) upload release tool.

Uploads Nuitka branches adapting the RPM configuration to the different
projects on OSC.
"""


import os
import shutil
import sys

from nuitka.tools.release.Documentation import createReleaseDocumentation
from nuitka.tools.release.Release import checkBranchName
from nuitka.Version import getNuitkaVersion


def main():
    nuitka_version = getNuitkaVersion()
    branch_name = checkBranchName()

    shutil.rmtree("dist", ignore_errors = True)
    shutil.rmtree("build", ignore_errors = True)

    createReleaseDocumentation()
    assert os.system("python setup.py sdist --formats=gztar") == 0

    # Upload stable releases to OpenSUSE Build Service:
    if branch_name.startswith("release") or \
       branch_name.startswith("hotfix") or \
       branch_name == "master":
        # Cleanup the osc directory.
        shutil.rmtree("osc", ignore_errors = True)
        os.makedirs("osc")

        # Stage the "osc" checkout from the ground up.
        assert os.system("""\
cd osc && \
osc init home:kayhayen Nuitka && osc repairwc && \
cp ../dist/Nuitka-*.tar.gz . && \
sed -e s/VERSION/%s/ ../rpm/nuitka.spec >./nuitka.spec && \
cp ../rpm/nuitka-rpmlintrc . && \
osc addremove && \
echo 'New release' >ci_message && \
osc ci --file ci_message
""" % nuitka_version) == 0

        # Cleanup the osc directory.
        shutil.rmtree("osc", ignore_errors = True)
    elif branch_name == "develop":
        # Cleanup the osc directory.
        shutil.rmtree("osc", ignore_errors = True)
        os.makedirs("osc")

        # Stage the "osc" checkout from the ground up, but path the RPM spec to say
        # it is nuitks-unstable package.
        assert os.system("""\
cd osc && \
osc init home:kayhayen Nuitka-Unstable && \
osc repairwc && \
cp ../dist/Nuitka-*.tar.gz . && \
sed -e s/VERSION/%s/ ../rpm/nuitka.spec >./nuitka-unstable.spec && \
sed -i nuitka-unstable.spec -e 's/Name: *nuitka/Name:           nuitka-unstable/' && \
cp ../rpm/nuitka-rpmlintrc . && \
osc addremove && echo 'New release' >ci_message && \
osc ci --file ci_message
""" % nuitka_version) == 0

        # Cleanup the osc directory.
        shutil.rmtree("osc", ignore_errors = True)
    elif branch_name == "factory":
        # Cleanup the osc directory.
        shutil.rmtree("osc", ignore_errors = True)
        os.makedirs("osc")

        # Stage the "osc" checkout from the ground up, but path the RPM spec to say
        # it is nuitks-unstable package.
        assert os.system("""\
cd osc && \
osc init home:kayhayen Nuitka-experimental && \
osc repairwc && \
cp ../dist/Nuitka-*.tar.gz . && \
sed -e s/VERSION/%s/ ../rpm/nuitka.spec >./nuitka-experimental.spec && \
sed -i nuitka-experimental.spec -e 's/Name: *nuitka/Name:           nuitka-experimental/' && \
cp ../rpm/nuitka-rpmlintrc . && \
osc addremove && \
echo 'New release' >ci_message && osc ci --file ci_message
""" % nuitka_version) == 0

        # Cleanup the osc directory.
        shutil.rmtree("osc", ignore_errors = True)
    else:
        sys.exit("Skipping OSC for branch '%s'" % branch_name)

if __name__ == "__main__":
    main()
