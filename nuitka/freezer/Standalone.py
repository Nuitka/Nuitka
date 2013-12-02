#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Pack and copy files for standalone mode.

This is in heavy flux now, cannot be expected to work or make sense on all
the platforms.
"""

import os
import subprocess
import sys
from logging import debug
import marshal
import re

from nuitka import Utils
from nuitka.codegen.ConstantCodes import needsPickleInit


python_dll_dir_name = "_python"


def loadCodeObjectData(precompiled_path):
    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    return open(precompiled_path, "rb").read()[8:]


def detectEarlyImports():
    # When we are using pickle internally (for some hard constant cases we do),
    # we need to make sure it will be available as well.
    if needsPickleInit():
        command = "import {pickle};".format(
            pickle = "pickle" if Utils.python_version >= 300 else "cPickle"
        )
    else:
        command = ""

    if Utils.python_version >= 300:
        command += "import inspect;"

    if Utils.python_version >= 300:
        command += r'import sys; print("\n".join(sorted("import " + module.__name__ + " # sourcefile " + module.__file__ for module in sys.modules.values() if hasattr(module, "__file__") and module.__file__ != "<frozen>")), file = sys.stderr)'  # do not read it, pylint: disable=C0301  lint:ok

    process = subprocess.Popen(
        args   = [sys.executable, "-s", "-S", "-v", "-c", command],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    _stdout, stderr = process.communicate()

    result = []

    debug("Detecting early imports:")

    # bug of PyLint, pylint: disable=E1103
    for line in stderr.replace(b"\r", b"").split(b"\n"):
        if line.startswith(b"import "):
            # print(line)

            parts = line.split(b" # ", 2)

            module_name = parts[0].split(b" ", 2)[1]
            origin = parts[1].split()[0]

            if origin == b"precompiled":
                # This is a ".pyc" file that was imported, even before we have a
                # chance to do anything, we need to preserve it.
                filename = parts[1][len(b"precompiled from "):]

                debug(
                    "Freezing module '%s' (from '%s').",
                    module_name,
                    filename
                )

                result.append(
                    (
                        module_name,
                        loadCodeObjectData( filename ),
                        b"__init__" in filename
                    )
                )

            elif origin == b"sourcefile":
                filename = parts[1][len(b"sourcefile "):]

                debug(
                    "Freezing module '%s' (from '%s').",
                    module_name,
                    filename
                )

                source_code = open(filename,"rb").read()

                if Utils.python_version >= 300:
                    source_code = source_code.decode( "utf-8" )

                result.append(
                    (
                        module_name,
                        marshal.dumps(
                            compile(source_code, filename, "exec")
                        ),
                        Utils.basename(filename) == b"__init__.py"
                    )
                )

    debug("Finished detecting early imports.")

    return result

def _detectPythonDLLs( binary_filename ):
    result = set()

    if os.name == "posix" and os.uname()[0] == "Linux":
        # Ask "ldd" about the libraries being used by the created binary, these
        # are the ones that interest us.
        process = subprocess.Popen(
            args   = [ "ldd", binary_filename ],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        stdout, _stderr = process.communicate()

        for line in stdout.split( b"\n" ):
            if not line:
                continue

            if b"=>" not in line:
                continue

            part = line.split(b" => ", 2)[1]
            filename = part[:part.rfind(b"(")-1]

            if Utils.python_version >= 300:
                filename = filename.decode("utf-8")

            result.add(filename)
    elif os.name == "nt":
        import ctypes
        from ctypes import windll
        from ctypes.wintypes import HANDLE, LPCSTR, DWORD
        dll = getattr( windll, "python%s%s" % ( sys.version_info[:2] ) )
        getname = windll.kernel32.GetModuleFileNameA
        getname.argtypes = ( HANDLE, LPCSTR, DWORD )
        getname.restype = DWORD
        result = ctypes.create_string_buffer( 1024 )
        size = getname( dll._handle, result, 1024 )
        path = result.value[ :size ]

        if Utils.python_version >= 300:
            path = path.decode("utf-8")

        result.add(path)
    else:
        # Support your platform above.
        assert False

    return result


def detectPythonDLLs( standalone_entry_points ):
    result = set()

    for binary_filename in standalone_entry_points:
        result.update(
            _detectPythonDLLs(binary_filename)
        )

    return result
