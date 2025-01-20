//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* Small helpers to access files and their contents */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Small helper to open files with few arguments.
PyObject *BUILTIN_OPEN_SIMPLE(PyThreadState *tstate, PyObject *filename, char const *mode, bool buffering,
                              PyObject *encoding) {
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

    result = BUILTIN_OPEN(tstate, filename, mode_obj, buffering_obj);

#else
    if ((strcmp(mode, "w") == 0) && buffering == false) {
        // TODO: Hard import code could be used for this.
        static PyObject *_io_module_text_io_wrapper = NULL;
        if (_io_module_text_io_wrapper == NULL) {
            _io_module_text_io_wrapper = PyObject_GetAttrString(IMPORT_HARD__IO(), "TextIOWrapper");
            CHECK_OBJECT(_io_module_text_io_wrapper);
        }

        PyObject *mode_obj2 = PyUnicode_FromString("wb");

        PyObject *binary_stream =
            BUILTIN_OPEN(tstate, filename, mode_obj2, buffering_obj, NULL, NULL, NULL, NULL, NULL);

        Py_DECREF(mode_obj2);

        if (binary_stream == NULL) {
            return NULL;
        }

        PyObject *encoding_default = NULL;

        if (encoding == NULL) {
            if (encoding_default == NULL) {
                encoding_default = Nuitka_String_FromString("utf-8");
            }

            encoding = encoding_default;
        }

        PyObject *args[] = {binary_stream, encoding, Py_None, Py_None, Py_False, Py_True};

        result = CALL_FUNCTION_WITH_ARGS6(tstate, _io_module_text_io_wrapper, args);
    } else {
        result = BUILTIN_OPEN(tstate, filename, mode_obj, buffering_obj, encoding, NULL, NULL, NULL, NULL);
    }

#endif
    Py_DECREF(mode_obj);

    return result;
}

PyObject *BUILTIN_OPEN_BINARY_READ_SIMPLE(PyThreadState *tstate, PyObject *filename) {
    PyObject *result;

#if PYTHON_VERSION < 0x300
    // On Windows, it seems that line buffering is actually the default.
    result = BUILTIN_OPEN(tstate, filename, const_str_plain_rb, const_int_0);
#else
    result = BUILTIN_OPEN(tstate, filename, const_str_plain_rb, const_int_0, NULL, NULL, NULL, NULL, NULL);
#endif

    return result;
}

PyObject *GET_FILE_BYTES(PyThreadState *tstate, PyObject *filename) {
    PyObject *read_result;

    if (TRACE_FILE_READ(tstate, filename, &read_result)) {
        return read_result;
    }

    PyObject *data_file = BUILTIN_OPEN_BINARY_READ_SIMPLE(tstate, filename);

    if (unlikely(data_file == NULL)) {
        // TODO: Issue a runtime warning maybe.
        return NULL;
    }

    PyObject *read_method = LOOKUP_ATTRIBUTE(tstate, data_file, const_str_plain_read);
    Py_DECREF(data_file);

    if (unlikely(read_method == NULL)) {
        return NULL;
    }

    PyObject *close_method = LOOKUP_ATTRIBUTE(tstate, data_file, const_str_plain_close);

    if (unlikely(close_method == NULL)) {
        Py_DECREF(read_method);
        return NULL;
    }

    read_result = CALL_FUNCTION_NO_ARGS(tstate, read_method);
    Py_DECREF(read_method);

    if (unlikely(read_result == NULL)) {
        Py_DECREF(close_method);
        return NULL;
    }

    PyObject *close_result = CALL_FUNCTION_NO_ARGS(tstate, close_method);
    Py_DECREF(close_method);

    if (unlikely(close_result == NULL)) {
        Py_DECREF(read_result);
        return NULL;
    }

    Py_DECREF(close_result);

    return read_result;
}

// TODO: Don't we have this generated.
static PyObject *IMPORT_HARD_OS_PATH(PyThreadState *tstate) {
    static PyObject *os_path = NULL;

    if (os_path == NULL) {
        os_path = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS(), const_str_plain_path);

        CHECK_OBJECT(os_path);
    }

    return os_path;
}

PyObject *OS_PATH_FILE_EXISTS(PyThreadState *tstate, PyObject *filename) {
    PyObject *result;

    if (TRACE_FILE_EXISTS(tstate, filename, &result)) {
        return result;
    }

    PyObject *exists_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_exists);

    result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, exists_func, filename);

    Py_DECREF(exists_func);
    return result;
}

PyObject *OS_PATH_FILE_ISFILE(PyThreadState *tstate, PyObject *filename) {
    PyObject *result;

    if (TRACE_FILE_ISFILE(tstate, filename, &result)) {
        return result;
    }

    PyObject *isfile_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_isfile);

    result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, isfile_func, filename);

    Py_DECREF(isfile_func);
    return result;
}

