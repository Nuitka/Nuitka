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
/* The main program for onefile bootstrap.
 *
 * It needs to unpack the attached files and and then loads and executes
 * the compiled program.
 *
 * spell-checker: ignore _wrename,SHFILEOPSTRUCTW,FOF_NOCONFIRMATION,FOF_NOERRORUI
 * spell-checker: ignore HRESULT,HINSTANCE,lpUnkcaller,MAKELANGID,SUBLANG
 *
 */

#define _CRT_SECURE_NO_WARNINGS

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#ifdef __NUITKA_NO_ASSERT__
#undef NDEBUG
#define NDEBUG
#endif

#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

/* Type bool */
#ifndef __cplusplus
#include "stdbool.h"
#endif

#if defined(_WIN32)
// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>

#include <imagehlp.h>
#else
#include <dirent.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

#ifndef __IDE_ONLY__
// Generated during build with optional defines.
#include "onefile_definitions.h"
#else
#define _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
#define _NUITKA_ONEFILE_TEMP 0
#define _NUITKA_ONEFILE_AUTO_UPDATE 1
#define _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
#define _NUITKA_ONEFILE_TEMP_SPEC "%TEMP%/onefile_%PID%_%TIME%"
#define _NUITKA_ONEFILE_AUTO_UPDATE_URL_SPEC "https://..."
#endif

#if _NUITKA_ONEFILE_COMPRESSION == 1
// Header goes first.
#include "zstd.h"

// Should be in our inline copy, we include all C files into this one.
#include "common/error_private.c"
#include "common/fse_decompress.c"
#include "common/xxhash.c"
#include "common/zstd_common.c"
// Need to make sure this is last in common as it depends on the others.
#include "common/entropy_common.c"

// Decompression stuff.
#include "decompress/huf_decompress.c"
#include "decompress/zstd_ddict.c"
#include "decompress/zstd_decompress.c"
#include "decompress/zstd_decompress_block.c"
#endif

// Some handy macro definitions, e.g. unlikely.
#include "nuitka/hedley.h"
#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)

// Safe string operations.
#include "HelpersSafeStrings.c"

// For tracing outputs if enabled at compile time.
#include "nuitka/tracing.h"

static void printError(char const *message) {
#if defined(_WIN32)
    LPCTSTR err_buffer;

    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL,
                  GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&err_buffer, 0, NULL);

    puts(message);
    puts(err_buffer);
#else
    perror(message);
#endif
}

static void fatalError(char const *message) {
    printError(message);
    abort();
}

static void fatalErrorTempFiles(void) { fatalError("Error, couldn't runtime expand temporary files."); }

#if _NUITKA_ONEFILE_COMPRESSION == 1
static void fatalErrorAttachedData(void) { fatalError("Error, couldn't decode attached data."); }
#endif

static void fatalErrorFindAttachedData(void) { fatalError("Error, couldn't find attached data."); }

static void fatalErrorReadAttachedData(void) { fatalError("Error, couldn't read attached data."); }

static void fatalErrorMemory(void) { fatalError("Error, couldn't allocate memory."); }

// TODO: Make use of this on other platforms as well.
#if defined(_WIN32)
static void fatalErrorChild(void) { fatalError("Error, couldn't launch child."); }
#endif

#if defined(_WIN32)
static void appendWCharSafeW(wchar_t *target, wchar_t c, size_t buffer_size) {
    while (*target != 0) {
        target++;
        buffer_size -= 1;
    }

    if (buffer_size < 1) {
        abort();
    }

    *target++ = c;
    *target = 0;
}
#endif

// Have a type for filename type different on Linux and Win32.
#if defined(_WIN32)
#define filename_char_t wchar_t
#define FILENAME_SEP_STR L"\\"
#define FILENAME_SEP_CHAR L'\\'
#define FILENAME_FORMAT_STR "%ls"
#define appendStringSafeFilename appendWStringSafeW
#define appendCharSafeFilename appendWCharSafeW
#define FILENAME_TMP_STR L".tmp"
#else
#define filename_char_t char
#define FILENAME_SEP_STR "/"
#define FILENAME_SEP_CHAR '/'
#define FILENAME_FORMAT_STR "%s"
#define appendStringSafeFilename appendStringSafe
#define appendCharSafeFilename appendCharSafe
#define FILENAME_TMP_STR ".tmp"
#endif

static void fatalErrorTempFileCreate(filename_char_t const *filename) {
    fprintf(stderr, "Error, failed to open '" FILENAME_FORMAT_STR "' for writing.\n", filename);
    exit(2);
}

static void fatalErrorSpec(filename_char_t const *spec) {
    fprintf(stderr, "Error, couldn't runtime expand spec '" FILENAME_FORMAT_STR "'.\n", spec);
    abort();
}

