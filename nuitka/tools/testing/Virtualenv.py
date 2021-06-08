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
""" Creating virtualenvs and running commands in them.

"""


from __future__ import print_function

import os
import subprocess
import sys
from contextlib import contextmanager

from nuitka.__past__ import unicode  # pylint: disable=I0021,redefined-builtin
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import removeDirectory, withDirectoryChange

from .Common import my_print


class Virtualenv(object):
    def __init__(self, env_dir):
        self.env_dir = os.path.abspath(env_dir)

    def runCommand(self, commands):
        if type(commands) in (str, unicode):
            commands = [commands]

        with withDirectoryChange(self.env_dir):
            if os.name == "nt":
                commands = [r"call scripts\activate.bat"] + commands
            else:
                commands = [". bin/activate"] + commands

            command = " && ".join(commands)
            assert os.system(command) == 0, command

    def runCommandWithOutput(self, commands, style=None):
        """
        Returns the stdout,stderr from process.communicate()
        """
        if type(commands) in (str, unicode):
            commands = [commands]

        with withDirectoryChange(self.env_dir):
            if os.name == "nt":
                commands = [r"call scripts\activate.bat"] + commands
            else:
                commands = [". bin/activate"] + commands

            popen_arg = " && ".join(commands)

            if style is not None:
                my_print("Executing: %s" % popen_arg, style=style)

            # Use subprocess and also return outputs, stdout, stderr, result
            process = subprocess.Popen(
                args=popen_arg,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            return process.communicate()

    def getVirtualenvDir(self):
        return self.env_dir


@contextmanager
def withVirtualenv(env_name, base_dir=None, python=None, delete=True, style=None):
    """Create a virtualenv and change into it.

    Activating for actual use will be your task.
    """

    print("Creating virtualenv for quick test:")

    if python is None:
        python = sys.executable

    if base_dir is not None:
        env_dir = os.path.join(base_dir, env_name)
    else:
        env_dir = env_name

    removeDirectory(env_dir, ignore_errors=False)

    with withDirectoryChange(base_dir, allow_none=True):
        command = [python, "-m", "virtualenv", env_name]
        if style is not None:
            my_print("Executing: %s" % " ".join(command))
        check_call(command)

        yield Virtualenv(env_dir)

    if delete:
        removeDirectory(env_dir, ignore_errors=False)
