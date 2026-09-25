//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#define unlikely(x) (x)
#endif

#include "nuitka/safe_string_ops.h"

#include <ctype.h>
#include <wctype.h>

#if !defined(_WIN32)
// For 'newlocale', 'uselocale', 'freelocale'.
#include <locale.h>
#if defined(__APPLE__) || defined(__FreeBSD__) || defined(__NetBSD__)
// For 'mbstowcs_l' BSD/Darwin extension.
#include <xlocale.h>
#endif
#endif

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

#if defined(__APPLE__) || defined(__FreeBSD__) || defined(__NetBSD__)
    // On macOS/FreeBSD/NetBSD filesystem paths are always UTF-8, independent
    // of the process locale.
    static locale_t utf8_locale = (locale_t)0;

    if (unlikely(utf8_locale == (locale_t)0)) {
        utf8_locale = newlocale(LC_CTYPE_MASK, "UTF-8", (locale_t)0);

        if (unlikely(utf8_locale == (locale_t)0)) {
            abort();
        }
    }

    size_t converted = mbstowcs_l(target, source, buffer_size, utf8_locale);

    if (unlikely(converted == (size_t)-1 || converted >= buffer_size)) {
        abort();
    }
#elif !defined(_WIN32)
    // On other platforms (e.g. Linux) filesystem paths are typically UTF-8,
    // but the process locale may be "C". Respect the environment locale first
    // (LC_CTYPE/LANG) to handle legacy single-byte encodings, then fall back
    // to a fixed UTF-8 locale for UTF-8 paths in C locale.
    bool converted = false;

    locale_t env_locale = newlocale(LC_CTYPE_MASK, "", (locale_t)0);
    if (env_locale != (locale_t)0) {
        locale_t old_locale = uselocale(env_locale);
        size_t res = mbstowcs(target, source, buffer_size);
        uselocale(old_locale);
        freelocale(env_locale);

        if (res != (size_t)-1 && res < buffer_size) {
            converted = true;
        }
    }

    if (!converted) {
        static locale_t utf8_locale = (locale_t)0;
        static int utf8_locale_failed = 0;

        if (!utf8_locale_failed && utf8_locale == (locale_t)0) {
            utf8_locale = newlocale(LC_CTYPE_MASK, "C.UTF-8", (locale_t)0);
            if (utf8_locale == (locale_t)0) {
                utf8_locale = newlocale(LC_CTYPE_MASK, "C.utf8", (locale_t)0);
            }
            if (utf8_locale == (locale_t)0) {
                utf8_locale = newlocale(LC_CTYPE_MASK, "UTF-8", (locale_t)0);
            }
            if (utf8_locale == (locale_t)0) {
                utf8_locale_failed = 1;
            }
        }

        if (!utf8_locale_failed) {
            locale_t old_locale = uselocale(utf8_locale);
            size_t res = mbstowcs(target, source, buffer_size);
            uselocale(old_locale);

            if (res != (size_t)-1 && res < buffer_size) {
                converted = true;
            }
        }
    }

    if (!converted) {
        abort();
    }
#else
    // On Windows the binary directory is already wide-char; this fallback
    // is for other callers (e.g. env vars) which are ASCII-only.
    while (*source != 0) {
        appendCharSafeW(target, *source, buffer_size);
        target++;
        source++;
        buffer_size -= 1;
    }
#endif
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
    LPTSTR err_buffer;

    DWORD res =
        FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL,
                      error_code, MAKELANGID(LANG_ENGLISH, SUBLANG_ENGLISH_US), (LPTSTR)&err_buffer, 0, NULL);
    assert(res != 0);

    while (res > 0 && (err_buffer[res - 1] == '\r' || err_buffer[res - 1] == '\n')) {
        res -= 1;
        err_buffer[res] = 0;
    }

    fprintf(stderr, "%s ([Error " ERROR_CODE_FORMAT_STR "] %s)\n", message, error_code, err_buffer);
#else
    fprintf(stderr, "%s: %s\n", message, strerror(error_code));
#endif
}

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
