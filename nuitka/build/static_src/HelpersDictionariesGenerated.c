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

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION < 0x3b0
typedef PyObject *PyDictValues;
#endif

static inline PyDictValues *Nuitka_PyDict_new_values(Py_ssize_t size) {
#if PYTHON_VERSION < 0x3b0
    return PyMem_MALLOC(sizeof(PyObject *) * size);
#else
    // With Python3.11 or higher a prefix is allocated too.
    size_t prefix_size = _Py_SIZE_ROUND_UP(size + 2, sizeof(PyObject *));
    size_t n = prefix_size + size * sizeof(PyObject *);
    uint8_t *mem = (uint8_t *)PyMem_MALLOC(n);

    assert(mem != NULL);

    assert(prefix_size % sizeof(PyObject *) == 0);
    mem[prefix_size - 1] = (uint8_t)prefix_size;

    return (PyDictValues *)(mem + prefix_size);
#endif
}

PyObject *DICT_COPY(PyObject *dict_value) {
#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    return PyDict_Copy(dict_value);
#else
    PyObject *result;

    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    if (((PyDictObject *)dict_value)->ma_used == 0) {
        result = PyDict_New();
    } else {
        PyDictObject *dict_mp = (PyDictObject *)dict_value;

#if PYTHON_VERSION < 0x300
        // For Python3, this can be done much faster in the same way as it is
        // done in parameter parsing.
        result = _PyDict_NewPresized(dict_mp->ma_used);

        for (Py_ssize_t i = 0; i <= dict_mp->ma_mask; i++) {
            PyDictEntry *entry = &dict_mp->ma_table[i];

            if (entry->me_value != NULL) {
                PyObject *key = entry->me_key;

                PyObject *value = entry->me_value;

                int res = PyDict_SetItem(result, key, value);
                assert(res == 0);
            }
        }
#else
        /* Python 3 */
#ifndef PY_NOGIL
        if (_PyDict_HasSplitTable(dict_mp)) {
#if PYTHON_VERSION < 0x360
            Py_ssize_t size = dict_mp->ma_keys->dk_size;
#elif PYTHON_VERSION < 0x3b0
            Py_ssize_t size = DK_USABLE_FRACTION(DK_SIZE(dict_mp->ma_keys));
#else
            Py_ssize_t size = Nuitka_Py_shared_keys_usable_size(dict_mp->ma_keys);
#endif

            PyDictObject *result_mp = PyObject_GC_New(PyDictObject, &PyDict_Type);
            assert(result_mp != NULL);
            result = (PyObject *)result_mp;

            PyDictValues *new_values = Nuitka_PyDict_new_values(size);
            assert(new_values != NULL);

            result_mp->ma_values = new_values;
            result_mp->ma_keys = dict_mp->ma_keys;
            result_mp->ma_used = dict_mp->ma_used;

            dict_mp->ma_keys->dk_refcnt += 1;

            for (Py_ssize_t i = 0; i < size; i++) {
                if (DK_VALUE(dict_mp, i)) {
                    PyObject *value = DK_VALUE(dict_mp, i);

                    DK_VALUE(result_mp, i) = value;
                    Py_INCREF(value);

                } else {
                    DK_VALUE(result_mp, i) = NULL;
                }
            }

            Nuitka_GC_Track(result_mp);
        } else
#endif
        {
            result = _PyDict_NewPresized(dict_mp->ma_used);

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = dict_mp->ma_keys->dk_size;
#else
            Py_ssize_t size = dict_mp->ma_keys->dk_nentries;
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &DK_ENTRIES(dict_mp->ma_keys)[i];

                if (entry->me_value != NULL) {
                    PyObject *key = entry->me_key;

                    PyObject *value = entry->me_value;

                    int res = PyDict_SetItem(result, key, value);
                    assert(res == 0);
                }
            }
        }
#endif
    }

    return result;
#endif
}