// Have a type for file type different on Linux and Win32.
#if defined(_WIN32)
#define FILE_HANDLE HANDLE
#define FILE_HANDLE_NULL INVALID_HANDLE_VALUE
#else
#define FILE_HANDLE FILE *
#define FILE_HANDLE_NULL NULL
#endif

static FILE_HANDLE createFileForWriting(filename_char_t const *filename) {
#if defined(_WIN32)
    FILE_HANDLE result = CreateFileW(filename, GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, 0, NULL);
    if (result == INVALID_HANDLE_VALUE) {
        fatalErrorTempFileCreate(filename);
    }
#else
    FILE *result = fopen(filename, "wb");

    if (result == NULL) {
        fatalErrorTempFileCreate(filename);
    }
#endif

    return result;
}

static void writeToFile(FILE_HANDLE target_file, void *chunk, size_t chunk_size) {
#if defined(_WIN32)
    BOOL bool_res = WriteFile(target_file, chunk, (DWORD)chunk_size, NULL, NULL);
    if (bool_res == false) {
        fatalErrorTempFiles();
    }
#else
    size_t written = fwrite(chunk, 1, chunk_size, target_file);

    if (written != chunk_size) {
        fatalErrorTempFiles();
    }
#endif
}

static void closeFile(FILE_HANDLE target_file) {
#if defined(_WIN32)
    CloseHandle(target_file);
#else
    int r = fclose(target_file);

    if (r != 0) {
        fatalErrorTempFiles();
    }
#endif
}

#if _NUITKA_ONEFILE_AUTO_UPDATE == 1
static void replaceFile(filename_char_t const *dest, filename_char_t const *source) {

#if defined(_WIN32)
    filename_char_t tmp_dest[4096] = {0};
    appendStringSafeFilename(tmp_dest, dest, sizeof(tmp_dest) / sizeof(filename_char_t));
    appendStringSafeFilename(tmp_dest, FILENAME_TMP_STR, sizeof(tmp_dest) / sizeof(filename_char_t));

    DeleteFileW(tmp_dest);
    _wrename(dest, tmp_dest);
    DeleteFileW(dest);
    _wrename(source, dest);
#else
    rename(source, dest);
#endif
}
#endif

static int getMyPid(void) {
#if defined(_WIN32)
    return GetCurrentProcessId();
#else
    return getpid();
#endif
}

static void setEnvironVar(char const *var_name, char const *value) {
#if defined(_WIN32)
    SetEnvironmentVariable("NUITKA_ONEFILE_PARENT", value);
#else
    setenv(var_name, value, 1);
#endif
}

// Note: Made payload file handle global until we properly abstracted compression.
static FILE_HANDLE exe_file;

#if _NUITKA_ONEFILE_AUTO_UPDATE == 1
static bool exe_file_updatable = false;
#endif

#if _NUITKA_ONEFILE_COMPRESSION == 1

static ZSTD_DCtx *dest_ctx = NULL;
static ZSTD_inBuffer input = {NULL, 0, 0};
static ZSTD_outBuffer output = {NULL, 0, 0};

static void initZSTD(void) {
    size_t const input_buffer_size = ZSTD_DStreamInSize();
    input.src = malloc(input_buffer_size);
    if (input.src == NULL) {
        fatalErrorMemory();
    }

    size_t const output_buffer_size = ZSTD_DStreamOutSize();
    output.dst = malloc(output_buffer_size);
    if (output.dst == NULL) {
        fatalErrorMemory();
    }

    dest_ctx = ZSTD_createDCtx();
    if (dest_ctx == NULL) {
        fatalErrorMemory();
    }
}

static void releaseZSTD(void) {
    ZSTD_freeDCtx(dest_ctx);

    free((void *)input.src);
    free(output.dst);
}

#endif

static size_t stream_end_pos;

static size_t getPosition(void) {
#if defined(_WIN32)
    return SetFilePointer(exe_file, 0, NULL, FILE_CURRENT);
#else
    return ftell(exe_file);
#endif
}

static void readChunk(void *buffer, size_t size) {
    // printf("Reading %d\n", size);

#if defined(_WIN32)
    DWORD read_size;
    BOOL bool_res = ReadFile(exe_file, buffer, (DWORD)size, &read_size, NULL);

    if (bool_res == false || read_size != size) {
        fatalErrorReadAttachedData();
    }
#else
    size_t read_size = fread(buffer, 1, size, exe_file);

    if (read_size != size) {
        fatalErrorReadAttachedData();
    }

#endif
}

static unsigned long long readSizeValue(void) {
    unsigned long long result;
    readChunk(&result, sizeof(unsigned long long));

    return result;
}

