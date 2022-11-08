#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Module for handling Windows resources.

Nuitka needs to do a couple of things with Windows resources, e.g. adding
and removing manifests amd copying icon image resources into the created
binary. For this purpose, we need to list, remove, add resources and extract
their data.

Previously we used the Windows SDK tools for this purpose, but for some tasks,
e.g. deleting unwanted manifest resources for include into the distribution,
we needed to do it manually. Also setting icon resources with images for
multiple resources proved to be not possible.

"""

import ctypes
import os
import struct

from nuitka import TreeXML

from .Utils import decoratorRetries

# SxS manifest files resource kind
RT_MANIFEST = 24
# Version info
RT_VERSION = 16
# Data resource kind
RT_RCDATA = 10
# Icon group resource kind
RT_GROUP_ICON = 14
# Icon resource kind
RT_ICON = 3


def getResourcesFromDLL(filename, resource_kinds, with_data=False):
    """Get the resources of a specific kind from a Windows DLL.

    Args:
        filename - filename where the resources are taken from
        resource_kinds - tuple of numeric values indicating types of resources
        with_data - Return value includes data or only the name, lang pairs

    Returns:
        List of resources in the DLL, see with_data which controls scope.

    """
    # Quite complex stuff, pylint: disable=too-many-locals

    import ctypes.wintypes  # Not really redefined, but extended, pylint: disable=redefined-outer-name

    if type(filename) is str and str is not bytes:
        LoadLibraryEx = ctypes.windll.kernel32.LoadLibraryExW
    else:
        LoadLibraryEx = ctypes.windll.kernel32.LoadLibraryExA

    EnumResourceLanguages = ctypes.windll.kernel32.EnumResourceLanguagesA
    FreeLibrary = ctypes.windll.kernel32.FreeLibrary

    EnumResourceNameCallback = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HMODULE,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
    )

    EnumResourceNames = ctypes.windll.kernel32.EnumResourceNamesA
    EnumResourceNames.argtypes = [
        ctypes.wintypes.HMODULE,
        ctypes.wintypes.LPVOID,
        EnumResourceNameCallback,
        ctypes.wintypes.LPARAM,
    ]

    DONT_RESOLVE_DLL_REFERENCES = 0x1
    LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE = 0x40
    LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x20

    hmodule = LoadLibraryEx(
        filename,
        0,
        DONT_RESOLVE_DLL_REFERENCES
        | LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE
        | LOAD_LIBRARY_AS_IMAGE_RESOURCE,
    )

    if hmodule == 0:
        raise ctypes.WinError()

    EnumResourceLanguagesCallback = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HMODULE,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
        ctypes.wintypes.WORD,
        ctypes.wintypes.LONG,
    )

    result = []

    def callback(hModule, lpType, lpName, _lParam):
        langs = []

        def callback2(hModule2, lpType2, lpName2, wLang, _lParam):
            assert hModule2 == hModule
            assert lpType2 == lpType
            assert lpName2 == lpName

            langs.append(wLang)

            return True

        EnumResourceLanguages(
            hModule, lpType, lpName, EnumResourceLanguagesCallback(callback2), 0
        )
        # Always pick first one, we should get away with that. On very old Python,
        # we do not find any, and pick 0.
        try:
            lang_id = langs[0]
        except IndexError:
            lang_id = 0

        if with_data:
            hResource = ctypes.windll.kernel32.FindResourceA(hModule, lpName, lpType)
            size = ctypes.windll.kernel32.SizeofResource(hModule, hResource)
            hData = ctypes.windll.kernel32.LoadResource(hModule, hResource)

            try:
                ptr = ctypes.windll.kernel32.LockResource(hData)
                result.append((lpType, lpName, lang_id, ctypes.string_at(ptr, size)))
            finally:
                ctypes.windll.kernel32.FreeResource(hData)
        else:
            result.append((lpName, lang_id))

        return True

    for resource_kind in resource_kinds:
        EnumResourceNames(hmodule, resource_kind, EnumResourceNameCallback(callback), 0)

    FreeLibrary(hmodule)
    return result


def _openFileWindowsResources(filename):
    fullpath = os.path.abspath(filename)
    if type(filename) is str and str is bytes:
        BeginUpdateResource = ctypes.windll.kernel32.BeginUpdateResourceA
        BeginUpdateResource.argtypes = [ctypes.wintypes.LPCSTR, ctypes.wintypes.BOOL]
    else:
        BeginUpdateResource = ctypes.windll.kernel32.BeginUpdateResourceW
        BeginUpdateResource.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.BOOL]

    BeginUpdateResource.restype = ctypes.wintypes.HANDLE

    update_handle = BeginUpdateResource(fullpath, False)

    if not update_handle:
        raise ctypes.WinError()

    return update_handle


def _closeFileWindowsResources(update_handle):
    EndUpdateResource = ctypes.windll.kernel32.EndUpdateResourceA
    EndUpdateResource.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.BOOL]
    EndUpdateResource.restype = ctypes.wintypes.BOOL

    ret = EndUpdateResource(update_handle, False)

    if not ret:
        raise ctypes.WinError()


def _updateWindowsResource(update_handle, resource_kind, res_name, lang_id, data):
    if data is None:
        size = 0
    else:
        size = len(data)

        assert type(data) is bytes

    UpdateResourceA = ctypes.windll.kernel32.UpdateResourceA

    UpdateResourceA.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.LPVOID,
        ctypes.wintypes.LPVOID,
        ctypes.wintypes.WORD,
        ctypes.wintypes.LPVOID,
        ctypes.wintypes.DWORD,
    ]

    ret = UpdateResourceA(update_handle, resource_kind, res_name, lang_id, data, size)

    if not ret:
        raise ctypes.WinError()


def deleteWindowsResources(filename, resource_kind, res_names):
    update_handle = _openFileWindowsResources(filename)

    for res_name, lang_id in res_names:
        _updateWindowsResource(update_handle, resource_kind, res_name, lang_id, None)

    _closeFileWindowsResources(update_handle)


def copyResourcesFromFileToFile(source_filename, target_filename, resource_kinds):
    """Copy resources from one file to another.

    Args:
        source_filename - filename where the resources are taken from
        target_filename - filename where the resources are added to
        resource_kinds - tuple of numeric values indicating types of resources

    Returns:
        int - amount of resources copied, in case you want report

    Notes:
        Only windows resources are handled. Will not touch target filename
        unless there are resources in the source.

    """

    res_data = getResourcesFromDLL(
        filename=source_filename, resource_kinds=resource_kinds, with_data=True
    )

    if res_data:
        update_handle = _openFileWindowsResources(target_filename)

        for resource_kind, res_name, lang_id, data in res_data:
            assert resource_kind in resource_kinds

            # Not seeing the point at this time really, but seems to cause troubles otherwise.
            lang_id = 0

            _updateWindowsResource(
                update_handle, resource_kind, res_name, lang_id, data
            )

        _closeFileWindowsResources(update_handle)

    return len(res_data)


def addResourceToFile(target_filename, data, resource_kind, lang_id, res_name, logger):
    assert os.path.exists(target_filename), target_filename

    @decoratorRetries(
        logger=logger,
        purpose="add resources to file %r" % target_filename,
        consequence="the result is unusable",
    )
    def _addResourceToFile():
        update_handle = _openFileWindowsResources(target_filename)
        _updateWindowsResource(update_handle, resource_kind, res_name, lang_id, data)
        _closeFileWindowsResources(update_handle)

    _addResourceToFile()


class WindowsExecutableManifest(object):
    def __init__(self, template):
        self.tree = TreeXML.fromString(template)

    def addResourceToFile(self, filename, logger):
        manifest_data = TreeXML.toBytes(self.tree, indent=False)

        addResourceToFile(
            target_filename=filename,
            data=manifest_data,
            resource_kind=RT_MANIFEST,
            res_name=1,
            lang_id=0,
            logger=logger,
        )

    def addUacAdmin(self):
        """Add indication, the binary should request admin rights."""
        self._getRequestedExecutionLevelNode().attrib["level"] = "requireAdministrator"

    def addUacUiAccess(self):
        """Add indication, the binary be allowed for remote desktop."""
        self._getRequestedExecutionLevelNode().attrib["uiAccess"] = "true"

    def _getTrustInfoNode(self):
        # To lazy to figure out proper usage of namespaces, this is good enough for now.
        for child in self.tree:
            if child.tag == "{urn:schemas-microsoft-com:asm.v3}trustInfo":
                return child

    def _getTrustInfoSecurityNode(self):
        return self._getTrustInfoNode()[0]

    def _getRequestedPrivilegesNode(self):
        # To lazy to figure out proper usage of namespaces, this is good enough for now.
        for child in self._getTrustInfoSecurityNode():
            if child.tag == "{urn:schemas-microsoft-com:asm.v3}requestedPrivileges":
                return child

    def _getRequestedExecutionLevelNode(self):
        # To lazy to figure out proper usage of namespaces, this is good enough for now.
        for child in self._getRequestedPrivilegesNode():
            if child.tag == "{urn:schemas-microsoft-com:asm.v3}requestedExecutionLevel":
                return child


def getWindowsExecutableManifest(filename):
    manifests_data = getResourcesFromDLL(
        filename=filename, resource_kinds=(RT_MANIFEST,), with_data=True
    )

    if manifests_data:
        return WindowsExecutableManifest(manifests_data[0][-1])
    else:
        return None


def _getDefaultWindowsExecutableTrustInfo():
    return """\
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
"""


def getDefaultWindowsExecutableManifest():
    # Note: Supported OS are lied about by CPython.
    template = (
        """\
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="Mini" version="1.0.0.0"/>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    </application>
  </compatibility>
  %s
