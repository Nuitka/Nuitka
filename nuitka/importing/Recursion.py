#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from logging import debug, warning

from nuitka import ModuleRegistry, Options
from nuitka.freezer.BytecodeModuleFreezer import isFrozenModule
from nuitka.importing import ImportCache, Importing, StandardLibrary
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils import Utils


def recurseTo(module_package, module_filename, module_relpath, module_kind,
             reason):
    from nuitka.tree import Building

    if not ImportCache.isImportedModuleByPath(module_relpath):
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
            debug(
                "Recurse to import '%s' from %s. (%s)",
                module.getFullName(),
                module_relpath,
                reason
            )

            if module_kind == "py" and source_filename is not None:
                try:
                    Building.createModuleTree(
                        module      = module,
                        source_ref  = source_ref,
                        source_code = readSourceCodeFromFilename(
                            module_name     = module.getFullName(),
                            source_filename = source_filename
                        ),
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

            ImportCache.addImportedModule(
                module_relpath,
                module
            )

            is_added = True
        else:
            ImportCache.addImportedModule(
                module_relpath,
                ImportCache.getImportedModuleByName(module.getFullName())
            )

            module = ImportCache.getImportedModuleByName(
                module.getFullName()
            )

            is_added = False

        assert not module_relpath.endswith("/__init__.py"), module

        return module, is_added
    else:
        return ImportCache.getImportedModuleByPath(module_relpath), False


def decideRecursion(module_filename, module_name, module_package,
                    module_kind):
    # Many branches, which make decisions immediately, by returning
    # pylint: disable=R0911,R0912

    if module_kind == "shlib":
        if Options.isStandaloneMode():
            return True, "Shared library for inclusion."
        else:
            return False, "Shared library cannot be inspected."

    if module_package is None:
        full_name = module_name
    else:
        full_name = module_package + '.' + module_name

    if isFrozenModule(full_name):
        return False, "Module is frozen."

    no_case_modules = Options.getShallFollowInNoCase()

    for no_case_module in no_case_modules:
        if full_name == no_case_module:
            return (
                False,
                "Module listed explicitly to not recurse to."
            )

        if full_name.startswith(no_case_module + '.'):
            return (
                False,
                "Module in package listed explicitly to not recurse to."
            )

    any_case_modules = Options.getShallFollowModules()

    for any_case_module in any_case_modules:
        if full_name == any_case_module:
            return (
                True,
                "Module listed explicitly to recurse to."
            )

        if full_name.startswith(any_case_module + '.'):
            return (
                True,
                "Module in package listed explicitly to recurse to."
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
    return (
        None,
        "Default behavior, not recursing without request."
    )


def considerFilename(module_filename, module_package):
    assert module_package is None or \
           ( type(module_package) is str and module_package != "" )

    module_filename = Utils.normpath(module_filename)

    if Utils.isDir(module_filename):
        module_filename = Utils.abspath(module_filename)

        module_name = Utils.basename(module_filename)
        module_relpath = Utils.relpath(module_filename)

        return module_filename, module_relpath, module_name
    elif module_filename.endswith(".py"):
        module_name = Utils.basename(module_filename)[:-3]
        module_relpath = Utils.relpath(module_filename)

        return module_filename, module_relpath, module_name
    else:
        return None

def isSameModulePath(path1, path2):
    if Utils.basename(path1) == "__init__.py":
        path1 = Utils.dirname(path1)
    if Utils.basename(path2) == "__init__.py":
        path2 = Utils.dirname(path2)

    return Utils.abspath(path1) == Utils.abspath(path2)

def _checkPluginPath(plugin_filename, module_package):
    # Many branches, for the decision is very complex, pylint: disable=R0912

    debug(
        "Checking detail plug-in path '%s' '%s':",
        plugin_filename,
        module_package
    )

    plugin_info = considerFilename(
        module_package  = module_package,
        module_filename = plugin_filename
    )

    if plugin_info is not None:
        module, is_added = recurseTo(
            module_filename = plugin_info[0],
            module_relpath  = plugin_info[1],
            module_package  = module_package,
            module_kind     = "py",
            reason          = "Lives in plug-in directory."
        )

        if module:
            if not is_added:
                warning(
                    "Recursed to %s '%s' at '%s' twice.",
                    "package" if module.isPythonPackage() else "module",
                    module.getName(),
                    plugin_info[0]
                )

                if not isSameModulePath(module.getFilename(), plugin_info[0]):
                    warning(
                        "Duplicate ignored '%s'.",
                        plugin_info[1]
                    )

                    return

            debug(
                "Recursed to %s %s %s",
                module.getName(),
                module.getPackage(),
                module
            )

            if module.isPythonPackage():
                package_filename = module.getFilename()

                if Utils.isDir(package_filename):
                    # Must be a namespace package.
                    assert Utils.python_version >= 330

                    package_dir = package_filename

                    # Only include it, if it contains actual modules, which will
                    # recurse to this one and find it again.
                    useful = False
                else:
                    package_dir = Utils.dirname(package_filename)

                    # Real packages will always be included.
                    useful = True

                debug(
                    "Package directory %s",
                    package_dir
                )


                for sub_path, sub_filename in Utils.listDir(package_dir):
                    if sub_filename in ("__init__.py", "__pycache__"):
                        continue

                    assert sub_path != plugin_filename

                    if Importing.isPackageDir(sub_path) or \
                       sub_path.endswith(".py"):
                        _checkPluginPath(sub_path, module.getFullName())
            else:
                # Modules should always be included.
                useful = True

            if useful:
                ModuleRegistry.addRootModule(module)

        else:
            warning("Failed to include module from '%s'.", plugin_info[0])


def checkPluginPath(plugin_filename, module_package):
    debug(
        "Checking top level plug-in path %s %s",
        plugin_filename,
        module_package
    )

    plugin_info = considerFilename(
        module_package  = module_package,
        module_filename = plugin_filename
    )

    if plugin_info is not None:
        # File or package makes a difference, handle that
        if Utils.isFile(plugin_info[0]) or \
           Importing.isPackageDir(plugin_info[0]):
            _checkPluginPath(plugin_filename, module_package)
        elif Utils.isDir(plugin_info[0]):
            for sub_path, sub_filename in Utils.listDir(plugin_info[0]):
                assert sub_filename != "__init__.py"

                if Importing.isPackageDir(sub_path) or \
                   sub_path.endswith(".py"):
                    _checkPluginPath(sub_path, None)
        else:
            warning("Failed to include module from '%s'.", plugin_info[0])
    else:
        warning("Failed to recurse to directory '%s'.", plugin_filename)


def checkPluginFilenamePattern(pattern):
    import sys, glob

    debug(
        "Checking plug-in pattern '%s':",
        pattern,
    )

    if Utils.isDir(pattern):
        sys.exit("Error, pattern cannot be a directory name.")

    found = False

    for filename in glob.iglob(pattern):
        if filename.endswith(".pyc"):
            continue

        if not Utils.isFile(filename):
            continue

        found = True
        _checkPluginPath(filename, None)

    if not found:
        warning("Didn't match any files against pattern '%s'." % pattern)
