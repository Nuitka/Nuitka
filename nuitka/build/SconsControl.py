#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Setup and execution of the Scons build.

This is the shared entry and exit point of the Scons files, e.g. to set up
the Scons signature database and stack size before the build, and to launch
the target at the end.
"""

import os
import sys

from nuitka.Tracing import scons_details_logger
from nuitka.utils.FileOperations import getNormalizedPathJoin
from nuitka.utils.Utils import isWin32Windows

from .SconsHacks import makeLinkerUseResponseFile
from .SconsProgress import setSconsProgressBarTotal
from .SconsSpawn import enableSpawnMonitoring
from .SconsStableIncludePaths import makeIncludePathsStable
from .SconsUtils import (
    changeKeyboardInterruptToErrorExit,
    getArgumentList,
    writeSconsReport,
)

# spell-checker: ignore cppdefines,cpppath,libpath


def _raiseStackSizeLimit():
    """Increase the stack size limit for the scons process.

    Notes:
        The C compiler processes spawned by scons inherit the stack size
        limit. Compiling very large generated source files can make the C
        compiler use deep recursion and crash with a stack overflow, if the
        limit is too small. The limit is only ever increased, never decreased.
    """

    if not isWin32Windows():
        import resource  # pylint: disable=I0021,import-error

        stack_soft, stack_hard = resource.getrlimit(resource.RLIMIT_STACK)

        if stack_hard == resource.RLIM_INFINITY:
            stack_wanted = stack_hard
        else:
            stack_wanted = max(stack_soft, stack_hard)

        try:
            resource.setrlimit(resource.RLIMIT_STACK, (stack_wanted, stack_hard))
        except (OSError, ValueError):
            pass
        else:
            scons_details_logger.info(
                "Stack size limit set to %s (was %s)."
                % tuple(
                    "unlimited" if limit == resource.RLIM_INFINITY else limit
                    for limit in (stack_wanted, stack_soft)
                )
            )


def setupScons(env, source_dir):
    env["BUILD_DIR"] = source_dir

    # Store the file signatures database with the rest of the source files and
    # make it version dependent on the Python version of running Scons, as its
    # pickle is being used, spell-checker: ignore sconsign
    sconsign_filename = os.path.abspath(
        getNormalizedPathJoin(
            source_dir, ".sconsign-%d%s" % (sys.version_info[0], sys.version_info[1])
        )
    )

    env.SConsignFile(sconsign_filename)

    _raiseStackSizeLimit()


def executeSconsBuild(
    env, target, source_filenames, progressbar_name, stable_include_paths
):
    """Execute the Scons build by preparing and launching the target.

    Notes:
        This makes the include paths stable across machines if requested,
        enables the spawn monitoring, turns keyboard interrupts into error
        exits, writes the Scons report, sets the progress bar total, and
        launches the target.

    Args:
        env: The Scons environment to work with.
        target: The Scons target to build.
        source_filenames: The source filenames being built.
        progressbar_name: Name of the progress bar to use.
        stable_include_paths: Whether to make include paths stable across
            machines by replacing absolute ones with build local paths.
    """
    # Plugin contributed C defines should be used too.
    cpp_defines = getArgumentList("cpp_defines", "")
    env.Append(CPPDEFINES=cpp_defines)

    # Plugin contributed C include directories should be used too.
    cpp_include_dirs = getArgumentList("cpp_include_dirs", "")
    env.Prepend(CPPPATH=cpp_include_dirs)

    # Plugin contributed link dirs should be used too.
    link_dirs = getArgumentList("link_dirs", "")
    env.Append(LIBPATH=link_dirs)

    # Plugin contributed link libraries should be used too.
    link_libraries = getArgumentList("link_libraries", "")
    env.Append(LIBS=link_libraries)

    if stable_include_paths:
        makeIncludePathsStable(env)

    # Hack to make Scons use a response file for gcc linking, to avoid line
    # length limits, which can make linking fail with many modules otherwise.
    # Most needed on Windows, but useful on other platforms too. The MSVC
    # linker already uses a Scons "TEMPFILE", and its "LINKCOM" is not a
    # string, so it must not be handled here.
    if env.gcc_mode:
        makeLinkerUseResponseFile(
            env=env,
            source_filenames=source_filenames,
        )

    # Work around windows bugs and use watchdogs to track progress of
    # compilation.
    enableSpawnMonitoring(
        env=env,
        source_filenames=source_filenames,
    )

    # Before we go, also lets turn KeyboardInterrupt into a mere error exit as
    # the scons traceback is not going to be very interesting to us.
    changeKeyboardInterruptToErrorExit()

    writeSconsReport(env=env, target=target)

    setSconsProgressBarTotal(
        name=progressbar_name,
        total=len(source_filenames),
    )

    scons_details_logger.info("Launching Scons target: %s" % target)

    env.Default(target)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
