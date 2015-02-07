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
""" Pack and copy files for standalone mode.

This is still under heavy evolution, but expected to work for
MacOS, Windows, and Linux. Patches for other platforms are
very welcome.
"""

import os
import shutil
import subprocess
import sys
from logging import debug, info, warning

import marshal
from nuitka import Options, Tracing, Utils
from nuitka.__past__ import (  # pylint: disable=W0622
    iterItems,
    raw_input,
    urlretrieve
)
from nuitka.codegen.ConstantCodes import needsPickleInit
from nuitka.Importing import getStandardLibraryPaths
from nuitka.tree.SourceReading import readSourceCodeFromFilename


def getDependsExePath():
    """ Return the path of depends.exe (for Windows).

        Will prompt the user to download if not already cached in AppData
        directory for Nuitka.
    """
    if Utils.getArchitecture() == "x86":
        depends_url = "http://dependencywalker.com/depends22_x86.zip"
    else:
        depends_url = "http://dependencywalker.com/depends22_x64.zip"

    if "APPDATA" not in os.environ:
        sys.exit("Error, standalone mode cannot find 'APPDATA' environment.")

    nuitka_app_dir = Utils.joinpath(os.environ["APPDATA"], "nuitka")
    if not Utils.isDir(nuitka_app_dir):
        Utils.makePath(nuitka_app_dir)

    nuitka_depends_zip = Utils.joinpath(
        nuitka_app_dir,
        Utils.basename(depends_url)
    )

    if not Utils.isFile(nuitka_depends_zip):
        Tracing.printLine("""\
Nuitka will make use of Dependency Walker (http://dependencywalker.com) tool
to analyze the dependencies of Python extension modules. Is it OK to download
and put it in APPDATA (no installer needed, cached, one time question).""")

        reply = raw_input("Proceed and download? [Yes]/No ")

        if reply.lower() in ("no", 'n'):
            sys.exit("Nuitka does not work in --standalone on Windows without.")

        info("Downloading '%s'" % depends_url)

        urlretrieve(
            depends_url,
            nuitka_depends_zip
        )

    nuitka_depends_dir = Utils.joinpath(
        nuitka_app_dir,
        Utils.getArchitecture()
    )

    if not Utils.isDir(nuitka_depends_dir):
        os.makedirs(nuitka_depends_dir)

    depends_exe = os.path.join(
        nuitka_depends_dir,
        "depends.exe"
    )

    if not Utils.isFile(depends_exe):
        info("Extracting to '%s'" % depends_exe)

        import zipfile

        try:
            depends_zip = zipfile.ZipFile(nuitka_depends_zip)
            depends_zip.extractall(nuitka_depends_dir)
        except Exception: # Catching anything zip throws, pylint:disable=W0703
            info("Problem with the downloaded zip file, deleting it.")

            Utils.deleteFile(depends_exe, must_exist = False)
            Utils.deleteFile(nuitka_depends_zip, must_exist = True)

            sys.exit(
                "Error, need '%s' as extracted from '%s'." % (
                    depends_exe,
                    depends_url
                )
            )

    assert Utils.isFile(depends_exe)

    return depends_exe


def loadCodeObjectData(precompiled_filename):
    # Ignoring magic numbers, etc. which we don't have to care for much as
    # CPython already checked them (would have rejected it otherwise).
    return open(precompiled_filename, "rb").read()[8:]


module_names = set()

def _detectedPrecompiledFile(filename, module_name, result, is_late):
    if filename.endswith(b".pyc"):
        if Utils.isFile(filename[:-1]):
            return _detectedSourceFile(
                filename    = filename[:-1],
                module_name = module_name,
                result      = result,
                is_late     = is_late
            )

    if Utils.python_version >= 300:
        filename = filename.decode("utf-8")

    if module_name in module_names:
        return

    debug(
        "Freezing module '%s' (from '%s').",
        module_name,
        filename
    )

    result.append(
        (
            module_name,
            loadCodeObjectData(
                precompiled_filename = filename
            ),
            "__init__" in filename,
            filename,
            is_late
        ),
    )

    module_names.add(module_name)


