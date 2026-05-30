//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#define _NUITKA_ATTACH_CONSOLE_WINDOW 1
#endif

#include "nuitka/tracing.h"

#if defined(_WIN32)
#if defined(_NUITKA_ATTACH_CONSOLE_WINDOW)
#include <fcntl.h>
#include <io.h>

// Attach to the parent console respecting redirection only, otherwise we cannot
// even output traces.
static bool needs_stdin_attaching = false;
static bool needs_stdout_attaching = false;
static bool needs_stderr_attaching = false;

static bool is_attachable = false;

static void _enableConsoleModeProcessed(FILE_HANDLE handle, bool is_input) {
    DWORD dwMode = 0;
    if (GetConsoleMode(handle, &dwMode)) {
        if (is_input) {
            // Ensure processed input is enabled for Windows terminal backward compatibility
            dwMode |= ENABLE_PROCESSED_INPUT;

            // Optionally enable ANSI input sequences (ENABLE_VIRTUAL_TERMINAL_INPUT).
            if (!SetConsoleMode(handle, dwMode | 0x0200)) {
                SetConsoleMode(handle, dwMode);
            }
        } else {
            // Ensure processed output is enabled so \r\n works
            dwMode |= ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT;

            // Optionally enable ANSI support for modern terminals (ENABLE_VIRTUAL_TERMINAL_PROCESSING).
            // This fails on Windows versions prior to Windows 10, so we fallback gracefully.
            if (!SetConsoleMode(handle, dwMode | 0x0004)) {
                SetConsoleMode(handle, dwMode);
            }
        }
    }
}

