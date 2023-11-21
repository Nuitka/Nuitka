//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

// Helpers for working with environment variables in a portable way. This mainly
// abstracts the string type differences between Win32 and non-Win32 environment
// variables.

#include "nuitka/environment_variables.h"

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

void undoEnvironmentVariable(PyThreadState *tstate, char const *variable_name, environment_char_t const *old_value) {
    PyObject *os_module = IMPORT_HARD_OS();
    CHECK_OBJECT(os_module);

    PyObject *os_environ = PyObject_GetAttrString(os_module, "environ");
    CHECK_OBJECT(os_environ);

    PyObject *variable_name_str = Nuitka_String_FromString(variable_name);
    CHECK_OBJECT(variable_name_str);

    if (old_value) {
        setEnvironmentVariable(variable_name, old_value);

#ifdef _WIN32
        PyObject *env_value = NuitkaUnicode_FromWideChar(old_value, -1);
#else
        PyObject *env_value = Nuitka_String_FromString(old_value);
#endif
        CHECK_OBJECT(env_value);

        int res = PyObject_SetItem(os_environ, variable_name_str, env_value);

        if (unlikely(res != 0)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        Py_DECREF(env_value);
    } else {
        unsetEnvironmentVariable(variable_name);

        int res = PyObject_DelItem(os_environ, variable_name_str);

        if (unlikely(res != 0)) {
            CLEAR_ERROR_OCCURRED(tstate);
        }
    }

    Py_DECREF(variable_name_str);
    Py_DECREF(os_environ);
}
