#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Utils to work with shebang lines.

"""

import os
import re


def getShebangFromSource(source_code):
    """Given source code, extract the shebang (#!) part.

    Notes:
        This function is less relevant on Windows, because it will not use
        this method of determining the execution. Still scripts aimed at
        multiple platforms will contain it and it can be used to e.g. guess
        the Python version expected, if it is a Python script at all.

        There are variants of the function that will work on filenames instead.
    Args:
        source_code: The source code as a unicode string
    Returns:
        The binary and arguments that the kernel will use (Linux and compatible).
    """

    if source_code.startswith("#!"):
        shebang = re.match(r"^#!\s*(.*?)\n", source_code)

        if shebang is not None:
            shebang = shebang.group(0).rstrip("\n")
    else:
        shebang = None

    return shebang


def getShebangFromFile(filename):
    """Given a filename, extract the shebang (#!) part from it.

    Notes:
        This function is less relevant on Windows, because it will not use
        this method of determining the execution. Still scripts aimed at
        multiple platforms will contain it and it can be used to e.g. guess
        the Python version expected, if it is a Python script at all.

        There are variants of the function that will work on file content
        instead.
    Args:
        filename: The filename to get the shebang of
    Returns:
        The binary that the kernel will use (Linux and compatible).
    """

    with open(filename, "rb") as f:
        source_code = f.readline()

        if str is not bytes:
            try:
                source_code = source_code.decode("utf8")
            except UnicodeDecodeError:
                source_code = ""

        return getShebangFromSource(source_code)


def parseShebang(shebang):
    """Given a concrete shebang value, it will extract the binary used.

    Notes:
        This function is less relevant on Windows, because it will not use
        this method of determining the execution.

        This handles that many times people use `env` binary to search the
        PATH for an actual binary, e.g. `/usr/bin/env python3.7` where we
        would care most about the `python3.7` part and want to see through
        the `env` usage.
    Args:
        shebang: The shebang extracted with one of the methods to do so.
    Returns:
        The binary the kernel will use (Linux and compatible).
    """

    parts = shebang.split()

    if os.path.basename(parts[0]) == "env":
        # This attempts to handle env with arguments and options.
        del parts[0]

        while parts[0].startswith("-"):
            del parts[0]

        while "=" in parts[0]:
            del parts[0]

    return parts[0][2:].lstrip(), parts[1:]


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
