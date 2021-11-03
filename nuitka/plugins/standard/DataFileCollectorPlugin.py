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
""" Standard plug-in to find data files.

"""

import os

from nuitka import Options
from nuitka.containers.oset import OrderedSet
from nuitka.freezer.IncludedDataFiles import (
    makeIncludedDataDirectory,
    makeIncludedDataFile,
    makeIncludedEmptyDirectories,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import (
    getFileList,
    resolveShellPatternToFilenames,
)
from nuitka.utils.Yaml import parsePackageYaml


def _getSubDirectoryFolders(module, subdirs):
    """Get dirnames in given subdirs of the module.

    Notes:
        All dirnames in folders below one of the subdirs are recursively
        retrieved and returned shortened to begin with the string of subdir.
    Args:
        module: module object
        subdirs: sub folder name(s) - tuple
    Returns:
        makeIncludedEmptyDirectories of found dirnames.
    """

    module_dir = module.getCompileTimeDirectory()
    file_list = []

    data_dirs = [os.path.join(module_dir, subdir) for subdir in subdirs]

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
        msg = "No files or folders found for '%s' in subfolder(s) %r (%r)." % (
            module.getFullName(),
            subdirs,
            data_dirs,
        )
        NuitkaPluginDataFileCollector.warning(msg)

    is_package = module.isCompiledPythonPackage() or module.isUncompiledPythonPackage()

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

    return makeIncludedEmptyDirectories(
        source_path=module_dir,
        dest_paths=item_set,
        reason="Subdirectories of module %s" % module.getFullName(),
    )


class NuitkaPluginDataFileCollector(NuitkaPluginBase):
    plugin_name = "data-files"

    def __init__(self):
        self.config = parsePackageYaml(__package__, "data-files.yml")

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    @staticmethod
    def isAlwaysEnabled():
        return True

    def considerDataFiles(self, module):
        # Many cases to deal with, pylint: disable=too-many-branches

        module_name = module.getFullName()
        module_folder = module.getCompileTimeDirectory()

        config = self.config.get(module_name)

        if config:
            target_dir = config.get("dest_path")

            # Default to near module or inside package folder.
            if target_dir is None:
                if (
                    module.isCompiledPythonPackage()
                    or module.isUncompiledPythonPackage()
                ):
                    target_dir = module_name.asPath()
                else:
                    package_name = module_name.getPackageName()

                    if package_name is not None:
                        target_dir = module_name.getPackageName().asPath()
                    else:
                        target_dir = "."

            patterns = config.get("patterns")
            if patterns is not None:
                if type(patterns) is not list or not patterns:
                    self.sysexit(
                        "Error, requiring list below 'pattern' entry for '%s' entry."
                        % module_name
                    )

                # TODO: Pattern should be data file kind potentially.
                for pattern in patterns:
                    pattern = os.path.join(module_folder, pattern)

                    for filename in resolveShellPatternToFilenames(pattern):
                        yield makeIncludedDataFile(
                            source_path=filename,
                            dest_path=os.path.normpath(
                                os.path.join(target_dir, os.path.basename(filename))
                            ),
                            reason="package data for %r" % module_name.asString(),
                        )

            empty_dirs = config.get("empty_dirs")
            if empty_dirs is not None:
                if type(empty_dirs) is not list or not empty_dirs:
                    self.sysexit(
                        "Error, requiring list below 'empty_dirs' entry for '%s' entry."
                        % module_name
                    )

                yield makeIncludedEmptyDirectories(
                    source_path=target_dir,
                    dest_paths=tuple(
                        os.path.join(target_dir, empty_dir) for empty_dir in empty_dirs
                    ),
                    reason="empty dir needed for %r" % module_name.asString(),
                )

            empty_dir_structures = config.get("empty_dir_structures")
            if empty_dir_structures is not None:
                if type(empty_dir_structures) is not list or not empty_dir_structures:
                    self.sysexit(
                        "Error, requiring list below 'empty_dirs_structure' entry for '%s' entry."
                        % module_name
                    )

                # TODO: This ignored dest_path, which is unused, but not consistent.
                yield _getSubDirectoryFolders(module, empty_dir_structures)

            dirs = config.get("dirs")
            if dirs is not None:
                if type(dirs) is not list or not dirs:
                    self.sysexit(
                        "Error, requiring list below 'empty_dirs_structure' entry for '%s' entry."
                        % module_name
                    )

                for data_dir in dirs:
                    source_path = os.path.join(module_folder, data_dir)

                    if os.path.isdir(source_path):
                        yield makeIncludedDataDirectory(
                            source_path=source_path,
                            dest_path=os.path.join(target_dir, data_dir),
                            reason="package data directory for %r"
                            % module_name.asString(),
                        )
