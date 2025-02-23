#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This module deals with finding and information about shared libraries.

"""

import os
import re
import sys

from nuitka.__past__ import WindowsError  # pylint: disable=I0021,redefined-builtin
from nuitka.__past__ import unicode
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import getMacOSTargetArch, isShowInclusion, isUnstripped
from nuitka.PythonVersions import python_version
from nuitka.Tracing import inclusion_logger, postprocessing_logger

from .Execution import executeToolChecked, withEnvironmentPathAdded
from .FileOperations import (
    addFileExecutablePermission,
    changeFilenameExtension,
    copyFile,
    getFileList,
    makeContainingPath,
    withMadeWritableFileMode,
)
from .Importing import importFromInlineCopy
from .Utils import (
    isAlpineLinux,
    isLinux,
    isMacOS,
    isWin32Windows,
    raiseWindowsError,
)
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


_ldconfig_usage = "The 'ldconfig' is used to analyze dependencies on ELF using systems and required to be found."


def locateDLL(dll_name):
    # This function is a case driven by returns, pylint: disable=too-many-return-statements
    import ctypes.util

    dll_name = ctypes.util.find_library(dll_name)

    if dll_name is None:
        return None

    # This happens on macOS.
    if isMacOS() and not os.path.exists(dll_name):
        return None

    if isWin32Windows() or isMacOS():
        return os.path.abspath(dll_name)

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

    # TODO: Could and probably should cache "ldconfig -p" output to avoid forks
    output = executeToolChecked(
        logger=postprocessing_logger,
        command=("/sbin/ldconfig", "-p"),
        absence_message=_ldconfig_usage,
    )

    dll_map = {}

    for line in output.splitlines()[1:]:
        if line.startswith(b"Cache generated by:"):
            continue

        assert line.count(b"=>") == 1, line
        left, right = line.strip().split(b" => ")
        assert b" (" in left, line
        left = left[: left.rfind(b" (")]

        if python_version >= 0x300:
            # spell-checker: ignore getfilesystemencoding

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


def _removeSxsFromDLL(filename):
    """Remove the Windows DLL SxS manifest.

    Args:
        filename: Filename to remove SxS manifests from
    """
    # There may be more files that need this treatment, these are from scans
    # with the "find_sxs_modules" tool. spell-checker: ignore winxpgui
    if os.path.normcase(os.path.basename(filename)) not in (
        "sip.pyd",
        "win32ui.pyd",
        "winxpgui.pyd",
    ):
        return

    res_names = getSxsFromDLL(filename)

    if res_names:
        deleteWindowsResources(filename, RT_MANIFEST, res_names)


def _getDLLVersionWindows(filename):
    """Return DLL version information from a file.

    If not present, it will be (0, 0, 0, 0), otherwise it will be
    a tuple of 4 numbers.
    """
    # Get size needed for buffer (0 if no info)
    import ctypes.wintypes

    if type(filename) is unicode:
        GetFileVersionInfoSizeW = ctypes.windll.version.GetFileVersionInfoSizeW
        GetFileVersionInfoSizeW.argtypes = (
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.LPDWORD,
        )
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
        GetFileVersionInfo.argtypes = (
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.LPVOID,
        )
        GetFileVersionInfo.restype = ctypes.wintypes.BOOL

    else:
        # Python2 just works.
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoA

    success = GetFileVersionInfo(filename, 0, size, res)
    # This cannot really fail anymore.
    assert success

    # Look for code pages
    VerQueryValueA = ctypes.windll.version.VerQueryValueA
    VerQueryValueA.argtypes = (
        ctypes.wintypes.LPCVOID,
        ctypes.wintypes.LPCSTR,
        ctypes.wintypes.LPVOID,
        ctypes.POINTER(ctypes.c_uint32),
    )
    VerQueryValueA.restype = ctypes.wintypes.BOOL

    file_info = ctypes.POINTER(VsFixedFileInfoStructure)()
    uLen = ctypes.c_uint32(ctypes.sizeof(file_info))

    b = VerQueryValueA(res, b"\\\\", ctypes.byref(file_info), ctypes.byref(uLen))
    if not b:
        return (0, 0, 0, 0)

    if file_info.contents.dwSignature != 0xFEEF04BD:
        return (0, 0, 0, 0)

    ms = file_info.contents.dwFileVersionMS
    ls = file_info.contents.dwFileVersionLS

    return (ms >> 16) & 0xFFFF, ms & 0xFFFF, (ls >> 16) & 0xFFFF, ls & 0xFFFF


# spell-checker: ignore readelf
_readelf_usage = "The 'readelf' is used to analyse dependencies on ELF using systems and required to be found."


def _getSharedLibraryRPATHsElf(filename):
    rpaths = []
    output = executeToolChecked(
        logger=postprocessing_logger,
        command=("readelf", "-d", filename),
        absence_message=_readelf_usage,
    )

    for line in output.split(b"\n"):
        # spell-checker: ignore RUNPATH
        if b"RPATH" in line or b"RUNPATH" in line:
            result = line[line.find(b"[") + 1 : line.rfind(b"]")]

            if str is not bytes:
                result = result.decode("utf8")

            rpaths.append(result)
        elif b"NEEDED" in line:
            # If the Python binary has a library dependency like
            # $ORIGIN/../lib/libpython.so, then treat it like it has an rpath of
            # $ORIGIN/../lib. This is needed for python-build-standalone (used
            # by UV-Python).
            result = line[line.find(b"[") + 1 : line.rfind(b"]")]

            if str is not bytes:
                result = result.decode("utf8")

            path_part = os.path.dirname(result)
            if path_part:
                rpaths.append(path_part)

    return rpaths


_otool_output_cache = {}


def _getMacOSArchOption():
    macos_target_arch = getMacOSTargetArch()

    if macos_target_arch != "universal":
        return ("-arch", macos_target_arch)
    else:
        return ()


# TODO: Use this for more output filters.
def _filterOutputByLine(output, filter_func):
    non_errors = []

    for line in output.splitlines():
        if line and not filter_func(line):
            non_errors.append(line)

    output = b"\n".join(non_errors)

    return (0 if non_errors else None), output


def _filterOtoolErrorOutput(stderr):
    def isNonErrorExit(line):
        if b"missing from root that overrides" in line:
            return True

        return False

    return _filterOutputByLine(stderr, isNonErrorExit)


def _getOToolCommandOutput(otool_option, filename):
    filename = os.path.abspath(filename)

    command = ("otool",) + _getMacOSArchOption() + (otool_option, filename)

    if otool_option == "-L":
        cache_key = command, os.getenv("DYLD_LIBRARY_PATH")
    else:
        cache_key = command

    if cache_key not in _otool_output_cache:
        _otool_output_cache[cache_key] = executeToolChecked(
            logger=postprocessing_logger,
            command=command,
            stderr_filter=_filterOtoolErrorOutput,
            absence_message="The 'otool' is used to analyze dependencies on macOS and required to be found.",
        )

    return _otool_output_cache[cache_key]


def getOtoolListing(filename):
    return _getOToolCommandOutput("-l", filename)


def getOtoolDependencyOutput(filename, package_specific_dirs):
    with withEnvironmentPathAdded("DYLD_LIBRARY_PATH", *package_specific_dirs):
        return _getOToolCommandOutput("-L", filename)


def parseOtoolListingOutput(output):
    paths = OrderedSet()

    for line in output.split(b"\n")[1:]:
        if str is not bytes:
            line = line.decode("utf8")

        if not line:
            continue

        filename = line.split(" (", 1)[0].strip()

        paths.add(filename)

    return paths


def _getDLLVersionMacOS(filename):
    output = _getOToolCommandOutput("-D", filename).splitlines()

    if len(output) < 2:
        return None

    dll_id = output[1].strip()

    if str is not bytes:
        dll_id = dll_id.decode("utf8")

    output = _getOToolCommandOutput("-L", filename).splitlines()
    for line in output:
        if str is not bytes:
            line = line.decode("utf8")

        if dll_id in line and "version" in line:
            version_string = re.search(r"current version (.*)\)", line).group(1)
            return tuple(int(x) for x in version_string.split("."))

    return None


def _getSharedLibraryRPATHsDarwin(filename):
    rpaths = []
    output = getOtoolListing(filename)

    cmd = b""
    last_was_load_command = False

    for line in output.split(b"\n"):
        line = line.strip()

        if cmd == b"LC_RPATH":
            if line.startswith(b"path "):
                result = line[5 : line.rfind(b"(") - 1]

                if str is not bytes:
                    result = result.decode("utf8")

                rpaths.append(result)

        if last_was_load_command and line.startswith(b"cmd "):
            cmd = line.split()[1]

        last_was_load_command = line.startswith(b"Load command")

    return rpaths


def getSharedLibraryRPATHs(filename):
    if isMacOS():
        return _getSharedLibraryRPATHsDarwin(filename)
    else:
        return _getSharedLibraryRPATHsElf(filename)


def _filterPatchelfErrorOutput(stderr):
    non_errors = []

    def isNonErrorExit(line):
        if b"cannot find section '.dynamic'" in line:
            non_errors.append(line)

            return True

        return False

    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if line
        if b"warning: working around" not in line
        if not isNonErrorExit(line)
    )

    return (0 if non_errors else None), stderr


_patchelf_usage = """\
Error, needs 'patchelf' on your system, to modify 'RPATH' settings that \
need to be updated."""


def checkPatchElfPresenceAndUsability(logger):
    """Checks if patchelf is present and usable."""

    output = executeToolChecked(
        logger=logger,
        command=("patchelf", "--version"),
        absence_message="""\
