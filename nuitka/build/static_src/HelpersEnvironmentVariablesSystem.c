//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Helpers for working with environment variables in a portable way. This mainly
// abstracts the string type differences between Win32 and non-Win32 environment
// variables.

#include "nuitka/environment_variables_system.h"
#include "nuitka/safe_string_ops.h"

#if defined(_WIN32)

environment_char_t const *getEnvironmentVariableW(wchar_t const *name) {
    // Max size for environment variables according to docs.
    wchar_t buffer[32768];
    buffer[0] = 0;

    // Size must be in bytes apparently, not in characters. Cannot be larger anyway.
    DWORD res = GetEnvironmentVariableW(name, buffer, 65536);

    if (res == 0 || res > sizeof(buffer)) {
        return NULL;
    }

    return wcsdup(buffer);
}

environment_char_t const *getEnvironmentVariable(char const *name) {
    wchar_t name_wide[40];
    name_wide[0] = 0;
    appendStringSafeW(name_wide, name, sizeof(name_wide) / sizeof(wchar_t));

    return getEnvironmentVariableW(name_wide);
}

// Update the C runtime environment too, since "getenv" uses it and does not
// see changes done with "SetEnvironmentVariableW".
static void updateCRTEnvironmentVariable(char const *name, wchar_t const *value) {
    wchar_t name_wide[64];
    name_wide[0] = 0;
    appendStringSafeW(name_wide, name, sizeof(name_wide) / sizeof(wchar_t));

    size_t name_length = wcslen(name_wide);
    size_t value_length = wcslen(value);

    wchar_t *env_string = (wchar_t *)malloc((name_length + value_length + 2) * sizeof(wchar_t));
    assert(env_string != NULL);

    memcpy(env_string, name_wide, name_length * sizeof(wchar_t));
    env_string[name_length] = L'=';
    memcpy(env_string + name_length + 1, value, (value_length + 1) * sizeof(wchar_t));

    _wputenv(env_string);

    // When Nuitka is compiled with a different C runtime than Python, e.g.
    // MinGW against an official UCRT based Python, the environment of the
    // Python runtime must be updated as well, since it uses "getenv".
    {
        static wchar_t const *const crt_names[] = {
            L"ucrtbase.dll", L"msvcrt.dll",   L"msvcr80.dll",  L"msvcr90.dll",
            L"msvcr100.dll", L"msvcr110.dll", L"msvcr120.dll",
        };

        typedef int(__cdecl * wputenv_function_t)(wchar_t const *);

        for (size_t i = 0; i < sizeof(crt_names) / sizeof(crt_names[0]); i++) {
            HMODULE crt_module = GetModuleHandleW(crt_names[i]);

            if (crt_module != NULL) {
                // Avoid a cast between incompatible function types, which
                // newer compilers warn about.
                union {
                    FARPROC as_proc;
                    wputenv_function_t as_function;
                } function;

                function.as_proc = GetProcAddress(crt_module, "_wputenv");

                if (function.as_function != NULL) {
                    function.as_function(env_string);
                }
            }
        }
    }

    // Intentionally not freed, a C runtime might keep a pointer to it.
}

void setEnvironmentVariable(char const *name, environment_char_t const *value) {
    assert(name != NULL);
    assert(value != NULL);

    wchar_t name_wide[40];
    name_wide[0] = 0;
    appendStringSafeW(name_wide, name, sizeof(name_wide) / sizeof(wchar_t));

    DWORD res = SetEnvironmentVariableW(name_wide, value);
    assert(wcscmp(getEnvironmentVariable(name), value) == 0);
    assert(res != 0);

    updateCRTEnvironmentVariable(name, value);
}

void unsetEnvironmentVariable(char const *name) {
    wchar_t name_wide[40];
    name_wide[0] = 0;
    appendStringSafeW(name_wide, name, sizeof(name_wide) / sizeof(wchar_t));

    DWORD res = SetEnvironmentVariableW(name_wide, NULL);
    assert(res != 0);

    updateCRTEnvironmentVariable(name, L"");
}

#else

environment_char_t const *getEnvironmentVariable(char const *name) { return getenv(name); }

void setEnvironmentVariable(char const *name, environment_char_t const *value) { setenv(name, value, 1); }

void unsetEnvironmentVariable(char const *name) { unsetenv(name); }

#endif

void setEnvironmentVariableFromLong(char const *name, long value) {
    char buffer[128];
    snprintf(buffer, sizeof(buffer), "%ld", value);

#if defined(_WIN32)
    wchar_t buffer2[128];
    buffer2[0] = 0;
    appendStringSafeW(buffer2, buffer, 128);

    setEnvironmentVariable(name, buffer2);
#else
    setEnvironmentVariable(name, buffer);
#endif
}

bool getEnvironmentVariableValueAsLong(environment_char_t const *value, long *result) {
#if defined(_WIN32)
    errno = 0;
    wchar_t *endptr = NULL;
    long parsed = wcstol(value, &endptr, 10);

    if (errno == ERANGE || endptr == value || *endptr != '\0') {
        return false;
    }

    *result = parsed;
#else
    errno = 0;
    char *endptr = NULL;
    long parsed = strtol(value, &endptr, 10);

    if (errno == ERANGE || endptr == value || *endptr != '\0') {
        return false;
    }

    *result = parsed;
#endif
    return true;
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
