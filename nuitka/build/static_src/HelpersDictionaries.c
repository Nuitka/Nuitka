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
/* This helpers is used to work with dictionaries.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *DICT_GET_ITEM0(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (!PyString_CheckExact(key) || (hash = ((PyStringObject *)key)->ob_shash) == -1) {
        hash = HASH_VALUE_WITHOUT_ERROR(key);

        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;
    PyDictEntry *entry = (dict_object->ma_lookup)(dict_object, key, hash);

    if (unlikely(entry == NULL || entry->me_value == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(entry->me_value);
    return entry->me_value;
#else
    if (!PyUnicode_CheckExact(key) || (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = HASH_VALUE_WITHOUT_ERROR(key);

        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;
    PyDictKeyEntry *entry = dict_object->ma_keys->dk_lookup(dict_object, key, hash, &value_addr);

    if (unlikely(entry == NULL || *value_addr == NULL)) {
        return NULL;
    }
#else
#if PYTHON_VERSION < 0x370
    PyObject **value_addr;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value_addr, NULL);

#else
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif
    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(result);
    return result;
#endif
}

PyObject *DICT_GET_ITEM1(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (!PyString_CheckExact(key) || (hash = ((PyStringObject *)key)->ob_shash) == -1) {
        hash = HASH_VALUE_WITHOUT_ERROR(key);

        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;
    PyDictEntry *entry = (dict_object->ma_lookup)(dict_object, key, hash);

    if (unlikely(entry == NULL || entry->me_value == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(entry->me_value);
    Py_INCREF(entry->me_value);
    return entry->me_value;
#else
    if (!PyUnicode_CheckExact(key) || (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = HASH_VALUE_WITHOUT_ERROR(key);

        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;
    PyDictKeyEntry *entry = dict_object->ma_keys->dk_lookup(dict_object, key, hash, &value_addr);

    if (unlikely(entry == NULL || *value_addr == NULL)) {
        return NULL;
    }
#else
#if PYTHON_VERSION < 0x370
    PyObject **value_addr;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value_addr, NULL);

#else
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif
    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(result);
    Py_INCREF(result);
    return result;
#endif
}

static void SET_KEY_ERROR_EXCEPTION(PyObject *key) {
    /* Wrap all kinds of tuples, because normalization will later unwrap
     * it, but then that changes the key for the KeyError, which is not
     * welcome. The check is inexact, as the unwrapping one is too.
     */
    if (PyTuple_Check(key) || key == Py_None) {
        PyObject *tuple = PyTuple_Pack(1, key);

        SET_CURRENT_EXCEPTION_TYPE0_VALUE1(PyExc_KeyError, tuple);
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_VALUE0(PyExc_KeyError, key);
    }
}

// TODO: This gives a reference, where would often be one time immediate users
// of the value, forcing temporary variable releases on the outside. We need
// to add indication of how long a value is going to be used, so in case where
// we have the knowledge, we can provide the reference or not. Maybe we can
// also include temporary nature of the key and/or dict releases to be done
// inside of such helper code, possibly in template generation, where also
// the hashing check wouldn't be needed anymore.
PyObject *DICT_GET_ITEM_WITH_ERROR(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (!PyString_CheckExact(key) || (hash = ((PyStringObject *)key)->ob_shash) == -1) {
        hash = HASH_VALUE_WITH_ERROR(key);
        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;
    PyDictEntry *entry = (dict_object->ma_lookup)(dict_object, key, hash);

    if (unlikely(entry == NULL || entry->me_value == NULL)) {
        if (unlikely(ERROR_OCCURRED())) {
            return NULL;
        }

        SET_KEY_ERROR_EXCEPTION(key);

        return NULL;
    }

    CHECK_OBJECT(entry->me_value);
    Py_INCREF(entry->me_value);
    return entry->me_value;
#else
    if (!PyUnicode_CheckExact(key) || (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = HASH_VALUE_WITH_ERROR(key);
        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;
    PyDictKeyEntry *entry = dict_object->ma_keys->dk_lookup(dict_object, key, hash, &value_addr);

    if (unlikely(entry == NULL || *value_addr == NULL)) {
        if (unlikely(ERROR_OCCURRED())) {
            return NULL;
        }

        SET_KEY_ERROR_EXCEPTION(key);

        return NULL;
    }
#else
#if PYTHON_VERSION < 0x370
    PyObject **value_addr;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value_addr, NULL);

#else
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#endif

    if (unlikely(ix < 0)) {
        if (unlikely(ERROR_OCCURRED())) {
            return NULL;
        }

        SET_KEY_ERROR_EXCEPTION(key);

        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif

    if (unlikely(result == NULL)) {
        if (unlikely(ERROR_OCCURRED())) {
            return NULL;
        }

        SET_KEY_ERROR_EXCEPTION(key);

        return NULL;
    }

    CHECK_OBJECT(result);
    Py_INCREF(result);
    return result;
#endif
}

int DICT_HAS_ITEM(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (!PyString_CheckExact(key) || (hash = ((PyStringObject *)key)->ob_shash) == -1) {
        hash = HASH_VALUE_WITH_ERROR(key);
        if (unlikely(hash == -1)) {
            return -1;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;
    PyDictEntry *entry = (dict_object->ma_lookup)(dict_object, key, hash);

    if (unlikely(entry == NULL || entry->me_value == NULL)) {
        if (unlikely(ERROR_OCCURRED())) {
            return -1;
        }

        return 0;
    }

    return 1;
#else
    if (!PyUnicode_CheckExact(key) || (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = HASH_VALUE_WITH_ERROR(key);
        if (unlikely(hash == -1)) {
            return -1;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;
    PyDictKeyEntry *entry = dict_object->ma_keys->dk_lookup(dict_object, key, hash, &value_addr);

    if (unlikely(entry == NULL || *value_addr == NULL)) {
        if (unlikely(ERROR_OCCURRED())) {
            return -1;
        }

        return 0;
    }

    return 1;
#else
#if PYTHON_VERSION < 0x370
    PyObject **value_addr;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value_addr, NULL);

#else
    PyObject *value;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value);
#endif

    if (unlikely(ix < 0)) {
        if (unlikely(ERROR_OCCURRED())) {
            return -1;
        }

        return 0;
    }
#endif
    return 1;
#endif
}
