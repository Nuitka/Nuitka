//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Basic C host example for loading and running a Nuitka '--mode=dll' build.
//
// Includes the Nuitka-generated 'BasicDllMain.h' header, expects
// 'BasicDllMain.dist' next to the compiled host executable, and invokes
// 'run_code' passing NULL for 'dll_filename' so Nuitka resolves the library
// path automatically.

#define _CRT_SECURE_NO_WARNINGS

#if !defined(_WIN32) && !defined(__APPLE__) && !defined(__FreeBSD__) && !defined(__NetBSD__) &&                        \
    !defined(__OpenBSD__) && !defined(__DragonFly__)
#define _POSIX_C_SOURCE 200809L
#endif

#if defined(_WIN32)
#include <windows.h>
#else
#include <dlfcn.h>
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

#include "BasicDllMain.h"

#if defined(_WIN32)

int wmain(int argc, wchar_t **argv) {
    wchar_t host_dir[MAX_PATH];
    DWORD len = GetModuleFileNameW(NULL, host_dir, MAX_PATH);
    if (len == 0 || len >= MAX_PATH) {
        fprintf(stderr, "Failed to query host executable path.\n");
        return EXIT_FAILURE;
    }

    wchar_t *last_sep = wcsrchr(host_dir, L'\\');
    if (last_sep != NULL) {
        *last_sep = L'\0';
    }

    wchar_t dist_dir[MAX_PATH];
    wchar_t dll_path[MAX_PATH];
    _snwprintf(dist_dir, MAX_PATH, L"%ls\\%ls", host_dir, NUITKA_DLL_DIST_DIR);
    _snwprintf(dll_path, MAX_PATH, L"%ls\\%ls", host_dir, NUITKA_DLL_RELATIVE_PATH);

    if (AddDllDirectory(dist_dir) == 0) {
        fprintf(stderr, "AddDllDirectory failed (%lu).\n", GetLastError());
        return EXIT_FAILURE;
    }

    HMODULE dll_handle =
        LoadLibraryExW(dll_path, NULL,
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

    return (*run_code_symbol.as_function)(argc, argv, NULL, false);
}

#else

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

int main(int argc, char **argv) {
    char host_dir[4096];
    getHostDirectory(argc > 0 ? argv[0] : NULL, host_dir, sizeof(host_dir));

    char dll_path[4096];
    snprintf(dll_path, sizeof(dll_path), "%s/%s", host_dir, NUITKA_DLL_RELATIVE_PATH);

    void *dll_handle = dlopen(dll_path, RTLD_LOCAL | RTLD_NOW);
    if (dll_handle == NULL) {
        char const *error = dlerror();
        fprintf(stderr, "dlopen failed: %s\n", error != NULL ? error : "unknown error");
        return EXIT_FAILURE;
    }

    nuitka_dll_run_code_fn run_code_ptr = (nuitka_dll_run_code_fn)dlsym(dll_handle, "run_code");
    if (run_code_ptr == NULL) {
        fprintf(stderr, "Could not locate 'run_code' export.\n");
        return EXIT_FAILURE;
    }

    return (*run_code_ptr)(argc, argv, NULL, false);
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
