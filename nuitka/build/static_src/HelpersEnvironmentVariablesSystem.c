//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Helpers for working with environment variables in a portable way. This mainly
// abstracts the string type differences between Win32 and non-Win32 environment
// variables.

#include "nuitka/environment_variables_system.h"
#include "nuitka/safe_string_ops.h"

#if defined(_WIN32)

environment_char_t const *getEnvironmentVariable(char const *name) {
    // Max size for environment variables according to docs.
    wchar_t buffer[32768];
    buffer[0] = 0;

    wchar_t name_wide[40];
    name_wide[0] = 0;
    appendStringSafeW(name_wide, name, sizeof(name_wide) / sizeof(wchar_t));

    // Size must be in bytes apparently, not in characters. Cannot be larger anyway.
    DWORD res = GetEnvironmentVariableW(name_wide, buffer, 65536);

    if (res == 0 || res > sizeof(buffer)) {
        return NULL;
    }

    return wcsdup(buffer);
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
}

void unsetEnvironmentVariable(char const *name) {
    wchar_t name_wide[40];
    name_wide[0] = 0;
    appendStringSafeW(name_wide, name, sizeof(name_wide) / sizeof(wchar_t));

    DWORD res = SetEnvironmentVariableW(name_wide, NULL);

    assert(res != 0);
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
