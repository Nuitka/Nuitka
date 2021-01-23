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
/**
 * This is responsible for deep copy and hashing of constants.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *DEEP_COPY(PyObject *value) {
    if (PyDict_Check(value)) {
#if PYTHON_VERSION < 0x330
        // For Python3, this can be done much faster in the same way as it is
        // done in parameter parsing.

        PyObject *result = _PyDict_NewPresized(((PyDictObject *)value)->ma_used);

        for (Py_ssize_t i = 0; i <= ((PyDictObject *)value)->ma_mask; i++) {
            PyDictEntry *entry = &((PyDictObject *)value)->ma_table[i];

            if (entry->me_value != NULL) {
                PyObject *deep_copy = DEEP_COPY(entry->me_value);

                int res = PyDict_SetItem(result, entry->me_key, deep_copy);

                Py_DECREF(deep_copy);

                if (unlikely(res != 0)) {
                    return NULL;
                }
            }
        }

        return result;
#else
        /* Python 3.3 or higher */
        if (_PyDict_HasSplitTable((PyDictObject *)value)) {
            PyDictObject *mp = (PyDictObject *)value;

            PyObject **newvalues = PyMem_NEW(PyObject *, mp->ma_keys->dk_size);
            assert(newvalues != NULL);

            PyDictObject *result = PyObject_GC_New(PyDictObject, &PyDict_Type);
            assert(result != NULL);

            result->ma_values = newvalues;
            result->ma_keys = mp->ma_keys;
            result->ma_used = mp->ma_used;

            mp->ma_keys->dk_refcnt += 1;

            Nuitka_GC_Track(result);

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = mp->ma_keys->dk_size;
#else
            Py_ssize_t size = DK_USABLE_FRACTION(DK_SIZE(mp->ma_keys));
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
                if (mp->ma_values[i]) {
                    result->ma_values[i] = DEEP_COPY(mp->ma_values[i]);
                } else {
                    result->ma_values[i] = NULL;
                }
            }

            return (PyObject *)result;
        } else {
            PyObject *result = _PyDict_NewPresized(((PyDictObject *)value)->ma_used);

            PyDictObject *mp = (PyDictObject *)value;

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = mp->ma_keys->dk_size;
#else
            Py_ssize_t size = mp->ma_keys->dk_nentries;
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
#if PYTHON_VERSION < 0x360
                PyDictKeyEntry *entry = &mp->ma_keys->dk_entries[i];
#else
                PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[i];
#endif

                if (entry->me_value != NULL) {
                    PyObject *deep_copy = DEEP_COPY(entry->me_value);

                    PyDict_SetItem(result, entry->me_key, deep_copy);

                    Py_DECREF(deep_copy);
                }
            }

            return result;
        }
#endif
    } else if (PyTuple_Check(value)) {
        Py_ssize_t n = PyTuple_GET_SIZE(value);
        PyObject *result = PyTuple_New(n);

        for (Py_ssize_t i = 0; i < n; i++) {
            PyTuple_SET_ITEM(result, i, DEEP_COPY(PyTuple_GET_ITEM(value, i)));
        }

        return result;
    } else if (PyList_Check(value)) {
        Py_ssize_t n = PyList_GET_SIZE(value);
        PyObject *result = PyList_New(n);

        for (Py_ssize_t i = 0; i < n; i++) {
            PyList_SET_ITEM(result, i, DEEP_COPY(PyList_GET_ITEM(value, i)));
        }

        return result;
    } else if (PySet_Check(value)) {
        // Sets cannot contain unhashable types, so they must be immutable.
        return PySet_New(value);
    } else if (PyFrozenSet_Check(value)) {
        // Sets cannot contain unhashable types, so they must be immutable.
        return PyFrozenSet_New(value);
    } else if (
#if PYTHON_VERSION < 0x300
        PyString_Check(value) ||
#endif
        PyUnicode_Check(value) ||
#if PYTHON_VERSION < 0x300
        PyInt_Check(value) ||
#endif
        PyLong_Check(value) || value == Py_None || PyBool_Check(value) || PyFloat_Check(value) ||
        PyBytes_Check(value) || PyRange_Check(value) || PyType_Check(value) || PySlice_Check(value) ||
        PyComplex_Check(value) || PyCFunction_Check(value) || value == Py_Ellipsis || value == Py_NotImplemented) {
        Py_INCREF(value);
        return value;
    } else if (PyByteArray_Check(value)) {
        // TODO: Could make an exception for zero size.
        return PyByteArray_FromObject(value);
    } else {
        PyErr_Format(PyExc_TypeError, "DEEP_COPY does not implement: %s", value->ob_type->tp_name);

        return NULL;
    }
}

#ifndef __NUITKA_NO_ASSERT__

static Py_hash_t DEEP_HASH_INIT(PyObject *value) {
    // To avoid warnings about reduced sizes, we put an intermediate value
    // that is size_t.
    size_t value2 = (size_t)value;
    Py_hash_t result = (Py_hash_t)(value2);

    if (Py_TYPE(value) != &PyType_Type) {
        result ^= DEEP_HASH((PyObject *)Py_TYPE(value));
    }

    return result;
}

static void DEEP_HASH_BLOB(Py_hash_t *hash, char const *s, Py_ssize_t size) {
    while (size > 0) {
        *hash = (1000003 * (*hash)) ^ (Py_hash_t)(*s++);
        size--;
    }
}

static void DEEP_HASH_CSTR(Py_hash_t *hash, char const *s) { DEEP_HASH_BLOB(hash, s, strlen(s)); }

