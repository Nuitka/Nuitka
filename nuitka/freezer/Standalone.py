#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Pack and copy files for standalone mode.

This is expected to work for macOS, Windows, and Linux. Other things like
FreeBSD are also very welcome, but might break with time and need your
help.
"""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Errors import NuitkaForbiddenDLLEncounter
from nuitka.importing.Importing import (
    getPythonUnpackedSearchPath,
    locateModule,
)
from nuitka.importing.StandardLibrary import isStandardLibraryPath
from nuitka.Options import (
    isShowProgress,
    shallNotStoreDependsExeCachedResults,
    shallNotUseDependsExeCachedResults,
)
from nuitka.plugins.Plugins import Plugins
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.PythonFlavors import (
    getHomebrewInstallPath,
    isAnacondaPython,
    isHomebrewPython,
    isMSYS2MingwPython,
)
from nuitka.PythonVersions import getSystemPrefixPath
from nuitka.Tracing import general, inclusion_logger
from nuitka.utils.FileOperations import areInSamePaths, isFilenameBelowPath
from nuitka.utils.SharedLibraries import copyDllFile, setSharedLibraryRPATH
from nuitka.utils.Signing import addMacOSCodeSignature
from nuitka.utils.Timing import TimerReport
from nuitka.utils.Utils import (
    getOS,
    isDebianBasedLinux,
    isMacOS,
    isPosixWindows,
    isWin32Windows,
)

from .DllDependenciesMacOS import (
    detectBinaryPathDLLsMacOS,
    fixupBinaryDLLPathsMacOS,
)
from .DllDependenciesPosix import detectBinaryPathDLLsPosix
from .DllDependenciesWin32 import detectBinaryPathDLLsWin32
from .IncludedEntryPoints import (
    addIncludedEntryPoint,
    getIncludedExtensionModule,
    makeDllEntryPoint,
)


def checkFreezingModuleSet():
    """Check the module set for troubles.

    Typically Linux OS specific packages must be avoided, e.g. Debian packaging
    does make sure the packages will not run on other OSes.
    """
    # Cyclic dependency
    from nuitka import ModuleRegistry

    problem_modules = OrderedSet()

    if isDebianBasedLinux():
        message = "Standalone with Python package from Debian installation may not be working."
        mnemonic = "debian-dist-packages"

        def checkModulePath(module):
            module_filename = module.getCompileTimeFilename()
            module_filename_parts = module_filename.split("/")

            if (
                "dist-packages" in module_filename_parts
                and "local" not in module_filename_parts
            ):
                module_name = module.getFullName()

                package_name = module_name.getTopLevelPackageName()

                if package_name is not None:
                    problem_modules.add(package_name)
                else:
                    problem_modules.add(module_name)

    else:
        checkModulePath = None
        message = None
        mnemonic = None

    # We intend for other platforms to join, e.g. Fedora, etc. but currently
    # only Debian is done.
    if checkModulePath is not None:
        for module in ModuleRegistry.getDoneModules():
            if not module.getFullName().isFakeModuleName():
                checkModulePath(module)

    if problem_modules:
        general.info("Using Debian packages for '%s'." % ",".join(problem_modules))
        general.warning(message=message, mnemonic=mnemonic)


def _detectBinaryDLLs(
    is_main_executable,
    source_dir,
    original_filename,
    binary_filename,
    package_name,
    use_path,
    use_cache,
    update_cache,
):
    """Detect the DLLs used by a binary.

    Using "ldd" (Linux), "depends.exe" (Windows), or
    "otool" (macOS) the list of used DLLs is retrieved.
    """

    if getOS() in ("Linux", "NetBSD", "FreeBSD", "OpenBSD") or isPosixWindows():
        return detectBinaryPathDLLsPosix(
            dll_filename=original_filename,
            package_name=package_name,
            original_dir=os.path.dirname(original_filename),
        )
    elif isWin32Windows():
        with TimerReport(
            message="Running 'depends.exe' for %s took %%.2f seconds" % binary_filename,
            decider=isShowProgress,
        ):
            return detectBinaryPathDLLsWin32(
                is_main_executable=is_main_executable,
                source_dir=source_dir,
                original_dir=os.path.dirname(original_filename),
                binary_filename=binary_filename,
                package_name=package_name,
                use_path=use_path,
                use_cache=use_cache,
                update_cache=update_cache,
            )
    elif isMacOS():
        return detectBinaryPathDLLsMacOS(
            original_dir=os.path.dirname(original_filename),
            binary_filename=original_filename,
            package_name=package_name,
            keep_unresolved=False,
            recursive=True,
        )
    else:
        # Support your platform above.
        assert False, getOS()


def copyDllsUsed(dist_dir, standalone_entry_points):
    # This is complex, because we also need to handle OS specifics.

    # Only do ones not ignored
    copy_standalone_entry_points = [
        standalone_entry_point
        for standalone_entry_point in standalone_entry_points[1:]
        if not standalone_entry_point.kind.endswith("_ignored")
    ]
    main_standalone_entry_point = standalone_entry_points[0]

    if isMacOS():
        fixupBinaryDLLPathsMacOS(
            binary_filename=os.path.join(
                dist_dir, main_standalone_entry_point.dest_path
            ),
            package_name=main_standalone_entry_point.package_name,
            original_location=main_standalone_entry_point.source_path,
            standalone_entry_points=standalone_entry_points,
        )

        # After dependency detection, we can change the RPATH for macOS main
        # binary.
        setSharedLibraryRPATH(
            os.path.join(dist_dir, standalone_entry_points[0].dest_path), "$ORIGIN"
        )

    setupProgressBar(
        stage="Copying used DLLs",
        unit="DLL",
        total=len(copy_standalone_entry_points),
    )

    for standalone_entry_point in copy_standalone_entry_points:
        reportProgressBar(standalone_entry_point.dest_path)

        copyDllFile(
            source_path=standalone_entry_point.source_path,
            dist_dir=dist_dir,
            dest_path=standalone_entry_point.dest_path,
            executable=standalone_entry_point.executable,
        )

        if isMacOS():
            fixupBinaryDLLPathsMacOS(
                binary_filename=os.path.join(
                    dist_dir, standalone_entry_point.dest_path
                ),
                package_name=standalone_entry_point.package_name,
                original_location=standalone_entry_point.source_path,
                standalone_entry_points=standalone_entry_points,
            )

    closeProgressBar()

    # Add macOS code signature
    if isMacOS():
        addMacOSCodeSignature(
            filenames=[
                os.path.join(dist_dir, standalone_entry_point.dest_path)
                for standalone_entry_point in [main_standalone_entry_point]
                + copy_standalone_entry_points
            ]
        )

    Plugins.onCopiedDLLs(
        dist_dir=dist_dir, standalone_entry_points=copy_standalone_entry_points
    )


_excluded_system_dlls = set()


def _reduceToPythonPath(used_dll_paths):
    """Remove DLLs outside of python path."""
    inside_paths = getPythonUnpackedSearchPath()

    if isAnacondaPython():
        inside_paths.insert(0, getSystemPrefixPath())

    if isHomebrewPython():
        inside_paths.insert(0, getHomebrewInstallPath())

    if isMSYS2MingwPython():
        inside_paths.insert(0, os.path.join(getSystemPrefixPath(), "bin"))

    def decideInside(dll_filename):
        return any(
            isFilenameBelowPath(path=inside_path, filename=dll_filename)
            for inside_path in inside_paths
        )

    kept_used_dll_paths = OrderedSet()
    removed_dll_paths = OrderedSet()

    for dll_filename in used_dll_paths:
        if decideInside(dll_filename):
            kept_used_dll_paths.add(dll_filename)
        else:
            if dll_filename not in _excluded_system_dlls:
                _excluded_system_dlls.add(dll_filename)
                inclusion_logger.info("Not including system DLL '%s'" % dll_filename)

            removed_dll_paths.add(dll_filename)

    return kept_used_dll_paths, removed_dll_paths


_removed_dll_usages = {}


def getRemovedUsedDllsInfo():
    return _removed_dll_usages.items()


def _detectUsedDLLs(standalone_entry_point, source_dir):
    # TODO: We are handling a bunch of cases here, but also some special cases,
    # that should live elsewhere.
    # pylint: disable=too-many-branches,too-many-locals

    if standalone_entry_point.module_name is not None:
        module_name, module_filename, _kind, finding = locateModule(
            standalone_entry_point.module_name, parent_package=None, level=0
        )

        # TODO: How can this be None at all.
        if module_filename is not None and isStandardLibraryPath(module_filename):
            allow_outside_dependencies = True
        else:
            allow_outside_dependencies = Plugins.decideAllowOutsideDependencies(
                standalone_entry_point.module_name
            )
    else:
        allow_outside_dependencies = False

    binary_filename = standalone_entry_point.source_path
    try:
        used_dll_paths = _detectBinaryDLLs(
            is_main_executable=standalone_entry_point.kind == "executable",
            source_dir=source_dir,
            original_filename=standalone_entry_point.source_path,
            binary_filename=binary_filename,
            package_name=standalone_entry_point.package_name,
            use_path=allow_outside_dependencies,
            use_cache=not shallNotUseDependsExeCachedResults(),
            update_cache=not shallNotStoreDependsExeCachedResults(),
        )
    except NuitkaForbiddenDLLEncounter:
        inclusion_logger.info(
            "Not including due to forbidden DLL '%s'." % binary_filename
        )
    except (RuntimeError, Exception) as e:
        inclusion_logger.warning(
            """\
