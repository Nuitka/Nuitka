//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
// Tools for working with file, and paths cross platform
// for use in both onefile bootstrap and python compiled
// program.

#if defined(__APPLE__)
#include <dlfcn.h>
#include <libgen.h>
#include <mach-o/dyld.h>
#endif

#if defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/sysctl.h>
#endif

#if !defined(_WIN32)
#include <dlfcn.h>
#include <fcntl.h>
#include <libgen.h>
#include <pwd.h>
#include <stdlib.h>
#include <strings.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <unistd.h>
#endif

// We are using in onefile bootstrap as well, so copy it.
#ifndef Py_MIN
#define Py_MIN(x, y) (((x) > (y)) ? (y) : (x))
#endif

#include "nuitka/filesystem_paths.h"
#include "nuitka/safe_string_ops.h"

filename_char_t *getBinaryPath(void) {
    static filename_char_t binary_filename[MAXPATHLEN];

#if defined(_WIN32)
    DWORD res = GetModuleFileNameW(NULL, binary_filename, sizeof(binary_filename) / sizeof(wchar_t));
    if (res == 0) {
        abort();
    }
#elif defined(__APPLE__)
    uint32_t bufsize = sizeof(binary_filename);
    int res = _NSGetExecutablePath(binary_filename, &bufsize);

    if (res != 0) {
        abort();
    }
#elif defined(__FreeBSD__) || defined(__OpenBSD__)
    /* Not all of FreeBSD has /proc file system, so use the appropriate
     * "sysctl" instead.
     */
    int mib[4];
    mib[0] = CTL_KERN;
    mib[1] = KERN_PROC;
    mib[2] = KERN_PROC_PATHNAME;
    mib[3] = -1;
    size_t cb = sizeof(binary_filename);
    int res = sysctl(mib, 4, binary_filename, &cb, NULL, 0);

    if (res != 0) {
        abort();
    }
#else
    /* The remaining platforms, mostly Linux or compatible. */

    /* The "readlink" call does not terminate result, so fill zeros there, then
     * it is a proper C string right away. */
    memset(binary_filename, 0, sizeof(binary_filename));
    ssize_t res = readlink("/proc/self/exe", binary_filename, sizeof(binary_filename) - 1);

    if (res == -1) {
        abort();
    }
#endif

    return binary_filename;
}

bool readFileChunk(FILE_HANDLE file_handle, void *buffer, size_t size) {
    // printf("Reading %d\n", size);

#if defined(_WIN32)
    DWORD read_size;
    BOOL bool_res = ReadFile(file_handle, buffer, (DWORD)size, &read_size, NULL);

    return bool_res && (read_size == size);
#else
    size_t read_size = fread(buffer, 1, size, file_handle);

    return read_size == size;
#endif
}

bool writeFileChunk(FILE_HANDLE target_file, void *chunk, size_t chunk_size) {
#if defined(_WIN32)
    DWORD write_size = 0;
    return WriteFile(target_file, chunk, (DWORD)chunk_size, &write_size, NULL);
#else
    size_t written = fwrite(chunk, 1, chunk_size, target_file);
    return written == chunk_size;
#endif
}

FILE_HANDLE createFileForWriting(filename_char_t const *filename) {
#if defined(_WIN32)
    FILE_HANDLE result = CreateFileW(filename, GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, 0, NULL);
#else
    FILE *result = fopen(filename, "wb");
#endif

    return result;
}

