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
""" Recursion into other modules.

"""

import glob
import os

from nuitka import ModuleRegistry, Options
from nuitka.importing import ImportCache, Importing, StandardLibrary
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.Tracing import recursion_logger
from nuitka.utils.FileOperations import listDir, relpath
from nuitka.utils.ModuleNames import ModuleName


def _recurseTo(module_package, module_filename, module_kind):
    from nuitka.tree import Building

    module, is_added = Building.buildModule(
        module_filename=module_filename,
        module_package=module_package,
        source_code=None,
        is_top=False,
        is_main=False,
        is_shlib=module_kind == "shlib",
        is_fake=False,
        hide_syntax_error=True,
    )

    ImportCache.addImportedModule(module)

    return module, is_added


def recurseTo(
    signal_change, module_package, module_filename, module_relpath, module_kind, reason
):
    if ImportCache.isImportedModuleByPath(module_relpath):
        try:
            module = ImportCache.getImportedModuleByPath(module_relpath, module_package)
        except KeyError:
            module = None
    else:
        module = None

    if module is None:
        module, added_flag = _recurseTo(
            module_package=module_package,
            module_filename=module_filename,
            module_kind=module_kind,
        )

        if added_flag and signal_change is not None:
            signal_change("new_code", module.getSourceReference(), reason)

    return module


def decideRecursion(module_filename, module_name, module_kind, extra_recursion=False):
    # Many branches, which make decisions immediately, by returning
    # pylint: disable=too-many-return-statements
    if module_name == "__main__":
        return False, "Main program is not recursed to again."

    plugin_decision = Plugins.onModuleEncounter(
        module_filename, module_name, module_kind
    )

    if plugin_decision is not None:
        return plugin_decision

    if module_kind == "shlib":
        if Options.isStandaloneMode():
            return True, "Extension module needed for standalone mode."
        else:
            return False, "Shared library cannot be inspected."

    no_case, reason = module_name.matchesToShellPatterns(
        patterns=Options.getShallFollowInNoCase()
    )

    if no_case:
        return (False, "Module %s instructed by user to not recurse to." % reason)

    any_case, reason = module_name.matchesToShellPatterns(
        patterns=Options.getShallFollowModules()
    )

    if any_case:
        return (True, "Module %s instructed by user to recurse to." % reason)

    if Options.shallFollowNoImports():
        return (False, "Requested to not recurse at all.")

    if StandardLibrary.isStandardLibraryPath(module_filename):
        return (
            Options.shallFollowStandardLibrary(),
            "Requested to %srecurse to standard library."
            % ("" if Options.shallFollowStandardLibrary() else "not "),
        )

    if Options.shallFollowAllImports():
        return (True, "Requested to recurse to all non-standard library modules.")

    # Means, we were not given instructions how to handle things.
    if extra_recursion:
        return (True, "Lives in plug-in directory.")

    if Options.shallMakeModule():
        return (False, "Making a module, not following any imports by default.")

    return (None, "Default behavior, not recursing without request.")


def considerFilename(module_filename):
    module_filename = os.path.normpath(module_filename)

    if os.path.isdir(module_filename):
        module_filename = os.path.abspath(module_filename)

        module_name = os.path.basename(module_filename)
        module_relpath = relpath(module_filename)

        return module_filename, module_relpath, module_name
    elif module_filename.endswith(".py"):
        module_name = os.path.basename(module_filename)[:-3]
        module_relpath = relpath(module_filename)

        return module_filename, module_relpath, module_name
    elif module_filename.endswith(".pyw"):
        module_name = os.path.basename(module_filename)[:-4]
        module_relpath = relpath(module_filename)

        return module_filename, module_relpath, module_name
    else:
        return None


def isSameModulePath(path1, path2):
    if os.path.basename(path1) == "__init__.py":
        path1 = os.path.dirname(path1)
    if os.path.basename(path2) == "__init__.py":
        path2 = os.path.dirname(path2)

    return os.path.abspath(path1) == os.path.abspath(path2)


