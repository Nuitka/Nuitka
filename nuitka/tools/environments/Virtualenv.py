#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Creating virtualenvs and running commands in them."""

import os
import sys
from contextlib import contextmanager

from nuitka.__past__ import unicode
from nuitka.utils.Execution import (
    NuitkaCalledProcessError,
    check_call,
    executeProcess,
    getExecutablePath,
    withEnvironmentVarsOverridden,
)
from nuitka.utils.FileOperations import (
    getDirectoryRealPath,
    relpath,
    removeDirectory,
    withDirectoryChange,
)


class Virtualenv(object):
    def __init__(self, env_dir, tool, logger):
        self.env_dir = os.path.abspath(env_dir)
        self.logger = logger
        self.tool = tool

    def runCommand(self, commands, keep_cwd=False, env=None, style=None):
        if type(commands) in (str, unicode):
            commands = [commands]

        # TODO: For uv, we need to not install inside of the environment
        # from from the outside.
        if self.tool == "uv":
            assert all("pip" not in command for command in commands), commands

        with withDirectoryChange(None if keep_cwd else self.env_dir, allow_none=True):
            if keep_cwd:
                activate_dir = relpath(self.env_dir, os.getcwd())
            else:
                activate_dir = "."

            if os.name == "nt":
                commands = [r"call %s\Scripts\activate.bat" % activate_dir] + commands
            else:
                commands = [". %s/bin/activate" % activate_dir] + commands

            command = " && ".join(commands)

            if style is not None:
                self.logger.info("Executing: %s" % command, style=style)

            with withEnvironmentVarsOverridden(env):
                stdout, stderr, exit_code = executeProcess(
                    command=command,
                    shell=True,
                    stdout=None,
                    stderr=None,
                )

                if exit_code != 0:
                    self.logger.info(
                        "Failure %s for: %s" % (exit_code, command),
                        keep_format=True,
                        style=style,
                    )

                    raise NuitkaCalledProcessError(
                        exit_code, command, output=stdout, stderr=stderr
                    )

    def runCommandWithOutput(self, commands, style=None):
        """
        Returns the stdout,stderr,exit_code from running command
        """
        if type(commands) in (str, unicode):
            commands = [commands]

        # TODO: For uv, we need to not install inside of the environment
        # from from the outside.
        if self.tool == "uv":
            assert all("pip" not in command for command in commands), commands

        with withDirectoryChange(self.env_dir):
            if os.name == "nt":
                commands = [r"call Scripts\activate.bat"] + commands
            else:
                commands = [". bin/activate"] + commands

            # Build shell command.
            command = " && ".join(commands)

            if style is not None:
                self.logger.info("Executing: %s" % command, style=style)

            # Use subprocess and also return outputs, stdout, stderr, result
            return executeProcess(
                command=command,
                shell=True,
            )

    def getBinaryPath(self, binary_name):
        return os.path.join(
            self.env_dir,
            "bin" if os.name != "nt" else "Scripts",
            binary_name,
        )

    def getVirtualenvDir(self):
        return self.env_dir


@contextmanager
def withVirtualenv(
    env_name,
    logger,
    base_dir=None,
    python=None,
    tool="virtualenv",
    delete=True,
    style=None,
):
    """Create a virtualenv and change into it.

    Activating for actual use will be your task.
    """

    if style is not None:
        logger.info("Creating a virtualenv:")

    if python is None:
        python = sys.executable

    # Avoid symlinks on Windows, they won't work for virtualenv e.g.
    python = os.path.join(
        getDirectoryRealPath(os.path.dirname(python)),
        os.path.basename(python),
    )

    if base_dir is not None:
        env_dir = os.path.join(base_dir, env_name)
    else:
        env_dir = env_name

    removeDirectory(
        env_dir,
        logger=logger,
        ignore_errors=False,
        extra_recommendation=None,
    )

    with withDirectoryChange(base_dir, allow_none=True):
        if tool == "virtualenv":
            command = [python, "-m", "virtualenv", env_name]
        elif tool == "venv":
            command = [python, "-m", "venv", env_name]
        elif tool == "uv":
            uv_path = getExecutablePath("uv")
            if uv_path is None:
                logger.sysexit("Error, cannot find 'uv' executable.")

            command = [uv_path, "venv", "--python", python, env_name]
        else:
            logger.sysexit("Error, unsupported virtualenv tool '%s'." % tool)

        if style is not None:
            # False alarm, pylint: disable=possibly-used-before-assignment
            logger.info("Executing: %s" % " ".join(command), style=style)

        check_call(command)

    try:
        yield Virtualenv(
            env_dir,
            logger=logger,
            tool=tool,
        )
    finally:
        if delete:
            removeDirectory(
                env_dir,
                logger=logger,
                ignore_errors=False,
                extra_recommendation=None,
            )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