void inheritAttachedConsole(void) {
    is_attachable = AttachConsole(ATTACH_PARENT_PROCESS);

#ifdef _NUITKA_ONEFILE_DLL_MODE
    // In onefile DLL mode the bootstrap (static CRT) already attached,
    // so AttachConsole fails. But GetStdHandle has valid handles from
    // the bootstrap, so we can still initialize this CRT instance.
    if (!is_attachable) {
        FILE_HANDLE h_out = GetStdHandle(STD_OUTPUT_HANDLE);
        is_attachable = ((h_out != NULL) && (h_out != INVALID_HANDLE_VALUE));
    }
#endif

    if (is_attachable) {
        // The static CRT (/MT) skips _ioinit() for GUI subsystem. The
        // dynamic CRT (/MD) may have initialized with NULL handles
        // before AttachConsole ran. In either case, if fds are -2,
        // wire them up from GetStdHandle so the else-branch works.
        if (fileno(stdout) < 0) {
            freopen("NUL", "w", stdout);
            FILE_HANDLE win_handle = GetStdHandle(STD_OUTPUT_HANDLE);
            if ((win_handle != NULL) && (win_handle != INVALID_HANDLE_VALUE)) {
                int fd = _open_osfhandle((intptr_t)win_handle, _O_WRONLY | _O_TEXT);
                if (fd >= 0) {
                    _dup2(fd, _fileno(stdout));
                    _close(fd);
                }
                _setmode(_fileno(stdout), _O_U8TEXT);
                _enableConsoleModeProcessed(win_handle, false);
            }
            clearerr(stdout);
        }
#if !defined(NUITKA_FORCED_STDERR_PATH) && !defined(NUITKA_FORCED_STDERR_NONE_BOOL) &&                                 \
    !defined(NUITKA_FORCED_STDERR_NULL_BOOL)
        if (fileno(stderr) < 0) {
            freopen("NUL", "w", stderr);
            FILE_HANDLE win_handle = GetStdHandle(STD_ERROR_HANDLE);
            if ((win_handle != NULL) && (win_handle != INVALID_HANDLE_VALUE)) {
                int fd = _open_osfhandle((intptr_t)win_handle, _O_WRONLY | _O_TEXT);
                if (fd >= 0) {
                    _dup2(fd, _fileno(stderr));
                    _close(fd);
                }
                _setmode(_fileno(stderr), _O_U8TEXT);
                _enableConsoleModeProcessed(win_handle, false);
            }
            clearerr(stderr);
        }
#endif
        if (fileno(stdin) < 0) {
            freopen("NUL", "r", stdin);
            FILE_HANDLE win_handle = GetStdHandle(STD_INPUT_HANDLE);
            if ((win_handle != NULL) && (win_handle != INVALID_HANDLE_VALUE)) {
                int fd = _open_osfhandle((intptr_t)win_handle, _O_TEXT | _O_RDONLY);
                if (fd >= 0) {
                    _dup2(fd, _fileno(stdin));
                    _close(fd);
                }
                _setmode(_fileno(stdin), _O_U8TEXT);
                _enableConsoleModeProcessed(win_handle, true);
            }
            clearerr(stdin);
        }

        needs_stdin_attaching = fileno(stdin) < 0;
        needs_stdout_attaching = fileno(stdout) < 0;
#if !defined(NUITKA_FORCED_STDERR_PATH) && !defined(NUITKA_FORCED_STDERR_NONE_BOOL) &&                                 \
    !defined(NUITKA_FORCED_STDERR_NULL_BOOL)
        needs_stderr_attaching = fileno(stderr) < 0;
#endif
    }

    SECURITY_ATTRIBUTES security_attributes = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};

    if (needs_stdout_attaching) {
        FILE_HANDLE win_handle =
            CreateFileW(L"CONOUT$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                        &security_attributes, OPEN_EXISTING, 0, NULL);
        assert(win_handle != INVALID_HANDLE_VALUE);

        FILE *new_handle = _wfreopen(L"CONOUT$", L"wb", stdout);
        assert(new_handle != NULL);
        // Win32 doesn't allow line buffering.
        setvbuf(stdout, NULL, _IONBF, 0);
        _setmode(_fileno(stdout), _O_U8TEXT);

        _enableConsoleModeProcessed(win_handle, false);
        _enableConsoleModeProcessed((FILE_HANDLE)_get_osfhandle(fileno(stdout)), false);

        BOOL r = SetStdHandle(STD_OUTPUT_HANDLE, win_handle);
        assert(r);
    } else {
        setvbuf(stdout, NULL, _IONBF, 0);
        BOOL r = SetStdHandle(STD_OUTPUT_HANDLE, (HANDLE)_get_osfhandle(fileno(stdout)));
        assert(r);
    }

    if (needs_stderr_attaching) {
        FILE_HANDLE win_handle =
            CreateFileW(L"CONOUT$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                        &security_attributes, OPEN_EXISTING, 0, NULL);

        FILE *new_handle = _wfreopen(L"CONOUT$", L"wb", stderr);
        assert(new_handle != NULL);
        // Win32 doesn't allow line buffering.
        setvbuf(stderr, NULL, _IONBF, 0);
        _setmode(_fileno(stderr), _O_U8TEXT);

        _enableConsoleModeProcessed(win_handle, false);
        _enableConsoleModeProcessed((FILE_HANDLE)_get_osfhandle(fileno(stderr)), false);

        SetStdHandle(STD_ERROR_HANDLE, win_handle);
    } else {
#if !defined(NUITKA_FORCED_STDERR_PATH) && !defined(NUITKA_FORCED_STDERR_NONE_BOOL) &&                                 \
    !defined(NUITKA_FORCED_STDERR_NULL_BOOL)
        setvbuf(stderr, NULL, _IONBF, 0);
        BOOL r = SetStdHandle(STD_ERROR_HANDLE, (HANDLE)_get_osfhandle(fileno(stderr)));
        assert(r);
#endif
    }

    if (needs_stdin_attaching) {
        FILE_HANDLE win_handle =
            CreateFileW(L"CONIN$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                        &security_attributes, OPEN_EXISTING, 0, NULL);

        // Get the current mode of the console input buffer if possible.
        DWORD console_mode = 0;
        GetConsoleMode(win_handle, &console_mode);

        needs_stdin_attaching = (console_mode & 0x100) == 0;

        if (needs_stdin_attaching) {
            FILE *new_handle = _wfreopen(L"CONIN$", L"rb", stdin);
            assert(new_handle != NULL);
            assert(new_handle == stdin);
            _setmode(_fileno(stdin), _O_U8TEXT);

            _enableConsoleModeProcessed(win_handle, true);
            _enableConsoleModeProcessed((FILE_HANDLE)_get_osfhandle(fileno(stdin)), true);

            SetStdHandle(STD_INPUT_HANDLE, win_handle);
        }
    } else {
        BOOL r = SetStdHandle(STD_INPUT_HANDLE, (HANDLE)_get_osfhandle(fileno(stdin)));
        assert(r);
    }

    NUITKA_PRINTF_TRACE("inheritAttachedConsole(): Attachable: %s\n", (is_attachable ? "true" : "false"));
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
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
