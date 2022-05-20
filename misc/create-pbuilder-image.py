#!/usr/bin/python
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

""" Small tool to creaet a pbuilder image for Nuitka private CI mainly. """

import os
import shutil
import subprocess
import sys
import tempfile

debian, codename, output = sys.argv[1:]

if "-" in codename:
    codename, arch = codename.split("-")
else:
    arch = subprocess.check_output("dpkg-architecture -q DEB_HOST_ARCH".split()).strip()

start_dir = os.getcwd()

stage = tempfile.mkdtemp()

try:
    os.chdir(stage)

    if debian == "debian":
        mirror = "https://ftp.us.debian.org/debian"
        components = "main"
    elif debian == "ubuntu":
        mirror = "http://de.archive.ubuntu.com/ubuntu"
        components = "main,universe"
    else:
        assert False, debian

    subprocess.check_call(
        [
            "debootstrap",
            "--include=ccache",
            "--include=dpkg-dev",
            "--arch=" + arch,
            "--components=" + components,
            codename,
            "chroot",
            mirror,
        ]
    )

    subprocess.check_output(["rm", "-rf", "chroot/var/cache/apt/archives"])

    os.makedirs("chroot/var/cache/apt/archives")

    os.makedirs("chroot/etc/apt.conf.d")
    with open("chroot/etc/apt.conf.d/75mine", "w") as output_file:
        output_file.write('Acquire::Languages "none";\n')

    target_filename = codename + ".tgz"
    subprocess.check_call(["tar", "czf", target_filename, "-C", "chroot", "."])

    shutil.copy(target_filename, os.path.join(start_dir, output))
finally:
    os.chdir(start_dir)
    shutil.rmtree(stage)
