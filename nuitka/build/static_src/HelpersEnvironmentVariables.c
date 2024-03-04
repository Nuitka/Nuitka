//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Helpers for working with environment variables from Python binary in a
// portable way.

#include "nuitka/environment_variables.h"

#include "HelpersEnvironmentVariablesSystem.c"

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
