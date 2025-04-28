//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Tools for working with file, and paths cross platform
// for use in both onefile bootstrap and python compiled
// program.

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/sysctl.h>
#endif

#if !defined(_WIN32)
#include <dlfcn.h>
#include <fcntl.h>
#include <libgen.h>
#if !defined(__wasi__)
#include <pwd.h>
#endif
#include <stdlib.h>
#include <strings.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <unistd.h>
#endif

#if defined(__APPLE__)
#include <mach-o/dyld.h>
#endif

// We are using in onefile bootstrap as well, so copy it.
#ifndef Py_MIN
#define Py_MIN(x, y) (((x) > (y)) ? (y) : (x))
#endif

#include "nuitka/environment_variables_system.h"
#include "nuitka/filesystem_paths.h"
#include "nuitka/safe_string_ops.h"

void normalizePath(filename_char_t *filename) {
    filename_char_t *w = filename;

    while (*w != 0) {
        // Eliminate duplicate slashes.
        if (*w == FILENAME_SEP_CHAR) {
            while (*(w + 1) == FILENAME_SEP_CHAR) {
                filename_char_t *f = w;

                for (;;) {
                    *f = *(f + 1);

                    if (*f == 0) {
                        break;
                    }

                    f++;
                }
            }
        }

        w++;
    }

    // TODO: Need to also remove "./" and resolve "/../" sequences for best
    // results.
}

#if defined(_WIN32)
// Replacement for RemoveFileSpecW, slightly smaller, avoids a link library.
static wchar_t *stripFilenameW(wchar_t *path) {
    wchar_t *last_slash = NULL;

    while (*path != 0) {
        if (*path == L'\\') {
            last_slash = path;
        }

        path++;
    }

    if (last_slash != NULL) {
        *last_slash = 0;
    }

    return last_slash;
}

filename_char_t *stripBaseFilename(filename_char_t const *filename) {
    static wchar_t result[MAXPATHLEN + 1];

    copyStringSafeW(result, filename, sizeof(result) / sizeof(wchar_t));
    stripFilenameW(result);

    return result;
}
#else
filename_char_t *stripBaseFilename(filename_char_t const *filename) {
    static char result[MAXPATHLEN + 1];
    copyStringSafe(result, filename, sizeof(result));

    return dirname(result);
}
#endif

#if defined(_WIN32)
static void makeShortFilename(wchar_t *filename, size_t buffer_size) {
#ifndef _NUITKA_EXPERIMENTAL_AVOID_SHORT_PATH
    // Query length of result first.
    DWORD length = GetShortPathNameW(filename, NULL, 0);
    if (length == 0) {
        return;
    }

    wchar_t *short_filename = (wchar_t *)malloc((length + 1) * sizeof(wchar_t));
    DWORD res = GetShortPathNameW(filename, short_filename, length);
    assert(res != 0);

    if (unlikely(res > length)) {
        abort();
    }

    filename[0] = 0;
    appendWStringSafeW(filename, short_filename, buffer_size);

    free(short_filename);
#endif
}

static void makeShortDirFilename(wchar_t *filename, size_t buffer_size) {
    wchar_t *changed = stripFilenameW(filename);
    if (changed != NULL) {
        changed = wcsdup(changed + 1);
    }

    // Shorten only the directory name.
    makeShortFilename(filename, buffer_size);

    if (changed != NULL) {
        appendWCharSafeW(filename, FILENAME_SEP_CHAR, buffer_size);
        appendWStringSafeW(filename, changed, buffer_size);

        free(changed);
    }
}

#endif