FILE_HANDLE openFileForReading(filename_char_t const *filename) {
#if defined(_WIN32)
    FILE_HANDLE result = CreateFileW(filename, GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
#else
    FILE *result = fopen(filename, "rb");
#endif

    return result;
}

bool closeFile(FILE_HANDLE target_file) {
#if defined(_WIN32)
    CloseHandle(target_file);
    return true;
#else
    int r = fclose(target_file);

    return r == 0;
#endif
}

int64_t getFileSize(FILE_HANDLE file_handle) {
#if defined(_WIN32)
    // TODO: File size is truncated here, but maybe an OK thing.
    DWORD file_size = GetFileSize(file_handle, NULL);

    if (file_size == INVALID_FILE_SIZE) {
        return -1;
    }
#else
    int res = fseek(file_handle, 0, SEEK_END);

    if (res != 0) {
        return -1;
    }

    long file_size = ftell(file_handle);

    res = fseek(file_handle, 0, SEEK_SET);

    if (res != 0) {
        return -1;
    }
#endif

    return (int64_t)file_size;
}

#if !defined(_WIN32)
#if defined(__APPLE__)
#include <copyfile.h>
#else
#if defined(__MSYS__)
static bool sendfile(int output_file, int input_file, off_t *bytesCopied, size_t count) {
    char buffer[32768];

    *bytesCopied = 0;

    while (count > 0) {
        ssize_t read_bytes = read(input_file, buffer, Py_MIN(sizeof(buffer), count));

        if (unlikely(read <= 0)) {
            return false;
        }

        count -= read_bytes;

        ssize_t written_bytes = write(output_file, buffer, read_bytes);

        if (unlikely(written_bytes != read_bytes)) {
            return false;
        }

        *bytesCopied += written_bytes;
    }

    return true;
}
#elif !defined(__FreeBSD__)
#include <sys/sendfile.h>
#endif
#endif
#endif

int getFileMode(filename_char_t const *filename) {
#if !defined(_WIN32)
    struct stat fileinfo = {0};
    if (stat(filename, &fileinfo) == -1) {
        return -1;
    }

    return fileinfo.st_mode;
#else
    // There is no mode on Windows, but copyFile calls should get it.
    return 0;
#endif
}

bool copyFile(filename_char_t const *source, filename_char_t const *dest, int mode) {
#if !defined(_WIN32)
    int input_file = open(source, O_RDONLY);

    if (input_file == -1) {
        return false;
    }

    int output_file = creat(dest, mode);

    if (output_file == -1) {
        close(input_file);
        return false;
    }

#if defined(__APPLE__)
    // Use fcopyfile works on FreeBSD and macOS
    bool result = fcopyfile(input_file, output_file, 0, COPYFILE_ALL) == 0;
#elif defined(__FreeBSD__)
    struct stat input_fileinfo = {0};
    fstat(input_file, &input_fileinfo);
    off_t bytesCopied = 0;

    bool result = sendfile(output_file, input_file, 0, input_fileinfo.st_size, 0, &bytesCopied, 0);
#else
    // sendfile will work with on Linux 2.6.33+
    struct stat fileinfo = {0};
    fstat(input_file, &fileinfo);

    off_t bytesCopied = 0;
    bool result = sendfile(output_file, input_file, &bytesCopied, fileinfo.st_size) != -1;
#endif

    close(input_file);
    close(output_file);

    return result;
#else
    return CopyFileW(source, dest, 0) != 0;
#endif
}

bool deleteFile(filename_char_t const *filename) {
#if defined(_WIN32)
    return DeleteFileW(filename) != 0;
#else
    return unlink(filename) == 0;
#endif
}

bool renameFile(filename_char_t const *source, filename_char_t const *dest) {
// spell-checker: ignore _wrename
#if defined(_WIN32)
    return _wrename(source, dest) == 0;
#else
    return rename(source, dest) == 0;
#endif
}

#include "nuitka/checksum_tools.h"

#if defined(_WIN32)
struct MapFileToMemoryInfo {
    bool error;
    DWORD error_code;
    char const *erroring_function;
    unsigned char const *data;
    HANDLE file_handle;
    int64_t file_size;
    HANDLE handle_mapping;
};

static struct MapFileToMemoryInfo mapFileToMemory(filename_char_t const *filename) {
    struct MapFileToMemoryInfo result;

    result.file_handle = CreateFileW(filename, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                     NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

    if (result.file_handle == INVALID_HANDLE_VALUE) {
        result.error = true;
        result.error_code = GetLastError();
        result.erroring_function = "CreateFileW";

        return result;
    }

    result.file_size = getFileSize(result.file_handle);

    if (result.file_size == -1) {
        result.error = true;
        result.error_code = GetLastError();
        result.erroring_function = "GetFileSize";

        CloseHandle(result.file_handle);

        return result;
    }

    result.handle_mapping = CreateFileMappingW(result.file_handle, NULL, PAGE_READONLY, 0, 0, NULL);

    if (result.handle_mapping == NULL) {
        result.error = true;
        result.error_code = GetLastError();
        result.erroring_function = "CreateFileMappingW";

        CloseHandle(result.file_handle);

        return result;
    }

    result.data = (unsigned char const *)MapViewOfFile(result.handle_mapping, FILE_MAP_READ, 0, 0, 0);

    if (unlikely(result.data == NULL)) {
        result.error = true;
        result.error_code = GetLastError();
        result.erroring_function = "MapViewOfFile";

        CloseHandle(result.handle_mapping);
        CloseHandle(result.file_handle);

        return result;
    }

    result.error = false;
    result.error_code = 0;

    return result;
}

static void unmapFileFromMemory(struct MapFileToMemoryInfo *mapped_file) {
    assert(!mapped_file->error);

    UnmapViewOfFile(mapped_file->data);
    CloseHandle(mapped_file->handle_mapping);
    CloseHandle(mapped_file->file_handle);
}
#else

struct MapFileToMemoryInfo {
    bool error;
    int error_code;
    char const *erroring_function;
    unsigned char const *data;
    int file_handle;
    int64_t file_size;
};

static struct MapFileToMemoryInfo mapFileToMemory(filename_char_t const *filename) {
    struct MapFileToMemoryInfo result;

    result.file_handle = open(filename, O_RDONLY);

    if (unlikely(result.file_handle == -1)) {
        result.error = true;
        result.error_code = errno;
        result.erroring_function = "open";
        return result;
    }

    result.file_size = lseek(result.file_handle, 0, SEEK_END);
    if (unlikely(result.file_size == -1)) {
        result.error = true;
        result.error_code = errno;
        result.erroring_function = "lseek";

        close(result.file_handle);

        return result;
    }
    off_t res = lseek(result.file_handle, 0, SEEK_SET);

    if (unlikely(res == -1)) {
        result.error = true;
        result.error_code = errno;
        result.erroring_function = "lseek";

        close(result.file_handle);

        return result;
    }

    result.data = (unsigned char const *)mmap(NULL, result.file_size, PROT_READ, MAP_PRIVATE, result.file_handle, 0);

    if (unlikely(result.data == MAP_FAILED)) {
        result.error = true;
        result.error_code = errno;
        result.erroring_function = "mmap";

        close(result.file_handle);

        return result;
    }

    result.error = false;
    return result;
}

static void unmapFileFromMemory(struct MapFileToMemoryInfo *mapped_file) {
    assert(!mapped_file->error);

    munmap((void *)mapped_file->data, mapped_file->file_size);
    close(mapped_file->file_handle);
}
#endif

uint32_t getFileCRC32(filename_char_t const *filename) {
    struct MapFileToMemoryInfo mapped_file = mapFileToMemory(filename);

    if (mapped_file.error) {
        return 0;
    }
    uint32_t result = calcCRC32(mapped_file.data, (long)mapped_file.file_size);

    // Lets reserve "0" value for error indication.
    if (result == 0) {
        result = 1;
    }

    unmapFileFromMemory(&mapped_file);

    return result;
}

#ifdef _WIN32

static DWORD Nuitka_GetFinalPathNameByHandleW(HANDLE hFile, LPWSTR lpszFilePath, DWORD cchFilePath, DWORD dwFlags) {
    typedef DWORD(WINAPI * pfnGetFinalPathNameByHandleW)(HANDLE hFile, LPWSTR lpszFilePath, DWORD cchFilePath,
                                                         DWORD dwFlags);

    pfnGetFinalPathNameByHandleW fnGetFinalPathNameByHandleW =
        (pfnGetFinalPathNameByHandleW)GetProcAddress(GetModuleHandleA("Kernel32.dll"), "GetFinalPathNameByHandleW");

    if (fnGetFinalPathNameByHandleW != NULL) {
        return fnGetFinalPathNameByHandleW(hFile, lpszFilePath, cchFilePath, dwFlags);
    } else {
        // There are no symlinks before Windows Vista.
        return 0;
    }
}

static void resolveFileSymbolicLink(wchar_t *resolved_filename, wchar_t const *filename, DWORD resolved_filename_size,
                                    bool resolve_symlinks) {
    // Resolve any symbolic links in the filename.
    // Copies the resolved path over the top of the parameter.

    if (resolve_symlinks) {
        // Open the file in the most non-exclusive way possible
        HANDLE file_handle = CreateFileW(filename, 0, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                                         OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

        if (unlikely(file_handle == INVALID_HANDLE_VALUE)) {
            abort();
        }

        // In case, the Windows API for symlinks does not yet exist, just used
        // the unresolved one.
        copyStringSafeW(resolved_filename, filename, resolved_filename_size);

        // Resolve the path, get the result with a drive letter
        DWORD len = Nuitka_GetFinalPathNameByHandleW(file_handle, resolved_filename, resolved_filename_size,
                                                     FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);

        CloseHandle(file_handle);

        if (unlikely(len >= resolved_filename_size)) {
            abort();
        }

        // Avoid network filenames added by just the resolution, revert it if
        // they are pointing to local drive.
        if (wcsncmp(resolved_filename, L"\\\\?\\", 4) == 0) {
            if (wcscmp(resolved_filename + 4, filename) == 0) {
                copyStringSafeW(resolved_filename, filename, resolved_filename_size);
            } else if (resolved_filename[5] == L':') {
                copyStringSafeW(resolved_filename, resolved_filename + 4, resolved_filename_size);
            }
        }
    } else {
        copyStringSafeW(resolved_filename, filename, resolved_filename_size);
    }
}

#else

static void resolveFileSymbolicLink(char *resolved_filename, char const *filename, size_t resolved_filename_size,
                                    bool resolve_symlinks) {
    if (resolve_symlinks) {
        // At least on macOS, realpath cannot allocate a buffer, itself, so lets
        // use a local one, only on Linux we could use NULL argument and have a
        // malloc of the resulting value.
        char buffer[MAXPATHLEN];

        char *result = realpath(filename, buffer);

        if (unlikely(result == NULL)) {
            abort();
        }

        copyStringSafe(resolved_filename, buffer, resolved_filename_size);
    } else {
        copyStringSafe(resolved_filename, filename, resolved_filename_size);
    }
}
#endif

#ifdef _WIN32
wchar_t const *getBinaryFilenameWideChars(bool resolve_symlinks) {
    static wchar_t binary_filename[MAXPATHLEN + 1];
    static bool init_done = false;

    if (init_done == false) {
        DWORD res = GetModuleFileNameW(NULL, binary_filename, sizeof(binary_filename) / sizeof(wchar_t));
        assert(res != 0);

        // Resolve any symlinks we were invoked via
        resolveFileSymbolicLink(binary_filename, binary_filename, sizeof(binary_filename) / sizeof(wchar_t),
                                resolve_symlinks);
    }

    return binary_filename;
}
#endif

#ifdef _WIN32
extern wchar_t const *getBinaryFilenameWideChars(bool resolve_symlinks);

char const *getBinaryFilenameHostEncoded(bool resolve_symlinks) {
    static char *binary_filename = NULL;
    static char *binary_filename_resolved = NULL;

    char *binary_filename_target;

    if (resolve_symlinks) {
        binary_filename_target = binary_filename_resolved;
    } else {
        binary_filename_target = binary_filename;
    }

    if (binary_filename_target != NULL) {
        return binary_filename_target;
    }
    wchar_t const *w = getBinaryFilenameWideChars(resolve_symlinks);

    DWORD bufsize = WideCharToMultiByte(CP_ACP, 0, w, -1, NULL, 0, NULL, NULL);
    assert(bufsize != 0);

    binary_filename_target = (char *)malloc(bufsize + 1);
    assert(binary_filename_target);

    DWORD res2 = WideCharToMultiByte(CP_ACP, 0, w, -1, binary_filename_target, bufsize, NULL, NULL);
    assert(res2 != 0);

    if (unlikely(res2 > bufsize)) {
        abort();
    }

    return (char const *)binary_filename_target;
}

#else
char const *getBinaryFilenameHostEncoded(bool resolve_symlinks) {
    const int buffer_size = MAXPATHLEN + 1;

    static char binary_filename[MAXPATHLEN + 1] = {0};
    static char binary_filename_resolved[MAXPATHLEN + 1] = {0};

    char *binary_filename_target;

    if (resolve_symlinks) {
        binary_filename_target = binary_filename_resolved;
    } else {
        binary_filename_target = binary_filename;
    }

    if (*binary_filename_target != 0) {
        return binary_filename_target;
    }

#if defined(__APPLE__)
    uint32_t bufsize = buffer_size;
    int res = _NSGetExecutablePath(binary_filename_target, &bufsize);

    if (unlikely(res != 0)) {
        abort();
    }

    // Resolve any symlinks we were invoked via
    resolveFileSymbolicLink(binary_filename_target, binary_filename_target, buffer_size, resolve_symlinks);

#elif defined(__FreeBSD__) || defined(__OpenBSD__)
    /* Not all of FreeBSD has /proc file system, so use the appropriate
     * "sysctl" instead.
     */
    int mib[4];
    mib[0] = CTL_KERN;
    mib[1] = KERN_PROC;
    mib[2] = KERN_PROC_PATHNAME;
    mib[3] = -1;
    size_t cb = buffer_size;
    int res = sysctl(mib, 4, binary_filename_target, &cb, NULL, 0);

    if (unlikely(res != 0)) {
        abort();
    }

    // Resolve any symlinks we were invoked via
    resolveFileSymbolicLink(binary_filename_target, binary_filename_target, buffer_size, resolve_symlinks);
#else
    /* The remaining platforms, mostly Linux or compatible. */

    /* The "readlink" call does not terminate result, so fill zeros there, then
     * it is a proper C string right away. */
    memset(binary_filename_target, 0, buffer_size);
    ssize_t res = readlink("/proc/self/exe", binary_filename_target, buffer_size - 1);

    if (unlikely(res == -1)) {
        abort();
    }

    // Resolve any symlinks we were invoked via
    resolveFileSymbolicLink(binary_filename_target, binary_filename_target, buffer_size, resolve_symlinks);
#endif

    return binary_filename_target;
}
#endif

#if defined(_WIN32)

// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>

#include <shlobj.h>
#include <shlwapi.h>

// For less complete C compilers.
#ifndef CSIDL_LOCAL_APPDATA
#define CSIDL_LOCAL_APPDATA 28
#endif
#ifndef CSIDL_PROFILE
#define CSIDL_PROFILE 40
#endif

// spell-checker: ignore csidl

static bool appendStringCSIDLPathW(wchar_t *target, int csidl_id, size_t buffer_size) {
    wchar_t path_buffer[MAX_PATH];
#if !defined(_M_ARM64)
    int res = SHGetFolderPathW(NULL, csidl_id, NULL, 0, path_buffer);

    if (res != S_OK) {
        return false;
    }
#else
    DWORD res = 0;
    if (csidl_id == CSIDL_PROFILE) {
        res = GetEnvironmentVariableW(L"USERPROFILE", path_buffer, sizeof(path_buffer));
    } else if (csidl_id == CSIDL_LOCAL_APPDATA) {
        res = GetEnvironmentVariableW(L"LOCALAPPDATA", path_buffer, sizeof(path_buffer));
    }

    if (res == 0 || res > sizeof(path_buffer)) {
        return false;
    }
#endif
    appendWStringSafeW(target, path_buffer, buffer_size);

    return true;
}

bool expandTemplatePathW(wchar_t *target, wchar_t const *source, size_t buffer_size) {
    target[0] = 0;

    wchar_t var_name[1024];
    wchar_t *w = NULL;

    while (*source != 0) {
        if (*source == '%') {
            if (w == NULL) {
                w = var_name;
                *w = 0;

                source++;

                continue;
            } else {
                *w = 0;

                bool is_path = false;

                if (wcsicmp(var_name, L"TEMP") == 0) {
                    GetTempPathW((DWORD)buffer_size, target);
                    is_path = true;
                } else if (wcsicmp(var_name, L"PROGRAM") == 0) {
#if _NUITKA_ONEFILE_TEMP_BOOL == 1
                    appendWStringSafeW(target, __wargv[0], buffer_size);
#else
                    if (!GetModuleFileNameW(NULL, target, (DWORD)buffer_size)) {
                        return false;
                    }
#endif
                } else if (wcsicmp(var_name, L"PROGRAM_BASE") == 0) {
                    if (expandTemplatePathW(target, L"%PROGRAM%", buffer_size - wcslen(target)) == false) {
                        return false;
                    }

                    size_t length = wcslen(target);

                    if ((length >= 4) && (wcsicmp(target + length - 4, L".exe") == 0)) {
                        target[length - 4] = 0;
                    }
                } else if (wcsicmp(var_name, L"PID") == 0) {
                    char pid_buffer[128];
                    snprintf(pid_buffer, sizeof(pid_buffer), "%d", GetCurrentProcessId());

                    appendStringSafeW(target, pid_buffer, buffer_size);
                } else if (wcsicmp(var_name, L"HOME") == 0) {
                    if (appendStringCSIDLPathW(target, CSIDL_PROFILE, buffer_size) == false) {
                        return false;
                    }
                    is_path = true;
                } else if (wcsicmp(var_name, L"CACHE_DIR") == 0) {
                    if (appendStringCSIDLPathW(target, CSIDL_LOCAL_APPDATA, buffer_size) == false) {
                        return false;
                    }
                    is_path = true;
#ifdef NUITKA_COMPANY_NAME
                } else if (wcsicmp(var_name, L"COMPANY") == 0) {
                    appendWStringSafeW(target, L"" NUITKA_COMPANY_NAME, buffer_size);
#endif
#ifdef NUITKA_PRODUCT_NAME
                } else if (wcsicmp(var_name, L"PRODUCT") == 0) {
                    appendWStringSafeW(target, L"" NUITKA_PRODUCT_NAME, buffer_size);
#endif
#ifdef NUITKA_VERSION_COMBINED
                } else if (wcsicmp(var_name, L"VERSION") == 0) {
                    appendWStringSafeW(target, L"" NUITKA_VERSION_COMBINED, buffer_size);
#endif
                } else if (wcsicmp(var_name, L"TIME") == 0) {
                    char time_buffer[1024];

                    __int64 time = 0;
                    assert(sizeof(time) == sizeof(FILETIME));
                    GetSystemTimeAsFileTime((LPFILETIME)&time);

                    snprintf(time_buffer, sizeof(time_buffer), "%lld", time);

                    appendStringSafeW(target, time_buffer, buffer_size);
                } else {
                    return false;
                }

                // Skip over appended stuff.
                while (*target) {
                    target++;
                    buffer_size -= 1;
                }

                if (is_path) {
                    while (*(target - 1) == FILENAME_SEP_CHAR) {
                        target--;
                        *target = 0;
                        buffer_size += 1;
                    }
                }

                w = NULL;
                source++;

                continue;
            }
        }

        if (w != NULL) {
            *w++ = *source++;
            continue;
        }

        if (buffer_size < 1) {
            return false;
        }

        *target++ = *source++;
        buffer_size -= 1;
    }

    *target = 0;

    return true;
}

#else

bool expandTemplatePath(char *target, char const *source, size_t buffer_size) {
    target[0] = 0;

    char var_name[1024];
    char *w = NULL;

    while (*source != 0) {
        if (*source == '%') {
            if (w == NULL) {
                w = var_name;
                *w = 0;

                source++;

                continue;
            } else {
                *w = 0;

                bool is_path = false;

                if (strcasecmp(var_name, "TEMP") == 0) {
                    char const *tmp_dir = getenv("TMPDIR");
                    if (tmp_dir == NULL) {
                        tmp_dir = "/tmp";
                    }

                    appendStringSafe(target, tmp_dir, buffer_size);
                    is_path = true;
                } else if (strcasecmp(var_name, "PROGRAM") == 0) {
                    char const *exe_name = getBinaryFilenameHostEncoded(false);

                    appendStringSafe(target, exe_name, buffer_size);
                } else if (strcasecmp(var_name, "PROGRAM_BASE") == 0) {
                    if (expandTemplatePath(target, "%PROGRAM%", buffer_size - strlen(target)) == false) {
                        return false;
                    }

                    size_t length = strlen(target);

                    if ((length >= 4) && (strcasecmp(target + length - 4, ".exe") == 0)) {
                        target[length - 4] = 0;
                    }
                } else if (strcasecmp(var_name, "PID") == 0) {
                    char pid_buffer[128];

                    snprintf(pid_buffer, sizeof(pid_buffer), "%d", getpid());

                    appendStringSafe(target, pid_buffer, buffer_size);
                } else if (strcasecmp(var_name, "HOME") == 0) {
                    char const *home_path = getenv("HOME");

                    if (home_path == NULL) {
                        struct passwd *pw_data = getpwuid(getuid());

                        if (unlikely(pw_data == NULL)) {
                            return false;
                        }

                        home_path = pw_data->pw_dir;
                    }

                    appendStringSafe(target, home_path, buffer_size);
                    is_path = true;
                } else if (strcasecmp(var_name, "CACHE_DIR") == 0) {
                    if (expandTemplatePath(target, "%HOME%", buffer_size - strlen(target)) == false) {
                        return false;
                    }

                    appendCharSafe(target, '/', buffer_size);
                    appendStringSafe(target, ".cache", buffer_size);
                    is_path = true;
#ifdef NUITKA_COMPANY_NAME
                } else if (strcasecmp(var_name, "COMPANY") == 0) {
                    appendStringSafe(target, NUITKA_COMPANY_NAME, buffer_size);
#endif
#ifdef NUITKA_PRODUCT_NAME
                } else if (strcasecmp(var_name, "PRODUCT") == 0) {
                    appendStringSafe(target, NUITKA_PRODUCT_NAME, buffer_size);
#endif
#ifdef NUITKA_VERSION_COMBINED
                } else if (strcasecmp(var_name, "VERSION") == 0) {
                    appendStringSafe(target, NUITKA_VERSION_COMBINED, buffer_size);
#endif
                } else if (strcasecmp(var_name, "TIME") == 0) {
                    char time_buffer[1024];

                    struct timeval current_time;
                    gettimeofday(&current_time, NULL);
                    snprintf(time_buffer, sizeof(time_buffer), "%ld_%ld", current_time.tv_sec,
                             (long)current_time.tv_usec);

                    appendStringSafe(target, time_buffer, buffer_size);
                } else {
                    return false;
                }
                // Skip over appended stuff.
                while (*target) {
                    target++;
                    buffer_size -= 1;
                }

                if (is_path) {
                    while (*(target - 1) == FILENAME_SEP_CHAR) {
                        target--;
                        *target = 0;
                        buffer_size += 1;
                    }
                }

                w = NULL;
                source++;

                continue;
            }
        }

        if (w != NULL) {
            *w++ = *source++;
            continue;
        }

        if (buffer_size < 1) {
            return false;
        }

        *target++ = *source++;
        buffer_size -= 1;
    }

    *target = 0;

    return true;
}

#endif