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
""" Utils to work with shebang lines.

"""
import os
import re


def getShebangFromSource(source_code):
    if source_code.startswith("#!"):
        shebang = re.match(r"^#!\s*(.*?)\n", source_code)

        if shebang is not None:
            shebang = shebang.group(0).rstrip('\n')
    else:
        shebang = None

    return shebang


def getShebangFromFile(filename):
    return getShebangFromSource(open(filename).readline())


def parseShebang(shebang):
    parts = shebang.split()

    if os.path.basename(parts[0]) == "env":
        # This attempts to handle env with arguments and options.
        del parts[0]

        while parts[0].startswith('-'):
            del parts[0]

        while '=' in parts[0]:
            del parts[0]

    return parts[0][2:].lstrip(), parts[1:]