Error, standalone mode on Linux requires 'patchelf' to be \
installed. Use 'apt/dnf/yum install patchelf' first.""",
    )

    if output.split() == b"0.18.0":
        logger.sysexit(
            "Error, patchelf version 0.18.0 is a known buggy release and cannot be used. Please upgrade or downgrade it."
        )


def _setSharedLibraryRPATHElf(filename, rpath):
    # patchelf --set-rpath "$ORIGIN/path/to/library" <executable>
    executeToolChecked(
        logger=postprocessing_logger,
        command=("patchelf", "--set-rpath", rpath, filename),
        stderr_filter=_filterPatchelfErrorOutput,
        absence_message=_patchelf_usage,
    )


def _filterInstallNameToolErrorOutput(stderr):
    stderr = b"\n".join(
        line
        for line in stderr.splitlines()
        if line
        if b"invalidate the code signature" not in line
        if b"generating fake signature" not in line
    )

    return None, stderr


_install_name_tool_usage = "The 'install_name_tool' is used to make binaries portable on macOS and required to be found."


def _removeSharedLibraryRPATHDarwin(filename, rpaths):
    for rpath in rpaths:
        executeToolChecked(
            logger=postprocessing_logger,
            command=("install_name_tool", "-delete_rpath", rpath, filename),
            absence_message=_install_name_tool_usage,
            stderr_filter=_filterInstallNameToolErrorOutput,
        )


def _setSharedLibraryRPATHDarwin(filename, rpath):
    old_rpaths = getSharedLibraryRPATHs(filename)

    with withMadeWritableFileMode(filename):
        _removeSharedLibraryRPATHDarwin(filename=filename, rpaths=old_rpaths)

        executeToolChecked(
            logger=postprocessing_logger,
            command=("install_name_tool", "-add_rpath", rpath, filename),
            absence_message=_install_name_tool_usage,
            stderr_filter=_filterInstallNameToolErrorOutput,
        )


def setSharedLibraryRPATH(filename, rpath):
    if isShowInclusion():
        inclusion_logger.info(
            "Setting 'RPATH' value '%s' for '%s'." % (rpath, filename)
        )

    with withMadeWritableFileMode(filename):
        if isMacOS():
            _setSharedLibraryRPATHDarwin(filename, rpath)
        else:
            _setSharedLibraryRPATHElf(filename, rpath)


def callInstallNameTool(filename, mapping, id_path, rpath):
    """Update the macOS shared library information for a binary or shared library.

    Adds the rpath path name `rpath` in the specified `filename` Mach-O
    binary or shared library. If the Mach-O binary already contains the new
    `rpath` path name, it is an error.

    Args:
        filename - The file to be modified.
        mapping  - old_path, new_path pairs of values that should be changed
        id_path  - Use this value for library id
        rpath    - Set this as an rpath if not None, delete if False

    Returns:
        None

    Notes:
        This is obviously macOS specific.
    """
    command = ["install_name_tool"]

    needs_call = False
    for old_path, new_path in mapping:
        if old_path != new_path:
            command += ("-change", old_path, new_path)
            needs_call = True

    if rpath is not None:
        command += ("-add_rpath", os.path.join(rpath, "."))
        needs_call = True

    if id_path is not None:
        command += ("-id", id_path)
        needs_call = True

    command.append(filename)

    if needs_call:
        with withMadeWritableFileMode(filename):
            executeToolChecked(
                logger=postprocessing_logger,
                command=command,
                absence_message=_install_name_tool_usage,
                stderr_filter=_filterInstallNameToolErrorOutput,
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
    # spell-checker: ignore pywin32

    for path_element in sys.path:
        if not path_element:
            continue

        candidate = os.path.join(path_element, "pywin32_system32")

        if os.path.isdir(candidate):
            return candidate


def detectBinaryMinMacOS(binary_filename):
    """Detect the minimum required macOS version of a binary.

    Args:
        binary_filename - path of the binary to check

    Returns:
        str - minimum OS version that the binary will run on

    """

    minos_version = None

    # This is cached, so we don't have to care about that.
    stdout = getOtoolListing(binary_filename)

    lines = stdout.split(b"\n")

    for i, line in enumerate(lines):
        # Form one, used by CPython builds.
        if line.endswith(b"cmd LC_VERSION_MIN_MACOSX"):
            line = lines[i + 2]
            if str is not bytes:
                line = line.decode("utf8")

            minos_version = line.split("version ", 1)[1]
            break

        # Form two, used by Apple Python builds.
        if line.strip().startswith(b"minos"):
            if str is not bytes:
                line = line.decode("utf8")

            minos_version = line.split("minos ", 1)[1]
            break

    return minos_version


_re_dll_filename = re.compile(r"^.*(\.(?:dll|so(?:\..*)|dylib))$", re.IGNORECASE)


def locateDLLsInDirectory(directory):
    """Locate all DLLs in a folder

    Returns:
        list of (filename, filename_relative, dll_extension)
    """

    # This needs to be done a bit more manually, because DLLs on Linux can have no
    # defined suffix, cannot use e.g. only_suffixes for this.
    result = []

    for filename in getFileList(path=directory):
        filename_relative = os.path.relpath(filename, start=directory)

        # TODO: Might want to be OS specific on what to match.
        match = _re_dll_filename.match(filename_relative)

        if match:
            result.append((filename, filename_relative, match.group(1)))

    return result


_file_usage = "The 'file' tool is used to detect macOS file architectures."

_file_output_cache = {}


def _getFileCommandOutput(filename):
    """Cached file output."""

    if filename not in _file_output_cache:
        file_output = executeToolChecked(
            logger=postprocessing_logger,
            command=("file", filename),
            absence_message=_file_usage,
            decoding=str is not bytes,
        )

        assert file_output.startswith(filename + ":")
        file_output = file_output[len(filename) + 1 :].splitlines()[0].strip()

        _file_output_cache[filename] = file_output

    return _file_output_cache[filename]


def hasUniversalOrMatchingMacOSArchitecture(filename):
    assert isMacOS() and os.path.isfile(filename), filename

    file_output = _getFileCommandOutput(filename)

    return "universal" in file_output or getMacOSTargetArch() in file_output


# spell-checker: ignore lipo

_lipo_usage = (
    "The 'lipo' tool from XCode is used to manage universal binaries on macOS platform."
)


def makeMacOSThinBinary(dest_path, original_path):
    file_output = _getFileCommandOutput(dest_path)

    macos_target_arch = getMacOSTargetArch()

    if "universal" in file_output:
        executeToolChecked(
            logger=postprocessing_logger,
            command=(
                "lipo",
                "-thin",
                macos_target_arch,
                dest_path,
                "-o",
                dest_path + ".tmp",
            ),
            absence_message=_lipo_usage,
        )

        with withMadeWritableFileMode(dest_path):
            os.unlink(dest_path)
            os.rename(dest_path + ".tmp", dest_path)
    elif macos_target_arch not in file_output:
        postprocessing_logger.sysexit(
            "Error, cannot use file '%s' (%s) to build arch '%s' result"
            % (original_path, file_output, macos_target_arch)
        )


def copyDllFile(source_path, dist_dir, dest_path, executable):
    """Copy an extension/DLL file making some adjustments on the way."""

    target_filename = os.path.join(dist_dir, dest_path)
    makeContainingPath(target_filename)

    copyFile(source_path=source_path, dest_path=target_filename)

    if isWin32Windows() and python_version < 0x300:
        _removeSxsFromDLL(target_filename)

    if isMacOS() and getMacOSTargetArch() != "universal":
        makeMacOSThinBinary(dest_path=target_filename, original_path=source_path)

    if isLinux():
        # Path must be normalized for this to be correct, but entry points enforced that.
        count = dest_path.count(os.path.sep)

        # TODO: This ought to depend on actual presence of used DLLs with middle
        # paths and not just do it, but maybe there is not much harm in it.
        rpath = ":".join(
            os.path.join("$ORIGIN", *([".."] * c)) for c in range(count, -1, -1)
        )

        setSharedLibraryRPATH(target_filename, rpath)

    if isWin32Windows() and isUnstripped():
        pdb_filename = changeFilenameExtension(path=source_path, extension=".pdb")

        if os.path.exists(pdb_filename):
            copyFile(
                source_path=pdb_filename,
                dest_path=changeFilenameExtension(
                    path=target_filename, extension=".pdb"
                ),
            )

    if isMacOS():
        # spell-checker: ignore xattr

        executeToolChecked(
            logger=postprocessing_logger,
            command=("xattr", "-c", target_filename),
            absence_message="needs 'xattr' to remove extended attributes",
        )

    if executable:
        addFileExecutablePermission(target_filename)


def getDLLVersion(filename):
    """Determine version of the DLL filename."""
    if isMacOS():
        return _getDLLVersionMacOS(filename)
    elif isWin32Windows():
        return _getDLLVersionWindows(filename)


def getWindowsRunningProcessModuleFilename(handle):
    """Run time lookup of filename of a module in the current Python process."""

    import ctypes.wintypes

    MAX_PATH = 4096
    buf = ctypes.create_unicode_buffer(MAX_PATH)

    GetModuleFileName = ctypes.windll.kernel32.GetModuleFileNameW
    GetModuleFileName.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD,
    )
    GetModuleFileName.restype = ctypes.wintypes.DWORD

    res = GetModuleFileName(handle, buf, MAX_PATH)
    if res == 0:
        raiseWindowsError("getWindowsRunningProcessModuleFilename")

    return os.path.normcase(buf.value)


def _getWindowsRunningProcessModuleHandles():
    """Return list of process module handles for running process."""
    import ctypes.wintypes

    try:
        EnumProcessModulesProc = ctypes.windll.psapi.EnumProcessModules
    except AttributeError:
        EnumProcessModulesProc = ctypes.windll.kernel32.EnumProcessModules

    EnumProcessModulesProc.restype = ctypes.wintypes.BOOL
    EnumProcessModulesProc.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.HANDLE),
        ctypes.wintypes.LONG,
        ctypes.POINTER(ctypes.wintypes.ULONG),
    )

    # Very unlikely that this is not sufficient for CPython.
    handles = (ctypes.wintypes.HANDLE * 1024)()
    needed = ctypes.wintypes.ULONG()

    res = EnumProcessModulesProc(
        ctypes.windll.kernel32.GetCurrentProcess(),
        handles,
        ctypes.sizeof(handles),
        ctypes.byref(needed),
    )

    if not res:
        raiseWindowsError("getWindowsRunningProcessModuleHandles")

    return tuple(handle for handle in handles if handle is not None)


def getWindowsRunningProcessDLLPaths():
    result = OrderedDict()

    for handle in _getWindowsRunningProcessModuleHandles():
        try:
            filename = getWindowsRunningProcessModuleFilename(handle)
        except WindowsError:
            continue

        result[os.path.basename(filename)] = filename

    return result


# spell-checker: ignore termux DT_RUNPATH
_termux_elf_cleaner_usage = (
    "Needs 'termux-elf-cleaner' to clean up created files. Install it for best results."
)


def cleanupHeaderForAndroid(filename):
    """Change a DT_RPATH to DT_RUNPATH

    On Android this seems required, because the linker doesn't support the one
    created by default.
    """

    executeToolChecked(
        logger=postprocessing_logger,
        command=("patchelf", "--shrink-rpath", filename),
        stderr_filter=_filterPatchelfErrorOutput,
        absence_message=_patchelf_usage,
    )

    executeToolChecked(
        logger=postprocessing_logger,
        command=("termux-elf-cleaner", "--quiet", filename),
        absence_message=_termux_elf_cleaner_usage,
        optional=True,
    )


_nm_usage = """\
Error, needs 'nm' on your system, to detect exported DLL symbols."""


def _decodeWin32EntryPoint(entry_point_name):
    if str is bytes:
        return entry_point_name
    else:
        # Not sure about the actual encoding used, this will cover most cases.
        return entry_point_name.decode("utf8", "backslashreplace")


def getPEFileUsedDllNames(filename):
    """Return the used DLL PE file information of a Windows EXE or DLL

    Args:
        filename - The file to be investigated.

    Notes:
        Use of this is obviously only for Windows, although the module
        will exist on other platforms too.
    """

    pefile = importFromInlineCopy("pefile", must_exist=True)

    try:
        pe_info = pefile.PE(filename)
    except pefile.PEFormatError:
        return None

    # TODO: Check arch with pefile as well and ignore wrong arches if asked to.

    # TODO: The decoding cannot expect ASCII, but also surely is not UTF8.
    return OrderedSet(
        dll_entry.dll.decode("utf8")
        for dll_entry in getattr(pe_info, "DIRECTORY_ENTRY_IMPORT", ())
    )


def getDllExportedSymbols(logger, filename):
    if isWin32Windows():
        pefile = importFromInlineCopy("pefile", must_exist=True)

        try:
            pe_info = pefile.PE(filename)
        except pefile.PEFormatError:
            return None

        return tuple(
            _decodeWin32EntryPoint(entry_point.name)
            for entry_point in pe_info.DIRECTORY_ENTRY_EXPORT.symbols
            if entry_point.name is not None
        )
    else:
        if isLinux():
            command = ("nm", "-D", filename)
        elif isMacOS():
            command = ("nm", "-gU", filename) + _getMacOSArchOption()
        else:
            # Need to add e.g. FreeBSD here.
            assert False

        output = executeToolChecked(
            logger=logger,
            command=command,
            absence_message=_nm_usage,
        )

        result = OrderedSet()
        for line in output.splitlines():
            try:
                _addr, marker, symbol_name = line.split()
            except ValueError:
                continue

            if marker == b"T":
                result.add(symbol_name.decode("utf8"))

        return result


def getDllSuffix():
    if isWin32Windows():
        return ".dll"
    elif isMacOS():
        return ".dylib"
    else:
        return ".so"


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
