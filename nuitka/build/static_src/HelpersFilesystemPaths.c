//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

#if defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/sysctl.h>
#endif

// We are using in onefile bootstrap as well, so copy it.
#ifndef Py_MIN
#define Py_MIN(x, y) (((x) > (y)) ? (y) : (x))
#endif

#include "nuitka/filesystem_paths.h"

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
#include <fcntl.h>
#include <unistd.h>
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

#if !defined(_WIN32)
#include <fcntl.h>
#include <sys/mman.h>
#endif

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
