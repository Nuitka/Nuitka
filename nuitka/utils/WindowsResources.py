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

# SxS manifest files resource kind
RT_MANIFEST = 24
# Data resource kind
RT_RCDATA = 10
# Icon group resource kind
RT_GROUP_ICON = 14
# Icon resource kind
RT_ICON = 3


def getResourcesFromDLL(filename, resource_kind, with_data=False):
    """ Get the resources of a specific kind from a Windows DLL.

    Returns:
        List of resource names in the DLL.

    """
    # Quite complex stuff, pylint: disable=too-many-locals

    import ctypes.wintypes

    if type(filename) is str and str is not bytes:
        LoadLibraryEx = ctypes.windll.kernel32.LoadLibraryExW
    else:
        LoadLibraryEx = ctypes.windll.kernel32.LoadLibraryExA

    EnumResourceNames = ctypes.windll.kernel32.EnumResourceNamesA
    EnumResourceLanguages = ctypes.windll.kernel32.EnumResourceLanguagesA
    FreeLibrary = ctypes.windll.kernel32.FreeLibrary

    EnumResourceNameCallback = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HMODULE,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
    )

    DONT_RESOLVE_DLL_REFERENCES = 0x1
    LOAD_LIBRARY_AS_DATAFILE = 0x2
    LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x20

    hmodule = LoadLibraryEx(
        filename,
        0,
        DONT_RESOLVE_DLL_REFERENCES
        | LOAD_LIBRARY_AS_DATAFILE
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

    EnumResourceNames(hmodule, resource_kind, EnumResourceNameCallback(callback), None)

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

    ctypes.windll.kernel32.EndUpdateResourceA.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.BOOL,
    ]
    ret = ctypes.windll.kernel32.EndUpdateResourceA(update_handle, False)

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


def copyResourcesFromFileToFile(source_filename, target_filename, resource_kind):
    """ Copy resources from one file to another.

    Args:
        source_filename - filename where the resources are taken from
        target_filename - filename where the resources are added to
        resource_kind - numeric value indicating which type of resource

    Returns:
        int - amount of resources copied, in case you want report

    Notes:
        Only windows resources are handled. Will not touch target filename
        unless there are resources in the source.

    """

    res_data = getResourcesFromDLL(
        filename=source_filename, resource_kind=resource_kind, with_data=True
    )

    if res_data:
        update_handle = _openFileWindowsResources(target_filename)

        for kind, res_name, lang_id, data in res_data:
            assert kind == resource_kind

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
