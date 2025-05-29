//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* The main program for onefile bootstrap.
 *
 * It needs to unpack the attached files and and then loads and executes
 * the compiled program as a separate process.
 *
 * spell-checker: ignore _wrename,SHFILEOPSTRUCTW,FOF_NOCONFIRMATION,FOF_NOERRORUI
 * spell-checker: ignore HRESULT,HINSTANCE,lpUnkcaller,MAKELANGID,SUBLANG
 *
 */

#define _CRT_SECURE_NO_WARNINGS

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#endif

#ifdef __NUITKA_NO_ASSERT__
#undef NDEBUG
#define NDEBUG
#endif

#if defined(_WIN32)
// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>

// Other windows header files.
#include <psapi.h>

#endif

#include <assert.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wchar.h>

/* Type bool */
#ifndef __cplusplus
#include <stdbool.h>
#endif

#if !defined(_WIN32)
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
#define _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
#define _NUITKA_ONEFILE_TEMP_BOOL 0
#define _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT 5000
#define _NUITKA_ONEFILE_TEMP_SPEC "{TEMP}/onefile_{PID}_{TIME}"

#define _NUITKA_AUTO_UPDATE_BOOL 1
#define _NUITKA_AUTO_UPDATE_DEBUG_BOOL 1
#define _NUITKA_AUTO_UPDATE_URL_SPEC "https://..."

#define _NUITKA_ATTACH_CONSOLE_WINDOW 1
#endif

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
// Header of zstd goes first, spellchecker: ignore ZSTDERRORLIB,ZSTDLIB
#define ZSTDERRORLIB_VISIBILITY
#define ZSTDLIB_VISIBILITY
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

// Some handy macro definitions, e.g. unlikely and NUITKA_MAY_BE_UNUSED
#include "nuitka/hedley.h"
#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)
#ifdef __GNUC__
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

#include "HelpersChecksumTools.c"
#include "HelpersEnvironmentVariablesSystem.c"
#include "HelpersFilesystemPaths.c"
#include "HelpersSafeStrings.c"

#if defined(_WIN32) && (defined(_NUITKA_ATTACH_CONSOLE_WINDOW) || defined(_NUITKA_HIDE_CONSOLE_WINDOW))
#include "HelpersConsole.c"
#endif

// For tracing outputs if enabled at compile time.
#include "nuitka/tracing.h"

static void fatalError(char const *message) {
    puts(message);
    exit(2);
}

static void fatalIOError(char const *message, error_code_t error_code) {
    printOSErrorMessage(message, error_code);
    exit(2);
}

// Failure to expand the template for where to extract to.
static void fatalErrorTempFiles(void) {
    fatalIOError("Error, couldn't unpack file to target path.", getLastErrorCode());
}

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
static void fatalErrorAttachedData(void) { fatalError("Error, couldn't decode attached data."); }
#endif

static void fatalErrorHeaderAttachedData(void) { fatalError("Error, couldn't find attached data header."); }

// Out of memory error.
#if !defined(_WIN32) || _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
static void fatalErrorMemory(void) { fatalError("Error, couldn't allocate memory."); }
#endif

// Could not launch child process.
static void fatalErrorChild(char const *message, error_code_t error_code) { fatalIOError(message, error_code); }

static void fatalErrorTempFileCreate(filename_char_t const *filename) {
    fprintf(stderr, "Error, failed to open '" FILENAME_FORMAT_STR "' for writing.\n", filename);
    exit(2);
}

static void fatalErrorSpec(filename_char_t const *spec) {
    fprintf(stderr, "Error, couldn't runtime expand spec '" FILENAME_FORMAT_STR "'.\n", spec);
    abort();
}

static FILE_HANDLE createFileForWritingChecked(filename_char_t const *filename) {
    FILE_HANDLE result = createFileForWriting(filename);

    if (result == FILE_HANDLE_NULL) {
        fatalErrorTempFileCreate(filename);
    }

    return result;
}

static unsigned char const *payload_data = NULL;
static unsigned char const *payload_current = NULL;
static unsigned long long payload_size = 0;

#ifdef __APPLE__

#include <mach-o/getsect.h>
#include <mach-o/ldsyms.h>

