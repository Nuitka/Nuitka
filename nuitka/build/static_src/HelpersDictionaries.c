//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* These helpers are used to work with dictionaries.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// spell-checker: ignore ob_shash dictiterobject dictiteritems_type dictiterkeys_type
// spell-checker: ignore dictitervalues_type dictviewobject dictvaluesview_type dictkeysview_type

PyObject *DICT_GET_ITEM0(PyThreadState *tstate, PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
        hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);

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
        hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);

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
#elif PYTHON_VERSION < 0x3b0
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || PYTHON_VERSION >= 0x3b0
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

PyObject *DICT_GET_ITEM1(PyThreadState *tstate, PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
        hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);

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
        hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);

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
#elif PYTHON_VERSION < 0x3b0
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || PYTHON_VERSION >= 0x3b0
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

#if PYTHON_VERSION >= 0x3c0
static PyObject *Nuitka_CreateKeyError(PyThreadState *tstate, PyObject *key) {
    return (PyObject *)Nuitka_BaseExceptionSingleArg_new(tstate, (PyTypeObject *)PyExc_KeyError, key);
}
#endif

static void SET_CURRENT_EXCEPTION_KEY_ERROR(PyThreadState *tstate, PyObject *key) {
#if PYTHON_VERSION < 0x3c0
    /* Wrap all kinds of tuples, because normalization will later unwrap
     * it, but then that changes the key for the KeyError, which is not
     * welcome. The check is inexact, as the unwrapping one is too.
     */
    if (PyTuple_Check(key) || key == Py_None) {
        PyObject *tuple = MAKE_TUPLE1(tstate, key);

        SET_CURRENT_EXCEPTION_TYPE0_VALUE1(tstate, PyExc_KeyError, tuple);
    } else {
        SET_CURRENT_EXCEPTION_TYPE0_VALUE0(tstate, PyExc_KeyError, key);
    }
#else
    struct Nuitka_ExceptionPreservationItem exception_state = {Nuitka_CreateKeyError(tstate, key)};

    RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
#endif
}

// TODO: This gives a reference, where would often be one time immediate users
// of the value, forcing temporary variable releases on the outside. We need
// to add indication of how long a value is going to be used, so in case where
// we have the knowledge, we can provide the reference or not. Maybe we can
// also include temporary nature of the key and/or dict releases to be done
// inside of such helper code, possibly in template generation, where also
// the hashing check wouldn't be needed anymore.
PyObject *DICT_GET_ITEM_WITH_ERROR(PyThreadState *tstate, PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);

        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;
    PyDictEntry *entry = (dict_object->ma_lookup)(dict_object, key, hash);

    if (unlikely(entry == NULL || entry->me_value == NULL)) {
        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);

        return NULL;
    }

    CHECK_OBJECT(entry->me_value);
    Py_INCREF(entry->me_value);
    return entry->me_value;
#else
    if (!PyUnicode_CheckExact(key) || (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);
        if (unlikely(hash == -1)) {
            return NULL;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;
    PyDictKeyEntry *entry = dict_object->ma_keys->dk_lookup(dict_object, key, hash, &value_addr);

    if (unlikely(entry == NULL || *value_addr == NULL)) {
        if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
            return NULL;
        }

        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);

        return NULL;
    }
#else
#if PYTHON_VERSION < 0x370
    PyObject **value_addr;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value_addr, NULL);
#elif PYTHON_VERSION < 0x3b0
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
            return NULL;
        }

        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);

        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || PYTHON_VERSION >= 0x3b0
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif

    if (unlikely(result == NULL)) {
        if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
            return NULL;
        }

        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);

        return NULL;
    }

    CHECK_OBJECT(result);
    Py_INCREF(result);
    return result;
#endif
}

PyObject *DICT_GET_ITEM_WITH_HASH_ERROR0(PyThreadState *tstate, PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);

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
        hash = HASH_VALUE_WITH_ERROR(tstate, key);
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
#elif PYTHON_VERSION < 0x3b0
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || PYTHON_VERSION >= 0x3b0
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

