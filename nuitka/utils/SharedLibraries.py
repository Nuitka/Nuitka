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
""" This module deals with finding and information about shared libraries.

"""

from sys import getfilesystemencoding

from nuitka.PythonVersions import python_version


def locateDLL(dll_name):
    import ctypes.util

    dll_name = ctypes.util.find_library(dll_name)

    import subprocess
    process = subprocess.Popen(
        args   = ["/sbin/ldconfig", "-p"],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    stdout, _stderr = process.communicate()

    dll_map = {}

    for line in stdout.splitlines()[1:]:
        assert line.count(b"=>") == 1, line
        left, right = line.strip().split(b" => ")
        assert b" (" in left, line
        left = left[:left.rfind(b" (")]

        if python_version >= 300:
            left = left.decode(getfilesystemencoding())
            right = right.decode(getfilesystemencoding())

        if left not in dll_map:
            dll_map[left] = right

    return dll_map[dll_name]
