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
""" Scons interface.

Interaction with scons. Find the binary, and run it with a set of given
options.

"""

import contextlib
import copy
import os
import subprocess
import sys

from nuitka import Options, Tracing
from nuitka.__past__ import unicode  # pylint: disable=I0021,redefined-builtin
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import getTargetPythonDLLPath, python_version
from nuitka.utils import Execution, Utils
from nuitka.utils.FileOperations import (
    deleteFile,
    getExternalUsePath,
    getWindowsShortPathName,
    hasFilenameExtension,
    listDir,
)

from .SconsCaching import checkCachingSuccess


def getSconsDataPath():
    """Return path to where data for scons lives, e.g. static C source files."""

    return os.path.dirname(__file__)


def _getSconsInlinePath():
    """ Return path to inline copy of scons. """

    return os.path.join(getSconsDataPath(), "inline_copy")


def _getSconsBinaryCall():
    """Return a way to execute Scons.

    Using potentially in-line copy if no system Scons is available
    or if we are on Windows, there it is mandatory.
    """

    inline_path = os.path.join(_getSconsInlinePath(), "bin", "scons.py")

    if os.path.exists(inline_path):
        return [
            _getPythonForSconsExePath(),
            "-W",
            "ignore",  # Disable Python warnings in case of debug Python.
            getExternalUsePath(inline_path),
        ]
    else:
        scons_path = Execution.getExecutablePath("scons")

        if scons_path is not None:
            return [scons_path]
        else:
            Tracing.scons_logger.sysexit(
                "Error, the inline copy of scons is not present, nor a scons binary in the PATH."
            )


def _getPythonSconsExePathWindows():
    """Find Python for Scons on Windows.

    Only 3.5 or higher will do.
    """

    # Ordered in the list of preference.
    python_dir = Execution.getPythonInstallPathWindows(
        supported=("3.5", "3.6", "3.7", "3.8", "3.9")
    )

    if python_dir is not None:
        return os.path.join(python_dir, "python.exe")
    else:
        return None


def _getPythonForSconsExePath():
    """Find a way to call any Python that works for Scons.

    Scons needs it as it doesn't support all Python versions.
    """
    python_exe = Options.getPythonPathForScons()

    if python_exe is not None:
        return python_exe

    if python_version < 0x300 and not Utils.isWin32Windows():
        # Python 2.6 and 2.7 are fine for scons on all platforms, but not
        # on Windows due to clcache usage.
        return sys.executable
    elif python_version >= 0x350:
        # Python 3.5 or higher work on all platforms.
        return sys.executable
    elif Utils.isWin32Windows():
        python_exe = _getPythonSconsExePathWindows()

        if python_exe is not None:
            return python_exe
        else:
            Tracing.scons_logger.sysexit(
                """\
Error, while Nuitka works with older Python, Scons does not, and therefore
Nuitka needs to find a Python 3.5 or higher executable, so please install
it.

You may provide it using option "--python-for-scons=path_to_python.exe"
in case it is not visible in registry, e.g. due to using uninstalled
Anaconda Python.
"""
            )

    for version_candidate in ("2.7", "2.6", "3.5", "3.6", "3.7", "3.8", "3.9"):
        candidate = Execution.getExecutablePath("python" + version_candidate)

        if candidate is not None:
            return candidate

    # Lets be optimistic, this is most often going to be new enough or a
    # Python2 variant.
    return "python"


@contextlib.contextmanager
def _setupSconsEnvironment():
    """Setup the scons execution environment.

    For the target Python we provide "NUITKA_PYTHON_DLL_PATH" to see where the
    Python DLL lives, in case it needs to be copied, and then also the
    "NUITKA_PYTHON_EXE_PATH" to find the Python binary itself.

    We also need to preserve PYTHONPATH and PYTHONHOME, but remove it potentially
    as well, so not to confuse the other Python binary used to run scons.
    """

    # For Python2, avoid unicode working directory.
    if Utils.isWin32Windows() and python_version < 0x300:
        if os.getcwd() != os.getcwdu():
            os.chdir(getWindowsShortPathName(os.getcwdu()))

    if Utils.isWin32Windows():
        # On Win32, we use the Python.DLL path for some things. We pass it
        # via environment variable
        os.environ["NUITKA_PYTHON_DLL_PATH"] = getTargetPythonDLLPath()

    os.environ["NUITKA_PYTHON_EXE_PATH"] = sys.executable

    # Remove environment variables that can only harm if we have to switch
    # major Python versions, these cannot help Python2 to execute scons, this
    # is a bit of noise, but helpful.
    old_pythonpath = None
    old_pythonhome = None

    if python_version >= 0x300:
        if "PYTHONPATH" in os.environ:
            old_pythonpath = os.environ["PYTHONPATH"]
            del os.environ["PYTHONPATH"]

        if "PYTHONHOME" in os.environ:
            old_pythonhome = os.environ["PYTHONHOME"]
            del os.environ["PYTHONHOME"]

    import nuitka

    os.environ["NUITKA_PACKAGE_DIR"] = os.path.abspath(nuitka.__path__[0])

    yield

    if old_pythonpath is not None:
        os.environ["PYTHONPATH"] = old_pythonpath

    if old_pythonhome is not None:
        os.environ["PYTHONHOME"] = old_pythonhome

    if Utils.isWin32Windows():
        del os.environ["NUITKA_PYTHON_DLL_PATH"]

    del os.environ["NUITKA_PYTHON_EXE_PATH"]

    del os.environ["NUITKA_PACKAGE_DIR"]


