#!/usr/bin/env python
#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Runner for standalone program tests of Nuitka.

These tests aim at showing that one specific module works in standalone
mode, trying to find issues with that packaging.

"""


import os
import sys

# Find nuitka package relative to us. The replacement is for POSIX python
# and Windows paths on command line.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__.replace("\\", os.sep))), "..", ".."
        )
    ),
)

# isort:start

import subprocess

from nuitka.tools.testing.Common import (
    compareWithCPython,
    createSearchMode,
    decideFilenameVersionSkip,
    getPythonVendor,
    getRuntimeTraceOfLoadedFiles,
    hasModule,
    my_print,
    reportSkip,
    setup,
)
from nuitka.tree.SourceReading import readSourceCodeFromFilename
from nuitka.utils.FileOperations import areSamePaths, removeDirectory
from nuitka.utils.Utils import getOS


# checks requirements needed to run each test module, according to the specified special comment
# special comments are in the following formats:
#     "# nuitka-skip-unless-expression: expression to be evaluated"
#       OR
#     "# nuitka-skip-unless-imports: module1,module2,..."
def checkRequirements(filename):
    for line in readSourceCodeFromFilename(None, filename).splitlines():
        if line.startswith("# nuitka-skip-unless-"):
            if line[21:33] == "expression: ":
                expression = line[33:]
                with open(os.devnull, "w") as devnull:
                    result = subprocess.call(
                        (
                            os.environ["PYTHON"],
                            "-c",
                            "import sys, os; sys.exit(not bool(%s))" % expression,
                        ),
                        stdout=devnull,
                        stderr=subprocess.STDOUT,
                    )
                if result != 0:
                    return (False, "Expression '%s' evaluated to false" % expression)

            elif line[21:30] == "imports: ":
                imports_needed = line[30:].rstrip().split(",")
                for i in imports_needed:
                    if not hasModule(i):
                        return (
                            False,
                            i
                            + " not installed for this Python version, but test needs it",
                        )
    # default return value
    return (True, "")


def displayError(dirname, filename):
    assert dirname is None

    my_print("Listing of dist folder:")

    if os.name == "nt":
        command = "dir /b /s /a:-D %s"
    else:
        command = "ls -Rla %s"

    os.system(command % filename)


def main():
    # Complex stuff, even more should become common code though.
    # pylint: disable=too-many-branches,too-many-statements

    python_version = setup(needs_io_encoding=True)

    search_mode = createSearchMode()

    for filename in sorted(os.listdir(".")):
        if not filename.endswith(".py"):
            continue

        if not decideFilenameVersionSkip(filename):
            continue

        active = search_mode.consider(dirname=None, filename=filename)

        if not active:
            my_print("Skipping", filename)
            continue

        extra_flags = [
            "expect_success",
            "standalone",
            "remove_output",
            # For enum plugin info
            "ignore_infos",
        ]

        # skip each test if their respective requirements are not met
        requirements_met, error_message = checkRequirements(filename)
        if not requirements_met:
            reportSkip(error_message, ".", filename)
            continue

        # catch error
        if filename == "Boto3Using.py":
            reportSkip("boto3 test not fully working yet", ".", filename)
            continue

        if "Idna" in filename:
            # For the warnings of Python2.
            if python_version.startswith("2"):
                extra_flags.append("ignore_stderr")

        if filename == "CtypesUsing.py":
            extra_flags.append("plugin_disable:pylint-warnings")

        if filename == "GtkUsing.py":
            # Don't test on platforms not supported by current Debian testing, and
            # which should be considered irrelevant by now.
            if python_version.startswith("2.6"):
                reportSkip("irrelevant Python version", ".", filename)
                continue

            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename.startswith("Win"):
            if os.name != "nt":
                reportSkip("Windows only test", ".", filename)
                continue

        if filename == "TkInterUsing.py":
            if getOS() == "Darwin":
                reportSkip("Not working macOS yet", ".", filename)
                continue

            # For the plug-in information.
            extra_flags.append("plugin_enable:tk-inter")

        if filename == "FlaskUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename == "NumpyUsing.py":
            # TODO: Disabled for now.
            reportSkip("numpy.test not fully working yet", ".", filename)
            continue

            # extra_flags.append("plugin_enable:data-files")
        if filename == "PmwUsing.py":
            extra_flags.append("plugin_enable:pmw-freezer")

        if filename == "OpenGLUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename == "PasslibUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename == "PySideUsing.py":
            # TODO: Disabled due to lack of upstream support.
            reportSkip("PySide not supported yet", ".", filename)
            continue

        if filename == "Win32ComUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename.startswith(("PySide", "PyQt")):
            if python_version.startswith("2.6"):
                reportSkip("irrelevant Python version", ".", filename)
                continue

            # For the plug-in information.
            if getPythonVendor() != "Anaconda":
                extra_flags.append("plugin_enable:qt-plugins")
            else:
                # For the plug-in not used information.
                extra_flags.append("ignore_warnings")

        my_print("Consider output of recursively compiled program:", filename)

        # First compare so we know the program behaves identical.
        compareWithCPython(
            dirname=None,
            filename=filename,
            extra_flags=extra_flags,
            search_mode=search_mode,
            needs_2to3=False,
            on_error=displayError,
        )

        # Second check if glibc libraries haven't been accidentally
        # shipped with the standalone executable
        found_glibc_libs = []
        for dist_filename in os.listdir(os.path.join(filename[:-3] + ".dist")):
            if os.path.basename(dist_filename).startswith(
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
                    "libutil.so.",
                )
            ):
                found_glibc_libs.append(dist_filename)

        if found_glibc_libs:
            my_print(
                "Should not ship glibc libraries with the standalone executable (found %s)"
                % found_glibc_libs
            )
            sys.exit(1)

        binary_filename = os.path.join(
            filename[:-3] + ".dist", filename[:-3] + (".exe" if os.name == "nt" else "")
        )

        # Then use "strace" on the result.
        loaded_filenames = getRuntimeTraceOfLoadedFiles(binary_filename)

        current_dir = os.path.normpath(os.getcwd())
        current_dir = os.path.normcase(current_dir)

        illegal_access = False

        for loaded_filename in loaded_filenames:
            loaded_filename = os.path.normpath(loaded_filename)
            loaded_filename = os.path.normcase(loaded_filename)
            loaded_basename = os.path.basename(loaded_filename)

            if os.name == "nt":
                if areSamePaths(
                    os.path.dirname(loaded_filename),
                    os.path.normpath(
                        os.path.join(os.environ["SYSTEMROOT"], "System32")
                    ),
                ):
                    continue
                if areSamePaths(
                    os.path.dirname(loaded_filename),
                    os.path.normpath(
                        os.path.join(os.environ["SYSTEMROOT"], "SysWOW64")
                    ),
                ):
                    continue

                if r"windows\winsxs" in loaded_filename:
                    continue

                # Github actions have these in PATH overriding SYSTEMROOT
                if r"windows performance toolkit" in loaded_filename:
                    continue
                if r"powershell" in loaded_filename:
                    continue

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

            if loaded_filename in (
                "/usr",
                "/usr/local",
                "/usr/local/lib",
                "/usr/share",
                "/usr/local/share",
                "/usr/lib64",
            ):
                continue

            # TCL/tk for tkinter for non-Windows is OK.
            if loaded_filename.startswith(
                (
                    "/usr/lib/tcltk/",
                    "/usr/share/tcltk/",
                    "/usr/lib/tcl/",
                    "/usr/lib64/tcl/",
                )
            ):
                continue
            if loaded_filename in (
                "/usr/lib/tcltk",
                "/usr/share/tcltk",
                "/usr/lib/tcl",
                "/usr/lib64/tcl",
            ):
                continue

            if loaded_filename in (
                "/lib",
                "/lib64",
                "/lib/sse2",
                "/lib/tls",
                "/lib64/tls",
                "/usr/lib/sse2",
                "/usr/lib/tls",
                "/usr/lib64/tls",
            ):
                continue

            if loaded_filename in ("/usr/share/tcl8.6", "/usr/share/tcl8.5"):
                continue
            if loaded_filename in (
                "/usr/share/tcl8.6/init.tcl",
                "/usr/share/tcl8.5/init.tcl",
            ):
                continue
            if loaded_filename in (
                "/usr/share/tcl8.6/encoding",
                "/usr/share/tcl8.5/encoding",
            ):
                continue

            # System SSL config on Linux. TODO: Should this not be included and
            # read from dist folder.
            if loaded_basename == "openssl.cnf":
                continue

            # Taking these from system is harmless and desirable
            if loaded_basename.startswith(("libz.so", "libgcc_s.so")):
                continue

            # System C libraries are to be expected.
            if loaded_basename.startswith(
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
                    "libutil.so.",
                )
            ):
                continue

            # Loaded by C library potentially for DNS lookups.
            if loaded_basename.startswith(
                (
                    "libnss_",
                    "libnsl",
                    # Some systems load a lot more, this is CentOS 7 on OBS
                    "libattr.so.",
                    "libbz2.so.",
                    "libcap.so.",
                    "libdw.so.",
                    "libelf.so.",
                    "liblzma.so.",
                    # Some systems load a lot more, this is Fedora 26 on OBS
                    "libselinux.so.",
                    "libpcre.so.",
                    # And this is Fedora 29 on OBS
                    "libblkid.so.",
                    "libmount.so.",
                    "libpcre2-8.so.",
                    # CentOS 8 on OBS
                    "libuuid.so.",
                )
            ):
                continue

            # Loaded by dtruss on macOS X.
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
            if (
                loaded_filename.startswith("/home/")
                or loaded_filename.startswith("/data/")
                or loaded_filename.startswith("/root/")
                or loaded_filename in ("/home", "/data", "/root")
            ):
                continue

            # For Debian builders, /build is OK too.
            if loaded_filename.startswith("/build/") or loaded_filename == "/build":
                continue

            # TODO: Unclear, loading gconv from filesystem of installed system
            # may be OK or not. I think it should be.
            if loaded_basename == "gconv-modules.cache":
                continue
            if "/gconv/" in loaded_filename:
                continue
            if loaded_basename.startswith("libicu"):
                continue
            if loaded_filename.startswith("/usr/share/icu/"):
                continue

            # Loading from caches is OK.
            if loaded_filename.startswith("/var/cache/"):
                continue

            # PySide accesses its directory.
            if (
                loaded_filename
                == "/usr/lib/python" + python_version[:3] + "/dist-packages/PySide"
            ):
                continue

            # GTK accesses package directories only.
            if (
                loaded_filename
                == "/usr/lib/python" + python_version[:3] + "/dist-packages/gtk-2.0/gtk"
            ):
                continue
            if (
                loaded_filename
                == "/usr/lib/python" + python_version[:3] + "/dist-packages/glib"
            ):
                continue
            if (
                loaded_filename
                == "/usr/lib/python" + python_version[:3] + "/dist-packages/gtk-2.0/gio"
            ):
                continue
            if (
                loaded_filename
                == "/usr/lib/python" + python_version[:3] + "/dist-packages/gobject"
            ):
                continue

            # PyQt5 seems to do this, but won't use contents then.
            if loaded_filename in (
                "/usr/lib/qt5/plugins",
                "/usr/lib/qt5",
                "/usr/lib64/qt5/plugins",
                "/usr/lib64/qt5",
                "/usr/lib/x86_64-linux-gnu/qt5/plugins",
                "/usr/lib/x86_64-linux-gnu/qt5",
                "/usr/lib/x86_64-linux-gnu",
                "/usr/lib",
            ):
                continue

            # Can look at the interpreter of the system.
            if loaded_basename == "python3":
                continue

            # Current Python executable can actually be a symlink and
            # the real executable which it points to will be on the
            # loaded_filenames list. This is all fine, let's ignore it.
            # Also, because the loaded_filename can be yet another symlink
            # (this is weird, but it's true), let's better resolve its real
            # path too.
            if os.path.realpath(loaded_filename) == os.path.realpath(sys.executable):
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

            # QtNetwork insist on doing this it seems.
            if loaded_basename.startswith(("libcrypto.so", "libssl.so")):
                continue

            # macOS uses these:
            if loaded_basename in (
                "libcrypto.1.0.0.dylib",
                "libssl.1.0.0.dylib",
                "libcrypto.1.1.dylib",
            ):
                continue

            # MSVC run time DLLs, seem to sometimes come from system.
            if loaded_basename.upper() in ("MSVCRT.DLL", "MSVCR90.DLL"):
                continue

            my_print("Should not access '%s'." % loaded_filename)
            illegal_access = True

        if illegal_access:
            if os.name != "nt":
                my_print("Listing of dist folder:")
                os.system("ls -Rla %s" % filename[:-3] + ".dist")

                my_print("strace:")
                os.system("strace -s4096 -e file %s" % binary_filename)

            search_mode.onErrorDetected(1)

        removeDirectory(filename[:-3] + ".dist", ignore_errors=True)

        if search_mode.abortIfExecuted():
            break

    search_mode.finish()


if __name__ == "__main__":
    main()
