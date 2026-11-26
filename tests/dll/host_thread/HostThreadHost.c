//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// C host example invoking 'run_code' on a dedicated native worker thread
// (with argc=0, argv=NULL and an explicit 'dll_filename'), interacting with
// the C host's main thread while Python runs, and continuing in C after
// 'run_code' finalizes Python and returns without terminating the process.

#define _CRT_SECURE_NO_WARNINGS

#if !defined(_WIN32) && !defined(__APPLE__) && !defined(__FreeBSD__) && !defined(__NetBSD__) &&                        \
    !defined(__OpenBSD__) && !defined(__DragonFly__)
#define _POSIX_C_SOURCE 200809L
#endif

#if defined(_WIN32)
#include <windows.h>
#else
#include <dlfcn.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#if defined(__APPLE__)
#include <mach-o/dyld.h>
#endif
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include "custom_host_dll.h"

#if defined(_WIN32)

static wchar_t g_handshake_dir[MAX_PATH];
static wchar_t g_dll_path[MAX_PATH];
static nuitka_dll_run_code_fn g_run_code_fn = NULL;
static int g_python_exit_code = -999;

static DWORD WINAPI pythonRunnerThread(LPVOID param) {
    (void)param;

    g_python_exit_code = (*g_run_code_fn)(0, NULL, g_dll_path, false);
    return 0;
}

static bool answerPythonHandshake(void) {
    wchar_t ping_path[MAX_PATH];
    wchar_t pong_tmp_path[MAX_PATH];
    wchar_t pong_path[MAX_PATH];

    _snwprintf(ping_path, MAX_PATH, L"%ls\\handshake.ping", g_handshake_dir);
    _snwprintf(pong_tmp_path, MAX_PATH, L"%ls\\handshake.pong.tmp", g_handshake_dir);
    _snwprintf(pong_path, MAX_PATH, L"%ls\\handshake.pong", g_handshake_dir);

    for (int attempt = 0; attempt < 1000; attempt++) {
        if (GetFileAttributesW(ping_path) != INVALID_FILE_ATTRIBUTES) {
            FILE *pong_file = _wfopen(pong_tmp_path, L"w");
            if (pong_file == NULL) {
                return false;
            }
            fputs("PONG\n", pong_file);
            fclose(pong_file);
            return MoveFileExW(pong_tmp_path, pong_path, MOVEFILE_REPLACE_EXISTING) != 0;
        }

        Sleep(10);
    }

    return false;
}