static void readPayloadChunk(void *buffer, size_t size) {
#if _NUITKA_ONEFILE_COMPRESSION == 1

    // bool no_payload = false;
    bool end_of_buffer = false;

    // Loop until finished with asked chunk.
    while (size > 0) {
        size_t available = output.size - output.pos;

        // printf("already available %d asking for %d\n", available, size);

        // Consider available data.
        if (available != 0) {
            size_t use = available;
            if (size < use) {
                use = size;
            }

            memcpy(buffer, ((char *)output.dst) + output.pos, use);
            buffer = (void *)(((char *)buffer) + use);
            size -= use;

            output.pos += use;

            // Loop end check may exist when "size" is "use".
            continue;
        }

        // Nothing available, make sure to make it available from existing input.
        if (input.pos < input.size || end_of_buffer) {
            output.pos = 0;
            output.size = ZSTD_DStreamOutSize();

            size_t const ret = ZSTD_decompressStream(dest_ctx, &output, &input);
            // printf("return output %d %d\n", output.pos, output.size);
            end_of_buffer = (output.pos == output.size);

            if (ZSTD_isError(ret)) {
                fatalErrorAttachedData();
            }

            output.size = output.pos;
            output.pos = 0;

            // printf("made output %d %d\n", output.pos, output.size);

            // Above code gets a turn.
            continue;
        }

        if (input.size != input.pos) {
            fatalErrorAttachedData();
        }

        // No input available, make it available from stream respecting end.
        size_t to_read = ZSTD_DStreamInSize();
        size_t payload_available = stream_end_pos - getPosition();

        static size_t payload_so_far = 0;

        if (payload_available == 0) {
            continue;
        }

        if (to_read > payload_available) {
            to_read = payload_available;
        }

        readChunk((void *)input.src, to_read);
        input.pos = 0;
        input.size = to_read;

        payload_so_far += to_read;
    }

#else
    readChunk(buffer, size);
#endif
}

#if _NUITKA_ONEFILE_TEMP == 0
static uint32_t readPayloadChecksumValue(void) {
    unsigned int result;
    readPayloadChunk(&result, sizeof(unsigned int));

    return (uint32_t)result;
}
#endif

static unsigned char readPayloadFileFlagsValue(void) {
    unsigned char result;
    readPayloadChunk(&result, 1);

    return result;
}

static unsigned long long readPayloadSizeValue(void) {
    unsigned long long result;
    readPayloadChunk(&result, sizeof(unsigned long long));

    return result;
}

static filename_char_t readPayloadFilenameCharacter(void) {
    filename_char_t result;

    readPayloadChunk(&result, sizeof(filename_char_t));

    return result;
}

static filename_char_t *readPayloadFilename(void) {
    static filename_char_t buffer[1024];

    filename_char_t *w = buffer;

    for (;;) {
        *w = readPayloadFilenameCharacter();

        if (*w == 0) {
            break;
        }

        w += 1;
    }

    return buffer;
}

// Zero means, not yet created, created unsuccessfully, terminated already.
#if defined(_WIN32)
HANDLE handle_process = 0;
#else
pid_t handle_process = 0;
#endif

static filename_char_t payload_path[4096] = {0};

static bool payload_created = false;

bool createDirectory(filename_char_t *path) {
#if defined(_WIN32)
    BOOL bool_res = CreateDirectoryW(path, NULL);
    return bool_res;
#else
    return mkdir(path, 0700) == 0;
#endif
}

#if defined(_WIN32)
void removeDirectory(wchar_t const *path) {
    SHFILEOPSTRUCTW file_op_struct = {
        NULL, FO_DELETE, payload_path, L"", FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT, false, 0, L""};
    SHFileOperationW(&file_op_struct);
}
#else
int removeDirectory(char const *path) {
    DIR *d = opendir(path);
    size_t path_len = strlen(path);

    int r = -1;

    if (d != NULL) {
        struct dirent *p;

        r = 0;
        while (!r && (p = readdir(d))) {
            int r2 = -1;

            size_t len;

            // Ignore special names
            if (!strcmp(p->d_name, ".") || !strcmp(p->d_name, "..")) {
                continue;
            }

            len = path_len + strlen(p->d_name) + 2;
            char *buf = (char *)malloc(len);

            if (buf == NULL) {
                fatalErrorMemory();
            }

            struct stat statbuf;

            snprintf(buf, len, "%s/%s", path, p->d_name);

            if (!stat(buf, &statbuf)) {
                if (S_ISDIR(statbuf.st_mode))
                    r2 = removeDirectory(buf);
                else
                    r2 = unlink(buf);
            }
            free(buf);
            r = r2;
        }
        closedir(d);
    }

    if (!r) {
        rmdir(path);
    }

    return r;
}
#endif

#if !defined(_WIN32)
static int waitpid_retried(pid_t pid, int *status) {
    int res;

    for (;;) {
        *status = 0;
        res = waitpid(pid, status, 0);

        if ((res == -1) && (errno == EINTR)) {
            continue;
        }

        break;
    }

    return res;
}
#endif