// TODO: Exact copy of DICT_GET_ITEM_WITH_HASH_ERROR0 with just a Py_INCREF added, we should
// generate these and all other variants rather than manually maintaining them, so we can
// also specialize by type and not just result needs.
PyObject *DICT_GET_ITEM_WITH_HASH_ERROR1(PyThreadState *tstate, PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);
        }

        if (unlikely(hash == -1)) {
            return NULL;
        }
    } else {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);

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
        hash = HASH_VALUE_WITH_ERROR(tstate, key);
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
#elif PYTHON_VERSION < 0x3b0
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || PYTHON_VERSION >= 0x3b0
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

int DICT_HAS_ITEM(PyThreadState *tstate, PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));

    CHECK_OBJECT(key);

    Py_hash_t hash;

// This variant is uncertain about the hashing.
#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITHOUT_ERROR(tstate, key);
        }

        if (unlikely(hash == -1)) {
            return -1;
        }
    } else {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);

        if (unlikely(hash == -1)) {
            return -1;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;
    PyDictEntry *entry = (dict_object->ma_lookup)(dict_object, key, hash);

    if (unlikely(entry == NULL || entry->me_value == NULL)) {
        return 0;
    }

    return 1;
#else
    if (!PyUnicode_CheckExact(key) || (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);
        if (unlikely(hash == -1)) {
            return -1;
        }
    }

    PyDictObject *dict_object = (PyDictObject *)dict;

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;
    PyDictKeyEntry *entry = dict_object->ma_keys->dk_lookup(dict_object, key, hash, &value_addr);

    if (unlikely(entry == NULL || *value_addr == NULL)) {
        return 0;
    }

    return 1;
#else
#if PYTHON_VERSION < 0x370
    PyObject **value_addr;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &value_addr, NULL);
#elif PYTHON_VERSION < 0x3b0
    PyObject *result;
    Py_ssize_t ix = (dict_object->ma_keys->dk_lookup)(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
            return -1;
        }

        return 0;
    }

#if PYTHON_VERSION < 0x370 || PYTHON_VERSION >= 0x3b0
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif

    if (unlikely(result == NULL)) {
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
    result = MAKE_LIST_EMPTY(tstate, size);
    CHECK_OBJECT(result);

    for (Py_ssize_t i = 0; i < size; i++) {
        // Later populated.
        PyObject *item = MAKE_TUPLE_EMPTY(tstate, 2);
        CHECK_OBJECT(item);

        PyList_SET_ITEM(result, i, item);
    }

    if (unlikely(size != mp->ma_used)) {
        // Garbage collection can compactify dictionaries.
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

#if PYTHON_VERSION < 0x300
PyObject *DICT_KEYS(PyObject *dict) {
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
    result = MAKE_LIST_EMPTY(tstate, size);
    CHECK_OBJECT(result);

    if (unlikely(size != mp->ma_used)) {
        // Garbage collection can compactify dictionaries.
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
            PyList_SET_ITEM0(result, j, key);

            j++;
        }
    }

    assert(PyList_GET_SIZE(result) == size);

    return result;
}
#endif

#if PYTHON_VERSION < 0x300
PyObject *DICT_VALUES(PyObject *dict) {
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
    result = MAKE_LIST_EMPTY(tstate, size);
    CHECK_OBJECT(result);

    if (unlikely(size != mp->ma_used)) {
        // Garbage collection can compactify dictionaries.
        Py_DECREF(result);
        goto retry;
    }

    // Nothing must cause any functions to be called
    PyDictEntry *ep = mp->ma_table;
    Py_ssize_t mask = mp->ma_mask;

    for (Py_ssize_t i = 0, j = 0; i <= mask; i++) {
        PyObject *value = ep[i].me_value;
        if (value != NULL) {
            PyList_SET_ITEM0(result, j, value);

            j++;
        }
    }

    assert(PyList_GET_SIZE(result) == size);

    return result;
}
#endif

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
static inline PyObject *_MAKE_DICT_ITERATOR(PyThreadState *tstate, PyDictObject *dict, PyTypeObject *type,
                                            bool is_iteritems) {
    CHECK_OBJECT((PyObject *)dict);
    assert(PyDict_CheckExact((PyObject *)dict));

#if PYTHON_VERSION < 0x300
    dictiterobject *di = (dictiterobject *)Nuitka_GC_New(type);
    CHECK_OBJECT(di);
    Py_INCREF(dict);
    di->di_dict = dict;
    di->di_used = dict->ma_used;
    di->di_pos = 0;
    di->len = dict->ma_used;
    if (is_iteritems) {
        // TODO: Have this as faster variants, we do these sometimes.
        di->di_result = MAKE_TUPLE2(tstate, Py_None, Py_None);
        CHECK_OBJECT(di->di_result);
    } else {
        di->di_result = NULL;
    }

    Nuitka_GC_Track(di);
    return (PyObject *)di;
#else
    _PyDictViewObject *dv = (_PyDictViewObject *)Nuitka_GC_New(type);
    CHECK_OBJECT(dv);

    Py_INCREF(dict);
    dv->dv_dict = dict;

    Nuitka_GC_Track(dv);
    return (PyObject *)dv;
#endif
}

PyObject *DICT_ITERITEMS(PyThreadState *tstate, PyObject *dict) {
#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictiteritems_type = NULL;

    if (unlikely(dictiteritems_type == NULL)) {
        dictiteritems_type =
            Py_TYPE(CALL_FUNCTION_NO_ARGS(tstate, PyObject_GetAttrString(const_dict_empty, "iteritems")));
    }

    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, dictiteritems_type, true);
#elif PYTHON_VERSION < 0x300
    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, &PyDictIterItem_Type, true);
