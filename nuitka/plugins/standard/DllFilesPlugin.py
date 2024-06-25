#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to tell Nuitka about DLLs needed for standalone imports.

When DLLs are imported, we cannot see this and need to be told that. This
encodes the knowledge we have for various modules. Feel free to add to this
and submit patches to make it more complete.
"""

import fnmatch
import os
import sys

from nuitka.Options import isStandaloneMode
from nuitka.plugins.YamlPluginBase import NuitkaYamlPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.Distributions import (
    getDistributionFromModuleName,
    getDistributionName,
    isDistributionSystemPackage,
)
from nuitka.utils.FileOperations import (
    listDllFilesFromDirectory,
    listExeFilesFromDirectory,
)
from nuitka.utils.SharedLibraries import getPyWin32Dir
from nuitka.utils.Utils import isFreeBSD, isLinux, isMacOS, isWin32Windows


class NuitkaPluginDllFiles(NuitkaYamlPluginBase):
    plugin_name = "dll-files"

    plugin_desc = "Include DLLs as per package configuration files."

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def isRelevant():
        return isStandaloneMode()

    def _handleDllConfigFromFilenames(self, dll_config, full_name, dest_path):
        # A lot of details here, pylint: disable=too-many-locals

        # The "when" is at that level too for these.
        if not self.evaluateCondition(
            full_name=full_name, condition=dll_config.get("when", "True")
        ):
            return

        config_name = "module '%s' DLL config" % full_name

        relative_path = self.evaluateExpressionOrConstant(
            full_name=full_name,
            expression=dll_config.get("relative_path", "."),
            config_name=config_name,
            extra_context=None,
            single_value=True,
        )

        module_filename = self.locateModule(full_name)

        if os.path.isdir(module_filename):
            module_directory = module_filename

            if dest_path is None:
                dest_path = os.path.join(full_name.asPath(), relative_path)
        else:
            module_directory = os.path.dirname(module_filename)

            if dest_path is None:
                dest_path = os.path.join(full_name.asPath(), "..", relative_path)

        dll_dir = os.path.normpath(os.path.join(module_directory, relative_path))

        if os.path.exists(dll_dir):
            exe = dll_config.get("executable", "no") == "yes"

            suffixes = tuple(
                self.evaluateExpressionOrConstant(
                    full_name=full_name,
                    expression=suffix,
                    config_name=config_name,
                    extra_context=None,
                    single_value=True,
                ).lstrip(".")
                for suffix in dll_config.get("suffixes", ())
            )

            prefixes = tuple(
                self.evaluateExpressionOrConstant(
                    full_name=full_name,
                    expression=prefix,
                    config_name=config_name,
                    extra_context=None,
                    single_value=True,
                ).lstrip(".")
                for prefix in dll_config.get("prefixes", ())
            )

            for prefix in prefixes:
                if exe:
                    for exe_filename, filename in listExeFilesFromDirectory(
                        dll_dir, prefix=prefix, suffixes=suffixes
                    ):
                        yield self.makeExeEntryPoint(
                            source_path=exe_filename,
                            dest_path=os.path.normpath(
                                os.path.join(
                                    dest_path,
                                    filename,
                                )
                            ),
                            module_name=full_name,
                            package_name=full_name,
                            reason="Yaml config of '%s'" % full_name.asString(),
                        )
                else:
                    for dll_filename, filename in listDllFilesFromDirectory(
                        dll_dir, prefix=prefix, suffixes=suffixes
                    ):
                        yield self.makeDllEntryPoint(
                            source_path=dll_filename,
                            dest_path=os.path.normpath(
                                os.path.join(
                                    dest_path,
                                    filename,
                                )
                            ),
                            module_name=full_name,
                            package_name=full_name,
                            reason="Yaml config of '%s'" % full_name.asString(),
                        )

    def _handleDllConfigByCodeResult(self, filename, full_name, dest_path, executable):
        # Expecting absolute paths internally for DLL sources.
        filename = os.path.abspath(filename)

        if dest_path is None:
            module_filename = self.locateModule(full_name)

            if os.path.isdir(module_filename):
                dest_path = full_name.asPath()
            else:
                dest_path = os.path.join(full_name.asPath(), "..")

            dest_path = os.path.join(
                dest_path,
                os.path.relpath(filename, os.path.dirname(module_filename)),
            )
        else:
            dest_path = os.path.join(
                dest_path,
                os.path.basename(filename),
            )

        dest_path = os.path.normpath(dest_path)

        if executable:
            yield self.makeExeEntryPoint(
                source_path=filename,
                dest_path=dest_path,
                module_name=full_name,
                package_name=full_name,
                reason="Yaml config of '%s'" % full_name.asString(),
            )
        else:
            yield self.makeDllEntryPoint(
                source_path=filename,
                dest_path=dest_path,
                module_name=full_name,
                package_name=full_name,
                reason="Yaml config of '%s'" % full_name.asString(),
            )

    def _handleDllConfigByCode(self, dll_config, full_name, dest_path, count):
        # The "when" is at that level too for these.
        if not self.evaluateCondition(
            full_name=full_name, condition=dll_config.get("when", "True")
        ):
            return

        setup_codes = dll_config.get("setup_code")
        filename_code = dll_config.get("filename_code")

        filename = self.queryRuntimeInformationMultiple(
            "%s_%s" % (full_name.asString(), count),
            setup_codes=setup_codes,
            values=(("filename", filename_code),),
        ).filename

        if not filename:
            self.warning(
                """\
