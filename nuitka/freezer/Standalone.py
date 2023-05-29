#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Pack and copy files for standalone mode.

This is expected to work for macOS, Windows, and Linux. Other things like
FreeBSD are also very welcome, but might break with time and need your
help.
"""

import marshal
import os
import pkgutil
import sys

from nuitka import Options, SourceCodeReferences
from nuitka.Bytecodes import compileSourceToBytecode
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Errors import NuitkaForbiddenDLLEncounter
from nuitka.importing import ImportCache
from nuitka.importing.Importing import getPythonUnpackedSearchPath
from nuitka.importing.StandardLibrary import (
    getStandardLibraryPaths,
    isStandardLibraryNoAutoInclusionModule,
    isStandardLibraryPath,
    scanStandardLibraryPath,
)
from nuitka.nodes.ModuleNodes import (
    PythonExtensionModule,
    makeUncompiledPythonModule,
)
from nuitka.plugins.Plugins import Plugins
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.PythonVersions import python_version
from nuitka.Tracing import general, inclusion_logger, printError
from nuitka.tree.SourceHandling import (
    readSourceCodeFromFilenameWithInformation,
)
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import (
    areInSamePaths,
    areSamePaths,
    isFilenameBelowPath,
)
from nuitka.utils.ModuleNames import ModuleName
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
from .DllDependenciesWin32 import detectBinaryPathDLLsWindowsDependencyWalker
from .IncludedEntryPoints import addIncludedEntryPoint, makeDllEntryPoint


def loadCodeObjectData(bytecode_filename):
    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    with open(bytecode_filename, "rb") as f:
        return f.read()[8 if str is bytes else 16 :]


module_names = set()


def _detectedPreCompiledFile(filename, module_name, result, user_provided, technical):
    if filename.endswith(".pyc") and os.path.isfile(filename[:-1]):
        return _detectedSourceFile(
            filename=filename[:-1],
            module_name=module_name,
            result=result,
            user_provided=user_provided,
            technical=technical,
        )

    if module_name in module_names:
        return

    if Options.isShowInclusion():
        inclusion_logger.info(
            "Freezing module '%s' (from '%s')." % (module_name, filename)
        )

    uncompiled_module = makeUncompiledPythonModule(
        module_name=module_name,
        bytecode=loadCodeObjectData(bytecode_filename=filename),
        is_package="__init__" in filename,
        filename=filename,
        user_provided=user_provided,
        technical=technical,
    )

    ImportCache.addImportedModule(uncompiled_module)

    result.append(uncompiled_module)
    module_names.add(module_name)


def _detectedSourceFile(filename, module_name, result, user_provided, technical):
    if module_name in module_names:
        return

    if module_name == "collections.abc":
        _detectedSourceFile(
            filename=filename,
            module_name=ModuleName("_collections_abc"),
            result=result,
            user_provided=user_provided,
            technical=technical,
        )

    (
        source_code,
        _original_code,
        _contributing_plugins,
    ) = readSourceCodeFromFilenameWithInformation(module_name, filename)

    if module_name == "site":
        if source_code.startswith("def ") or source_code.startswith("class "):
            source_code = "\n" + source_code

        source_code = """\