#else
    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, &PyDictItems_Type, true);
#endif
}

PyObject *DICT_ITERKEYS(PyThreadState *tstate, PyObject *dict) {
#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictiterkeys_type = NULL;

    if (unlikely(dictiterkeys_type == NULL)) {
        dictiterkeys_type =
            Py_TYPE(CALL_FUNCTION_NO_ARGS(tstate, PyObject_GetAttrString(const_dict_empty, "iterkeys")));
    }

    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, dictiterkeys_type, false);
#elif PYTHON_VERSION < 0x300
    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, &PyDictIterKey_Type, false);
#else
    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, &PyDictKeys_Type, false);
#endif
}

PyObject *DICT_ITERVALUES(PyThreadState *tstate, PyObject *dict) {
#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictitervalues_type = NULL;

    if (unlikely(dictitervalues_type == NULL)) {
        dictitervalues_type =
            Py_TYPE(CALL_FUNCTION_NO_ARGS(tstate, PyObject_GetAttrString(const_dict_empty, "itervalues")));
    }

    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, dictitervalues_type, false);
#elif PYTHON_VERSION < 0x300
    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, &PyDictIterValue_Type, false);
#else
    return _MAKE_DICT_ITERATOR(tstate, (PyDictObject *)dict, &PyDictValues_Type, false);
#endif
}

typedef struct {
    PyObject_HEAD PyDictObject *dv_dict;
} dictviewobject;

static PyObject *_MAKE_DICT_VIEW(PyDictObject *dict, PyTypeObject *type) {
    CHECK_OBJECT((PyObject *)dict);
    assert(PyDict_CheckExact((PyObject *)dict));

    dictviewobject *dv = (dictviewobject *)Nuitka_GC_New(type);

    CHECK_OBJECT(dv);
    Py_INCREF(dict);
    dv->dv_dict = (PyDictObject *)dict;
    Nuitka_GC_Track(dv);
    return (PyObject *)dv;
}

PyObject *DICT_VIEWKEYS(PyObject *dict) {
#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictkeysview_type = NULL;

    if (unlikely(dictkeysview_type)) {
        dictkeysview_type = Py_TYPE(PyObject_GetIter(PyObject_GetAttrString(const_dict_empty, "viewkeys")));
    }

    return _MAKE_DICT_VIEW((PyDictObject *)dict, dictkeysview_type);
#else
    return _MAKE_DICT_VIEW((PyDictObject *)dict, &PyDictKeys_Type);
#endif
}

PyObject *DICT_VIEWVALUES(PyObject *dict) {
#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictvaluesview_type = NULL;

    if (unlikely(dictvaluesview_type)) {
        dictvaluesview_type = Py_TYPE(PyObject_GetIter(PyObject_GetAttrString(const_dict_empty, "viewvalues")));
    }

    return _MAKE_DICT_VIEW((PyDictObject *)dict, dictvaluesview_type);
#else
    return _MAKE_DICT_VIEW((PyDictObject *)dict, &PyDictValues_Type);
#endif
}

