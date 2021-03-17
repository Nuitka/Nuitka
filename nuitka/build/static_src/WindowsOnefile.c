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
/* The main program for a compiled program.
 *
 * It needs to prepare the interpreter and then loads and executes
 * the "__main__" module.
 *
 */

#define _CRT_SECURE_NO_WARNINGS

#include <assert.h>
#include <stdio.h>

/* Type bool */
#ifndef __cplusplus
#include "stdbool.h"
#endif

#include <Shlobj.h>
#include <windows.h>

#ifndef CSIDL_LOCAL_APPDATA
#define CSIDL_LOCAL_APPDATA 28
#endif

#define NUITKA_PRINT_TRACE(arg)

#ifndef __IDE_ONLY__
// Generated during build with optional defines.
#include "onefile_definitions.h"
#else
#define ONEFILE_COMPANY "SomeVendor"
#define ONEFILE_PRODUCT "SomeProduct"
#define ONEFILE_VERSION "SomeVersion"
#endif

#ifdef _NUITKA_EXPERIMENTAL_ZSTD2
#include "WindowsDecompression.c"
#endif

#include "HelpersSafeStrings.c"

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

// Note: Made payload file handle global until we properly abstracted compression.
static HANDLE exe_file;

static void readChunk(void *buffer, DWORD size) {
    DWORD read_size;
    BOOL bool_res = ReadFile(exe_file, buffer, size, &read_size, NULL);

    assert(bool_res);
    assert(read_size == size);
}

static unsigned long long readSizeValue() {
    unsigned long long result;
    readChunk(&result, sizeof(unsigned long long));

    return result;
}

static wchar_t readChar() {
    wchar_t result;

    readChunk(&result, 2);

    return result;
}

static wchar_t *readFilename() {
    static wchar_t buffer[1024];

    wchar_t *w = buffer;

    for (;;) {
        *w = readChar();

        if (*w == 0) {
            break;
        }

        w += 1;
    }

    return buffer;
}

static void printError(char const *message) {
    LPCTSTR err_buffer;

    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL,
                  GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&err_buffer, 0, NULL);

    puts(message);
    puts(err_buffer);
}

// Zero means, not yet created, created unsuccessfully, terminated already.
HANDLE handle_process = 0;

static wchar_t payload_path[4096] = {0};
static bool payload_created = false;

static void cleanupChildProcess() {

    // Cause KeyboardInterrupt in the child process.
    if (handle_process != 0) {
        NUITKA_PRINT_TRACE("Sending CTRL-C to child\n");
        BOOL res = GenerateConsoleCtrlEvent(CTRL_C_EVENT, GetProcessId(handle_process));

        if (res == false) {
            printError("Failed to send CTRL-C to child process.");
            // No error exit is done, we still want to cleanup when it does exit
        }

        // We only need to wait if there is a need to cleanup files.
#if _NUITKA_ONEFILE_TEMP == 1
        WaitForSingleObject(handle_process, INFINITE);
        CloseHandle(handle_process);
#endif
    }

#if _NUITKA_ONEFILE_TEMP == 1
    if (payload_created) {
        // _putws(payload_path);

        SHFILEOPSTRUCTW fileop_struct = {
            NULL, FO_DELETE, payload_path, L"", FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT, false, 0, L""};
        SHFileOperationW(&fileop_struct);
    }
#endif
}

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