DLL configuration by filename code for '%s' did not give a result. Either \
conditions are missing, or this version of the module needs treatment added."""
                % full_name.asString()
            )

        if type(filename) in (tuple, list):
            filenames = filename
        else:
            filenames = (filename,)

        for filename in filenames:
            yield self._handleDllConfigByCodeResult(
                filename=filename,
                full_name=full_name,
                dest_path=dest_path,
                executable=dll_config.get("executable", "no") == "yes",
            )

    def _handleDllConfig(self, dll_config, full_name, count):
        dest_path = dll_config.get("dest_path")

        found = False

        if "by_code" in dll_config:
            for result in self._handleDllConfigByCode(
                dll_config=dll_config.get("by_code"),
                full_name=full_name,
                dest_path=dest_path,
                count=count,
            ):
                yield result

            found = True

        if "from_filenames" in dll_config:
            for result in self._handleDllConfigFromFilenames(
                dll_config=dll_config.get("from_filenames"),
                full_name=full_name,
                dest_path=dest_path,
            ):
                yield result

            found = True

        if not found:
            self.sysexit(
                "Unsupported DLL config for module '%s' encountered."
                % full_name.asString()
            )

    def getExtraDlls(self, module):
        # TODO: Need to move all code here into configuration file usage.

        full_name = module.getFullName()

        # Checking for config, but also allowing fall through for cases that have to
        # have some code still here.
        found = 0

        for count, dll_config in enumerate(
            self.config.get(full_name, section="dlls"), start=1
        ):
            if self.evaluateCondition(
                full_name=full_name, condition=dll_config.get("when", "True")
            ):
                for dll_entry_point in self._handleDllConfig(
                    dll_config=dll_config,
                    full_name=full_name,
                    count=count,
                ):
                    yield dll_entry_point
                    found += 1

        if found > 0:
            self.reportFileCount(full_name, found)

        # TODO: This is legacy code, ideally moved to yaml config over time.
        if (
            full_name == "uuid"
            and (isLinux() or isFreeBSD())
            and python_version < 0x300
        ):
            uuid_dll_path = self.locateDLL("uuid")

            if uuid_dll_path is not None:
                yield self.makeDllEntryPoint(
                    source_path=uuid_dll_path,
                    dest_path=os.path.basename(uuid_dll_path),
                    module_name=full_name,
                    package_name=None,
                    reason="needed by uuid package",
                )
        elif full_name == "iptc" and isLinux():
            import iptc.util  # pylint: disable=I0021,import-error

            xtwrapper_dll = iptc.util.find_library("xtwrapper")[0]
            xtwrapper_dll_path = xtwrapper_dll._name  # pylint: disable=protected-access

            yield self.makeDllEntryPoint(
                source_path=xtwrapper_dll_path,
                dest_path=os.path.basename(xtwrapper_dll_path),
                module_name=full_name,
                package_name=None,
                reason="needed by 'iptc'",
            )
        elif full_name == "coincurve._libsecp256k1" and isWin32Windows():
            yield self.makeDllEntryPoint(
                source_path=os.path.join(
                    module.getCompileTimeDirectory(), "libsecp256k1.dll"
                ),
                dest_path=os.path.join(full_name.getPackageName(), "libsecp256k1.dll"),
                module_name=full_name,
                package_name=full_name.getPackageName(),
                reason="needed by 'coincurve._libsecp256k1'",
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
                "win32ui",
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
                            source_path=pythoncom_dll_path,
                            dest_path=pythoncom_filename,
                            module_name=full_name,
                            package_name=None,
                            reason="needed by '%s'" % full_name.asString(),
                        )

    def getModuleSpecificDllPaths(self, module_name):
        for _config_module_name, near_module_name in self.getYamlConfigItemSet(
            module_name=module_name,
            section="import-hacks",
            item_name="find-dlls-near-module",
            decide_relevant=None,
            recursive=True,
        ):
            module_filename = self.locateModule(near_module_name)

            if module_filename is not None:
                if os.path.isfile(module_filename):
                    package_directory = os.path.dirname(module_filename)
                else:
                    package_directory = module_filename

                yield package_directory

                if isMacOS():
                    # Some packages for macOS put their DLLs in a ".dylibs" folder,
                    # consider those as well, spell-checker: ignore dylibs
                    dylib_directory = os.path.join(package_directory, ".dylibs")

                    if os.path.isdir(package_directory):
                        yield dylib_directory

    def isAcceptableMissingDLL(self, package_name, dll_basename):
        if package_name is None:
            return None

        # Config is to be attached to top level package.
        package_name = package_name.getTopLevelPackageName()

        for entry in self.config.get(package_name, section="import-hacks"):
            if self.evaluateCondition(
                full_name=package_name, condition=entry.get("when", "True")
            ):
                result = self._isAcceptableMissingDLL(
                    config=entry, dll_basename=dll_basename
                )

                if result is not None:
                    return result

        return None

    @staticmethod
    def _isAcceptableMissingDLL(config, dll_basename):
        for config_dll_name in config.get("acceptable-missing-dlls", ()):
            if fnmatch.fnmatch(dll_basename, config_dll_name):
                return True

        return None

    def decideAllowOutsideDependencies(self, module_name):
        distribution = None

        while 1:
            for entry in self.config.get(module_name, section="import-hacks"):
                if self.evaluateCondition(
                    full_name=module_name, condition=entry.get("when", "True")
                ):
                    if "package-system-dlls" in entry:
                        return entry["package-system-dlls"] == "yes"

            if distribution is None:
                distribution = getDistributionFromModuleName(module_name)

            module_name = module_name.getPackageName()
            if not module_name:
                break

        if distribution is None:
            return None

        if not isDistributionSystemPackage(getDistributionName(distribution)):
            return False
        else:
            return None


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
