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

/* WARNING, this code is GENERATED. Modify the template HelperDictionaryCopy.c.j2 instead! */

// Usable fraction of keys.
#define DK_USABLE_FRACTION(n) (((n) << 1) / 3)

#if PYTHON_VERSION < 0x3b0
typedef PyObject *PyDictValues;
#endif

#if PYTHON_VERSION < 0x360
#define DK_ENTRIES_SIZE(keys) (keys->dk_size)
#elif PYTHON_VERSION < 0x3b0
#define DK_ENTRIES_SIZE(keys) DK_USABLE_FRACTION(DK_SIZE(keys))
#else
#define DK_ENTRIES_SIZE(keys) (keys->dk_nentries)
#endif

// More than 2/3 of the keys are used, i.e. no space is wasted.
#if PYTHON_VERSION < 0x360
#define IS_COMPACT(dict_mp) (dict_mp->ma_used >= (dict_mp->ma_keys->dk_size * 2) / 3)
#else
#define IS_COMPACT(dict_mp) (dict_mp->ma_used >= (dict_mp->ma_keys->dk_nentries * 2) / 3)
#endif

static inline PyDictValues *_Nuitka_PyDict_new_values(Py_ssize_t size) {
    Py_ssize_t values_size = sizeof(PyObject *) * size;

#if PYTHON_VERSION < 0x3b0
    return (PyDictValues *)PyMem_MALLOC(values_size);
#else
    // With Python3.11 or higher a prefix is allocated too.
    size_t prefix_size = _Py_SIZE_ROUND_UP(size + 2, sizeof(PyObject *));
    size_t n = prefix_size + values_size;
    uint8_t *mem = (uint8_t *)PyMem_MALLOC(n);

    assert(mem != NULL);

    assert(prefix_size % sizeof(PyObject *) == 0);
    mem[prefix_size - 1] = (uint8_t)prefix_size;

    return (PyDictValues *)(mem + prefix_size);
#endif
}

#if NUITKA_DICT_HAS_FREELIST
static struct _Py_dict_state *_Nuitka_Py_get_dict_state(void) {
    PyInterpreterState *interp = _PyInterpreterState_GET();
    return &interp->dict_state;
}
#endif

#if PYTHON_VERSION >= 0x300
static PyDictObject *_Nuitka_AllocatePyDictObject(void) {
    PyDictObject *result_mp;

#if NUITKA_DICT_HAS_FREELIST
    struct _Py_dict_state *state = _Nuitka_Py_get_dict_state();

    if (state->numfree) {
        result_mp = state->free_list[--state->numfree];

        Nuitka_Py_NewReference((PyObject *)result_mp);

        assert(PyDict_CheckExact((PyObject *)result_mp));
        assert(result_mp != NULL);
    } else
#endif
    {
        result_mp = (PyDictObject *)Nuitka_GC_New(&PyDict_Type);
    }

    return result_mp;
}
#endif

#if PYTHON_VERSION >= 0x360 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT)
static Py_ssize_t _Nuitka_Py_PyDict_KeysSize(PyDictKeysObject *keys) {
#if PYTHON_VERSION < 0x360
    return sizeof(PyDictKeysObject) + (DK_SIZE(keys) - 1) * sizeof(PyDictKeyEntry);
#elif PYTHON_VERSION < 0x370
    return (sizeof(PyDictKeysObject) - Py_MEMBER_SIZE(PyDictKeysObject, dk_indices) + DK_IXSIZE(keys) * DK_SIZE(keys) +
            DK_USABLE_FRACTION(DK_SIZE(keys)) * sizeof(PyDictKeyEntry));
#elif PYTHON_VERSION < 0x3b0
    return (sizeof(PyDictKeysObject) + DK_IXSIZE(keys) * DK_SIZE(keys) +
            DK_USABLE_FRACTION(DK_SIZE(keys)) * sizeof(PyDictKeyEntry));
#else
    size_t entry_size = keys->dk_kind == DICT_KEYS_GENERAL ? sizeof(PyDictKeyEntry) : sizeof(PyDictUnicodeEntry);
    return (sizeof(PyDictKeysObject) + ((size_t)1 << keys->dk_log2_index_bytes) +
            DK_USABLE_FRACTION(DK_SIZE(keys)) * entry_size);
#endif
}
#endif

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
        result = MAKE_DICT_EMPTY();
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
            Py_ssize_t size = DK_ENTRIES_SIZE(dict_mp->ma_keys);

            PyDictObject *result_mp = _Nuitka_AllocatePyDictObject();
            assert(result_mp != NULL);
            result = (PyObject *)result_mp;

            PyDictValues *new_values = _Nuitka_PyDict_new_values(size);
            assert(new_values != NULL);

