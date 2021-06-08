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
#ifndef __NUITKA_DICTIONARIES_H__
#define __NUITKA_DICTIONARIES_H__

static inline Py_ssize_t DICT_SIZE(PyObject *dict) {
    CHECK_OBJECT(dict);

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

typedef struct {
    /* Cached hash code of me_key. */
    Py_hash_t me_hash;
    PyObject *me_key;
    PyObject *me_value; /* This field is only meaningful for combined tables */
} PyDictKeyEntry;

#if PYTHON_VERSION < 0x360
typedef PyDictKeyEntry *(*dict_lookup_func)(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr);
#elif PYTHON_VERSION < 0x370
typedef Py_ssize_t (*dict_lookup_func)(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr,
                                       Py_ssize_t *hashpos);
#else
typedef Py_ssize_t (*dict_lookup_func)(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject **value_addr);
#endif

// Taken from CPython3.3 "Objects/dictobject.c", lives in "Objects/dict-common.h" later

struct _dictkeysobject {
    Py_ssize_t dk_refcnt;
    Py_ssize_t dk_size;
    dict_lookup_func dk_lookup;
    Py_ssize_t dk_usable;
#if PYTHON_VERSION < 0x360
    PyDictKeyEntry dk_entries[1];
#else
    Py_ssize_t dk_nentries;
    union {
        int8_t as_1[8];
        int16_t as_2[4];
        int32_t as_4[2];
#if SIZEOF_VOID_P > 4
        int64_t as_8[1];
#endif
    } dk_indices;

#endif
};

// Taken from Objects/dictobject.c of CPython 3.6
#if PYTHON_VERSION >= 0x360

#define DK_SIZE(dk) ((dk)->dk_size)

#if SIZEOF_VOID_P > 4
#define DK_IXSIZE(dk)                                                                                                  \
    (DK_SIZE(dk) <= 0xff ? 1 : DK_SIZE(dk) <= 0xffff ? 2 : DK_SIZE(dk) <= 0xffffffff ? 4 : sizeof(int64_t))
#else
#define DK_IXSIZE(dk) (DK_SIZE(dk) <= 0xff ? 1 : DK_SIZE(dk) <= 0xffff ? 2 : sizeof(int32_t))
#endif

#define DK_ENTRIES(dk) ((PyDictKeyEntry *)(&(dk)->dk_indices.as_1[DK_SIZE(dk) * DK_IXSIZE(dk)]))

#define DK_USABLE_FRACTION(n) (((n) << 1) / 3)

#endif

typedef PyObject **Nuitka_DictEntryHandle;

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
#else
    PyObject *value;

    Py_ssize_t ix = dict->ma_keys->dk_lookup(dict, (PyObject *)key, hash, &value);

    if (value == NULL) {
        return NULL;
    } else if (_PyDict_HasSplitTable(dict)) {
        return &dict->ma_values[ix];
    } else {
        return &DK_ENTRIES(dict->ma_keys)[ix].me_value;
    }

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
// Get dict lookup for a key, similar to PyDict_GetItem, 1=ref returned, 0=not
extern PyObject *DICT_GET_ITEM1(PyObject *dict, PyObject *key);
extern PyObject *DICT_GET_ITEM0(PyObject *dict, PyObject *key);

// Get dict lookup for a key, similar to PyDict_Contains
extern int DICT_HAS_ITEM(PyObject *dict, PyObject *key);

// Convert to dictionary, helper for built-in "dict" mainly.
NUITKA_MAY_BE_UNUSED static PyObject *TO_DICT(PyObject *seq_obj, PyObject *dict_obj) {
    PyObject *result = PyDict_New();

    if (seq_obj != NULL) {
        int res;

        if (PyObject_HasAttrString(seq_obj, "keys")) {
            res = PyDict_Merge(result, seq_obj, 1);
        } else {
            res = PyDict_MergeFromSeq2(result, seq_obj, 1);
        }

        if (res == -1) {
            return NULL;
        }
    }

    if (dict_obj != NULL) {
        int res = PyDict_Merge(result, dict_obj, 1);

        if (res == -1) {
            return NULL;
        }
    }

    return result;
}

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

#endif
