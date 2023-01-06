#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

import distutils.command.build  # pylint: disable=I0021,import-error,no-name-in-module
import distutils.command.install  # pylint: disable=I0021,import-error,no-name-in-module
import os
import sys

import wheel.bdist_wheel  # pylint: disable=I0021,import-error,no-name-in-module

from nuitka.__past__ import Iterable, unicode
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import (
    addMainScriptDirectory,
    decideModuleSourceRef,
    locateModule,
)
from nuitka.Tracing import wheel_logger
from nuitka.utils.Execution import check_call
from nuitka.utils.ModuleNames import ModuleName


def setupNuitkaDistutilsCommands(dist, keyword, value):
    # If the user project setup.py includes the key "build_with_nuitka=True" all
    # build operations (build, bdist_wheel, install etc) will run via Nuitka.
    # pylint: disable=unused-argument

    if not value:
        return

    dist.cmdclass = dist.cmdclass or {}  # Ensure is a dict
    dist.cmdclass["build"] = build
    dist.cmdclass["install"] = install
    dist.cmdclass["bdist_wheel"] = bdist_nuitka


# Class name enforced by distutils, must match the command name.
# Required by distutils, used as command name, pylint: disable=invalid-name
class build(distutils.command.build.build):

    # pylint: disable=attribute-defined-outside-init
    def run(self):
        wheel_logger.info(
            "Specified packages: %s." % self.distribution.packages, style="blue"
        )
        wheel_logger.info(
            "Specified modules: %s." % self.distribution.py_modules, style="blue"
        )

        self.compile_packages = self.distribution.packages or []
        self.py_modules = self.distribution.py_modules or []

        # Determine
        self.script_module_names = OrderedSet()
        if self.distribution.entry_points is not None:
            for group, script_specs in self.distribution.entry_points.items():
                for script_spec in script_specs:
                    try:
                        script_module_name = (
                            script_spec.split("=", 1)[1].strip().split(":")[0]
                        )
                    except Exception as e:  # Catch all the things, pylint: disable=broad-except
                        wheel_logger.info(
                            "Problem parsing '%s' script specification in '%s' due to %s"
                            % (script_spec, group, e)
                        )

                    self.script_module_names.add(ModuleName(script_module_name))

        if not self.compile_packages and not self.py_modules:
            wheel_logger.sysexit(
                "No modules or packages specified, aborting. Did you provide packages in 'setup.cfg' or 'setup.py'?"
            )

        # Python2 does not allow super on this old style class.
        distutils.command.build.build.run(self)

        self._build(os.path.abspath(self.build_lib))

    def _find_to_build(self):
        """
        Helper for _build
        Returns list containing bool (is_package) and module_names

        Algorithm for finding distinct packages:
        1) Take minimum package
        2) Find related packages that start with this name
        3) Add this to the list to return, then repeat steps 1 & 2
           until no more packages exist

        """

        builds = []

        # Namespace packages can use / rather than dots.
        py_packages = [
            ModuleName(m.replace("/", ".")) for m in sorted(set(self.compile_packages))
        ]
        py_modules = [ModuleName(m) for m in sorted(set(self.py_modules))]

        for script_module_name in self.script_module_names:
            script_module_filename = locateModule(
                module_name=script_module_name, parent_package=None, level=0
            )[1]

            # Decide package or module.
            (
                _main_added,
                is_package,
                _is_namespace,
                _source_ref,
                _source_filename,
            ) = decideModuleSourceRef(
                filename=script_module_filename,
                module_name=script_module_name,
                is_main=False,
                is_fake=False,
                logger=wheel_logger,
            )

            if is_package:
                py_packages.append(script_module_name)
            else:
                py_modules.append(script_module_name)

        # Plain modules if they are not in packages to build.
        builds.extend(
            (False, current_module)
            for current_module in py_modules
            if not current_module.hasOneOfNamespaces(py_packages)
        )

        while py_packages:
            current_package = min(py_packages)

            py_packages = [
                p for p in py_packages if not p.hasNamespace(current_package)
            ]
            builds.append((True, current_package))

        return builds

    @staticmethod
    def _parseOptionsEntry(option, value):
        option = "--" + option.lstrip("-")

        if type(value) is tuple and len(value) == 2 and value[0] == "setup.py":
            value = value[1]

        if value is None or value == "":
            yield option
        elif isinstance(value, bool):
            yield "--" + ("no" if not value else "") + option.lstrip("-")
        elif isinstance(value, Iterable) and not isinstance(
            value, (unicode, bytes, str)
        ):
            for val in value:
                yield "%s=%s" % (option, val)
        else:
            yield "%s=%s" % (option, value)

    def _build(self, build_lib):
        # High complexity, pylint: disable=too-many-branches,too-many-locals

        # Nuitka wants the main package by filename, probably we should stop
        # needing that.

        old_dir = os.getcwd()
        os.chdir(build_lib)

        if self.distribution.package_dir and "" in self.distribution.package_dir:
            main_package_dir = self.distribution.package_dir.get("")
        else:
            main_package_dir = os.path.abspath(old_dir)

        # Search in the build directory preferably.
        addMainScriptDirectory(main_package_dir)

        for is_package, module_name in self._find_to_build():
            module_name, main_filename, _module_kind, finding = locateModule(
                module_name=module_name,
                parent_package=None,
                level=0,
            )

            package = module_name.getPackageName()

            # Check expectations, e.g. do not compile built-in modules.
            assert finding == "absolute", finding

            if package is not None:
                output_dir = os.path.join(build_lib, package.asPath())
            else:
                output_dir = build_lib

            command = [
                sys.executable,
                "-m",
                "nuitka",
                "--module",
                "--enable-plugin=pylint-warnings",
                "--output-dir=%s" % output_dir,
                "--nofollow-import-to=*.tests",
                "--remove-output",
            ]

            if is_package:
                command.append("--include-package=%s" % module_name)

            else:
                command.append("--include-module=%s" % module_name)

            toml_filename = os.environ.get("NUITKA_TOML_FILE")
            if toml_filename:
                # Import toml parser like "build" module does.
                try:
                    from tomli import loads as toml_loads
                except ImportError:
                    from toml import loads as toml_loads

                # Cannot use FileOperations.getFileContents() here, because of non-Nuitka process
                # pylint: disable=unspecified-encoding

                with open(toml_filename) as toml_file:
                    toml_options = toml_loads(toml_file.read())

                for option, value in toml_options.get("nuitka", {}).items():
                    command.extend(self._parseOptionsEntry(option, value))

            # Process any extra options from setuptools
            if "nuitka" in self.distribution.command_options:
                for option, value in self.distribution.command_options[
                    "nuitka"
                ].items():
                    command.extend(self._parseOptionsEntry(option, value))

            command.append(main_filename)

            # Adding traces for clarity
            wheel_logger.info(
                "Building: '%s' with command '%s'" % (module_name.asString(), command),
                style="blue",
            )
            check_call(command, cwd=build_lib)
            wheel_logger.info(
                "Finished compilation of '%s'." % module_name.asString(), style="green"
            )

            for root, _, filenames in os.walk(build_lib):
                for filename in filenames:
                    fullpath = os.path.join(root, filename)

                    if fullpath.lower().endswith((".py", ".pyw", ".pyc", ".pyo")):
                        os.unlink(fullpath)

        self.build_lib = build_lib

        os.chdir(old_dir)


