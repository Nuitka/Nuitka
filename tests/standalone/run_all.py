#!/usr/bin/env python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )
)
from nuitka.tools.testing.Common import (
    my_print,
    setup,
    hasModule,
    compareWithCPython,
    decideFilenameVersionSkip,
    getRuntimeTraceOfLoadedFiles,
    createSearchMode,
    reportSkip
)
from nuitka.utils.FileOperations import removeDirectory

python_version = setup(needs_io_encoding = True)

search_mode = createSearchMode()

search_mode.mayFailFor(
    # Do not expect PySide to work yet, because it has that bug still
    # where it won't call compiled functions as slots.
    "PySideUsing.py"
)

for filename in sorted(os.listdir('.')):
    if not filename.endswith(".py"):
        continue

    if not decideFilenameVersionSkip(filename):
        continue

    path = os.path.relpath(filename)

    active = search_mode.consider(dirname = None, filename = filename)

    if not active:
        my_print("Skipping", filename)
        continue

    extra_flags = [
        "expect_success",
        "standalone",
        "remove_output"
    ]

    if filename == "PySideUsing.py":
        # Don't test on platforms not supported by current Debian testing, and
        # which should be considered irrelevant by now.
        if python_version.startswith("2.6") or \
           python_version.startswith("3.2"):
            reportSkip("irrelevant Python version", ".", filename)
            continue

        if not hasModule("PySide.QtCore"):
            reportSkip("PySide not installed for this Python version, but test needs it", ".", filename )
            continue

        # For the warnings.
        extra_flags.append("ignore_stderr")

    if "PyQt4" in filename:
        # Don't test on platforms not supported by current Debian testing, and
        # which should be considered irrelevant by now.
        if python_version.startswith("2.6") or \
           python_version.startswith("3.2"):
            reportSkip("irrelevant Python version", ".", filename)
            continue

        if not hasModule("PyQt4.QtGui"):
            reportSkip("PyQt4 not installed for this Python version, but test needs it", ".", filename)
            continue

        # For the plug-in information.
        extra_flags.append("ignore_infos")

    if "Idna" in filename:
        if not hasModule("idna.core"):
            reportSkip("idna not installed for this Python version, but test needs it", ".", filename)
            continue

        # For the warnings of Python2.
        if python_version.startswith("2"):
            extra_flags.append("ignore_stderr")

    if "PyQt5" in filename:
        # Don't test on platforms not supported by current Debian testing, and
        # which should be considered irrelevant by now.
        if python_version.startswith("2.6") or \
           python_version.startswith("3.2"):
            reportSkip("irrelevant Python version", ".", filename)
            continue

        if not hasModule("PyQt5.QtGui"):
            reportSkip("PyQt5 not installed for this Python version, but test needs it", ".", filename)
            continue

        # For the plug-in information.
        extra_flags.append("ignore_infos")

    # TODO: Temporary only
    if os.name == "nt" and "PyQt" in filename:
        continue

    if "PySide" in filename or "PyQt" in filename:
        extra_flags.append("plugin_enable:qt-plugins")

    if filename == "CtypesUsing.py":
        extra_flags.append("plugin_disable:pylint-warnings")

    if filename == "GtkUsing.py":
        # Don't test on platforms not supported by current Debian testing, and
        # which should be considered irrelevant by now.
        if python_version.startswith("2.6") or \
           python_version.startswith("3.2"):
            reportSkip("irrelevant Python version", ".", filename)
            continue

        if not hasModule("pygtk"):
            reportSkip("pygtk not installed for this Python version, but test needs it", ".", filename)
            continue

        # For the warnings.
        extra_flags.append("ignore_stderr")

    if filename.startswith("Win"):
        if os.name != "nt":
            reportSkip("Windows only test", ".", filename)
            continue

    if filename == "Win32ComUsing.py":
        if not hasModule("win32com"):
            reportSkip("win32com not installed for this Python version, but test needs it", ".", filename)
            continue

    if filename == "LxmlUsing.py":
        if not hasModule("lxml.etree"):
            reportSkip("lxml.etree not installed for this Python version, but test needs it", ".", filename)
            continue

    if filename == "TkInterUsing.py":
        if python_version.startswith("2"):
            if not hasModule("Tkinter"):
                reportSkip("Tkinter not installed for this Python version, but test needs it", ".", filename)
                continue
        else:
            if not hasModule("tkinter"):
                reportSkip("tkinter not installed for this Python version, but test needs it", ".", filename)
                continue

            # For the warnings.
            extra_flags.append("ignore_stderr")


    if filename == "FlaskUsing.py":
        if not hasModule("flask"):
            reportSkip( "flask not installed for this Python version, but test needs it", ".", filename)
            continue

        # For the warnings.
        extra_flags.append("ignore_stderr")

    if filename == "NumpyUsing.py":
        # TODO: Disabled for now.
        reportSkip("numpy.test not fully working yet", ".", filename)
        continue

        if not hasModule("numpy"):
            reportSkip("numpy not installed for this Python version, but test needs it", ".", filename)
            continue

        extra_flags.append("plugin_enable:data-files")

    if filename == "PmwUsing.py":
        if not hasModule("Pwm"):
            reportSkip("Pwm not installed for this Python version, but test needs it", ".", filename)
            continue

        extra_flags.append("plugin_enable:pmw-freeze")

    my_print("Consider output of recursively compiled program:", filename)

    # First compare so we know the program behaves identical.
    compareWithCPython(
        dirname     = None,
        filename    = filename,
        extra_flags = extra_flags,
        search_mode = search_mode,
        needs_2to3  = False
    )

    # Second use "strace" on the result.
    loaded_filenames = getRuntimeTraceOfLoadedFiles(
        path = os.path.join(
            filename[:-3] + ".dist",
            filename[:-3] + (".exe" if os.name == "nt" else "")
        )
    )

    current_dir = os.path.normpath(os.getcwd())
    current_dir = os.path.normcase(current_dir)

    illegal_access = False

    for loaded_filename in loaded_filenames:
        loaded_filename = os.path.normpath(loaded_filename)
        loaded_filename = os.path.normcase(loaded_filename)
        loaded_basename = os.path.basename(loaded_filename)

        if loaded_filename.startswith(current_dir):
            continue

        if loaded_filename.startswith(os.path.abspath(current_dir)):
            continue

        if loaded_filename.startswith("/etc/"):
            continue

        if loaded_filename.startswith("/proc/") or loaded_filename == "/proc":
            continue

        if loaded_filename.startswith("/dev/"):
            continue

        if loaded_filename.startswith("/tmp/"):
            continue

        if loaded_filename.startswith("/run/"):
            continue

        if loaded_filename.startswith("/usr/lib/locale/"):
            continue

        if loaded_filename.startswith("/usr/share/locale/"):
            continue

        if loaded_filename.startswith("/usr/share/X11/locale/"):
            continue

        # Themes may of course be loaded.
        if loaded_filename.startswith("/usr/share/themes"):
            continue
        if "gtk" in loaded_filename and "/engines/" in loaded_filename:
            continue

        # Taking these from system is harmless and desirable
        if loaded_basename.startswith((
            "libz.so",
            "libutil.so",
            "libgcc_s.so",
            "libm.so.",
        )):
            continue

        # System C libraries are to be expected.
        if loaded_basename.startswith((
            "libc.so.",
            "libpthread.so.",
            "libdl.so.",
            "libm.so.",
        )):
            continue

        # Loaded by C library potentially for DNS lookups.
        if loaded_basename.startswith((
            "libnss_",
            "libnsl",
        )):
            continue

        # Loaded by dtruss on MacOS X.
        if loaded_filename.startswith("/usr/lib/dtrace/"):
            continue

        # Loaded by cowbuilder and pbuilder on Debian
        if loaded_basename == ".ilist":
            continue
        if "cowdancer" in loaded_filename:
            continue
        if "eatmydata" in loaded_filename:
            continue

        # Loading from home directories is OK too.
        if loaded_filename.startswith("/home/") or \
           loaded_filename.startswith("/data/") or \
           loaded_filename.startswith("/root/") or \
           loaded_filename in ("/home", "/data", "/root"):
            continue

        # For Debian builders, /build is OK too.
        if loaded_filename.startswith("/build/") or \
           loaded_filename == "/build":
            continue

        # TODO: Unclear, loading gconv from filesystem of installed system
        # may be OK or not. I think it should be.
        if loaded_basename == "gconv-modules.cache":
            continue
        if "/gconv/" in loaded_filename:
            continue
        if loaded_basename.startswith("libicu"):
            continue

        # Loading from caches is OK.
        if loaded_filename.startswith("/var/cache/"):
            continue

        # PySide accesses its directory.
        if loaded_filename == "/usr/lib/python" + \
           python_version[:3] + \
              "/dist-packages/PySide":
            continue

        # GTK accesses package directories only.
        if loaded_filename == "/usr/lib/python" + \
           python_version[:3] + \
              "/dist-packages/gtk-2.0/gtk":
            continue
        if loaded_filename == "/usr/lib/python" + \
           python_version[:3] + \
              "/dist-packages/glib":
            continue
        if loaded_filename == "/usr/lib/python" + \
           python_version[:3] + \
              "/dist-packages/gtk-2.0/gio":
            continue
        if loaded_filename == "/usr/lib/python" + \
           python_version[:3] + \
              "/dist-packages/gobject":
            continue

        # PyQt5 seems to do this, but won't use contents then.
        if loaded_filename in (
            "/usr/lib/x86_64-linux-gnu/qt5/plugins",
            "/usr/lib/x86_64-linux-gnu/qt5",
            "/usr/lib/x86_64-linux-gnu",
            "/usr/lib"
        ):
            continue

        if loaded_filename == "/usr/bin/python3.2mu":
            continue

        # Accessing SE-Linux is OK.
        if loaded_filename in ("/sys/fs/selinux", "/selinux"):
            continue

        # Allow reading time zone info of local system.
        if loaded_filename.startswith("/usr/share/zoneinfo/"):
            continue

        # The access to .pth files has no effect.
        if loaded_filename.endswith(".pth"):
            continue

        # Looking at site-package dir alone is alone.
        if loaded_filename.endswith(("site-packages", "dist-packages")):
            continue

        # Windows baseline DLLs
        if loaded_basename.upper() in (
            "SHELL32.DLL","USER32.DLL","KERNEL32.DLL",
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
            "UCRTBASE.DLL", "TOKENBINDING.DLL"):
            continue

        # Win API can be assumed.
        if loaded_basename.upper().startswith("API-MS-WIN"):
            continue

        # MSVC run time DLLs, seem to sometimes come from system. TODO:
        # clarify if that means we did it wrong.
        if loaded_basename.upper() in ("MSVCRT.DLL", "MSVCR90.DLL"):
            continue

        # These stopped being loaded by system on Windows 10.
        if loaded_basename.upper() in ("MSVCP_WIN.DLL", "WIN32U.DLL"):
            continue

        my_print("Should not access '%s'." % loaded_filename)
        illegal_access = True

    if illegal_access:
        sys.exit(1)

    removeDirectory(filename[:-3] + ".dist", ignore_errors = True)

search_mode.finish()
