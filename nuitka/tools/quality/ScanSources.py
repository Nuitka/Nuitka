#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Many tools work on Nuitka sources and need to find the files."""

import os

from nuitka.utils.Shebang import getShebangFromFile

_default_ignore_list = ("inline_copy", "tblib", "__pycache__")


def _addFromDirectory(path, suffixes, ignore_list):
    """Recursively find files in a directory with specific suffixes.

    Args:
        path: str - directory path to start from
        suffixes: tuple - file suffixes to match
        ignore_list: tuple - list of filenames to ignore
    """
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()

        # Remove things we never care about.
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in _default_ignore_list
            if not dirname.endswith((".build", ".dist", ".egg-info"))
            if not dirname.startswith(("CPython", "venv_"))
        ]

        filenames.sort()

        for filename in filenames:
            if filename in ignore_list:
                continue

            fullpath = os.path.join(dirpath, filename)

            # Ignore links
            if os.path.islink(fullpath):
                continue

            # Skip temporary files from flymake mode of Emacs, spell-checker: ignore flymake
            if filename.endswith("_flymake.py"):
                continue
            # Skip temporary files from unsaved files of Emacs.
            if filename.startswith(".#"):
                continue
            # Skip bytecode files
            if filename.endswith((".pyc", ".pyo")):
                continue
            # Skip executables
            if filename.endswith((".exe", ".bin")):
                continue

            # Python files only might include files with a shebang that points
            # to Python.
            if ".py" in suffixes and not filename.endswith(suffixes):
                shebang = getShebangFromFile(fullpath)

                if shebang is None or "python" not in shebang:
                    continue

            yield fullpath


def scanTargets(positional_args, suffixes, ignore_list=()):
    """Scan list of paths for files with specific suffixes.

    Args:
        positional_args: list - paths to scan (files or directories)
        suffixes: tuple - file suffixes to match
        ignore_list: tuple - list of filenames to ignore
    """
    for positional_arg in positional_args:
        positional_arg = os.path.normpath(positional_arg)

        if os.path.isdir(positional_arg):
            for value in _addFromDirectory(positional_arg, suffixes, ignore_list):
                yield value
        else:
            yield positional_arg


def isPythonFile(filename, effective_filename=None):
    """Check if a file is a Python file.

    Checks extension and shebang for files without extension.

    Args:
        filename: str - path to the file
        effective_filename: str - effective filename to use for extension check
    """
    if effective_filename is None:
        effective_filename = filename

    if effective_filename.lower().endswith((".py", ".pyw", ".scons")):
        return True
    elif os.path.isdir(filename):
        return False
    else:
        shebang = getShebangFromFile(filename)

        if shebang is not None:
            shebang = shebang[2:].lstrip()
            if shebang.startswith("/usr/bin/env"):
                shebang = shebang[12:].lstrip()

            if shebang.startswith("python"):
                return True

    return False


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
