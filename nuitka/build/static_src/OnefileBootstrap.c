//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
 */

#define _CRT_SECURE_NO_WARNINGS

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#ifdef __NUITKA_NO_ASSERT__
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
#include <Shlobj.h>
#include <imagehlp.h>
#include <windows.h>

#ifndef CSIDL_LOCAL_APPDATA
#define CSIDL_LOCAL_APPDATA 28
#endif

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
#define ONEFILE_COMPANY "SomeVendor"
#define ONEFILE_PRODUCT "SomeProduct"
#define ONEFILE_VERSION "SomeVersion"
#define _NUITKA_ONEFILE_TEMP_SPEC "%TEMP%/onefile_%PID%_%TIME%"
#endif

#ifdef _NUITKA_ONEFILE_COMPRESSION
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

static void fatalErrorTempFiles() { fatalError("Error, couldn't runtime expand temporary files."); }

static void fatalErrorAttachedData() { fatalError("Error, couldn't decode attached data."); }

static void fatalErrorMemory() { fatalError("Error, couldn't allocate memory."); }

// TODO: Make use of this on other platforms as well.
#if defined(_WIN32)
static void fatalErrorChild() { fatalError("Error, couldn't launch child."); }
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
#define appendStringSafeFilename appendWStringSafeW
#define appendCharSafeFilename appendWCharSafeW
#else
#define filename_char_t char
#define FILENAME_SEP_STR "/"
#define FILENAME_SEP_CHAR '/'
#define appendStringSafeFilename appendStringSafe
#define appendCharSafeFilename appendCharSafe
#endif

// Have a type for file type different on Linux and Win32.
#if defined(_WIN32)
#define FILE_HANDLE HANDLE
#else
#define FILE_HANDLE FILE *
#endif

static FILE_HANDLE createFileForWriting(filename_char_t const *filename) {
#if defined(_WIN32)
    FILE_HANDLE result = CreateFileW(filename, GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, 0, NULL);
    if (result == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "Error, failed to open '%ls' for writing.", filename);
        exit(2);
    }
