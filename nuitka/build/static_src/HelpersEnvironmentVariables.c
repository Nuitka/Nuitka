//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Helpers for working with environment variables from Python binary in a
// portable way.

#include "nuitka/environment_variables.h"

#include "HelpersEnvironmentVariablesSystem.c"

static PyObject *Nuitka_String_FromEnvironmentVariable(environment_char_t const *value) {
#if defined(_WIN32) && PYTHON_VERSION < 0x300
    // CPython 2 exposes environment variables as 'str' in the ANSI code page,
    // and e.g. 'subprocess.Popen' rejects unicode values for the environment.
    int buffer_size = WideCharToMultiByte(CP_ACP, 0, value, -1, NULL, 0, NULL, NULL);

    if (unlikely(buffer_size <= 0)) {
        abort();
    }

    char *buffer = (char *)malloc((size_t)buffer_size);

    if (unlikely(buffer == NULL)) {
        abort();
    }

    int converted_size = WideCharToMultiByte(CP_ACP, 0, value, -1, buffer, buffer_size, NULL, NULL);

    if (unlikely(converted_size != buffer_size)) {
        free(buffer);
        abort();
    }

    PyObject *result = Nuitka_String_FromStringAndSize(buffer, (Py_ssize_t)(converted_size - 1));

    free(buffer);

    return result;
#elif defined(_WIN32)
    return NuitkaUnicode_FromWideChar(value, -1);
#else
    return Nuitka_String_FromString(value);
#endif
}

void undoEnvironmentVariable(PyThreadState *tstate, char const *variable_name, environment_char_t const *old_value) {
    PyObject *os_module = IMPORT_HARD_OS();
    CHECK_OBJECT(os_module);

    PyObject *os_environ = LOOKUP_ATTRIBUTE(tstate, os_module, const_str_plain_environ);
    CHECK_OBJECT(os_environ);

    PyObject *variable_name_str = Nuitka_String_FromString(variable_name);
    CHECK_OBJECT(variable_name_str);

    if (old_value) {
        PyObject *env_value = Nuitka_String_FromEnvironmentVariable(old_value);

        if (unlikely(env_value == NULL)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        bool res = SET_SUBSCRIPT(tstate, os_environ, variable_name_str, env_value);

        if (unlikely(res == false)) {
            PyErr_PrintEx(1);
            Py_Exit(1);
        }

        Py_DECREF(env_value);

        // Python 2's 'os.environ' assignment uses 'nt.putenv', which writes the
        // ANSI environment, so restoring the wide value must come afterwards.
        setEnvironmentVariable(variable_name, old_value);
    } else {
        bool res = DEL_SUBSCRIPT(os_environ, variable_name_str);

        if (unlikely(res == false)) {
            CLEAR_ERROR_OCCURRED(tstate);
        }

        unsetEnvironmentVariable(variable_name);
    }

    Py_DECREF(variable_name_str);
    Py_DECREF(os_environ);
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
