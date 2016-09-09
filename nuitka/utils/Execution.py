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
""" Program execution related stuff.

Basically a layer for os, subprocess, shutil to come together. It can find
binaries (needed for exec) and run them capturing outputs.
"""


import os
import subprocess
import sys

from .Utils import getOS


def callExec(args):
    """ Do exec in a portable way preserving exit code.

        On Windows, unfortunately there is no real exec, so we have to spawn
        a new process instead.
    """

    # On Windows os.execl does not work properly
    if getOS() != "Windows":
        # The star arguments is the API of execl
        os.execl(*args)
    else:
        args = list(args)
        del args[1]

        try:
            sys.exit(
                subprocess.call(args)
            )
        except KeyboardInterrupt:
            # There was a more relevant stack trace already, so abort this
            # right here, pylint: disable=W0212
            os._exit(2)


def getExecutablePath(filename):
    """ Find an execute in PATH environment. """

    # Append ".exe" suffix  on Windows if not already present.
    if getOS() == "Windows" and not filename.lower().endswith(".exe"):
        filename += ".exe"

    # Search in PATH environment.
    search_path = os.environ["PATH"]

    # Now check in each path element, much like the shell will.
    path_elements = search_path.split(os.pathsep)

    for path_element in path_elements:
        path_element = path_element.strip('"')

        full = os.path.join(path_element, filename)

        if os.path.exists(full):
            return full

    return None