static void initPayloadData2(void) {
    const struct mach_header *header = &_mh_execute_header;

    unsigned long section_size;

    payload_data = getsectiondata(header, "payload", "payload", &section_size);
    payload_current = payload_data;
    payload_size = section_size;
}

static void closePayloadData(void) {}

#elif defined(_WIN32)

static void initPayloadData2(void) {
    HRSRC windows_resource = FindResource(NULL, MAKEINTRESOURCE(27), RT_RCDATA);

    payload_data = (const unsigned char *)LockResource(LoadResource(NULL, windows_resource));
    payload_current = payload_data;

    payload_size = SizeofResource(NULL, windows_resource);
}

// Note: it appears unlocking the resource is not actually foreseen.
static void closePayloadData(void) {}

#else

static void fatalErrorFindAttachedData(char const *erroring_function, error_code_t error_code) {
    char buffer[1024] = "Error, couldn't find attached data:";
    appendStringSafe(buffer, erroring_function, sizeof(buffer));

    fatalIOError(buffer, error_code);
}

static struct MapFileToMemoryInfo exe_file_mapped;

static void initPayloadData2(void) {
    exe_file_mapped = mapFileToMemory(getBinaryPath());

    if (exe_file_mapped.error) {
        fatalErrorFindAttachedData(exe_file_mapped.erroring_function, exe_file_mapped.error_code);
    }

    payload_data = exe_file_mapped.data;
    payload_current = payload_data;
}

static void closePayloadData(void) { unmapFileFromMemory(&exe_file_mapped); }

#endif

static void initPayloadData(void) {
    initPayloadData2();

#if !defined(__APPLE__) && !defined(_WIN32)
    const off_t size_end_offset = exe_file_mapped.file_size;

    NUITKA_PRINT_TIMING("ONEFILE: Determining payload start position.");

    assert(sizeof(payload_size) == sizeof(unsigned long long));
    memcpy(&payload_size, payload_data + size_end_offset - sizeof(payload_size), sizeof(payload_size));

    unsigned long long start_pos = size_end_offset - sizeof(payload_size) - payload_size;

    payload_current += start_pos;
    payload_data += start_pos;
#endif
}

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1

static ZSTD_DCtx *dest_ctx = NULL;
static ZSTD_inBuffer input = {NULL, 0, 0};
static ZSTD_outBuffer output = {NULL, 0, 0};

static void initZSTD(void) {
    input.src = NULL;

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

    free(output.dst);
}

#endif

static void readChunk(void *buffer, size_t size) {
    // printf("Reading %d\n", size);

    memcpy(buffer, payload_current, size);
    payload_current += size;
}

static void readPayloadChunk(void *buffer, size_t size) {
#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1 && _NUITKA_ONEFILE_ARCHIVE_BOOL == 0
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
    }
#else
    readChunk(buffer, size);
#endif
}

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
static uint32_t readPayloadChecksumValue(void) {
    unsigned int result;
    readPayloadChunk(&result, sizeof(unsigned int));

    return (uint32_t)result;
}
#endif

#if !defined(_WIN32) && !defined(__MSYS__)
static unsigned char readPayloadFileFlagsValue(void) {
    unsigned char result;
    readPayloadChunk(&result, 1);

    return result;
}
#endif

static unsigned long long readPayloadSizeValue(void) {
    unsigned long long result;
    readPayloadChunk(&result, sizeof(unsigned long long));

    return result;
}

#if _NUITKA_ONEFILE_ARCHIVE_BOOL == 1 && _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
static unsigned long long readArchiveFileSizeValue(void) {
    unsigned long long result;
    readPayloadChunk(&result, sizeof(unsigned int));

    return result;
}
#endif

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

