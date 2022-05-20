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
""" Standard plug-in to tell Nuitka about DLLs needed for standalone imports.

When DLLs are imported, we cannot see this and need to be told that. This
encodes the knowledge we have for various modules. Feel free to add to this
and submit patches to make it more complete.
"""

import os
import sys

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import listDllFilesFromDirectory
from nuitka.utils.SharedLibraries import getPyWin32Dir
from nuitka.utils.Utils import isLinux, isWin32Windows
from nuitka.utils.Yaml import parsePackageYaml


class NuitkaPluginDllFiles(NuitkaPluginBase):
    plugin_name = "dll-files"

    def __init__(self):
        self.config = parsePackageYaml(__package__, "dll-files.yml")

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def isRelevant():
        return isStandaloneMode()

    def _handleDllConfig(self, dll_config, full_name, count):
        config_found = False

        if "include_from_code" in dll_config:
            config_found = True

            setup_codes = dll_config.get("setup_code")
            dll_filename_code = dll_config.get("dll_filename_code")
            dest_path = dll_config.get("dest_path")

            dll_filename = self.queryRuntimeInformationMultiple(
                "%s_%s" % (full_name.asString().replace(".", "_"), count),
                setup_codes=setup_codes,
                values=(("dll_filename", dll_filename_code),),
            ).dll_filename

            module_filename = self.locateModule(full_name)

            yield self.makeDllEntryPoint(
                source_path=dll_filename,
                dest_path=os.path.join(
                    dest_path,
                    os.path.relpath(dll_filename, os.path.dirname(module_filename)),
                ),
                package_name=full_name,
            )

        if "include_from_filenames" in dll_config:
            config_found = True

            module_filename = self.locateModule(full_name)

            if os.path.isdir(module_filename):
                module_directory = module_filename
            else:
                module_directory = os.path.dirname(module_filename)

            dll_dir = dll_config.get("dir", ".")
            dll_dir = os.path.normpath(os.path.join(module_directory, dll_dir))

            dest_path = dll_config.get("dest_path")

            for pattern in dll_config.get("patterns"):
                for dll_filename, filename in listDllFilesFromDirectory(
                    dll_dir, prefix=pattern
                ):
                    yield self.makeDllEntryPoint(
                        source_path=dll_filename,
                        dest_path=os.path.join(
                            dest_path,
                            filename,
                        ),
                        package_name=full_name,
                    )

        if not config_found:
            self.sysexit(
                "Unsupported config for module '%s' encountered." % full_name.asString()
            )

    def _handleDllConfigs(self, config, full_name):
        dll_configs = config.get("dlls")

        if dll_configs:
            if type(dll_configs) is not list or not dll_configs:
                self.sysexit(
                    "Error, requiring list below 'dlls' entry for '%s' entry."
                    % full_name
                )

            found = 0

            for count, dll_config in enumerate(dll_configs, start=1):
                for dll_entry_point in self._handleDllConfig(
                    dll_config=dll_config, full_name=full_name, count=count
                ):
                    yield dll_entry_point
                    found += 1

            self.reportFileCount(full_name, found)

    def getExtraDlls(self, module):
        full_name = module.getFullName()

        # Checking for config, but also allowing fall through for cases that have to
        # have some code still here.
        config = self.config.get(full_name)
        if config:
            for dll_entry_point in self._handleDllConfigs(
                config=config, full_name=full_name
            ):
                yield dll_entry_point

        # TODO: This is legacy code, ideally moved to yaml config over time.
        if full_name == "uuid" and isLinux():
            uuid_dll_path = self.locateDLL("uuid")

            if uuid_dll_path is not None:
                yield self.makeDllEntryPoint(
                    uuid_dll_path, os.path.basename(uuid_dll_path), None
                )
        elif full_name == "iptc" and isLinux():
            import iptc.util  # pylint: disable=I0021,import-error

            xtwrapper_dll = iptc.util.find_library("xtwrapper")[0]
            xtwrapper_dll_path = xtwrapper_dll._name  # pylint: disable=protected-access

            yield self.makeDllEntryPoint(
                xtwrapper_dll_path, os.path.basename(xtwrapper_dll_path), None
            )
        elif full_name == "coincurve._libsecp256k1" and isWin32Windows():
            yield self.makeDllEntryPoint(
                os.path.join(module.getCompileTimeDirectory(), "libsecp256k1.dll"),
                os.path.join(full_name.getPackageName(), "libsecp256k1.dll"),
                full_name.getPackageName(),
            )
        # TODO: This should be its own plugin.
        elif (
            full_name
            in (
                "pythoncom",
                "win32api",
                "win32clipboard",
                "win32console",
                "win32cred",
                "win32crypt",
                "win32event",
                "win32evtlog",
                "win32file",
                "win32gui",
                "win32help",
                "win32inet",
                "win32job",
                "win32lz",
                "win32net",
                "win32pdh",
                "win32pipe",
                "win32print",
                "win32process",
                "win32profile",
                "win32ras",
                "win32security",
                "win32service",
                "win32trace",
                "win32transaction",
                "win32ts",
                "win32wnet",
            )
            and isWin32Windows()
        ):
            pywin_dir = getPyWin32Dir()

            if pywin_dir is not None:
                for dll_name in "pythoncom", "pywintypes":

                    pythoncom_filename = "%s%d%d.dll" % (
                        dll_name,
                        sys.version_info[0],
                        sys.version_info[1],
                    )
                    pythoncom_dll_path = os.path.join(pywin_dir, pythoncom_filename)

                    if os.path.exists(pythoncom_dll_path):
                        yield self.makeDllEntryPoint(
                            pythoncom_dll_path, pythoncom_filename, None
                        )
