#!/usr/bin/env python3
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

    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)

    createReleaseDocumentation()
    assert os.system("python setup.py sdist --formats=gztar") == 0

    # Upload stable releases to OpenSUSE Build Service:
    if (
        branch_name.startswith("release")
        or branch_name.startswith("hotfix")
        or branch_name == "main"
    ):
        osc_project_name = "Nuitka"
        spec_suffix = ""
    elif branch_name == "develop":
        osc_project_name = "Nuitka-Unstable"
        spec_suffix = "-unstable"
    elif branch_name == "factory":
        osc_project_name = "Nuitka-experimental"
        spec_suffix = "-experimental"
    else:
        sys.exit("Skipping OSC for branch '%s'" % branch_name)

    # Cleanup the osc directory.
    shutil.rmtree("osc", ignore_errors=True)
    os.makedirs("osc")

    # Stage the "osc" checkout from the ground up.
    assert (
        os.system(
            f"""\
cd osc && \
osc checkout home:kayhayen {osc_project_name} && \
rm home:kayhayen/{osc_project_name}/* && \
cp ../dist/Nuitka-*.tar.gz home:kayhayen/{osc_project_name}/ && \
sed -e s/VERSION/{nuitka_version}/ ../rpm/nuitka.spec >home:kayhayen/{osc_project_name}/nuitka{spec_suffix}.spec && \
sed -i home:kayhayen/{osc_project_name}/nuitka{spec_suffix}.spec -e \
    's/Name: *nuitka/Name:           nuitka{spec_suffix}/' && \
cp ../rpm/nuitka-rpmlintrc home:kayhayen/{osc_project_name}/ && \
cd home:kayhayen/{osc_project_name}/ && \
osc addremove -r && \
echo 'New release' >ci_message && \
osc ci --file ci_message
"""
        )
        == 0
    )


if __name__ == "__main__":
    main()
