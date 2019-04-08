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


def getResourcesFromDLL(filename, resource_kind, with_data=False):
    """ Get the resources of a specific kind from a Windows DLL.

    Returns:
        List of resource names in the DLL.

    """
    import ctypes.wintypes

    if type(filename) is str and str is not bytes:
        LoadLibraryEx = ctypes.windll.kernel32.LoadLibraryExW  # @UndefinedVariable
    else:
        LoadLibraryEx = ctypes.windll.kernel32.LoadLibraryExA  # @UndefinedVariable

    EnumResourceNames = ctypes.windll.kernel32.EnumResourceNamesA  # @UndefinedVariable
    FreeLibrary = ctypes.windll.kernel32.FreeLibrary  # @UndefinedVariable

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

    result = []

    def callback(hModule, lpType, lpName, _lParam):
        if with_data:
            hResource = ctypes.windll.kernel32.FindResourceA(  # @UndefinedVariable
                hModule, lpName, lpType
            )
            size = ctypes.windll.kernel32.SizeofResource(  # @UndefinedVariable
                hModule, hResource
            )
            hData = ctypes.windll.kernel32.LoadResource(  # @UndefinedVariable
                hModule, hResource
            )
            try:
                ptr = ctypes.windll.kernel32.LockResource(hData)  # @UndefinedVariable
                result.append((lpType, lpName, ctypes.string_at(ptr, size)))
            finally:
                ctypes.windll.kernel32.FreeResource(hData)  # @UndefinedVariable
        else:
            result.append(lpName)

        return True

    EnumResourceNames(hmodule, resource_kind, EnumResourceNameCallback(callback), None)

    FreeLibrary(hmodule)
    return result


def _openFileWindowsResources(filename):
    import ctypes

    update_handle = ctypes.windll.kernel32.BeginUpdateResourceA(  # @UndefinedVariable
        filename, False
    )

    if not update_handle:
        raise ctypes.WinError()

    return update_handle


def _closeFileWindowsResources(update_handle):
    import ctypes

    ret = ctypes.windll.kernel32.EndUpdateResourceA(  # @UndefinedVariable
        update_handle, False
    )

    if not ret:
        raise ctypes.WinError()


def deleteWindowsResources(filename, resource_kind, res_names):
    import ctypes

    update_handle = _openFileWindowsResources(filename)

    for res_name in res_names:
        ret = ctypes.windll.kernel32.UpdateResource(  # @UndefinedVariable
            update_handle, resource_kind, res_name, 0, None, 0
        )

        if not ret:
            raise ctypes.WinError()

    _closeFileWindowsResources(update_handle)


def copyResourcesFromFileToFile(source_filename, target_filename, resource_kind):
    import ctypes

    res_data = getResourcesFromDLL(source_filename, resource_kind, True)

    if res_data:
        update_handle = _openFileWindowsResources(target_filename)

        for kind, res_name, data in res_data:
            assert kind == resource_kind

            ret = ctypes.windll.kernel32.UpdateResourceA(  # @UndefinedVariable
                update_handle, resource_kind, res_name, 0, data, len(data)
            )

            if not ret:
                raise ctypes.WinError()

        _closeFileWindowsResources(update_handle)
