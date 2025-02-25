//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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
#include <stdio.h>
#endif

#include "nuitka/safe_string_ops.h"

#include <ctype.h>
#include <wctype.h>

void copyStringSafe(char *buffer, char const *source, size_t buffer_size) {
    if (strlen(source) >= buffer_size) {
        abort();
    }

    if (buffer != source) {
        strcpy(buffer, source);
    }
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
    if (unlikely(source == NULL)) {
        abort();
    }

    while (*target != 0) {
        target++;
        buffer_size -= 1;
    }

    while (*source != 0) {
        if (unlikely(buffer_size < 1)) {
            abort();
        }

        *target++ = *source++;
        buffer_size -= 1;
    }

    *target = 0;
}

void appendWCharSafeW(wchar_t *target, wchar_t c, size_t buffer_size) {
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

void appendCharSafeW(wchar_t *target, char c, size_t buffer_size) {
    char buffer_c[2] = {c, 0};
    wchar_t wide_buffer_c[2];

    size_t res = mbstowcs(wide_buffer_c, buffer_c, 2);
    if (res != 1) {
        abort();
    }

    appendWCharSafeW(target, wide_buffer_c[0], buffer_size);
}

void appendStringSafeW(wchar_t *target, char const *source, size_t buffer_size) {
    while (*target != 0) {
        target++;
        buffer_size -= 1;
    }

    while (*source != 0) {
        appendCharSafeW(target, *source, buffer_size);
        target++;
        source++;
        buffer_size -= 1;
    }
}

void checkWStringNumber(wchar_t const *value) {
    if (unlikely(value == NULL || *value == 0)) {
        abort();
    }

    while (*value) {
        if (!iswdigit(*value)) {
            abort();
        }

        value++;
    }
}

void checkStringNumber(char const *value) {
    if (unlikely(value == NULL || *value == 0)) {
        abort();
    }

    while (*value) {
        if (!isdigit(*value)) {
            abort();
        }

        value++;
    }
}

void printOSErrorMessage(char const *message, error_code_t error_code) {
#if defined(_WIN32)
    LPCTSTR err_buffer;

    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL,
                  error_code, MAKELANGID(LANG_ENGLISH, SUBLANG_ENGLISH_US), (LPTSTR)&err_buffer, 0, NULL);

    fprintf(stderr, "%s ([Error " ERROR_CODE_FORMAT_STR "] %s)\n", message, error_code, err_buffer);
#else
    fprintf(stderr, "%s: %s\n", message, strerror(error_code));
#endif
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