PyObject *DICT_VIEWITEMS(PyObject *dict) {
#if PYTHON_VERSION < 0x270
    static PyTypeObject *dictvaluesview_type = NULL;

    if (unlikely(dictvaluesview_type)) {
        dictvaluesview_type = Py_TYPE(PyObject_GetIter(PyObject_GetAttrString(const_dict_empty, "viewitems")));
    }

    return _MAKE_DICT_VIEW((PyDictObject *)dict, dictvaluesview_type);
#else
    return _MAKE_DICT_VIEW((PyDictObject *)dict, &PyDictItems_Type);
#endif
}

#if PYTHON_VERSION >= 0x300
static PyDictObject *_Nuitka_AllocatePyDictObject(PyThreadState *tstate) {
    PyDictObject *result_mp;

#if NUITKA_DICT_HAS_FREELIST
    // This is the CPython name, spell-checker: ignore numfree

#if PYTHON_VERSION < 0x3d0
    PyDictObject **items = tstate->interp->dict_state.free_list;
    int *numfree = &tstate->interp->dict_state.numfree;
#else
    struct _Py_object_freelists *freelists = _Nuitka_object_freelists_GET(tstate);
    struct _Py_dict_freelist *state = &freelists->dicts;
    PyDictObject **items = state->items;
    int *numfree = &state->numfree;
#endif

    if (*numfree) {
        (*numfree) -= 1;
        result_mp = items[*numfree];

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

#if PYTHON_VERSION >= 0x360
static PyDictKeysObject *_Nuitka_AllocatePyDictKeysObject(PyThreadState *tstate, Py_ssize_t keys_size) {
    // CPython names, spell-checker: ignore numfree,dictkeys
    PyDictKeysObject *dk;

// TODO: Cannot always use cached objects. Need to also consider
// "log2_size == PyDict_LOG_MINSIZE && unicode" as a criterion,
// seems it can only be used for the smallest keys type.
#if NUITKA_DICT_HAS_FREELIST && 0
#if PYTHON_VERSION < 0x3d0
    PyDictKeysObject **items = tstate->interp->dict_state.keys_free_list;
    int *numfree = &tstate->interp->dict_state.keys_numfree;
#else
    struct _Py_object_freelists *freelists = _Nuitka_object_freelists_GET(tstate);
    struct _Py_dictkeys_freelist *state = &freelists->dictkeys;
    PyDictKeysObject **items = state->items;
    int *numfree = &state->numfree;
#endif

    if (*numfree) {
        (*numfree) -= 1;
        dk = items[*numfree];
    } else
#endif
    {
#if PYTHON_VERSION < 0x3d0
        dk = (PyDictKeysObject *)NuitkaObject_Malloc(keys_size);
#else
        dk = (PyDictKeysObject *)NuitkaMem_Malloc(keys_size);
#endif
    }

    return dk;
}
#endif

#if PYTHON_VERSION >= 0x360 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT)

// Usable fraction of keys.
#define DK_USABLE_FRACTION(n) (((n) << 1) / 3)

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

#include "HelpersDictionariesGenerated.c"

void DICT_CLEAR(PyObject *dict) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    // TODO: Could inline this for enhanced optimization, but it does
    // some pretty sophisticated memory handling.
    PyDict_Clear(dict);
}

#if PYTHON_VERSION >= 0x3b0
static inline int Nuitka_py_get_index_from_order(PyDictObject *mp, Py_ssize_t i) {
    assert(mp->ma_used <= SHARED_KEYS_MAX_SIZE);
    assert(i < (((char *)mp->ma_values)[-2]));

    return ((char *)mp->ma_values)[-3 - i];
}
#endif

#if PYTHON_VERSION >= 0x3b0

static inline Py_ssize_t Nuitka_Py_dictkeys_get_index(const PyDictKeysObject *keys, Py_ssize_t i) {
    int log2size = DK_LOG_SIZE(keys);
    Py_ssize_t ix;

    if (log2size < 8) {
        const int8_t *indices = (const int8_t *)(keys->dk_indices);
        ix = indices[i];
    } else if (log2size < 16) {
        const int16_t *indices = (const int16_t *)(keys->dk_indices);
        ix = indices[i];
    }
#if SIZEOF_VOID_P > 4
    else if (log2size >= 32) {
        const int64_t *indices = (const int64_t *)(keys->dk_indices);
        ix = indices[i];
    }
#endif
    else {
        const int32_t *indices = (const int32_t *)(keys->dk_indices);
        ix = indices[i];
    }

    assert(ix >= DKIX_DUMMY);
    return ix;
}

static inline Py_hash_t Nuitka_Py_unicode_get_hash(PyObject *o) { return _PyASCIIObject_CAST(o)->hash; }

// From CPython
#define PERTURB_SHIFT 5

static Py_ssize_t Nuitka_Py_unicodekeys_lookup_generic(PyDictObject *mp, PyDictKeysObject *dk, PyObject *key,
                                                       Py_hash_t hash) {
    PyDictUnicodeEntry *ep0 = DK_UNICODE_ENTRIES(dk);

    size_t mask = DK_MASK(dk);
    size_t perturb = hash;
    size_t i = (size_t)hash & mask;

    while (1) {
        Py_ssize_t ix = Nuitka_Py_dictkeys_get_index(dk, i);

        if (ix >= 0) {
            PyDictUnicodeEntry *ep = &ep0[ix];

            assert(ep->me_key != NULL);
            assert(PyUnicode_CheckExact(ep->me_key));

            if (ep->me_key == key) {
                return ix;
            }

            if (Nuitka_Py_unicode_get_hash(ep->me_key) == hash) {
                PyObject *startkey = ep->me_key;
                Py_INCREF(startkey);
                nuitka_bool cmp = RICH_COMPARE_EQ_NBOOL_UNICODE_OBJECT(startkey, key);
                Py_DECREF(startkey);

                if (unlikely(cmp == NUITKA_BOOL_EXCEPTION)) {
                    return DKIX_ERROR;
                }

                if (dk == mp->ma_keys && ep->me_key == startkey) {
                    if (cmp == NUITKA_BOOL_TRUE) {
                        return ix;
                    }
                } else {
                    // In case of changed dictionary, trigger restart in caller.
                    return DKIX_KEY_CHANGED;
                }
            }
        } else if (ix == DKIX_EMPTY) {
            return DKIX_EMPTY;
        }
        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }

    NUITKA_CANNOT_GET_HERE("Nuitka_Py_unicodekeys_lookup_generic failed");
}

Py_ssize_t Nuitka_Py_unicodekeys_lookup_unicode(PyDictKeysObject *dk, PyObject *key, Py_hash_t hash) {
    assert(PyUnicode_CheckExact(key));
    assert(dk->dk_kind != DICT_KEYS_GENERAL);

    PyDictUnicodeEntry *ep0 = DK_UNICODE_ENTRIES(dk);

    size_t mask = DK_MASK(dk);
    size_t perturb = hash;
    size_t i = (size_t)hash & mask;

    while (true) {
        Py_ssize_t ix = Nuitka_Py_dictkeys_get_index(dk, i);

        // Found it.
        if (ix >= 0) {
            PyDictUnicodeEntry *ep = &ep0[ix];
            assert(ep->me_key != NULL);
            assert(PyUnicode_CheckExact(ep->me_key));

            if (ep->me_key == key || (Nuitka_Py_unicode_get_hash(ep->me_key) == hash &&
                                      RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(ep->me_key, key))) {
                return ix;
            }
        } else if (ix == DKIX_EMPTY) {
            return DKIX_EMPTY;
        }
        perturb >>= PERTURB_SHIFT;

        i = mask & (i * 5 + perturb + 1);
        ix = Nuitka_Py_dictkeys_get_index(dk, i);

        if (ix >= 0) {
            PyDictUnicodeEntry *ep = &ep0[ix];

            assert(ep->me_key != NULL);
            assert(PyUnicode_CheckExact(ep->me_key));

            if (ep->me_key == key || (Nuitka_Py_unicode_get_hash(ep->me_key) == hash &&
                                      RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(ep->me_key, key))) {
                return ix;
            }
        } else if (ix == DKIX_EMPTY) {
            return DKIX_EMPTY;
        }

        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }

    NUITKA_CANNOT_GET_HERE("Nuitka_Py_unicodekeys_lookup_unicode failed");
}

// Search key from Generic table.
static Py_ssize_t Nuitka_Py_dictkeys_generic_lookup(PyDictObject *mp, PyDictKeysObject *dk, PyObject *key,
                                                    Py_hash_t hash) {
    PyDictKeyEntry *ep0 = DK_ENTRIES(dk);

    size_t mask = DK_MASK(dk);
    size_t perturb = hash;
    size_t i = (size_t)hash & mask;

    while (1) {
        Py_ssize_t ix = Nuitka_Py_dictkeys_get_index(dk, i);

        if (ix >= 0) {
            PyDictKeyEntry *ep = &ep0[ix];
            assert(ep->me_key != NULL);
            if (ep->me_key == key) {
                return ix;
            }
            if (ep->me_hash == hash) {
                PyObject *startkey = ep->me_key;
                Py_INCREF(startkey);
                nuitka_bool cmp = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(startkey, key);
                Py_DECREF(startkey);
                if (cmp == NUITKA_BOOL_EXCEPTION) {
                    return DKIX_ERROR;
                }
                if (dk == mp->ma_keys && ep->me_key == startkey) {
                    if (cmp == NUITKA_BOOL_TRUE) {
                        return ix;
                    }
                } else {
                    // In case of changed dictionary, trigger restart in caller.
                    return DKIX_KEY_CHANGED;
                }
            }
        } else if (ix == DKIX_EMPTY) {
            return DKIX_EMPTY;
        }
        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }
}

Py_ssize_t Nuitka_PyDictLookup(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr) {
    PyDictKeysObject *dk;
    DictKeysKind kind;
    Py_ssize_t ix;

restart:
    dk = mp->ma_keys;
    kind = (DictKeysKind)dk->dk_kind;

    if (kind != DICT_KEYS_GENERAL) {
        if (PyUnicode_CheckExact(key)) {
            ix = Nuitka_Py_unicodekeys_lookup_unicode(dk, key, hash);
        } else {
            ix = Nuitka_Py_unicodekeys_lookup_generic(mp, dk, key, hash);

            // Dictionary lookup changed the dictionary, retry.
            if (ix == DKIX_KEY_CHANGED) {
                goto restart;
            }
        }

        if (ix >= 0) {
            if (kind == DICT_KEYS_SPLIT) {
                *value_addr = &mp->ma_values->values[ix];
            } else {
                *value_addr = &DK_UNICODE_ENTRIES(dk)[ix].me_value;
            }
        } else {
            *value_addr = NULL;
        }
    } else {
        ix = Nuitka_Py_dictkeys_generic_lookup(mp, dk, key, hash);

        // Dictionary lookup changed the dictionary, retry.
        if (ix == DKIX_KEY_CHANGED) {
            goto restart;
        }

        if (ix >= 0) {
            *value_addr = &DK_ENTRIES(dk)[ix].me_value;
        } else {
            *value_addr = NULL;
        }
    }

    return ix;
}

Py_ssize_t Nuitka_PyDictLookupStr(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr) {
    assert(PyUnicode_CheckExact(key));

    PyDictKeysObject *dk = mp->ma_keys;
    assert(dk->dk_kind != DICT_KEYS_GENERAL);

    Py_ssize_t ix = Nuitka_Py_unicodekeys_lookup_unicode(dk, key, hash);

    if (ix >= 0) {
        if (dk->dk_kind == DICT_KEYS_SPLIT) {
            *value_addr = &mp->ma_values->values[ix];
        } else {
            *value_addr = &DK_UNICODE_ENTRIES(dk)[ix].me_value;
        }
    } else {
        *value_addr = NULL;
    }

    return ix;
}

#endif

bool Nuitka_DictNext(PyObject *dict, Py_ssize_t *pos, PyObject **key_ptr, PyObject **value_ptr) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));
    assert(key_ptr != NULL);
    assert(value_ptr != NULL);