#ifdef _NUITKA_WINMAIN_ENTRY_POINT
int __stdcall WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, char *lpCmdLine, int nCmdShow) {
#if defined(__MINGW32__) && !defined(_W64)
    /* MINGW32 */
    int argc = _argc;
    char **argv = _argv;
#else
    /* MSVC, MINGW64 */
    int argc = __argc;
    char **argv = __argv;
#endif
#else
int main(int argc, char **argv) {
#endif
    NUITKA_PRINT_TRACE("main(): Entered.");

    // puts("Hello onefile world!");

    static wchar_t exe_filename[4096] = {0};

    DWORD res = GetModuleFileNameW(NULL, exe_filename, sizeof(exe_filename) / sizeof(wchar_t));
    if (res == 0) {
        printError("Error, failed to locate onefile filename.");
        return 1;
    }

    BOOL bool_res;

#if _NUITKA_ONEFILE_TEMP == 0
    res = SHGetFolderPathW(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, payload_path);

    if (res != S_OK) {
        char error_message[1024];
        int size;

        unsigned int error_code = GetLastError();

        size = FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL, error_code, 0,
                             (LPTSTR)error_message, sizeof(error_message), NULL);

        if (size == 0) {
            printf("SHGetFolderPathW failed with error code %d\n", error_code);
        } else {

            // Strip trailing newline.
            if (size >= 2 && error_message[size - 2] == '\r' && error_message[size - 1] == '\n') {
                size -= 2;
                error_message[size] = '\0';
            }
            printf("SHGetFolderPathW failed: %s\n", error_message);
        }

        return 1;
    }

    // _putws(payload_path);
    appendWCharSafeW(payload_path, L'\\', sizeof(payload_path) / sizeof(wchar_t));
    appendWStringSafeW(payload_path, L"" ONEFILE_COMPANY, sizeof(payload_path) / sizeof(wchar_t));

    bool_res = CreateDirectoryW(payload_path, NULL);

    appendWCharSafeW(payload_path, L'\\', sizeof(payload_path));
    appendWStringSafeW(payload_path, L"" ONEFILE_PRODUCT, sizeof(payload_path) / sizeof(wchar_t));
    bool_res = CreateDirectoryW(payload_path, NULL);

    appendWCharSafeW(payload_path, L'\\', sizeof(payload_path));
    appendWStringSafeW(payload_path, L"" ONEFILE_VERSION, sizeof(payload_path) / sizeof(wchar_t));

#else
    wchar_t const *pattern = L"" _NUITKA_ONEFILE_TEMP_SPEC;

    bool_res = expandWindowsPath(payload_path, pattern, sizeof(payload_path) / sizeof(wchar_t));

    if (bool_res == false) {
        puts("Error, couldn't runtime expand temporary directory pattern:");
        _putws(pattern);
        abort();
    }

#endif
    bool_res = SetConsoleCtrlHandler(ourConsoleCtrlHandler, true);
    if (bool_res == false) {
        printError("Error, failed to register signal handler.");
        return 1;
    }

    bool_res = CreateDirectoryW(payload_path, NULL);

    payload_created = true;

    exe_file = CreateFileW(exe_filename, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (exe_file == INVALID_HANDLE_VALUE) {
        printError("Error, failed to access unpacked executable.");
        return 1;
    }

    res = SetFilePointer(exe_file, -8, NULL, FILE_END);
    assert(res != INVALID_SET_FILE_POINTER);

    DWORD read_size;

    unsigned long long start_pos = readSizeValue();

    // printf("Start at %lld\n", start_pos);
    // printf("Start at %ld\n", (LONG)start_pos);

    // The start offset won't exceed LONG.
    res = SetFilePointer(exe_file, (LONG)start_pos, NULL, FILE_BEGIN);
    assert(res != INVALID_SET_FILE_POINTER);

    char header[3];
    bool_res = ReadFile(exe_file, &header, sizeof(header), &read_size, NULL);
    assert(bool_res);
    assert(read_size == 3);

    assert(header[0] == 'K');
    assert(header[1] == 'A');

    // TODO: The 'X' stands for no compression, 'Y' is compressed, handle that.
    assert(header[2] == 'X');

    static wchar_t first_filename[1024] = {0};

    for (;;) {
        wchar_t *filename = readFilename();

        // Detect EOF from empty filename.
        if (filename[0] == 0) {
            break;
        }

        // puts("at:");
        // _putws(filename);

        static wchar_t target_path[4096] = {0};
        target_path[0] = 0;

        wchar_t *w = filename;

        while (*w) {
            if (*w == L'\\') {
                *w = 0;

                target_path[0] = 0;
                appendWStringSafeW(target_path, payload_path, sizeof(target_path) / sizeof(wchar_t));
                appendWCharSafeW(target_path, L'\\', sizeof(target_path) / sizeof(wchar_t));
                appendWStringSafeW(target_path, filename, sizeof(target_path) / sizeof(wchar_t));

                *w = L'\\';

                // _putws(target_path);
                bool_res = CreateDirectoryW(target_path, NULL);
            }

            w++;
        }

        target_path[0] = 0;
        appendWStringSafeW(target_path, payload_path, sizeof(target_path) / sizeof(wchar_t));
        appendWCharSafeW(target_path, L'\\', sizeof(target_path) / sizeof(wchar_t));
        appendWStringSafeW(target_path, filename, sizeof(target_path) / sizeof(wchar_t));

        if (first_filename[0] == 0) {
            appendWStringSafeW(first_filename, target_path, sizeof(target_path) / sizeof(wchar_t));
        }

        // _putws(target_path);

        HANDLE target_file = CreateFileW(target_path, GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, 0, NULL);
        assert(target_file != INVALID_HANDLE_VALUE);

        unsigned long long file_size = readSizeValue();

        while (file_size > 0) {
            static char chunk[32768];

            LONG chunk_size;

            // Doing min manually, as otherwise the compiler is confused from types.
            if (file_size <= sizeof(chunk)) {
                chunk_size = (LONG)file_size;
            } else {
                chunk_size = sizeof(chunk);
            }

            readChunk(chunk, chunk_size);
            bool_res = WriteFile(target_file, chunk, chunk_size, NULL, NULL);
            assert(bool_res);

            file_size -= chunk_size;
        }
        assert(file_size == 0);

        CloseHandle(target_file);
    }

    STARTUPINFOW si;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);

    PROCESS_INFORMATION pi;

    // Pass our pid by value to the child.
    {
        char buffer[128];
        _itoa_s(GetCurrentProcessId(), buffer, sizeof(buffer), 10);
        SetEnvironmentVariable("NUITKA_ONEFILE_PARENT", buffer);
    }

    bool_res = CreateProcessW(first_filename,           // application name
                              GetCommandLineW(),        // command line
                              NULL,                     // process attributes
                              NULL,                     // thread attributes
                              FALSE,                    // inherit handles
                              CREATE_NEW_PROCESS_GROUP, // creation flags
                              NULL, NULL, &si, &pi);
    assert(bool_res);

    CloseHandle(pi.hThread);
    handle_process = pi.hProcess;

    DWORD exit_code = 0;

    if (handle_process != 0) {
        WaitForSingleObject(handle_process, INFINITE);

        if (!GetExitCodeProcess(handle_process, &exit_code)) {
            exit_code = 1;
        }

        CloseHandle(handle_process);

        handle_process = 0;
    }

    cleanupChildProcess();

    return exit_code;
}
