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
/* This helpers are used to interact safely with buffers to not overflow.

   Currently this is used for char and wchar_t string buffers and shared
   between onefile bootstrap for Windows, plugins and Nuitka core, but
   should not use any Python level functionality.
*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#if defined(_WIN32)
#include <windows.h>
#endif
#include <stdbool.h>
#endif

void copyStringSafe(char *buffer, char const *source, size_t buffer_size) {
    if (strlen(source) >= buffer_size) {
        abort();
    }
    strcpy(buffer, source);
}

void copyStringSafeN(char *buffer, char const *source, size_t n, size_t buffer_size) {
    if (n >= buffer_size - 1) {
        abort();
    }
    strncpy(buffer, source, n);
    buffer[n] = 0;
}

void copyStringSafeW(wchar_t *buffer, wchar_t const *source, size_t buffer_size) {
    while (*source != 0) {
        if (buffer_size < 1) {
            abort();
        }

        *buffer++ = *source++;
        buffer_size -= 1;
    }

    *buffer = 0;
}

void appendStringSafe(char *target, char const *source, size_t buffer_size) {
    if (strlen(source) + strlen(target) >= buffer_size) {
        abort();
    }
    strcat(target, source);
}

void appendCharSafe(char *target, char c, size_t buffer_size) {
    char source[2] = {c, 0};

    appendStringSafe(target, source, buffer_size);
}

void appendWStringSafeW(wchar_t *target, wchar_t const *source, size_t buffer_size) {
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

void appendCharSafeW(wchar_t *target, char c, size_t buffer_size) {
    while (*target != 0) {
        target++;
        buffer_size -= 1;
    }

    if (buffer_size < 1) {
        abort();
    }

    target += wcslen(target);
    char buffer_c[2] = {c, 0};
    size_t res = mbstowcs(target, buffer_c, 2);
    assert(res == 1);
}

void appendStringSafeW(wchar_t *target, char const *source, size_t buffer_size) {
    while (*target != 0) {
        target++;
        buffer_size -= 1;
    }

    while (*source != 0) {
        appendCharSafeW(target, *source, buffer_size);
        source++;
        buffer_size -= 1;
    }
}

#if defined(_WIN32)

// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>

#include <shlobj.h>
#include <shlwapi.h>

// For less complete C compilers.
#ifndef CSIDL_LOCAL_APPDATA
#define CSIDL_LOCAL_APPDATA 28
#endif
#ifndef CSIDL_PROFILE
#define CSIDL_PROFILE 40
#endif

static bool appendStringWCSIDLPath(wchar_t *target, int csidl_id, size_t buffer_size) {
    wchar_t path_buffer[MAX_PATH];

    int res = SHGetFolderPathW(NULL, csidl_id, NULL, 0, path_buffer);

    if (res != S_OK) {
        return false;
    }

    appendWStringSafeW(target, path_buffer, buffer_size);

    return true;
}

bool expandTemplatePathW(wchar_t *target, wchar_t const *source, size_t buffer_size) {
    target[0] = 0;

    wchar_t var_name[1024];
    wchar_t *w = NULL;

    while (*source != 0) {
        if (*source == '%') {
            if (w == NULL) {
                w = var_name;
                *w = 0;

                source++;

                continue;
            } else {
                *w = 0;

                if (wcsicmp(var_name, L"TEMP") == 0) {
                    GetTempPathW((DWORD)buffer_size, target);
                } else if (wcsicmp(var_name, L"PROGRAM") == 0) {
#if _NUITKA_ONEFILE_TEMP == 1
                    appendWStringSafeW(target, __wargv[0], buffer_size);
#else
                    if (!GetModuleFileNameW(NULL, target, (DWORD)buffer_size)) {
                        return false;
                    }
#endif
                } else if (wcsicmp(var_name, L"PID") == 0) {
                    char pid_buffer[128];
                    snprintf(pid_buffer, sizeof(pid_buffer), "%d", GetCurrentProcessId());

                    appendStringSafeW(target, pid_buffer, buffer_size);
                } else if (wcsicmp(var_name, L"HOME") == 0) {
                    if (appendStringWCSIDLPath(target, CSIDL_PROFILE, buffer_size) == false) {
                        return false;
                    }
                } else if (wcsicmp(var_name, L"CACHE_DIR") == 0) {
                    if (appendStringWCSIDLPath(target, CSIDL_LOCAL_APPDATA, buffer_size) == false) {
                        return false;
                    }
#ifdef NUITKA_COMPANY_NAME
                } else if (wcsicmp(var_name, L"COMPANY") == 0) {
                    appendWStringSafeW(target, L"" NUITKA_COMPANY_NAME, buffer_size);
#endif
#ifdef NUITKA_PRODUCT_NAME
                } else if (wcsicmp(var_name, L"PRODUCT") == 0) {
                    appendWStringSafeW(target, L"" NUITKA_PRODUCT_NAME, buffer_size);
#endif
#ifdef NUITKA_VERSION_COMBINED
                } else if (wcsicmp(var_name, L"VERSION") == 0) {
                    appendWStringSafeW(target, L"" NUITKA_VERSION_COMBINED, buffer_size);
#endif
                } else if (wcsicmp(var_name, L"TIME") == 0) {
                    char time_buffer[1024];

                    __int64 time = 0;
                    assert(sizeof(time) == sizeof(FILETIME));
                    GetSystemTimeAsFileTime((LPFILETIME)&time);

                    snprintf(time_buffer, sizeof(time_buffer), "%lld", time);

                    appendStringSafeW(target, time_buffer, buffer_size);
                } else {
                    return false;
                }

                // Skip over appended stuff.
                while (*target) {
                    target++;
                    buffer_size -= 1;
                }

                w = NULL;
                source++;

                continue;
            }
        }

        if (w != NULL) {
            *w++ = *source++;
            continue;
        }

        if (buffer_size < 1) {
            return false;
        }

        *target++ = *source++;
        buffer_size -= 1;
    }

    *target = 0;

    return true;
}

#else

#include <pwd.h>
#include <strings.h>
#include <sys/time.h>

bool expandTemplatePath(char *target, char const *source, size_t buffer_size) {
    target[0] = 0;

    char var_name[1024];
    char *w = NULL;

    while (*source != 0) {
        if (*source == '%') {
            if (w == NULL) {
                w = var_name;
                *w = 0;

                source++;

                continue;
            } else {
                *w = 0;

                if (strcasecmp(var_name, "TEMP") == 0) {
                    char const *tmp_dir = getenv("TMPDIR");
                    if (tmp_dir == NULL) {
                        tmp_dir = "/tmp";
                    }

                    appendStringSafe(target, tmp_dir, buffer_size);
                } else if (strcasecmp(var_name, "PROGRAM") == 0) {
                    // Not implemented outside of Windows yet.
                    return false;
                } else if (strcasecmp(var_name, "PID") == 0) {
                    char pid_buffer[128];

                    snprintf(pid_buffer, sizeof(pid_buffer), "%d", getpid());

                    appendStringSafe(target, pid_buffer, buffer_size);
                } else if (strcasecmp(var_name, "HOME") == 0) {
                    char const *home_path = getenv("HOME");

                    if (home_path == NULL) {
                        struct passwd *pw_data = getpwuid(getuid());

                        if (unlikely(pw_data == NULL)) {
                            return false;
                        }

                        home_path = pw_data->pw_dir;
                    }

                    appendStringSafe(target, home_path, buffer_size);
                } else if (strcasecmp(var_name, "CACHE_DIR") == 0) {
                    if (expandTemplatePath(target, "HOME", buffer_size - strlen(target)) == false) {
                        return false;
                    }

                    appendCharSafe(target, '/', buffer_size);
                    appendStringSafe(target, ".cache", buffer_size);
#ifdef NUITKA_COMPANY_NAME
                } else if (strcasecmp(var_name, "COMPANY") == 0) {
                    appendStringSafe(target, NUITKA_COMPANY_NAME, buffer_size);
#endif
#ifdef NUITKA_PRODUCT_NAME
                } else if (strcasecmp(var_name, "PRODUCT") == 0) {
                    appendStringSafe(target, NUITKA_PRODUCT_NAME, buffer_size);
#endif
#ifdef NUITKA_VERSION_COMBINED
                } else if (strcasecmp(var_name, "VERSION") == 0) {
                    appendStringSafe(target, NUITKA_VERSION_COMBINED, buffer_size);
#endif
                } else if (strcasecmp(var_name, "TIME") == 0) {
                    char time_buffer[1024];

                    struct timeval current_time;
                    gettimeofday(&current_time, NULL);
                    snprintf(time_buffer, sizeof(time_buffer), "%ld_%ld", current_time.tv_sec,
                             (long)current_time.tv_usec);

                    appendStringSafe(target, time_buffer, buffer_size);
                } else {
                    return false;
                }

                // Skip over appended stuff.
                while (*target) {
                    target++;
                    buffer_size -= 1;
                }

                w = NULL;
                source++;

                continue;
            }
        }

        if (w != NULL) {
            *w++ = *source++;
            continue;
        }

        if (buffer_size < 1) {
            return false;
        }

        *target++ = *source++;
        buffer_size -= 1;
    }

    *target = 0;

    return true;
}

#endif