#if PYTHON_VERSION < 0x300
    Py_ssize_t i = *pos;

    PyDictEntry *ep = ((PyDictObject *)dict)->ma_table;
    Py_ssize_t mask = ((PyDictObject *)dict)->ma_mask;

    while (i <= mask && ep[i].me_value == NULL) {
        i++;
    }

    *pos = i + 1;

    if (i > mask) {
        return false;
    }

    *key_ptr = ep[i].me_key;
    *value_ptr = ep[i].me_value;

    return true;

#elif PYTHON_VERSION < 0x360
    PyDictObject *mp = (PyDictObject *)dict;
    PyObject **dict_value_ptr;
    Py_ssize_t offset;

    Py_ssize_t i = *pos;
    assert(i >= 0);

    if (mp->ma_values) {
        dict_value_ptr = &mp->ma_values[i];
        offset = sizeof(PyObject *);
    } else {
        dict_value_ptr = &mp->ma_keys->dk_entries[i].me_value;
        offset = sizeof(PyDictKeyEntry);
    }

    Py_ssize_t mask = DK_MASK(mp->ma_keys);

    while ((i <= mask) && (*dict_value_ptr == NULL)) {
        dict_value_ptr = (PyObject **)(((char *)dict_value_ptr) + offset);
        i++;
    }

    if (i > mask) {
        return false;
    }

    *key_ptr = mp->ma_keys->dk_entries[i].me_key;
    *value_ptr = *dict_value_ptr;
    *pos = i + 1;

    return true;

