#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Detect imports made for code by Python.

In the freezer, this is a step done to detect the technically needed modules to
initialize the CPython interpreter.

"""

import os
import pkgutil
import sys

from nuitka.importing.StandardLibrary import (
    getStandardLibraryPaths,
    isStandardLibraryNoAutoInclusionModule,
    isStandardLibraryPath,
    scanStandardLibraryPath,
)
from nuitka.Options import isStandaloneMode
from nuitka.PythonVersions import python_version
from nuitka.Tracing import general, printError
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import areSamePaths
from nuitka.utils.ModuleNames import ModuleName


def _detectImports(command):
    # This is pretty complicated stuff, with variants to deal with.
    # pylint: disable=too-many-branches,too-many-statements

    # Print statements for stuff to show, the modules loaded.
    if python_version >= 0x300:
        command += """
print("\\n".join(sorted(
    "import %s # sourcefile %s" % (module.__name__, module.__file__)
    for module in sys.modules.values()
    if getattr(module, "__file__", None) not in (None, "<frozen>"
))), file = sys.stderr)"""

    reduced_path = [
        path_element
        for path_element in sys.path
        if not areSamePaths(path_element, ".")
        if not areSamePaths(
            path_element, os.path.dirname(sys.modules["__main__"].__file__)
        )
    ]

    # Make sure the right import path (the one Nuitka binary is running with)
    # is used.
    command = (
        "import sys; sys.path = %s; sys.real_prefix = sys.prefix;" % repr(reduced_path)
    ) + command

    if str is not bytes:
        command = command.encode("utf8")

    _stdout, stderr, exit_code = executeProcess(
        command=(
            sys.executable,
            "-s",
            "-S",
            "-v",
            "-c",
            "import sys;exec(sys.stdin.read())",
        ),
        stdin=command,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )

    assert type(stderr) is bytes

    # Don't let errors here go unnoticed.
    if exit_code != 0:
        # An error by the user pressing CTRL-C should not lead to the below output.
        if b"KeyboardInterrupt" in stderr:
            general.sysexit("Pressed CTRL-C while detecting early imports.")

        general.warning("There is a problem with detecting imports, CPython said:")
        for line in stderr.split(b"\n"):
            printError(line)
        general.sysexit("Error, please report the issue with above output.")

    detections = []

    for line in stderr.replace(b"\r", b"").split(b"\n"):
        if line.startswith(b"import "):
            parts = line.split(b" # ", 2)

            module_name = parts[0].split(b" ", 2)[1].strip(b"'")
            origin = parts[1].split()[0]

            if python_version >= 0x300:
                module_name = module_name.decode("utf8")

            module_name = ModuleName(module_name)

            if origin == b"precompiled":
                # This is a ".pyc" file that was imported, even before we have a
                # chance to do anything, we need to preserve it.
                filename = parts[1][len(b"precompiled from ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append((module_name, 3, "precompiled", filename))
            elif origin == b"from" and python_version < 0x300:
                filename = parts[1][len(b"from ") :]
                if str is not bytes:  # For consistency, and maybe later reuse
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                if filename.endswith(".py"):
                    detections.append((module_name, 2, "sourcefile", filename))
                else:
                    assert False
            elif origin == b"sourcefile":
                filename = parts[1][len(b"sourcefile ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                # Python3 started lying in "__name__" for the "_collections_abc" module
                # as well, which then is interpreted wrongly, this affects at least 3.9
                if os.path.basename(filename) in (
                    "_collections_abc.py",
                    "_collections_abc.pyc",
                ):
                    if python_version >= 0x3D0:
                        detections.append((module_name, 2, "sourcefile", filename))

                    module_name = ModuleName("_collections_abc")

                if filename.endswith(".py"):
                    detections.append((module_name, 2, "sourcefile", filename))
                elif filename.endswith(".pyc"):
                    detections.append((module_name, 3, "precompiled", filename))
                elif not filename.endswith("<frozen>"):
                    # Python3 started lying in "__name__" for the "_decimal"
                    # calls itself "decimal", which then is wrong and also
                    # clashes with "decimal" proper
                    if python_version >= 0x300 and module_name == "decimal":
                        module_name = ModuleName("_decimal")

                    detections.append((module_name, 2, "extension", filename))
            elif origin == b"dynamically":
                # Shared library in early load, happens on RPM based systems and
                # or self compiled Python installations.
                filename = parts[1][len(b"dynamically loaded from ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append((module_name, 1, "extension", filename))

    module_names = set()

    for module_name, _priority, kind, filename in sorted(detections):
        if isStandardLibraryNoAutoInclusionModule(module_name):
            continue

        if kind == "extension":
            # Extension modules are not tracked outside of standalone
            # mode.
            if not isStandaloneMode():
                continue

            # That is not a shared library, but looks like one.
            if module_name == "__main__":
                continue

            module_names.add(module_name)
        elif kind == "precompiled":
            module_names.add(module_name)
        elif kind == "sourcefile":
            module_names.add(module_name)
        else:
            assert False, kind

    return module_names


def _detectEarlyImports():
    encoding_names = [
        m[1] for m in pkgutil.iter_modules(sys.modules["encodings"].__path__)
    ]

    if os.name != "nt":
        # On posix systems, and posix Python variants on Windows, these won't
        # work and fail to import.
        for encoding_name in ("mbcs", "cp65001", "oem"):
            if encoding_name in encoding_names:
                encoding_names.remove(encoding_name)

    # Not for startup.
    for non_locale_encoding in (
        "bz2_codec",
        "idna",
        "base64_codec",
        "hex_codec",
        "rot_13",
        "punycode",
    ):
        if non_locale_encoding in encoding_names:
            encoding_names.remove(non_locale_encoding)

    import_code = ";".join(
        "import encodings.%s" % encoding_name
        for encoding_name in sorted(encoding_names)
    )

    import_code += ";import locale;"

    # For Python3 we patch inspect without knowing if it is used.
    if python_version >= 0x300:
        import_code += "import inspect;import importlib._bootstrap"

    return _detectImports(command=import_code)


_early_modules_names = None


def detectEarlyImports():
    if not isStandaloneMode():
        return ()

    global _early_modules_names  # singleton, pylint: disable=global-statement

    if _early_modules_names is None:
        _early_modules_names = tuple(sorted(_detectEarlyImports()))

    return _early_modules_names


def _detectStdlibAutoInclusionModules():
    if not isStandaloneMode():
        return ()

    stdlib_modules = set()

    # Scan the standard library paths (multiple in case of virtualenv).
    for stdlib_dir in getStandardLibraryPaths():
        for module_name in scanStandardLibraryPath(stdlib_dir):
            if not isStandardLibraryNoAutoInclusionModule(module_name):
                stdlib_modules.add(module_name)

    # Put here ones that should be imported first.
    first_ones = ("Tkinter",)

    # We have to fight zombie modules in this, some things, e.g. Tkinter
    # on newer Python 2.7, comes back after failure without a second error
    # being raised, leading to other issues. So we fight it after each
    # module that was tried, and prevent re-try by adding a meta path
    # based loader that will never load it again, and remove it from the
    # "sys.modules" over and over, once it sneaks back. The root cause is
    # that extension modules sometimes only raise an error when first
    # imported, not the second time around.
    # Otherwise this just makes imports of everything so we can see where
    # it comes from and what it requires.

    import_code = """
