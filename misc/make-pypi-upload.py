#!/usr/bin/env python
#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import os, sys, shutil, subprocess

nuitka_version = subprocess.check_output(
    "./bin/nuitka --version", shell = True
).strip()
branch_name = subprocess.check_output(
    "git name-rev --name-only HEAD".split()
).strip()

assert branch_name == "master", branch_name
assert "pre" not in nuitka_version

# Need to remove the contents from the Rest, or else PyPI will not render
# it. Stupid but true.
contents = open("README.rst", "rb").read()
contents.replace(b".. contents::", b"")
open("README.rst", "wb").write(contents)
contents = open("README.rst", "rb").read()
assert ".. contents" not in contents

assert 0 == os.system("misc/make-doc.py")
assert 0 == os.system("python setup.py sdist upload")

# A delay might be necessary before making the check.

import xmlrpclib
import time

# Wait some time for PyPI to catch up with us. Without delay
# the old version will still appear. Since this is running
# in a Buildbot, we need not be optimal.
time.sleep(360)

pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
pypi_versions = pypi.package_releases("Nuitka")

assert len(pypi_versions) == 1, pypi_versions
assert nuitka_version == pypi_versions[0], (nuitka_version, pypi_versions)

print("Uploaded OK:", pypi_versions[0])
