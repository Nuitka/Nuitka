#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Standard plug-in to find data files.

"""

import os
import pkgutil

from nuitka import Options
from nuitka.code_generation.ConstantCodes import addDistributionMetadataValue
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.plugins.YamlPluginBase import NuitkaYamlPluginBase
from nuitka.PythonFlavors import isDebianPackagePython
from nuitka.utils.Distributions import getDistribution
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    getFileList,
    resolveShellPatternToFilenames,
)


class NuitkaPluginDataFileCollector(NuitkaYamlPluginBase):
    plugin_name = "data-files"
    plugin_desc = "Include data files specified by package configuration files."
    plugin_category = "core"

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    @staticmethod
    def isAlwaysEnabled():
        return True

    def _considerDataFiles(self, module, data_file_config):
        # Many details and cases to deal with
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements

        module_name = module.getFullName()
        module_folder = module.getCompileTimeDirectory()

        target_dir = data_file_config.get("dest_path")

        # Default to near module or inside package folder.
        if target_dir is None:
            if (
                module.isCompiledPythonPackage()
                or module.isUncompiledPythonPackage()
                or module.isExtensionModulePackage()
            ):
                target_dir = module_name.asPath()
            else:
                package_name = module_name.getPackageName()

                if package_name is not None:
                    target_dir = module_name.getPackageName().asPath()
                else:
                    target_dir = "."

        patterns = data_file_config.get("patterns")
        if patterns is not None:
            if type(patterns) is not list or not patterns:
                self.sysexit(
                    "Error, requiring list below 'pattern' entry for '%s' entry."
                    % module_name
                )

            # TODO: Pattern should be data file kind potentially.
            for pattern in patterns:
                pattern = self.evaluateExpressionOrConstant(
                    full_name=module_name,
                    expression=pattern,
                    config_name="data file pattern for '%s'" % module_name,
                    extra_context=None,
                    single_value=True,
                )

                pattern = os.path.join(module_folder, pattern)

                for filename in resolveShellPatternToFilenames(pattern):
                    filename_base = os.path.relpath(filename, module_folder)

                    yield self.makeIncludedDataFile(
                        source_path=filename,
                        dest_path=os.path.normpath(
                            os.path.join(target_dir, filename_base)
                        ),
                        reason="package data for '%s'" % module_name.asString(),
                        tags="config",
                    )

        empty_dirs = data_file_config.get("empty_dirs")
        if empty_dirs is not None:
            if type(empty_dirs) is not list or not empty_dirs:
                self.sysexit(
                    "Error, requiring list below 'empty_dirs' entry for '%s' entry."
                    % module_name
                )

            for empty_dir in empty_dirs:
                yield self.makeIncludedEmptyDirectory(
                    dest_path=os.path.normpath(os.path.join(target_dir, empty_dir)),
                    reason="empty dir needed for %r" % module_name.asString(),
                    tags="config",
                )

        empty_dir_structures = data_file_config.get("empty_dir_structures")
        if empty_dir_structures is not None:
            if type(empty_dir_structures) is not list or not empty_dir_structures:
                self.sysexit(
                    "Error, requiring list below 'empty_dirs_structure' entry for '%s' entry."
                    % module_name
                )

            # TODO: This ignored config dest_path, which is unused, but not consistent.
            for included_data_file in self._getSubDirectoryFolders(
                module, sub_dirs=empty_dir_structures
            ):
                yield included_data_file

        dirs = data_file_config.get("dirs")
        if dirs is not None:
            if type(dirs) is not list or not dirs:
                self.sysexit(
                    "Error, requiring list below 'dirs' entry for '%s' entry."
                    % module_name
                )

            for data_dir in dirs:
                source_path = os.path.join(module_folder, data_dir)

                if os.path.isdir(source_path):
                    yield self.makeIncludedDataDirectory(
                        source_path=source_path,
                        dest_path=os.path.normpath(os.path.join(target_dir, data_dir)),
                        reason="package data directory '%s' for %r"
                        % (data_dir, module_name.asString()),
                        tags="config",
                    )

        raw_dirs = data_file_config.get("raw_dirs")
        if raw_dirs is not None:
            if type(raw_dirs) is not list or not raw_dirs:
                self.sysexit(
                    "Error, requiring list below 'raw_dirs' entry for '%s' entry."
                    % module_name
                )

            for raw_dir in raw_dirs:
                source_path = os.path.join(module_folder, raw_dir)

                if os.path.isdir(source_path):
                    yield self.makeIncludedDataDirectory(
                        source_path=source_path,
                        dest_path=os.path.normpath(os.path.join(target_dir, raw_dir)),
                        reason="package raw directory '%s' for %r"
                        % (raw_dir, module_name.asString()),
                        tags="config",
                        raw=True,
                    )

        include_pyi_file = data_file_config.get("include-pyi-file")

        if include_pyi_file == "yes":
            pyi_filename = changeFilenameExtension(
                path=module.getCompileTimeFilename(), extension=".pyi"
            )

            if os.path.exists(pyi_filename):
                if (
                    module.isCompiledPythonPackage()
                    or module.isUncompiledPythonPackage()
                ):
                    module_path = module_name.asPath()
                else:
                    module_path = os.path.dirname(module_name.asPath())

                yield self.makeIncludedDataFile(
                    source_path=pyi_filename,
                    dest_path=os.path.join(module_path, os.path.basename(pyi_filename)),
                    reason="runtime required '.pyi' file for '%s'"
                    % module_name.asString(),
                    tags="config",
                )

        distribution_names = data_file_config.get("include-metadata", ())

        for distribution_name in distribution_names:
            distribution = getDistribution(distribution_name)

            if distribution is not None:
                addDistributionMetadataValue(
                    distribution_name=distribution_name,
                    distribution=distribution,
                    reason="According to Yaml configuration 'include-metadata' for '%s'"
                    % module_name.asString(),
                )

    def considerDataFiles(self, module):
        full_name = module.getFullName()

        for entry in self.config.get(full_name, section="data-files"):
            if self.evaluateCondition(
                full_name=full_name, condition=entry.get("when", "True")
            ):
                for included_data_file in self._considerDataFiles(
                    module=module, data_file_config=entry
                ):
                    yield included_data_file

        # TODO: Until the data files are a list and support features to do similar, namely
        # to look up via package data interface "pkgutil.get_data" rather than file scan.
        if full_name == "lib2to3.pygram" and isDebianPackagePython():
            yield self.makeIncludedGeneratedDataFile(
                data=pkgutil.get_data("lib2to3", "Grammar.txt"),
                dest_path="lib2to3/Grammar.txt",
                reason="package data for '%s'" % full_name,
                tags="config",
            )

            yield self.makeIncludedGeneratedDataFile(
                data=pkgutil.get_data("lib2to3", "PatternGrammar.txt"),
                dest_path="lib2to3/PatternGrammar.txt",
                reason="package data for '%s'" % full_name,
                tags="config",
            )

    def _getSubDirectoryFolders(self, module, sub_dirs):
        """Get dirnames in given subdirectories of the module.

        Notes:
            All dirnames in folders below one of the sub_dirs are recursively
            retrieved and returned shortened to begin with the string of subdir.
        Args:
            module: module object
            sub_dirs: sub folder name(s) - tuple
        Returns:
            makeIncludedEmptyDirectory of found dirnames.
        """

        module_dir = module.getCompileTimeDirectory()
        file_list = []

        data_dirs = [os.path.join(module_dir, subdir) for subdir in sub_dirs]

        # Gather the full file list, probably makes no sense to include bytecode files
        file_list = sum(
            (
                getFileList(
                    data_dir, ignore_dirs=("__pycache__",), ignore_suffixes=(".pyc",)
                )
                for data_dir in data_dirs
            ),
            [],
        )

        if not file_list:
            msg = "No files or folders found for '%s' in subfolder(s) '%s' (%r)." % (
                module.getFullName(),
                sub_dirs,
                data_dirs,
            )
            self.warning(msg)

        is_package = (
            module.isCompiledPythonPackage() or module.isUncompiledPythonPackage()
        )

        # We need to preserve the package target path in the dist folder.
        if is_package:
            package_part = module.getFullName().asPath()
        else:
            package = module.getFullName().getPackageName()

            if package is None:
                package_part = ""
            else:
                package_part = package.asPath()

        item_set = OrderedSet()

        for f in file_list:
            target = os.path.join(package_part, os.path.relpath(f, module_dir))

            dir_name = os.path.dirname(target)
            item_set.add(dir_name)

        for dest_path in item_set:
            yield self.makeIncludedEmptyDirectory(
                dest_path=dest_path,
                reason="Subdirectories of module %s" % module.getFullName(),
                tags="config",
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