// Hash function that actually verifies things done to the bit level. Can be
// used to detect corruption.
Py_hash_t DEEP_HASH(PyObject *value) {
    assert(value != NULL);

    if (PyType_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        DEEP_HASH_CSTR(&result, ((PyTypeObject *)value)->tp_name);
        return result;
    } else if (PyDict_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t ppos = 0;
        PyObject *key, *dict_value;

        while (PyDict_Next(value, &ppos, &key, &dict_value)) {
            if (key != NULL && value != NULL) {
                result ^= DEEP_HASH(key);
                result ^= DEEP_HASH(dict_value);
            }
        }

        return result;
    } else if (PyTuple_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t n = PyTuple_GET_SIZE(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            result ^= DEEP_HASH(PyTuple_GET_ITEM(value, i));
        }

        return result;
    } else if (PyList_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t n = PyList_GET_SIZE(value);

        for (Py_ssize_t i = 0; i < n; i++) {
            result ^= DEEP_HASH(PyList_GET_ITEM(value, i));
        }

        return result;
    } else if (PySet_Check(value) || PyFrozenSet_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        PyObject *iterator = PyObject_GetIter(value);
        CHECK_OBJECT(iterator);

        while (true) {
            PyObject *item = PyIter_Next(iterator);
            if (!item)
                break;

            CHECK_OBJECT(item);

            result ^= DEEP_HASH(item);

            Py_DECREF(item);
        }

        Py_DECREF(iterator);

        return result;
    } else if (PyLong_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        PyObject *exception_type, *exception_value;
        PyTracebackObject *exception_tb;

        FETCH_ERROR_OCCURRED_UNTRACED(&exception_type, &exception_value, &exception_tb);

        // Use string to hash the long value, which relies on that to not
        // use the object address.
        PyObject *str = PyObject_Str(value);
        result ^= DEEP_HASH(str);
        Py_DECREF(str);

        RESTORE_ERROR_OCCURRED_UNTRACED(exception_type, exception_value, exception_tb);

        return result;
    } else if (PyUnicode_Check(value)) {
        Py_hash_t result = DEEP_HASH((PyObject *)Py_TYPE(value));

        PyObject *exception_type, *exception_value;
        PyTracebackObject *exception_tb;

        FETCH_ERROR_OCCURRED_UNTRACED(&exception_type, &exception_value, &exception_tb);

#if PYTHON_VERSION >= 0x300
        char const *s = (char const *)PyUnicode_DATA(value);
        Py_ssize_t size = PyUnicode_GET_LENGTH(value) * PyUnicode_KIND(value);

        DEEP_HASH_BLOB(&result, s, size);
#else
        PyObject *str = PyUnicode_AsUTF8String(value);

        if (str) {
            result ^= DEEP_HASH(str);
        }

        Py_DECREF(str);
#endif
        RESTORE_ERROR_OCCURRED_UNTRACED(exception_type, exception_value, exception_tb);

        return result;
    }
#if PYTHON_VERSION < 0x300
    else if (PyString_Check(value)) {
        Py_hash_t result = DEEP_HASH((PyObject *)Py_TYPE(value));

        Py_ssize_t size;
        char *s;

        int res = PyString_AsStringAndSize(value, &s, &size);
        assert(res != -1);

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    }
#else
    else if (PyBytes_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t size;
        char *s;

        int res = PyBytes_AsStringAndSize(value, &s, &size);
        assert(res != -1);

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    }
#endif
    else if (PyByteArray_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t size = PyByteArray_Size(value);
        assert(size >= 0);

        char *s = PyByteArray_AsString(value);

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    } else if (value == Py_None || value == Py_Ellipsis || value == Py_NotImplemented) {
        return DEEP_HASH_INIT(value);
    } else if (PyComplex_Check(value)) {
        Py_complex c = PyComplex_AsCComplex(value);

        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t size = sizeof(c);
        char *s = (char *)&c;

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    } else if (PyFloat_Check(value)) {
        double f = PyFloat_AsDouble(value);

        Py_hash_t result = DEEP_HASH_INIT(value);

        Py_ssize_t size = sizeof(f);
        char *s = (char *)&f;

        DEEP_HASH_BLOB(&result, s, size);

        return result;
    } else if (
#if PYTHON_VERSION < 0x300
        PyInt_Check(value) ||
#endif
        PyBool_Check(value) || PyRange_Check(value) || PySlice_Check(value) || PyCFunction_Check(value)) {
        Py_hash_t result = DEEP_HASH_INIT(value);

#if 0
        printf("Too simple deep hash: %s\n", Py_TYPE(value)->tp_name);
#endif

        return result;
    } else {
        assert(false);

        return -1;
    }
}
#endif

// Note: Not recursion safe, cannot do this everywhere.
void CHECK_OBJECT_DEEP(PyObject *value) {
    CHECK_OBJECT(value);

    if (PyTuple_Check(value)) {
        for (Py_ssize_t i = 0, size = PyTuple_GET_SIZE(value); i < size; i++) {
            PyObject *element = PyTuple_GET_ITEM(value, i);

            CHECK_OBJECT_DEEP(element);
        }
    } else if (PyList_Check(value)) {
        for (Py_ssize_t i = 0, size = PyList_GET_SIZE(value); i < size; i++) {
            PyObject *element = PyList_GET_ITEM(value, i);

            CHECK_OBJECT_DEEP(element);
        }
    }
}
