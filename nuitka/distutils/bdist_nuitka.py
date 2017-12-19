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
import fnmatch
import wheel.bdist_wheel  # @UnresolvedImport


# Class name enforced by distutils, must match the command name.
# pylint: disable=C0103
class bdist_nuitka(wheel.bdist_wheel.bdist_wheel):

    def finalize_options(self):
        # self.distribution.libraries = [[True]]
        self.distribution.has_ext_modules = lambda: True

        super(bdist_nuitka, self).finalize_options()
        # Force module to be recognised as binary rather than pure python
        self.root_is_pure = False
        self.plat_name_supplied = self.plat_name is not None

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

        old_dir = os.getcwd()
        os.chdir(build_lib)

        # Search in the build directory preferably.
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

        # If there are other files left over in the wheel after python scripts
        # are compiled, we'll keep the folder structure with the files in the wheel
        keep_resources = False

        python_files = []
        recurse_packages = self.compile_packages.copy()
        if os.path.isdir(main_filename):
            # Include all python files in wheel
            for root, dirs, files in os.walk(main_filename):
                for fn in files:
                    if fnmatch.fnmatch(fn, '*.py'):
                        relpath = os.path.relpath(os.path.join(root, fn), os.path.dirname(main_filename))
                        module = relpath[:-3] if fn != '__init__.py' else os.path.basename(root)
                        pypath = ".".join(module.split(os.sep))
                        recurse_packages.append(pypath)
                        python_files.append(os.path.join(root, fn))
                    else:
                        keep_resources = True

        output_dir = build_lib

        nuitka_binary = getExecutablePath("nuitka")
        if nuitka_binary is None:
            sys.exit("Error, cannot find nuitka binary in PATH.")

        command = [
            sys.executable,
            nuitka_binary,
            "--module",
            "--plugin-enable=pylint-warnings",
            "--output-dir=%s" % output_dir,
            "--recurse-dir=%s" % self.main_package,
            "--recurse-not-to=*.tests",
            "--show-modules",
            "--remove-output",
            main_filename,
        ] + ["--recurse-to=%s" % p for p in recurse_packages]

        subprocess.check_call(
            command
        )
        os.chdir(old_dir)

        self.build_lib = build_lib

        if keep_resources:
            # Delete the individual source files and add new __init__ stub
            for fn in python_files:
                os.unlink(fn)
        else:
            # Delete the source copy of the module
            shutil.rmtree(os.path.join(self.build_lib, self.main_package))

    def run_command(self, command):
        if command == "install":
            command_obj = self.distribution.get_command_obj("install_lib")
            setattr(command_obj, "install_dir", self.bdist_dir)

        result = super(bdist_nuitka, self).run_command(command)

        # After building, we are ready to build the extension module, from
        # the folder what "build_py" command has assembled for us.
        if command == "build":
            command_obj = self.distribution.get_command_obj(command)
            command_obj.ensure_finalized()

            self._buildPackage(os.path.abspath(command_obj.build_lib))

        return result

    def write_wheelfile(self, wheelfile_base, generator = None):
        if generator is None:
            from nuitka.Version import getNuitkaVersion
            generator = "Nuitka (%s)" % getNuitkaVersion()

        wheel.bdist_wheel.bdist_wheel.write_wheelfile(
            self,
            wheelfile_base = wheelfile_base,
            generator      = generator
        )