def _detectedSourceFile(filename, module_name, result, is_late):
    if module_name in module_names:
        return

    if module_name == "collections.abc":
        _detectedSourceFile(
            filename    = filename,
            module_name = "_collections_abc",
            result      = result,
            is_late     = is_late
        )

    source_code = readSourceCodeFromFilename(filename)

    if Utils.python_version >= 300:
        filename = filename.decode("utf-8")

    if module_name == "site":
        source_code = """\
__file__ = (__nuitka_binary_dir + '%s%s') if '__nuitka_binary_dir' in dict(__builtins__ ) else '<frozen>';%s""" % (
            os.path.sep,
            Utils.basename(filename),
            source_code
        )

    debug(
        "Freezing module '%s' (from '%s').",
        module_name,
        filename
    )

    result.append(
        (
            module_name,
            marshal.dumps(
                compile(source_code, filename, "exec")
            ),
            Utils.basename(filename) == "__init__.py",
            filename,
            is_late
        )
    )

    module_names.add(module_name)


def _detectedShlibFile(filename, module_name):
    if Utils.python_version >= 300:
        filename = filename.decode("utf-8")

    # That is not a shared library, but looks like one.
    if module_name == "__main__":
        return

    parts = module_name.split('.')
    if len(parts) == 1:
        package_name = None
        name = module_name
    else:
        package_name = '.'.join(parts[:-1])
        name = parts[-1]

    from nuitka.nodes.FutureSpecs import FutureSpec
    from nuitka.nodes.ModuleNodes import PythonShlibModule
    from nuitka import SourceCodeReferences

    source_ref = SourceCodeReferences.fromFilename(
        filename    = filename,
        future_spec = FutureSpec()
    )

    shlib_module = PythonShlibModule(
        name         = name,
        package_name = package_name,
        source_ref   = source_ref
    )

    from nuitka import ModuleRegistry
    ModuleRegistry.addRootModule(shlib_module)

    module_names.add(module_name)


def _detectImports(command, is_late):
    # This is pretty complicated stuff, with variants to deal with.
    # pylint: disable=R0912,R0914

    # Print statements for stuff to show, the modules loaded.
    if Utils.python_version >= 300:
        command += '\nimport sys\nprint("\\n".join(sorted("import " + module.__name__ + " # sourcefile " + ' \
                   'module.__file__ for module in sys.modules.values() if hasattr(module, "__file__") and ' \
                   'module.__file__ != "<frozen>")), file = sys.stderr)'  # do not read it

    reduced_path = list(sys.path)

    reduced_path = [
        path_element
        for path_element in
        sys.path
        if not Utils.areSamePaths(
            path_element,
            '.'
        )
        if not Utils.areSamePaths(
            path_element,
            Utils.dirname(sys.modules["__main__"].__file__)
        )
    ]

    # Make sure the right import path (the one Nuitka binary is running with)
    # is used.
    command = ("import sys; sys.path = %s;" % repr(reduced_path)) + command

    import tempfile
    tmp_file, tmp_filename = tempfile.mkstemp()

    try:
        if Utils.python_version >= 300:
            command = command.encode("ascii")
        os.write(tmp_file, command)
        os.close(tmp_file)

        process = subprocess.Popen(
            args   = [sys.executable, "-s", "-S", "-v", tmp_filename],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )
        _stdout, stderr = process.communicate()
    finally:
        os.unlink(tmp_filename)

    # Don't let errors here go unnoticed.
    if process.returncode != 0:
        warning("There is a problem with detecting imports, CPython said:")
        for line in stderr.split(b"\n"):
            Tracing.printLine(line)
        sys.exit("Error, please report the issue with above output.")

    result = []

    debug("Detecting imports:")

    for line in stderr.replace(b"\r", b"").split(b"\n"):
        if line.startswith(b"import "):
            # print(line)

            parts = line.split(b" # ", 2)

            module_name = parts[0].split(b" ", 2)[1]
            origin = parts[1].split()[0]

            if Utils.python_version >= 300:
                module_name = module_name.decode("utf-8")

            if origin == b"precompiled":
                # This is a ".pyc" file that was imported, even before we have a
                # chance to do anything, we need to preserve it.
                filename = parts[1][len(b"precompiled from "):]

                _detectedPrecompiledFile(
                    filename    = filename,
                    module_name = module_name,
                    result      = result,
                    is_late     = is_late
                )
            elif origin == b"sourcefile":
                filename = parts[1][len(b"sourcefile "):]

                if filename.endswith(b".py"):
                    _detectedSourceFile(
                        filename    = filename,
                        module_name = module_name,
                        result      = result,
                        is_late     = is_late
                    )
                elif not filename.endswith(b"<frozen>"):
                    _detectedShlibFile(
                        filename    = filename,
                        module_name = module_name
                    )
            elif origin == b"dynamically":
                # Shared library in early load, happens on RPM based systems and
                # or self compiled Python installations.
                filename = parts[1][len(b"dynamically loaded from "):]

                _detectedShlibFile(
                    filename    = filename,
                    module_name = module_name
                )

    return result


