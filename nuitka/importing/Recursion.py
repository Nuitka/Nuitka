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
""" Recursion into other modules.

"""

import fnmatch
import glob
import marshal
import os
import sys
from logging import debug, info, warning

from nuitka import ModuleRegistry, Options
from nuitka.importing import ImportCache, Importing, StandardLibrary
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils.FileOperations import listDir, relpath


def logRecursion(*args):
    if Options.isShowInclusion():
        info(*args)
    else:
        debug(*args)


def matchesModuleNameToPatterns(module_name, patterns):
    for pattern in patterns:
        if module_name == pattern:
            return True, "is exact match of %r" % pattern
        elif module_name.startswith(pattern):
            return True, "is package content of %r" % pattern
        elif fnmatch.fnmatch(module_name, pattern):
            return True, "matches pattern %r" % pattern
        elif fnmatch.fnmatch(module_name, pattern + ".*"):
            return True, "is package content of match to pattern %r" % pattern

    return False, None


def _recurseTo(module_package, module_filename, module_relpath, module_kind,
              reason):
    from nuitka.tree import Building
    from nuitka.nodes.ModuleNodes import makeUncompiledPythonModule

    module, source_ref, source_filename = Building.decideModuleTree(
        filename = module_filename,
        package  = module_package,
        is_top   = False,
        is_main  = False,
        is_shlib = module_kind == "shlib"
    )

    # Check if the module name is known. In order to avoid duplicates,
    # learn the new filename, and continue build if its not.
    if not ImportCache.isImportedModuleByName(module.getFullName()):
        logRecursion(
            "Recurse to import '%s' from '%s'. (%s)",
            module.getFullName(),
            module_relpath,
            reason
        )

        if module_kind == "py" and source_filename is not None:
            try:
                source_code = readSourceCodeFromFilename(
                    module_name     = module.getFullName(),
                    source_filename = source_filename
                )

                Building.createModuleTree(
                    module      = module,
                    source_ref  = source_ref,
                    source_code = source_code,
                    is_main     = False
                )
            except (SyntaxError, IndentationError) as e:
                if module_filename not in Importing.warned_about:
                    Importing.warned_about.add(module_filename)

                    warning(
                        """\
Cannot recurse to import module '%s' (%s) because of '%s'""",
                        module_relpath,
                        module_filename,
                        e.__class__.__name__
                    )

                return None, False
            except Building.CodeTooComplexCode:
                if module_filename not in Importing.warned_about:
                    Importing.warned_about.add(module_filename)

                    warning(
                        """\
Cannot recurse to import module '%s' (%s) because code is too complex.""",
                        module_relpath,
                        module_filename,
                    )

                    if Options.isStandaloneMode():
                        module = makeUncompiledPythonModule(
                            module_name   = module.getFullName(),
                            filename      = module_filename,
                            bytecode      = marshal.dumps(
                                compile(
                                    source_code,
                                    module_filename,
                                    "exec",
                                    dont_inherit = True
                                )
                            ),
                            is_package    = module.isCompiledPythonPackage(),
                            user_provided = True,
                            technical     = False
                        )

                        ModuleRegistry.addUncompiledModule(module)

                return None, False

        ImportCache.addImportedModule(module)

        is_added = True
    else:
        module = ImportCache.getImportedModuleByName(
            module.getFullName()
        )

        is_added = False

    return module, is_added


def recurseTo(module_package, module_filename, module_relpath, module_kind,
              reason):
    if ImportCache.isImportedModuleByPath(module_relpath):
        module = ImportCache.getImportedModuleByPath(module_relpath)

        if module.getCompileTimeFilename().endswith("__init__.py") and \
           module.getPackage() != module_package:
            module = None
    else:
        module = None

    if module is None:
        return _recurseTo(
            module_package  = module_package,
            module_filename = module_filename,
            module_relpath  = module_relpath,
            module_kind     = module_kind,
            reason          = reason
        )
    else:
        return module, False