# Required by distutils, used as command name, pylint: disable=invalid-name
class install(distutils.command.install.install):

    # pylint: disable=attribute-defined-outside-init
    def finalize_options(self):
        distutils.command.install.install.finalize_options(self)
        # Ensure the purelib folder is not used
        self.install_lib = self.install_platlib


# Required by distutils, used as command name, pylint: disable=invalid-name
class bdist_nuitka(wheel.bdist_wheel.bdist_wheel):
    def initialize_options(self):
        # Register the command class overrides above
        dist = self.distribution
        dist.cmdclass = dist.cmdclass or {}  # Ensure is a dict
        dist.cmdclass["build"] = build
        dist.cmdclass["install"] = install

        wheel.bdist_wheel.bdist_wheel.initialize_options(self)

    # pylint: disable=attribute-defined-outside-init
    def finalize_options(self):
        wheel.bdist_wheel.bdist_wheel.finalize_options(self)
        # Force module to use correct platform in name
        self.root_is_pure = False
        self.plat_name_supplied = self.plat_name is not None

    def write_wheelfile(self, wheelfile_base, generator=None):
        if generator is None:
            from nuitka.Version import getNuitkaVersion

            generator = "Nuitka (%s)" % getNuitkaVersion()

        wheel.bdist_wheel.bdist_wheel.write_wheelfile(
            self, wheelfile_base=wheelfile_base, generator=generator
        )