def detectLateImports():
    command = ""
    # When we are using pickle internally (for some hard constant cases we do),
    # we need to make sure it will be available as well.
    if needsPickleInit():
        command += "import {pickle};".format(
            pickle = "pickle" if Utils.python_version >= 300 else "cPickle"
        )

    # For Python3 we patch inspect without knowing if it is used.
    if Utils.python_version >= 300:
        command += "import inspect;"

    if command:
        result = _detectImports(command, True)

        debug("Finished detecting late imports.")

        return result
    else:
        return ""

# Some modules we want to blacklist.
ignore_modules = [
    "__main__.py",
    "__init__.py",
    "antigravity.py",
]
if Utils.getOS() != "Windows":
    ignore_modules.append("wintypes.py")
    ignore_modules.append("cp65001.py")

def scanStandardLibraryPath(stdlib_dir):
    # There is a lot of black-listing here, done in branches, so there
    # is many of them, but that's acceptable, pylint: disable=R0912

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

        if import_path in ("tkinter", "importlib", "ctypes"):
            if "test" in dirs:
                dirs.remove("test")

        if import_path == "lib2to3":
            if "tests" in dirs:
                dirs.remove("tests")

        if Utils.python_version >= 340 and Utils.getOS() == "Windows":
            if import_path == "multiprocessing":
                filenames.remove("popen_fork.py")
                filenames.remove("popen_forkserver.py")
                filenames.remove("popen_spawn_posix.py")

        for filename in filenames:
            if filename.endswith(".py") and filename not in ignore_modules:
                module_name = filename[:-3]
                if import_path == "":
                    yield module_name
                else:
                    yield import_path + '.' + module_name

        if Utils.python_version >= 300:
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")

        for dirname in dirs:
            if import_path == "":
                yield dirname
            else:
                yield import_path + '.' + dirname


def detectEarlyImports():
    if Options.freezeAllStdlib():
        stdlib_modules = set()

        # Scan the standard library paths (multiple in case of virtualenv.
        for stdlib_dir in getStandardLibraryPaths():
            for module_name in scanStandardLibraryPath(stdlib_dir):
                stdlib_modules.add(module_name)

        import_code = "imports = " + repr(sorted(stdlib_modules)) + '\n'\
                      "for imp in imports:\n" \
                      "    try:\n" \
                      "        __import__(imp)\n" \
                      "    except ImportError:\n" \
                      "        pass\n"
    else:
        # TODO: Should recursively include all of encodings module.
        import_code = "import encodings.utf_8;import encodings.ascii;import encodings.idna;"

        if Utils.getOS() == "Windows":
            import_code += "import encodings.mbcs;import encodings.cp437;"

        # String method hex depends on it.
        if Utils.python_version < 300:
            import_code += "import encodings.hex_codec;"

        import_code += "import locale;"

    result = _detectImports(import_code, False)
    debug("Finished detecting early imports.")

    return result