</assembly>
"""
        % _getDefaultWindowsExecutableTrustInfo()
    )

    return WindowsExecutableManifest(template)


class VsFixedFileInfoStructure(ctypes.Structure):
    _fields_ = [
        ("dwSignature", ctypes.c_uint32),  # 0xFEEF04BD
        ("dwStructVersion", ctypes.c_uint32),
        ("dwFileVersionMS", ctypes.c_uint32),
        ("dwFileVersionLS", ctypes.c_uint32),
        ("dwProductVersionMS", ctypes.c_uint32),
        ("dwProductVersionLS", ctypes.c_uint32),
        ("dwFileFlagsMask", ctypes.c_uint32),
        ("dwFileFlags", ctypes.c_uint32),
        ("dwFileOS", ctypes.c_uint32),
        ("dwFileType", ctypes.c_uint32),
        ("dwFileSubtype", ctypes.c_uint32),
        ("dwFileDateMS", ctypes.c_uint32),
        ("dwFileDateLS", ctypes.c_uint32),
    ]


def convertStructureToBytes(c_value):
    """Convert ctypes structure to bytes for output."""

    result = (ctypes.c_char * ctypes.sizeof(c_value)).from_buffer_copy(c_value)
    r = b"".join(result)
    assert len(result) == ctypes.sizeof(c_value)
    return r


def _makeVersionInfoStructure(product_version, file_version, file_date, is_exe):
    return VsFixedFileInfoStructure(
        dwSignature=0xFEEF04BD,
        dwFileVersionMS=file_version[0] << 16 | (file_version[1] & 0xFFFF),
        dwFileVersionLS=file_version[2] << 16 | (file_version[3] & 0xFFFF),
        dwProductVersionMS=product_version[0] << 16 | (product_version[1] & 0xFFFF),
        dwProductVersionLS=product_version[2] << 16 | (product_version[3] & 0xFFFF),
        dwFileFlagsMask=0x3F,
        dwFileFlags=0,  # TODO: Could be interesting VS_FF_DEBUG and VS_FF_PRERELEASE.
        dwFileOS=4,  # NT or higher, hasn't been changed in a long time.
        dwFileType=1 if is_exe else 2,  #
        dwFileSubtype=0,  # Not applicable for DLL or EXE, only drivers use this.
        dwFileDateMS=file_date[0],
        dwFileDateLS=file_date[1],
    )


def _getVersionString(value):
    """Encodes string for version information string tables.

    Arguments:
        value - string to encode

    Returns:
        bytes - value encoded as utf-16le
    """
    return value.encode("utf-16le")


class VersionResourceHeader(ctypes.Structure):
    _fields_ = [
        ("full_length", ctypes.c_short),
        ("item_size", ctypes.c_short),
        ("type", ctypes.c_short),
    ]


def _makeVersionStringEntry(key, value):
    key_data = _getVersionString(key)
    value_data = _getVersionString(value)

    value_size = len(value_data) + 2
    key_size = 6 + len(key_data) + 2

    pad = b"\0\0" if key_size % 4 else b""
    full_size = key_size + len(pad) + value_size

    header_data = convertStructureToBytes(
        VersionResourceHeader(
            full_length=full_size,
            item_size=value_size,
            type=1,
        )
    )

    return header_data + key_data + b"\0\0" + pad + value_data + b"\0\0"


def _makeVersionStringTable(values):
    block_name = _getVersionString("000004b0")
    size = 6 + len(block_name) + 2
    pad = b"\0\0" if size % 4 else b""

    parts = []
    for key, value in values.items():
        chunk = _makeVersionStringEntry(key, value)

        if len(chunk) % 4:
            chunk += b"\0\0"

        parts.append(chunk)

    block_data = b"".join(parts)
    size += len(block_data)

    header_data = convertStructureToBytes(
        VersionResourceHeader(
            full_length=size,
            item_size=0,
            type=1,
        )
    )

    return header_data + block_name + b"\0\0" + pad + block_data


def _makeVersionStringBlock(values):
    block_name = _getVersionString("StringFileInfo")
    size = 6 + len(block_name) + 2
    pad = b"\0\0" if size % 4 else b""

    block_data = _makeVersionStringTable(values)

    size = size + len(pad) + len(block_data)

    header_data = convertStructureToBytes(
        VersionResourceHeader(
            full_length=size,
            item_size=0,
            type=1,
        )
    )

    return header_data + block_name + b"\0\0" + pad + block_data


def _makeVarFileInfoStruct():
    block_name = _getVersionString("Translation")
    size = 6 + len(block_name) + 2
    pad = b"\0\0" if size % 4 else b""

    values = [0, 1200]  # Language and code page
    block_data = struct.pack("hh", *values)

    block_size = len(block_data)
    size += len(pad) + block_size

    header_data = convertStructureToBytes(
        VersionResourceHeader(
            full_length=size,
            item_size=block_size,
            type=0,
        )
    )

    return header_data + block_name + b"\0\0" + pad + block_data


def _makeVarFileInfoBlock():
    block_name = _getVersionString("VarFileInfo")
    size = 6 + len(block_name) + 2
    pad = b"\0\0" if size % 4 else b""
    block_data = _makeVarFileInfoStruct()
    size += len(pad) + len(block_data)

    header_data = convertStructureToBytes(
        VersionResourceHeader(
            full_length=size,
            item_size=0,
            type=1,
        )
    )

    return header_data + block_name + b"\0\0" + pad + block_data


def makeVersionInfoResource(
    string_values, product_version, file_version, file_date, is_exe
):

    # Every item has name and gets padded.
    block_name = _getVersionString("VS_VERSION_INFO")
    size = 6 + len(block_name) + 2
    pad1 = b"\0\0" if size % 4 else b""

    # First create the static C structure data
    version_info = _makeVersionInfoStructure(
        product_version=product_version,
        file_version=file_version,
        file_date=file_date,
        is_exe=is_exe,
    )

    version_data = convertStructureToBytes(version_info)
    version_size = len(version_data)

    size += len(pad1) + version_size
    pad2 = b"\0\0" if size % 4 else b""

    block_data = _makeVersionStringBlock(string_values) + _makeVarFileInfoBlock()

    size += len(pad2) + len(block_data)

    header_data = convertStructureToBytes(
        VersionResourceHeader(
            full_length=size,
            item_size=version_size,
            type=0,
        )
    )

    return header_data + block_name + b"\0\0" + pad1 + version_data + pad2 + block_data


def addVersionInfoResource(
    string_values,
    product_version,
    file_version,
    file_date,
    is_exe,
    result_filename,
    logger,
):
    if product_version is None:
        product_version = file_version
    if file_version is None:
        file_version = product_version

    assert product_version
    assert file_version

    if "ProductVersion" not in string_values:
        string_values["ProductVersion"] = ".".join(str(d) for d in product_version)

    if "FileVersion" not in string_values:
        string_values["FileVersion"] = ".".join(str(d) for d in file_version)

    if "OriginalFilename" not in string_values:
        string_values["OriginalFilename"] = os.path.basename(result_filename)

    if "InternalName" not in string_values:
        string_values["InternalName"] = string_values["OriginalFilename"].rsplit(
            ".", 1
        )[0]

    if "ProductName" not in string_values:
        string_values["ProductName"] = string_values["InternalName"]

    if "FileDescription" not in string_values:
        string_values["FileDescription"] = string_values["OriginalFilename"]

    ver_info = makeVersionInfoResource(
        string_values=string_values,
        product_version=product_version,
        file_version=file_version,
        file_date=file_date,
        is_exe=is_exe,
    )

    addResourceToFile(
        target_filename=result_filename,
        data=ver_info,
        resource_kind=RT_VERSION,
        res_name=1,
        lang_id=0,
        logger=logger,
    )