#if PYTHON_VERSION >= 0x3b0
            // Need to preserve values prefix.
            size_t prefix_size = ((uint8_t *)new_values)[-1];
            memcpy(((char *)new_values) - prefix_size, ((char *)dict_mp->ma_values) - prefix_size, prefix_size - 1);
#endif

            result_mp->ma_values = new_values;
            result_mp->ma_keys = dict_mp->ma_keys;
            result_mp->ma_used = dict_mp->ma_used;

            // This is a manual reference count for the keys.
#ifdef Py_REF_DEBUG
            _Py_RefTotal++;
#endif
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
#if PYTHON_VERSION >= 0x360
            // Fast dictionary copy if it has at least 2/3 space usage. This is most relevant
            // for the DICT_COPY, where it might even be the intention to trigger a shrink with
            // a fresh copy.
            if (dict_mp->ma_values == NULL && IS_COMPACT(dict_mp)) {
            assert(dict_mp->ma_values == NULL);
            assert(dict_mp->ma_keys->dk_refcnt == 1);

            PyDictObject *result_mp = _Nuitka_AllocatePyDictObject();
            result = (PyObject *)result_mp;

            result_mp->ma_values = NULL;
            result_mp->ma_used = dict_mp->ma_used;

            Py_ssize_t keys_size = _Nuitka_Py_PyDict_KeysSize(dict_mp->ma_keys);
            result_mp->ma_keys = (PyDictKeysObject *)PyObject_MALLOC(keys_size);
            assert(result_mp->ma_keys);

            memcpy(result_mp->ma_keys, dict_mp->ma_keys, keys_size);

            // Take reference of all keys and values.
#if PYTHON_VERSION < 0x3b0
            PyDictKeyEntry *entries = DK_ENTRIES(result_mp->ma_keys);
            Py_ssize_t size = DK_ENTRIES_SIZE(result_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &entries[i];
                PyObject *value = entry->me_value;

                if (value != NULL) {
                    PyObject *key = entry->me_key;

                    Py_INCREF(key);

                    Py_INCREF(value);
                }
            }
#else
            PyObject **key_ptr, **value_ptr;
            size_t entry_size;

            bool is_unicode = DK_IS_UNICODE(result_mp->ma_keys);

            if (is_unicode) {
                PyDictUnicodeEntry *ep0 = DK_UNICODE_ENTRIES(result_mp->ma_keys);

                key_ptr = &ep0->me_key;
                value_ptr = &ep0->me_value;
                entry_size = sizeof(PyDictUnicodeEntry) / sizeof(PyObject *);
            } else {
                PyDictKeyEntry *ep0 = DK_ENTRIES(result_mp->ma_keys);

                key_ptr = &ep0->me_key;
                value_ptr = &ep0->me_value;
                entry_size = sizeof(PyDictKeyEntry) / sizeof(PyObject *);
            }

            Py_ssize_t size = DK_ENTRIES_SIZE(result_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *value = *value_ptr;

                if (value != NULL) {

                    Py_INCREF(value);
                    PyObject *key = *key_ptr;
                    Py_INCREF(key);
                }

                value_ptr += entry_size;
                key_ptr += entry_size;
            }
#endif

            // The new keys are an object counted.
#ifdef Py_REF_DEBUG
            _Py_RefTotal++;
#endif

            Nuitka_GC_Track(result_mp);
        } else