Error, cannot detect used DLLs for DLL '%s' in package '%s' due to: %s"""
            % (binary_filename, standalone_entry_point.package_name, str(e))
        )

        raise
    else:
        # Plugins generally decide if they allow dependencies from the outside
        # based on the package name.

        if standalone_entry_point.module_name is not None and used_dll_paths:
            module_name, module_filename, _kind, finding = locateModule(
                standalone_entry_point.module_name, parent_package=None, level=0
            )

            # Make sure we are not surprised here.
            assert (
                module_name == standalone_entry_point.module_name
            ), standalone_entry_point.module_name
            assert finding == "absolute", standalone_entry_point.module_name

            if not allow_outside_dependencies:
                used_dll_paths, removed_dll_paths = _reduceToPythonPath(used_dll_paths)

                if removed_dll_paths:
                    _removed_dll_usages[standalone_entry_point] = (
                        "no outside dependencies allowed for '%s'"
                        % standalone_entry_point.module_name,
                        removed_dll_paths,
                    )

        # Lets be sure of this
        assert type(used_dll_paths) is OrderedSet, type(used_dll_paths)

        # Allow plugins can prevent inclusion, this may discard things from
        # used_dlls through its return value.
        removed_dlls = Plugins.removeDllDependencies(
            dll_filename=binary_filename, dll_filenames=OrderedSet(used_dll_paths)
        )
        used_dll_paths = used_dll_paths - removed_dlls

        for used_dll_path in used_dll_paths:
            extension_standalone_entry_point = getIncludedExtensionModule(used_dll_path)
            if extension_standalone_entry_point is not None:
                # Sometimes an extension module is used like a DLL, make sure to
                # remove it as a DLL then, there is no value in keeping those. Need
                # to keep it's destination path from that extension module then.
                dest_path = extension_standalone_entry_point.dest_path
            elif (
                standalone_entry_point.package_name is not None
                and standalone_entry_point.package_name.hasOneOfNamespaces(
                    "openvino",
                    "av",
                )
                and areInSamePaths(binary_filename, used_dll_path)
            ):
                # TODO: If used by a DLL from the same folder, put it there,
                # otherwise top level, but for now this is limited to a few cases
                # where required that way (openvino) or known to be good only (av),
                # because it broke other things. spell-checker: ignore openvino

                dest_path = os.path.normpath(
                    os.path.join(
                        os.path.dirname(standalone_entry_point.dest_path),
                        os.path.basename(used_dll_path),
                    )
                )
            else:
                dest_path = os.path.basename(used_dll_path)

            dll_entry_point = makeDllEntryPoint(
                logger=inclusion_logger,
                source_path=used_dll_path,
                dest_path=dest_path,
                module_name=standalone_entry_point.module_name,
                package_name=standalone_entry_point.package_name,
                reason="Used by '%s'" % standalone_entry_point.dest_path,
            )

            addIncludedEntryPoint(dll_entry_point)


def detectUsedDLLs(standalone_entry_points, source_dir):
    setupProgressBar(
        stage="Detecting used DLLs",
        unit="DLL",
        total=len(standalone_entry_points),
    )

    for standalone_entry_point in standalone_entry_points:
        reportProgressBar(standalone_entry_point.dest_path)

        _detectUsedDLLs(
            standalone_entry_point=standalone_entry_point, source_dir=source_dir
        )

    closeProgressBar()


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