__file__ = (__nuitka_binary_dir + '%s%s') if '__nuitka_binary_dir' in dict(__builtins__ ) else '<frozen>';%s""" % (
            os.path.sep,
            os.path.basename(filename),
            source_code,
        )

        # Debian stretch site.py
        source_code = source_code.replace(
            "PREFIXES = [sys.prefix, sys.exec_prefix]", "PREFIXES = []"
        )

    if Options.isShowInclusion():
        inclusion_logger.info(
            "Freezing module '%s' (from '%s')." % (module_name, filename)
        )

    is_package = os.path.basename(filename) == "__init__.py"

    # Plugins can modify source code again, this time knowing it will be frozen.
    source_code = Plugins.onFrozenModuleSourceCode(
        module_name=module_name, is_package=is_package, source_code=source_code
    )

    # TODO: Not yet handling SyntaxError here, although plugins might cause them.
    bytecode = compileSourceToBytecode(
        source_code=source_code,
        filename=module_name.replace(".", os.path.sep) + ".py",
    )

    # Plugins can modify bytecode code:
    bytecode = Plugins.onFrozenModuleBytecode(
        module_name=module_name, is_package=is_package, bytecode=bytecode
    )

    uncompiled_module = makeUncompiledPythonModule(
        module_name=module_name,
        bytecode=marshal.dumps(bytecode),
        is_package=is_package,
        filename=filename,
        user_provided=user_provided,
        technical=technical,
    )

    ImportCache.addImportedModule(uncompiled_module)

    result.append(uncompiled_module)
    module_names.add(module_name)


def _detectedExtensionModule(filename, module_name, result, technical):
    # That is not a shared library, but looks like one.
    if module_name == "__main__":
        return

    # Extension modules are not tracked outside of standalone
    # mode.
    if not Options.isStandaloneMode():
        return

    # Avoid duplicates
    if module_name in module_names:
        return

    source_ref = SourceCodeReferences.fromFilename(filename=filename)

    extension_module = PythonExtensionModule(
        module_name=module_name, technical=technical, source_ref=source_ref
    )

    ImportCache.addImportedModule(extension_module)

    module_names.add(module_name)
    result.append(extension_module)


def _detectImports(command, user_provided, technical):
    # This is pretty complicated stuff, with variants to deal with.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # Print statements for stuff to show, the modules loaded.
    if python_version >= 0x300:
        command += """