#elif PYTHON_VERSION < 0x3b0
    PyDictObject *mp = (PyDictObject *)dict;
    PyDictKeyEntry *entry;
    PyObject *value;

    Py_ssize_t i = *pos;
    assert(i >= 0);

    if (mp->ma_values) {
        if (i >= mp->ma_used) {
            return false;
        }

        entry = &DK_ENTRIES(mp->ma_keys)[i];
        value = DK_VALUE(mp, i);

        assert(value != NULL);
    } else {
        Py_ssize_t n = mp->ma_keys->dk_nentries;

        if (i >= n) {
            return false;
        }

        entry = &DK_ENTRIES(mp->ma_keys)[i];

        while (i < n && entry->me_value == NULL) {
            entry += 1;
            i += 1;
        }

        if (i >= n) {
            return false;
        }

        value = entry->me_value;
    }

    *pos = i + 1;

    *key_ptr = entry->me_key;
    *value_ptr = value;

    return true;
#else
    PyDictObject *mp = (PyDictObject *)dict;
    Py_ssize_t i = *pos;
    PyObject *key, *value;

    if (mp->ma_values) {
        // Shared keys dictionary.
        assert(mp->ma_used <= SHARED_KEYS_MAX_SIZE);

        if (i >= mp->ma_used) {
            return false;
        }

        int index = Nuitka_py_get_index_from_order(mp, i);
        value = mp->ma_values->values[index];

        key = DK_UNICODE_ENTRIES(mp->ma_keys)[index].me_key;

        assert(value != NULL);
    } else {
        Py_ssize_t n = mp->ma_keys->dk_nentries;

        if (i >= n) {
            return false;
        }

        // Unicode keys or general keys have different sizes, make sure to index
        // the right type, the algorithm is the same however.
        if (DK_IS_UNICODE(mp->ma_keys)) {
            PyDictUnicodeEntry *entry_ptr = &DK_UNICODE_ENTRIES(mp->ma_keys)[i];

            while (i < n && entry_ptr->me_value == NULL) {
                entry_ptr++;
                i++;
            }

            if (i >= n) {
                return false;
            }

            key = entry_ptr->me_key;
            value = entry_ptr->me_value;
        } else {
            PyDictKeyEntry *entry_ptr = &DK_ENTRIES(mp->ma_keys)[i];

            while (i < n && entry_ptr->me_value == NULL) {
                entry_ptr++;
                i++;
            }

            if (i >= n) {
                return false;
            }

            key = entry_ptr->me_key;
            value = entry_ptr->me_value;
        }
    }

    *pos = i + 1;

    *key_ptr = key;
    *value_ptr = value;

    return true;
