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
""" Many tools work on Nuitka sources and need to find the files.

"""

import os

from nuitka.utils.Shebang import getShebangFromFile

_default_ignore_list = ("inline_copy", "tblib", "__pycache__")


def _addFromDirectory(path, suffixes, ignore_list):
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()

        for entry in _default_ignore_list:
            if entry in dirnames:
                dirnames.remove(entry)

        filenames.sort()

        for filename in filenames:
            if filename in ignore_list:
                continue

            fullpath = os.path.join(dirpath, filename)

            # Ignore links
            if os.path.islink(fullpath):
                continue

            # Skip temporary files from flymake mode of Emacs.
            if filename.endswith("_flymake.py"):
                continue
            # Skip temporary files from unsaved files of Emacs.
            if filename.startswith(".#"):
                continue
            # Skip bytecode files
            if filename.endswith((".pyc", ".pyo")):
                continue

            # Python files only.
            if ".py" in suffixes and not filename.endswith(suffixes):
                shebang = getShebangFromFile(fullpath)

                if shebang is None or "python" not in shebang:
                    continue

            yield fullpath


def scanTargets(positional_args, suffixes, ignore_list=()):
    for positional_arg in positional_args:
        positional_arg = os.path.normpath(positional_arg)

        if os.path.isdir(positional_arg):
            for value in _addFromDirectory(positional_arg, suffixes, ignore_list):
                yield value
        else:
            yield positional_arg


def isPythonFile(filename, effective_filename=None):
    if effective_filename is None:
        effective_filename = filename

    if os.path.isdir(filename):
        return False

    if effective_filename.endswith((".py", ".pyw", ".scons")):
        return True
    else:
        shebang = getShebangFromFile(filename)

        if shebang is not None:
            shebang = shebang[2:].lstrip()
            if shebang.startswith("/usr/bin/env"):
                shebang = shebang[12:].lstrip()

            if shebang.startswith("python"):
                return True

    return False