static void writeContainedFile(FILE_HANDLE target_file, unsigned long long file_size) {
#if _NUITKA_ONEFILE_ARCHIVE_BOOL == 1

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 0
    if (target_file != FILE_HANDLE_NULL) {
        if (writeFileChunk(target_file, payload_current, file_size) == false) {
            fatalErrorTempFiles();
        }
    }

    payload_current += file_size;
#else
    if (target_file != FILE_HANDLE_NULL) {

        // Nothing available, make sure to make it available from existing input.
        while (input.pos < input.size) {
            // printf("available input %ld %ld\n", input.pos, input.size);

            output.pos = 0;
            output.size = ZSTD_DStreamOutSize();

            size_t const ret = ZSTD_decompressStream(dest_ctx, &output, &input);
            if (ZSTD_isError(ret)) {
                fatalErrorAttachedData();
            }

            // printf("available output %ld %ld\n", output.pos, output.size);

            if (writeFileChunk(target_file, (char const *)output.dst, output.pos) == false) {
                fatalErrorTempFiles();
            }

            // printf("made output %ld %lld\n", output.pos, file_size);
            file_size -= output.pos;
            assert(file_size >= 0);
        }

        assert(file_size == 0);
    }
#endif
#else
    while (file_size > 0) {
        static char chunk[32768];

        long chunk_size;

        // Doing min manually, as otherwise the compiler is confused from types.
        if (file_size <= sizeof(chunk)) {
            chunk_size = (long)file_size;
        } else {
            chunk_size = sizeof(chunk);
        }

        readPayloadChunk(chunk, chunk_size);

        if (target_file != FILE_HANDLE_NULL) {
            if (writeFileChunk(target_file, chunk, chunk_size) == false) {
                fatalErrorTempFiles();
            }
        }

        file_size -= chunk_size;
    }

    assert(file_size == 0);
#endif
}

// Zero means, not yet created, created unsuccessfully, terminated already.
#if defined(_WIN32)
HANDLE handle_process = 0;
#else
pid_t handle_process = 0;
#endif

static filename_char_t payload_path[4096] = {0};

#if _NUITKA_ONEFILE_TEMP_BOOL
static bool payload_created = false;
#endif

#define MAX_CREATED_DIRS 1024
static filename_char_t *created_dir_paths[MAX_CREATED_DIRS];
int created_dir_count = 0;

static bool createDirectory(filename_char_t const *path) {
    bool bool_res;

#if defined(_WIN32)
    if (created_dir_count == 0) {
        filename_char_t home_path[4096];
        wchar_t *pattern = L"{HOME}";

        bool_res = expandTemplatePathFilename(home_path, pattern, sizeof(payload_path) / sizeof(filename_char_t));

        if (unlikely(bool_res == false)) {
            fatalErrorSpec(pattern);
        }

        created_dir_paths[created_dir_count] = wcsdup(home_path);
        created_dir_count += 1;
    }
#endif

    for (int i = 0; i < created_dir_count; i++) {
        if (strcmpFilename(path, created_dir_paths[i]) == 0) {
            return true;
        }
    }

#if defined(_WIN32)
    // On Windows, lets ignore drive letters.
    if (strlenFilename(path) == 2 && path[1] == L':') {
        return true;
    }
#endif

#if defined(_WIN32)
    bool_res = CreateDirectoryW(path, NULL);

    if (bool_res == false && GetLastError() == 183) {
        bool_res = true;
    }
#else
    if (access(path, F_OK) != -1) {
        bool_res = true;
    } else {
        bool_res = mkdir(path, 0700) == 0;
    }
#endif

    if (bool_res != false && created_dir_count < MAX_CREATED_DIRS) {
        created_dir_paths[created_dir_count] = strdupFilename(path);
        created_dir_count += 1;
    }

    return bool_res;
}

static bool createContainingDirectory(filename_char_t const *path) {
    filename_char_t dir_path[4096] = {0};
    dir_path[0] = 0;

    appendStringSafeFilename(dir_path, path, sizeof(dir_path) / sizeof(filename_char_t));

    filename_char_t *w = dir_path + strlenFilename(dir_path);

    while (w > dir_path) {
        if (*w == FILENAME_SEP_CHAR) {
            *w = 0;

            bool res = createDirectory(dir_path);
            if (res != false) {
                return true;
            }

            createContainingDirectory(dir_path);
            return createDirectory(dir_path);
        }

        w--;
    }

    return true;
}

#if _NUITKA_ONEFILE_TEMP_BOOL
#if defined(_WIN32)

static bool isDirectory(wchar_t const *path) {
    DWORD dwAttrib = GetFileAttributesW(path);

    return (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY) != 0);
}

static void _removeDirectory(wchar_t const *path) {
    SHFILEOPSTRUCTW file_op_struct = {
        NULL, FO_DELETE, payload_path, L"", FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT, false, 0, L""};
    SHFileOperationW(&file_op_struct);
}