#else
    FILE *result = fopen(filename, "wb");

    if (result == NULL) {
        fprintf(stderr, "Error, failed to open '%s' for writing.", filename);
        exit(2);
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
    long written = fwrite(chunk, 1, chunk_size, target_file);

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

static int getMyPid() {
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

#ifdef _NUITKA_ONEFILE_COMPRESSION

static ZSTD_DCtx *dctx = NULL;
static ZSTD_inBuffer input = {NULL, 0, 0};
static ZSTD_outBuffer output = {NULL, 0, 0};

static void initZSTD() {
    size_t const buffInSize = ZSTD_DStreamInSize();
    input.src = malloc(buffInSize);
    if (input.src == NULL) {
        fatalErrorMemory();
    }

    size_t const buffOutSize = ZSTD_DStreamOutSize();
    output.dst = malloc(buffOutSize);
    if (output.dst == NULL) {
        fatalErrorMemory();
    }

    dctx = ZSTD_createDCtx();
    if (dctx == NULL) {
        fatalErrorMemory();
    }
}

#endif

static size_t stream_end_pos;

static size_t getPosition() {
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
        fatalErrorAttachedData();
    }
#else
    size_t read_size = fread(buffer, 1, size, exe_file);

    if (read_size != size) {
        fatalErrorAttachedData();
    }

#endif
}

static unsigned long long readSizeValue() {
    unsigned long long result;
    readChunk(&result, sizeof(unsigned long long));

    return result;
}

static void readPayloadChunk(void *buffer, size_t size) {
#ifdef _NUITKA_ONEFILE_COMPRESSION

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

            size_t const ret = ZSTD_decompressStream(dctx, &output, &input);
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

static unsigned long long readPayloadSizeValue() {
    unsigned long long result;
    readPayloadChunk(&result, sizeof(unsigned long long));

    return result;
}

static filename_char_t readPayloadChar() {
    filename_char_t result;

    readPayloadChunk(&result, sizeof(filename_char_t));

    return result;
}

static filename_char_t *readPayloadFilename() {
    static filename_char_t buffer[1024];

    filename_char_t *w = buffer;

    for (;;) {
        *w = readPayloadChar();

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
    // _putws(payload_path);

    SHFILEOPSTRUCTW fileop_struct = {
        NULL, FO_DELETE, payload_path, L"", FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT, false, 0, L""};
    SHFileOperationW(&fileop_struct);
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
            char *buf = malloc(len);

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

static void cleanupChildProcess() {

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
        // We only need to wait if there is a need to cleanup files.
#if _NUITKA_ONEFILE_TEMP == 1
#if defined(_WIN32)
        WaitForSingleObject(handle_process, INFINITE);
        CloseHandle(handle_process);
#else
        waitpid(handle_process, NULL, 0);
#endif
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
    wchar_t *shortPath = (wchar_t *)malloc(sizeof(wchar_t) * (l + 1));
    if (shortPath == NULL) {
        fatalErrorMemory();
    }

    l = GetShortPathNameW(path, shortPath, l);
    if (unlikely(l == 0)) {
        goto err_shortPath;
    }

    size_t i;
    if (unlikely(wcstombs_s(&i, NULL, 0, shortPath, _TRUNCATE) != 0)) {
        goto err_shortPath;
    }
    char *ansiPath = (char *)malloc(i);
    if (ansiPath == NULL) {
        fatalErrorMemory();
    }
    if (unlikely(wcstombs_s(&i, ansiPath, i, shortPath, _TRUNCATE) != 0)) {
        goto err_ansiPath;
    }
    return ansiPath;

err_ansiPath:
    free(ansiPath);
err_shortPath:
    free(shortPath);
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
#define MAXPATHLEN 2048
#endif

#if defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/sysctl.h>
#endif

#if !defined(_WIN32)
char const *getBinaryPath() {
    static char binary_filename[MAXPATHLEN];

#if defined(__APPLE__)
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
#endif

#if _NUITKA_ONEFILE_SPLASH_SCREEN
#include "OnefileSplashScreen.cpp"
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
    static wchar_t exe_filename[4096] = {0};

    DWORD res = GetModuleFileNameW(NULL, exe_filename, sizeof(exe_filename) / sizeof(wchar_t));
    if (res == 0) {
        printError("Error, failed to locate onefile filename.");
        return 1;
    }

    wchar_t const *pattern = L"" _NUITKA_ONEFILE_TEMP_SPEC;
    BOOL bool_res = expandTemplatePathW(payload_path, pattern, sizeof(payload_path) / sizeof(wchar_t));

    if (bool_res == false) {
        puts("Error, couldn't runtime expand temporary directory pattern:");
        _putws(pattern);
        abort();
    }

#else
    char const *pattern = "" _NUITKA_ONEFILE_TEMP_SPEC;
    bool bool_res = expandTemplatePath(payload_path, pattern, sizeof(payload_path));

    if (bool_res == false) {
        puts("Error, couldn't runtime expand temporary directory pattern:");
        puts(pattern);
        abort();
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

    NUITKA_PRINT_TIMING("ONEFILE: Unpacking payload.");

    createDirectory(payload_path);
    payload_created = true;

#if defined(_WIN32)
    exe_file = CreateFileW(exe_filename, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
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

    PSTR exe_filename_a = convertUnicodePathToAnsi(exe_filename);
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

    if (cert_table_addr == 0) {
        res = SetFilePointer(exe_file, -8, NULL, FILE_END);
    } else {
        res = SetFilePointer(exe_file, cert_table_addr - 8, NULL, FILE_BEGIN);
    }
    if (res == INVALID_SET_FILE_POINTER) {
        fatalErrorAttachedData();
    }
#else
    int res = fseek(exe_file, -8, SEEK_END);
    if (res != 0) {
        fatalErrorAttachedData();
    }
#endif
    stream_end_pos = getPosition();

    unsigned long long start_pos = readSizeValue();

    // printf("Start at %lld\n", start_pos);
    // printf("Start at %ld\n", (LONG)start_pos);

    // The start offset won't exceed LONG.
#if defined(_WIN32)
    res = SetFilePointer(exe_file, (LONG)start_pos, NULL, FILE_BEGIN);
    if (res == INVALID_SET_FILE_POINTER) {
        fatalErrorAttachedData();
    }
#else
    res = fseek(exe_file, start_pos, SEEK_SET);
    if (res != 0) {
        fatalErrorAttachedData();
    }
#endif

    char header[3];
    readChunk(&header, sizeof(header));

    if (header[0] != 'K' || header[1] != 'A') {
        fatalErrorAttachedData();
    }

// The 'X' stands for no compression, 'Y' is compressed, handle that.
#ifdef _NUITKA_ONEFILE_COMPRESSION
    if (header[2] != 'Y') {
        fatalErrorAttachedData();
    }
    initZSTD();
#else
    if (header[2] != 'X') {
        fatalErrorAttachedData();
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

                // _putws(target_path);
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

        FILE_HANDLE target_file = createFileForWriting(target_path);

        unsigned long long file_size = readPayloadSizeValue();

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
            writeToFile(target_file, chunk, chunk_size);

            file_size -= chunk_size;
        }
        if (file_size != 0) {
            fatalErrorAttachedData();
        }

        closeFile(target_file);
    }

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

    chmod(first_filename, 0700);

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
        int res = waitpid(handle_process, &status, 0);

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