#if _NUITKA_ONEFILE_AUTO_UPDATE == 1
#if defined(_WIN32)
static filename_char_t *downloadFileSyncW(filename_char_t const *url) {
    static filename_char_t output_filename[4096];

    HRESULT res = URLDownloadToCacheFileW(NULL, // lpUnkcaller
                                          url,  // szURL
                                          // TODO: Needs to unique by using PID probably.
                                          output_filename,                                   // cached filename
                                          sizeof(output_filename) / sizeof(filename_char_t), // filename size
                                          0, NULL);

    if (res == S_OK) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
        fprintf(stderr, "AUTO UPDATE: Download OK.\n");
#endif
        return output_filename;
    } else {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
        fprintf(stderr, "AUTO UPDATE: Download error.\n");
#endif
        return NULL;
    }
}
#endif

static filename_char_t *downloadFileSync(char const *url) {
#if defined(_WIN32)
    static filename_char_t url_wide[4096] = {0};
    appendStringSafeW(url_wide, url, sizeof(url_wide) / sizeof(filename_char_t));

    return downloadFileSyncW(url_wide);
#else
    return NULL;
#endif
}

// Return buffer with contents.
static char *downloadTextContentsSync(filename_char_t const *url) {
    char *result = NULL;

#if defined(_WIN32)
    filename_char_t const *downloaded_filename = downloadFileSyncW(url);

    if (downloaded_filename != NULL) {
        FILE_HANDLE file_handle =
            CreateFileW(downloaded_filename, GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

        // Error is surprising though, but could be a race.
        if (file_handle == NULL) {
            return NULL;
        }

        DWORD file_size = GetFileSize(file_handle, NULL);

        result = (char *)malloc(file_size + 1);

        DWORD read_size;
        BOOL bool_res = ReadFile(file_handle, result, file_size, &read_size, NULL);

        CloseHandle(file_handle);

        if (bool_res == false || read_size != file_size) {
            free(result);
            result = NULL;
        }

        return result;
    }
#else
    char const *downloaded_filename = downloadFileSync(url);

    if (downloaded_filename != NULL) {
        FILE_HANDLE file_handle = fopen(downloaded_filename, "rb");

        if (file_handle != NULL) {
            int res = fseek(file_handle, 0, SEEK_END);

            if (res == 0) {
                int file_size = ftell(file_handle);

                result = (char *)malloc(file_size + 1);

                if (fread(result, 1, file_size, file_handle) != file_size) {
                    free(result);
                    result = NULL;
                }
            }

            fclose(file_handle);
        }
    }
#endif

    return NULL;
}
#endif

static void cleanupChildProcess(void) {

    // Cause KeyboardInterrupt in the child process.
    if (handle_process != 0) {
        NUITKA_PRINT_TRACE("Sending CTRL-C to child\n");

#if defined(_WIN32)
        BOOL res = GenerateConsoleCtrlEvent(CTRL_C_EVENT, GetProcessId(handle_process));

        if (res == false) {
            printError("Failed to send CTRL-C to child process.");
            // No error exit is done, we still want to cleanup when it does exit
        }
#else
        kill(handle_process, SIGINT);
#endif
        // TODO: We ought to only need to wait if there is a need to cleanup
        // files when we are on Windows, on Linux maybe exec can be used to
        // this process to exist anymore.
#if _NUITKA_ONEFILE_TEMP == 1 || 1
        NUITKA_PRINT_TRACE("Waiting for child to exit.\n");
#if defined(_WIN32)
        WaitForSingleObject(handle_process, INFINITE);
        CloseHandle(handle_process);
#else
        int status;
        waitpid_retried(handle_process, &status);
#endif
        NUITKA_PRINT_TRACE("Child is exited.\n");
#endif
    }

#if _NUITKA_ONEFILE_TEMP == 1
    if (payload_created) {
        removeDirectory(payload_path);
    }
#endif
}

#if defined(_WIN32)
static char *convertUnicodePathToAnsi(wchar_t const *path) {
    // first get short path as otherwise, conversion might not be reliable
    DWORD l = GetShortPathNameW(path, NULL, 0);
    wchar_t *short_path = (wchar_t *)malloc(sizeof(wchar_t) * (l + 1));
    if (short_path == NULL) {
        fatalErrorMemory();
    }

    l = GetShortPathNameW(path, short_path, l);
    if (unlikely(l == 0)) {
        goto err_short_path;
    }

    size_t i;
    if (unlikely(wcstombs_s(&i, NULL, 0, short_path, _TRUNCATE) != 0)) {
        goto err_short_path;
    }
    char *ansi_path = (char *)malloc(i);
    if (ansi_path == NULL) {
        fatalErrorMemory();
    }
    if (unlikely(wcstombs_s(&i, ansi_path, i, short_path, _TRUNCATE) != 0)) {
        goto err_ansi_path;
    }

    free(short_path);

    return ansi_path;

err_ansi_path:
    free(ansi_path);
err_short_path:
    free(short_path);
    return NULL;
}
#endif

#if defined(_WIN32)
BOOL WINAPI ourConsoleCtrlHandler(DWORD fdwCtrlType) {
    switch (fdwCtrlType) {
        // Handle the CTRL-C signal.
    case CTRL_C_EVENT:
        NUITKA_PRINT_TRACE("Ctrl-C event");
        cleanupChildProcess();
        return FALSE;

        // CTRL-CLOSE: confirm that the user wants to exit.
    case CTRL_CLOSE_EVENT:
        NUITKA_PRINT_TRACE("Ctrl-Close event");
        cleanupChildProcess();
        return FALSE;

        // Pass other signals to the next handler.
    case CTRL_BREAK_EVENT:
        NUITKA_PRINT_TRACE("Ctrl-Break event");
        cleanupChildProcess();
        return FALSE;

    case CTRL_LOGOFF_EVENT:
        NUITKA_PRINT_TRACE("Ctrl-Logoff event");
        cleanupChildProcess();
        return FALSE;

    case CTRL_SHUTDOWN_EVENT:
        NUITKA_PRINT_TRACE("Ctrl-Shutdown event");
        cleanupChildProcess();
        return FALSE;

    default:
        return FALSE;
    }
}

#else
void ourConsoleCtrlHandler(int sig) { cleanupChildProcess(); }
#endif

#ifndef MAXPATHLEN
#define MAXPATHLEN 4096
#endif

#if defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/sysctl.h>
#endif

filename_char_t *getBinaryPath(void) {
    static filename_char_t binary_filename[MAXPATHLEN];

#if defined(_WIN32)
    DWORD res = GetModuleFileNameW(NULL, binary_filename, sizeof(binary_filename) / sizeof(wchar_t));
    if (res == 0) {
        fatalError("Error, failed to locate onefile filename.");
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

#if _NUITKA_ONEFILE_SPLASH_SCREEN
#include "OnefileSplashScreen.cpp"
#endif

#if _NUITKA_ONEFILE_TEMP == 0
static uint32_t _calcCRC32(uint32_t crc, unsigned char const *message, long size) {

    for (uint32_t i = 0; i < size; i++) {
        unsigned int c = message[i];
        crc = crc ^ c;

        for (int j = 7; j >= 0; j--) {
            uint32_t mask = ((crc & 1) != 0) ? 0xFFFFFFFF : 0;
            crc = (crc >> 1) ^ (0xEDB88320 & mask);
        }
    }

    return crc;
}

#if defined(_WIN32)
static uint32_t calcCRC32(unsigned char const *message, long size) {
    uint32_t crc = _calcCRC32(0xFFFFFFFF, message, size);

    return ~crc;
}
#endif

#if !defined(_WIN32)
#include <fcntl.h>
#include <sys/mman.h>
#endif

static uint32_t getFileChecksum(filename_char_t const *filename) {
#if defined(_WIN32)
    FILE_HANDLE file_handle = CreateFileW(filename, GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

    if (file_handle == NULL) {
        return 0;
    }

    // TODO: File size is truncated here, but maybe a good thing.
    DWORD file_size = GetFileSize(file_handle, NULL);

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

    static unsigned char chunk[32768];

    uint32_t crc32 = 0xFFFFFFFF;

    while (file_size > 0) {
        ssize_t read_bytes = (ssize_t)read(file_handle, chunk, sizeof(chunk));

        if (read_bytes < 0) {
            close(file_handle);
            return 0;
        }

        // crc32 = _calcCRC32(crc32, chunk, read_bytes);

        file_size -= read_bytes;
    }

    crc32 = ~crc32;
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
#endif

#if _NUITKA_ONEFILE_AUTO_UPDATE == 1

#include <ctype.h>

static char *trimWhitespace(char *str) {

    // Trim leading space
    while (isspace((unsigned char)*str)) {
        str++;
    }

    if (*str == 0) {
        return str;
    }

    // Trim trailing space
    char *end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) {
        end--;
    }

    // Write new null terminator character
    end[1] = 0;

    return str;
}

static char *getAutoUpdateUrl(void) {

    filename_char_t download_url[4096];
#if defined(_WIN32)
    wchar_t const *url_pattern = L"" _NUITKA_ONEFILE_AUTO_UPDATE_URL_SPEC;
    bool bool_res = expandTemplatePathW(download_url, url_pattern, sizeof(download_url) / sizeof(wchar_t));
#else
    char const *url_pattern = "" _NUITKA_ONEFILE_AUTO_UPDATE_URL_SPEC;
    bool bool_res = expandTemplatePath(download_url, url_pattern, sizeof(download_url));
#endif

    if (unlikely(bool_res == false)) {
        fatalErrorSpec(url_pattern);
    }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
    fprintf(stderr, "AUTO UPDATE: Expanded info URL to '" FILENAME_FORMAT_STR "'.\n", download_url);
#endif

    char *download_info = downloadTextContentsSync(download_url);

    if (download_info != NULL) {
        char *download_line = strtok(download_info, "\n");

        while (download_line != NULL) {
            download_line = trimWhitespace(download_line);

            char *sep = strchr(download_line, '=');

            if (sep != NULL) {
                *sep = 0;

                char *key = trimWhitespace(download_line);

                if (strcmp(key, "url") == 0) {
                    char *value = trimWhitespace(sep + 1);

                    if (strlen(value) == 0) {
                        return NULL;
                    }

                    return value;
                }
            }

            download_line = strtok(NULL, "\n");
        }
    }

    return NULL;
}

static void _checkAutoUpdates(void) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
    fprintf(stderr, "AUTO UPDATE: Thread started.\n");
#endif

    char const *update_url = getAutoUpdateUrl();

    if (update_url != NULL) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
        fprintf(stderr, "AUTO UPDATE: URL to check '%s'.\n", update_url);
#endif
        if ((strncmp(update_url, "https://", strlen("https://")) == 0) ||
            (strncmp(update_url, "http://", strlen("http://")) == 0)) {

            filename_char_t *downloaded_binary = downloadFileSync(update_url);

            if (downloaded_binary != NULL) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
                fprintf(stderr, "AUTO UPDATE: Downloaded to '" FILENAME_FORMAT_STR "' .\n", downloaded_binary);
#endif
                while (exe_file_updatable == false) {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
                    fprintf(stderr, "AUTO UPDATE: May not yet update.\n");
#endif
                    // Wait for executable to become replaceable.
#if defined(_WIN32)
                    Sleep(1000);
#else
                    sleep(1);
#endif
                }

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_AUTO_UPDATE
                fprintf(stderr, "AUTO UPDATE: May update.\n");
#endif
                replaceFile(getBinaryPath(), downloaded_binary);
            }
        }
    }
}

#if defined(_WIN32)
DWORD WINAPI doAutoUpdateThread(LPVOID lpParam) {
    _checkAutoUpdates();
    return 0;
}
#else
#include <pthread.h>

void *doAutoUpdateThread(void *ptr) {
    _checkAutoUpdates();
    return NULL;
}

pthread_t auto_update_thread;

#endif

static void checkAutoUpdates(void) {
#if defined(_WIN32)
    CreateThread(NULL, 0, doAutoUpdateThread, NULL, 0, NULL);
#else
    pthread_create(&auto_update_thread, NULL, doAutoUpdateThread, NULL);
#endif
}

#endif

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, wchar_t *lpCmdLine, int nCmdShow) {
    int argc = __argc;
    wchar_t **argv = __wargv;
#else
#if defined(_WIN32)
int wmain(int argc, wchar_t **argv) {
#else
int main(int argc, char **argv) {
#endif
#endif
    NUITKA_PRINT_TIMING("ONEFILE: Entered main().");

#if defined(_WIN32)
    wchar_t const *pattern = L"" _NUITKA_ONEFILE_TEMP_SPEC;
    BOOL bool_res = expandTemplatePathW(payload_path, pattern, sizeof(payload_path) / sizeof(wchar_t));

    if (unlikely(bool_res == false)) {
        fatalErrorSpec(pattern);
    }

#else
    char const *pattern = "" _NUITKA_ONEFILE_TEMP_SPEC;
    bool bool_res = expandTemplatePath(payload_path, pattern, sizeof(payload_path));

    if (unlikely(bool_res == false)) {
        fatalErrorSpec(pattern);
    }

#endif

#if defined(_WIN32)
    bool_res = SetConsoleCtrlHandler(ourConsoleCtrlHandler, true);
    if (bool_res == false) {
        printError("Error, failed to register signal handler.");
        return 1;
    }
#else
    signal(SIGINT, ourConsoleCtrlHandler);
#endif

#if _NUITKA_ONEFILE_AUTO_UPDATE == 1
    NUITKA_PRINT_TIMING("ONEFILE: Checking for auto update.");

    checkAutoUpdates();
#endif

    NUITKA_PRINT_TIMING("ONEFILE: Unpacking payload.");

    createDirectory(payload_path);
    payload_created = true;

#if defined(_WIN32)
    exe_file = CreateFileW(getBinaryPath(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (exe_file == INVALID_HANDLE_VALUE) {
        printError("Error, failed to access unpacked executable.");
        return 1;
    }
#else
    exe_file = fopen(getBinaryPath(), "rb");
#endif

#if defined(_WIN32)
    /* if an application is signed, the signature is at the end of the file
       where we normally expect the start position of out container.
       the overcome this limitation, use the windows function MapAndLoad()
       to parse the PE header. The header contains information whether
       a signature is present and at which address the first signature
       start. so we can use that address to find the start position value */
    DWORD cert_table_addr = 0;

    char *exe_filename_a = convertUnicodePathToAnsi(getBinaryPath());
    if (exe_filename_a) {
        LOADED_IMAGE loaded_image;
        if (MapAndLoad(exe_filename_a, "\\dont-search-path", &loaded_image, false, true)) {
            if (loaded_image.FileHeader) {
                if (loaded_image.FileHeader->OptionalHeader.NumberOfRvaAndSizes > IMAGE_DIRECTORY_ENTRY_SECURITY) {
                    cert_table_addr =
                        loaded_image.FileHeader->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_SECURITY]
                            .VirtualAddress;
                    // printf("Certificate Table at: %d\n", cert_table_addr);
                }
            }
            UnMapAndLoad(&loaded_image);
        }
        free(exe_filename_a);
    }

    DWORD res;

    if (cert_table_addr == 0) {
        res = SetFilePointer(exe_file, -8, NULL, FILE_END);
    } else {
        res = SetFilePointer(exe_file, cert_table_addr - 8, NULL, FILE_BEGIN);
    }

    if (res == INVALID_SET_FILE_POINTER) {
        fatalErrorFindAttachedData();
    }
#else
    int res = fseek(exe_file, -8, SEEK_END);
    if (res != 0) {
        fatalErrorFindAttachedData();
    }
#endif
    stream_end_pos = getPosition();

    unsigned long long payload_size = readSizeValue();
    unsigned long long start_pos = stream_end_pos - payload_size;

    // printf("Payload size at %lld\n", payload_size);
    // printf("Start at %lld\n", start_pos);
    // printf("Start at %ld\n", (LONG)start_pos);

    // The start offset won't exceed LONG.
#if defined(_WIN32)
    res = SetFilePointer(exe_file, (LONG)start_pos, NULL, FILE_BEGIN);
    if (res == INVALID_SET_FILE_POINTER) {
        fatalErrorFindAttachedData();
    }
#else
    res = fseek(exe_file, start_pos, SEEK_SET);
    if (res != 0) {
        fatalErrorFindAttachedData();
    }
#endif

    char header[3];
    readChunk(&header, sizeof(header));

    if (header[0] != 'K' || header[1] != 'A') {
        fatalErrorFindAttachedData();
    }

// The 'X' stands for no compression, 'Y' is compressed, handle that.
#if _NUITKA_ONEFILE_COMPRESSION == 1
    if (header[2] != 'Y') {
        fatalErrorFindAttachedData();
    }
    initZSTD();
#else
    if (header[2] != 'X') {
        fatalErrorFindAttachedData();
    }
#endif

    static filename_char_t first_filename[1024] = {0};

#if _NUITKA_ONEFILE_SPLASH_SCREEN
    initSplashScreen();
#endif

    // printf("Entering decompression loop:");

    for (;;) {
        filename_char_t *filename = readPayloadFilename();

        // printf("Filename: %s\n", filename);

        // Detect EOF from empty filename.
        if (filename[0] == 0) {
            break;
        }

        // puts("at:");
        // _putws(filename);

        static filename_char_t target_path[4096] = {0};
        target_path[0] = 0;

        filename_char_t *w = filename;

        while (*w) {
            if (*w == FILENAME_SEP_CHAR) {
                *w = 0;

                target_path[0] = 0;
                appendStringSafeFilename(target_path, payload_path, sizeof(target_path) / sizeof(filename_char_t));
                appendCharSafeFilename(target_path, FILENAME_SEP_CHAR, sizeof(target_path) / sizeof(filename_char_t));
                appendStringSafeFilename(target_path, filename, sizeof(target_path) / sizeof(filename_char_t));

                *w = FILENAME_SEP_CHAR;

                createDirectory(target_path);
            }

            w++;
        }

        target_path[0] = 0;
        appendStringSafeFilename(target_path, payload_path, sizeof(target_path) / sizeof(filename_char_t));
        appendCharSafeFilename(target_path, FILENAME_SEP_CHAR, sizeof(target_path) / sizeof(filename_char_t));
        appendStringSafeFilename(target_path, filename, sizeof(target_path) / sizeof(filename_char_t));

        if (first_filename[0] == 0) {
            appendStringSafeFilename(first_filename, target_path, sizeof(target_path) / sizeof(filename_char_t));
        }

        // _putws(target_path);
        unsigned long long file_size = readPayloadSizeValue();
        unsigned char file_flags = readPayloadFileFlagsValue();

        bool needs_write = true;

#if _NUITKA_ONEFILE_TEMP == 0
        uint32_t contained_file_checksum = readPayloadChecksumValue();
        uint32_t existing_file_checksum = getFileChecksum(target_path);

        if (contained_file_checksum == existing_file_checksum) {
            needs_write = false;

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
            printf(stderr, "CACHE HIT for '" FILENAME_FORMAT_STR "'.", target_path);
#endif
        } else {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
            printf(stderr, "CACHE HIT for '" FILENAME_FORMAT_STR "'.", target_path);
#endif
        }
#endif

        FILE_HANDLE target_file = FILE_HANDLE_NULL;

        if (needs_write) {
            target_file = createFileForWriting(target_path);
        }

        while (file_size > 0) {
            static char chunk[32768];

            long chunk_size;

            // Doing min manually, as otherwise the compiler is confused from types.
            if (file_size <= sizeof(chunk)) {
                chunk_size = (long)file_size;
            } else {
                chunk_size = sizeof(chunk);
            }

            // TODO: Does zstd support skipping data as well, such that we
            // do not have to fully decode.
            readPayloadChunk(chunk, chunk_size);

            if (target_file != FILE_HANDLE_NULL) {
                writeToFile(target_file, chunk, chunk_size);
            }

            file_size -= chunk_size;
        }

        if (file_size != 0) {
            fatalErrorReadAttachedData();
        }

#if !defined(_WIN32)
        if ((file_flags & 1) && (target_file != FILE_HANDLE_NULL)) {
            int fd = fileno(target_file);

            struct stat stat_buffer;
            int res = fstat(fd, &stat_buffer);

            if (res == -1) {
                printError("fstat");
            }

            // User shall be able to execute if at least.
            stat_buffer.st_mode |= S_IXUSR;

            // Follow read flags for group, others according to umask.
            if ((stat_buffer.st_mode & S_IRGRP) != 0) {
                stat_buffer.st_mode |= S_IXOTH;
            }

            if ((stat_buffer.st_mode & S_IRGRP) != 0) {
                stat_buffer.st_mode |= S_IXOTH;
            }

            res = fchmod(fd, stat_buffer.st_mode);

            if (res == -1) {
                printError("fchmod");
            }
        }
#endif

        if (target_file != FILE_HANDLE_NULL) {
            closeFile(target_file);
        }
    }

    closeFile(exe_file);

#if _NUITKA_ONEFILE_AUTO_UPDATE == 1
    exe_file_updatable = true;
#endif

#if _NUITKA_ONEFILE_COMPRESSION == 1
    releaseZSTD();
#endif

    // Pass our pid by value to the child. If we exit for some reason, re-parenting
    // might change it by the time the child looks at its parent.
    {
        char buffer[128];
        snprintf(buffer, sizeof(buffer), "%d", getMyPid());
        setEnvironVar("NUITKA_ONEFILE_PARENT", buffer);
    }

    NUITKA_PRINT_TIMING("ONEFILE: Preparing forking of slave process.");

#if defined(_WIN32)

    STARTUPINFOW si;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);

    PROCESS_INFORMATION pi;

    bool_res = CreateProcessW(first_filename,        // application name
                              GetCommandLineW(),     // command line
                              NULL,                  // process attributes
                              NULL,                  // thread attributes
                              FALSE,                 // inherit handles
                              NORMAL_PRIORITY_CLASS, // creation flags
                              NULL, NULL, &si, &pi);

    NUITKA_PRINT_TIMING("ONEFILE: Started slave process.");

    if (bool_res == false) {
        fatalErrorChild();
    }

    CloseHandle(pi.hThread);
    handle_process = pi.hProcess;

    DWORD exit_code = 0;

#if _NUITKA_ONEFILE_SPLASH_SCREEN
    DWORD wait_time = 50;
#else
    DWORD wait_time = INFINITE;
#endif

    // Loop with splash screen, otherwise this will be only once.
    while (handle_process != 0) {
        WaitForSingleObject(handle_process, wait_time);

        if (!GetExitCodeProcess(handle_process, &exit_code)) {
            exit_code = 1;
        }

#if _NUITKA_ONEFILE_SPLASH_SCREEN
        if (exit_code == STILL_ACTIVE) {
            bool done = checkSplashScreen();

            // Stop checking splash screen, can increase timeout.
            if (done) {
                wait_time = INFINITE;
            }

            continue;
        }
#endif
        CloseHandle(handle_process);

        handle_process = 0;
    }

    cleanupChildProcess();
#else
    int exit_code;

    pid_t pid = fork();

    if (pid < 0) {
        printError("fork");
        exit_code = 2;
    } else if (pid == 0) {
        execv(first_filename, argv);

        printError("exec failed");
        exit_code = 2;
    } else {
        handle_process = pid;
        int status;
        int res = waitpid_retried(handle_process, &status);

        if (res == -1 && errno != ECHILD) {
            printError("waitpid");
            cleanupChildProcess();
            exit_code = 2;
        } else {
            exit_code = WEXITSTATUS(status);
            cleanupChildProcess();
        }
    }

#endif

    NUITKA_PRINT_TIMING("ONEFILE: Exiting.");

    return exit_code;
}
