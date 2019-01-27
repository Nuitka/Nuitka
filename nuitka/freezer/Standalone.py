#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import contextlib
import hashlib
import marshal
import os
import shutil
import subprocess
import sys
from logging import debug, info, warning

from nuitka import Options, SourceCodeReferences, Tracing
from nuitka.__past__ import iterItems
from nuitka.containers.odict import OrderedDict
from nuitka.importing import ImportCache
from nuitka.importing.StandardLibrary import (
    getStandardLibraryPaths,
    isStandardLibraryPath
)
from nuitka.nodes.ModuleNodes import (
    PythonShlibModule,
    makeUncompiledPythonModule
)
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils import Utils
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Execution import withEnvironmentPathAdded
from nuitka.utils.FileOperations import (
    areSamePaths,
    deleteFile,
    getSubDirectories,
    listDir,
    makePath
)
from nuitka.utils.SharedLibraries import getWindowsDLLVersion, removeSxsFromDLL
from nuitka.utils.ThreadedExecutor import Lock, ThreadPoolExecutor, waitWorkers
from nuitka.utils.Timing import TimerReport
from nuitka.utils.Utils import getArchitecture

from .DependsExe import getDependsExePath

# Use PE file analysis only on Windows
if os.name == "nt" and Options.isExperimental("use_pefile"):
    import pefile # @UnresolvedImport pylint: disable=I0021,import-error
    # Finding site-packages directory when recursive internal dependency walker is used
    from distutils.sysconfig import get_python_lib # @UnresolvedImport pylint: disable=I0021,import-error


def loadCodeObjectData(precompiled_filename):
    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    return open(precompiled_filename, "rb").read()[8:]


module_names = set()

def _detectedPrecompiledFile(filename, module_name, result, user_provided,
                             technical):
    if filename.endswith(".pyc"):
        if os.path.isfile(filename[:-1]):
            return _detectedSourceFile(
                filename      = filename[:-1],
                module_name   = module_name,
                result        = result,
                user_provided = user_provided,
                technical     = technical
            )

    if module_name in module_names:
        return

    debug(
        "Freezing module '%s' (from '%s').",
        module_name,
        filename
    )

    uncompiled_module = makeUncompiledPythonModule(
        module_name   = module_name,
        bytecode      = loadCodeObjectData(
            precompiled_filename = filename
        ),
        is_package    = "__init__" in filename,
        filename      = filename,
        user_provided = user_provided,
        technical     = technical
    )

    ImportCache.addImportedModule(uncompiled_module)

    result.append(uncompiled_module)
    module_names.add(module_name)


def _detectedSourceFile(filename, module_name, result, user_provided, technical):
    if module_name in module_names:
        return

    if module_name == "collections.abc":
        _detectedSourceFile(
            filename      = filename,
            module_name   = "_collections_abc",
            result        = result,
            user_provided = user_provided,
            technical     = technical
        )

    source_code = readSourceCodeFromFilename(module_name, filename)

    if module_name == "site":
        if source_code.startswith("def ") or source_code.startswith("class "):
            source_code = '\n' + source_code

        source_code = """\
__file__ = (__nuitka_binary_dir + '%s%s') if '__nuitka_binary_dir' in dict(__builtins__ ) else '<frozen>';%s""" % (
            os.path.sep,
            os.path.basename(filename),
            source_code
        )

        # Debian stretch site.py
        source_code = source_code.replace(
            "PREFIXES = [sys.prefix, sys.exec_prefix]",
            "PREFIXES = []"
        )

        # Anaconda3 4.1.2 site.py
        source_code = source_code.replace(
            "def main():",
            "def main():return\n\nif 0:\n def _unused():",
        )

    debug(
        "Freezing module '%s' (from '%s').",
        module_name,
        filename
    )

    is_package = os.path.basename(filename) == "__init__.py"
    source_code = Plugins.onFrozenModuleSourceCode(
        module_name = module_name,
        is_package  = is_package,
        source_code = source_code
    )

    bytecode = compile(source_code, filename, "exec", dont_inherit = True)

    bytecode = Plugins.onFrozenModuleBytecode(
        module_name = module_name,
        is_package  = is_package,
        bytecode    = bytecode
    )

    uncompiled_module = makeUncompiledPythonModule(
        module_name   = module_name,
        bytecode      = marshal.dumps(
            bytecode
        ),
        is_package    = is_package,
        filename      = filename,
        user_provided = user_provided,
        technical     = technical
    )

    ImportCache.addImportedModule(uncompiled_module)

    result.append(uncompiled_module)
    module_names.add(module_name)


def _detectedShlibFile(filename, module_name):
    # That is not a shared library, but looks like one.
    if module_name == "__main__":
        return

    from nuitka import ModuleRegistry
    if ModuleRegistry.hasRootModule(module_name):
        return

    parts = module_name.split('.')
    if len(parts) == 1:
        package_name = None
        name = module_name
    else:
        package_name = '.'.join(parts[:-1])
        name = parts[-1]

    source_ref = SourceCodeReferences.fromFilename(
        filename = filename
    )

    shlib_module = PythonShlibModule(
        name         = name,
        package_name = package_name,
        source_ref   = source_ref
    )

    ModuleRegistry.addRootModule(shlib_module)
    ImportCache.addImportedModule(shlib_module)

    module_names.add(module_name)