#if !defined(_WIN32)
filename_char_t *_getBinaryPath2(void) {
    static filename_char_t binary_filename[MAXPATHLEN] = {0};
    const size_t buffer_size = sizeof(binary_filename);

    if (binary_filename[0] != 0) {
        return binary_filename;
    }

#if defined(__APPLE__)
    uint32_t bufsize = buffer_size;
    int res = _NSGetExecutablePath(binary_filename, &bufsize);

    if (unlikely(res != 0)) {
        abort();
    }
#elif defined(__OpenBSD__) || defined(_AIX) || defined(_NUITKA_EXPERIMENTAL_FORCE_UNIX_BINARY_NAME)
    const char *comm = getOriginalArgv0();

    bool success = false;

    if (*comm == '/') {
        copyStringSafe(binary_filename, comm, buffer_size);
        success = true;
    } else {
        if (getcwd(binary_filename, buffer_size) == NULL) {
            abort();
        }
        // Add a separator either way, later removed.
        appendCharSafe(binary_filename, '/', buffer_size);
        appendStringSafe(binary_filename, comm, buffer_size);

        if (isExecutableFile(binary_filename)) {
            success = true;
        } else {
            char *path_environment_value = strdup(getenv("PATH"));

            if (path_environment_value != NULL) {
                char *sp;
                char *path = strtok_r(path_environment_value, ":", &sp);

                while (path != NULL) {
                    if (*path != '/') {
                        if (getcwd(binary_filename, buffer_size) == NULL) {
                            abort();
                        }

                        appendCharSafe(binary_filename, '/', buffer_size);
                    } else {
                        binary_filename[0] = 0;
                    }
                    appendStringSafe(binary_filename, path, buffer_size);
                    appendCharSafe(binary_filename, '/', buffer_size);
                    appendStringSafe(binary_filename, comm, buffer_size);

                    if (isExecutableFile(binary_filename)) {
                        success = true;
                        break;
                    }

                    path = strtok_r(NULL, ":", &sp);
                }

                free(path_environment_value);
            }
        }
    }

    if (success == true) {
        // fprintf(stderr, "Did resolve binary path %s from PATH %s.\n", comm, binary_filename);

        // TODO: Once it's fully capable, we ought to use this for all methods
        // for consistency.
        normalizePath(binary_filename);
        // fprintf(stderr, "Did normalize binary path %s from PATH %s.\n", comm, binary_filename);
    } else {
        fprintf(stderr, "Error, cannot resolve binary path %s from PATH or current directory.\n", comm);
        abort();
    }
#elif defined(__FreeBSD__)
    /* Not all of FreeBSD has /proc file system, so use the appropriate
     * "sysctl" instead.
     */
    int mib[4];
    mib[0] = CTL_KERN;
    mib[1] = KERN_PROC;
    mib[2] = KERN_PROC_PATHNAME;
    mib[3] = -1;
    size_t cb = buffer_size;
    int res = sysctl(mib, 4, binary_filename, &cb, NULL, 0);

    if (unlikely(res != 0)) {
        abort();
    }
#elif defined(__wasi__)
    const char *wasi_filename = "program.wasm";
    copyStringSafe(binary_filename, wasi_filename, buffer_size);
#elif defined(_AIX)
    char proc_link_path[64];
    snprintf(proc_link_path, sizeof(proc_link_path), "/proc/%d/object/a.out", (int)getpid());

    memset(binary_filename, 0, sizeof(binary_filename));
    ssize_t res = readlink(proc_link_path, binary_filename, buffer_size - 1);

    if (unlikely(res == -1)) {
        abort();
    }
#else
    /* The remaining platforms, mostly Linux or compatible. */

    /* The "readlink" call does not terminate result, so fill zeros there, then
     * it is a proper C string right away. */
    memset(binary_filename, 0, buffer_size);
    ssize_t res = readlink("/proc/self/exe", binary_filename, buffer_size - 1);

    if (unlikely(res == -1)) {
        abort();
    }
#endif
    return binary_filename;
}
#endif