int wmain(int argc, wchar_t **argv) {
    bool verify_reentry_rejected = (argc == 2 && wcscmp(argv[1], L"--verify-reentry-rejected") == 0);

    DWORD len = GetModuleFileNameW(NULL, g_handshake_dir, MAX_PATH);
    if (len == 0 || len >= MAX_PATH) {
        fprintf(stderr, "Failed to query host executable path.\n");
        return EXIT_FAILURE;
    }

    wchar_t *last_sep = wcsrchr(g_handshake_dir, L'\\');
    if (last_sep != NULL) {
        *last_sep = L'\0';
    }

    if (_wputenv_s(L"NUITKA_DLL_HANDSHAKE_DIR", g_handshake_dir) != 0) {
        fprintf(stderr, "_wputenv_s failed.\n");
        return EXIT_FAILURE;
    }

    wchar_t dist_dir[MAX_PATH];
    _snwprintf(dist_dir, MAX_PATH, L"%ls\\%ls", g_handshake_dir, NUITKA_DLL_DIST_DIR);
    _snwprintf(g_dll_path, MAX_PATH, L"%ls\\%ls", g_handshake_dir, NUITKA_DLL_RELATIVE_PATH);

    if (AddDllDirectory(dist_dir) == 0) {
        fprintf(stderr, "AddDllDirectory failed (%lu).\n", GetLastError());
        return EXIT_FAILURE;
    }

    if (!SetDllDirectoryW(g_handshake_dir)) {
        fprintf(stderr, "SetDllDirectoryW failed (%lu).\n", GetLastError());
        return EXIT_FAILURE;
    }

    HMODULE dll_handle =
        LoadLibraryExW(g_dll_path, NULL,
                       LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32 | LOAD_LIBRARY_SEARCH_USER_DIRS);
    if (dll_handle == NULL) {
        fprintf(stderr, "LoadLibraryExW failed (%lu).\n", GetLastError());
        return EXIT_FAILURE;
    }

    union {
        FARPROC as_proc;
        nuitka_dll_run_code_fn as_function;
    } run_code_symbol;

    run_code_symbol.as_proc = GetProcAddress(dll_handle, "run_code");
    if (run_code_symbol.as_function == NULL) {
        fprintf(stderr, "Could not locate 'run_code' export.\n");
        return EXIT_FAILURE;
    }
    g_run_code_fn = run_code_symbol.as_function;

    HANDLE python_thread = CreateThread(NULL, 0, pythonRunnerThread, NULL, 0, NULL);
    if (python_thread == NULL) {
        fprintf(stderr, "CreateThread failed (%lu).\n", GetLastError());
        return EXIT_FAILURE;
    }

    bool handshake_ok = answerPythonHandshake();
    WaitForSingleObject(python_thread, INFINITE);
    CloseHandle(python_thread);

    if (!handshake_ok) {
        fprintf(stderr, "Host handshake failed.\n");
        return EXIT_FAILURE;
    }

    wchar_t current_dll_dir[MAX_PATH];
    DWORD current_dll_dir_len = GetDllDirectoryW(MAX_PATH, current_dll_dir);
    if (current_dll_dir_len == 0 || wcscmp(current_dll_dir, g_handshake_dir) != 0) {
        fprintf(stderr, "Host SetDllDirectoryW state was clobbered ('%ls' != '%ls').\n", current_dll_dir,
                g_handshake_dir);
        return EXIT_FAILURE;
    }

    printf("Host continuing after Python thread returned: %d\n", g_python_exit_code);
    fflush(stdout);

    if (verify_reentry_rejected) {
        int second_false = (*g_run_code_fn)(0, NULL, g_dll_path, false);
        int second_true = (*g_run_code_fn)(0, NULL, g_dll_path, true);
        if (second_false != -1 || second_true != -1) {
            fprintf(stderr, "Expected repeated run_code calls to return -1, got %d and %d.\n", second_false,
                    second_true);
            return EXIT_FAILURE;
        }
    }

    return g_python_exit_code;
}

#else

static char g_handshake_dir[4096];
static char g_dll_path[4096];
static nuitka_dll_run_code_fn g_run_code_fn = NULL;
static int g_python_exit_code = -999;

static void getHostDirectory(char const *argv0, char *buffer, size_t buffer_size) {
    buffer[0] = '\0';

#if defined(__APPLE__)
    uint32_t size = (uint32_t)buffer_size;
    if (_NSGetExecutablePath(buffer, &size) != 0) {
        buffer[0] = '\0';
    }
#elif defined(__linux__)
    ssize_t len = readlink("/proc/self/exe", buffer, buffer_size - 1);
    if (len > 0) {
        buffer[len] = '\0';
    }
#endif

    if (buffer[0] == '\0' && argv0 != NULL) {
        snprintf(buffer, buffer_size, "%s", argv0);
    }

    char *last_sep = strrchr(buffer, '/');
    if (last_sep != NULL) {
        *last_sep = '\0';
    } else {
        snprintf(buffer, buffer_size, ".");
    }
}

static void *pythonRunnerThread(void *param) {
    (void)param;

    g_python_exit_code = (*g_run_code_fn)(0, NULL, g_dll_path, false);
    return NULL;
}

