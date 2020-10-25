#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import TreeXML

# SxS manifest files resource kind
RT_MANIFEST = 24
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
        List of resourcs in the DLL, see with_data which controls scope.

    """
    # Quite complex stuff, pylint: disable=too-many-locals

    import ctypes.wintypes

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
        # Always pick first one, we should get away with that.
        lang_id = langs[0]

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
    import ctypes

    if type(filename) is str and str is not bytes:
        BeginUpdateResource = ctypes.windll.kernel32.BeginUpdateResourceW
        BeginUpdateResource.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.BOOL]
    else:
        BeginUpdateResource = ctypes.windll.kernel32.BeginUpdateResourceA
        BeginUpdateResource.argtypes = [ctypes.wintypes.LPCSTR, ctypes.wintypes.BOOL]

    BeginUpdateResource.restype = ctypes.wintypes.HANDLE

    update_handle = BeginUpdateResource(filename, False)

    if not update_handle:
        raise ctypes.WinError()

    return update_handle


def _closeFileWindowsResources(update_handle):
    import ctypes

    EndUpdateResource = ctypes.windll.kernel32.EndUpdateResourceA
    EndUpdateResource.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.BOOL]
    EndUpdateResource.restype = ctypes.wintypes.BOOL

    ret = EndUpdateResource(update_handle, False)

    if not ret:
        raise ctypes.WinError()


def _updateWindowsResource(update_handle, resource_kind, res_name, lang_id, data):
    import ctypes

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


def addResourceToFile(target_filename, data, resource_kind, lang_id, res_name):
    update_handle = _openFileWindowsResources(target_filename)

    _updateWindowsResource(update_handle, resource_kind, res_name, lang_id, data)

    _closeFileWindowsResources(update_handle)


class WindowsExecutableManifest(object):
    def __init__(self, template):
        self.tree = TreeXML.fromString(template)

    def addResourceToFile(self, filename):
        addResourceToFile(
            target_filename=filename,
            data=TreeXML.toBytes(self.tree),
            resource_kind=RT_MANIFEST,
            res_name=1,
            lang_id=0,
        )

    def addUacAdmin(self):
        """ Add indication, the binary should request admin rights. """
        self._getRequestedExecutionLevelNode().attrib["level"] = "requireAdministrator"

    def addUacUiAccess(self):
        """ Add indication, the binary be allowed for remote desktop. """
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
    template = (
        """\
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="Mini" version="1.0.0.0"/>
  %s
</assembly>
"""
        % _getDefaultWindowsExecutableTrustInfo()
    )

    return WindowsExecutableManifest(template)
