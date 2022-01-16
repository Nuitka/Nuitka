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
""" Pack and copy files for standalone mode.

This is still under heavy evolution, but expected to work for
macOS, Windows, and Linux. Patches for other platforms are
very welcome.
"""

import hashlib
import marshal
import os
import pkgutil
import shutil
import sys

from nuitka import Options, SourceCodeReferences
from nuitka.__past__ import iterItems
from nuitka.build.SconsUtils import readSconsReport
from nuitka.Bytecodes import compileSourceToBytecode
from nuitka.containers.odict import OrderedDict
from nuitka.containers.oset import OrderedSet
from nuitka.importing import ImportCache
from nuitka.importing.Importing import locateModule
from nuitka.importing.StandardLibrary import (
    getStandardLibraryPaths,
    isStandardLibraryPath,
)
from nuitka.nodes.ModuleNodes import (
    PythonShlibModule,
    makeUncompiledPythonModule,
)
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.Tracing import general, inclusion_logger, printError
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils import Utils
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Execution import executeProcess, withEnvironmentPathAdded
from nuitka.utils.FileOperations import (
    areSamePaths,
    copyFileWithPermissions,
    getDirectoryRealPath,
    getFileContentByLine,
    getFileList,
    getSubDirectories,
    haveSameFileContents,
    listDir,
    makePath,
    putTextFileContents,
    relpath,
    resolveShellPatternToFilenames,
    withFileLock,
)
from nuitka.utils.Importing import getSharedLibrarySuffixes
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import (
    callInstallNameTool,
    getPyWin32Dir,
    getSharedLibraryRPATH,
    getWindowsDLLVersion,
    removeSxsFromDLL,
    setSharedLibraryRPATH,
)
from nuitka.utils.Signing import removeMacOSCodeSignature
from nuitka.utils.ThreadedExecutor import ThreadPoolExecutor, waitWorkers
from nuitka.utils.Timing import TimerReport

from .DependsExe import detectDLLsWithDependencyWalker
from .IncludedDataFiles import (
    IncludedDataDirectory,
    IncludedDataFile,
    makeIncludedDataFile,
)


def loadCodeObjectData(precompiled_filename):
    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    with open(precompiled_filename, "rb") as f:
        return f.read()[8:]


module_names = set()


def _detectedPrecompiledFile(filename, module_name, result, user_provided, technical):
    if filename.endswith(".pyc"):
        if os.path.isfile(filename[:-1]):
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
        bytecode=loadCodeObjectData(precompiled_filename=filename),
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

    source_code = readSourceCodeFromFilename(module_name, filename)

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

    # Plugins can modify source code:
    source_code = Plugins.onFrozenModuleSourceCode(
        module_name=module_name, is_package=is_package, source_code=source_code
    )

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


