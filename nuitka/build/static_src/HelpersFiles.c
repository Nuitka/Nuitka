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
/* Small helpers to access files and their contents */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Small helper to open files with few arguments.
PyObject *BUILTIN_OPEN_SIMPLE(PyObject *filename, char const *mode, bool buffering, PyObject *encoding) {
    PyObject *mode_obj = Nuitka_String_FromString(mode);
    PyObject *buffering_obj = buffering ? const_int_pos_1 : const_int_0;

    PyObject *result;

#if PYTHON_VERSION < 0x300
    // On Windows, it seems that line buffering is actually the default.
#ifdef _WIN32
    if ((strcmp(mode, "w") == 0) && buffering == true) {
        buffering_obj = const_int_0;
    }
#endif

    result = BUILTIN_OPEN(filename, mode_obj, buffering_obj);

#else
    if ((strcmp(mode, "w") == 0) && buffering == false) {
        // TODO: Hard import code could be used for this.
        static PyObject *_io_module = NULL;
        static PyObject *_io_module_text_io_wrapper = NULL;
        if (_io_module == NULL) {
            _io_module = PyImport_ImportModule("_io");
            CHECK_OBJECT(_io_module);

            _io_module_text_io_wrapper = PyObject_GetAttrString(_io_module, "TextIOWrapper");
            CHECK_OBJECT(_io_module_text_io_wrapper);
        }

        PyObject *mode_obj2 = PyUnicode_FromString("wb");

        PyObject *binary_stream = BUILTIN_OPEN(filename, mode_obj2, buffering_obj, NULL, NULL, NULL, NULL, NULL);

        Py_DECREF(mode_obj2);

        if (binary_stream == NULL) {
            return NULL;
        }

        PyObject *args[] = {binary_stream, encoding, Py_None, Py_None, Py_False, Py_True};

        result = CALL_FUNCTION_WITH_ARGS6(_io_module_text_io_wrapper, args);
    } else {
        result = BUILTIN_OPEN(filename, mode_obj, buffering_obj, encoding, NULL, NULL, NULL, NULL);
    }

#endif
    Py_DECREF(mode_obj);

    return result;
}

PyObject *BUILTIN_OPEN_BINARY_READ_SIMPLE(PyObject *filename) {
    PyObject *result;

#if PYTHON_VERSION < 0x300
    // On Windows, it seems that line buffering is actually the default.
    result = BUILTIN_OPEN(filename, const_str_plain_rb, const_int_0);
#else
    result = BUILTIN_OPEN(filename, const_str_plain_rb, const_int_0, NULL, NULL, NULL, NULL, NULL);
#endif

    return result;
}

PyObject *GET_FILE_BYTES(PyObject *filename) {
    PyObject *result;

    if (TRACE_FILE_READ(filename, &result)) {
        return result;
    }

    PyObject *data_file = BUILTIN_OPEN_BINARY_READ_SIMPLE(filename);

    if (unlikely(data_file == NULL)) {
        // TODO: Issue a runtime warning maybe.
        return NULL;
    }

    PyObject *read_method = LOOKUP_ATTRIBUTE(data_file, const_str_plain_read);
    Py_DECREF(data_file);

    if (unlikely(read_method == NULL)) {
        return NULL;
    }

    result = CALL_FUNCTION_NO_ARGS(read_method);
    Py_DECREF(read_method);
    return result;
}