PyObject *DEEP_COPY_DICT(PyObject *dict_value) {
    PyObject *result;

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT
    CHECK_OBJECT(value);
    assert(PyDict_CheckExact(value));

    result = DICT_COPY(value);

    Py_ssize_t pos = 0;
    PyObject *dict_key, *dict_value;

    while (Nuitka_DictNext(value, &pos, &dict_key, &dict_value)) {
        PyObject *dict_value_copy = DEEP_COPY(dict_value);

        if (dict_value_copy != dict_value) {
            DICT_SET_ITEM(value, dict_key, dict_value_copy);
        }
    }

#else
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    if (((PyDictObject *)dict_value)->ma_used == 0) {
        result = PyDict_New();
    } else {
        PyDictObject *dict_mp = (PyDictObject *)dict_value;

#if PYTHON_VERSION < 0x300
        // For Python3, this can be done much faster in the same way as it is
        // done in parameter parsing.
        result = _PyDict_NewPresized(dict_mp->ma_used);

        for (Py_ssize_t i = 0; i <= dict_mp->ma_mask; i++) {
            PyDictEntry *entry = &dict_mp->ma_table[i];

            if (entry->me_value != NULL) {
                PyObject *key = entry->me_key;

                PyObject *value = entry->me_value;
                value = DEEP_COPY(value);

                int res = PyDict_SetItem(result, key, value);
                assert(res == 0);

                Py_DECREF(value);
            }
        }
#else
        /* Python 3 */
#ifndef PY_NOGIL
        if (_PyDict_HasSplitTable(dict_mp)) {
#if PYTHON_VERSION < 0x360
            Py_ssize_t size = dict_mp->ma_keys->dk_size;
#elif PYTHON_VERSION < 0x3b0
            Py_ssize_t size = DK_USABLE_FRACTION(DK_SIZE(dict_mp->ma_keys));
#else
            Py_ssize_t size = Nuitka_Py_shared_keys_usable_size(dict_mp->ma_keys);
#endif

            PyDictObject *result_mp = PyObject_GC_New(PyDictObject, &PyDict_Type);
            assert(result_mp != NULL);
            result = (PyObject *)result_mp;

            PyDictValues *new_values = Nuitka_PyDict_new_values(size);
            assert(new_values != NULL);

            result_mp->ma_values = new_values;
            result_mp->ma_keys = dict_mp->ma_keys;
            result_mp->ma_used = dict_mp->ma_used;

            dict_mp->ma_keys->dk_refcnt += 1;

            for (Py_ssize_t i = 0; i < size; i++) {
                if (DK_VALUE(dict_mp, i)) {
                    PyObject *value = DK_VALUE(dict_mp, i);
                    value = DEEP_COPY(value);

                    DK_VALUE(result_mp, i) = value;

                } else {
                    DK_VALUE(result_mp, i) = NULL;
                }
            }

            Nuitka_GC_Track(result_mp);
        } else
#endif
        {
            result = _PyDict_NewPresized(dict_mp->ma_used);

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = dict_mp->ma_keys->dk_size;
#else
            Py_ssize_t size = dict_mp->ma_keys->dk_nentries;
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &DK_ENTRIES(dict_mp->ma_keys)[i];

                if (entry->me_value != NULL) {
                    PyObject *key = entry->me_key;

                    PyObject *value = entry->me_value;
                    value = DEEP_COPY(value);

                    int res = PyDict_SetItem(result, key, value);
                    assert(res == 0);

                    Py_DECREF(value);
                }
            }
        }
#endif
    }

#endif

    return result;
}

// Helper for function calls with star dict arguments. */
static PyObject *COPY_DICT_KW(PyObject *dict_value) {
    PyObject *result;

    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    if (((PyDictObject *)dict_value)->ma_used == 0) {
        result = PyDict_New();
    } else {
        PyDictObject *dict_mp = (PyDictObject *)dict_value;

#if PYTHON_VERSION < 0x300
        // For Python3, this can be done much faster in the same way as it is
        // done in parameter parsing.
        result = _PyDict_NewPresized(dict_mp->ma_used);

        for (Py_ssize_t i = 0; i <= dict_mp->ma_mask; i++) {
            PyDictEntry *entry = &dict_mp->ma_table[i];

            if (entry->me_value != NULL) {
                PyObject *key = entry->me_key;
                if (unlikely(!checkKeywordType(key))) {
                    Py_DECREF(result);
                    return NULL;
                }

                PyObject *value = entry->me_value;

                int res = PyDict_SetItem(result, key, value);
                assert(res == 0);
            }
        }
#else
        /* Python 3 */
#ifndef PY_NOGIL
        if (_PyDict_HasSplitTable(dict_mp)) {
#if PYTHON_VERSION < 0x360
            Py_ssize_t size = dict_mp->ma_keys->dk_size;
#elif PYTHON_VERSION < 0x3b0
            Py_ssize_t size = DK_USABLE_FRACTION(DK_SIZE(dict_mp->ma_keys));
#else
            Py_ssize_t size = Nuitka_Py_shared_keys_usable_size(dict_mp->ma_keys);
#endif

            PyDictObject *result_mp = PyObject_GC_New(PyDictObject, &PyDict_Type);
            assert(result_mp != NULL);
            result = (PyObject *)result_mp;

            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &DK_ENTRIES(dict_mp->ma_keys)[i];

                if (entry->me_value != NULL) {
                    PyObject *key = entry->me_key;
                    if (unlikely(!checkKeywordType(key))) {
                        Py_DECREF(result);
                        return NULL;
                    }
                }
            }

            PyDictValues *new_values = Nuitka_PyDict_new_values(size);
            assert(new_values != NULL);

            result_mp->ma_values = new_values;
            result_mp->ma_keys = dict_mp->ma_keys;
            result_mp->ma_used = dict_mp->ma_used;

            dict_mp->ma_keys->dk_refcnt += 1;

            for (Py_ssize_t i = 0; i < size; i++) {
                if (DK_VALUE(dict_mp, i)) {
                    PyObject *value = DK_VALUE(dict_mp, i);

                    DK_VALUE(result_mp, i) = value;
                    Py_INCREF(value);

                } else {
                    DK_VALUE(result_mp, i) = NULL;
                }
            }

            Nuitka_GC_Track(result_mp);
        } else
#endif
        {
            result = _PyDict_NewPresized(dict_mp->ma_used);

#if PYTHON_VERSION < 0x360
            Py_ssize_t size = dict_mp->ma_keys->dk_size;
#else
            Py_ssize_t size = dict_mp->ma_keys->dk_nentries;
#endif
            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &DK_ENTRIES(dict_mp->ma_keys)[i];

                if (entry->me_value != NULL) {
                    PyObject *key = entry->me_key;
                    if (unlikely(!checkKeywordType(key))) {
                        Py_DECREF(result);
                        return NULL;
                    }

                    PyObject *value = entry->me_value;

                    int res = PyDict_SetItem(result, key, value);
                    assert(res == 0);
                }
            }
        }
#endif
    }

    return result;
}