def _detectedShlibFile(filename, module_name):
    # That is not a shared library, but looks like one.
    if module_name == "__main__":
        return

    # Cyclic dependency
    from nuitka import ModuleRegistry

    if ModuleRegistry.hasRootModule(module_name):
        return

    source_ref = SourceCodeReferences.fromFilename(filename=filename)

    shlib_module = PythonShlibModule(module_name=module_name, source_ref=source_ref)

    ModuleRegistry.addRootModule(shlib_module)
    ImportCache.addImportedModule(shlib_module)

    module_names.add(module_name)


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

    import tempfile

    tmp_file, tmp_filename = tempfile.mkstemp()

    try:
        if python_version >= 0x300:
            command = command.encode("utf8")
        os.write(tmp_file, command)
        os.close(tmp_file)

        # TODO: Check exit code, should never fail.
        _stdout, stderr, exit_code = executeProcess(
            command=(sys.executable, "-s", "-S", "-v", tmp_filename),
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
    finally:
        os.unlink(tmp_filename)

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
                if python_version >= 0x300:  # For consistency, and maybe later reuse
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
                    if python_version >= 0x300:
                        if module_name == "decimal":
                            module_name = ModuleName("_decimal")

                    detections.append((module_name, 2, "shlib", filename))
            elif origin == b"dynamically":
                # Shared library in early load, happens on RPM based systems and
                # or self compiled Python installations.
                filename = parts[1][len(b"dynamically loaded from ") :]
                if python_version >= 0x300:
                    filename = filename.decode("utf8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append((module_name, 1, "shlib", filename))

    for module_name, _prio, kind, filename in sorted(detections):
        if kind == "precompiled":
            _detectedPrecompiledFile(
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
        elif kind == "shlib":
            _detectedShlibFile(filename=filename, module_name=module_name)
        else:
            assert False, kind

    return result


# Some modules we want to exclude.
_excluded_stdlib_modules = ["__main__.py", "__init__.py", "antigravity.py"]

if os.name != "nt":
    # On posix systems, and posix Python veriants on Windows, this won't
    # work.
    _excluded_stdlib_modules.append("wintypes.py")
    _excluded_stdlib_modules.append("cp65001.py")


def scanStandardLibraryPath(stdlib_dir):
    # There is a lot of filtering here, done in branches, so there # is many of
    # them, but that's acceptable, pylint: disable=too-many-branches,too-many-statements

    for root, dirs, filenames in os.walk(stdlib_dir):
        import_path = root[len(stdlib_dir) :].strip("/\\")
        import_path = import_path.replace("\\", ".").replace("/", ".")

        if import_path == "":
            if "site-packages" in dirs:
                dirs.remove("site-packages")
            if "dist-packages" in dirs:
                dirs.remove("dist-packages")
            if "test" in dirs:
                dirs.remove("test")
            if "idlelib" in dirs:
                dirs.remove("idlelib")
            if "turtledemo" in dirs:
                dirs.remove("turtledemo")

            if "ensurepip" in filenames:
                filenames.remove("ensurepip")
            if "ensurepip" in dirs:
                dirs.remove("ensurepip")

            # Ignore "lib-dynload" and "lib-tk" and alike.
            dirs[:] = [
                dirname
                for dirname in dirs
                if not dirname.startswith("lib-")
                if dirname != "Tools"
                if not dirname.startswith("plat-")
            ]

        if import_path in (
            "tkinter",
            "importlib",
            "ctypes",
            "unittest",
            "sqlite3",
            "distutils",
            "email",
            "bsddb",
        ):
            if "test" in dirs:
                dirs.remove("test")

        if import_path == "distutils.command":
            # Misbehaving and crashing while importing the world.
            if "bdist_conda.py" in filenames:
                filenames.remove("bdist_conda.py")

        if import_path in ("lib2to3", "json", "distutils"):
            if "tests" in dirs:
                dirs.remove("tests")

        if import_path == "asyncio":
            if "test_utils.py" in filenames:
                filenames.remove("test_utils.py")

        if python_version >= 0x340 and Utils.isWin32Windows():
            if import_path == "multiprocessing":
                filenames.remove("popen_fork.py")
                filenames.remove("popen_forkserver.py")
                filenames.remove("popen_spawn_posix.py")

        if python_version >= 0x300 and Utils.isPosixWindows():
            if import_path == "curses":
                filenames.remove("has_key.py")

        if Utils.isNetBSD():
            if import_path == "xml.sax":
                filenames.remove("expatreader.py")

        for filename in filenames:
            if filename.endswith(".py") and filename not in _excluded_stdlib_modules:
                module_name = filename[:-3]
                if import_path == "":
                    yield module_name
                else:
                    yield import_path + "." + module_name

        if python_version >= 0x300:
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")

        for dirname in dirs:
            if import_path == "":
                yield dirname
            else:
                yield import_path + "." + dirname


def _detectEarlyImports():
    encoding_names = [
        m[1] for m in pkgutil.iter_modules(sys.modules["encodings"].__path__)
    ]

    if os.name != "nt":
        # On posix systems, and posix Python veriants on Windows, these won't
        # work and fail to import.
        for encoding_name in ("mbcs", "cp65001", "oem"):
            if encoding_name in encoding_names:
                encoding_names.remove(encoding_name)

    import_code = ";".join(
        "import encodings.%s" % encoding_name
        for encoding_name in sorted(encoding_names)
    )

    import_code += ";import locale;"

    # For Python3 we patch inspect without knowing if it is used.
    if python_version >= 0x300:
        import_code += "import inspect;"

    result = _detectImports(command=import_code, user_provided=False, technical=True)

    if Options.shallFreezeAllStdlib():
        stdlib_modules = set()

        # Scan the standard library paths (multiple in case of virtualenv.
        for stdlib_dir in getStandardLibraryPaths():
            for module_name in scanStandardLibraryPath(stdlib_dir):
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
""" % sorted(
            stdlib_modules, key=lambda name: (name not in first_ones, name)
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


def detectEarlyImports():
    # Cyclic dependency
    from nuitka import ModuleRegistry

    early_modules = tuple(_detectEarlyImports())
    for module in early_modules:
        ModuleRegistry.addUncompiledModule(module)

    return early_modules


_detected_python_rpath = None

ldd_result_cache = {}

_linux_dll_ignore_list = (
    # Do not include kernel / glibc specific libraries. This list has been
    # assembled by looking what are the most common .so files provided by
    # glibc packages from ArchLinux, Debian Stretch and CentOS.
    #
    # Online sources:
    #  - https://centos.pkgs.org/7/puias-computational-x86_64/glibc-aarch64-linux-gnu-2.24-2.sdl7.2.noarch.rpm.html
    #  - https://centos.pkgs.org/7/centos-x86_64/glibc-2.17-222.el7.x86_64.rpm.html
    #  - https://archlinux.pkgs.org/rolling/archlinux-core-x86_64/glibc-2.28-5-x86_64.pkg.tar.xz.html
    #  - https://packages.debian.org/stretch/amd64/libc6/filelist
    #
    # Note: This list may still be incomplete. Some additional libraries
    # might be provided by glibc - it may vary between the package versions
    # and between Linux distros. It might or might not be a problem in the
    # future, but it should be enough for now.
    "ld-linux-x86-64.so",
    "libc.so",
    "libpthread.so",
    "libm.so",
    "libdl.so",
    "libBrokenLocale.so",
    "libSegFault.so",
    "libanl.so",
    "libcidn.so",
    "libcrypt.so",
    "libmemusage.so",
    "libmvec.so",
    "libnsl.so",
    "libnss3.so",
    "libnssutils3.so",
    "libnss_compat.so",
    "libnss_db.so",
    "libnss_dns.so",
    "libnss_files.so",
    "libnss_hesiod.so",
    "libnss_nis.so",
    "libnss_nisplus.so",
    "libpcprofile.so",
    "libresolv.so",
    "librt.so",
    "libthread_db-1.0.so",
    "libthread_db.so",
    "libutil.so",
    # The C++ standard library can also be ABI specific, and can cause system
    # libraries like MESA to not load any drivers, so we exclude it too, and
    # it can be assumed to be installed everywhere anyway.
    "libstdc++.so",
    # The DRM layer should also be taken from the OS in question and won't
    # allow loading native drivers otherwise.
    "libdrm.so",
)


def _getLdLibraryPath(package_name, python_rpath, original_dir):
    ld_library_path = OrderedSet()
    if python_rpath:
        ld_library_path.add(python_rpath)
    ld_library_path.update(getPackageSpecificDLLDirectories(package_name))

    if original_dir is not None:
        ld_library_path.add(original_dir)

    return ld_library_path


def _detectBinaryPathDLLsPosix(dll_filename, package_name, original_dir):
    # This is complex, as it also includes the caching mechanism
    # pylint: disable=too-many-branches

    if ldd_result_cache.get(dll_filename):
        return ldd_result_cache[dll_filename]

    # Ask "ldd" about the libraries being used by the created binary, these
    # are the ones that interest us.

    # This is the rpath of the Python binary, which will be effective when
    # loading the other DLLs too. This happens at least for Python installs
    # on Travis. pylint: disable=global-statement
    global _detected_python_rpath
    if _detected_python_rpath is None and not Utils.isPosixWindows():
        _detected_python_rpath = getSharedLibraryRPATH(sys.executable) or False

        if _detected_python_rpath:
            _detected_python_rpath = _detected_python_rpath.replace(
                "$ORIGIN", os.path.dirname(sys.executable)
            )

    # TODO: Actually would be better to pass it as env to the created process instead.
    with withEnvironmentPathAdded(
        "LD_LIBRARY_PATH",
        *_getLdLibraryPath(
            package_name=package_name,
            python_rpath=_detected_python_rpath,
            original_dir=original_dir,
        )
    ):
        # TODO: Check exit code, should never fail.
        stdout, stderr, _exit_code = executeProcess(command=("ldd", dll_filename))

    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if not line.startswith(
            b"ldd: warning: you do not have execution permission for"
        )
    )

    inclusion_logger.debug("ldd output for %s is:\n%s" % (dll_filename, stdout))

    if stderr:
        inclusion_logger.debug("ldd error for %s is:\n%s" % (dll_filename, stderr))

    result = set()

    for line in stdout.split(b"\n"):
        if not line:
            continue

        if b"=>" not in line:
            continue

        part = line.split(b" => ", 2)[1]

        if b"(" in part:
            filename = part[: part.rfind(b"(") - 1]
        else:
            filename = part

        if not filename:
            continue

        if python_version >= 0x300:
            filename = filename.decode("utf8")

        # Sometimes might use stuff not found or supplied by ldd itself.
        if filename in ("not found", "ldd"):
            continue

        # Normalize, sometimes the DLLs produce "something/../", this has
        # been seen with Qt at least.
        filename = os.path.normpath(filename)

        # Do not include kernel DLLs on the ignore list.
        filename_base = os.path.basename(filename)
        if any(
            filename_base == entry or filename_base.startswith(entry + ".")
            for entry in _linux_dll_ignore_list
        ):
            continue

        result.add(filename)

    ldd_result_cache[dll_filename] = result

    sub_result = set(result)

    for sub_dll_filename in result:
        sub_result = sub_result.union(
            _detectBinaryPathDLLsPosix(
                dll_filename=sub_dll_filename,
                package_name=package_name,
                original_dir=original_dir,
            )
        )

    return sub_result


def _detectBinaryPathDLLsMacOS(
    original_dir, binary_filename, package_name, keep_unresolved
):
    # TODO: Actually would be better to pass it as env to the created process instead.
    with withEnvironmentPathAdded(
        "DYLD_LIBRARY_PATH",
        *_getLdLibraryPath(
            package_name=package_name, python_rpath=None, original_dir=original_dir
        )
    ):
        # TODO: Check exit code, should never fail.
        stdout, _stderr, _exit_code = executeProcess(
            command=("otool", "-L", binary_filename)
        )
    system_paths = (
        "/usr/lib/",
        "/System/Library/Frameworks/",
        "/System/Library/PrivateFrameworks/",
    )

    result = OrderedSet()

    for line in stdout.split(b"\n")[1:]:
        if str is not bytes:
            line = line.decode("utf8")

        if not line:
            continue

        filename = line.split(" (", 1)[0].strip()
        for w in system_paths:
            if filename.startswith(w):
                break
        else:
            result.add(filename)

    resolved_result = _resolveBinaryPathDLLsMacOS(
        original_dir=original_dir,
        binary_filename=binary_filename,
        paths=result,
        keep_unresolved=keep_unresolved,
    )
    return resolved_result


def _resolveBinaryPathDLLsMacOS(original_dir, binary_filename, paths, keep_unresolved):
    if keep_unresolved:
        result = {}
    else:
        result = set()

    rpaths = _detectBinaryRPathsMacOS(original_dir, binary_filename)

    for path in paths:
        if path.startswith("@rpath/"):
            for rpath in rpaths:
                if os.path.isfile(os.path.join(rpath, path[7:])):
                    resolved_path = os.path.join(rpath, path[7:])
                    break
            else:
                resolved_path = os.path.join(original_dir, path[7:])

        elif path.startswith("@loader_path/"):
            resolved_path = os.path.join(original_dir, path[13:])
        else:
            resolved_path = path
        if keep_unresolved:
            result.update({resolved_path: path})
        else:
            result.add(resolved_path)
    return result


def _detectBinaryRPathsMacOS(original_dir, binary_filename):
    # TODO: Check exit code, should never fail.
    stdout, _stderr, _exit_code = executeProcess(
        command=("otool", "-l", binary_filename)
    )
    lines = stdout.split(b"\n")

    result = set()

    for i, line in enumerate(lines):
        if line.endswith(b"cmd LC_RPATH"):
            line = lines[i + 2]
            if str is not bytes:
                line = line.decode("utf8")

            line = line.split("path ", 1)[1]
            line = line.split(" (offset", 1)[0]
            if line.startswith("@loader_path"):
                line = os.path.join(original_dir, line[13:])
            elif line.startswith("@executable_path"):
                continue
            result.add(line)

    return result


def _getCacheFilename(
    dependency_tool, is_main_executable, source_dir, original_dir, binary_filename
):
    original_filename = os.path.join(original_dir, os.path.basename(binary_filename))
    original_filename = os.path.normcase(original_filename)

    if is_main_executable:
        # Normalize main program name for caching as well, but need to use the
        # scons information to distinguish different compilers, so we use
        # different libs there.

        # Ignore values, that are variable per compilation.
        hashed_value = "".join(
            key + value
            for key, value in iterItems(readSconsReport(source_dir=source_dir))
            if key not in ("CLCACHE_STATS",)
        )
    else:
        hashed_value = original_filename

    # Have different values for different Python major versions.
    hashed_value += sys.version + sys.executable

    if str is not bytes:
        hashed_value = hashed_value.encode("utf8")

    cache_dir = os.path.join(getCacheDir(), "library_deps", dependency_tool)

    makePath(cache_dir)

    return os.path.join(cache_dir, hashlib.md5(hashed_value).hexdigest())


_scan_dir_cache = {}


def getPackageSpecificDLLDirectories(package_name):
    scan_dirs = OrderedSet()

    if package_name is not None:
        package_dir = locateModule(
            module_name=package_name, parent_package=None, level=0
        )[1]

        if os.path.isdir(package_dir):
            scan_dirs.add(package_dir)
            scan_dirs.update(
                getSubDirectories(package_dir, ignore_dirs=("__pycache__",))
            )

        scan_dirs.update(Plugins.getModuleSpecificDllPaths(package_name))

    return scan_dirs


def getScanDirectories(package_name, original_dir):
    # Many cases, pylint: disable=too-many-branches

    cache_key = package_name, original_dir

    if cache_key in _scan_dir_cache:
        return _scan_dir_cache[cache_key]

    scan_dirs = [sys.prefix]

    if package_name is not None:
        scan_dirs.extend(getPackageSpecificDLLDirectories(package_name))

    if original_dir is not None:
        scan_dirs.append(original_dir)
        scan_dirs.extend(getSubDirectories(original_dir))

    if (
        Utils.isWin32Windows()
        and package_name is not None
        and package_name.isBelowNamespace("win32com")
    ):
        pywin32_dir = getPyWin32Dir()

        if pywin32_dir is not None:
            scan_dirs.append(pywin32_dir)

    for path_dir in os.environ["PATH"].split(";"):
        if not os.path.isdir(path_dir):
            continue

        if areSamePaths(path_dir, os.path.join(os.environ["SYSTEMROOT"])):
            continue
        if areSamePaths(path_dir, os.path.join(os.environ["SYSTEMROOT"], "System32")):
            continue
        if areSamePaths(path_dir, os.path.join(os.environ["SYSTEMROOT"], "SysWOW64")):
            continue

        scan_dirs.append(path_dir)

    result = []

    # Remove directories that hold no DLLs.
    for scan_dir in scan_dirs:
        sys.stdout.flush()

        # These are useless, but plenty.
        if os.path.basename(scan_dir) == "__pycache__":
            continue

        scan_dir = getDirectoryRealPath(scan_dir)

        # No DLLs, no use.
        if not any(entry[1].lower().endswith(".dll") for entry in listDir(scan_dir)):
            continue

        result.append(os.path.realpath(scan_dir))

    _scan_dir_cache[cache_key] = result
    return result


def detectBinaryPathDLLsWindowsDependencyWalker(
    is_main_executable,
    source_dir,
    original_dir,
    binary_filename,
    package_name,
    use_cache,
    update_cache,
):
    # This is the caching mechanism and plugin handling for DLL imports.
    if use_cache or update_cache:
        cache_filename = _getCacheFilename(
            dependency_tool="depends.exe",
            is_main_executable=is_main_executable,
            source_dir=source_dir,
            original_dir=original_dir,
            binary_filename=binary_filename,
        )

        if use_cache:
            with withFileLock():
                if not os.path.exists(cache_filename):
                    use_cache = False

        if use_cache:
            result = OrderedSet()

            for line in getFileContentByLine(cache_filename):
                line = line.strip()

                result.add(line)

            return result

    if Options.isShowProgress():
        general.info("Analysing dependencies of '%s'." % binary_filename)

    scan_dirs = getScanDirectories(package_name, original_dir)

    result = detectDLLsWithDependencyWalker(binary_filename, scan_dirs)

    if update_cache:
        putTextFileContents(filename=cache_filename, contents=result)

    return result


def detectBinaryDLLs(
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

    if (
        Utils.getOS() in ("Linux", "NetBSD", "FreeBSD", "OpenBSD")
        or Utils.isPosixWindows()
    ):
        return _detectBinaryPathDLLsPosix(
            dll_filename=original_filename,
            package_name=package_name,
            original_dir=os.path.dirname(original_filename),
        )
    elif Utils.isWin32Windows():
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
    elif Utils.isMacOS():
        return _detectBinaryPathDLLsMacOS(
            original_dir=os.path.dirname(original_filename),
            binary_filename=original_filename,
            package_name=package_name,
            keep_unresolved=False,
        )
    else:
        # Support your platform above.
        assert False, Utils.getOS()


_unfound_dlls = set()


def detectUsedDLLs(source_dir, standalone_entry_points, use_cache, update_cache):
    def addDLLInfo(count, source_dir, original_filename, binary_filename, package_name):
        used_dlls = detectBinaryDLLs(
            is_main_executable=count == 0,
            source_dir=source_dir,
            original_filename=original_filename,
            binary_filename=binary_filename,
            package_name=package_name,
            use_cache=use_cache,
            update_cache=update_cache,
        )

        # Allow plugins to prevent inclusion, this may discard things from used_dlls.
        Plugins.removeDllDependencies(
            dll_filename=binary_filename, dll_filenames=used_dlls
        )

        for dll_filename in sorted(tuple(used_dlls)):
            if not os.path.isfile(dll_filename):
                if _unfound_dlls:
                    general.warning(
                        "Dependency '%s' could not be found, you might need to copy it manually."
                        % dll_filename
                    )

                    _unfound_dlls.add(dll_filename)

                used_dlls.remove(dll_filename)

        return binary_filename, used_dlls

    result = OrderedDict()

    with ThreadPoolExecutor(max_workers=Utils.getCoreCount() * 3) as worker_pool:
        workers = []

        for count, standalone_entry_point in enumerate(standalone_entry_points):
            workers.append(
                worker_pool.submit(
                    addDLLInfo,
                    count,
                    source_dir,
                    standalone_entry_point.source_path,
                    standalone_entry_point.dest_path,
                    standalone_entry_point.package_name,
                )
            )

        for binary_filename, used_dlls in waitWorkers(workers):
            for dll_filename in used_dlls:
                # We want these to be absolute paths. Solve that in the parts
                # where detectBinaryDLLs is platform specific.
                assert os.path.isabs(dll_filename), dll_filename

                if dll_filename not in result:
                    result[dll_filename] = []
                result[dll_filename].append(binary_filename)

    return result


def fixupBinaryDLLPathsMacOS(binary_filename, dll_map, original_location):
    """For macOS, the binary needs to be told to use relative DLL paths"""

    # There may be nothing to do, in case there are no DLLs.
    if not dll_map:
        return

    rpath_map = _detectBinaryPathDLLsMacOS(
        original_dir=os.path.dirname(original_location),
        binary_filename=original_location,
        package_name=None,
        keep_unresolved=True,
    )
    for i, o in enumerate(dll_map):
        dll_map[i] = (rpath_map.get(o[0], o[0]), o[1])

    callInstallNameTool(
        filename=binary_filename,
        mapping=(
            (original_path, "@executable_path/" + dist_path)
            for (original_path, dist_path) in dll_map
        ),
        rpath=None,
    )


# These DLLs are run time DLLs from Microsoft, and packages will depend on different
# ones, but it will be OK to use the latest one.
ms_runtime_dlls = (
    "msvcp140_1.dll",
    "msvcp140.dll",
    "vcruntime140_1.dll",
    "concrt140.dll",
)


def copyUsedDLLs(source_dir, dist_dir, standalone_entry_points):
    # This is terribly complex, because we check the list of used DLLs
    # trying to avoid duplicates, and detecting errors with them not
    # being binary identical, so we can report them. And then of course
    # we also need to handle OS specifics.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    used_dlls = detectUsedDLLs(
        source_dir=source_dir,
        standalone_entry_points=standalone_entry_points,
        use_cache=not Options.shallNotUseDependsExeCachedResults()
        and not Options.getWindowsDependencyTool() == "depends.exe",
        update_cache=not Options.shallNotStoreDependsExeCachedResults()
        and not Options.getWindowsDependencyTool() == "depends.exe",
    )

    removed_dlls = set()
    warned_about = set()

    # Fist make checks and remove some.
    for dll_filename1, sources1 in tuple(iterItems(used_dlls)):
        if dll_filename1 in removed_dlls:
            continue

        for dll_filename2, sources2 in tuple(iterItems(used_dlls)):
            if dll_filename1 == dll_filename2:
                continue

            if dll_filename2 in removed_dlls:
                continue

            # Colliding basenames are an issue to us.
            if os.path.basename(dll_filename1) != os.path.basename(dll_filename2):
                continue

            # May already have been removed earlier
            if dll_filename1 not in used_dlls:
                continue

            if dll_filename2 not in used_dlls:
                continue

            dll_name = os.path.basename(dll_filename1)

            if Options.isShowInclusion():
                inclusion_logger.info(
                    """Colliding DLL names for %s, checking identity of \
'%s' <-> '%s'."""
                    % (dll_name, dll_filename1, dll_filename2)
                )

            # Check that if a DLL has the same name, if it's identical, then it's easy.
            if haveSameFileContents(dll_filename1, dll_filename2):
                del used_dlls[dll_filename2]
                removed_dlls.add(dll_filename2)

                continue

            # For Win32 we can check out file versions.
            if Utils.isWin32Windows():
                dll_version1 = getWindowsDLLVersion(dll_filename1)
                dll_version2 = getWindowsDLLVersion(dll_filename2)

                if dll_version2 < dll_version1:
                    del used_dlls[dll_filename2]
                    removed_dlls.add(dll_filename2)

                    solved = True
                elif dll_version1 < dll_version2:
                    del used_dlls[dll_filename1]
                    removed_dlls.add(dll_filename1)

                    solved = True
                else:
                    solved = False

                if solved:
                    if dll_name not in warned_about and dll_name not in ms_runtime_dlls:
                        warned_about.add(dll_name)

                        inclusion_logger.warning(
                            "Conflicting DLLs for '%s' in your installation, newest file version used, hoping for the best."
                            % dll_name
                        )

                    continue

            # So we have conflicting DLLs, in which case we do report the fact.
            inclusion_logger.warning(
                """\
Ignoring non-identical DLLs for '%s'.
%s used by:
   %s
different from
%s used by
   %s"""
                % (
                    dll_name,
                    dll_filename1,
                    "\n   ".join(sources1),
                    dll_filename2,
                    "\n   ".join(sources2),
                )
            )

            del used_dlls[dll_filename2]
            removed_dlls.add(dll_filename2)

    dll_map = []

    for dll_filename, sources in iterItems(used_dlls):
        dll_name = os.path.basename(dll_filename)

        target_path = os.path.join(dist_dir, dll_name)

        # Sometimes DLL dependencies were copied there already.
        if not os.path.exists(target_path):
            shutil.copyfile(dll_filename, target_path)

        dll_map.append((dll_filename, dll_name))

        if Options.isShowInclusion():
            inclusion_logger.info(
                "Included used shared library '%s' (used by %s)."
                % (dll_filename, ", ".join(sources))
            )

    if Utils.isMacOS():
        # For macOS, the binary and the DLLs needs to be changed to reflect
        # the relative DLL location in the ".dist" folder.
        for standalone_entry_point in standalone_entry_points:
            fixupBinaryDLLPathsMacOS(
                binary_filename=standalone_entry_point.dest_path,
                dll_map=dll_map,
                original_location=standalone_entry_point.source_path,
            )

        for original_path, dll_filename in dll_map:
            fixupBinaryDLLPathsMacOS(
                binary_filename=os.path.join(dist_dir, dll_filename),
                dll_map=dll_map,
                original_location=original_path,
            )

        # Remove code signature from CPython installed library
        candidate = os.path.join(
            dist_dir,
            "Python",
        )

        if os.path.exists(candidate):
            removeMacOSCodeSignature(candidate)

    # Remove or update rpath settings.
    if Utils.getOS() in ("Linux", "Darwin"):
        # For Linux, the "rpath" of libraries may be an issue and must be
        # removed.
        if Utils.isMacOS():
            start = 0
        else:
            start = 1

        for standalone_entry_point in standalone_entry_points[start:]:
            count = relpath(
                path=standalone_entry_point.dest_path, start=dist_dir
            ).count(os.path.sep)

            rpath = os.path.join("$ORIGIN", *([".."] * count))
            setSharedLibraryRPATH(standalone_entry_point.dest_path, rpath)

        for _original_path, dll_filename in dll_map:
            setSharedLibraryRPATH(os.path.join(dist_dir, dll_filename), "$ORIGIN")

    if Utils.isWin32Windows():
        if python_version < 0x300:
            # For Win32, we might have to remove SXS paths
            for standalone_entry_point in standalone_entry_points[1:]:
                removeSxsFromDLL(standalone_entry_point.dest_path)

            for _original_path, dll_filename in dll_map:
                removeSxsFromDLL(os.path.join(dist_dir, dll_filename))


def _handleDataFile(dist_dir, tracer, included_datafile):
    """Handle a data file."""
    if not isinstance(included_datafile, (IncludedDataFile, IncludedDataDirectory)):
        tracer.sysexit("Error, cannot only include 'IncludedData*' objects in plugins.")

    if included_datafile.kind == "empty_dirs":
        tracer.info(
            "Included empty directories '%s' due to %s."
            % (
                ",".join(included_datafile.dest_path),
                included_datafile.reason,
            )
        )

        for sub_dir in included_datafile.dest_path:
            created_dir = os.path.join(dist_dir, sub_dir)

            makePath(created_dir)
            putTextFileContents(
                filename=os.path.join(created_dir, ".keep_dir.txt"), contents=""
            )

    elif included_datafile.kind == "data_file":
        dest_path = os.path.join(dist_dir, included_datafile.dest_path)

        tracer.info(
            "Included data file '%s' due to %s."
            % (
                included_datafile.dest_path,
                included_datafile.reason,
            )
        )

        makePath(os.path.dirname(dest_path))
        copyFileWithPermissions(
            source_path=included_datafile.source_path, dest_path=dest_path
        )
    elif included_datafile.kind == "data_dir":
        dest_path = os.path.join(dist_dir, included_datafile.dest_path)
        makePath(os.path.dirname(dest_path))

        copied = []

        for filename in getFileList(
            included_datafile.source_path,
            ignore_dirs=included_datafile.ignore_dirs,
            ignore_filenames=included_datafile.ignore_filenames,
            ignore_suffixes=included_datafile.ignore_suffixes,
            only_suffixes=included_datafile.only_suffixes,
            normalize=included_datafile.normalize,
        ):
            filename_relative = os.path.relpath(filename, included_datafile.source_path)

            filename_dest = os.path.join(dest_path, filename_relative)
            makePath(os.path.dirname(filename_dest))

            copyFileWithPermissions(source_path=filename, dest_path=filename_dest)

            copied.append(filename_relative)

        tracer.info(
            "Included data dir %r with %d files due to: %s."
            % (
                included_datafile.dest_path,
                len(copied),
                included_datafile.reason,
            )
        )
    elif included_datafile.kind == "data_blob":
        dest_path = os.path.join(dist_dir, included_datafile.dest_path)
        makePath(os.path.dirname(dest_path))

        putTextFileContents(filename=dest_path, contents=included_datafile.data)

        tracer.info(
            "Included data file '%s' due to %s."
            % (
                included_datafile.dest_path,
                included_datafile.reason,
            )
        )
    else:
        assert False, included_datafile


def copyDataFiles(dist_dir):
    """Copy the data files needed for standalone distribution.

    Args:
        dist_dir: The distribution folder under creation
    Notes:
        This is for data files only, not DLLs or even extension modules,
        those must be registered as entry points, and would not go through
        necessary handling if provided like this.
    """

    # Many details to deal with, pylint: disable=too-many-branches,too-many-locals

    for pattern, src, dest, arg in Options.getShallIncludeDataFiles():
        filenames = resolveShellPatternToFilenames(pattern)

        if not filenames:
            inclusion_logger.warning(
                "No matching data file to be included for '%s'." % pattern
            )

        for filename in filenames:
            file_reason = "specified data file '%s' on command line" % arg

            if src is None:
                rel_path = dest

                if rel_path.endswith(("/", os.path.sep)):
                    rel_path = os.path.join(rel_path, os.path.basename(filename))
            else:
                rel_path = os.path.join(dest, relpath(filename, src))

            _handleDataFile(
                dist_dir,
                inclusion_logger,
                makeIncludedDataFile(filename, rel_path, file_reason),
            )

    for src, dest in Options.getShallIncludeDataDirs():
        filenames = getFileList(src)

        if not filenames:
            inclusion_logger.warning("No files in directory '%s.'" % src)

        for filename in filenames:
            relative_filename = relpath(filename, src)

            file_reason = "specified data dir %r on command line" % src

            rel_path = os.path.join(dest, relative_filename)

            _handleDataFile(
                dist_dir,
                inclusion_logger,
                makeIncludedDataFile(filename, rel_path, file_reason),
            )

    # Cyclic dependency
    from nuitka import ModuleRegistry

    for module in ModuleRegistry.getDoneModules():
        for plugin, included_datafile in Plugins.considerDataFiles(module):
            _handleDataFile(
                dist_dir=dist_dir, tracer=plugin, included_datafile=included_datafile
            )

    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonPackage() or module.isUncompiledPythonPackage():
            package_name = module.getFullName()

            match, reason = package_name.matchesToShellPatterns(
                patterns=Options.getShallIncludePackageData()
            )

            if match:
                package_directory = module.getCompileTimeDirectory()

                pkg_filenames = getFileList(
                    package_directory,
                    ignore_dirs=("__pycache__",),
                    ignore_suffixes=(".py", ".pyw", ".pyc", ".pyo", ".dll")
                    + getSharedLibrarySuffixes(),
                )

                if pkg_filenames:
                    file_reason = "package '%s' %s" % (package_name, reason)

                    for pkg_filename in pkg_filenames:
                        rel_path = os.path.join(
                            package_name.asPath(),
                            os.path.relpath(pkg_filename, package_directory),
                        )

                        _handleDataFile(
                            dist_dir,
                            inclusion_logger,
                            makeIncludedDataFile(pkg_filename, rel_path, file_reason),
                        )