def _detectBinaryPathDLLsLinuxBSD(binary_filename):
    # Ask "ldd" about the libraries being used by the created binary, these
    # are the ones that interest us.
    result = set()

    process = subprocess.Popen(
        args   = [
            "ldd",
            binary_filename
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

        if Utils.python_version >= 300:
            filename = filename.decode("utf-8")

        result.add(filename)

    return result

def _detectBinaryPathDLLsMacOS(binary_filename):
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
    for line in stdout.split(b"\n"):
        if not line:
            continue

        if line.startswith(b"\t"):
            filename = line.split(b" (")[0].strip()
            stop = False
            for w in system_paths:
                if filename.startswith(w):
                    stop = True
                    break
            if not stop:
                if Utils.python_version >= 300:
                    filename = filename.decode("utf-8")

                # print "adding", filename
                result.add(filename)

    return result


def _makeBinaryPathPathDLLSearchEnv(package_name):
    # Put the PYTHONPATH into the system "PATH", DLLs frequently live in
    # the package directories.
    env = os.environ.copy()
    path = env.get("PATH","").split(';')

    # Put the "Python.exe" first. At least for WinPython, they put the DLLs
    # there.
    path = [sys.prefix] + sys.path + path

    if package_name is not None:
        for element in sys.path:
            candidate = Utils.joinpath(element, package_name)

            if Utils.isDir(candidate):
                path.append(candidate)


    env["PATH"] = ';'.join(path)

    return env


def _detectBinaryPathDLLsWindows(binary_filename, package_name):
    result = set()

    depends_exe = getDependsExePath()

    # The search order by default prefers the system directory, where a
    # wrong "PythonXX.dll" might be living.
    with open(binary_filename + ".dwp", 'w') as dwp_file:
        dwp_file.write("""\
KnownDLLs
SysPath
AppDir
32BitSysDir
16BitSysDir
OSDir
AppPath
SxS
""")

    subprocess.call(
        (
            depends_exe,
            "-c",
            "-ot%s" % binary_filename + ".depends",
            "-d:%s" % binary_filename + ".dwp",
            "-f1",
            "-pa1",
            "-ps1",
            binary_filename
        ),
        env = _makeBinaryPathPathDLLSearchEnv(package_name),
    )

    inside = False
    for line in open(binary_filename + ".depends"):
        if "| Module Dependency Tree |" in line:
            inside = True
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

        dll_filename = line[line.find(']')+2:-1]
        assert Utils.isFile(dll_filename), dll_filename

        # The executable itself is of course exempted.
        if Utils.normcase(dll_filename) == \
            Utils.normcase(Utils.abspath(binary_filename)):
            continue

        dll_name = Utils.basename(dll_filename).upper()

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
            "CERTCA.DLL", "CHARTV.DLL", "COMBASE.DLL", "DCOMP.DLL",
            "DPAPI.DLL", "DSPARSE.DLL", "FECLIENT.DLL", "FIREWALLAPI.DLL",
            "FLTLIB.DLL", "MRMCORER.DLL", "MSVCRT.DLL",
            "NINPUT.DLL", "NTASN1.DLL", "PCACLI.DLL", "RTWORKQ.DLL",
            "SECHOST.DLL", "SETTINGSYNCPOLICY.DLL", "SHCORE.DLL",
            "TBS.DLL", "TWINAPI.DLL", "TWINAPI.APPCORE.DLL", "VIRTDISK.DLL",
            "WEBSOCKET.DLL", "WEVTAPI.DLL", "WINMMBASE.DLL", "WMICLNT.DLL"):
            continue

        result.add(
            Utils.normcase(Utils.abspath(dll_filename))
        )

    Utils.deleteFile(binary_filename + ".depends", must_exist = True)
    Utils.deleteFile(binary_filename + ".dwp", must_exist = True)

    return result

def detectBinaryDLLs(binary_filename, package_name):
    """ Detect the DLLs used by a binary.

        Using "ldd" (Linux), "depends.exe" (Windows), or "otool" (MacOS) the list
        of used DLLs is retrieved.
    """


    if Utils.getOS() in ("Linux", "NetBSD"):
        # TODO: FreeBSD may work the same way, not tested.

        return _detectBinaryPathDLLsLinuxBSD(
            binary_filename = binary_filename
        )
    elif Utils.getOS() == "Windows":
        return _detectBinaryPathDLLsWindows(
            binary_filename = binary_filename,
            package_name    = package_name
        )
    elif Utils.getOS() == "Darwin":
        return _detectBinaryPathDLLsMacOS(
            binary_filename = binary_filename
        )
    else:
        # Support your platform above.
        assert False, Utils.getOS()


def detectUsedDLLs(standalone_entry_points):
    result = {}

    for binary_filename, package_name in standalone_entry_points:
        used_dlls = detectBinaryDLLs(
            binary_filename = binary_filename,
            package_name    = package_name
        )

        for dll_filename in used_dlls:
            if dll_filename not in result:
                result[dll_filename] = []

            result[dll_filename].append(binary_filename)

    return result


def fixupBinaryDLLPaths(binary_filename, is_exe, dll_map):
    """ For MacOS, the binary needs to be told to use relative DLL paths """

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


def removeSharedLibraryRPATH(filename):
    process = subprocess.Popen(
        ["readelf", "-d", filename],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        shell  = False
    )

    stdout, _stderr = process.communicate()
    retcode = process.poll()

    assert retcode == 0, filename

    for line in stdout.split(b"\n"):
        if b"RPATH" in line:
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


def copyUsedDLLs(dist_dir, standalone_entry_points):
    # This is terribly complex, because we check the list of used DLLs
    # trying to avoid duplicates, and detecting errors with them not
    # being binary identical, so we can report them. And then of course
    # we also need to handle OS specifics, pylint: disable=R0912

    dll_map = []

    used_dlls = detectUsedDLLs(standalone_entry_points)

    for dll_filename1, sources1 in tuple(iterItems(used_dlls)):
        for dll_filename2, sources2 in tuple(iterItems(used_dlls)):
            if dll_filename1 == dll_filename2:
                continue

            # Colliding basenames are an issue to us.
            if Utils.basename(dll_filename1) != Utils.basename(dll_filename2):
                continue

            # May already have been removed earlier
            if dll_filename1 not in used_dlls:
                continue

            if dll_filename2 not in used_dlls:
                continue

            dll_name = Utils.basename(dll_filename1)

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
                continue

            sys.exit(
                """Error, conflicting DLLs for '%s' \
(%s used by %s different from %s used by %s).""" % (
                    dll_name,
                    dll_filename1,
                    ", ".join(sources1),
                    dll_filename2,
                    ", ".join(sources2)
                )
            )

    for dll_filename, sources in iterItems(used_dlls):
        dll_name = Utils.basename(dll_filename)

        target_path = Utils.joinpath(
            dist_dir,
            dll_name
        )

        shutil.copy(
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
        # For MacOS, the binary and the DLLs needs to be changed to reflect
        # the relative DLL location in the ".dist" folder.
        for standalone_entry_point in standalone_entry_points:
            fixupBinaryDLLPaths(
                binary_filename = standalone_entry_point[0],
                is_exe          = standalone_entry_point is standalone_entry_points[0],
                dll_map         = dll_map
            )

        for _original_path, dll_filename in dll_map:
            fixupBinaryDLLPaths(
                binary_filename = Utils.joinpath(
                    dist_dir,
                    dll_filename
                ),
                is_exe          = False,
                dll_map         = dll_map
            )

    if Utils.getOS() == "Linux":
        # For Linux, the "rpath" of libraries may be an issue and must be
        # removed.
        for _original_path, dll_filename in dll_map:
            removeSharedLibraryRPATH(
                Utils.joinpath(dist_dir, dll_filename)
            )

        for standalone_entry_point in standalone_entry_points[1:]:
            removeSharedLibraryRPATH(
                standalone_entry_point[0]
            )