def _detectImports(command, user_provided, technical):
    # This is pretty complicated stuff, with variants to deal with.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # Print statements for stuff to show, the modules loaded.
    if python_version >= 300:
        command += '\nprint("\\n".join(sorted("import " + module.__name__ + " # sourcefile " + ' \
                   'module.__file__ for module in sys.modules.values() if hasattr(module, "__file__") and ' \
                   'module.__file__ not in (None, "<frozen>"))), file = sys.stderr)'  # do not read it

    reduced_path = [
        path_element
        for path_element in
        sys.path
        if not areSamePaths(
            path_element,
            '.'
        )
        if not areSamePaths(
            path_element,
            os.path.dirname(sys.modules["__main__"].__file__)
        )
    ]

    # Make sure the right import path (the one Nuitka binary is running with)
    # is used.
    command = ("import sys; sys.path = %s; sys.real_prefix = sys.prefix;" % repr(reduced_path)) + command

    import tempfile
    tmp_file, tmp_filename = tempfile.mkstemp()

    try:
        if python_version >= 300:
            command = command.encode("utf8")
        os.write(tmp_file, command)
        os.close(tmp_file)

        process = subprocess.Popen(
            args   = [sys.executable, "-s", "-S", "-v", tmp_filename],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            env    = dict(os.environ, PYTHONIOENCODING = "utf_8")
        )
        _stdout, stderr = process.communicate()
    finally:
        os.unlink(tmp_filename)

    # Don't let errors here go unnoticed.
    if process.returncode != 0:
        warning("There is a problem with detecting imports, CPython said:")
        for line in stderr.split(b"\n"):
            Tracing.printError(line)
        sys.exit("Error, please report the issue with above output.")

    result = []

    debug("Detecting imports:")

    detections = []

    for line in stderr.replace(b"\r", b"").split(b"\n"):
        if line.startswith(b"import "):
            # print(line)

            parts = line.split(b" # ", 2)

            module_name = parts[0].split(b" ", 2)[1]
            origin = parts[1].split()[0]

            if python_version >= 300:
                module_name = module_name.decode("utf-8")

            if origin == b"precompiled":
                # This is a ".pyc" file that was imported, even before we have a
                # chance to do anything, we need to preserve it.
                filename = parts[1][len(b"precompiled from "):]
                if python_version >= 300:
                    filename = filename.decode("utf-8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append(
                    (module_name, 3, "precompiled", filename)
                )
            elif origin == b"sourcefile":
                filename = parts[1][len(b"sourcefile "):]
                if python_version >= 300:
                    filename = filename.decode("utf-8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                if filename.endswith(".py"):
                    detections.append(
                        (module_name, 2, "sourcefile", filename)
                    )
                elif not filename.endswith("<frozen>"):
                    # Python3 started lying in "__name__" for the "_decimal"
                    # calls itself "decimal", which then is wrong and also
                    # clashes with "decimal" proper
                    if python_version >= 300:
                        if module_name == "decimal":
                            module_name = "_decimal"

                    detections.append(
                        (module_name, 2, "shlib", filename)
                    )
            elif origin == b"dynamically":
                # Shared library in early load, happens on RPM based systems and
                # or self compiled Python installations.
                filename = parts[1][len(b"dynamically loaded from "):]
                if python_version >= 300:
                    filename = filename.decode("utf-8")

                # Do not leave standard library when freezing.
                if not isStandardLibraryPath(filename):
                    continue

                detections.append(
                    (module_name, 1, "shlib", filename)
                )

    for module_name, _prio, kind, filename in sorted(detections):
        if kind == "precompiled":
            _detectedPrecompiledFile(
                filename      = filename,
                module_name   = module_name,
                result        = result,
                user_provided = user_provided,
                technical     = technical
            )
        elif kind == "sourcefile":
            _detectedSourceFile(
                filename      = filename,
                module_name   = module_name,
                result        = result,
                user_provided = user_provided,
                technical     = technical
            )
        elif kind == "shlib":
            _detectedShlibFile(
                filename    = filename,
                module_name = module_name
            )
        else:
            assert False, kind

    return result


# Some modules we want to blacklist.
ignore_modules = [
    "__main__.py",
    "__init__.py",
    "antigravity.py",
]

if os.name != "nt":
    # On posix systems, and posix Python veriants on Windows, this won't
    # work.
    ignore_modules.append("wintypes.py")
    ignore_modules.append("cp65001.py")


def scanStandardLibraryPath(stdlib_dir):
    # There is a lot of black-listing here, done in branches, so there
    # is many of them, but that's acceptable, pylint: disable=too-many-branches

    for root, dirs, filenames in os.walk(stdlib_dir):
        import_path = root[len(stdlib_dir):].strip("/\\")
        import_path = import_path.replace('\\', '.').replace('/','.')

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

            # Ignore "lib-dynload" and "lib-tk" and alikes.
            dirs[:] = [
                dirname
                for dirname in
                dirs
                if not dirname.startswith("lib-")
                if dirname != "Tools"
            ]

        if import_path in ("tkinter", "importlib", "ctypes", "unittest",
                           "sqlite3", "distutils", "email", "bsddb"):
            if "test" in dirs:
                dirs.remove("test")

        if import_path in ("lib2to3", "json", "distutils"):
            if "tests" in dirs:
                dirs.remove("tests")

        if import_path == "asyncio":
            if "test_utils.py" in filenames:
                filenames.remove("test_utils.py")

        if python_version >= 340 and Utils.getOS() == "Windows":
            if import_path == "multiprocessing":
                filenames.remove("popen_fork.py")
                filenames.remove("popen_forkserver.py")
                filenames.remove("popen_spawn_posix.py")

        if Utils.getOS() == "NetBSD":
            if import_path == "xml.sax":
                filenames.remove("expatreader.py")

        for filename in filenames:
            if filename.endswith(".py") and filename not in ignore_modules:
                module_name = filename[:-3]
                if import_path == "":
                    yield module_name
                else:
                    yield import_path + '.' + module_name

        if python_version >= 300:
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")

        for dirname in dirs:
            if import_path == "":
                yield dirname
            else:
                yield import_path + '.' + dirname


def detectEarlyImports():
    encoding_names = [
        filename[:-3]
        for _path, filename in
        listDir(os.path.dirname(sys.modules["encodings"].__file__))
        if filename.endswith(".py")
        if "__init__" not in filename
    ]


    if os.name != "nt":
        # On posix systems, and posix Python veriants on Windows, this won't
        # work.
        for encoding_name in ("mbcs", "cp65001", "oem"):
            if encoding_name in encoding_names:
                encoding_names.remove(encoding_name)

    import_code = ';'.join(
        "import encodings.%s" % encoding_name
        for encoding_name in
        encoding_names
    )

    import_code += ";import locale;"

    # For Python3 we patch inspect without knowing if it is used.
    if python_version >= 300:
        import_code += "import inspect;"

    result = _detectImports(
        command       = import_code,
        user_provided = False,
        technical     = True
    )

    if Options.shallFreezeAllStdlib():
        stdlib_modules = set()

        # Scan the standard library paths (multiple in case of virtualenv.
        for stdlib_dir in getStandardLibraryPaths():
            for module_name in scanStandardLibraryPath(stdlib_dir):
                stdlib_modules.add(module_name)

        # Put here ones that should be imported first.
        first_ones = (
            "Tkinter",
        )

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

    for fail in failed:
        if fail in sys.modules:
            del sys.modules[fail]
""" % sorted(
    stdlib_modules,
    key = lambda name: (name not in first_ones, name)
)

        early_names = [
            module.getFullName()
            for module in result
        ]

        result += [
            module
            for module in _detectImports(
                command       = import_code,
                user_provided = False,
                technical     = False
            )
            if module.getFullName() not in early_names
        ]

    debug("Finished detecting early imports.")

    return result

_detected_python_rpath = None

ldd_result_cache = {}

def _detectBinaryPathDLLsLinuxBSD(dll_filename):
    # This is complex, as it also includes the caching mechanism
    # pylint: disable=too-many-branches

    if ldd_result_cache.get(dll_filename):
        return ldd_result_cache[dll_filename]

    # Ask "ldd" about the libraries being used by the created binary, these
    # are the ones that interest us.
    result = set()

    # This is the rpath of the Python binary, which will be effective when
    # loading the other DLLs too. This happens at least for Python installs
    # on Travis. pylint: disable=global-statement
    global _detected_python_rpath
    if _detected_python_rpath is None:
        _detected_python_rpath = getSharedLibraryRPATH(sys.executable) or False

        if _detected_python_rpath:
            _detected_python_rpath = _detected_python_rpath.replace(
                b"$ORIGIN",
                os.path.dirname(sys.executable).encode("utf-8")
            )

    with withEnvironmentPathAdded("LD_LIBRARY_PATH", _detected_python_rpath):
        process = subprocess.Popen(
            args   = [
                "ldd",
                dll_filename
            ],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        stdout, _stderr = process.communicate()

        for line in stdout.split(b"\n"):
            if not line:
                continue

            if b"=>" not in line:
                continue

            part = line.split(b" => ", 2)[1]

            if b"(" in part:
                filename = part[:part.rfind(b"(")-1]
            else:
                filename = part

            if not filename:
                continue

            if python_version >= 300:
                filename = filename.decode("utf-8")

            # Sometimes might use stuff not found.
            if filename == "not found":
                continue

            # pylint: disable=line-too-long
            #
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
            #
            # pylint: enable=line-too-long
            if os.path.basename(filename).startswith(
                    (
                        "ld-linux-x86-64.so",
                        "libc.so.",
                        "libpthread.so.",
                        "libm.so.",
                        "libdl.so.",
                        "libBrokenLocale.so.",
                        "libSegFault.so",
                        "libanl.so.",
                        "libcidn.so.",
                        "libcrypt.so.",
                        "libmemusage.so",
                        "libmvec.so.",
                        "libnsl.so.",
                        "libnss_compat.so.",
                        "libnss_db.so.",
                        "libnss_dns.so.",
                        "libnss_files.so.",
                        "libnss_hesiod.so.",
                        "libnss_nis.so.",
                        "libnss_nisplus.so.",
                        "libpcprofile.so",
                        "libresolv.so.",
                        "librt.so.",
                        "libthread_db-1.0.so",
                        "libthread_db.so.",
                        "libutil.so."
                    )
                ):
                continue

            result.add(filename)

    # Allow plugins to prevent inclusion.
    blocked = Plugins.removeDllDependencies(
        dll_filename  = dll_filename,
        dll_filenames = result
    )

    for to_remove in blocked:
        result.discard(to_remove)

    ldd_result_cache[dll_filename] = result

    sub_result = set(result)

    for sub_dll_filename in result:
        sub_result = sub_result.union(_detectBinaryPathDLLsLinuxBSD(sub_dll_filename))

    return sub_result


def _detectBinaryPathDLLsMacOS(original_dir, binary_filename):
    result = set()

    process = subprocess.Popen(
        args   = [
            "otool",
            "-L",
            binary_filename
        ],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    stdout, _stderr = process.communicate()
    system_paths = (b"/usr/lib/", b"/System/Library/Frameworks/")

    for line in stdout.split(b"\n")[2:]:
        if not line:
            continue

        filename = line.split(b" (")[0].strip()
        stop = False
        for w in system_paths:
            if filename.startswith(w):
                stop = True
                break
        if not stop:
            if python_version >= 300:
                filename = filename.decode("utf-8")

            if filename.startswith("@rpath/"):
                filename = os.path.join(original_dir, filename[7:])
            elif filename.startswith("@loader_path/"):
                filename = os.path.join(original_dir, filename[13:])

            # print "adding", filename
            result.add(filename)

    return result


def _getCacheFilename(is_main_executable, source_dir, original_dir, binary_filename):
    original_filename = os.path.join(
        original_dir,
        os.path.basename(binary_filename)
    )

    original_filename = os.path.normcase(original_filename)


    if is_main_executable:
        # Normalize main program name for caching as well, but need to use the
        # scons information to distinguish different Python and arches, and
        # compilers, so we use different libs there.
        hashed_value = open(os.path.join(source_dir, "scons-report.txt")).read()
    else:
        hashed_value = original_filename

    # Have different values for different Python major versions.
    hashed_value += sys.version + sys.executable

    if str is not bytes:
        hashed_value = hashed_value.encode("utf8")

    cache_dir = os.path.join(
        getCacheDir(),
        "library_deps_pefile" if Options.isExperimental("use_pefile") else "library_deps",
    )

    makePath(cache_dir)

    return os.path.join(
        cache_dir,
        hashlib.md5(hashed_value).hexdigest()
    )


# Locking seems to be only required for Windows currently, expressed that in the
# lock name.
windows_lock = None

@contextlib.contextmanager
def _withLock():
    # This is a singleton, pylint: disable=global-statement
    global windows_lock

    if windows_lock is None:
        windows_lock = Lock()

    windows_lock.acquire()
    yield
    windows_lock.release()

def _parseDependsExeOutput(filename, result):
    inside = False
    first = False

    for line in open(filename):
        if "| Module Dependency Tree |" in line:
            inside = True
            first = True
            continue

        if not inside:
            continue

        if "| Module List |" in line:
            break

        if ']' not in line:
            continue

        # Skip missing DLLs, apparently not needed anyway.
        if '?' in line[:line.find(']')]:
            continue

        # Skip DLLs that failed to load, apparently not needed anyway.
        if 'E' in line[:line.find(']')]:
            continue

        dll_filename = line[line.find(']')+2:-1]

        # The executable itself is of course exempted. We cannot check its path
        # because depends.exe mistreats unicode paths.
        if first:
            first = False
            continue

        assert os.path.isfile(dll_filename), dll_filename

        dll_name = os.path.basename(dll_filename).upper()

        # Win API can be assumed.
        if dll_name.startswith("API-MS-WIN-") or \
           dll_name.startswith("EXT-MS-WIN-"):
            continue

        if dll_name in ("SHELL32.DLL", "USER32.DLL", "KERNEL32.DLL",
            "NTDLL.DLL", "NETUTILS.DLL", "LOGONCLI.DLL", "GDI32.DLL",
            "RPCRT4.DLL", "ADVAPI32.DLL", "SSPICLI.DLL", "SECUR32.DLL",
            "KERNELBASE.DLL", "WINBRAND.DLL", "DSROLE.DLL", "DNSAPI.DLL",
            "SAMCLI.DLL", "WKSCLI.DLL", "SAMLIB.DLL", "WLDAP32.DLL",
            "NTDSAPI.DLL", "CRYPTBASE.DLL", "W32TOPL", "WS2_32.DLL",
            "SPPC.DLL", "MSSIGN32.DLL", "CERTCLI.DLL", "WEBSERVICES.DLL",
            "AUTHZ.DLL", "CERTENROLL.DLL", "VAULTCLI.DLL", "REGAPI.DLL",
            "BROWCLI.DLL", "WINNSI.DLL", "DHCPCSVC6.DLL", "PCWUM.DLL",
            "CLBCATQ.DLL", "IMAGEHLP.DLL", "MSASN1.DLL", "DBGHELP.DLL",
            "DEVOBJ.DLL", "DRVSTORE.DLL", "CABINET.DLL", "SCECLI.DLL",
            "SPINF.DLL", "SPFILEQ.DLL", "GPAPI.DLL", "NETJOIN.DLL",
            "W32TOPL.DLL", "NETBIOS.DLL", "DXGI.DLL", "DWRITE.DLL",
            "D3D11.DLL", "WLANAPI.DLL", "WLANUTIL.DLL", "ONEX.DLL",
            "EAPPPRXY.DLL", "MFPLAT.DLL", "AVRT.DLL", "ELSCORE.DLL",
            "INETCOMM.DLL", "MSOERT2.DLL", "IEUI.DLL", "MSCTF.DLL",
            "MSFEEDS.DLL", "UIAUTOMATIONCORE.DLL", "PSAPI.DLL",
            "EFSADU.DLL", "MFC42U.DLL", "ODBC32.DLL", "OLEDLG.DLL",
            "NETAPI32.DLL", "LINKINFO.DLL", "DUI70.DLL", "ADVPACK.DLL",
            "NTSHRUI.DLL", "WINSPOOL.DRV", "EFSUTIL.DLL", "WINSCARD.DLL",
            "SHDOCVW.DLL", "IEFRAME.DLL", "D2D1.DLL", "GDIPLUS.DLL",
            "OCCACHE.DLL", "IEADVPACK.DLL", "MLANG.DLL", "MSI.DLL",
            "MSHTML.DLL", "COMDLG32.DLL", "PRINTUI.DLL", "PUIAPI.DLL",
            "ACLUI.DLL", "WTSAPI32.DLL", "FMS.DLL", "DFSCLI.DLL",
            "HLINK.DLL", "MSRATING.DLL", "PRNTVPT.DLL", "IMGUTIL.DLL",
            "MSLS31.DLL", "VERSION.DLL", "NORMALIZ.DLL", "IERTUTIL.DLL",
            "WININET.DLL", "WINTRUST.DLL", "XMLLITE.DLL", "APPHELP.DLL",
            "PROPSYS.DLL", "RSTRTMGR.DLL", "NCRYPT.DLL", "BCRYPT.DLL",
            "MMDEVAPI.DLL", "MSILTCFG.DLL", "DEVMGR.DLL", "DEVRTL.DLL",
            "NEWDEV.DLL", "VPNIKEAPI.DLL", "WINHTTP.DLL", "WEBIO.DLL",
            "NSI.DLL", "DHCPCSVC.DLL", "CRYPTUI.DLL", "ESENT.DLL",
            "DAVHLPR.DLL", "CSCAPI.DLL", "ATL.DLL", "OLEAUT32.DLL",
            "SRVCLI.DLL", "RASDLG.DLL", "MPRAPI.DLL", "RTUTILS.DLL",
            "RASMAN.DLL", "MPRMSG.DLL", "SLC.DLL", "CRYPTSP.DLL",
            "RASAPI32.DLL", "TAPI32.DLL", "EAPPCFG.DLL", "NDFAPI.DLL",
            "WDI.DLL", "COMCTL32.DLL", "UXTHEME.DLL", "IMM32.DLL",
            "OLEACC.DLL", "WINMM.DLL", "WINDOWSCODECS.DLL", "DWMAPI.DLL",
            "DUSER.DLL", "PROFAPI.DLL", "URLMON.DLL", "SHLWAPI.DLL",
            "LPK.DLL", "USP10.DLL", "CFGMGR32.DLL", "MSIMG32.DLL",
            "POWRPROF.DLL", "SETUPAPI.DLL", "WINSTA.DLL", "CRYPT32.DLL",
            "IPHLPAPI.DLL", "MPR.DLL", "CREDUI.DLL", "NETPLWIZ.DLL",
            "OLE32.DLL", "ACTIVEDS.DLL", "ADSLDPC.DLL", "USERENV.DLL",
            "APPREPAPI.DLL", "BCP47LANGS.DLL", "BCRYPTPRIMITIVES.DLL",
            "CERTCA.DLL", "CHARTV.DLL", "COMBASE.DLL", "COML2.DLL",
            "DCOMP.DLL", "DPAPI.DLL", "DSPARSE.DLL", "FECLIENT.DLL",
            "FIREWALLAPI.DLL", "FLTLIB.DLL", "MRMCORER.DLL", "NTASN1.DLL",
            "SECHOST.DLL", "SETTINGSYNCPOLICY.DLL", "SHCORE.DLL", "TBS.DLL",
            "TWINAPI.APPCORE.DLL", "TWINAPI.DLL", "VIRTDISK.DLL",
            "WEBSOCKET.DLL", "WEVTAPI.DLL", "WINMMBASE.DLL", "WMICLNT.DLL",
            "ICUUC.DLL"):
            continue

        result.add(
            os.path.normcase(os.path.abspath(dll_filename))
        )


def _detectBinaryPathDLLsWindows(is_main_executable, source_dir, original_dir, binary_filename, package_name):
    # This is complex, as it also includes the caching mechanism
    # pylint: disable=too-many-locals

    result = set()

    cache_filename = _getCacheFilename(is_main_executable, source_dir, original_dir, binary_filename)

    if os.path.exists(cache_filename) and not Options.shallNotUseDependsExeCachedResults():
        for line in open(cache_filename):
            line = line.strip()

            result.add(line)

        return result

    # User query should only happen once if at all.
    with _withLock():
        depends_exe = getDependsExePath()

    scan_dirs = [sys.prefix]

    if package_name is not None:
        from nuitka.importing.Importing import findModule

        package_dir = findModule(None, package_name, None, 0, False)[1]

        if os.path.isdir(package_dir):
            scan_dirs.append(package_dir)
            scan_dirs.extend(getSubDirectories(package_dir))

    if original_dir is not None:
        scan_dirs.append(original_dir)
        scan_dirs.extend(getSubDirectories(original_dir))

    with _withLock():
        # The search order by default prefers the system directory, where a
        # wrong "PythonXX.dll" might be living.
        with open(binary_filename + ".dwp", 'w') as dwp_file:
            dwp_file.write(
                """\
KnownDLLs
%(original_dirs)s
SysPath
32BitSysDir
16BitSysDir
OSDir
AppPath
SxS
""" % {
                "original_dirs" : '\n'.join(
                    "UserDir %s" % dirname
                    for dirname in
                    scan_dirs
                    if not os.path.basename(dirname) == "__pycache__"
                    if any(entry[1].lower().endswith(".dll") for entry in listDir(dirname))
                ),
                }
            )

        # Starting the process while locked, so file handles are not duplicated.
        depends_exe_process = subprocess.Popen(
            (
                depends_exe,
                "-c",
                "-ot%s" % binary_filename + ".depends",
                "-d:%s" % binary_filename + ".dwp",
                "-f1",
                "-pa1",
                "-ps1",
                binary_filename
            )
        )

    # TODO: Exit code should be checked.
    depends_exe_process.wait()

    # Opening the result under lock, so it is not getting locked by new processes.
    with _withLock():
        _parseDependsExeOutput(binary_filename + ".depends", result)

    deleteFile(binary_filename + ".depends", must_exist = True)
    deleteFile(binary_filename + ".dwp", must_exist = True)

    if not Options.shallNotStoreDependsExeCachedResults():
        with open(cache_filename, 'w') as cache_file:
            for dll_filename in result:
                print(dll_filename, file = cache_file)

    return result


def _getPEFile(binary_filename):
    try:
        pe = pefile.PE(binary_filename)
        return pe
    except AttributeError:
        assert False, "Bogus PE header in " + binary_filename


def _isPE64(pe_file):
    pe = _getPEFile(pe_file)
    arch = {pefile.OPTIONAL_HEADER_MAGIC_PE: False,
            pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS: True}
    try:
        return arch[pe.PE_TYPE]
    except KeyError:
        # Support your architecture.
        assert False, "Unknown PE file architecture"


def _parsePEFileOutput(binary_filename, scan_dirs, result):
    pe = _getPEFile(binary_filename)

    # Some DLLs (eg numpy) don't have imports
    if not hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        info("Warning: no DIRECTORY_ENTRY_IMPORT PE section for library '%s'!" % binary_filename)
        return

    # Get DLL imports from PE file
    for imported_module in pe.DIRECTORY_ENTRY_IMPORT:
        dll_filename = imported_module.dll.decode()

        # Try to guess DLL path from scan dirs
        for scan_dir in scan_dirs:
            try:
                guessed_path = os.path.join(scan_dir, dll_filename)
                if os.path.isfile(guessed_path):
                    dll_filename = guessed_path
                    break
            except TypeError:
                pass

        dll_name = os.path.basename(dll_filename).upper()

        # Win API can be assumed.
        if dll_name.startswith("API-MS-WIN-") or \
                dll_name.startswith("EXT-MS-WIN-"):
            continue

        # MFC140U.DLL, MFCM140U.DLL may be excluded too since it comes with VC2015 redist, which we can assume
        # is installed on target machine anyway, even if pythonwin distributes it's own copies of those DLLs
        if dll_name in ("SHELL32.DLL", "USER32.DLL", "KERNEL32.DLL",
                        "NTDLL.DLL", "NETUTILS.DLL", "LOGONCLI.DLL", "GDI32.DLL",
                        "RPCRT4.DLL", "ADVAPI32.DLL", "SSPICLI.DLL", "SECUR32.DLL",
                        "KERNELBASE.DLL", "WINBRAND.DLL", "DSROLE.DLL", "DNSAPI.DLL",
                        "SAMCLI.DLL", "WKSCLI.DLL", "SAMLIB.DLL", "WLDAP32.DLL",
                        "NTDSAPI.DLL", "CRYPTBASE.DLL", "W32TOPL", "WS2_32.DLL",
                        "SPPC.DLL", "MSSIGN32.DLL", "CERTCLI.DLL", "WEBSERVICES.DLL",
                        "AUTHZ.DLL", "CERTENROLL.DLL", "VAULTCLI.DLL", "REGAPI.DLL",
                        "BROWCLI.DLL", "WINNSI.DLL", "DHCPCSVC6.DLL", "PCWUM.DLL",
                        "CLBCATQ.DLL", "IMAGEHLP.DLL", "MSASN1.DLL", "DBGHELP.DLL",
                        "DEVOBJ.DLL", "DRVSTORE.DLL", "CABINET.DLL", "SCECLI.DLL",
                        "SPINF.DLL", "SPFILEQ.DLL", "GPAPI.DLL", "NETJOIN.DLL",
                        "W32TOPL.DLL", "NETBIOS.DLL", "DXGI.DLL", "DWRITE.DLL",
                        "D3D11.DLL", "WLANAPI.DLL", "WLANUTIL.DLL", "ONEX.DLL",
                        "EAPPPRXY.DLL", "MFPLAT.DLL", "AVRT.DLL", "ELSCORE.DLL",
                        "INETCOMM.DLL", "MSOERT2.DLL", "IEUI.DLL", "MSCTF.DLL",
                        "MSFEEDS.DLL", "UIAUTOMATIONCORE.DLL", "PSAPI.DLL",
                        "EFSADU.DLL", "MFC42U.DLL", "ODBC32.DLL", "OLEDLG.DLL",
                        "NETAPI32.DLL", "LINKINFO.DLL", "DUI70.DLL", "ADVPACK.DLL",
                        "NTSHRUI.DLL", "WINSPOOL.DRV", "EFSUTIL.DLL", "WINSCARD.DLL",
                        "SHDOCVW.DLL", "IEFRAME.DLL", "D2D1.DLL", "GDIPLUS.DLL",
                        "OCCACHE.DLL", "IEADVPACK.DLL", "MLANG.DLL", "MSI.DLL",
                        "MSHTML.DLL", "COMDLG32.DLL", "PRINTUI.DLL", "PUIAPI.DLL",
                        "ACLUI.DLL", "WTSAPI32.DLL", "FMS.DLL", "DFSCLI.DLL",
                        "HLINK.DLL", "MSRATING.DLL", "PRNTVPT.DLL", "IMGUTIL.DLL",
                        "MSLS31.DLL", "VERSION.DLL", "NORMALIZ.DLL", "IERTUTIL.DLL",
                        "WININET.DLL", "WINTRUST.DLL", "XMLLITE.DLL", "APPHELP.DLL",
                        "PROPSYS.DLL", "RSTRTMGR.DLL", "NCRYPT.DLL", "BCRYPT.DLL",
                        "MMDEVAPI.DLL", "MSILTCFG.DLL", "DEVMGR.DLL", "DEVRTL.DLL",
                        "NEWDEV.DLL", "VPNIKEAPI.DLL", "WINHTTP.DLL", "WEBIO.DLL",
                        "NSI.DLL", "DHCPCSVC.DLL", "CRYPTUI.DLL", "ESENT.DLL",
                        "DAVHLPR.DLL", "CSCAPI.DLL", "ATL.DLL", "OLEAUT32.DLL",
                        "SRVCLI.DLL", "RASDLG.DLL", "MPRAPI.DLL", "RTUTILS.DLL",
                        "RASMAN.DLL", "MPRMSG.DLL", "SLC.DLL", "CRYPTSP.DLL",
                        "RASAPI32.DLL", "TAPI32.DLL", "EAPPCFG.DLL", "NDFAPI.DLL",
                        "WDI.DLL", "COMCTL32.DLL", "UXTHEME.DLL", "IMM32.DLL",
                        "OLEACC.DLL", "WINMM.DLL", "WINDOWSCODECS.DLL", "DWMAPI.DLL",
                        "DUSER.DLL", "PROFAPI.DLL", "URLMON.DLL", "SHLWAPI.DLL",
                        "LPK.DLL", "USP10.DLL", "CFGMGR32.DLL", "MSIMG32.DLL",
                        "POWRPROF.DLL", "SETUPAPI.DLL", "WINSTA.DLL", "CRYPT32.DLL",
                        "IPHLPAPI.DLL", "MPR.DLL", "CREDUI.DLL", "NETPLWIZ.DLL",
                        "OLE32.DLL", "ACTIVEDS.DLL", "ADSLDPC.DLL", "USERENV.DLL",
                        "APPREPAPI.DLL", "BCP47LANGS.DLL", "BCRYPTPRIMITIVES.DLL",
                        "CERTCA.DLL", "CHARTV.DLL", "COMBASE.DLL", "COML2.DLL",
                        "DCOMP.DLL", "DPAPI.DLL", "DSPARSE.DLL", "FECLIENT.DLL",
                        "FIREWALLAPI.DLL", "FLTLIB.DLL", "MRMCORER.DLL", "NTASN1.DLL",
                        "SECHOST.DLL", "SETTINGSYNCPOLICY.DLL", "SHCORE.DLL", "TBS.DLL",
                        "TWINAPI.APPCORE.DLL", "TWINAPI.DLL", "VIRTDISK.DLL",
                        "WEBSOCKET.DLL", "WEVTAPI.DLL", "WINMMBASE.DLL", "WMICLNT.DLL",
                        "ICUUC.DLL", "MFC140U.DLL", "MFCM140U.DLL"):
            continue

        # Allow plugins to prevent inclusion.
        blocked = Plugins.removeDllDependencies(
            dll_filename  = dll_filename,
            dll_filenames = result
        )

        for to_remove in blocked:
            result.discard(to_remove)

        result.add(
            os.path.normcase(os.path.abspath(dll_filename))
        )


def _detectBinaryPathDLLsWindowsPE(is_main_executable, source_dir, original_dir, binary_filename, package_name):
    # This is complex, as it also includes the caching mechanism
    # pylint: disable=too-many-branches,too-many-locals

    result = set()

    cache_filename = _getCacheFilename(is_main_executable, source_dir, original_dir, binary_filename)

    if os.path.exists(cache_filename) and not Options.shallNotUseDependsExeCachedResults():
        for line in open(cache_filename):
            line = line.strip()

            result.add(line)

        return result

    scan_dirs = [sys.prefix]

    if package_name is not None:
        from nuitka.importing.Importing import findModule

        package_dir = findModule(None, package_name, None, 0, False)[1]

        if os.path.isdir(package_dir):
            scan_dirs.append(package_dir)
            scan_dirs.extend(getSubDirectories(package_dir))

    if os.path.isdir(original_dir):
        scan_dirs.append(original_dir)
        scan_dirs.extend(getSubDirectories(original_dir))

    if Options.isExperimental("use_pefile_fullrecurse"):
        try:
            scan_dirs.extend(getSubDirectories(get_python_lib()))
        except OSError:
            print("Cannot recurse into site-packages for dependencies. Path not found.")
    else:
        # Fix for missing pywin32 inclusion when using pythonwin library, no way to detect that automagically
        # Since there are more than one dependencies on pywintypes37.dll, let's include this anyway
        # In recursive mode, using dirname(original_dir) won't always work, hence get_python_lib
        try:
            scan_dirs.append(os.path.join(get_python_lib(), "pywin32_system32"))
        except OSError:
            pass

    # Add native system directory based on pe file architecture and os architecture
    # Python 32: system32 = syswow64 = 32 bits systemdirectory
    # Python 64: system32 = 64 bits systemdirectory, syswow64 = 32 bits systemdirectory
    binary_file_is_64bit = _isPE64(binary_filename)
    python_is_64bit = getArchitecture() == "x86_64"
    if binary_file_is_64bit is not python_is_64bit:
        print("Warning: Using Python x64=%s with x64=%s binary dependencies" % (binary_file_is_64bit, python_is_64bit))

    if binary_file_is_64bit:
        # This is actually not useful as of today since we don't compile 32 bits on 64 bits
        if python_is_64bit:
            scan_dirs.append(os.path.join(os.environ["SYSTEMROOT"], "System32"))
        else:
            scan_dirs.append(os.path.join(os.environ["SYSTEMROOT"], "SysWOW64"))
    else:
        scan_dirs.append(os.path.join(os.environ["SYSTEMROOT"], "System32"))

    if Options.isExperimental("use_pefile_recurse"):
        # Recursive one level scanning of all .pyd and .dll in the original_dir too
        # This shall fix a massive list of missing dependencies that may come with included libraries which themselves
        # need to be scanned for inclusions
        for root, _, filenames in os.walk(original_dir):
            for optional_libary in filenames:
                if optional_libary.endswith(".dll") or optional_libary.endswith(".pyd"):
                    _parsePEFileOutput(os.path.join(root, optional_libary), scan_dirs, result)

    _parsePEFileOutput(binary_filename, scan_dirs, result)

    if not Options.shallNotStoreDependsExeCachedResults():
        with open(cache_filename, 'w') as cache_file:
            for dll_filename in result:
                print(dll_filename, file = cache_file)

    return result

def detectBinaryDLLs(is_main_executable, source_dir, original_filename,
                     binary_filename, package_name):
    """ Detect the DLLs used by a binary.

        Using "ldd" (Linux), "depends.exe" (Windows), or "otool" (macOS) the list
        of used DLLs is retrieved.
    """

    if Utils.getOS() in ("Linux", "NetBSD", "FreeBSD"):
        return _detectBinaryPathDLLsLinuxBSD(
            dll_filename = original_filename
        )
    elif Utils.getOS() == "Windows":
        if Options.isExperimental("use_pefile"):
            with TimerReport("Running internal dependency walker for %s took %%.2f seconds" % binary_filename):
                return _detectBinaryPathDLLsWindowsPE(
                    is_main_executable = is_main_executable,
                    source_dir         = source_dir,
                    original_dir       = os.path.dirname(original_filename),
                    binary_filename    = binary_filename,
                    package_name       = package_name
                )
        else:
            with TimerReport("Running depends.exe for %s took %%.2f seconds" % binary_filename):
                return _detectBinaryPathDLLsWindows(

                    is_main_executable = is_main_executable,
                    source_dir         = source_dir,
                    original_dir       = os.path.dirname(original_filename),
                    binary_filename    = binary_filename,
                    package_name       = package_name
                )
    elif Utils.getOS() == "Darwin":
        return _detectBinaryPathDLLsMacOS(
            original_dir    = os.path.dirname(original_filename),
            binary_filename = original_filename
        )
    else:
        # Support your platform above.
        assert False, Utils.getOS()


_unfound_dlls = set()

def detectUsedDLLs(source_dir, standalone_entry_points):
    def addDLLInfo(count, source_dir, original_filename, binary_filename, package_name):
        used_dlls = detectBinaryDLLs(
            is_main_executable = count == 0,
            source_dir         = source_dir,
            original_filename  = original_filename,
            binary_filename    = binary_filename,
            package_name       = package_name
        )

        for dll_filename in sorted(tuple(used_dlls)):
            if not os.path.isfile(dll_filename):
                if _unfound_dlls:
                    warning(
                        """\
Dependency '%s' could not be found, you might need to copy it
manually."""  % dll_filename
                    )

                    _unfound_dlls.add(dll_filename)

                used_dlls.remove(dll_filename)

        return binary_filename, used_dlls

    result = OrderedDict()

    with ThreadPoolExecutor(max_workers = Utils.getCoreCount() * 3) as worker_pool:
        workers = []

        for count, (original_filename, binary_filename, package_name) in enumerate(standalone_entry_points):
            workers.append(
                worker_pool.submit(
                    addDLLInfo,
                    count, source_dir, original_filename, binary_filename, package_name
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


def fixupBinaryDLLPaths(binary_filename, is_exe, dll_map):
    """ For macOS, the binary needs to be told to use relative DLL paths """

    # There may be nothing to do, in case there are no DLLs.
    if not dll_map:
        return

    command = [
        "install_name_tool"
    ]

    for original_path, dist_path in dll_map:
        command += [
            "-change",
            original_path,
            "@executable_path/" + dist_path,
        ]

    os.chmod(binary_filename, int("644", 8))
    command.append(binary_filename)
    process = subprocess.Popen(
        args   = command,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    _stdout, stderr = process.communicate()
    os.chmod(binary_filename, int("755" if is_exe else "444", 8))

    # Don't let errors here go unnoticed.
    assert process.returncode == 0, stderr


def getSharedLibraryRPATH(filename):
    process = subprocess.Popen(
        ["readelf", "-d", filename],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        shell  = False
    )

    stdout, stderr = process.communicate()
    retcode = process.poll()

    if retcode != 0:
        sys.exit(
            "Error reading shared library path for %s, tool said %r" % (
                filename,
                stderr
            )
        )

    for line in stdout.split(b"\n"):
        if b"RPATH" in line or b"RUNPATH" in line:
            return line[line.find(b'[')+1:line.rfind(b']')]

    return None


def removeSharedLibraryRPATH(filename):
    rpath = getSharedLibraryRPATH(filename)

    if rpath is not None:
        if Options.isShowInclusion():
            info("Removing 'RPATH' setting from '%s'.", filename)

        if not Utils.isExecutableCommand("chrpath"):
            sys.exit(
                """\
Error, needs 'chrpath' on your system, due to 'RPATH' settings in used shared
libraries that need to be removed."""
            )

        os.chmod(filename, int("644", 8))
        process = subprocess.Popen(
            ["chrpath", "-d", filename],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            shell  = False
        )
        process.communicate()
        retcode = process.poll()
        os.chmod(filename, int("444", 8))

        assert retcode == 0, filename


def copyUsedDLLs(source_dir, dist_dir, standalone_entry_points):
    # This is terribly complex, because we check the list of used DLLs
    # trying to avoid duplicates, and detecting errors with them not
    # being binary identical, so we can report them. And then of course
    # we also need to handle OS specifics.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    used_dlls = detectUsedDLLs(source_dir, standalone_entry_points)

    removed_dlls = set()

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
            if os.path.basename(dll_filename1) != \
               os.path.basename(dll_filename2):
                continue

            # May already have been removed earlier
            if dll_filename1 not in used_dlls:
                continue

            if dll_filename2 not in used_dlls:
                continue

            dll_name = os.path.basename(dll_filename1)

            if Options.isShowInclusion():
                info(
                     """Colliding DLL names for %s, checking identity of \
'%s' <-> '%s'.""" % (
                        dll_name,
                        dll_filename1,
                        dll_filename2,
                    )
                )

            # Check that if a DLL has the same name, if it's identical,
            # happens at least for OSC and Fedora 20.
            import filecmp
            if filecmp.cmp(dll_filename1, dll_filename2):
                del used_dlls[dll_filename2]
                removed_dlls.add(dll_filename2)

                continue

            # For Win32 we can check out file versions.
            if os.name == "nt":
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
                    warning("Ignoring conflicting DLLs for '%s' and using newest file version." % dll_name)
                    continue

            # So we have conflicting DLLs, in which case we do not proceed.
            warning(
                """Ignoring non-identical DLLs for '%s'.
%s used by:
   %s
different from
%s used by
   %s""" % (
                    dll_name,
                    dll_filename1,
                    "\n   ".join(sources1),
                    dll_filename2,
                    "\n   ".join(sources2)
                )
            )

            del used_dlls[dll_filename2]
            removed_dlls.add(dll_filename2)

    dll_map = []

    for dll_filename, sources in iterItems(used_dlls):
        dll_name = os.path.basename(dll_filename)

        target_path = os.path.join(
            dist_dir,
            dll_name
        )

        shutil.copyfile(
            dll_filename,
            target_path
        )

        dll_map.append(
            (dll_filename, dll_name)
        )

        if Options.isShowInclusion():
            info(
                 "Included used shared library '%s' (used by %s)." % (
                    dll_filename,
                    ", ".join(sources)
                 )
            )

    if Utils.getOS() == "Darwin":
        # For macOS, the binary and the DLLs needs to be changed to reflect
        # the relative DLL location in the ".dist" folder.
        for standalone_entry_point in standalone_entry_points:
            fixupBinaryDLLPaths(
                binary_filename = standalone_entry_point[1],
                is_exe          = standalone_entry_point is standalone_entry_points[0],
                dll_map         = dll_map
            )

        for _original_path, dll_filename in dll_map:
            fixupBinaryDLLPaths(
                binary_filename = os.path.join(
                    dist_dir,
                    dll_filename
                ),
                is_exe          = False,
                dll_map         = dll_map
            )

    if Utils.getOS() == "Linux":
        # For Linux, the "rpath" of libraries may be an issue and must be
        # removed.
        for standalone_entry_point in standalone_entry_points[1:]:
            removeSharedLibraryRPATH(
                standalone_entry_point[1]
            )

        for _original_path, dll_filename in dll_map:
            removeSharedLibraryRPATH(
                os.path.join(dist_dir, dll_filename)
            )
    elif os.name == "nt":
        if python_version < 300:
            # For Win32, we might have to remove SXS paths
            for standalone_entry_point in standalone_entry_points[1:]:
                removeSxsFromDLL(
                    standalone_entry_point[1]
                )

            for _original_path, dll_filename in dll_map:
                removeSxsFromDLL(
                    os.path.join(dist_dir, dll_filename)
                )
