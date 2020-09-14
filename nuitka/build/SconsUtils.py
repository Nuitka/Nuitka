#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Helper functions for the scons file.

"""

import os
import signal
import sys

from nuitka.Tracing import scons_logger


def decodeData(data):
    """Our own decode tries to workaround MSVC misbehavior."""
    try:
        return data.decode(sys.stdout.encoding)
    except UnicodeDecodeError:
        import locale

        try:
            return data.decode(locale.getpreferredencoding())
        except UnicodeDecodeError:
            return data.decode("utf8", "backslashreplace")


# Windows target mode: Compile for Windows. Used to be an option, but we
# no longer cross compile this way.
win_target = os.name == "nt"


def getExecutablePath(filename, env):
    """ Find an execute in either normal PATH, or Scons detected PATH. """

    if os.path.exists(filename):
        return filename

    # Variable substitution from environment is needed, because this can contain
    # "$CC" which should be looked up too.
    while filename.startswith("$"):
        filename = env[filename[1:]]

    # Append ".exe" suffix  on Windows if not already present.
    if win_target and not filename.lower().endswith(".exe"):
        filename += ".exe"

    # Either look at the initial "PATH" as given from the outside or look at the
    # current environment.
    if env is None:
        search_path = os.environ["PATH"]
    else:
        search_path = env._dict["ENV"]["PATH"]  # pylint: disable=protected-access

    # Now check in each path element, much like the shell will.
    path_elements = search_path.split(os.pathsep)

    for path_element in path_elements:
        path_element = path_element.strip('"')

        full = os.path.join(path_element, filename)

        if os.path.exists(full):
            return full

    return None


def changeKeyboardInteruptToErrorExit():
    def signalHandler(
        signal, frame
    ):  # pylint: disable=redefined-outer-name,unused-argument
        sys.exit(2)

    signal.signal(signal.SIGINT, signalHandler)


def setEnvironmentVariable(env, key, value):
    os.environ[key] = value

    if env is not None:
        env._dict["ENV"][key] = value  # pylint: disable=protected-access


def addToPATH(env, dirname, prefix):
    path_value = os.environ["PATH"].split(os.pathsep)

    if prefix:
        path_value.insert(0, dirname)
    else:
        path_value.append(dirname)

    setEnvironmentVariable(env, "PATH", os.pathsep.join(path_value))


scons_report = None


def readSconsReport(source_dir):
    # singleton, pylint: disable=global-statement
    global scons_report

    if scons_report is None:
        scons_report = {}

        for line in open(os.path.join(source_dir, "scons-report.txt")):
            if "=" not in line:
                continue

            key, value = line.strip().split("=", 1)

            scons_report[key] = value

    return scons_report


def getSconsReportValue(source_dir, key):
    return readSconsReport(source_dir).get(key)


def addClangClPathFromMSVC(env, target_arch, show_scons_mode):
    cl_exe = getExecutablePath("cl", env=env)

    if cl_exe is None:
        scons_logger.warning("Visual Studio required for for Clang on Windows.")
        return

    clang_dir = cl_exe = os.path.join(cl_exe[: cl_exe.lower().rfind("msvc")], "Llvm")

    if target_arch == "x86_64":
        clang_dir = os.path.join(clang_dir, "x64", "bin")
    else:
        clang_dir = os.path.join(clang_dir, "bin")

    if os.path.exists(clang_dir):
        if show_scons_mode:
            scons_logger.info("Adding MSVC directory %r for Clang to PATH." % clang_dir)

        addToPATH(env, clang_dir, prefix=True)
    else:
        if show_scons_mode:
            scons_logger.info("No Clang component for MSVC found." % clang_dir)