def _buildSconsCommand(quiet, options, scons_filename):
    """Build the scons command to run.

    The options are a dictionary to be passed to scons as a command line,
    and other scons stuff is set.
    """

    scons_command = _getSconsBinaryCall()

    if quiet:
        scons_command.append("--quiet")

    scons_command += [
        # The scons file
        "-f",
        getExternalUsePath(os.path.join(getSconsDataPath(), scons_filename)),
        # Parallel compilation.
        "--jobs",
        str(Options.getJobLimit()),
        # Do not warn about deprecation from Scons
        "--warn=no-deprecated",
        # Don't load "site_scons" at all.
        "--no-site-dir",
    ]

    if Options.isShowScons():
        scons_command.append("--debug=explain,stacktrace")

    # Python2, encoding unicode values
    def encode(value):
        if str is bytes and type(value) is unicode:
            return value.encode("utf8")
        else:
            return value

    # Option values to provide to scons. Find these in the caller.
    for key, value in options.items():
        scons_command.append(key + "=" + encode(value))

    # Python2, make argument encoding recognizable.
    if str is bytes:
        scons_command.append("arg_encoding=utf8")

    return scons_command


def runScons(options, quiet, scons_filename):
    with _setupSconsEnvironment():
        if Options.shallCompileWithoutBuildDirectory():
            # Make sure we become non-local, by changing all paths to be
            # absolute, but ones that can be resolved by any program
            # externally, as the Python of Scons may not be good at unicode.

            options = copy.deepcopy(options)
            source_dir = options["source_dir"]
            options["source_dir"] = "."
            options["result_name"] = getExternalUsePath(
                options["result_name"], only_dirname=True
            )
            options["nuitka_src"] = getExternalUsePath(options["nuitka_src"])
            if "result_exe" in options:
                options["result_exe"] = getExternalUsePath(
                    options["result_exe"], only_dirname=True
                )
            if "compiled_exe" in options:
                options["compiled_exe"] = getExternalUsePath(
                    options["compiled_exe"], only_dirname=True
                )

        else:
            source_dir = None

        scons_command = _buildSconsCommand(
            quiet=quiet, options=options, scons_filename=scons_filename
        )

        if Options.isShowScons():
            Tracing.printLine("Scons command:", " ".join(scons_command))

        Tracing.flushStandardOutputs()

        # Call scons, make sure to pass on quiet setting.
        with Execution.withEnvironmentVarOverriden(
            "NUITKA_QUIET", "1" if Tracing.is_quiet else "0"
        ):
            result = subprocess.call(scons_command, shell=False, cwd=source_dir)

        if result == 0:
            checkCachingSuccess(source_dir or options["source_dir"])

        return result == 0


def asBoolStr(value):
    """ Encode booleans for transfer via command line. """

    return "true" if value else "false"


def cleanSconsDirectory(source_dir):
    """ Clean scons build directory. """

    extensions = (
        ".bin",
        ".c",
        ".cpp",
        ".exp",
        ".h",
        ".lib",
        ".manifest",
        ".o",
        ".obj",
        ".os",
        ".rc",
        ".res",
        ".S",
        ".txt",
        ".const",
    )

    def check(path):
        if hasFilenameExtension(path, extensions):
            deleteFile(path, must_exist=True)

    if os.path.isdir(source_dir):
        for path, _filename in listDir(source_dir):
            check(path)

        static_dir = os.path.join(source_dir, "static_src")

        if os.path.exists(static_dir):
            for path, _filename in listDir(static_dir):
                check(path)

        plugins_dir = os.path.join(source_dir, "plugins")

        if os.path.exists(plugins_dir):
            for path, _filename in listDir(plugins_dir):
                check(path)


def setCommonOptions(options):
    # Scons gets transported many details, that we express as variables, and
    # have checks for them, leading to many branches and statements,

    if Options.shallRunInDebugger():
        options["full_names"] = "true"

    if Options.assumeYesForDownloads():
        options["assume_yes_for_downloads"] = asBoolStr(True)

    if not Options.shallUseProgressBar():
        options["progress_bar"] = "false"

    if Options.isClang():
        options["clang_mode"] = "true"

    if Options.isShowScons():
        options["show_scons"] = "true"

    if Options.isMingw64():
        options["mingw_mode"] = "true"

    if Options.getMsvcVersion():
        msvc_version = Options.getMsvcVersion()

        msvc_version = msvc_version.replace("exp", "Exp")
        if "." not in msvc_version:
            msvc_version += ".0"

        options["msvc_version"] = msvc_version

    if Options.shallDisableConsoleWindow():
        options["win_disable_console"] = asBoolStr(True)

    if Options.isLto():
        options["lto_mode"] = asBoolStr(True)

    cpp_defines = Plugins.getPreprocessorSymbols()
    if cpp_defines:
        options["cpp_defines"] = ",".join(
            "%s%s%s" % (key, "=" if value else "", value or "")
            for key, value in cpp_defines.items()
        )

    link_libraries = Plugins.getExtraLinkLibraries()
    if link_libraries:
        options["link_libraries"] = ",".join(link_libraries)