filename_char_t const *getBinaryPath(void) {
#if defined(_WIN32)
    static filename_char_t binary_filename[MAXPATHLEN] = {0};

    if (binary_filename[0] != 0) {
        return binary_filename;
    }

    DWORD res = GetModuleFileNameW(NULL, binary_filename, sizeof(binary_filename) / sizeof(wchar_t));
    if (unlikely(res == 0)) {
        abort();
    }

    return binary_filename;
#else
    return _getBinaryPath2();
#endif
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

bool writeFileChunk(FILE_HANDLE target_file, void const *chunk, size_t chunk_size) {
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

    if (unlikely(res != 0)) {
        return -1;
    }

    long file_size = ftell(file_handle);

    res = fseek(file_handle, 0, SEEK_SET);

    if (unlikely(res != 0)) {
        return -1;
    }
#endif

    return (int64_t)file_size;
}

#if !defined(_WIN32)
#if defined(__APPLE__)
#include <copyfile.h>
#else
#if defined(__MSYS__) || defined(__HAIKU__) || defined(__OpenBSD__) || defined(_AIX) || defined(__wasi__)
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

#if !defined(_WIN32)
bool isExecutableFile(filename_char_t const *filename) {
    int mode = getFileMode(filename);

    if (mode == -1) {
        return false;
    }
    return mode & S_IXUSR;
}
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

extern error_code_t getLastErrorCode(void) {
#if defined(_WIN32)
    return GetLastError();
#else
    return errno;
#endif
}

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
        result.file_size = -1;
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

static DWORD Nuitka_GetFinalPathNameByHandleW(HANDLE hFile, LPWSTR FilePath, DWORD cchFilePath, DWORD dwFlags) {
    typedef DWORD(WINAPI * pfnGetFinalPathNameByHandleW)(HANDLE hFile, LPWSTR FilePath, DWORD cchFilePath,
                                                         DWORD dwFlags);

    pfnGetFinalPathNameByHandleW fnGetFinalPathNameByHandleW =
        (pfnGetFinalPathNameByHandleW)GetProcAddress(GetModuleHandleA("Kernel32.dll"), "GetFinalPathNameByHandleW");

    if (fnGetFinalPathNameByHandleW != NULL) {
        return fnGetFinalPathNameByHandleW(hFile, FilePath, cchFilePath, dwFlags);
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

        // Avoid network filenames with UNC prefix, they won't work for loading
        // extension modules and other things, Python avoids them too.
        if (wcsncmp(resolved_filename, L"\\\\?\\UNC\\", 8) == 0) {
            copyStringSafeW(resolved_filename, resolved_filename + 6, resolved_filename_size);
            resolved_filename[0] = L'\\';
        }

    } else {
        copyStringSafeW(resolved_filename, filename, resolved_filename_size);
    }
}

#else

static void resolveFileSymbolicLink(char *resolved_filename, char const *filename, size_t resolved_filename_size,
                                    bool resolve_symlinks) {
#ifdef __wasi__
    copyStringSafe(resolved_filename, filename, resolved_filename_size);
#else
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
#endif
}
#endif

#ifdef _WIN32
wchar_t const *getBinaryFilenameWideChars(bool resolve_symlinks) {
    static wchar_t binary_filename[MAXPATHLEN + 1] = {0};
    static wchar_t binary_filename_resolved[MAXPATHLEN + 1] = {0};

    wchar_t *buffer = resolve_symlinks ? binary_filename : binary_filename_resolved;
    assert(sizeof(binary_filename) == sizeof(binary_filename_resolved));

    if (buffer[0] == 0) {
        DWORD res = GetModuleFileNameW(NULL, buffer, sizeof(binary_filename) / sizeof(wchar_t));
        assert(res != 0);

        // Resolve any symlinks we were invoked via
        resolveFileSymbolicLink(buffer, buffer, sizeof(binary_filename) / sizeof(wchar_t), resolve_symlinks);
        makeShortDirFilename(binary_filename, sizeof(binary_filename) / sizeof(wchar_t));
    }

    return buffer;
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

    copyStringSafe(binary_filename_target, _getBinaryPath2(), buffer_size);
    resolveFileSymbolicLink(binary_filename_target, binary_filename_target, buffer_size, resolve_symlinks);

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
    int res = SHGetFolderPathW(NULL, csidl_id, NULL, 0, path_buffer);

    if (res != S_OK) {
        return false;
    }
    appendWStringSafeW(target, path_buffer, buffer_size);

    return true;
}

bool expandTemplatePathW(wchar_t *target, wchar_t const *source, size_t buffer_size) {
    target[0] = 0;

    wchar_t var_name[1024];
    wchar_t *w = NULL;

    bool var_started = false;

    while (*source != 0) {
        if (*source == L'{') {
            assert(var_started == false);
            var_started = true;

            w = var_name;
            *w = 0;

            source++;

            continue;
        } else if (*source == L'}') {
            assert(var_started == true);
            var_started = false;

            *w = 0;

            bool is_path = false;

            if (wcsicmp(var_name, L"TEMP") == 0) {
                GetTempPathW((DWORD)buffer_size, target);
                is_path = true;
            } else if (wcsicmp(var_name, L"PROGRAM") == 0) {
#if _NUITKA_ONEFILE_TEMP_BOOL
                appendWStringSafeW(target, __wargv[0], buffer_size);
#else
                if (!GetModuleFileNameW(NULL, target, (DWORD)buffer_size)) {
                    return false;
                }
#endif
            } else if (wcsicmp(var_name, L"PROGRAM_BASE") == 0) {
                if (expandTemplatePathW(target, L"{PROGRAM}", buffer_size - wcslen(target)) == false) {
                    return false;
                }

                size_t length = wcslen(target);

                if ((length >= 4) && (wcsicmp(target + length - 4, L".exe") == 0)) {
                    target[length - 4] = 0;
                }
            } else if (wcsicmp(var_name, L"PROGRAM_DIR") == 0) {
                if (expandTemplatePathW(target, L"{PROGRAM}", buffer_size - wcslen(target)) == false) {
                    return false;
                }

                stripFilenameW(target);
            } else if (wcsicmp(var_name, L"PID") == 0) {
                // Python binaries from onefile use onefile parent pid
                environment_char_t const *environment_value = NULL;

#if _NUITKA_ONEFILE_MODE
                environment_value = getEnvironmentVariable("NUITKA_ONEFILE_PARENT");
#endif
                if (environment_value != NULL) {
                    checkWStringNumber(environment_value);

                    appendWStringSafeW(target, getEnvironmentVariable("NUITKA_ONEFILE_PARENT"), buffer_size);
                } else {
                    char pid_buffer[128];
                    snprintf(pid_buffer, sizeof(pid_buffer), "%ld", GetCurrentProcessId());
                    appendStringSafeW(target, pid_buffer, buffer_size);
                }
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
                environment_char_t const *environment_value = NULL;

#if _NUITKA_ONEFILE_MODE
                environment_value = getEnvironmentVariable("NUITKA_ONEFILE_START");
#endif

                if (environment_value != NULL) {
                    appendWStringSafeW(target, getEnvironmentVariable("NUITKA_ONEFILE_START"), buffer_size);
                } else {
                    wchar_t time_buffer[1024];

                    // spell-checker: ignore LPFILETIME
                    __int64 time = 0;
                    assert(sizeof(time) == sizeof(FILETIME));
                    GetSystemTimeAsFileTime((LPFILETIME)&time);

                    swprintf(time_buffer, sizeof(time_buffer), L"%lld", time);

#if _NUITKA_ONEFILE_MODE
                    setEnvironmentVariable("NUITKA_ONEFILE_START", time_buffer);
#endif
                    appendWStringSafeW(target, time_buffer, buffer_size);
                }

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

        if (w != NULL) {
            *w++ = *source++;
            continue;
        }

        if (buffer_size < 1) {
            return false;
        }

        *target++ = *source++;
        *target = 0;
        buffer_size -= 1;
    }

    *target = 0;

    assert(var_started == false);
    return true;
}

#else

bool expandTemplatePath(char *target, char const *source, size_t buffer_size) {
    target[0] = 0;

    char var_name[1024];
    char *w = NULL;

    NUITKA_MAY_BE_UNUSED bool var_started = false;

    while (*source != 0) {
        if (*source == '{') {
            assert(var_started == false);
            var_started = true;

            w = var_name;
            *w = 0;

            source++;

            continue;
        } else if (*source == '}') {
            assert(var_started == true);
            var_started = false;
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
                if (expandTemplatePath(target, "{PROGRAM}", buffer_size - strlen(target)) == false) {
                    return false;
                }

                size_t length = strlen(target);

                if ((length >= 4) && (strcasecmp(target + length - 4, ".bin") == 0)) {
                    target[length - 4] = 0;
                }
            } else if (strcasecmp(var_name, "PROGRAM_DIR") == 0) {
                if (expandTemplatePath(target, "{PROGRAM}", buffer_size - strlen(target)) == false) {
                    return false;
                }

                size_t length = strlen(target);

                // TODO: We should have an inplace strip dirname function, like for
                // Win32 stripFilenameW, but that then knows the length and check
                // if that empties the string, but this works for now.
                while (true) {
                    if (length == 0) {
                        return false;
                    }

                    if (target[length] == '/') {
                        break;
                    }

                    target[length] = 0;
                }

                is_path = true;
            } else if (strcasecmp(var_name, "PID") == 0) {
                // Python binaries from onefile use onefile parent pid
                environment_char_t const *environment_value = NULL;

#if _NUITKA_ONEFILE_MODE
                environment_value = getEnvironmentVariable("NUITKA_ONEFILE_PARENT");
#endif
                if (environment_value != NULL) {
                    checkStringNumber(environment_value);

                    appendStringSafe(target, getEnvironmentVariable("NUITKA_ONEFILE_PARENT"), buffer_size);
                } else {
                    char pid_buffer[128];

                    snprintf(pid_buffer, sizeof(pid_buffer), "%d", getpid());

                    appendStringSafe(target, pid_buffer, buffer_size);
                }
            } else if (strcasecmp(var_name, "HOME") == 0) {
                char const *home_path = getenv("HOME");
                if (home_path == NULL) {
#ifdef __wasi__
                    return false;
#else
                    struct passwd *pw_data = getpwuid(getuid());

                    if (unlikely(pw_data == NULL)) {
                        return false;
                    }

                    home_path = pw_data->pw_dir;
#endif
                }

                appendStringSafe(target, home_path, buffer_size);
                is_path = true;
            } else if (strcasecmp(var_name, "CACHE_DIR") == 0) {
                char const *xdg_cache_home = getenv("XDG_CACHE_HOME");

                if (xdg_cache_home != NULL && xdg_cache_home[0] == '/') {
                    appendStringSafe(target, xdg_cache_home, buffer_size);
                } else {
                    if (expandTemplatePath(target, "{HOME}/.cache", buffer_size - strlen(target)) == false) {
                        return false;
                    }
                }
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
                environment_char_t const *environment_value = NULL;

#if _NUITKA_ONEFILE_MODE
                environment_value = getEnvironmentVariable("NUITKA_ONEFILE_START");
#endif

                if (environment_value != NULL) {
                    appendStringSafe(target, getEnvironmentVariable("NUITKA_ONEFILE_START"), buffer_size);
                } else {
                    char time_buffer[1024];

                    struct timeval current_time;
                    gettimeofday(&current_time, NULL);
                    snprintf(time_buffer, sizeof(time_buffer), "%ld_%ld", current_time.tv_sec,
                             (long)current_time.tv_usec);

#if _NUITKA_ONEFILE_MODE
                    setEnvironmentVariable("NUITKA_ONEFILE_START", time_buffer);
#endif

                    appendStringSafe(target, time_buffer, buffer_size);
                }
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

        if (w != NULL) {
            *w++ = *source++;
            continue;
        }

        if (buffer_size < 1) {
            return false;
        }

        *target++ = *source++;
        *target = 0;
        buffer_size -= 1;
    }

    *target = 0;

    assert(var_started == false);
    return true;
}

#endif

#if _NUITKA_DLL_MODE || _NUITKA_MODULE_MODE
#if defined(_WIN32)
// Small helper function to get current DLL handle, spell-checker: ignore lpcstr
static HMODULE getDllModuleHandle(void) {
    static HMODULE hm = NULL;

    if (hm == NULL) {
        int res =
            GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               (LPCSTR)&getDllModuleHandle, &hm);
        assert(res != 0);
    }

    assert(hm != NULL);
    return hm;
}
#endif

filename_char_t const *getDllDirectory(void) {
#if defined(_WIN32)
    static WCHAR path[MAXPATHLEN + 1];
    path[0] = 0;

    int res = GetModuleFileNameW(getDllModuleHandle(), path, MAXPATHLEN);
    assert(res != 0);

    stripFilenameW(path);

    return path;
#else
    // Need to cache it, as dirname modifies stuff.
    static char const *result = NULL;

    if (result == NULL) {
        Dl_info where;

        {
            NUITKA_MAY_BE_UNUSED int res = dladdr((void *)getDllDirectory, &where);
            assert(res != 0);
        }

        result = dirname((char *)strdup(where.dli_fname));
    }

    return result;
#endif
}
#endif
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
