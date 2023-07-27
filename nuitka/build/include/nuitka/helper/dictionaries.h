//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_DICTIONARIES_H__
#define __NUITKA_DICTIONARIES_H__

static inline Py_ssize_t DICT_SIZE(PyObject *dict) {
    CHECK_OBJECT(dict);
    assert(PyDict_CheckExact(dict));

    return ((PyDictObject *)dict)->ma_used;
}

static inline PyDictObject *MODULE_DICT(PyObject *module) {
    CHECK_OBJECT(module);

    PyDictObject *dict = (PyDictObject *)(((PyModuleObject *)module)->md_dict);

    return dict;
}

#if PYTHON_VERSION < 0x300
// Quick dictionary lookup for a string value.

typedef PyDictEntry *Nuitka_DictEntryHandle;

static PyDictEntry *GET_STRING_DICT_ENTRY(PyDictObject *dict, Nuitka_StringObject *key) {
    assert(PyDict_CheckExact(dict));
    assert(Nuitka_String_CheckExact(key));

    Py_hash_t hash = key->ob_shash;

    // Only improvement would be to identify how to ensure that the hash is
    // computed already. Calling hash early on could do that potentially.
    if (hash == -1) {
        hash = PyString_Type.tp_hash((PyObject *)key);
        key->ob_shash = hash;
    }

    PyDictEntry *entry = dict->ma_lookup(dict, (PyObject *)key, hash);

    // The "entry" cannot be NULL, it can only be empty for a string dict
    // lookup, but at least assert it.
    assert(entry != NULL);

    return entry;
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_DICT_ENTRY_VALUE(Nuitka_DictEntryHandle handle) { return handle->me_value; }

NUITKA_MAY_BE_UNUSED static void SET_DICT_ENTRY_VALUE(Nuitka_DictEntryHandle handle, PyObject *value) {
    handle->me_value = value;
}

static PyObject *GET_STRING_DICT_VALUE(PyDictObject *dict, Nuitka_StringObject *key) {
    return GET_STRING_DICT_ENTRY(dict, key)->me_value;
}

#else

// Python 3.3 or higher.

// Quick dictionary lookup for a string value.

#if PYTHON_VERSION < 0x3b0
typedef struct {
    /* Cached hash code of me_key. */
    Py_hash_t me_hash;
    PyObject *me_key;
    PyObject *me_value; /* This field is only meaningful for combined tables */
} PyDictKeyEntry;
#endif

#if PYTHON_VERSION < 0x360
typedef PyDictKeyEntry *(*dict_lookup_func)(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr);
#elif PYTHON_VERSION < 0x370
typedef Py_ssize_t (*dict_lookup_func)(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr,
                                       Py_ssize_t *hashpos);
#else
typedef Py_ssize_t (*dict_lookup_func)(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject **value_addr);
#endif

// Taken from CPython3.3 "Objects/dictobject.c", lives in "Objects/dict-common.h" later

#if PYTHON_VERSION < 0x3b0

#define DK_SIZE(dk) ((dk)->dk_size)
struct _dictkeysobject {
    Py_ssize_t dk_refcnt;
    Py_ssize_t dk_size;
    dict_lookup_func dk_lookup;
    Py_ssize_t dk_usable;
#if PYTHON_VERSION < 0x360
    PyDictKeyEntry dk_entries[1];
#else
    Py_ssize_t dk_nentries;
#if PYTHON_VERSION < 0x370
    union {
        int8_t as_1[8];
        int16_t as_2[4];
        int32_t as_4[2];
#if SIZEOF_VOID_P > 4
        int64_t as_8[1];
#endif
    } dk_indices;
#else
    char dk_indices[];
#endif
#endif
};

#endif

// Taken from Objects/dictobject.c of CPython 3.6
#if PYTHON_VERSION >= 0x360

#if PYTHON_VERSION < 0x3b0
#if SIZEOF_VOID_P > 4
#define DK_IXSIZE(dk)                                                                                                  \
    (DK_SIZE(dk) <= 0xff ? 1 : DK_SIZE(dk) <= 0xffff ? 2 : DK_SIZE(dk) <= 0xffffffff ? 4 : sizeof(int64_t))
#else
#define DK_IXSIZE(dk) (DK_SIZE(dk) <= 0xff ? 1 : DK_SIZE(dk) <= 0xffff ? 2 : sizeof(int32_t))
#endif

#if PYTHON_VERSION < 0x370
#define DK_ENTRIES(dk) ((PyDictKeyEntry *)(&(dk)->dk_indices.as_1[DK_SIZE(dk) * DK_IXSIZE(dk)]))
#else
#define DK_ENTRIES(dk) ((PyDictKeyEntry *)(&((int8_t *)((dk)->dk_indices))[DK_SIZE(dk) * DK_IXSIZE(dk)]))
#endif

#endif

#else
#define DK_ENTRIES(dk) (dk->dk_entries)
#endif

#if PYTHON_VERSION < 0x3b0
#define DK_VALUE(dk, i) dk->ma_values[i]
#else
#define DK_VALUE(dk, i) dk->ma_values->values[i]
#endif

#define DK_MASK(dk) (DK_SIZE(dk) - 1)

typedef PyObject **Nuitka_DictEntryHandle;

#if PYTHON_VERSION >= 0x3b0
extern Py_ssize_t Nuitka_PyDictLookup(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr);
extern Py_ssize_t Nuitka_PyDictLookupStr(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr);
#endif

static Nuitka_DictEntryHandle GET_STRING_DICT_ENTRY(PyDictObject *dict, Nuitka_StringObject *key) {
    assert(PyDict_CheckExact(dict));
    assert(Nuitka_String_CheckExact(key));

    Py_hash_t hash = key->_base._base.hash;

    // Only improvement would be to identify how to ensure that the hash is computed
    // already. Calling hash early on could do that potentially.
    if (hash == -1) {
        hash = PyUnicode_Type.tp_hash((PyObject *)key);
        key->_base._base.hash = hash;
    }

#if PYTHON_VERSION < 0x360
    PyObject **value_addr;

    PyDictKeyEntry *entry = dict->ma_keys->dk_lookup(dict, (PyObject *)key, hash, &value_addr);

    // The "entry" cannot be NULL, it can only be empty for a string dict lookup, but at
    // least assert it.
    assert(entry != NULL);

    return value_addr;

#elif PYTHON_VERSION < 0x370
    PyObject **value_addr;

    // TODO: Find out what the returned Py_ssize_t "ix" might be good for.
    dict->ma_keys->dk_lookup(dict, (PyObject *)key, hash, &value_addr,
                             NULL // hashpos, TODO: Find out what we could use it for.
    );

    return value_addr;
#elif PYTHON_VERSION < 0x3b0
    PyObject *value;

    Py_ssize_t ix = dict->ma_keys->dk_lookup(dict, (PyObject *)key, hash, &value);

    if (value == NULL) {
        return NULL;
#ifndef PY_NOGIL
    } else if (_PyDict_HasSplitTable(dict)) {
        return &dict->ma_values[ix];
#endif
    } else {
        return &DK_ENTRIES(dict->ma_keys)[ix].me_value;
    }

#else
    // Will be written by Nuitka_PyDictLookupStr in all cases.
    PyObject **value;
    Py_ssize_t found = Nuitka_PyDictLookupStr(dict, (PyObject *)key, hash, &value);
    assert(found != DKIX_ERROR);

    return value;
#endif
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_DICT_ENTRY_VALUE(Nuitka_DictEntryHandle handle) { return *handle; }

NUITKA_MAY_BE_UNUSED static void SET_DICT_ENTRY_VALUE(Nuitka_DictEntryHandle handle, PyObject *value) {
    *handle = value;
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_STRING_DICT_VALUE(PyDictObject *dict, Nuitka_StringObject *key) {
    Nuitka_DictEntryHandle handle = GET_STRING_DICT_ENTRY(dict, key);

#if PYTHON_VERSION >= 0x360
    if (handle == NULL) {
        return NULL;
    }
#endif

    return GET_DICT_ENTRY_VALUE(handle);
}

#endif

NUITKA_MAY_BE_UNUSED static bool DICT_SET_ITEM(PyObject *dict, PyObject *key, PyObject *value) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    CHECK_OBJECT(key);
    CHECK_OBJECT(value);

    int status = PyDict_SetItem(dict, key, value);

    if (unlikely(status != 0)) {
        return false;
    }

    return true;
}

NUITKA_MAY_BE_UNUSED static bool DICT_REMOVE_ITEM(PyObject *dict, PyObject *key) {
    int status = PyDict_DelItem(dict, key);

    if (unlikely(status == -1)) {
        return false;
    }

    return true;
}

// Get dict lookup for a key, similar to PyDict_GetItemWithError, ref returned
extern PyObject *DICT_GET_ITEM_WITH_ERROR(PyObject *dict, PyObject *key);

// Get dict lookup for a key, with only hash error, does not create KeyError, 1=ref returned, 0=not
extern PyObject *DICT_GET_ITEM_WITH_HASH_ERROR1(PyObject *dict, PyObject *key);
extern PyObject *DICT_GET_ITEM_WITH_HASH_ERROR0(PyObject *dict, PyObject *key);

// Get dict lookup for a key, similar to PyDict_GetItem, 1=ref returned, 0=not
extern PyObject *DICT_GET_ITEM1(PyObject *dict, PyObject *key);
extern PyObject *DICT_GET_ITEM0(PyObject *dict, PyObject *key);

// Get dict lookup for a key, similar to PyDict_Contains
extern int DICT_HAS_ITEM(PyObject *dict, PyObject *key);

// Convert to dictionary, helper for built-in "dict" mainly.
extern PyObject *TO_DICT(PyObject *seq_obj, PyObject *dict_obj);

NUITKA_MAY_BE_UNUSED static void UPDATE_STRING_DICT0(PyDictObject *dict, Nuitka_StringObject *key, PyObject *value) {
    CHECK_OBJECT(value);

    Nuitka_DictEntryHandle entry = GET_STRING_DICT_ENTRY(dict, key);

#if PYTHON_VERSION >= 0x360
    if (entry == NULL) {
        DICT_SET_ITEM((PyObject *)dict, (PyObject *)key, value);
        return;
    }
#endif

    PyObject *old = GET_DICT_ENTRY_VALUE(entry);

    // Values are more likely (more often) set than not set, in that case
    // speculatively try the quickest access method.
    if (likely(old != NULL)) {
        Py_INCREF(value);
        SET_DICT_ENTRY_VALUE(entry, value);

        CHECK_OBJECT(old);

        Py_DECREF(old);
    } else {
        DICT_SET_ITEM((PyObject *)dict, (PyObject *)key, value);
    }
}

NUITKA_MAY_BE_UNUSED static void UPDATE_STRING_DICT_INPLACE(PyDictObject *dict, Nuitka_StringObject *key,
                                                            PyObject *value) {
    CHECK_OBJECT(value);

    Nuitka_DictEntryHandle entry = GET_STRING_DICT_ENTRY(dict, key);

#if PYTHON_VERSION >= 0x360
    if (entry == NULL) {
        DICT_SET_ITEM((PyObject *)dict, (PyObject *)key, value);

        Py_DECREF(value);
        CHECK_OBJECT(value);

        return;
    }
#endif

    PyObject *old = GET_DICT_ENTRY_VALUE(entry);

    // Values are more likely (more often) set than not set, in that case
    // speculatively try the quickest access method.
    if (likely(old != NULL)) {
        SET_DICT_ENTRY_VALUE(entry, value);
    } else {
        DICT_SET_ITEM((PyObject *)dict, (PyObject *)key, value);
        Py_DECREF(value);

        CHECK_OBJECT(value);
    }
}

NUITKA_MAY_BE_UNUSED static void UPDATE_STRING_DICT1(PyDictObject *dict, Nuitka_StringObject *key, PyObject *value) {
    CHECK_OBJECT(value);

    Nuitka_DictEntryHandle entry = GET_STRING_DICT_ENTRY(dict, key);

#if PYTHON_VERSION >= 0x360
    if (entry == NULL) {
        DICT_SET_ITEM((PyObject *)dict, (PyObject *)key, value);

        Py_DECREF(value);
        CHECK_OBJECT(value);

        return;
    }
#endif

    PyObject *old = GET_DICT_ENTRY_VALUE(entry);

    // Values are more likely (more often) set than not set, in that case
    // speculatively try the quickest access method.
    if (likely(old != NULL)) {
        SET_DICT_ENTRY_VALUE(entry, value);

        Py_DECREF(old);
    } else {
        DICT_SET_ITEM((PyObject *)dict, (PyObject *)key, value);

        Py_DECREF(value);
        CHECK_OBJECT(value);
    }
}

#if PYTHON_VERSION < 0x300
// Python2 dictionary keys, return a list of keys
extern PyObject *DICT_KEYS(PyObject *dict);
// Python2 dictionary items, return a list of values
extern PyObject *DICT_VALUES(PyObject *dict);
// Python2 dictionary items, return a list of key/value tuples
extern PyObject *DICT_ITEMS(PyObject *dict);
#endif

// Python3 dictionary keys, Python2 iterkeys returns dictionary keys iterator
extern PyObject *DICT_ITERKEYS(PyObject *dict);

// Python3 dictionary values, Python2 itervalues returns dictionary values iterator
extern PyObject *DICT_ITERVALUES(PyObject *dict);

// Python3 dictionary items, Python2 iteritems returns dictionary items iterator
extern PyObject *DICT_ITERITEMS(PyObject *dict);

// Python dictionary keys view
extern PyObject *DICT_VIEWKEYS(PyObject *dict);

// Python dictionary values view
extern PyObject *DICT_VIEWVALUES(PyObject *dict);

// Python dictionary items view
extern PyObject *DICT_VIEWITEMS(PyObject *dict);

// Python dictionary copy, return a shallow copy of a dictionary.
extern PyObject *DICT_COPY(PyObject *dict);

// Python dictionary clear, empties the dictionary.
extern void DICT_CLEAR(PyObject *dict);

// Replacement for PyDict_Next that is faster (to call).
extern bool Nuitka_DictNext(PyObject *dict, Py_ssize_t *pos, PyObject **key_ptr, PyObject **value_ptr);

#if PYTHON_VERSION >= 0x3a0
#define NUITKA_DICT_HAS_FREELIST 1

// Replacement for PyDict_New that is faster
extern PyObject *MAKE_DICT_EMPTY(void);
#else
#define NUITKA_DICT_HAS_FREELIST 0
#define MAKE_DICT_EMPTY PyDict_New
#endif

// Create a dictionary from key/value pairs.
extern PyObject *MAKE_DICT(PyObject **pairs, Py_ssize_t size);
// Create a dictionary from key/value pairs (NULL value means skip)
extern PyObject *MAKE_DICT_X(PyObject **pairs, Py_ssize_t size);
// Create a dictionary from key/value pairs (NULL value means skip) where keys are C strings.
extern PyObject *MAKE_DICT_X_CSTR(char const **keys, PyObject **values, Py_ssize_t size);

#endif