static bool answerPythonHandshake(void) {
    char ping_path[4096];
    char pong_tmp_path[4096];
    char pong_path[4096];

    snprintf(ping_path, sizeof(ping_path), "%s/handshake.ping", g_handshake_dir);
    snprintf(pong_tmp_path, sizeof(pong_tmp_path), "%s/handshake.pong.tmp", g_handshake_dir);
    snprintf(pong_path, sizeof(pong_path), "%s/handshake.pong", g_handshake_dir);

    struct timespec sleep_spec;
    sleep_spec.tv_sec = 0;
    sleep_spec.tv_nsec = 10 * 1000 * 1000;

    for (int attempt = 0; attempt < 1000; attempt++) {
        if (access(ping_path, F_OK) == 0) {
            FILE *pong_file = fopen(pong_tmp_path, "w");
            if (pong_file == NULL) {
                return false;
            }
            fputs("PONG\n", pong_file);
            fclose(pong_file);
            return rename(pong_tmp_path, pong_path) == 0;
        }

        nanosleep(&sleep_spec, NULL);
    }

    return false;
}

int main(int argc, char **argv) {
    bool verify_reentry_rejected = (argc == 2 && strcmp(argv[1], "--verify-reentry-rejected") == 0);

    getHostDirectory(argc > 0 ? argv[0] : NULL, g_handshake_dir, sizeof(g_handshake_dir));

    if (setenv("NUITKA_DLL_HANDSHAKE_DIR", g_handshake_dir, 1) != 0) {
        fprintf(stderr, "setenv failed.\n");
        return EXIT_FAILURE;
    }

    snprintf(g_dll_path, sizeof(g_dll_path), "%s/%s", g_handshake_dir, NUITKA_DLL_RELATIVE_PATH);

    void *dll_handle = dlopen(g_dll_path, RTLD_LOCAL | RTLD_NOW);
    if (dll_handle == NULL) {
        char const *error = dlerror();
        fprintf(stderr, "dlopen failed: %s\n", error != NULL ? error : "unknown error");
        return EXIT_FAILURE;
    }

    g_run_code_fn = (nuitka_dll_run_code_fn)dlsym(dll_handle, "run_code");
    if (g_run_code_fn == NULL) {
        fprintf(stderr, "Could not locate 'run_code' export.\n");
        return EXIT_FAILURE;
    }

    // macOS and musl give new pthreads small stacks (512 KiB / 128 KiB) by
    // default, so request an 8 MiB stack matching a typical main thread.
    pthread_attr_t thread_attr;
    pthread_attr_init(&thread_attr);
    pthread_attr_setstacksize(&thread_attr, 8 * 1024 * 1024);

    pthread_t python_thread;
    if (pthread_create(&python_thread, &thread_attr, pythonRunnerThread, NULL) != 0) {
        pthread_attr_destroy(&thread_attr);
        fprintf(stderr, "pthread_create failed.\n");
        return EXIT_FAILURE;
    }
    pthread_attr_destroy(&thread_attr);

    bool handshake_ok = answerPythonHandshake();
    pthread_join(python_thread, NULL);

    if (!handshake_ok) {
        fprintf(stderr, "Host handshake failed.\n");
        return EXIT_FAILURE;
    }

    printf("Host continuing after Python thread returned: %d\n", g_python_exit_code);
    fflush(stdout);

    if (verify_reentry_rejected) {
        int second_false = (*g_run_code_fn)(0, NULL, g_dll_path, false);
        int second_true = (*g_run_code_fn)(0, NULL, g_dll_path, true);
        if (second_false != -1 || second_true != -1) {
            fprintf(stderr, "Expected repeated run_code calls to return -1, got %d and %d.\n", second_false,
                    second_true);
            return EXIT_FAILURE;
        }
    }

    return g_python_exit_code;
}

#endif

//     Python test originally created or extracted from other peoples work. The
//     parts from me are licensed as below. It is at least Free Software where
//     it's copied from other people. In these cases, that will normally be
//     indicated.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
