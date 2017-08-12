#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nuitka distutils integration.

"""

import os
import shutil
import subprocess
import sys

import wheel.bdist_wheel  # @UnresolvedImport


# Class name enforced by distutils, must match the command name.
# pylint: disable=C0103
class bdist_nuitka(wheel.bdist_wheel.bdist_wheel):

    # Our wheel base class is very unpure, so are we
    # pylint: disable=attribute-defined-outside-init
    def run(self):
        self.compile_packages = self.distribution.packages
        self.main_package = self.compile_packages[0]

        # Exclude packages from the wheel, we deal with them by compiling
        # into single package.
        # self.distribution.packages = []

        wheel.bdist_wheel.bdist_wheel.run(self)

    def _buildPackage(self, build_lib):
        # Nuitka wants the main package by filename, probably we should stop
        # needing that.
        from nuitka.importing.Importing import findModule, setMainScriptDirectory
        from nuitka.utils.Execution import getExecutablePath

        old_dir = os.getcwd()
        os.chdir(build_lib)

        # Search in the build directory preferrably.
        setMainScriptDirectory('.')

        package, main_filename, finding = findModule(
            importing      = None,
            module_name    = self.main_package,
            parent_package = None,
            level          = 0,
            warn           = False
        )

        # Check expectations, e.g. do not compile built-in modules.
        assert finding == "absolute", finding
        assert package is None, package

        nuitka_binary = getExecutablePath("nuitka")
        if nuitka_binary is None:
            sys.exit("Error, cannot find nuitka binary in PATH.")

        command = [
            sys.executable,
            nuitka_binary,
            "--module",
            "--plugin-enable=pylint-warnings",
            "--output-dir=%s" % build_lib,
            "--recurse-to={%s}" % ','.join(self.compile_packages),
            "--recurse-dir=%s" % self.main_package,
            "--recurse-not-to=*.tests",
            "--show-modules",
            "--remove-output",
            main_filename,
        ]

        subprocess.check_call(
            command
        )
        os.chdir(old_dir)

        self.build_lib = build_lib

    def run_command(self, command):
        if command == "install":
            command_obj = self.distribution.get_command_obj(command)

            basedir_observed = ""

            if os.name == "nt":
                # win32 barfs if any of these are ''; could be '.'?
                # (distutils.command.install:change_roots bug)
                basedir_observed = os.path.normpath(os.path.join(self.data_dir, ".."))

            setattr(command_obj, "install_platlib", basedir_observed)
            setattr(command_obj, "install_purelib", None)

            shutil.rmtree(os.path.join(self.build_lib, self.main_package))

        result = wheel.bdist_wheel.bdist_wheel.run_command(self, command)

        # After building, we are ready to build the extension module, from
        # what "build_py" command has done.
        if command == "build":
            command_obj = self.distribution.get_command_obj(command)
            command_obj.ensure_finalized()

            self._buildPackage(command_obj.build_lib)

        return result

    def write_wheelfile(self, wheelfile_base, generator = None):
        self.root_is_pure = False

        if generator is None:
            from nuitka.Version import getNuitkaVersion
            generator = "Nuitka (%s)" % getNuitkaVersion()

        wheel.bdist_wheel.bdist_wheel.write_wheelfile(
            self,
            wheelfile_base = wheelfile_base,
            generator      = generator
        )