print("\\n".join(sorted(
    "import %s # sourcefile %s" % (module.__name__, module.__file__)
    for module in sys.modules.values()
    if getattr(module, "__file__", None) not in (None, "<frozen>"
))), file = sys.stderr)"""

    reduced_path = [
        path_element
        for path_element in sys.path
        if not areSamePaths(path_element, ".")
        if not areSamePaths(
            path_element, os.path.dirname(sys.modules["__main__"].__file__)
        )
    ]

    # Make sure the right import path (the one Nuitka binary is running with)
    # is used.
    command = (
        "import sys; sys.path = %s; sys.real_prefix = sys.prefix;" % repr(reduced_path)
    ) + command

    if str is not bytes:
        command = command.encode("utf8")

    _stdout, stderr, exit_code = executeProcess(
        command=(
            sys.executable,
            "-s",
            "-S",
            "-v",
            "-c",
            "import sys;exec(sys.stdin.read())",
        ),
        stdin=command,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )

    assert type(stderr) is bytes

    # Don't let errors here go unnoticed.
    if exit_code != 0:
        # An error by the user pressing CTRL-C should not lead to the below output.
        if b"KeyboardInterrupt" in stderr:
            general.sysexit("Pressed CTRL-C while detecting early imports.")

        general.warning("There is a problem with detecting imports, CPython said:")
        for line in stderr.split(b"\n"):
            printError(line)
        general.sysexit("Error, please report the issue with above output.")

    result = []

    detections = []

    for line in stderr.replace(b"\r", b"").split(b"\n"):
        if line.startswith(b"import "):
            parts = line.split(b" # ", 2)

            module_name = parts[0].split(b" ", 2)[1]
            origin = parts[1].split()[0]

            if python_version >= 0x300:
                module_name = module_name.decode("utf8")

            module_name = ModuleName(module_name)

            if origin == b"precompiled":
                # This is a ".pyc" file that was imported, even before we have a
                # chance to do anything, we need to preserve it.
                filename = parts[1][len(b"precompiled from ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append((module_name, 3, "precompiled", filename))
            elif origin == b"from" and python_version < 0x300:
                filename = parts[1][len(b"from ") :]
                if str is not bytes:  # For consistency, and maybe later reuse
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                if filename.endswith(".py"):
                    detections.append((module_name, 2, "sourcefile", filename))
                else:
                    assert False
            elif origin == b"sourcefile":
                filename = parts[1][len(b"sourcefile ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                if filename.endswith(".py"):
                    detections.append((module_name, 2, "sourcefile", filename))
                elif filename.endswith(".pyc"):
                    detections.append((module_name, 3, "precompiled", filename))
                elif not filename.endswith("<frozen>"):
                    # Python3 started lying in "__name__" for the "_decimal"
                    # calls itself "decimal", which then is wrong and also
                    # clashes with "decimal" proper
                    if python_version >= 0x300 and module_name == "decimal":
                        module_name = ModuleName("_decimal")

                    detections.append((module_name, 2, "extension", filename))
            elif origin == b"dynamically":
                # Shared library in early load, happens on RPM based systems and
                # or self compiled Python installations.
                filename = parts[1][len(b"dynamically loaded from ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append((module_name, 1, "extension", filename))

    for module_name, _priority, kind, filename in sorted(detections):
        if isStandardLibraryNoAutoInclusionModule(module_name):
            continue

        if kind == "extension":
            _detectedExtensionModule(
                filename=filename,
                module_name=module_name,
                result=result,
                technical=technical,
            )
        elif kind == "precompiled":
            _detectedPreCompiledFile(
                filename=filename,
                module_name=module_name,
                result=result,
                user_provided=user_provided,
                technical=technical,
            )
        elif kind == "sourcefile":
            _detectedSourceFile(
                filename=filename,
                module_name=module_name,
                result=result,
                user_provided=user_provided,
                technical=technical,
            )
        else:
            assert False, kind

    return result


def _detectEarlyImports():
    encoding_names = [
        m[1] for m in pkgutil.iter_modules(sys.modules["encodings"].__path__)
    ]

    if os.name != "nt":
        # On posix systems, and posix Python variants on Windows, these won't
        # work and fail to import.
        for encoding_name in ("mbcs", "cp65001", "oem"):
            if encoding_name in encoding_names:
                encoding_names.remove(encoding_name)

    # Not for startup.
    for non_locale_encoding in (
        "bz2_codec",
        "idna",
        "base64_codec",
        "hex_codec",
        "rot_13",
    ):
        if non_locale_encoding in encoding_names:
            encoding_names.remove(non_locale_encoding)

    import_code = ";".join(
        "import encodings.%s" % encoding_name
        for encoding_name in sorted(encoding_names)
    )

    import_code += ";import locale;"

    # For Python3 we patch inspect without knowing if it is used.
    if python_version >= 0x300:
        import_code += "import inspect;import importlib._bootstrap"

    result = _detectImports(command=import_code, user_provided=False, technical=True)

    if Options.shallFreezeAllStdlib():
        stdlib_modules = set()

        # Scan the standard library paths (multiple in case of virtualenv).
        for stdlib_dir in getStandardLibraryPaths():
            for module_name in scanStandardLibraryPath(stdlib_dir):
                if not isStandardLibraryNoAutoInclusionModule(module_name):
                    stdlib_modules.add(module_name)

        # Put here ones that should be imported first.
        first_ones = ("Tkinter",)

        # We have to fight zombie modules in this, some things, e.g. Tkinter
        # on newer Python 2.7, comes back after failure without a second error
        # being raised, leading to other issues. So we fight it after each
        # module that was tried, and prevent re-try by adding a meta path
        # based loader that will never load it again, and remove it from the
        # "sys.modules" over and over, once it sneaks back. The root cause is
        # that extension modules sometimes only raise an error when first
        # imported, not the second time around.
        # Otherwise this just makes imports of everything so we can see where
        # it comes from and what it requires.

        import_code = """
imports = %r

failed = set()

class ImportBlocker(object):
    def find_module(self, fullname, path = None):
        if fullname in failed:
            return self

        return None

    def load_module(self, name):
        raise ImportError("%%s has failed before" %% name)

sys.meta_path.insert(0, ImportBlocker())

for imp in imports:
    try:
        __import__(imp)
    except (ImportError, SyntaxError):
        failed.add(imp)
    except ValueError as e:
        if "cannot contain null bytes" in e.args[0]:
            failed.add(imp)
        else:
            sys.stderr.write("PROBLEM with '%%s'\\n" %% imp)
            raise
    except Exception:
        sys.stderr.write("PROBLEM with '%%s'\\n" %% imp)
        raise

    for fail in failed:
        if fail in sys.modules:
            del sys.modules[fail]