def decideRecursion(module_filename, module_name, module_package, module_kind,
                    extra_recursion = False):
    # Many branches, which make decisions immediately, by returning
    # pylint: disable=too-many-return-statements
    Plugins.onModuleEncounter(
        module_filename,
        module_name,
        module_package,
        module_kind
    )

    if module_kind == "shlib":
        if Options.isStandaloneMode():
            return True, "Shared library for inclusion."
        else:
            return False, "Shared library cannot be inspected."

    if module_package is None:
        full_name = module_name
    else:
        full_name = module_package + '.' + module_name

    no_case, reason = matchesModuleNameToPatterns(
        module_name = full_name,
        patterns    = Options.getShallFollowInNoCase()
    )

    if no_case:
        return (
            False,
            "Module %s instructed by user to not recurse to." % reason
        )

    any_case, reason = matchesModuleNameToPatterns(
        module_name = full_name,
        patterns    = Options.getShallFollowModules()
    )

    if any_case:
        return (
            True,
            "Module %s instructed by user to recurse to." % reason
        )

    if Options.shallFollowNoImports():
        return (
            False,
            "Requested to not recurse at all."
        )

    if StandardLibrary.isStandardLibraryPath(module_filename):
        return (
            Options.shallFollowStandardLibrary(),
            "Requested to %srecurse to standard library." % (
                "" if Options.shallFollowStandardLibrary() else "not "
            )
        )

    if Options.shallFollowAllImports():
        return (
            True,
            "Requested to recurse to all non-standard library modules."
        )

    # Means, we were not given instructions how to handle things.
    if extra_recursion:
        return (
            True,
            "Lives in plug-in directory."
        )
    else:
        return (
            None,
            "Default behavior, not recursing without request."
        )


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


def _checkPluginPath(plugin_filename, module_package):
    # Many branches, for the decision is very complex, pylint: disable=too-many-branches

    debug(
        "Checking detail plug-in path '%s' '%s':",
        plugin_filename,
        module_package
    )

    module_name, module_kind = Importing.getModuleNameAndKindFromFilename(plugin_filename)

    if module_kind is not None:
        decision, reason = decideRecursion(
            module_filename = plugin_filename,
            module_name     = module_name,
            module_package  = module_package,
            module_kind     = module_kind,
            extra_recursion = True
        )

        if decision:
            module_relpath = relpath(plugin_filename)

            module, is_added = recurseTo(
                module_filename = plugin_filename,
                module_relpath  = module_relpath,
                module_package  = module_package,
                module_kind     = "py",
                reason          = reason
            )

            if module:
                if not is_added:
                    warning(
                        "Recursed to %s '%s' at '%s' twice.",
                        "package" if module.isCompiledPythonPackage() else "module",
                        module.getName(),
                        plugin_filename
                    )

                    if not isSameModulePath(module.getFilename(), plugin_filename):
                        warning(
                            "Duplicate '%s' of '%s' ignored .",
                            plugin_filename,
                            module.getFilename()
                        )

                        return

                debug(
                    "Recursed to %s %s %s",
                    module.getName(),
                    module.getPackage(),
                    module
                )

                ImportCache.addImportedModule(module)

                if module.isCompiledPythonPackage():
                    package_filename = module.getFilename()

                    if os.path.isdir(package_filename):
                        # Must be a namespace package.
                        assert python_version >= 330

                        package_dir = package_filename

                        # Only include it, if it contains actual modules, which will
                        # recurse to this one and find it again.
                    else:
                        package_dir = os.path.dirname(package_filename)

                        # Real packages will always be included.
                        ModuleRegistry.addRootModule(module)

                    debug(
                        "Package directory %s",
                        package_dir
                    )

                    for sub_path, sub_filename in listDir(package_dir):
                        if sub_filename in ("__init__.py", "__pycache__"):
                            continue

                        assert sub_path != plugin_filename

                        if Importing.isPackageDir(sub_path) or \
                           sub_path.endswith(".py"):
                            _checkPluginPath(sub_path, module.getFullName())

                elif module.isCompiledPythonModule():
                    ModuleRegistry.addRootModule(module)

            else:
                warning("Failed to include module from '%s'.", plugin_filename)


def checkPluginPath(plugin_filename, module_package):
    plugin_filename = os.path.normpath(plugin_filename)

    debug(
        "Checking top level plug-in path %s %s",
        plugin_filename,
        module_package
    )

    plugin_info = considerFilename(
        module_filename = plugin_filename
    )

    if plugin_info is not None:
        # File or package makes a difference, handle that
        if os.path.isfile(plugin_info[0]) or \
           Importing.isPackageDir(plugin_info[0]):
            _checkPluginPath(plugin_filename, module_package)
        elif os.path.isdir(plugin_info[0]):
            for sub_path, sub_filename in listDir(plugin_info[0]):
                assert sub_filename != "__init__.py"

                if Importing.isPackageDir(sub_path) or \
                   sub_path.endswith(".py"):
                    _checkPluginPath(sub_path, None)
        else:
            warning("Failed to include module from '%s'.", plugin_info[0])
    else:
        warning("Failed to recurse to directory '%s'.", plugin_filename)


def checkPluginFilenamePattern(pattern):
    debug(
        "Checking plug-in pattern '%s':",
        pattern,
    )

    if os.path.isdir(pattern):
        sys.exit("Error, pattern cannot be a directory name.")

    found = False

    for filename in glob.iglob(pattern):
        if filename.endswith(".pyc"):
            continue

        if not os.path.isfile(filename):
            continue

        found = True
        _checkPluginPath(filename, None)

    if not found:
        warning("Didn't match any files against pattern '%s'." % pattern)
