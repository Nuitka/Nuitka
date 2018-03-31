#!/usr/bin/env python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

"""
This is the main program of Nuitka, it checks the options and then translates
one or more modules to a C-ish source code using Python C/API in a "*.build"
directory and then compiles that to either an executable or an extension module
or package, that can contain all used modules too.
"""

# Import as little as possible initially, because we might be re-executing
# soon.
import os
import sys
import warnings


def main():
    # PyLint for Python3 thinks we import from ourselves if we really
    # import from package, pylint:disable=I0021,no-name-in-module

    # Also high complexity.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    if "NUITKA_BINARY_NAME" in os.environ:
        sys.argv[0] = os.environ["NUITKA_BINARY_NAME"]

    if "NUITKA_PYTHONPATH" in os.environ:
        # Restore the PYTHONPATH gained from the site module, that we chose not
        # to have imported. pylint: disable=eval-used
        sys.path = eval(os.environ["NUITKA_PYTHONPATH"])
        del os.environ["NUITKA_PYTHONPATH"]
    else:
        # Remove path element added for being called via "__main__.py", this can
        # only lead to trouble, having e.g. a "distutils" in sys.path that comes
        # from "nuitka.distutils".
        sys.path = [
            path_element
            for path_element in sys.path
            if os.path.dirname(os.path.abspath(__file__)) != path_element
        ]

    # For re-execution, we might not have done this.
    from nuitka import Options                  # isort:skip
    Options.parseArgs()

    from nuitka.utils import Utils, Execution   # isort:skip

    import logging # isort:skip
    logging.basicConfig(format = "Nuitka:%(levelname)s:%(message)s")

    # We don't care, and these are triggered by run time calculations of "range" and
    # others, while on python2.7 they are disabled by default.

    warnings.simplefilter("ignore", DeprecationWarning)

    # We will run with the Python configuration as specified by the user, if it does
    # not match, we restart ourselves with matching configuration.
    needs_reexec = False

    current_version = "%d.%d" % (sys.version_info[0], sys.version_info[1])

    # We support to execute with a specified version.
    intended_version = Options.getIntendedPythonVersion()
    if intended_version is None:
        intended_version = current_version

    # If it's a different version, we find it by guessing it, otherwise we use the
    # one previously used.
    if current_version != intended_version:
        if Utils.getOS() == "Windows":
            python_binary = Execution.getPythonExePathWindows(
                intended_version,
                Options.getIntendedPythonArch()
            )
        else:
            python_binary = Execution.getExecutablePath("python" + intended_version)

        if python_binary is None:
            sys.exit(
                "Error, cannot find Python %s binary in PATH (%s)." % (
                    intended_version,
                    os.environ.get("PATH", "")
                )
            )

        needs_reexec = True
    else:
        python_binary = sys.executable

    if sys.flags.no_site == 0:
        needs_reexec = True

    # The hash randomization totally changes the created source code created,
    # changing it every single time Nuitka is run. This kills any attempt at
    # caching it, and comparing generated source code. While the created binary
    # actually may still use it, during compilation we don't want to. So lets
    # disable it.
    if os.environ.get("PYTHONHASHSEED", "-1") != '0':
        needs_reexec = True

    # In case we need to re-execute.
    if needs_reexec:
        if not Options.isAllowedToReexecute():
            sys.exit("Error, not allowed to re-execute, but that would be needed.")

        our_filename = sys.modules[__name__].__file__

        # Workaround for --python-version which will choke on existing, but
        # not matching .pyc files.
        if current_version != intended_version:
            pyc_filename = our_filename[:-2] + ".pyc"

            if os.path.exists(pyc_filename):
                try:
                    os.unlink(pyc_filename)
                except OSError:
                    pass

        # Execute with full path as the process name, so it can find itself and its
        # libraries.
        args = [
            python_binary,
            python_binary,
            "-S",
            our_filename,
        ]

        os.environ["NUITKA_BINARY_NAME"] = sys.modules["__main__"].__file__

        if Options.is_nuitka_run:
            args.append("--run")

        # Same arguments as before.
        args += sys.argv[1:] + list(Options.getMainArgs())

        if current_version == intended_version:
            os.environ["NUITKA_PYTHONPATH"] = repr(
                sys.path
            )

            from nuitka.importing.PreloadedPackages import detectPreLoadedPackagePaths, detectPthImportedPackages
            os.environ["NUITKA_NAMESPACES"] = repr(
                detectPreLoadedPackagePaths()
            )

            if "site" in sys.modules:
                os.environ["NUITKA_SITE_FILENAME"] = sys.modules["site"].__file__

                os.environ["NUITKA_PTH_IMPORTED"] = repr(detectPthImportedPackages())


        os.environ["NUITKA_SITE_FLAG"] = str(sys.flags.no_site) \
                                           if "no_site" not in Options.getPythonFlags() \
                                         else '1'

        os.environ["PYTHONHASHSEED"] = '0'

        Execution.callExec(args)

    if Options.isShowMemory():
        from nuitka.utils import MemoryUsage
        MemoryUsage.startMemoryTracing()

    # Inform the user about potential issues.
    if current_version not in Options.getSupportedPythonVersions():

        # Do not disturb run of automatic tests, detected from the presence of
        # that environment variable.
        if "PYTHON" not in os.environ:
            logging.warning(
                "The version '%s' is not currently supported. Expect problems.",
                current_version
            )

    if "NUITKA_NAMESPACES" in os.environ:
        # Restore the detected name space packages, that were force loaded in
        # site.py, and will need a free pass later on. pylint: disable=eval-used

        from nuitka.importing.PreloadedPackages import setPreloadedPackagePaths

        setPreloadedPackagePaths(eval(os.environ["NUITKA_NAMESPACES"]))
        del os.environ["NUITKA_NAMESPACES"]

    if "NUITKA_PTH_IMPORTED" in os.environ:
        # Restore the packages that the ".pth" files asked to import.
        # pylint: disable=eval-used

        from nuitka.importing.PreloadedPackages import setPthImportedPackages

        setPthImportedPackages(eval(os.environ["NUITKA_PTH_IMPORTED"]))
        del os.environ["NUITKA_PTH_IMPORTED"]

    # Now the real main program of Nuitka can take over.
    from nuitka import MainControl  # isort:skip
    MainControl.main()

    if Options.isShowMemory():
        MemoryUsage.showMemoryTrace()

if __name__ == "__main__":
    main()
