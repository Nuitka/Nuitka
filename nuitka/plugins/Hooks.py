#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""This module gets setup by the plugins and provides hooks for use in Nuitka.

It does not contain much of any business logic, but only functions that will
be calling members "nuitka.plugins.Plugins" that is updated.

"""

Plugins = None


def onModuleSourceCode(module_name, source_filename, source_code):
    return Plugins.onModuleSourceCode(
        module_name=module_name,
        source_filename=source_filename,
        source_code=source_code,
    )


def onFrozenModuleBytecode(module_name, is_package, bytecode):
    return Plugins.onFrozenModuleBytecode(
        module_name=module_name, is_package=is_package, bytecode=bytecode
    )


def onBeforeCodeParsing():
    """Called before code parsing starts."""
    return Plugins.onBeforeCodeParsing()


def onModuleInitialSet():
    """Called after the initial module set is complete."""
    return Plugins.onModuleInitialSet()


def onModuleCompleteSet():
    """Called after the final module set is complete."""
    return Plugins.onModuleCompleteSet()


def getBuildDefinitions():
    """Called when Scons build definitions are collected."""
    return Plugins.getBuildDefinitions()


def onCompilationStartChecks():
    """Called before compilation starts, for checks."""
    return Plugins.onCompilationStartChecks()


def considerExtraDlls(module):
    """Called to add extra DLLs for a module."""
    return Plugins.considerExtraDlls(module=module)


def onStandaloneDistributionFinished(dist_dir, standalone_binary):
    """Called after the standalone distribution folder is prepared."""
    return Plugins.onStandaloneDistributionFinished(
        dist_dir=dist_dir, standalone_binary=standalone_binary
    )


def onFinalResult(filename):
    """Called after the final result has been created."""
    return Plugins.onFinalResult(filename=filename)


def getPluginsCacheContributionValues(module_name):
    """Let plugins provide values that need to be taken into account for caching."""

    return Plugins.getPluginsCacheContributionValues(module_name=module_name)


def writeExtraCodeFiles(onefile):
    return Plugins.writeExtraCodeFiles(onefile=onefile)


def onGeneratedSourceCode(source_dir, onefile):
    return Plugins.onGeneratedSourceCode(source_dir=source_dir, onefile=onefile)


def getPreprocessorSymbols():
    """Let plugins provide C defines to be used in compilation.

    Notes:
        The plugins can each contribute, but are hopefully using
        a namespace for their defines.

    Returns:
        OrderedDict(), where None value indicates no define value,
        i.e. "-Dkey=value" vs. "-Dkey"
    """
    # spell-checker: ignore Dkey
    return Plugins.getPreprocessorSymbols()


def getExtraIncludeDirectories():
    """Let plugins extra directories to use for C includes in compilation.

    Notes:
        The plugins can each contribute, but are hopefully not colliding,
        order will be plugin order.

    Returns:
        OrderedSet() of paths to include as well.
    """
    return Plugins.getExtraIncludeDirectories()


def getExtraLinkDirectories():
    """Let plugins extra directories to use for C linker in compilation.

    Notes:
        The plugins can each contribute, but are hopefully not colliding,
        order will be plugin order.

    Returns:
        OrderedSet() of paths to include as well.
    """
    return Plugins.getExtraLinkDirectories()


def getExtraLinkLibraries():
    """Let plugins extra libraries to use for C linker in compilation.

    Notes:
        The plugins can each contribute, but are hopefully not colliding,
        order will be plugin order.

    Returns:
        OrderedSet() of library names to link against.
    """
    return Plugins.getExtraLinkLibraries()


def decideCompilation(module_name):
    """Let plugins decide whether to C compile a module or include as bytecode.

    Notes:
        The decision is made by the first plugin not returning None.

    Returns:
        "compiled" (default) or "bytecode".
    """

    return Plugins.decideCompilation(module_name=module_name)


def decideRecompileExtensionModules(module_name):
    """Let plugins decide whether to re-compile an extension module from source code.

    Notes:
        The decision is made by the first plugin "never", otherwise a matching
        "yes" config wins, "no" is allowed to be overridden by command line options.
    """
    return Plugins.decideRecompileExtensionModules(module_name=module_name)


def decideAnnotations(module_name):
    return Plugins.decideAnnotations(module_name=module_name)


def decideAssertions(module_name):
    return Plugins.decideAssertions(module_name=module_name)


def decideDocStrings(module_name):
    return Plugins.decideDocStrings(module_name=module_name)


def onClassBodyParsing(provider, class_name, node):
    return Plugins.onClassBodyParsing(
        provider=provider, class_name=class_name, node=node
    )


def onFunctionBodyParsing(provider, function_name, body):
    return Plugins.onFunctionBodyParsing(
        provider=provider, function_name=function_name, body=body
    )


def onModuleEncounter(using_module_name, module_name, module_filename, module_kind):
    return Plugins.onModuleEncounter(
        using_module_name=using_module_name,
        module_name=module_name,
        module_filename=module_filename,
        module_kind=module_kind,
    )


def onModuleRecursion(
    module_name, module_filename, module_kind, using_module_name, source_ref, reason
):
    return Plugins.onModuleRecursion(
        module_name=module_name,
        module_filename=module_filename,
        module_kind=module_kind,
        using_module_name=using_module_name,
        source_ref=source_ref,
        reason=reason,
    )


def onModuleUsageLookAhead(module_name, module_filename, module_kind):
    return Plugins.onModuleUsageLookAhead(
        module_name=module_name,
        module_filename=module_filename,
        module_kind=module_kind,
    )


def onModuleDiscovered(module):
    return Plugins.onModuleDiscovered(module=module)


def getModuleSysPathAdditions(module_name):
    """Provide a list of directories, that should be considered in 'PYTHONPATH' when this module is used.

    Args:
        module_name: name of a package or module
    Returns:
        iterable of paths
    """

    return Plugins.getModuleSysPathAdditions(module_name=module_name)


def considerImplicitImports(module):
    """Let plugins add implicit imports for a module.

    Args:
        module: module object
    Returns:
        iterable of module names
    """
    return Plugins.considerImplicitImports(module=module)


def suppressUnknownImportWarning(importing, source_ref, module_name):
    """Let plugins decide whether to suppress import warnings for an unknown module.

    Notes:
        If all plugins return False or None, the return will be False, else True.
    Args:
        importing: the module which is importing "module_name"
        source_ref: pointer to file source code or bytecode
        module_name: the module to be imported
    returns:
        True or False (default)
    """
    return Plugins.suppressUnknownImportWarning(
        importing=importing, source_ref=source_ref, module_name=module_name
    )


def considerDataFiles(module):
    return Plugins.considerDataFiles(module=module)


def onDataFileTags(included_datafile):
    return Plugins.onDataFileTags(included_datafile=included_datafile)


def onDllTags(included_entry_point):
    return Plugins.onDllTags(included_entry_point=included_entry_point)


def deriveModuleConstantsBlobName(data_filename):
    return Plugins.deriveModuleConstantsBlobName(data_filename=data_filename)


def getExtraConstantDefaultPopulation():
    return Plugins.getExtraConstantDefaultPopulation()


def encodeDataComposerName(name):
    return Plugins.encodeDataComposerName(name=name)


def onDataComposerRun():
    return Plugins.onDataComposerRun()


def onDataComposerResult(blob_filename):
    return Plugins.onDataComposerResult(blob_filename=blob_filename)


def getModuleSpecificDllPaths(module_name):
    """Provide a list of directories, where DLLs should be searched for this package (or module).

    Args:
        module_name: name of a package or module, for which the DLL path addition applies.

    """
    return Plugins.getModuleSpecificDllPaths(module_name=module_name)


def isAcceptableMissingDLL(package_name, filename):
    return Plugins.isAcceptableMissingDLL(package_name=package_name, filename=filename)


def decideAllowOutsideDependencies(module_name):
    return Plugins.decideAllowOutsideDependencies(module_name=module_name)


def removeDllDependencies(dll_filename, dll_filenames):
    """Create list of removable shared libraries by scanning through the plugins.

    Args:
        dll_filename: shared library filename
        dll_filenames: list of shared library filenames
    Returns:
        list of removable files
    """
    return Plugins.removeDllDependencies(
        dll_filename=dll_filename, dll_filenames=dll_filenames
    )


def onCopiedDLLs(dist_dir, standalone_entry_points):
    """Lets the plugins modify entry points on disk."""
    return Plugins.onCopiedDLLs(
        dist_dir=dist_dir, standalone_entry_points=standalone_entry_points
    )


def onOnefileFinished(filename):
    """Let plugins post-process the onefile executable in onefile mode"""
    return Plugins.onOnefileFinished(filename=filename)


def onBootstrapBinary(filename):
    """Let plugins add to bootstrap binary in some way"""
    return Plugins.onBootstrapBinary(filename=filename)


def getPackageExtraScanPaths(package_name, package_dir):
    return Plugins.getPackageExtraScanPaths(
        package_name=package_name, package_dir=package_dir
    )


def getUncompiledDecoratorNames():
    """Return a tuple of decorator names that should cause the function to be uncompiled.

    Returns:
        tuple of strings
    """
    return Plugins.getUncompiledDecoratorNames()


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
