#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Access to standard library distinction.

For code to be in the standard library means that it's not written by the
user for sure. We treat code differently based on that information, by e.g.
including as byte code.

To determine if a module from the standard library, we can abuse the attribute
"__file__" of the "os" module like it's done in "isStandardLibraryPath" of this
module.
"""

import os

from nuitka.Options import shallUseStaticLibPython
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import getFileContents, isFilenameBelowPath
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Utils import (
    isNetBSD,
    isPosixWindows,
    isWin32OrPosixWindows,
    isWin32Windows,
)


def getStandardLibraryPaths():
    """Get the standard library paths."""

    # Using the function object to cache its result, avoiding global variable
    # usage.
    if not hasattr(getStandardLibraryPaths, "result"):
        os_filename = os.__file__
        if os_filename.endswith(".pyc"):
            os_filename = os_filename[:-1]

        os_path = os.path.normcase(os.path.dirname(os_filename))

        stdlib_paths = set([os_path])

        # Happens for virtualenv situation, some modules will come from the link
        # this points to.
        if os.path.islink(os_filename):
            os_filename = os.readlink(os_filename)
            stdlib_paths.add(os.path.normcase(os.path.dirname(os_filename)))

        # Another possibility is "orig-prefix.txt" file near the os.py, which
        # points to the original install.
        orig_prefix_filename = os.path.join(os_path, "orig-prefix.txt")

        if os.path.isfile(orig_prefix_filename):
            # Scan upwards, until we find a "bin" folder, with "activate" to
            # locate the structural path to be added. We do not know for sure
            # if there is a sub-directory under "lib" to use or not. So we try
            # to detect it.
            search = os_path
            lib_part = ""

            while os.path.splitdrive(search)[1] not in (os.path.sep, ""):
                if os.path.isfile(
                    os.path.join(search, "bin/activate")
                ) or os.path.isfile(os.path.join(search, "scripts/activate")):
                    break

                lib_part = os.path.join(os.path.basename(search), lib_part)

                search = os.path.dirname(search)

            assert search and lib_part

            stdlib_paths.add(
                os.path.normcase(
                    os.path.join(getFileContents(orig_prefix_filename), lib_part)
                )
            )

        # And yet another possibility, for macOS Homebrew created virtualenv
        # at least is a link ".Python", which points to the original install.
        python_link_filename = os.path.join(os_path, "..", ".Python")
        if os.path.islink(python_link_filename):
            stdlib_paths.add(
                os.path.normcase(os.path.join(os.readlink(python_link_filename), "lib"))
            )

        for stdlib_path in set(stdlib_paths):
            candidate = os.path.join(stdlib_path, "lib-tk")

            if os.path.isdir(candidate):
                stdlib_paths.add(candidate)

        if isWin32OrPosixWindows() and not shallUseStaticLibPython():
            import _ctypes

            stdlib_paths.add(os.path.dirname(_ctypes.__file__))

        getStandardLibraryPaths.result = [
            os.path.normcase(os.path.normpath(stdlib_path))
            for stdlib_path in stdlib_paths
        ]

    return getStandardLibraryPaths.result


def isStandardLibraryPath(filename):
    """Check if a path is in the standard library."""

    filename = os.path.normcase(os.path.normpath(filename))

    # In virtualenv, the "site.py" lives in a place that suggests it is not in
    # standard library, although it is.
    if os.path.basename(filename) == "site.py":
        return True

    # These never are in standard library paths.
    if "dist-packages" in filename or "site-packages" in filename:
        return False

    for candidate in getStandardLibraryPaths():
        if isFilenameBelowPath(path=candidate, filename=filename):
            return True

    return False


# Some modules we want to exclude entirely.
_excluded_stdlib_modules = ["__main__.py", "__init__.py", "antigravity.py"]

if not isWin32Windows():
    # On posix systems, and posix Python variants on Windows, this won't
    # work.
    _excluded_stdlib_modules.append("wintypes.py")
    _excluded_stdlib_modules.append("cp65001.py")


def scanStandardLibraryPath(stdlib_dir):
    # There is a lot of filtering here, done in branches, so there is many of
    # them, but that's acceptable, pylint: disable=too-many-branches,too-many-statements

    for root, dirs, filenames in os.walk(stdlib_dir):
        import_path = root[len(stdlib_dir) :].strip("/\\")
        import_path = import_path.replace("\\", ".").replace("/", ".")

        if import_path == "":
            if "site-packages" in dirs:
                dirs.remove("site-packages")
            if "dist-packages" in dirs:
                dirs.remove("dist-packages")
            if "test" in dirs:
                dirs.remove("test")
            if "turtledemo" in dirs:
                dirs.remove("turtledemo")

            if "ensurepip" in filenames:
                filenames.remove("ensurepip")
            if "ensurepip" in dirs:
                dirs.remove("ensurepip")

            # Ignore "lib-dynload" and "lib-tk" and alike.
            dirs[:] = [
                dirname
                for dirname in dirs
                if not dirname.startswith("lib-")
                if dirname != "Tools"
                if not dirname.startswith("plat-")
            ]

        if import_path in (
            "tkinter",
            "Tkinter",
            "importlib",
            "ctypes",
            "unittest",
            "sqlite3",
            "distutils",
            "email",
            "bsddb",
        ):
            if "test" in dirs:
                dirs.remove("test")

        if import_path == "distutils.command":
            # Misbehaving and crashing while importing the world.
            if "bdist_conda.py" in filenames:
                filenames.remove("bdist_conda.py")

        if import_path in ("lib2to3", "json", "distutils"):
            if "tests" in dirs:
                dirs.remove("tests")

        if import_path == "asyncio":
            if "test_utils.py" in filenames:
                filenames.remove("test_utils.py")

        if python_version >= 0x340 and isWin32Windows():
            if import_path == "multiprocessing":
                filenames.remove("popen_fork.py")
                filenames.remove("popen_forkserver.py")
                filenames.remove("popen_spawn_posix.py")

        if python_version >= 0x300 and isPosixWindows():
            if import_path == "curses":
                filenames.remove("has_key.py")

        if isNetBSD():
            if import_path == "xml.sax":
                filenames.remove("expatreader.py")

        for filename in filenames:
            if filename.endswith(".py") and filename not in _excluded_stdlib_modules:
                module_name = filename[:-3]

                if import_path == "":
                    yield ModuleName(module_name)
                else:
                    yield ModuleName(import_path + "." + module_name)

        if python_version >= 0x300:
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")

        for dirname in dirs:
            if import_path == "":
                yield ModuleName(dirname)
            else:
                yield ModuleName(import_path + "." + dirname)


_stdlib_no_auto_inclusion_list = (
    # Avoid this to be included, implicit usages will be rare, but it triggers
    # the Nuitka plugin "multiprocessing" that is always enabled.
    "multiprocessing",
    "_multiprocessing",
    # Implicit usages of these will be rare, but it can have that costly extension module
    "curses",
    "_curses",
    "ctypes",
    "_ctypes",
    "_curses_panel",
    "sqlite3",
    "_sqlite3",
    "dbm",
    "_dbm",
    "bdb",
    "xml",
    "_elementtree",
    "queue",
    "_queue",
    "uuid",
    "_uuid",
    "hashlib",
    "_hashlib",
    "secrets",
    "hmac",
    "fractions",
    "decimal",
    "_pydecimal",
    "_decimal",
    "statistics",
    "lzma",
    "_lzma",
    "bz2",
    "_bz2",
    "logging",
    "subprocess",
    "socket",
    "selectors",
    "select",
    "_socket",
    "ssl",
    "_ssl",
    "pyexpat",
    # This one can have license issues attached, so avoid it.
    "readline",
    # Avoid tests and doc stuff, profiling, etc. if not used.
    "unittest",
    "pydoc",
    "pydoc_data",
    "profile",
    "cProfile",
    "optparse",
    "pdb",
    "site",
    "sitecustomize",
    "runpy",
    "lib2to3",
    "doctest",
    "email",
    "tabnanny",
    "argparse",
    "telnetlib",
    "smtplib",
    "smtpd",
    "nntplib",
    "http",
    "xmlrpc",
    "urllib",
    "select",
    "wsgiref",
    "sunau",
    "this",
    # Distribution and bytecode related stuff
    "plistlib",
    "distutils",
    "compileall",
    "venv",
    "py_compile",
    "msilib",
    # tzdata is not always needed
    "zoneinfo",
    # tkinter under all its names
    "Tkinter",
    "tkinter",
    "_tkinter",
    # lib-tk from Python2
    "Tix",
    "FixTk",
    "ScrolledText",
    "turtle",
    "antigravity",
    "Dialog",
    "Tkdnd",
    "tkMessageBox",
    "tkSimpleDialog",
    "Tkinter",
    "tkFileDialog",
    "Canvas",
    "tkCommonDialog",
    "Tkconstants",
    "FileDialog",
    "SimpleDialog",
    "ttk",
    "tkFont",
    "tkColorChooser",
    "idlelib",
    # test code in standard modules
    "asyncio.test_utils",
    # strange OS specific extensions
    "_distutils_system_mod",
    # async libraries
    "concurrent",
    "asyncio",
    "asyncore",
    "asynchat",
)

if not isWin32Windows():
    _stdlib_no_auto_inclusion_list += ("ntpath",)


def isStandardLibraryNoAutoInclusionModule(module_name):
    return module_name.hasOneOfNamespaces(*_stdlib_no_auto_inclusion_list)
