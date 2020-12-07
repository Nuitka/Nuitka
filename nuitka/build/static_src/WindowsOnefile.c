//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include <assert.h>
#include <stdio.h>

/* Type bool */
#ifndef __cplusplus
#include "stdbool.h"
#endif

#include <Shlobj.h>
#include <windows.h>

#ifndef MAX_PATH
// TODO: Imitate definition of this from CPython headers.
#define MAX_PATH 1024
#endif

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

// #include <locale.h>

static void appendWStringSafeW(wchar_t *target, wchar_t const *source, size_t buffer_size) {
    while (*target != 0) {
        target++;
        buffer_size -= 1;
    }

    while (*source != 0) {
        if (buffer_size < 1) {
            abort();
        }

        *target++ = *source++;
        buffer_size -= 1;
    }

    *target = 0;
}

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

static wchar_t *readFilename(HANDLE exe_file) {
    static wchar_t buffer[1024];

    wchar_t *w = buffer;

    for (;;) {
        DWORD read_size;
        BOOL bool_res = ReadFile(exe_file, w, 2, &read_size, NULL);

        assert(bool_res);
        assert(read_size == 2);

        if (*w == 0) {
            break;
        }

        w += 1;
    }

    return buffer;
}

static unsigned long long readSizeValue(HANDLE exe_file) {
    unsigned long long result;
    DWORD read_size;
    BOOL bool_res = ReadFile(exe_file, &result, sizeof(unsigned long long), &read_size, NULL);
    assert(bool_res);
    assert(read_size == sizeof(unsigned long long));

    return result;
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

    static wchar_t exe_filename[MAX_PATH + 1] = {0};

    DWORD res = GetModuleFileNameW(NULL, exe_filename, sizeof(exe_filename));
    assert(res != 0);

    // _putws(exe_filename);

    static wchar_t payload_path[MAX_PATH + 1] = {0};

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
    }

    // _putws(payload_path);

    appendWCharSafeW(payload_path, L'\\', sizeof(payload_path));
    appendWStringSafeW(payload_path, L"" ONEFILE_COMPANY, sizeof(payload_path));

    BOOL bool_res = CreateDirectoryW(payload_path, NULL);

    appendWCharSafeW(payload_path, L'\\', sizeof(payload_path));
    appendWStringSafeW(payload_path, L"" ONEFILE_PRODUCT, sizeof(payload_path));
    bool_res = CreateDirectoryW(payload_path, NULL);

    appendWCharSafeW(payload_path, L'\\', sizeof(payload_path));
    appendWStringSafeW(payload_path, L"" ONEFILE_VERSION, sizeof(payload_path));
    bool_res = CreateDirectoryW(payload_path, NULL);

    // _putws(payload_path);

    HANDLE exe_file = CreateFileW(exe_filename, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    assert(exe_file != INVALID_HANDLE_VALUE);

    res = SetFilePointer(exe_file, -8, NULL, FILE_END);
    assert(res != INVALID_SET_FILE_POINTER);

    DWORD read_size;

    unsigned long long start_pos = readSizeValue(exe_file);

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
        wchar_t *filename = readFilename(exe_file);

        // Detect EOF from empty filename.
        if (filename[0] == 0) {
            break;
        }

        // puts("at:");
        // _putws(filename);

        static wchar_t target_path[MAX_PATH + 1] = {0};
        target_path[0] = 0;

        wchar_t *w = filename;

        while (*w) {
            if (*w == L'\\') {
                *w = 0;

                target_path[0] = 0;
                appendWStringSafeW(target_path, payload_path, sizeof(target_path));
                appendWCharSafeW(target_path, L'\\', sizeof(target_path));
                appendWStringSafeW(target_path, filename, sizeof(target_path));

                *w = L'\\';

                // _putws(target_path);
                bool_res = CreateDirectoryW(target_path, NULL);
            }

            w++;
        }

        target_path[0] = 0;
        appendWStringSafeW(target_path, payload_path, sizeof(target_path));
        appendWCharSafeW(target_path, L'\\', sizeof(target_path));
        appendWStringSafeW(target_path, filename, sizeof(target_path));

        if (first_filename[0] == 0) {
            appendWStringSafeW(first_filename, target_path, sizeof(target_path));
        }

        // _putws(target_path);

        HANDLE target_file = CreateFileW(target_path, GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, 0, NULL);
        assert(target_file != INVALID_HANDLE_VALUE);

        unsigned long long file_size = readSizeValue(exe_file);

        while (file_size > 0) {
            static char chunk[4096];

            LONG chunk_size;

            // Doing min manually, as otherwise the compiler is confused from types.
            if (file_size <= sizeof(chunk)) {
                chunk_size = (LONG)file_size;
            } else {
                chunk_size = sizeof(chunk);
            }

            bool_res = ReadFile(exe_file, chunk, chunk_size, NULL, NULL);
            assert(bool_res);
            bool_res = WriteFile(target_file, chunk, chunk_size, NULL, NULL);
            assert(bool_res);

            file_size -= chunk_size;
        }
        assert(file_size == 0);

        CloseHandle(target_file);
    }

    wchar_t const *orig_args = GetCommandLineW();

    bool inside_quotes = false;

    for (;;) {
        wchar_t c = *orig_args;

        if (c == L'\"') {
            inside_quotes = !inside_quotes;
        } else if (c == 0 || (c == L' ' && !inside_quotes)) {
            break;
        }

        orig_args++;
    }

    static wchar_t command_line[MAX_PATH + 1] = {0};

    appendWStringSafeW(command_line, first_filename, sizeof(command_line));
    // Note: The orig_args is either empty or has the leading space to separate:
    appendWStringSafeW(command_line, orig_args, sizeof(command_line));

    STARTUPINFOW si;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);

    PROCESS_INFORMATION pi;

    bool_res = CreateProcessW(NULL, command_line, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);
    assert(bool_res);

    CloseHandle(pi.hThread);
    HANDLE handle_process = pi.hProcess;

    DWORD exit_code = 0;

    if (handle_process != 0) {
        WaitForSingleObject(handle_process, INFINITE);

        if (!GetExitCodeProcess(handle_process, &exit_code)) {
            exit_code = 1;
        }

        CloseHandle(handle_process);
    }

    return exit_code;
}
