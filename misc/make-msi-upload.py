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
""" Release: Create and upload Windows MSI files for Nuitka

"""

from __future__ import print_function

import os
import shutil
import subprocess
import sys

if os.path.isdir("dist"):
    shutil.rmtree("dist")

branch_name = subprocess.check_output(
    "git name-rev --name-only HEAD".split()
).strip()

print("Building for branch '%s'." % branch_name)

assert branch_name in (
    b"master",
    b"develop",
    b"factory",
), branch_name

assert 0 == subprocess.call(
    (
        sys.executable,
        "setup.py",
        "bdist_msi",
        "--target-version=" + sys.version[:3]
    )
)

for filename in os.listdir("dist"):
    if not filename.endswith(".msi"):
        continue

    break
else:
    sys.exit("No MSI created.")

parts = [
    filename[:-4].\
        replace("-py2.6","").\
        replace("-py2.7","").\
        replace("-py3.2","").\
        replace("-py3.3","").\
        replace("-py3.4","").\
        replace("-py3.5","").\
        replace("Nuitka32","Nuitka").\
        replace("Nuitka64","Nuitka"),
    "py" + sys.version[:3].replace('.',""),
    "msi"
]

new_filename = '.'.join(parts)

if branch_name == b"factory":
    new_filename = "Nuitka-factory." + new_filename[new_filename.find("win"):]

os.rename(os.path.join("dist",filename),os.path.join("dist",new_filename))

assert 0 == subprocess.call(
    (
        "C:\\MinGW\\msys\\1.0\\bin\\scp.exe",
        "dist/"+new_filename,
        "git@nuitka.net:/var/www/releases/"
    )
)

print("OK, uploaded to dist/" + new_filename)