def checkPluginSinglePath(plugin_filename, module_package):
    # Many branches, for the decision is very complex, pylint: disable=too-many-branches

    if Options.isShowInclusion():
        recursion_logger.info(
            "Checking detail plug-in path '%s' '%s':"
            % (plugin_filename, module_package)
        )

    module_name, module_kind = Importing.getModuleNameAndKindFromFilename(
        plugin_filename
    )

    module_name = ModuleName.makeModuleNameInPackage(module_name, module_package)

    if module_kind is not None:
        decision, reason = decideRecursion(
            module_filename=plugin_filename,
            module_name=module_name,
            module_kind=module_kind,
            extra_recursion=True,
        )

        if decision:
            module_relpath = relpath(plugin_filename)

            module = recurseTo(
                signal_change=None,
                module_filename=plugin_filename,
                module_relpath=module_relpath,
                module_package=module_package,
                module_kind=module_kind,
                reason=reason,
            )

            if module:
                if Options.isShowInclusion():
                    recursion_logger.info(
                        "Included '%s' as '%s'."
                        % (
                            module.getFullName(),
                            module,
                        )
                    )

                ImportCache.addImportedModule(module)

                if module.isCompiledPythonPackage():
                    package_filename = module.getFilename()

                    if os.path.isdir(package_filename):
                        # Must be a namespace package.
                        assert python_version >= 0x300

                        package_dir = package_filename

                        # Only include it, if it contains actual modules, which will
                        # recurse to this one and find it again.
                    else:
                        package_dir = os.path.dirname(package_filename)

                        # Real packages will always be included.
                        ModuleRegistry.addRootModule(module)

                    if Options.isShowInclusion():
                        recursion_logger.info("Package directory '%s'." % package_dir)

                    for sub_path, sub_filename in listDir(package_dir):
                        if sub_filename in ("__init__.py", "__pycache__"):
                            continue

                        assert sub_path != plugin_filename

                        if Importing.isPackageDir(sub_path) and not os.path.exists(
                            sub_path + ".py"
                        ):
                            checkPluginSinglePath(
                                sub_path, module_package=module.getFullName()
                            )
                        elif sub_path.endswith(".py"):
                            checkPluginSinglePath(
                                sub_path, module_package=module.getFullName()
                            )

                elif module.isCompiledPythonModule():
                    ModuleRegistry.addRootModule(module)
                elif module.isPythonShlibModule():
                    if Options.isStandaloneMode():
                        ModuleRegistry.addRootModule(module)

            else:
                recursion_logger.warning(
                    "Failed to include module from '%s'." % plugin_filename
                )


def checkPluginPath(plugin_filename, module_package):
    plugin_filename = os.path.normpath(plugin_filename)

    if Options.isShowInclusion():
        recursion_logger.info(
            "Checking top level plug-in path %s %s" % (plugin_filename, module_package)
        )

    plugin_info = considerFilename(module_filename=plugin_filename)

    if plugin_info is not None:
        # File or package makes a difference, handle that
        if os.path.isfile(plugin_info[0]) or Importing.isPackageDir(plugin_info[0]):
            checkPluginSinglePath(plugin_filename, module_package=module_package)
        elif os.path.isdir(plugin_info[0]):
            for sub_path, sub_filename in listDir(plugin_info[0]):
                assert sub_filename != "__init__.py"

                if Importing.isPackageDir(sub_path) or sub_path.endswith(".py"):
                    checkPluginSinglePath(sub_path, module_package=None)
        else:
            recursion_logger.warning(
                "Failed to include module from %r." % plugin_info[0]
            )
    else:
        recursion_logger.warning("Failed to recurse to directory %r." % plugin_filename)


def checkPluginFilenamePattern(pattern):
    if Options.isShowInclusion():
        recursion_logger.info("Checking plug-in pattern '%s':" % pattern)

    assert not os.path.isdir(pattern), pattern

    found = False

    for filename in glob.iglob(pattern):
        if filename.endswith(".pyc"):
            continue

        if not os.path.isfile(filename):
            continue

        found = True
        checkPluginSinglePath(filename, module_package=None)

    if not found:
        recursion_logger.warning("Didn't match any files against pattern %r." % pattern)