#endif
        {
            result = _PyDict_NewPresized(dict_mp->ma_used);

            Py_ssize_t size = DK_ENTRIES_SIZE(dict_mp->ma_keys);

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
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    result = DICT_COPY(dict_value);

    Py_ssize_t pos = 0;
    PyObject *key, *value;

    while (Nuitka_DictNext(dict_value, &pos, &key, &value)) {
        PyObject *dict_value_copy = DEEP_COPY(value);

        if (dict_value_copy != value) {
            DICT_SET_ITEM(value, key, value);
        }
    }
#else
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    if (((PyDictObject *)dict_value)->ma_used == 0) {
        result = MAKE_DICT_EMPTY();
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
            Py_ssize_t size = DK_ENTRIES_SIZE(dict_mp->ma_keys);

            PyDictObject *result_mp = _Nuitka_AllocatePyDictObject();
            assert(result_mp != NULL);
            result = (PyObject *)result_mp;

            PyDictValues *new_values = _Nuitka_PyDict_new_values(size);
            assert(new_values != NULL);

#if PYTHON_VERSION >= 0x3b0
            // Need to preserve values prefix.
            size_t prefix_size = ((uint8_t *)new_values)[-1];
            memcpy(((char *)new_values) - prefix_size, ((char *)dict_mp->ma_values) - prefix_size, prefix_size - 1);
#endif

            result_mp->ma_values = new_values;
            result_mp->ma_keys = dict_mp->ma_keys;
            result_mp->ma_used = dict_mp->ma_used;

            // This is a manual reference count for the keys.
#ifdef Py_REF_DEBUG
            _Py_RefTotal++;
#endif
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
#if PYTHON_VERSION >= 0x360
            // Fast dictionary copy if it has at least 2/3 space usage. This is most relevant
            // for the DICT_COPY, where it might even be the intention to trigger a shrink with
            // a fresh copy.
            if (dict_mp->ma_values == NULL && IS_COMPACT(dict_mp)) {
            assert(dict_mp->ma_values == NULL);
            assert(dict_mp->ma_keys->dk_refcnt == 1);

            PyDictObject *result_mp = _Nuitka_AllocatePyDictObject();
            result = (PyObject *)result_mp;

            result_mp->ma_values = NULL;
            result_mp->ma_used = dict_mp->ma_used;

            Py_ssize_t keys_size = _Nuitka_Py_PyDict_KeysSize(dict_mp->ma_keys);
            result_mp->ma_keys = (PyDictKeysObject *)PyObject_MALLOC(keys_size);
            assert(result_mp->ma_keys);

            memcpy(result_mp->ma_keys, dict_mp->ma_keys, keys_size);

            // Take reference of all keys and values.
#if PYTHON_VERSION < 0x3b0
            PyDictKeyEntry *entries = DK_ENTRIES(result_mp->ma_keys);
            Py_ssize_t size = DK_ENTRIES_SIZE(result_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &entries[i];
                PyObject *value = entry->me_value;

                if (value != NULL) {
                    PyObject *key = entry->me_key;

                    Py_INCREF(key);

                    value = DEEP_COPY(value);

                    entry->me_value = value;
                }
            }
#else
            PyObject **key_ptr, **value_ptr;
            size_t entry_size;

            bool is_unicode = DK_IS_UNICODE(result_mp->ma_keys);

            if (is_unicode) {
                PyDictUnicodeEntry *ep0 = DK_UNICODE_ENTRIES(result_mp->ma_keys);

                key_ptr = &ep0->me_key;
                value_ptr = &ep0->me_value;
                entry_size = sizeof(PyDictUnicodeEntry) / sizeof(PyObject *);
            } else {
                PyDictKeyEntry *ep0 = DK_ENTRIES(result_mp->ma_keys);

                key_ptr = &ep0->me_key;
                value_ptr = &ep0->me_value;
                entry_size = sizeof(PyDictKeyEntry) / sizeof(PyObject *);
            }

            Py_ssize_t size = DK_ENTRIES_SIZE(result_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *value = *value_ptr;

                if (value != NULL) {
                    value = DEEP_COPY(value);
                    *value_ptr = value;
                    PyObject *key = *key_ptr;
                    Py_INCREF(key);
                }

                value_ptr += entry_size;
                key_ptr += entry_size;
            }
#endif

            // The new keys are an object counted.
#ifdef Py_REF_DEBUG
            _Py_RefTotal++;
#endif

            Nuitka_GC_Track(result_mp);
        } else
#endif
        {
            result = _PyDict_NewPresized(dict_mp->ma_used);

            Py_ssize_t size = DK_ENTRIES_SIZE(dict_mp->ma_keys);

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
    bool had_kw_error = false;

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    result = DICT_COPY(dict_value);

    Py_ssize_t pos = 0;
    PyObject *key, *value;

    while (Nuitka_DictNext(dict_value, &pos, &key, &value)) {
        if (unlikely(!checkKeywordType(key))) {
            had_kw_error = true;
        }
    }
#else
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    if (((PyDictObject *)dict_value)->ma_used == 0) {
        result = MAKE_DICT_EMPTY();
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
                    had_kw_error = true;
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
            Py_ssize_t size = DK_ENTRIES_SIZE(dict_mp->ma_keys);

            PyDictObject *result_mp = _Nuitka_AllocatePyDictObject();
            assert(result_mp != NULL);
            result = (PyObject *)result_mp;

            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &DK_ENTRIES(dict_mp->ma_keys)[i];

                if (entry->me_value != NULL) {
                    PyObject *key = entry->me_key;
                    if (unlikely(!checkKeywordType(key))) {
                        had_kw_error = true;
                    }
                }
            }

            PyDictValues *new_values = _Nuitka_PyDict_new_values(size);
            assert(new_values != NULL);

#if PYTHON_VERSION >= 0x3b0
            // Need to preserve values prefix.
            size_t prefix_size = ((uint8_t *)new_values)[-1];
            memcpy(((char *)new_values) - prefix_size, ((char *)dict_mp->ma_values) - prefix_size, prefix_size - 1);
#endif

            result_mp->ma_values = new_values;
            result_mp->ma_keys = dict_mp->ma_keys;
            result_mp->ma_used = dict_mp->ma_used;

            // This is a manual reference count for the keys.
#ifdef Py_REF_DEBUG
            _Py_RefTotal++;
#endif
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
#if PYTHON_VERSION >= 0x360
            // Fast dictionary copy if it has at least 2/3 space usage. This is most relevant
            // for the DICT_COPY, where it might even be the intention to trigger a shrink with
            // a fresh copy.
            if (dict_mp->ma_values == NULL && IS_COMPACT(dict_mp)) {
            assert(dict_mp->ma_values == NULL);
            assert(dict_mp->ma_keys->dk_refcnt == 1);

            PyDictObject *result_mp = _Nuitka_AllocatePyDictObject();
            result = (PyObject *)result_mp;

            result_mp->ma_values = NULL;
            result_mp->ma_used = dict_mp->ma_used;

            Py_ssize_t keys_size = _Nuitka_Py_PyDict_KeysSize(dict_mp->ma_keys);
            result_mp->ma_keys = (PyDictKeysObject *)PyObject_MALLOC(keys_size);
            assert(result_mp->ma_keys);

            memcpy(result_mp->ma_keys, dict_mp->ma_keys, keys_size);

            // Take reference of all keys and values.
#if PYTHON_VERSION < 0x3b0
            PyDictKeyEntry *entries = DK_ENTRIES(result_mp->ma_keys);
            Py_ssize_t size = DK_ENTRIES_SIZE(result_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &entries[i];
                PyObject *value = entry->me_value;

                if (value != NULL) {
                    PyObject *key = entry->me_key;
                    if (unlikely(!checkKeywordType(key))) {
                        had_kw_error = true;
                    }
                    Py_INCREF(key);

                    Py_INCREF(value);
                }
            }
#else
            PyObject **key_ptr, **value_ptr;
            size_t entry_size;

            bool is_unicode = DK_IS_UNICODE(result_mp->ma_keys);

            if (is_unicode) {
                PyDictUnicodeEntry *ep0 = DK_UNICODE_ENTRIES(result_mp->ma_keys);

                key_ptr = &ep0->me_key;
                value_ptr = &ep0->me_value;
                entry_size = sizeof(PyDictUnicodeEntry) / sizeof(PyObject *);
            } else {
                PyDictKeyEntry *ep0 = DK_ENTRIES(result_mp->ma_keys);

                key_ptr = &ep0->me_key;
                value_ptr = &ep0->me_value;
                entry_size = sizeof(PyDictKeyEntry) / sizeof(PyObject *);
            }

            Py_ssize_t size = DK_ENTRIES_SIZE(result_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyObject *value = *value_ptr;

                if (value != NULL) {

                    Py_INCREF(value);
                    PyObject *key = *key_ptr;
                    if (is_unicode) {
                        if (unlikely(!checkKeywordType(key))) {
                            had_kw_error = true;
                        }
                    }
                    Py_INCREF(key);
                }

                value_ptr += entry_size;
                key_ptr += entry_size;
            }
#endif

            // The new keys are an object counted.
#ifdef Py_REF_DEBUG
            _Py_RefTotal++;
#endif

            Nuitka_GC_Track(result_mp);
        } else
#endif
        {
            result = _PyDict_NewPresized(dict_mp->ma_used);

            Py_ssize_t size = DK_ENTRIES_SIZE(dict_mp->ma_keys);

            for (Py_ssize_t i = 0; i < size; i++) {
                PyDictKeyEntry *entry = &DK_ENTRIES(dict_mp->ma_keys)[i];

                if (entry->me_value != NULL) {
                    PyObject *key = entry->me_key;
                    if (unlikely(!checkKeywordType(key))) {
                        had_kw_error = true;
                    }

                    PyObject *value = entry->me_value;

                    int res = PyDict_SetItem(result, key, value);
                    assert(res == 0);
                }
            }
        }
#endif
    }

#endif

    if (unlikely(had_kw_error)) {
        Py_DECREF(result);
        return NULL;
    }

    return result;
}