imports = %r

failed = set()

class ImportBlocker(object):
    def find_module(self, fullname, path = None):
        if fullname in failed:
            return self

        return None

    def load_module(self, name):
        raise ImportError("%%s has failed before" %% name)

sys.meta_path.insert(0, ImportBlocker())

for imp in imports:
    try:
        __import__(imp)
    except (ImportError, SyntaxError):
        failed.add(imp)
    except ValueError as e:
        if "cannot contain null bytes" in e.args[0]:
            failed.add(imp)
        else:
            sys.stderr.write("PROBLEM with '%%s'\\n" %% imp)
            raise
    except Exception:
        sys.stderr.write("PROBLEM with '%%s'\\n" %% imp)
        raise

    for fail in failed:
        if fail in sys.modules:
            del sys.modules[fail]
""" % (
        tuple(
            module_name.asString()
            for module_name in sorted(
                stdlib_modules, key=lambda name: (name not in first_ones, name)
            )
        ),
    )

    return _detectImports(command=import_code)


_stdlib_modules_names = None


def detectStdlibAutoInclusionModules():
    if not isStandaloneMode():
        return ()

    global _stdlib_modules_names  # singleton, pylint: disable=global-statement

    if _stdlib_modules_names is None:
        _stdlib_modules_names = _detectStdlibAutoInclusionModules()

        for module_name in detectEarlyImports():
            _stdlib_modules_names.discard(module_name)

        _stdlib_modules_names = tuple(sorted(_stdlib_modules_names))

    return _stdlib_modules_names


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
