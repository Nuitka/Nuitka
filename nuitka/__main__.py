#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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

_cached_process_environments = {}


def getLaunchingNuitkaProcessEnvironmentValue(environment_variable_name):
    if environment_variable_name not in _cached_process_environments:
        _cached_process_environments[environment_variable_name] = os.getenv(
            environment_variable_name
        )
        if _cached_process_environments[environment_variable_name] is not None:
            del os.environ[environment_variable_name]

    value = _cached_process_environments[environment_variable_name]

    if value is not None and ":" not in value:
        value = None

    if value is not None:
        pid, value = value.split(":", 1)

        try:
            pid = int(pid)
        except ValueError:
            value = None
        else:
            if os.name != "nt":
                if pid != os.getpid():
                    value = None

    return value


def main():
    # PyLint for Python3 thinks we import from ourselves if we really
    # import from package, pylint: disable=I0021,no-name-in-module

    # Also high complexity.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    if (
        os.name == "nt"
        and os.path.normcase(os.path.basename(sys.executable)) == "pythonw.exe"
    ):
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None,
            "You have to use the 'python.exe' and not a 'pythonw.exe' to run Nuitka",
            "Error",
            0x1000,  # MB_SYSTEMMODAL
        )
        sys.exit(1)

    # Make sure this is removed if it exists.
    getLaunchingNuitkaProcessEnvironmentValue("NUITKA_SITE_FILENAME")

    nuitka_binary_name = getLaunchingNuitkaProcessEnvironmentValue("NUITKA_BINARY_NAME")
    if nuitka_binary_name is not None:
        sys.argv[0] = nuitka_binary_name

    nuitka_pythonpath_ast = getLaunchingNuitkaProcessEnvironmentValue(
        "NUITKA_PYTHONPATH_AST"
    )

    if nuitka_pythonpath_ast is not None:
        # Restore the PYTHONPATH gained from the site module, that we chose not
        # to have imported during compilation. For loading "ast" module, we need
        # one element, that is not necessarily in our current path, but we use
        # that to evaluate the current path.
        sys.path = [nuitka_pythonpath_ast]
        import ast

        sys.path = ast.literal_eval(
            getLaunchingNuitkaProcessEnvironmentValue("NUITKA_PYTHONPATH")
        )
    else:
        # Remove path element added for being called via "__main__.py", this can
        # only lead to trouble, having e.g. a "distutils" in sys.path that comes
        # from "nuitka.distutils". Also ignore path elements that do not really
        # exist.
        sys.path = [
            path_element
            for path_element in sys.path
            if os.path.dirname(os.path.abspath(__file__)) != path_element
            if os.path.exists(path_element)
        ]

    # We will run with the Python configuration as specified by the user, if it does
    # not match, we restart ourselves with matching configuration.
    needs_re_execution = False

    if sys.flags.no_site == 0:
        needs_re_execution = True

    # The hash randomization totally changes the created source code created,
    # changing it every single time Nuitka is run. This kills any attempt at
    # caching it, and comparing generated source code. While the created binary
    # actually may still use it, during compilation we don't want to. So lets
    # disable it.
    if os.getenv("PYTHONHASHSEED", "-1") != "0":
        needs_re_execution = True

    # The frozen stdlib modules of Python 3.11 are less compatible than the ones
    # of Nuitka, so prefer those.
    if sys.version_info >= (3, 11):
        from _imp import _frozen_module_names

        if "os" in _frozen_module_names():
            needs_re_execution = True

    # Avoid doing it when running in Visual Code.
    if needs_re_execution and "debugpy" in sys.modules:
        needs_re_execution = False

    # In case we need to re-execute.
    if needs_re_execution:
        from nuitka.utils.ReExecute import reExecuteNuitka  # isort:skip

        # Does not return
        reExecuteNuitka(pgo_filename=None)

    # We don't care about deprecations in any version, and these are triggered
    # by run time calculations of "range" and others, while on python2.7 they
    # are disabled by default.
    import warnings

    warnings.simplefilter("ignore", DeprecationWarning)

    # Hack, we need this to bootstrap and it's actually living in __main__
    # module of nuitka package and renamed to where we can get at easily for
    # other uses.
    __import__("nuitka").getLaunchingNuitkaProcessEnvironmentValue = (
        getLaunchingNuitkaProcessEnvironmentValue
    )

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
        # site.py, and will need a free pass later on
        from nuitka.importing.PreloadedPackages import setPreloadedPackagePaths

        setPreloadedPackagePaths(ast.literal_eval(os.environ["NUITKA_NAMESPACES"]))
        del os.environ["NUITKA_NAMESPACES"]

    if "NUITKA_PTH_IMPORTED" in os.environ:
        # Restore the packages that the ".pth" files asked to import.
        from nuitka.importing.PreloadedPackages import setPthImportedPackages

        setPthImportedPackages(ast.literal_eval(os.environ["NUITKA_PTH_IMPORTED"]))
        del os.environ["NUITKA_PTH_IMPORTED"]

    if "NUITKA_USER_SITE" in os.environ:
        from nuitka.utils.Distributions import setUserSiteDirectory

        setUserSiteDirectory(ast.literal_eval(os.environ["NUITKA_USER_SITE"]))

        del os.environ["NUITKA_USER_SITE"]

    # Now the real main program of Nuitka can take over.
    from nuitka import MainControl  # isort:skip

    MainControl.main()

    if Options.isShowMemory():
        MemoryUsage.showMemoryTrace()


if __name__ == "__main__":
    _nuitka_package_home = getLaunchingNuitkaProcessEnvironmentValue(
        "NUITKA_PACKAGE_HOME"
    )
    if _nuitka_package_home is not None:
        sys.path.insert(0, _nuitka_package_home)

        import nuitka  # just to have it loaded from there, pylint: disable=unused-import

        assert sys.path[0] is _nuitka_package_home
        del sys.path[0]

    main()

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