static void removeDirectory(wchar_t const *path) {
    _removeDirectory(path);

    for (int i = 0; i < 20; i++) {
        if (!isDirectory(path)) {
            break;
        }

        // Delay 0.1s before trying again.
        Sleep(100);

        _removeDirectory(path);
    }
}

#else
static int removeDirectory(char const *path) {
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
#endif

#if !defined(_WIN32)
static int waitpid_retried(pid_t pid, int *status, bool async) {
    int res;

    for (;;) {
        if (status != NULL) {
            *status = 0;
        }

        res = waitpid(pid, status, async ? WNOHANG : 0);

        if ((res == -1) && (errno == EINTR)) {
            continue;
        }

        break;
    }

    return res;
}

static int waitpid_timeout(pid_t pid) {
    // Check if already exited.
    if (waitpid(pid, NULL, WNOHANG) == -1) {
        return 0;
    }

    // Checking 5 times per second should be good enough.
    long ns = 200000000L; // 0.2s

    // Seconds, nanoseconds from our milliseconds value.
    struct timespec timeout = {
        _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT / 1000,
        (_NUITKA_ONEFILE_CHILD_GRACE_TIME_INT % 1000) * 1000,
    };
    struct timespec delay = {0, ns};
    struct timespec elapsed = {0, 0};
    struct timespec rem;

    do {
        // Only want to care about SIGCHLD here.
        int res = waitpid_retried(pid, NULL, true);

        if (unlikely(res < 0)) {
            perror("waitpid");

            return -1;
        }

        if (res != 0) {
            break;
        }

        nanosleep(&delay, &rem);

        elapsed.tv_sec += (elapsed.tv_nsec + ns) / 1000000000L;
        elapsed.tv_nsec = (elapsed.tv_nsec + ns) % 1000000000L;
    } while (elapsed.tv_sec < timeout.tv_sec ||
             (elapsed.tv_sec == timeout.tv_sec && elapsed.tv_nsec < timeout.tv_nsec));

    return 0;
}
#endif

static void cleanupChildProcess(bool send_sigint) {

    // Cause KeyboardInterrupt in the child process.
    if (handle_process != 0) {

        if (send_sigint) {
#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
            puts("Sending CTRL-C to child\n");
#endif

#if defined(_WIN32)
            BOOL res = GenerateConsoleCtrlEvent(CTRL_C_EVENT, GetProcessId(handle_process));

            if (res == false) {
                printOSErrorMessage("Failed to send CTRL-C to child process.", GetLastError());
                // No error exit is done, we still want to cleanup when it does exit
            }
#else
            kill(handle_process, SIGINT);
#endif
        }

        // TODO: We ought to only need to wait if there is a need to cleanup
        // files when we are on Windows, on Linux maybe exec can be used so
        // this process to exist anymore if there is nothing to do.
#if _NUITKA_ONEFILE_TEMP_BOOL || 1
        NUITKA_PRINT_TRACE("Waiting for child to exit.\n");
#if defined(_WIN32)
        if (WaitForSingleObject(handle_process, _NUITKA_ONEFILE_CHILD_GRACE_TIME_INT) != 0) {
            TerminateProcess(handle_process, 0);
        }

        CloseHandle(handle_process);
#else
        waitpid_timeout(handle_process);
        kill(handle_process, SIGKILL);
#endif
        NUITKA_PRINT_TRACE("Child is exited.\n");
#endif
    }

#if _NUITKA_ONEFILE_TEMP_BOOL
    if (payload_created) {
#if _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        wprintf(L"Removing payload path '%lS'\n", payload_path);
#endif
        removeDirectory(payload_path);
    }
#endif
}

#if defined(_WIN32)
BOOL WINAPI ourConsoleCtrlHandler(DWORD fdwCtrlType) {
    switch (fdwCtrlType) {
        // Handle the CTRL-C signal.
    case CTRL_C_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-C event");
#endif
        cleanupChildProcess(false);
        return FALSE;

        // CTRL-CLOSE: confirm that the user wants to exit.
    case CTRL_CLOSE_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Close event");
#endif
        cleanupChildProcess(false);
        return FALSE;

        // Pass other signals to the next handler.
    case CTRL_BREAK_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Break event");
#endif
        cleanupChildProcess(false);
        return FALSE;

    case CTRL_LOGOFF_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Logoff event");
#endif
        cleanupChildProcess(false);
        return FALSE;

    case CTRL_SHUTDOWN_EVENT:
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING
        puts("Ctrl-Shutdown event");
#endif
        cleanupChildProcess(false);
        return FALSE;

    default:
        return FALSE;
    }
}

#else
void ourConsoleCtrlHandler(int sig) { cleanupChildProcess(false); }
#endif

#if _NUITKA_AUTO_UPDATE_BOOL && !defined(__IDE_ONLY__)
#include "nuitka_onefile_auto_updater.h"
#endif

#if _NUITKA_AUTO_UPDATE_BOOL
extern bool exe_file_updatable;
#endif

#ifdef _NUITKA_ONEFILE_SPLASH_SCREEN
#ifdef __cplusplus
extern "C" {
#endif
extern void initSplashScreen(void);
extern bool checkSplashScreen(void);
#ifdef __cplusplus
}
#endif
#endif

#ifdef _WIN32

static bool containsWStringAny(wchar_t const *source, wchar_t const *characters) {
    while (*characters) {
        if (wcschr(source, *characters) != NULL) {
            return true;
        }

        characters++;
    }

    return false;
}

static wchar_t *getCommandLineForChildProcess(void) {

    wchar_t *orig_command_line = GetCommandLineW();
#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
    wprintf(L"Command line was '%ls'\n", orig_command_line);
#endif

    int argc;
    LPWSTR *argv = CommandLineToArgvW(orig_command_line, &argc);
    assert(argv != NULL);
    assert(argc > 0);

    static wchar_t result[32768];
    result[0] = 0;

    // Assigning constant value to there, strongly hoping nothing ever modifies
    // the contents.
    argv[0] = (wchar_t *)getBinaryPath();

    for (int i = 0; i < argc; i++) {
        if (i >= 1) {
            appendWCharSafeW(result, L' ', sizeof(result) / sizeof(wchar_t));
        }

        bool needs_quote = containsWStringAny(argv[i], L" \t\n\v\"");

#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
        wprintf(L"Command line arg %d was '%ls' needs quoting %ls\n", i, argv[i], needs_quote ? L"yes" : L"no");
#endif

        if (needs_quote) {
            appendWCharSafeW(result, L'"', sizeof(result) / sizeof(wchar_t));

            wchar_t const *current = argv[i];

            for (;;) {
                int backslash_count = 0;

                while (*current == L'\\') {
                    current++;
                    backslash_count += 1;
                }

                if (*current == 0) {
                    for (int j = 0; j < backslash_count * 2; j++) {
                        appendWCharSafeW(result, L'\\', sizeof(result) / sizeof(wchar_t));
                    }

                    break;
                } else if (*current == L'"') {
                    for (int j = 0; j < backslash_count * 2 + 1; j++) {
                        appendWCharSafeW(result, L'\\', sizeof(result) / sizeof(wchar_t));
                    }
                } else {
                    for (int j = 0; j < backslash_count; j++) {
                        appendWCharSafeW(result, L'\\', sizeof(result) / sizeof(wchar_t));
                    }
                }

                appendWCharSafeW(result, *current, sizeof(result) / sizeof(wchar_t));

                current++;
            }

            appendWCharSafeW(result, L'"', sizeof(result) / sizeof(wchar_t));

        } else {
            appendWStringSafeW(result, argv[i], sizeof(result) / sizeof(wchar_t));
        }
    }

#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
    wprintf(L"Command line composed to '%ls'\n", result);
#endif
    return result;
}
#endif

#if _NUITKA_ONEFILE_DLL_MODE
static int runPythonCodeDLL(filename_char_t const *dll_filename, int argc, native_command_line_argument_t **argv) {

#if defined(_WIN32)
    DLL_DIRECTORY_COOKIE dll_dir_cookie = AddDllDirectory(payload_path);
    assert(dll_dir_cookie != 0);

    HINSTANCE hGetProcIDDLL = LoadLibraryExW(dll_filename, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);

    if (!hGetProcIDDLL) {
        fatalIOError("Error, load DLL.", getLastErrorCode());

        return EXIT_FAILURE;
    }

    typedef int(__stdcall * nuitka_dll_function_ptr)(int, wchar_t **);

    nuitka_dll_function_ptr nuitka_dll_function = (nuitka_dll_function_ptr)GetProcAddress(hGetProcIDDLL, "run_code");

    if (nuitka_dll_function == NULL) {
        fatalError("Error, DLL entry point not found.");

        return EXIT_FAILURE;
    }

    return (*nuitka_dll_function)(argc, argv);
#else
    typedef int (*nuitka_dll_function_ptr)(int, native_command_line_argument_t **);

    void *handle = dlopen(dll_filename, RTLD_LOCAL | RTLD_NOW);

    if (unlikely(handle == NULL)) {
        const char *error = dlerror();

        if (unlikely(error == NULL)) {
            error = "unknown dlopen() error";
        }

        fatalError(error);
        return EXIT_FAILURE;
    }

    nuitka_dll_function_ptr nuitka_dll_function = (nuitka_dll_function_ptr)dlsym(handle, "run_code");
    assert(nuitka_dll_function);

    return (*nuitka_dll_function)(argc, argv);
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
#if defined(_NUITKA_HIDE_CONSOLE_WINDOW)
    hideConsoleIfSpawned();
#endif
#else
int main(int argc, char **argv) {
#endif
#endif
    // Attach to the parent console respecting redirection only, otherwise we cannot
    // even output traces.
#if defined(_WIN32) && defined(_NUITKA_ATTACH_CONSOLE_WINDOW)
    inheritAttachedConsole();
#endif

    NUITKA_PRINT_TIMING("ONEFILE: Entered main().");

    filename_char_t const *pattern = FILENAME_EMPTY_STR _NUITKA_ONEFILE_TEMP_SPEC;
    bool bool_res = expandTemplatePathFilename(payload_path, pattern, sizeof(payload_path) / sizeof(filename_char_t));

    // _putws(payload_path);

#if _NUITKA_ONEFILE_DLL_MODE
    environment_char_t const *process_role = getEnvironmentVariable("NUITKA_ONEFILE_PARENT");

    // Empty strings do not count.
    if (process_role != NULL && *process_role == 0) {
        process_role = NULL;
    }

#if defined(_WIN32)
    if (process_role != NULL) {
        errno = 0;
        wchar_t *endptr = NULL;
        unsigned long onefile_parent_pid = wcstoul(process_role, &endptr, 10);

        if (errno == 0 && *endptr == 0) {
            HANDLE parent_process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, onefile_parent_pid);

            if (parent_process != NULL) {
                filename_char_t onefile_parent_path[2048];

                DWORD len = GetModuleFileNameExW(parent_process, NULL, onefile_parent_path,
                                                 sizeof(onefile_parent_path) / sizeof(onefile_parent_path[0]));

                if (len == 0) {
                    process_role = NULL;
                } else {
                    resolveFileSymbolicLink(onefile_parent_path, onefile_parent_path,
                                            sizeof(onefile_parent_path) / sizeof(wchar_t), true);
                    makeShortDirFilename(onefile_parent_path, sizeof(onefile_parent_path) / sizeof(wchar_t));
                }

                if (strcmpFilename(onefile_parent_path, getBinaryFilenameWideChars(true)) != 0) {
                    process_role = NULL;
                }
            } else {
                process_role = NULL;
            }

            CloseHandle(parent_process);
        } else {
            process_role = NULL;
        }
    }
#endif

#else
    environment_char_t const *process_role = NULL;
#endif

    // IF we are the bootstrasp binary, show the splash screen.
#if defined(_NUITKA_ONEFILE_SPLASH_SCREEN) && _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
    if (process_role == NULL) {
        initSplashScreen();
    }
#endif

    NUITKA_PRINT_TIMING("ONEFILE: Unpacking payload.");
    initPayloadData();

    static filename_char_t first_filename[1024] = {0};

    if (unlikely(bool_res == false)) {
        fatalErrorSpec(pattern);
    }

#if defined(_NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_HANDLING)
    wprintf(L"payload path: '%lS'\n", payload_path);
#endif

#if defined(_WIN32)
    bool_res = SetConsoleCtrlHandler(ourConsoleCtrlHandler, true);
    if (bool_res == false) {
        fatalError("Error, failed to register signal handler.");
    }
#else
    signal(SIGINT, ourConsoleCtrlHandler);
    signal(SIGQUIT, ourConsoleCtrlHandler);
    signal(SIGTERM, ourConsoleCtrlHandler);
#endif

#if _NUITKA_AUTO_UPDATE_BOOL
    checkAutoUpdates();
#endif

    NUITKA_PRINT_TIMING("ONEFILE: Checking header for compression.");

    char header[3];
    readChunk(&header, sizeof(header));

    if (header[0] != 'K' || header[1] != 'A') {
        fatalErrorHeaderAttachedData();
    }

    NUITKA_PRINT_TIMING("ONEFILE: Header is OK.");

// The 'X' stands for no compression, 'Y' is compressed, handle that.
#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
    if (header[2] != 'Y') {
        fatalErrorHeaderAttachedData();
    }
    initZSTD();

    input.src = payload_current;
    input.pos = 0;

    // TODO: Ought to assert that this doesn't truncate anything.
    input.size = (size_t)payload_size;

    assert(payload_size > 0);
#else
    if (header[2] != 'X') {
        fatalErrorHeaderAttachedData();
    }
#endif

    NUITKA_PRINT_TIMING("ONEFILE: Entering decompression.");

#if _NUITKA_ONEFILE_TEMP_BOOL
    payload_created = true;
#endif

    for (;;) {
        filename_char_t *filename = readPayloadFilename();

        // printf("Filename: " FILENAME_FORMAT_STR "\n", filename);

        // Detect EOF from empty filename.
        if (filename[0] == 0) {
            break;
        }

        static filename_char_t target_path[4096] = {0};
        target_path[0] = 0;

        appendStringSafeFilename(target_path, payload_path, sizeof(target_path) / sizeof(filename_char_t));
        appendCharSafeFilename(target_path, FILENAME_SEP_CHAR, sizeof(target_path) / sizeof(filename_char_t));
        appendStringSafeFilename(target_path, filename, sizeof(target_path) / sizeof(filename_char_t));

        if (first_filename[0] == 0) {
            appendStringSafeFilename(first_filename, target_path, sizeof(target_path) / sizeof(filename_char_t));

            // Run the Python code DLL if it's already unpacked.
#if _NUITKA_ONEFILE_DLL_MODE
            if (process_role != NULL) {
                return runPythonCodeDLL(first_filename, argc, argv);
            }
#endif
        }

#if !defined(_WIN32) && !defined(__MSYS__)
        unsigned char file_flags = readPayloadFileFlagsValue();
#endif

#if !defined(_WIN32) && !defined(__MSYS__)
        if (file_flags & 2) {
            filename_char_t *link_target_path = readPayloadFilename();

            // printf("Filename: " FILENAME_FORMAT_STR " symlink to " FILENAME_FORMAT_STR "\n", target_path,
            // link_target_path);

            createContainingDirectory(target_path);

            unlink(target_path);
            if (symlink(link_target_path, target_path) != 0) {
                fatalErrorTempFileCreate(target_path);
            }

            continue;
        }
#endif
        // _putws(target_path);
        unsigned long long file_size = readPayloadSizeValue();

        bool needs_write = true;

#if _NUITKA_ONEFILE_TEMP_BOOL == 0
        uint32_t contained_file_checksum = readPayloadChecksumValue();
        uint32_t existing_file_checksum = getFileCRC32(target_path);

        if (contained_file_checksum == existing_file_checksum) {
            needs_write = false;

#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
            fprintf(stderr, "CACHE HIT for '" FILENAME_FORMAT_STR "'.\n", target_path);
#endif
        } else {
#ifdef _NUITKA_EXPERIMENTAL_DEBUG_ONEFILE_CACHING
            fprintf(stderr, "CACHE MISS for '" FILENAME_FORMAT_STR "'.\n", target_path);
#endif
        }
#endif

#if _NUITKA_ONEFILE_ARCHIVE_BOOL == 1
#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
        uint32_t contained_archive_file_size = readArchiveFileSizeValue();

        input.src = payload_current;
        input.pos = 0;
        input.size = contained_archive_file_size;

        output.pos = 0;
        output.size = 0;

        payload_current += contained_archive_file_size;
#endif
#endif
        FILE_HANDLE target_file = FILE_HANDLE_NULL;

        if (needs_write) {
            createContainingDirectory(target_path);
            target_file = createFileForWritingChecked(target_path);
        }

        writeContainedFile(target_file, file_size);

#if !defined(_WIN32) && !defined(__MSYS__)
        if ((file_flags & 1) && (target_file != FILE_HANDLE_NULL)) {
            int fd = fileno(target_file);

            struct stat stat_buffer;
            int res = fstat(fd, &stat_buffer);

            if (res == -1) {
                printOSErrorMessage("fstat", errno);
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
                printOSErrorMessage("fchmod", errno);
            }
        }
#endif

        if (target_file != FILE_HANDLE_NULL) {
            if (closeFile(target_file) == false) {
                fatalErrorTempFiles();
            }
        }
    }

    NUITKA_PRINT_TIMING("ONEFILE: Finishing decompression, cleanup payload.");

    closePayloadData();

#if _NUITKA_AUTO_UPDATE_BOOL
    exe_file_updatable = true;
#endif

#if _NUITKA_ONEFILE_COMPRESSION_BOOL == 1
    releaseZSTD();
#endif

    // Pass our pid by value to the child. If we exit for some reason, re-parenting
    // might change it by the time the child looks at its parent.
    if (process_role == NULL) {
#if defined(_WIN32)
        setEnvironmentVariableFromLong("NUITKA_ONEFILE_PARENT", GetCurrentProcessId());
#else
        setEnvironmentVariableFromLong("NUITKA_ONEFILE_PARENT", (long)getpid());
#endif
    }

#if defined(_WIN32)
    filename_char_t const *binary_filename = getBinaryFilenameWideChars(false);
#else
    filename_char_t const *binary_filename = getBinaryFilenameHostEncoded(false);
#endif
    setEnvironmentVariable("NUITKA_ONEFILE_DIRECTORY", stripBaseFilename(binary_filename));

    setEnvironmentVariable("NUITKA_ORIGINAL_ARGV0", argv[0]);

    NUITKA_PRINT_TIMING("ONEFILE: Preparing forking of slave process.");

#if _NUITKA_ONEFILE_DLL_MODE
    filename_char_t const *fork_binary = getBinaryPath();
#else
    filename_char_t const *fork_binary = first_filename;
#endif

#if defined(_WIN32)

    // spell-checker: ignore STARTUPINFOW, STARTF_USESTDHANDLES
    STARTUPINFOW si;
    memset(&si, 0, sizeof(si));
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    si.cb = sizeof(si);

    PROCESS_INFORMATION pi;

    bool_res = CreateProcessW(fork_binary,
                              getCommandLineForChildProcess(), // command line
                              NULL,                            // process attributes
                              NULL,                            // thread attributes
                              TRUE,                            // inherit handles
                              NORMAL_PRIORITY_CLASS,           // creation flags
                              NULL, NULL, &si, &pi);

    NUITKA_PRINT_TIMING("ONEFILE: Started slave process.");

    if (bool_res == false) {
        fatalErrorChild("Error, couldn't launch child", GetLastError());
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
        if (process_role == NULL) {
            if (exit_code == STILL_ACTIVE) {
                bool done = checkSplashScreen();

                // Stop checking splash screen, can increase timeout.
                if (done) {
                    wait_time = INFINITE;
                }

                continue;
            }
        }
#endif
        CloseHandle(handle_process);

        handle_process = 0;
    }

    cleanupChildProcess(false);
#else
    pid_t pid = fork();
    int exit_code;

    if (pid < 0) {
        int error_code = errno;

        cleanupChildProcess(false);

        fatalErrorChild("Error, couldn't launch child (fork)", error_code);
        exit_code = 2;
    } else if (pid == 0) {
        // Child process

        // Make sure, we use the absolute program path for argv[0]
        argv[0] = (char *)getBinaryPath();

        execv(fork_binary, argv);

        fatalErrorChild("Error, couldn't launch child (exec)", errno);
        exit_code = 2;
    } else {
        // Onefile bootstrap process
        handle_process = pid;

        int status;
        int res = waitpid_retried(handle_process, &status, false);

        if (res == -1 && errno != ECHILD) {
            exit_code = 2;
        } else {
            exit_code = WEXITSTATUS(status);
        }

        cleanupChildProcess(false);
    }

#endif

    NUITKA_PRINT_TIMING("ONEFILE: Exiting.");

    return exit_code;
}

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
