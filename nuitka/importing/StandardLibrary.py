#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Access to standard library distinction.

For code to be in the standard library means that it's not written by the
user for sure. We treat code differently based on that information, by e.g.
including as byte code.

To determine if a module from the standard library, we can abuse the attribute
"__file__" of the "os" module like it's done in "isStandardLibraryPath" of this
module.
"""

import os

from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import getFileContents, isFilenameBelowPath
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Utils import (
    isMacOS,
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

        if isWin32OrPosixWindows():
            from nuitka.Options import shallUseStaticLibPython

            if not shallUseStaticLibPython():
                import _ctypes

                stdlib_paths.add(os.path.dirname(_ctypes.__file__))

        getStandardLibraryPaths.result = [
            os.path.normcase(os.path.normpath(stdlib_path))
            for stdlib_path in stdlib_paths
        ]

    return getStandardLibraryPaths.result


def _isStandardLibraryPath(filename):
    # In virtualenv, the "site.py" lives in a place that suggests it is not in
    # standard library, although it is.
    if os.path.basename(filename) == "site.py":
        return True

    # These never are in standard library paths.
    if (
        "dist-packages" in filename
        or "site-packages" in filename
        or "vendor-packages" in filename
    ):
        return False

    for candidate in getStandardLibraryPaths():
        if isFilenameBelowPath(path=candidate, filename=filename):
            return True

    return False


_is_standard_library_path_cache = {}


def isStandardLibraryPath(filename):
    """Check if a path is in the standard library."""

    filename = os.path.normcase(os.path.normpath(filename))

    if filename not in _is_standard_library_path_cache:
        _is_standard_library_path_cache[filename] = _isStandardLibraryPath(filename)

    return _is_standard_library_path_cache[filename]


def scanStandardLibraryPath(stdlib_dir):
    # There is a lot of filtering here, done in branches, so there is many of
    # them, but that's acceptable, pylint: disable=too-many-branches

    for root, dirs, filenames in os.walk(stdlib_dir):
        import_path = root[len(stdlib_dir) :].strip("/\\")
        import_path = import_path.replace("\\", ".").replace("/", ".")

        def _removeFilenamesIfPresent(*remove_filenames):
            # pylint: intended for loop usage, pylint: disable=cell-var-from-loop
            for remove_filename in remove_filenames:
                if remove_filename in filenames:
                    filenames.remove(remove_filename)

        def _removeDirsIfPresent(*remove_dirs):
            # pylint: intended for loop usage, pylint: disable=cell-var-from-loop
            for remove_dir in remove_dirs:
                if remove_dir in dirs:
                    dirs.remove(remove_dir)

        _removeDirsIfPresent("__pycache__")

        # Ignore ".idea", ".git" and similar folders, they are not modules
        dirs[:] = [dirname for dirname in dirs if not dirname.startswith(".")]

        if import_path == "":
            # Ignore "lib-dynload" and "lib-tk" and alike, spell-checker: ignore dynload
            dirs[:] = [
                dirname
                for dirname in dirs
                if not dirname.startswith("lib-")
                if not dirname.startswith("plat-")
            ]

            _removeDirsIfPresent(
                "site-packages",
                "dist-packages",
                "vendor-packages",
                "test",
                "ensurepip",
                "turtledemo",
                "Tools",
            )
            _removeFilenamesIfPresent("ensurepip")

            if not isMacOS():
                _removeFilenamesIfPresent("_ios_support.py")

        # Ignore tests from selected packages, spell-checker: ignore bsddb
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
            _removeDirsIfPresent("test")

        if import_path in ("lib2to3", "json", "distutils"):
            _removeDirsIfPresent("tests")

        if import_path == "distutils.command":
            # Misbehaving and crashing while importing the world.
            _removeFilenamesIfPresent("bdist_conda.py")

        if import_path == "asyncio":
            _removeFilenamesIfPresent("test_utils.py")

        if python_version >= 0x300 and isPosixWindows():
            if import_path == "multiprocessing":
                _removeFilenamesIfPresent(
                    "popen_fork.py", "popen_forkserver.py", "popen_spawn_posix.py"
                )

            if import_path == "curses":
                _removeFilenamesIfPresent("has_key.py")

        if isNetBSD():
            if import_path == "xml.sax":
                _removeFilenamesIfPresent("expatreader.py")

        _removeFilenamesIfPresent("__main__.py", "__init__.py", "antigravity.py")

        if not isWin32Windows():
            # On POSIX systems, and on POSIX Python variants on Windows, this
            # won't work.
            _removeFilenamesIfPresent("wintypes.py", "cp65001.py")

        for filename in filenames:
            if filename.endswith(".py"):
                module_name = filename[:-3]

                if import_path == "":
                    yield ModuleName(module_name)
                else:
                    yield ModuleName(import_path + "." + module_name)

        for dirname in dirs:
            if import_path == "":
                yield ModuleName(dirname)
            else:
                yield ModuleName(import_path + "." + dirname)


_stdlib_no_auto_inclusion_list = (
    # Avoid this to be included, implicit usages will be rare, but it triggers
    # the Nuitka plugin "multiprocessing" that is always enabled.
    # spell-checker: ignore _pydecimal,_posixsubprocess,pyexpat,sitecustomize
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
    "shelve",
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
    "csv",
    "_csv",
    "lzma",
    "_lzma",
    "bz2",
    "_bz2",
    "logging",
    "tempfile",
    "subprocess",
    "_posixsubprocess",
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
    # Optional dependency of json need not by collect by itself, but usage will
    # go through "json.encoder/json.decoder/json.scanner" of course.
    "_json",
    # Optional dependency of "bisect" need not by collect by itself, but usage will
    # go through "bisect" of course.
    "_bisect",
    # Optional dependency of "heapq" need not by collect by itself, but usage will
    # go through "heapq" of course.
    "_heapq",
    # Dependency of crypt, that may not be used, requiring this to be explicit.
    "_crypt",
    # Dependency of contextvars, that may not be used, requiring this to be explicit.
    "_contextvars",
    # Dependency of random, that may not be used, requiring this to be explicit.
    "random",
    # Avoid this one if not built-in, since it's an extension module.
    "array",
    # Runners for programs
    "json.tool",
    "zipapp",
    "tabnanny",
    # Packages that will be imported rarely by extension modules
    "email",
    "mailbox",
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
    "aifc",
    "wave",
    "audioop",
    "getpass",
    "grp",
    "pty",
    "tty",
    "termios",
    "this",
    "textwrap",
    # Distribution and bytecode related stuff
    "plistlib",
    "distutils",
    "compileall",
    "venv",
    "py_compile",
    "msilib",
    "_opcode",
    # time zone data is not always needed
    "zoneinfo",
    # tkinter under all its names
    "Tkinter",
    "tkinter",
    "_tkinter",
    # lib-tk from Python2, spell-checker: ignore Tkdnd,Tkconstants
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
