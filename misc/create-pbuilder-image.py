#!/usr/bin/python
#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
import tempfile

debian, codename, output = sys.argv[1:]

start_dir = os.getcwd()

stage = tempfile.mkdtemp()

try:
    os.chdir(stage)

    for line in subprocess.check_output(["apt-config", "dump"]).splitlines():
        if line.startswith("Acquire::http::Proxy "):
            mirror = line.split(" ", 1)[1][:-1].strip('"')
            break
    else:
        sys.exit("Need acquire proxy, so we have hope it's apt-cacher using.")

    if debian == "debian":
        mirror += "/ftp.us.debian.org/debian"
        components = "main"
    elif debian == "ubuntu":
        mirror += "/archive.ubuntu.com/ubuntu"
        components = "main,universe"
    else:
        assert False, debian

    subprocess.check_call(
        [
            "debootstrap",
            "--include=ccache",
            "--components=" + components,
            codename,
            "chroot",
            mirror
        ]
    )

    subprocess.check_output(
        [
            "rm",
            "-rf",
            "chroot/var/cache/apt/archives",
        ],
    )

    os.makedirs("chroot/var/cache/apt/archives")

    os.makedirs("chroot/etc/apt.conf.d")
    with open("chroot/etc/apt.conf.d/75mine", "w") as output_file:
        output_file.write('Acquire::Languages "none";\n')

    subprocess.check_call(
        [
            "tar",
            "czf",
            "chroot.tgz",
            "-C",
            "chroot",
            "."
        ]
    )

    shutil.copy("chroot.tgz", os.path.join(start_dir, output))
finally:
    os.chdir(start_dir)
    shutil.rmtree(stage)