PyObject *OS_PATH_FILE_ISDIR(PyThreadState *tstate, PyObject *filename) {
    PyObject *result;

    if (TRACE_FILE_ISDIR(tstate, filename, &result)) {
        return result;
    }

    PyObject *isdir_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_isdir);

    result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, isdir_func, filename);

    Py_DECREF(isdir_func);
    return result;
}

PyObject *OS_LISTDIR(PyThreadState *tstate, PyObject *path) {
    PyObject *result;

    if (TRACE_FILE_LISTDIR(tstate, path, &result)) {
        return result;
    }

    PyObject *listdir_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS(), const_str_plain_listdir);

    if (path != NULL) {
        result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, listdir_func, path);
    } else {
        result = CALL_FUNCTION_NO_ARGS(tstate, listdir_func);
    }

    Py_DECREF(listdir_func);
    return result;
}

extern PyObject *OS_STAT(PyThreadState *tstate, PyObject *path, PyObject *dir_fd, PyObject *follow_symlinks) {
    assert(path != NULL);

    PyObject *result;

    if (TRACE_FILE_STAT(tstate, path, dir_fd, follow_symlinks, &result)) {
        return result;
    }

    PyObject *stat_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS(), const_str_plain_stat);

#if PYTHON_VERSION < 0x300
    assert(dir_fd == NULL);

    result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, stat_func, path);
#else

    PyObject *args[] = {path, dir_fd, follow_symlinks};

    char const *arg_names[] = {"path", "dir_fd", "follow_symlinks"};
    result = CALL_BUILTIN_KW_ARGS(tstate, stat_func, args, arg_names, 3, 2);
#endif

    Py_DECREF(stat_func);
    return result;
}

extern PyObject *OS_LSTAT(PyThreadState *tstate, PyObject *path, PyObject *dir_fd) {
    assert(path != NULL);
    PyObject *result;

#if PYTHON_VERSION < 0x300
    if (TRACE_FILE_STAT(tstate, path, dir_fd, Py_False, &result)) {
        return result;
    }

    assert(path != NULL);
    assert(dir_fd == NULL);
    PyObject *lstat_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS(), const_str_plain_lstat);

    result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, lstat_func, path);
#else
    if (TRACE_FILE_STAT(tstate, path, dir_fd, Py_True, &result)) {
        return result;
    }

    PyObject *args[] = {path, dir_fd};

    char const *arg_names[] = {"path", "dir_fd"};

    PyObject *lstat_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS(), const_str_plain_lstat);

    result = CALL_BUILTIN_KW_ARGS(tstate, lstat_func, args, arg_names, 2, 1);
#endif

    Py_DECREF(lstat_func);
    return result;
}

PyObject *OS_PATH_BASENAME(PyThreadState *tstate, PyObject *filename) {
    CHECK_OBJECT(filename);

    PyObject *basename_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_basename);

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, basename_func, filename);

    Py_DECREF(basename_func);
    return result;
}

PyObject *OS_PATH_DIRNAME(PyThreadState *tstate, PyObject *filename) {
    CHECK_OBJECT(filename);

    PyObject *dirname_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_dirname);

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, dirname_func, filename);

    Py_DECREF(dirname_func);
    return result;
}

PyObject *OS_PATH_ABSPATH(PyThreadState *tstate, PyObject *filename) {
    CHECK_OBJECT(filename);

    PyObject *abspath_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_abspath);

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, abspath_func, filename);

    Py_DECREF(abspath_func);
    return result;
}

PyObject *OS_PATH_ISABS(PyThreadState *tstate, PyObject *filename) {
    CHECK_OBJECT(filename);

    PyObject *isabs_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_isabs);

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, isabs_func, filename);

    Py_DECREF(isabs_func);
    return result;
}

extern PyObject *OS_PATH_NORMPATH(PyThreadState *tstate, PyObject *filename) {
    PyObject *normpath_func = LOOKUP_ATTRIBUTE(tstate, IMPORT_HARD_OS_PATH(tstate), const_str_plain_normpath);

    PyObject *result = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, normpath_func, filename);

    Py_DECREF(normpath_func);
    return result;
}

nuitka_bool compareFilePaths(PyThreadState *tstate, PyObject *filename_a, PyObject *filename_b) {
    filename_a = OS_PATH_ABSPATH(tstate, filename_a);

    if (unlikely(filename_a == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    filename_b = OS_PATH_ABSPATH(tstate, filename_b);

    if (unlikely(filename_b == NULL)) {
        Py_DECREF(filename_a);
        return NUITKA_BOOL_EXCEPTION;
    }

    return RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(filename_a, filename_b);
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
