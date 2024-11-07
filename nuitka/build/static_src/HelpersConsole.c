//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#define _NUITKA_ATTACH_CONSOLE_WINDOW 1
#endif

#if defined(_WIN32)
#if defined(_NUITKA_ATTACH_CONSOLE_WINDOW)
#include <io.h>

// Attach to the parent console respecting redirection only, otherwise we cannot
// even output traces.
static bool needs_stdin_attaching = false;
static bool needs_stdout_attaching = false;
static bool needs_stderr_attaching = false;

static bool is_attachable = false;

void inheritAttachedConsole(void) {
    is_attachable = AttachConsole(ATTACH_PARENT_PROCESS);

    if (is_attachable) {
        needs_stdin_attaching = fileno(stdin) < 0;
        needs_stdout_attaching = fileno(stdout) < 0;
#if !defined(NUITKA_FORCED_STDERR_PATH) && !defined(NUITKA_FORCED_STDERR_NONE_BOOL) &&                                 \
    !defined(NUITKA_FORCED_STDERR_NULL_BOOL)
        needs_stderr_attaching = fileno(stderr) < 0;
#endif
    }

    if (needs_stdin_attaching) {
        SECURITY_ATTRIBUTES security_attributes = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};

        FILE_HANDLE win_handle = CreateFileW(L"CONIN$", GENERIC_WRITE, FILE_SHARE_READ, &security_attributes,
                                             CREATE_ALWAYS, FILE_FLAG_NO_BUFFERING, NULL);

        FILE *new_handle = _wfreopen(L"CONIN$", L"rb", stdin);
        assert(new_handle != NULL);
        *stdin = *new_handle;

        SetStdHandle(STD_INPUT_HANDLE, win_handle);
    } else {
        BOOL r = SetStdHandle(STD_INPUT_HANDLE, (HANDLE)_get_osfhandle(fileno(stdin)));
        assert(r);
    }

    if (needs_stdout_attaching) {
        SECURITY_ATTRIBUTES security_attributes = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};

        FILE_HANDLE win_handle = CreateFileW(L"CONOUT$", GENERIC_WRITE, FILE_SHARE_WRITE, &security_attributes,
                                             CREATE_ALWAYS, FILE_FLAG_NO_BUFFERING, NULL);
        assert(win_handle != INVALID_HANDLE_VALUE);

        FILE *new_handle = _wfreopen(L"CONOUT$", L"wb", stdout);
        assert(new_handle != NULL);
        // Win32 doesn't allow line buffering.
        setvbuf(new_handle, NULL, _IONBF, 0);
        *stdout = *new_handle;

        BOOL r = SetStdHandle(STD_OUTPUT_HANDLE, win_handle);
        assert(r);
    } else {
        setvbuf(stdout, NULL, _IONBF, 0);
        BOOL r = SetStdHandle(STD_OUTPUT_HANDLE, (HANDLE)_get_osfhandle(fileno(stdout)));
        assert(r);
    }

    if (needs_stderr_attaching) {
        SECURITY_ATTRIBUTES security_attributes = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};

        FILE_HANDLE win_handle = CreateFileW(L"CONOUT$", GENERIC_WRITE, FILE_SHARE_WRITE, &security_attributes,
                                             CREATE_ALWAYS, FILE_FLAG_NO_BUFFERING, NULL);

        FILE *new_handle = _wfreopen(L"CONOUT$", L"wb", stderr);
        assert(new_handle != NULL);
        // Win32 doesn't allow line buffering.
        setvbuf(new_handle, NULL, _IONBF, 0);

        *stderr = *new_handle;
        SetStdHandle(STD_ERROR_HANDLE, win_handle);
    } else {
#if !defined(NUITKA_FORCED_STDERR_PATH) && !defined(NUITKA_FORCED_STDERR_NONE_BOOL) &&                                 \
    !defined(NUITKA_FORCED_STDERR_NULL_BOOL)
        setvbuf(stderr, NULL, _IONBF, 0);
        BOOL r = SetStdHandle(STD_ERROR_HANDLE, (HANDLE)_get_osfhandle(fileno(stderr)));
        assert(r);
#endif
    }
}
#endif
#if defined(_NUITKA_HIDE_CONSOLE_WINDOW)
void hideConsoleIfSpawned(void) {
    HWND hWnd = GetConsoleWindow();
    DWORD consoleProcesses[2];
    // detect if we were spawned from an existing cmdline window
    DWORD numProcesses = GetConsoleProcessList(consoleProcesses, 2);
    // if we have just one process that's us alone
    if (hWnd && numProcesses <= 1) {
        // then let's hide the console
        ShowWindow(hWnd, SW_HIDE);
    }
}
#endif
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
