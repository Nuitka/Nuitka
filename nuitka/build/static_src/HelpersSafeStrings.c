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
/* This helpers are used to interact safely with buffers to not overflow.

   Currently this is used for char and wchar_t string buffers and shared
   between onefile bootstrap for Windows, plugins and Nuitka core, but
   should not use any Python level functionality.
*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#if defined(_WIN32)
#include "windows.h"
#endif
#include <stdbool.h>
#endif

#if defined(_WIN32)
#include <Shlwapi.h>
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

void appendStringSafe(char *buffer, char const *source, size_t buffer_size) {
    if (strlen(source) + strlen(buffer) >= buffer_size) {
        abort();
    }
    strcat(buffer, source);
}

void appendCharSafe(char *buffer, char c, size_t buffer_size) {
    char source[2] = {c, 0};

    appendStringSafe(buffer, source, buffer_size);
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
#include <shellapi.h>

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
                    int argc;
                    wchar_t **args = CommandLineToArgvW(GetCommandLineW(), &argc);

                    appendWStringSafeW(target, args[0], buffer_size);
#else
                    if (!GetModuleFileNameW(NULL, target, (DWORD)buffer_size)) {
                        return false;
                    }
#endif
                } else if (wcsicmp(var_name, L"PID") == 0) {
                    char pid_buffer[128];
                    snprintf(pid_buffer, sizeof(pid_buffer), "%d", GetCurrentProcessId());

                    appendStringSafeW(target, pid_buffer, buffer_size);
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
                } else if (strcasecmp(var_name, "TIME") == 0) {
                    char time_buffer[1024];

                    struct timeval current_time;
                    gettimeofday(&current_time, NULL);

                    snprintf(time_buffer, sizeof(time_buffer), "%ld_%ld", current_time.tv_sec, current_time.tv_usec);

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