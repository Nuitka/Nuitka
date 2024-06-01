#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Creating virtualenvs and running commands in them.

"""

import os
import sys
from contextlib import contextmanager

from nuitka.__past__ import unicode
from nuitka.utils.Execution import (
    NuitkaCalledProcessError,
    check_call,
    executeProcess,
    withEnvironmentVarsOverridden,
)
from nuitka.utils.FileOperations import (
    getDirectoryRealPath,
    removeDirectory,
    withDirectoryChange,
)


class Virtualenv(object):
    def __init__(self, env_dir, logger):
        self.env_dir = os.path.abspath(env_dir)
        self.logger = logger

    def runCommand(self, commands, env=None, style=None):
        if type(commands) in (str, unicode):
            commands = [commands]

        with withDirectoryChange(self.env_dir):
            if os.name == "nt":
                commands = [r"call scripts\activate.bat"] + commands
            else:
                commands = [". bin/activate"] + commands

            command = " && ".join(commands)

            if style is not None:
                self.logger.info("Executing: %s" % command, style=style)

            with withEnvironmentVarsOverridden(env):
                exit_code = os.system(command)
                if exit_code != 0:
                    self.logger.info(
                        "Failure %s for: %s" % (exit_code, command), style=style
                    )

                    raise NuitkaCalledProcessError(
                        exit_code, command, output=None, stderr=None
                    )

    def runCommandWithOutput(self, commands, style=None):
        """
        Returns the stdout,stderr,exit_code from running command
        """
        if type(commands) in (str, unicode):
            commands = [commands]

        with withDirectoryChange(self.env_dir):
            if os.name == "nt":
                commands = [r"call scripts\activate.bat"] + commands
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

    def getVirtualenvDir(self):
        return self.env_dir


@contextmanager
def withVirtualenv(
    env_name, logger, base_dir=None, python=None, delete=True, style=None
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
        command = [python, "-m", "virtualenv", env_name]
        if style is not None:
            logger.info("Executing: %s" % " ".join(command), style=style)
        check_call(command)

    try:
        yield Virtualenv(env_dir, logger=logger)
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
