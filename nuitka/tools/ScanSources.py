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
""" Many tools work on Nuitka sources and need to find the files.

"""

import os


def addFromDirectory(path, blacklist):
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()

        if "inline_copy" in dirnames:
            dirnames.remove("inline_copy")

        if "__pycache__" in dirnames:
            dirnames.remove("__pycache__")

        filenames.sort()

        for filename in filenames:
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
            if filename.endswith(".pyc"):
                continue

            # Python files only. TODO: Provided this from the outside.
            if not filename.endswith(".py"):
                line = open(fullpath).readline()
                if not line.startswith("#!") or "python" not in line:
                    continue

            if filename in blacklist:
                continue

            yield fullpath


def scanTargets(positional_args, blacklist = ()):
    for positional_arg in positional_args:
        if os.path.isdir(positional_arg):
            for value in addFromDirectory(positional_arg, blacklist):
                yield value
        else:
            yield positional_arg
