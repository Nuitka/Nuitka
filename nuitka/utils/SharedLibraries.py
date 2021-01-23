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
""" This module deals with finding and information about shared libraries.

"""

import os
import subprocess
import sys

from nuitka.__past__ import unicode  # pylint: disable=I0021,redefined-builtin
from nuitka.Errors import NuitkaAssumptionError
from nuitka.PythonVersions import python_version
from nuitka.Tracing import postprocessing_logger

from .FileOperations import withMadeWritableFileMode
from .Importing import importFromInlineCopy
from .Utils import getArchitecture, getOS, isAlpineLinux, isWin32Windows
from .WindowsResources import (
    RT_MANIFEST,
    VsFixedFileInfoStructure,
    deleteWindowsResources,
    getResourcesFromDLL,
)


def locateDLLFromFilesystem(name, paths):
    for path in paths:
        for root, _dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)


def locateDLL(dll_name):
    # This function is a case driven by returns, pylint: disable=too-many-return-statements
    import ctypes.util

    dll_name = ctypes.util.find_library(dll_name)

    if dll_name is None:
        return None

    if isWin32Windows():
        return os.path.normpath(dll_name)

    if getOS() == "Darwin":
        return dll_name

    if os.path.sep in dll_name:
        # Use this from ctypes instead of rolling our own.
        # pylint: disable=protected-access

        so_name = ctypes.util._get_soname(dll_name)

        if so_name is not None:
            return os.path.join(os.path.dirname(dll_name), so_name)
        else:
            return dll_name

    if isAlpineLinux():
        return locateDLLFromFilesystem(
            name=dll_name, paths=["/lib", "/usr/lib", "/usr/local/lib"]
        )

    process = subprocess.Popen(
        args=["/sbin/ldconfig", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, _stderr = process.communicate()

    dll_map = {}

    for line in stdout.splitlines()[1:]:
        assert line.count(b"=>") == 1, line
        left, right = line.strip().split(b" => ")
        assert b" (" in left, line
        left = left[: left.rfind(b" (")]

        if python_version >= 0x300:
            left = left.decode(sys.getfilesystemencoding())
            right = right.decode(sys.getfilesystemencoding())

        if left not in dll_map:
            dll_map[left] = right

    return dll_map[dll_name]


def getSxsFromDLL(filename, with_data=False):
    """List the SxS manifests of a Windows DLL.

    Args:
        filename: Filename of DLL to investigate

    Returns:
        List of resource names that are manifests.

    """

    return getResourcesFromDLL(
        filename=filename, resource_kinds=(RT_MANIFEST,), with_data=with_data
    )


def removeSxsFromDLL(filename):
    """Remove the Windows DLL SxS manifest.

    Args:
        filename: Filename to remove SxS manifests from
    """
    # There may be more files that need this treatment, these are from scans
    # with the "find_sxs_modules" tool.
    if os.path.normcase(os.path.basename(filename)) not in (
        "sip.pyd",
        "win32ui.pyd",
        "winxpgui.pyd",
    ):
        return

    res_names = getSxsFromDLL(filename)

    if res_names:
        deleteWindowsResources(filename, RT_MANIFEST, res_names)


def getWindowsDLLVersion(filename):
    """Return DLL version information from a file.

    If not present, it will be (0, 0, 0, 0), otherwise it will be
    a tuple of 4 numbers.
    """
    # Get size needed for buffer (0 if no info)
    import ctypes.wintypes

    if type(filename) is unicode:
        GetFileVersionInfoSizeW = ctypes.windll.version.GetFileVersionInfoSizeW
        GetFileVersionInfoSizeW.argtypes = [
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.LPDWORD,
        ]
        GetFileVersionInfoSizeW.restype = ctypes.wintypes.HANDLE
        size = GetFileVersionInfoSizeW(filename, None)
    else:
        size = ctypes.windll.version.GetFileVersionInfoSizeA(filename, None)

    if not size:
        return (0, 0, 0, 0)

    # Create buffer
    res = ctypes.create_string_buffer(size)
    # Load file information into buffer res

    if type(filename) is unicode:
        # Python3 needs our help here.
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoW
        GetFileVersionInfo.argtypes = [
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.LPVOID,
        ]
        GetFileVersionInfo.restype = ctypes.wintypes.BOOL

    else:
        # Python2 just works.
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoA

    success = GetFileVersionInfo(filename, 0, size, res)
    # This cannot really fail anymore.
    assert success

    # Look for codepages
    VerQueryValueA = ctypes.windll.version.VerQueryValueA
    VerQueryValueA.argtypes = [
        ctypes.wintypes.LPCVOID,
        ctypes.wintypes.LPCSTR,
        ctypes.wintypes.LPVOID,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    VerQueryValueA.restype = ctypes.wintypes.BOOL

    file_info = ctypes.POINTER(VsFixedFileInfoStructure)()
    uLen = ctypes.c_uint32(ctypes.sizeof(file_info))

    b = VerQueryValueA(res, br"\\", ctypes.byref(file_info), ctypes.byref(uLen))
    if not b:
        return (0, 0, 0, 0)

    if not file_info.contents.dwSignature == 0xFEEF04BD:
        return (0, 0, 0, 0)

    ms = file_info.contents.dwFileVersionMS
    ls = file_info.contents.dwFileVersionLS

    return (ms >> 16) & 0xFFFF, ms & 0xFFFF, (ls >> 16) & 0xFFFF, ls & 0xFFFF


# TODO: Relocate this to nuitka.freezer maybe.
def getPEFileInformation(filename):
    """Return the PE file information of a Windows EXE or DLL

    Args:
        filename - The file to be investigated.

    Notes:
        Use of this is obviously only for Windows, although the module
        will exist on other platforms too. We use the system version
        of pefile in preference, but have an inline copy as a fallback
        too.
    """

    pefile = importFromInlineCopy("pefile", must_exist=True)

    pe = pefile.PE(filename)

    # This is the information we use from the file.
    extracted = {}
    extracted["DLLs"] = []

    for imported_module in getattr(pe, "DIRECTORY_ENTRY_IMPORT", ()):
        extracted["DLLs"].append(imported_module.dll.decode())

    pe_type2arch = {
        pefile.OPTIONAL_HEADER_MAGIC_PE: False,
        pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS: True,
    }

    if pe.PE_TYPE not in pe_type2arch:
        # Support your architecture, e.g. ARM if necessary.
        raise NuitkaAssumptionError(
            "Unknown PE file architecture", filename, pe.PE_TYPE, pe_type2arch
        )

    extracted["AMD64"] = pe_type2arch[pe.PE_TYPE]

    python_is_64bit = getArchitecture() == "x86_64"
    if extracted["AMD64"] is not python_is_64bit:
        postprocessing_logger.warning(
            "Python %s bits with %s bits dependencies in '%s'"
            % (
                ("32" if python_is_64bit else "64"),
                ("64" if extracted["AMD64"] else "32"),
                filename,
            )
        )

    return extracted


def callInstallNameTool(filename, mapping):
    """Update the macOS shared library information for a binary or shared library.

    Args:
        filename - The file to be modified.
        mapping  - old_path, new_path pairs of values that should be changed

    Returns:
        None

    Notes:
        This is obviously macOS specific.
    """
    command = ["install_name_tool"]
    for old_path, new_path in mapping:
        command += ("-change", old_path, new_path)
    command.append(filename)

    with withMadeWritableFileMode(filename):
        result = subprocess.call(command, stdout=subprocess.PIPE)

    if result != 0:
        postprocessing_logger.sysexit(
            "Error, call to 'install_name_tool' to fix shared library path failed."
        )


def callInstallNameToolAddRPath(filename, rpath):
    """Adds the rpath path name `rpath` in the specified `filename` Mach-O
    binary or shared library. If the Mach-O binary already contains the new
    `rpath` path name, it is an error.

    Args:
        filename - Mach-O binary or shared library file name.
        rpath  - rpath path name.

    Returns:
        None

    Notes:
        This is obviously macOS specific.
    """
    command = ["install_name_tool", "-add_rpath", os.path.join(rpath, "."), filename]

    with withMadeWritableFileMode(filename):
        result = subprocess.call(command, stdout=subprocess.PIPE)

    if result != 0:
        postprocessing_logger.sysexit(
            "Error, call to 'install_name_tool' to add rpath failed."
        )


def getPyWin32Dir():
    """Find the pywin32 DLL directory

    Args:
        None

    Returns:
        path to the pywin32 DLL directory or None

    Notes:
        This is needed for standalone mode only.
    """

    for path_element in sys.path:
        if not path_element:
            continue

        candidate = os.path.join(path_element, "pywin32_system32")

        if os.path.isdir(candidate):
            return candidate