#endif
}

PyObject *TO_DICT(PyThreadState *tstate, PyObject *seq_obj, PyObject *dict_obj) {
    PyObject *result;

    if (seq_obj != NULL) {
        CHECK_OBJECT(seq_obj);

        // Fast path for dictionaries.
        if (PyDict_CheckExact(seq_obj)) {
            result = DICT_COPY(tstate, seq_obj);
        } else {
            result = MAKE_DICT_EMPTY(tstate);

            Py_INCREF(seq_obj);

#if PYTHON_VERSION >= 0x300
            int res = HAS_ATTR_BOOL2(tstate, seq_obj, const_str_plain_keys);

            if (unlikely(res == -1)) {
                Py_DECREF(seq_obj);
                return NULL;
            }
#else
            int res = HAS_ATTR_BOOL(tstate, seq_obj, const_str_plain_keys) ? 1 : 0;
#endif

            if (res) {
                res = PyDict_Merge(result, seq_obj, 1);
            } else {
                res = PyDict_MergeFromSeq2(result, seq_obj, 1);
            }

            Py_DECREF(seq_obj);

            if (unlikely(res == -1)) {
                return NULL;
            }
        }
    } else {
        result = MAKE_DICT_EMPTY(tstate);
    }

    // TODO: Should specialize for dict_obj/seq_obj presence to save a bit of time
    // and complexity.
    if (dict_obj != NULL) {
        CHECK_OBJECT(dict_obj);

        int res = PyDict_Merge(result, dict_obj, 1);

        if (unlikely(res == -1)) {
            return NULL;
        }
    }

    return result;
}