""" % (
            tuple(
                module_name.asString()
                for module_name in sorted(
                    stdlib_modules, key=lambda name: (name not in first_ones, name)
                )
            ),
        )

        early_names = [module.getFullName() for module in result]

        result += [
            module
            for module in _detectImports(
                command=import_code, user_provided=False, technical=False
            )
            if module.getFullName() not in early_names
        ]

    return result


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
            module_name = module.getFullName()

            if (
                "dist-packages" in module_filename.split("/")
                and not module_name.isFakeModuleName()
            ):
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
            checkModulePath(module)

    if problem_modules:
        general.info("Using Debian packages for '%s'." % ",".join(problem_modules))
        general.warning(message=message, mnemonic=mnemonic)


def detectEarlyImports():
    # Cyclic dependency
    from nuitka import ModuleRegistry

    early_modules = tuple(_detectEarlyImports())

    # TODO: Return early_modules, then there is no cycle.
    for module in early_modules:
        if module.isUncompiledPythonModule():
            ModuleRegistry.addUncompiledModule(module)

    return early_modules


def _detectBinaryDLLs(
    is_main_executable,
    source_dir,
    original_filename,
    binary_filename,
    package_name,
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
            decider=Options.isShowProgress,
        ):
            return detectBinaryPathDLLsWindowsDependencyWalker(
                is_main_executable=is_main_executable,
                source_dir=source_dir,
                original_dir=os.path.dirname(original_filename),
                binary_filename=binary_filename,
                package_name=package_name,
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


def _detectUsedDLLs(standalone_entry_point, source_dir):
    binary_filename = standalone_entry_point.source_path
    try:
        used_dlls = _detectBinaryDLLs(
            is_main_executable=standalone_entry_point.kind == "executable",
            source_dir=source_dir,
            original_filename=standalone_entry_point.source_path,
            binary_filename=standalone_entry_point.source_path,
            package_name=standalone_entry_point.package_name,
            use_cache=not Options.shallNotUseDependsExeCachedResults(),
            update_cache=not Options.shallNotStoreDependsExeCachedResults(),
        )
    except NuitkaForbiddenDLLEncounter:
        inclusion_logger.info("Not including forbidden DLL '%s'." % binary_filename)
    else:
        # Plugins generally decide if they allow dependencies from the outside
        # based on the package name.
        allow_outside_dependencies = Plugins.decideAllowOutsideDependencies(
            standalone_entry_point.package_name
        )

        # TODO: Command line option maybe
        if allow_outside_dependencies is None:
            allow_outside_dependencies = True

        if not allow_outside_dependencies:
            inside_paths = getPythonUnpackedSearchPath()

            def decideInside(dll_filename):
                return any(
                    isFilenameBelowPath(path=inside_path, filename=dll_filename)
                    for inside_path in inside_paths
                )

            used_dlls = set(
                dll_filename for dll_filename in used_dlls if decideInside(dll_filename)
            )

        # Allow plugins can prevent inclusion, this may discard things from used_dlls.
        removed_dlls = Plugins.removeDllDependencies(
            dll_filename=binary_filename, dll_filenames=used_dlls
        )
        used_dlls = tuple(OrderedSet(used_dlls) - OrderedSet(removed_dlls))

        for used_dll in used_dlls:
            # TODO: If used by a DLL from the same folder, put it there,
            # otherwise top level, but for now this is limited to the case where
            # it is required that way only, because it broke other things.
            if standalone_entry_point.package_name == "openvino" and areInSamePaths(
                standalone_entry_point.source_path, used_dll
            ):
                dest_path = os.path.normpath(
                    os.path.join(
                        os.path.dirname(standalone_entry_point.dest_path),
                        os.path.basename(used_dll),
                    )
                )
            else:
                dest_path = os.path.basename(used_dll)

            dll_entry_point = makeDllEntryPoint(
                logger=inclusion_logger,
                source_path=used_dll,
                dest_path=dest_path,
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
