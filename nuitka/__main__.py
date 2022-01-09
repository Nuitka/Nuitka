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
"""
This is the main program of Nuitka, it checks the options and then translates
one or more modules to a C source code using Python C/API in a "*.build"
directory and then compiles that to either an executable or an extension module
or package, that can contain all used modules too.
"""

# Note: This avoids imports at all costs, such that initial startup doesn't do more
# than necessary, until re-execution has been decided.

import os
import sys


def main():
    # PyLint for Python3 thinks we import from ourselves if we really
    # import from package, pylint: disable=I0021,no-name-in-module

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

    # We will run with the Python configuration as specified by the user, if it does
    # not match, we restart ourselves with matching configuration.
    needs_reexec = False

    if sys.flags.no_site == 0:
        needs_reexec = True

    # The hash randomization totally changes the created source code created,
    # changing it every single time Nuitka is run. This kills any attempt at
    # caching it, and comparing generated source code. While the created binary
    # actually may still use it, during compilation we don't want to. So lets
    # disable it.
    if os.environ.get("PYTHONHASHSEED", "-1") != "0":
        needs_reexec = True

    # In case we need to re-execute.
    if needs_reexec:
        from nuitka.utils.ReExecute import reExecuteNuitka  # isort:skip

        # Does not return
        reExecuteNuitka(pgo_filename=None)

    # We don't care about deprecations in any version, and these are triggered
    # by run time calculations of "range" and others, while on python2.7 they
    # are disabled by default.
    import warnings

    warnings.simplefilter("ignore", DeprecationWarning)

    from nuitka import Options  # isort:skip

    Options.parseArgs()

    Options.commentArgs()

    # Load plugins after we know, we don't execute again.
    from nuitka.plugins.Plugins import activatePlugins

    activatePlugins()

    if Options.isShowMemory():
        from nuitka.utils import MemoryUsage

        MemoryUsage.startMemoryTracing()

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
    if "NUITKA_PACKAGE_HOME" in os.environ:
        sys.path.insert(0, os.environ["NUITKA_PACKAGE_HOME"])

        import nuitka  # just to have it loaded from there, pylint: disable=unused-import

        del sys.path[0]

    main()