#if _NUITKA_MAINTAIN_DICT_VERSION_TAG
uint64_t nuitka_dict_version_tag_counter = ((uint64_t)1) << 32;
#endif

#if NUITKA_DICT_HAS_FREELIST
PyObject *MAKE_DICT_EMPTY(PyThreadState *tstate) {
    PyDictObject *empty_dict_mp = (PyDictObject *)const_dict_empty;

#if PYTHON_VERSION < 0x3c0
    empty_dict_mp->ma_keys->dk_refcnt++;
#endif

    PyDictObject *result_mp = _Nuitka_AllocatePyDictObject(tstate);

    result_mp->ma_keys = empty_dict_mp->ma_keys;
    result_mp->ma_values = empty_dict_mp->ma_values;
    result_mp->ma_used = 0;
#if PYTHON_VERSION >= 0x3c0
    result_mp->ma_version_tag = DICT_NEXT_VERSION(_PyInterpreterState_GET());
#elif PYTHON_VERSION >= 0x360
    result_mp->ma_version_tag = 1;
#endif

    // Key reference needs to be counted on older Python
#if defined(Py_REF_DEBUG) && PYTHON_VERSION < 0x3c0
    _Py_RefTotal++;
#endif

    // No Nuitka_GC_Track for the empty dictionary.
    return (PyObject *)result_mp;
}
#endif

PyObject *MAKE_DICT(PyObject **pairs, Py_ssize_t size) {
    PyObject *result = _PyDict_NewPresized(size);

    // Reject usage like this.
    assert(size > 0);
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *key = pairs[i * 2];
        PyObject *value = pairs[i * 2 + 1];

        int res = PyDict_SetItem(result, key, value);

        if (unlikely(res != 0)) {
            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
}

PyObject *MAKE_DICT_X(PyObject **pairs, Py_ssize_t size) {
    PyObject *result = _PyDict_NewPresized(size);

    // Reject usage like this.
    assert(size > 0);
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *value = pairs[i * 2 + 1];

        if (value != NULL) {
            PyObject *key = pairs[i * 2];
            CHECK_OBJECT(key);
            CHECK_OBJECT(value);

            int res = PyDict_SetItem(result, key, value);

            if (unlikely(res != 0)) {
                Py_DECREF(result);
                return NULL;
            }
        }
    }

    return result;
}

PyObject *MAKE_DICT_X_CSTR(char const **keys, PyObject **values, Py_ssize_t size) {
    PyObject *result = _PyDict_NewPresized(size);

    // Reject usage like this.
    assert(size > 0);
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *value = values[i];

        if (value != NULL) {
            CHECK_OBJECT(value);

            int res = PyDict_SetItemString(result, keys[i], value);

            if (unlikely(res != 0)) {
                Py_DECREF(result);
                return NULL;
            }
        }
    }

    return result;
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
