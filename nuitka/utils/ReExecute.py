#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""Ability to restart Nuitka, needed for removing site module effects and using Python PGO after compile.

Note: This avoids imports at all costs, such that initial startup doesn't do more
than necessary.
"""

import os
import sys


def callExecProcess(args):
    """Do exec in a portable way preserving exit code.

    On Windows, unfortunately there is no real exec, so we have to spawn
    a new process instead.
    """

    # On Windows os.execl does not work properly
    if os.name == "nt":
        import subprocess

        args = list(args)
        del args[1]

        try:
            # Context manager is not available on all Python versions, pylint: disable=consider-using-with
            process = subprocess.Popen(args=args)
            process.communicate()
            # No point in cleaning up, pylint: disable=protected-access
            try:
                os._exit(process.returncode)
            except OverflowError:
                # Seems negative values go wrong otherwise,
                # see https://bugs.python.org/issue28474
                os._exit(process.returncode - 2 ** 32)
        except KeyboardInterrupt:
            # There was a more relevant stack trace already, so abort this
            # right here, pylint: disable=protected-access
            os._exit(2)
    else:
        # The star arguments is the API of execl
        os.execl(*args)


def reExecuteNuitka(pgo_filename):
    # Execute with full path as the process name, so it can find itself and its
    # libraries.
    args = [sys.executable, sys.executable]

    if sys.version_info >= (3, 7) and sys.flags.utf8_mode:
        args += ["-X", "utf8"]

    if "nuitka.__main__" in sys.modules:
        our_filename = sys.modules["nuitka.__main__"].__file__
    else:
        our_filename = sys.modules["__main__"].__file__

    args += ["-S", our_filename]

    os.environ["NUITKA_BINARY_NAME"] = sys.modules["__main__"].__file__
    os.environ["NUITKA_PACKAGE_HOME"] = os.path.dirname(
        os.path.abspath(sys.modules["nuitka"].__path__[0])
    )

    if pgo_filename is not None:
        args.append("--pgo-python-input=%s" % pgo_filename)

    # Same arguments as before.
    args += sys.argv[1:]

    os.environ["NUITKA_PYTHONPATH"] = repr(sys.path)

    from nuitka.importing.PreloadedPackages import (
        detectPreLoadedPackagePaths,
        detectPthImportedPackages,
    )

    os.environ["NUITKA_NAMESPACES"] = repr(detectPreLoadedPackagePaths())

    if "site" in sys.modules:
        site_filename = sys.modules["site"].__file__
        if site_filename.endswith(".pyc"):
            site_filename = site_filename[:-4] + ".py"

        os.environ["NUITKA_SITE_FILENAME"] = site_filename

        os.environ["NUITKA_PTH_IMPORTED"] = repr(detectPthImportedPackages())

    if sys.flags.no_site:
        os.environ["NUITKA_NOSITE_FLAG"] = "1"

    os.environ["PYTHONHASHSEED"] = "0"

    os.environ["NUITKA_REEXECUTION"] = "1"

    # Does not return:
    callExecProcess(args)
