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
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
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
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
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
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
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
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(key);
        }

        if (unlikely(hash == -1)) {
            return -1;
        }
    } else {
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

#if PYTHON_VERSION < 0x300
PyObject *DICT_ITEMS(PyObject *dict) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    PyDictObject *mp = (PyDictObject *)dict;

    PyObject *result;
    Py_ssize_t size;

    /* Preallocate the list of tuples, to avoid allocations during
     * the loop over the items, which could trigger GC, which
     * could resize the dict. :-(
     */
retry:
    size = mp->ma_used;
    result = PyList_New(size);
    CHECK_OBJECT(result);

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = PyTuple_New(2);
        CHECK_OBJECT(item);

        PyList_SET_ITEM(result, i, item);
    }

    if (unlikely(size != mp->ma_used)) {
        // Garbage collection can compatify dictionaries.
        Py_DECREF(result);
        goto retry;
    }

    // Nothing must cause any functions to be called
    PyDictEntry *ep = mp->ma_table;
    Py_ssize_t mask = mp->ma_mask;

    for (Py_ssize_t i = 0, j = 0; i <= mask; i++) {
        PyObject *value = ep[i].me_value;
        if (value != NULL) {
            PyObject *key = ep[i].me_key;
            PyObject *item = PyList_GET_ITEM(result, j);
            PyTuple_SET_ITEM0(item, 0, key);
            PyTuple_SET_ITEM0(item, 1, value);

            j++;
        }
    }

    assert(PyList_GET_SIZE(result) == size);

    return result;
}
#endif

#if PYTHON_VERSION < 0x300
typedef struct {
    PyObject_HEAD PyDictObject *di_dict;
    Py_ssize_t di_used;
    Py_ssize_t di_pos;
    PyObject *di_result;
    Py_ssize_t len;
} dictiterobject;
#endif

#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x350
typedef struct {
    PyObject_HEAD PyDictObject *dv_dict;
} _PyDictViewObject;

#endif

// Generic helper for various dictionary iterations, to be inlined.
static inline PyObject *_MAKE_DICT_ITERATOR(PyDictObject *dict, PyTypeObject *type, bool is_iteritems) {
#if PYTHON_VERSION < 0x300
    dictiterobject *di = PyObject_GC_New(dictiterobject, type);
    CHECK_OBJECT(di);
    Py_INCREF(dict);
    di->di_dict = dict;
    di->di_used = dict->ma_used;
    di->di_pos = 0;
    di->len = dict->ma_used;
    if (is_iteritems) {
        // TODO: Have this as faster variants, we do these sometimes.
        di->di_result = PyTuple_Pack(2, Py_None, Py_None);
        CHECK_OBJECT(di->di_result);
    } else {
        di->di_result = NULL;
    }

    Nuitka_GC_Track(di);
    return (PyObject *)di;
#else
    _PyDictViewObject *dv = PyObject_GC_New(_PyDictViewObject, type);
    CHECK_OBJECT(dv);

    Py_INCREF(dict);
    dv->dv_dict = dict;

    Nuitka_GC_Track(dv);
    return (PyObject *)dv;
#endif
}

PyObject *DICT_ITERITEMS(PyObject *dict) {
    CHECK_OBJECT(dict);

#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictiter_type = NULL;

    if (unlikely(dictiter_type)) {
        dictiter_type = Py_TYPE(PyObject_GetIter(const_dict_empty));
    }

    return _MAKE_DICT_ITERATOR((PyDictObject *)dict, dictiter_type, true);
#elif PYTHON_VERSION < 0x300
    return _MAKE_DICT_ITERATOR((PyDictObject *)dict, &PyDictIterItem_Type, true);
#else
    return _MAKE_DICT_ITERATOR((PyDictObject *)dict, &PyDictItems_Type, true);
#endif
}
