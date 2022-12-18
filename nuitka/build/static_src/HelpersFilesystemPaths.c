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

uint32_t getFileCRC32(filename_char_t const *filename) {
#if defined(_WIN32)
    FILE_HANDLE file_handle = CreateFileW(filename, GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

    if (file_handle == NULL) {
        return 0;
    }

    int64_t file_size = getFileSize(file_handle);

    HANDLE handle_mapping = CreateFileMappingW(file_handle, NULL, PAGE_READONLY, 0, 0, NULL);

    if (handle_mapping == NULL) {
        CloseHandle(file_handle);

        return 0;
    }

    unsigned char const *data = (unsigned char const *)MapViewOfFile(handle_mapping, FILE_MAP_READ, 0, 0, 0);

    uint32_t result;

    if (unlikely(data == NULL)) {
        result = 0;
    } else {
        result = calcCRC32(data, (long)file_size);
        // Lets use 0 for error indication.
        if (result == 0) {
            result = 1;
        }

        UnmapViewOfFile(data);
    }

    CloseHandle(handle_mapping);
    CloseHandle(file_handle);

    return result;
#else
    int file_handle = open(filename, O_RDONLY);

    if (file_handle == -1) {
        return 0;
    }

    size_t file_size = lseek(file_handle, 0, SEEK_END);
    lseek(file_handle, 0, SEEK_SET);

    unsigned char chunk[32768];

    uint32_t crc32 = initCRC32();

    while (file_size > 0) {
        ssize_t read_bytes = (ssize_t)read(file_handle, chunk, sizeof(chunk));

        if (read_bytes < 0) {
            close(file_handle);
            return 0;
        }

        crc32 = updateCRC32(crc32, chunk, read_bytes);

        file_size -= read_bytes;
    }

    crc32 = finalizeCRC32(crc32);
    uint32_t result = crc32;

    // TODO: Check if mmap is faster and if not, why
#if 0
    unsigned char const *data = mmap(NULL, file_size, PROT_READ, MAP_PRIVATE, file_handle, 0);

    uint32_t result;

    if (unlikely(data == MAP_FAILED)) {
        result = 0;
    } else {
        result = calcCRC32(data, file_size);
        // Lets use 0 for error indication.
        if (result == 0) {
            result = 1;
        }

        munmap((void *)data, file_size);
    }
#endif
    close(file_handle);

    return result;
#endif
}
