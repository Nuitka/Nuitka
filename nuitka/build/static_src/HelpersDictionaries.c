//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* These helpers are used to work with dictionaries.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

#include "nuitka/compiled_types_common.h"
#include "nuitka/freelists.h"
#endif

#include "nuitka/helper/dict_internals.h"

// spell-checker: ignore decref,dictiteritems_type,dictiterkeys_type,dictiterobject
// spell-checker: ignore dictitervalues_type,dictkeysview_type,dictvaluesview_type
// spell-checker: ignore dictviewobject,dkix,ixsize,ob_shash,qsbr

// Only needed for 3.13t right now, but I suspect we'll need to remove this
// guard later.
#ifdef Py_GIL_DISABLED

// From CPython
#define PyDict_LOG_MINSIZE 3

#if defined(WITH_FREELISTS) && PYTHON_VERSION >= 0x3d0
static struct _Py_dictkeys_freelist *get_dictkeys_freelist(void) {
    struct _Py_object_freelists *freelists = _Py_object_freelists_GET();
    return &freelists->dictkeys;
}
#endif

static void Nuitka_Py_dictkeys_free_keys_object(PyDictKeysObject *keys, bool use_qsbr) {
#ifdef Py_GIL_DISABLED
    if (use_qsbr) {
        NuitkaMem_FreeDelayed(keys);
        return;
    }
#endif

#if defined(WITH_FREELISTS) && PYTHON_VERSION >= 0x3d0
    struct _Py_dictkeys_freelist *freelist = get_dictkeys_freelist();
    if (DK_LOG_SIZE(keys) == PyDict_LOG_MINSIZE && freelist->numfree < PyDict_MAXFREELIST && freelist->numfree >= 0 &&
        DK_IS_UNICODE(keys)) {
        freelist->items[freelist->numfree++] = keys;
        return;
    }
#endif
    PyMem_Free(keys);
}

#endif

#ifdef Py_GIL_DISABLED

static inline void ASSERT_DICT_LOCKED(PyObject *op) { _Py_CRITICAL_SECTION_ASSERT_OBJECT_LOCKED(op); }
#define ASSERT_DICT_LOCKED(op) ASSERT_DICT_LOCKED(_Py_CAST(PyObject *, op))
#define ASSERT_WORLD_STOPPED_OR_DICT_LOCKED(op)                                                                        \
    if (!_PyInterpreterState_GET()->stoptheworld.world_stopped) {                                                      \
        ASSERT_DICT_LOCKED(op);                                                                                        \
    }
#define ASSERT_WORLD_STOPPED_OR_OBJ_LOCKED(op)                                                                         \
    if (!_PyInterpreterState_GET()->stoptheworld.world_stopped) {                                                      \
        _Py_CRITICAL_SECTION_ASSERT_OBJECT_LOCKED(op);                                                                 \
    }

#define IS_DICT_SHARED(mp) _PyObject_GC_IS_SHARED(mp)
#define SET_DICT_SHARED(mp) _PyObject_GC_SET_SHARED(mp)
#define LOAD_INDEX(keys, size, idx)                                                                                    \
    _Py_atomic_load_int##size##_relaxed(&((const int##size##_t *)keys->dk_indices)[idx]);
#define STORE_INDEX(keys, size, idx, value)                                                                            \
    _Py_atomic_store_int##size##_relaxed(&((int##size##_t *)keys->dk_indices)[idx], (int##size##_t)value);
#define ASSERT_OWNED_OR_SHARED(mp) assert(_Py_IsOwnedByCurrentThread((PyObject *)mp) || IS_DICT_SHARED(mp));

#define LOCK_KEYS_IF_SPLIT(keys, kind)                                                                                 \
    if (kind == DICT_KEYS_SPLIT) {                                                                                     \
        LOCK_KEYS(keys);                                                                                               \
    }

#define UNLOCK_KEYS_IF_SPLIT(keys, kind)                                                                               \
    if (kind == DICT_KEYS_SPLIT) {                                                                                     \
        UNLOCK_KEYS(keys);                                                                                             \
    }

#define ASSERT_KEYS_LOCKED(keys) assert(PyMutex_IsLocked(&keys->dk_mutex))
#define LOAD_SHARED_KEY(key) _Py_atomic_load_ptr_acquire(&key)
#define STORE_SHARED_KEY(key, value) _Py_atomic_store_ptr_release(&key, value)
// Inc refs the keys object, giving the previous value
#define INCREF_KEYS(dk) _Py_atomic_add_ssize(&dk->dk_refcnt, 1)
// Dec refs the keys object, giving the previous value
#define DECREF_KEYS(dk) _Py_atomic_add_ssize(&dk->dk_refcnt, -1)
#define LOAD_KEYS_NENTRIES(keys) _Py_atomic_load_ssize_relaxed(&keys->dk_nentries)

static inline void Nuitka_Py_dictkeys_incref(PyDictKeysObject *dk) {
    if (FT_ATOMIC_LOAD_SSIZE_RELAXED(dk->dk_refcnt) == _Py_IMMORTAL_REFCNT) {
        return;
    }
#ifdef Py_REF_DEBUG
    _Py_IncRefTotal(_PyThreadState_GET());
#endif
    INCREF_KEYS(dk);
}

static inline void Nuitka_Py_dictkeys_decref(PyInterpreterState *interp, PyDictKeysObject *dk, bool use_qsbr) {
    if (FT_ATOMIC_LOAD_SSIZE_RELAXED(dk->dk_refcnt) == _Py_IMMORTAL_REFCNT) {
        return;
    }
    assert(FT_ATOMIC_LOAD_SSIZE(dk->dk_refcnt) > 0);
#ifdef Py_REF_DEBUG
    _Py_DecRefTotal(_PyThreadState_GET());
#endif
    if (DECREF_KEYS(dk) == 1) {
        if (DK_IS_UNICODE(dk)) {
            PyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(dk);
            Py_ssize_t i, n;
            for (i = 0, n = dk->dk_nentries; i < n; i++) {
                Py_XDECREF(entries[i].me_key);
                Py_XDECREF(entries[i].me_value);
            }
        } else {
            PyDictKeyEntry *entries = DK_ENTRIES(dk);
            Py_ssize_t i, n;
            for (i = 0, n = dk->dk_nentries; i < n; i++) {
                Py_XDECREF(entries[i].me_key);
                Py_XDECREF(entries[i].me_value);
            }
        }
        Nuitka_Py_dictkeys_free_keys_object(dk, use_qsbr);
    }
}

#define INCREF_KEYS_FT(dk) Nuitka_Py_dictkeys_incref(dk)
#define DECREF_KEYS_FT(dk, shared) Nuitka_Py_dictkeys_decref(_PyInterpreterState_GET(), dk, shared)

static inline void split_keys_entry_added(PyDictKeysObject *keys) {
    ASSERT_KEYS_LOCKED(keys);

    // We increase before we decrease so we never get too small of a value
    // when we're racing with reads
    _Py_atomic_store_ssize_relaxed(&keys->dk_nentries, keys->dk_nentries + 1);
    _Py_atomic_store_ssize_release(&keys->dk_usable, keys->dk_usable - 1);
}

#else /* Py_GIL_DISABLED */

#define ASSERT_DICT_LOCKED(op)
#define ASSERT_WORLD_STOPPED_OR_DICT_LOCKED(op)
#define ASSERT_WORLD_STOPPED_OR_OBJ_LOCKED(op)
#define ASSERT_KEYS_LOCKED(keys)
#define LOAD_SHARED_KEY(key) key
#define STORE_SHARED_KEY(key, value) key = value
#define INCREF_KEYS(dk) dk->dk_refcnt++
#define DECREF_KEYS(dk) dk->dk_refcnt--
#define LOAD_KEYS_NENTRIES(keys) keys->dk_nentries
#define INCREF_KEYS_FT(dk)
#define DECREF_KEYS_FT(dk, shared)
#define LOCK_KEYS_IF_SPLIT(keys, kind)
#define UNLOCK_KEYS_IF_SPLIT(keys, kind)
#define IS_DICT_SHARED(mp) (false)
#define SET_DICT_SHARED(mp)
#define LOAD_INDEX(keys, size, idx) ((const int##size##_t *)(keys->dk_indices))[idx]
#define STORE_INDEX(keys, size, idx, value) ((int##size##_t *)(keys->dk_indices))[idx] = (int##size##_t)value
#endif

Py_ssize_t Nuitka_Py_dict_lookup_threadsafe(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject **value_addr);

#ifdef Py_GIL_DISABLED
static PyObject *Nuitka_Py_dict_lookup_threadsafe_borrowed(PyDictObject *mp, PyObject *key, Py_hash_t hash);
#endif

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

#if defined(Py_GIL_DISABLED)
    PyObject *borrowed_result = Nuitka_Py_dict_lookup_threadsafe_borrowed(dict_object, key, hash);

    if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
        CLEAR_ERROR_OCCURRED(tstate);
        return NULL;
    }

    return borrowed_result;
#endif

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
#elif defined(Py_GIL_DISABLED)
    PyObject *result;
    Py_ssize_t ix = Nuitka_Py_dict_lookup_threadsafe(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || (PYTHON_VERSION >= 0x3b0 && !defined(Py_GIL_DISABLED))
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
#elif defined(Py_GIL_DISABLED)
    PyObject *result;
    Py_ssize_t ix = Nuitka_Py_dict_lookup_threadsafe(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || (PYTHON_VERSION >= 0x3b0 && !defined(Py_GIL_DISABLED))
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif
    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(result);

#if defined(Py_GIL_DISABLED)
    return result;
#else
    Py_INCREF(result);
    return result;
#endif
#endif
}

#if PYTHON_VERSION >= 0x3c0
static PyObject *Nuitka_CreateKeyError(PyThreadState *tstate, PyObject *key) {
    return (PyObject *)Nuitka_BaseExceptionSingleArg_new(tstate, (PyTypeObject *)PyExc_KeyError, key);
}
#endif

void SET_CURRENT_EXCEPTION_KEY_ERROR(PyThreadState *tstate, PyObject *key) {
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
#elif defined(Py_GIL_DISABLED)
    PyObject *result;
    Py_ssize_t ix = Nuitka_Py_dict_lookup_threadsafe(dict_object, key, hash, &result);
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

#if PYTHON_VERSION < 0x370 || (PYTHON_VERSION >= 0x3b0 && !defined(Py_GIL_DISABLED))
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

#if defined(Py_GIL_DISABLED)
    return result;
#else
    Py_INCREF(result);
    return result;
#endif
#endif
}

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
#elif defined(Py_GIL_DISABLED)
    PyObject *result;
    Py_ssize_t ix = Nuitka_Py_dict_lookup_threadsafe(dict_object, key, hash, &result);
#else
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(dict_object, key, hash, &value_addr);
#endif

    if (unlikely(ix < 0)) {
        return NULL;
    }
#endif

#if PYTHON_VERSION < 0x370 || (PYTHON_VERSION >= 0x3b0 && !defined(Py_GIL_DISABLED))
    assert(value_addr != NULL);
    PyObject *result = *value_addr;
#endif

    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(result);

#if defined(Py_GIL_DISABLED)
    return result;
#else
    Py_INCREF(result);
    return result;
#endif
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
#elif defined(Py_GIL_DISABLED)
    PyObject *result;
    Py_ssize_t ix = Nuitka_Py_dict_lookup_threadsafe(dict_object, key, hash, &result);
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

#if defined(Py_GIL_DISABLED)
    if (result == NULL) {
        return 0;
    }

    Py_DECREF(result);
    return 1;
#endif

#if PYTHON_VERSION < 0x370 || (PYTHON_VERSION >= 0x3b0 && !defined(Py_GIL_DISABLED))
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

#if PYTHON_VERSION >= 0x3e0
static PyDictObject *_Nuitka_AllocatePyDictObjectFresh(void) {
    size_t pre_size = _PyType_PreHeaderSize(&PyDict_Type);
    size_t size = _PyObject_SIZE(&PyDict_Type);

    char *alloc = (char *)NuitkaObject_Malloc(size + pre_size);
    assert(alloc != NULL);

    ((PyObject **)alloc)[0] = NULL;
    ((PyObject **)alloc)[1] = NULL;

    PyObject *obj = (PyObject *)(alloc + pre_size);

    Nuitka_PyObject_GC_Link(obj);
    _PyObject_Init(obj, &PyDict_Type);

    return (PyDictObject *)obj;
}
#endif

#if PYTHON_VERSION >= 0x300 && (NUITKA_DICT_HAS_FREELIST || !_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT)
static PyDictObject *_Nuitka_AllocatePyDictObject(PyThreadState *tstate) {
    PyDictObject *result_mp;

#if NUITKA_DICT_HAS_FREELIST
#if PYTHON_VERSION < 0x3d0
    // This is the CPython name, spell-checker: ignore numfree
    PyDictObject **items = tstate->interp->dict_state.free_list;
    int *numfree = &tstate->interp->dict_state.numfree;
#elif PYTHON_VERSION < 0x3e0
    struct _Py_object_freelists *freelists = _Nuitka_object_freelists_GET(tstate);
    struct _Py_dict_freelist *state = &freelists->dicts;
    PyDictObject **items = state->items;
    int *numfree = &state->numfree;
#endif

#if PYTHON_VERSION >= 0x3e0
    struct _Py_freelists *freelists = Nuitka_Py_freelists_GET(tstate);

    result_mp = (PyDictObject *)Nuitka_PyFreeList_Pop(&freelists->dicts);

    if (result_mp != NULL) {
        Nuitka_Py_NewReference((PyObject *)result_mp);
    } else {
        result_mp = _Nuitka_AllocatePyDictObjectFresh();
    }
#else
    if (*numfree) {
        (*numfree) -= 1;
        result_mp = items[*numfree];

        Nuitka_Py_NewReference((PyObject *)result_mp);
    } else {
#if PYTHON_VERSION >= 0x3e0
        result_mp = _Nuitka_AllocatePyDictObjectFresh();
#else
        result_mp = (PyDictObject *)Nuitka_GC_New(&PyDict_Type);
#endif
    }
#endif
#else
#if PYTHON_VERSION >= 0x3e0
    result_mp = _Nuitka_AllocatePyDictObjectFresh();
#else
    result_mp = (PyDictObject *)Nuitka_GC_New(&PyDict_Type);
#endif
#endif
#if PYTHON_VERSION >= 0x3e0
    result_mp->_ma_watcher_tag = 0;
#endif

    CHECK_OBJECT(result_mp);
    assert(PyDict_CheckExact((PyObject *)result_mp));
    return result_mp;
}
#endif

#if PYTHON_VERSION >= 0x360
static PyDictKeysObject *_Nuitka_AllocatePyDictKeysObject(PyThreadState *tstate, Py_ssize_t keys_size) {
    // CPython names, spell-checker: ignore dictkeys,numfree
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

#if PYTHON_VERSION >= 0x360 && !_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT

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

static inline PyDictValues *_Nuitka_PyDict_new_values(Py_ssize_t size) {
#if PYTHON_VERSION < 0x3b0
    Py_ssize_t values_size = sizeof(PyObject *) * size;

    return (PyDictValues *)NuitkaMem_Malloc(values_size);
#elif PYTHON_VERSION < 0x3d0
    Py_ssize_t values_size = sizeof(PyObject *) * size;

    // With Python3.11-3.12 a prefix is allocated too.
    size_t prefix_size = _Py_SIZE_ROUND_UP(size + 2, sizeof(PyObject *));
    size_t n = prefix_size + values_size;
    uint8_t *mem = (uint8_t *)NuitkaMem_Malloc(n);
    assert(mem != NULL);

    assert(prefix_size % sizeof(PyObject *) == 0);
    mem[prefix_size - 1] = (uint8_t)prefix_size;

    return (PyDictValues *)(mem + prefix_size);
#else
    assert(size >= 1);
    size_t suffix_size = _Py_SIZE_ROUND_UP(size, sizeof(PyObject *));
    assert(suffix_size < 128);
    assert(suffix_size % sizeof(PyObject *) == 0);
    size_t n = (size + 1) * sizeof(PyObject *) + suffix_size;
    PyDictValues *result = (PyDictValues *)NuitkaMem_Malloc(n);

    result->embedded = 0;
    result->size = 0;
    assert(size < 256);
    result->capacity = (uint8_t)size;
    return result;
#endif
}

#if PYTHON_VERSION >= 0x3d0

static PyDictValues *_Nuitka_PyDict_copy_values(PyDictValues *values) {
    PyDictValues *new_values = _Nuitka_PyDict_new_values(values->capacity);
    if (unlikely(new_values == NULL)) {
        return NULL;
    }

    new_values->size = values->size;

    uint8_t *values_order = get_insertion_order_array(values);
    uint8_t *new_values_order = get_insertion_order_array(new_values);

    memcpy(new_values_order, values_order, values->capacity);

    for (int i = 0; i < values->capacity; i++) {
        new_values->values[i] = values->values[i];
    }
    assert(new_values->embedded == 0);
    return new_values;
}
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
#if PYTHON_VERSION < 0x3d0
    assert(i < (((char *)mp->ma_values)[-2]));
    return ((char *)mp->ma_values)[-3 - i];
#else
    assert(i < mp->ma_values->size);
    uint8_t *array = get_insertion_order_array(mp->ma_values);
    return array[i];
#endif
}
#endif

#if PYTHON_VERSION >= 0x3b0

static inline Py_ssize_t Nuitka_Py_dictkeys_get_index(const PyDictKeysObject *keys, Py_ssize_t i) {
    int log2size = DK_LOG_SIZE(keys);
    Py_ssize_t ix;

    if (log2size < 8) {
        ix = LOAD_INDEX(keys, 8, i);

    } else if (log2size < 16) {
        ix = LOAD_INDEX(keys, 16, i);
    }
#if SIZEOF_VOID_P > 4
    else if (log2size >= 32) {
        ix = LOAD_INDEX(keys, 64, i);
    }
#endif
    else {
        ix = LOAD_INDEX(keys, 32, i);
    }

    assert(ix >= DKIX_DUMMY);
    return ix;
}

// From CPython
#define PERTURB_SHIFT 5

// 3.13+
#if PYTHON_VERSION >= 0x3d0

static inline Py_ALWAYS_INLINE Py_ssize_t Nuitka_Py_dictkeys_do_lookup(
    PyDictObject *mp, PyDictKeysObject *dk, PyObject *key, Py_hash_t hash,
    int (*check_lookup)(PyDictObject *, PyDictKeysObject *, void *, Py_ssize_t ix, PyObject *key, Py_hash_t)) {
    void *ep0 = _DK_ENTRIES(dk);
    size_t mask = DK_MASK(dk);
    size_t perturb = hash;
    size_t i = (size_t)hash & mask;
    Py_ssize_t ix;
    for (;;) {
        ix = Nuitka_Py_dictkeys_get_index(dk, i);
        if (ix >= 0) {
            int cmp = check_lookup(mp, dk, ep0, ix, key, hash);
            if (cmp < 0) {
                return cmp;
            } else if (cmp) {
                return ix;
            }
        } else if (ix == DKIX_EMPTY) {
            return DKIX_EMPTY;
        }
        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);

        // Manual loop unrolling
        ix = Nuitka_Py_dictkeys_get_index(dk, i);
        if (ix >= 0) {
            int cmp = check_lookup(mp, dk, ep0, ix, key, hash);
            if (cmp < 0) {
                return cmp;
            } else if (cmp) {
                return ix;
            }
        } else if (ix == DKIX_EMPTY) {
            return DKIX_EMPTY;
        }
        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }
    NUITKA_CANNOT_GET_HERE("Nuitka_Py_dictkeys_do_lookup failed");
}

static inline int Nuitka_Py_dictkeys_compare_unicode_generic(PyDictObject *mp, PyDictKeysObject *dk, void *ep0,
                                                             Py_ssize_t ix, PyObject *key, Py_hash_t hash) {
    PyDictUnicodeEntry *ep = &((PyDictUnicodeEntry *)ep0)[ix];
    assert(ep->me_key != NULL);
    assert(PyUnicode_CheckExact(ep->me_key));
    assert(!PyUnicode_CheckExact(key));

    if (Nuitka_Py_unicode_get_hash(ep->me_key) == hash) {
        PyObject *startkey = ep->me_key;
        Py_INCREF(startkey);
        nuitka_bool cmp = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(startkey, key);
        Py_DECREF(startkey);
        if (cmp == NUITKA_BOOL_EXCEPTION) {
            return DKIX_ERROR;
        }
        if (dk == mp->ma_keys && ep->me_key == startkey) {
            return cmp;
        } else {
            /* The dict was mutated, restart */
            return DKIX_KEY_CHANGED;
        }
    }
    return 0;
}

static Py_ssize_t Nuitka_Py_unicodekeys_lookup_generic(PyDictObject *mp, PyDictKeysObject *dk, PyObject *key,
                                                       Py_hash_t hash) {
    return Nuitka_Py_dictkeys_do_lookup(mp, dk, key, hash, Nuitka_Py_dictkeys_compare_unicode_generic);
}

static inline int Nuitka_Py_dictkeys_compare_generic(PyDictObject *mp, PyDictKeysObject *dk, void *ep0, Py_ssize_t ix,
                                                     PyObject *key, Py_hash_t hash) {
    PyDictKeyEntry *ep = &((PyDictKeyEntry *)ep0)[ix];
    assert(ep->me_key != NULL);
    if (ep->me_key == key) {
        return 1;
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
            return cmp;
        } else {
            /* The dict was mutated, restart */
            return DKIX_KEY_CHANGED;
        }
    }
    return 0;
}

// Search non-Unicode key from Unicode table
static Py_ssize_t Nuitka_Py_dictkeys_generic_lookup(PyDictObject *mp, PyDictKeysObject *dk, PyObject *key,
                                                    Py_hash_t hash) {
    return Nuitka_Py_dictkeys_do_lookup(mp, dk, key, hash, Nuitka_Py_dictkeys_compare_generic);
}

static inline int Nuitka_Py_dictkeys_compare_unicode_unicode(PyDictObject *mp, PyDictKeysObject *dk, void *ep0,
                                                             Py_ssize_t ix, PyObject *key, Py_hash_t hash) {
    PyDictUnicodeEntry *ep = &((PyDictUnicodeEntry *)ep0)[ix];
    PyObject *ep_key = FT_ATOMIC_LOAD_PTR_RELAXED(ep->me_key);
    assert(ep_key != NULL);
    assert(PyUnicode_CheckExact(ep_key));
    if (ep_key == key ||
        (Nuitka_Py_unicode_get_hash(ep_key) == hash && RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(ep_key, key))) {
        return 1;
    }
    return 0;
}

Py_ssize_t _Py_HOT_FUNCTION Nuitka_Py_unicodekeys_lookup_unicode(PyDictKeysObject *dk, PyObject *key, Py_hash_t hash) {
    return Nuitka_Py_dictkeys_do_lookup(NULL, dk, key, hash, Nuitka_Py_dictkeys_compare_unicode_unicode);
}

#ifdef Py_GIL_DISABLED

static inline Py_ALWAYS_INLINE int
Nuitka_Py_dictkeys_compare_unicode_generic_threadsafe(PyDictObject *mp, PyDictKeysObject *dk, void *ep0, Py_ssize_t ix,
                                                      PyObject *key, Py_hash_t hash) {
    PyDictUnicodeEntry *ep = &((PyDictUnicodeEntry *)ep0)[ix];
    PyObject *startkey = _Py_atomic_load_ptr_relaxed(&ep->me_key);
    assert(startkey == NULL || PyUnicode_CheckExact(ep->me_key));
    assert(!PyUnicode_CheckExact(key));

    if (startkey != NULL) {
        if (!_Py_TryIncrefCompare(&ep->me_key, startkey)) {
            return DKIX_KEY_CHANGED;
        }

        if (Nuitka_Py_unicode_get_hash(startkey) == hash) {
            nuitka_bool cmp = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(startkey, key);
            Py_DECREF(startkey);
            if (cmp == NUITKA_BOOL_EXCEPTION) {
                return DKIX_ERROR;
            }
            if (dk == _Py_atomic_load_ptr_relaxed(&mp->ma_keys) &&
                startkey == _Py_atomic_load_ptr_relaxed(&ep->me_key)) {
                return cmp;
            } else {
                /* The dict was mutated, restart */
                return DKIX_KEY_CHANGED;
            }
        } else {
            Py_DECREF(startkey);
        }
    }
    return 0;
}

// Search non-Unicode key from Unicode table
static Py_ssize_t Nuitka_Py_unicodekeys_lookup_generic_threadsafe(PyDictObject *mp, PyDictKeysObject *dk, PyObject *key,
                                                                  Py_hash_t hash) {
    return Nuitka_Py_dictkeys_do_lookup(mp, dk, key, hash, Nuitka_Py_dictkeys_compare_unicode_generic_threadsafe);
}

static inline Py_ALWAYS_INLINE int
Nuitka_Py_dictkeys_compare_unicode_unicode_threadsafe(PyDictObject *mp, PyDictKeysObject *dk, void *ep0, Py_ssize_t ix,
                                                      PyObject *key, Py_hash_t hash) {
    PyDictUnicodeEntry *ep = &((PyDictUnicodeEntry *)ep0)[ix];
    PyObject *startkey = _Py_atomic_load_ptr_relaxed(&ep->me_key);
    assert(startkey == NULL || PyUnicode_CheckExact(startkey));
    if (startkey == key) {
        return 1;
    }
    if (startkey != NULL) {
        if (_Py_IsImmortal(startkey)) {
            return Nuitka_Py_unicode_get_hash(startkey) == hash && RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(startkey, key);
        } else {
            if (!_Py_TryIncrefCompare(&ep->me_key, startkey)) {
                return DKIX_KEY_CHANGED;
            }
            if (Nuitka_Py_unicode_get_hash(startkey) == hash && RICH_COMPARE_EQ_CBOOL_UNICODE_UNICODE(startkey, key)) {
                Py_DECREF(startkey);
                return 1;
            }
            Py_DECREF(startkey);
        }
    }
    return 0;
}

static Py_ssize_t _Py_HOT_FUNCTION Nuitka_Py_unicodekeys_lookup_unicode_threadsafe(PyDictKeysObject *dk, PyObject *key,
                                                                                   Py_hash_t hash) {
    return Nuitka_Py_dictkeys_do_lookup(NULL, dk, key, hash, Nuitka_Py_dictkeys_compare_unicode_unicode_threadsafe);
}

static inline Py_ALWAYS_INLINE int Nuitka_Py_dictkeys_compare_generic_threadsafe(PyDictObject *mp, PyDictKeysObject *dk,
                                                                                 void *ep0, Py_ssize_t ix,
                                                                                 PyObject *key, Py_hash_t hash) {
    PyDictKeyEntry *ep = &((PyDictKeyEntry *)ep0)[ix];
    PyObject *startkey = _Py_atomic_load_ptr_relaxed(&ep->me_key);
    if (startkey == key) {
        return 1;
    }
    Py_ssize_t ep_hash = _Py_atomic_load_ssize_relaxed(&ep->me_hash);
    if (ep_hash == hash) {
        if (startkey == NULL || !_Py_TryIncrefCompare(&ep->me_key, startkey)) {
            return DKIX_KEY_CHANGED;
        }
        nuitka_bool cmp = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(startkey, key);
        Py_DECREF(startkey);
        if (cmp == NUITKA_BOOL_EXCEPTION) {
            return DKIX_ERROR;
        }
        if (dk == _Py_atomic_load_ptr_relaxed(&mp->ma_keys) && startkey == _Py_atomic_load_ptr_relaxed(&ep->me_key)) {
            return cmp;
        } else {
            /* The dict was mutated, restart */
            return DKIX_KEY_CHANGED;
        }
    }
    return 0;
}

static Py_ssize_t Nuitka_Py_dictkeys_generic_lookup_threadsafe(PyDictObject *mp, PyDictKeysObject *dk, PyObject *key,
                                                               Py_hash_t hash) {
    return Nuitka_Py_dictkeys_do_lookup(mp, dk, key, hash, Nuitka_Py_dictkeys_compare_generic_threadsafe);
}

static inline void Nuitka_Py_dict_ensure_shared_on_read(PyDictObject *mp) {
    if (!_Py_IsOwnedByCurrentThread((PyObject *)mp) && !IS_DICT_SHARED(mp)) {
        // The first time we access a dict from a non-owning thread we mark it
        // as shared. This ensures that a concurrent resize operation will
        // delay freeing the old keys or values using QSBR, which is necessary
        // to safely allow concurrent reads without locking...
        Py_BEGIN_CRITICAL_SECTION(mp);
        if (!IS_DICT_SHARED(mp)) {
            SET_DICT_SHARED(mp);
        }
        Py_END_CRITICAL_SECTION();
    }
}

Py_ssize_t Nuitka_Py_dict_lookup_threadsafe(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject **value_addr) {
    PyDictKeysObject *dk;
    DictKeysKind kind;
    Py_ssize_t ix;
    PyObject *value;

    Nuitka_Py_dict_ensure_shared_on_read(mp);

    dk = _Py_atomic_load_ptr(&mp->ma_keys);
    kind = dk->dk_kind;

    if (kind != DICT_KEYS_GENERAL) {
        if (PyUnicode_CheckExact(key)) {
            ix = Nuitka_Py_unicodekeys_lookup_unicode_threadsafe(dk, key, hash);
        } else {
            ix = Nuitka_Py_unicodekeys_lookup_generic_threadsafe(mp, dk, key, hash);
        }
        if (ix == DKIX_KEY_CHANGED) {
            goto read_failed;
        }

        if (ix >= 0) {
            if (kind == DICT_KEYS_SPLIT) {
                PyDictValues *values = _Py_atomic_load_ptr(&mp->ma_values);
                if (values == NULL)
                    goto read_failed;

                uint8_t capacity = _Py_atomic_load_uint8_relaxed(&values->capacity);
                if (ix >= (Py_ssize_t)capacity)
                    goto read_failed;

                value = _Py_TryXGetRef(&values->values[ix]);
                if (value == NULL)
                    goto read_failed;

                if (values != _Py_atomic_load_ptr(&mp->ma_values)) {
                    Py_DECREF(value);
                    goto read_failed;
                }
            } else {
                value = _Py_TryXGetRef(&DK_UNICODE_ENTRIES(dk)[ix].me_value);
                if (value == NULL) {
                    goto read_failed;
                }

                if (dk != _Py_atomic_load_ptr(&mp->ma_keys)) {
                    Py_DECREF(value);
                    goto read_failed;
                }
            }
        } else {
            value = NULL;
        }
    } else {
        ix = Nuitka_Py_dictkeys_generic_lookup_threadsafe(mp, dk, key, hash);
        if (ix == DKIX_KEY_CHANGED) {
            goto read_failed;
        }
        if (ix >= 0) {
            value = _Py_TryXGetRef(&DK_ENTRIES(dk)[ix].me_value);
            if (value == NULL)
                goto read_failed;

            if (dk != _Py_atomic_load_ptr(&mp->ma_keys)) {
                Py_DECREF(value);
                goto read_failed;
            }
        } else {
            value = NULL;
        }
    }

    *value_addr = value;
    return ix;

read_failed:
    // In addition to the normal races of the dict being modified the _Py_TryXGetRef
    // can all fail if they don't yet have a shared ref count.  That can happen here
    // or in the *_lookup_* helper.  In that case we need to take the lock to avoid
    // mutation and do a normal incref which will make them shared.
    Py_BEGIN_CRITICAL_SECTION(mp);
    PyObject **locked_value_addr = NULL;
    ix = Nuitka_PyDictLookup(mp, key, hash, &locked_value_addr);
    value = locked_value_addr == NULL ? NULL : *locked_value_addr;
    *value_addr = value;
    if (value != NULL) {
        assert(ix >= 0);
        _Py_NewRefWithLock(value);
    }
    Py_END_CRITICAL_SECTION();
    return ix;
}

// Borrowed lookup with the same lifetime rules as CPython's PyDict_GetItem in
// free-threaded builds. Callers must provide external synchronization if the
// dictionary can be mutated concurrently.
static PyObject *Nuitka_Py_dict_lookup_threadsafe_borrowed(PyDictObject *mp, PyObject *key, Py_hash_t hash) {
    Nuitka_Py_dict_ensure_shared_on_read(mp);

    PyObject *result;

    Py_BEGIN_CRITICAL_SECTION(mp);
    PyObject **value_addr = NULL;
    Py_ssize_t ix = Nuitka_PyDictLookup(mp, key, hash, &value_addr);

    if (ix >= 0 && value_addr != NULL) {
        result = *value_addr;
    } else {
        result = NULL;
    }
    Py_END_CRITICAL_SECTION();

    return result;
}

#else // Py_GIL_DISABLED

Py_ssize_t Nuitka_Py_dict_lookup_threadsafe(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject **value_addr) {
    Py_ssize_t ix = Nuitka_PyDictLookup(mp, key, hash, &value_addr);
    Py_XNewRef(*value_addr);
    return ix;
}

#endif

Py_ssize_t Nuitka_PyDictLookup(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr) {
    PyDictKeysObject *dk;
    DictKeysKind kind;
    Py_ssize_t ix;

    _Py_CRITICAL_SECTION_ASSERT_OBJECT_LOCKED(mp);
restart:
    dk = mp->ma_keys;
    kind = (DictKeysKind)dk->dk_kind;

    if (kind != DICT_KEYS_GENERAL) {
        if (PyUnicode_CheckExact(key)) {
#ifdef Py_GIL_DISABLED
            if (kind == DICT_KEYS_SPLIT) {
                ix = Nuitka_Py_unicodekeys_lookup_unicode_threadsafe(dk, key, hash);

                if (ix == DKIX_KEY_CHANGED) {
                    LOCK_KEYS(dk);
                    ix = Nuitka_Py_unicodekeys_lookup_unicode(dk, key, hash);
                    UNLOCK_KEYS(dk);
                }
            } else
#endif
            {
                ix = Nuitka_Py_unicodekeys_lookup_unicode(dk, key, hash);
            }
        } else {
            INCREF_KEYS_FT(dk);
            LOCK_KEYS_IF_SPLIT(dk, kind);

            ix = Nuitka_Py_unicodekeys_lookup_generic(mp, dk, key, hash);

            UNLOCK_KEYS_IF_SPLIT(dk, kind);
            DECREF_KEYS_FT(dk, IS_DICT_SHARED(mp));

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

#else
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
}

Py_ssize_t Nuitka_PyDictLookup(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject ***value_addr) {
    PyDictKeysObject *dk;
    DictKeysKind kind;
    Py_ssize_t ix;

    _Py_CRITICAL_SECTION_ASSERT_OBJECT_LOCKED(mp);
restart:
    dk = mp->ma_keys;
    kind = (DictKeysKind)dk->dk_kind;

    if (kind != DICT_KEYS_GENERAL) {
        if (PyUnicode_CheckExact(key)) {
#ifdef Py_GIL_DISABLED
            if (kind == DICT_KEYS_SPLIT) {
                ix = Nuitka_Py_unicodekeys_lookup_unicode_threadsafe(dk, key, hash);

                if (ix == DKIX_KEY_CHANGED) {
                    LOCK_KEYS(dk);
                    ix = Nuitka_Py_unicodekeys_lookup_unicode(dk, key, hash);
                    UNLOCK_KEYS(dk);
                }
            } else
#endif
            {
                ix = Nuitka_Py_unicodekeys_lookup_unicode(dk, key, hash);
            }
        } else {
            INCREF_KEYS_FT(dk);
            LOCK_KEYS_IF_SPLIT(dk, kind);

            ix = Nuitka_Py_unicodekeys_lookup_generic(mp, dk, key, hash);

            UNLOCK_KEYS_IF_SPLIT(dk, kind);
            DECREF_KEYS_FT(dk, IS_DICT_SHARED(mp));

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
#endif

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

// Canonical dictionary access implementation. All direct CPython dictionary
// access APIs in Nuitka-owned code go through this code. The implementation
// works directly on the standard "PyDictObject" state, so dictionaries can be
// freely passed between it and CPython APIs.

static bool Nuitka_DictGetHash(PyThreadState *tstate, PyObject *key, Py_hash_t *hash_ptr) {
    CHECK_OBJECT(key);

    Py_hash_t hash;

#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(key)) {
        hash = ((PyStringObject *)key)->ob_shash;

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITH_ERROR(tstate, key);
        }
    } else {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);
    }
#else
    if (PyUnicode_CheckExact(key)) {
        hash = Nuitka_Py_unicode_get_hash(key);

        if (unlikely(hash == -1)) {
            hash = HASH_VALUE_WITH_ERROR(tstate, key);
        }
    } else {
        hash = HASH_VALUE_WITH_ERROR(tstate, key);
    }
#endif

    if (unlikely(hash == -1)) {
        return false;
    }

    *hash_ptr = hash;

    return true;
}

#if _NUITKA_MAINTAIN_DICT_VERSION_TAG
#define NUITKA_DICT_NEXT_VERSION(dict_mp) ((dict_mp)->ma_version_tag = nuitka_dict_version_tag_counter++)
#else
#define NUITKA_DICT_NEXT_VERSION(dict_mp)
#endif

#define NUITKA_DICT_MAINTAIN_TRACKING(dict_mp, key, value)                                                             \
    do {                                                                                                               \
        if (!_PyObject_GC_IS_TRACKED(dict_mp) &&                                                                       \
            (_PyObject_GC_MAY_BE_TRACKED(key) || _PyObject_GC_MAY_BE_TRACKED(value))) {                                \
            Nuitka_GC_Track(dict_mp);                                                                                  \
        }                                                                                                              \
    } while (0)

#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x3b0
// Get the "lookdict" function pointer that CPython uses for a dictionary with
// non-string keys. There is no exported way to get it, so a tiny template
// dictionary is used once. This gives compatibility with CPython internals
// that compare "dk_lookup" against their own "lookdict".
static void *Nuitka_GetGenericDictLookup(void) {
    static void *generic_lookup = NULL;

    if (generic_lookup == NULL) {
        PyObject *template_dict = PyDict_New();
        assert(template_dict != NULL);

        PyObject *key = PyLong_FromLong(0);
        assert(key != NULL);

        NUITKA_MAY_BE_UNUSED int res = PyObject_SetItem(template_dict, key, Py_None);
        assert(res == 0);

        generic_lookup = (void *)((PyDictObject *)template_dict)->ma_keys->dk_lookup;

        Py_DECREF(key);
        Py_DECREF(template_dict);

        assert(generic_lookup != NULL);
    }

    return generic_lookup;
}
#endif

#if PYTHON_VERSION < 0x360
static PyObject *Nuitka_GetDictDummy(void) {
    static PyObject *dict_dummy = NULL;

    if (dict_dummy == NULL) {
        PyObject *template_dict = PyDict_New();
        assert(template_dict != NULL);

        PyObject *key = PyLong_FromLong(0);
        assert(key != NULL);

        NUITKA_MAY_BE_UNUSED int res = PyObject_SetItem(template_dict, key, Py_None);
        assert(res == 0);

        res = PyObject_DelItem(template_dict, key);
        assert(res == 0);

        PyDictObject *template_dict_mp = (PyDictObject *)template_dict;

#if PYTHON_VERSION < 0x300
        for (Py_ssize_t i = 0; i <= template_dict_mp->ma_mask; i++) {
            PyDictEntry *entry = &template_dict_mp->ma_table[i];

            if (entry->me_key != NULL && entry->me_value == NULL) {
                dict_dummy = entry->me_key;
                break;
            }
        }
#else
        PyDictKeyEntry *entries = DK_ENTRIES(template_dict_mp->ma_keys);
        Py_ssize_t size = DK_SIZE(template_dict_mp->ma_keys);

        for (Py_ssize_t i = 0; i < size; i++) {
            if (entries[i].me_key != NULL && entries[i].me_value == NULL) {
                dict_dummy = entries[i].me_key;
                break;
            }
        }
#endif

        Py_DECREF(key);
        Py_DECREF(template_dict);

        assert(dict_dummy != NULL);
    }

    return dict_dummy;
}
#endif

#if PYTHON_VERSION >= 0x3b0 && !defined(Py_GIL_DISABLED)

#define NUITKA_DICT_MINSIZE 8
#define NUITKA_DICT_LOG_MINSIZE 3

static PyDictKeysObject *Nuitka_DictGetEmptyKeys(void) {
    if (const_dict_empty == NULL) {
        return NULL;
    }

    return ((PyDictObject *)const_dict_empty)->ma_keys;
}

static bool Nuitka_DictKeysIsEmpty(PyDictKeysObject *keys) {
#if PYTHON_VERSION < 0x360
    return keys->dk_size == 1;
#else
    return keys->dk_usable == 0 && keys->dk_nentries == 0;
#endif
}

static uint8_t Nuitka_DictCalculateLog2Keysize(Py_ssize_t minsize) {
    uint8_t log2_size;

    for (log2_size = NUITKA_DICT_LOG_MINSIZE; (((Py_ssize_t)1) << log2_size) < minsize; log2_size++) {
    }

    return log2_size;
}

static void Nuitka_DictKeysSetIndex(PyDictKeysObject *keys, Py_ssize_t i, Py_ssize_t ix) {
    int log2size = DK_LOG_SIZE(keys);

    if (log2size < 8) {
        STORE_INDEX(keys, 8, i, ix);
    } else if (log2size < 16) {
        STORE_INDEX(keys, 16, i, ix);
    }
#if SIZEOF_VOID_P > 4
    else if (log2size >= 32) {
        STORE_INDEX(keys, 64, i, ix);
    }
#endif
    else {
        STORE_INDEX(keys, 32, i, ix);
    }
}

static PyDictKeysObject *Nuitka_DictNewKeysObject(PyThreadState *tstate, uint8_t log2_size, bool unicode) {
    Py_ssize_t usable = DK_USABLE_FRACTION(((Py_ssize_t)1) << log2_size);
    size_t entry_size = unicode ? sizeof(PyDictUnicodeEntry) : sizeof(PyDictKeyEntry);
    int log2_bytes;

    if (log2_size < 8) {
        log2_bytes = log2_size;
    } else if (log2_size < 16) {
        log2_bytes = log2_size + 1;
    }
#if SIZEOF_VOID_P > 4
    else if (log2_size >= 32) {
        log2_bytes = log2_size + 3;
    }
#endif
    else {
        log2_bytes = log2_size + 2;
    }

    size_t keys_size = sizeof(PyDictKeysObject) + (((size_t)1) << log2_bytes) + entry_size * (size_t)usable;

    PyDictKeysObject *keys = _Nuitka_AllocatePyDictKeysObject(tstate, keys_size);

    if (unlikely(keys == NULL)) {
        PyErr_NoMemory();
        return NULL;
    }

    // Account for the newly allocated keys object, like CPython's new_keys_object().
    Nuitka_Py_IncRefTotal(tstate);

    keys->dk_refcnt = 1;
    keys->dk_log2_size = log2_size;
    keys->dk_log2_index_bytes = (uint8_t)log2_bytes;
    keys->dk_kind = unicode ? DICT_KEYS_UNICODE : DICT_KEYS_GENERAL;
    keys->dk_version = 0;
    keys->dk_usable = usable;
    keys->dk_nentries = 0;

    memset(&keys->dk_indices[0], 0xff, ((size_t)1) << log2_bytes);
    memset(&keys->dk_indices[((size_t)1) << log2_bytes], 0, entry_size * (size_t)usable);

    return keys;
}

static void Nuitka_DictKeysFreeStruct(PyDictKeysObject *keys) {
#if PYTHON_VERSION >= 0x3d0
    PyMem_Free(keys);
#else
    PyObject_Free(keys);
#endif
}

static void Nuitka_DictKeysDecref(PyThreadState *tstate, PyDictKeysObject *keys) {
#if PYTHON_VERSION >= 0x3e0
    // Python 3.14 uses an immortal reference count for the shared empty keys
    // object, which is negative, so "CHECK_OBJECT_X" is not suitable here.
    assert(keys == NULL || keys->dk_refcnt != 0);
#else
    CHECK_OBJECT_X(keys);
#endif

    if (keys == NULL) {
        return;
    }

#if PYTHON_VERSION >= 0x3e0
    // Immortal keys objects, e.g. the empty keys object, are not freed, like
    // CPython's "dictkeys_decref" does it.
    if (keys->dk_refcnt < 0) {
        return;
    }
#endif

#if PYTHON_VERSION < 0x3c0
    // The empty keys object is shared and not immortal before Python 3.12.
    if (keys == Nuitka_DictGetEmptyKeys()) {
        Nuitka_Py_DecRefTotal(tstate);
        keys->dk_refcnt--;
        return;
    }
#endif

    if (Nuitka_DictKeysIsEmpty(keys)) {
        return;
    }

    // Account for the released keys object, like CPython's dictkeys_decref().
    Nuitka_Py_DecRefTotal(tstate);

    assert(keys->dk_refcnt > 0);

    if (--keys->dk_refcnt != 0) {
        return;
    }

    if (DK_IS_UNICODE(keys)) {
        PyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(keys);
        Py_ssize_t i, n;

        for (i = 0, n = keys->dk_nentries; i < n; i++) {
            Py_XDECREF(entries[i].me_key);
            Py_XDECREF(entries[i].me_value);
        }
    } else {
        PyDictKeyEntry *entries = DK_ENTRIES(keys);
        Py_ssize_t i, n;

        for (i = 0, n = keys->dk_nentries; i < n; i++) {
            Py_XDECREF(entries[i].me_key);
            Py_XDECREF(entries[i].me_value);
        }
    }

    Nuitka_DictKeysFreeStruct(keys);
}

#if PYTHON_VERSION < 0x3d0
static void Nuitka_DictValuesFree(PyDictKeysObject *keys, PyDictValues *values) {
    if (values == NULL || Nuitka_DictKeysIsEmpty(keys)) {
        return;
    }

    size_t prefix_size = ((uint8_t *)values)[-1];

    PyMem_Free((char *)values - prefix_size);
}
#else
static void Nuitka_DictValuesFree(PyDictKeysObject *keys, PyDictValues *values) {
    if (values == NULL || Nuitka_DictKeysIsEmpty(keys)) {
        return;
    }

    if (values->embedded) {
        values->valid = 0;

        for (int i = 0; i < values->capacity; i++) {
            values->values[i] = NULL;
        }

        return;
    }

    PyMem_Free(values);
}
#endif

#if PYTHON_VERSION < 0x3d0
static void Nuitka_DictValuesAddToInsertionOrder(PyDictValues *values, Py_ssize_t ix) {
    assert(ix < SHARED_KEYS_MAX_SIZE);

    uint8_t *size_ptr = ((uint8_t *)values) - 2;
    int size = *size_ptr;
    size++;

    size_ptr[-size] = (uint8_t)ix;
    *size_ptr = (uint8_t)size;
}

static void Nuitka_DictValuesDeleteFromInsertionOrder(PyDictValues *values, Py_ssize_t ix) {
    uint8_t *size_ptr = ((uint8_t *)values) - 2;
    int size = *size_ptr;
    int i;

    for (i = 1; size_ptr[-i] != ix; i++) {
        assert(i <= size);
    }

    assert(i <= size);

    for (; i < size; i++) {
        size_ptr[-i] = size_ptr[-i - 1];
    }

    *size_ptr = (uint8_t)(size - 1);
}
#else
static void Nuitka_DictValuesAddToInsertionOrder(PyDictValues *values, Py_ssize_t ix) {
    assert(ix < SHARED_KEYS_MAX_SIZE);

    uint8_t *array = get_insertion_order_array(values);
    array[values->size++] = (uint8_t)ix;
}

static void Nuitka_DictValuesDeleteFromInsertionOrder(PyDictValues *values, Py_ssize_t ix) {
    uint8_t *array = get_insertion_order_array(values);
    Py_ssize_t i;

    for (i = 0; i < values->size; i++) {
        if (array[i] == ix) {
            break;
        }
    }

    assert(i < values->size);

    for (; i < values->size - 1; i++) {
        array[i] = array[i + 1];
    }

    values->size--;
}
#endif

static Py_ssize_t Nuitka_DictFindEmptySlot(PyDictKeysObject *keys, Py_hash_t hash) {
    size_t mask = DK_MASK(keys);
    size_t i = (size_t)hash & mask;
    Py_ssize_t ix = Nuitka_Py_dictkeys_get_index(keys, i);

    for (size_t perturb = hash; ix >= 0;) {
        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
        ix = Nuitka_Py_dictkeys_get_index(keys, i);
    }

    return i;
}

static Py_ssize_t Nuitka_DictFindIndex(PyDictKeysObject *keys, Py_hash_t hash, Py_ssize_t wanted_ix) {
    size_t mask = DK_MASK(keys);
    size_t i = (size_t)hash & mask;

    for (size_t perturb = hash;;) {
        Py_ssize_t ix = Nuitka_Py_dictkeys_get_index(keys, i);

        if (ix == wanted_ix) {
            return i;
        }

        if (ix == DKIX_EMPTY) {
            break;
        }

        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }

    NUITKA_CANNOT_GET_HERE("Nuitka_DictFindIndex failed");
}

static void Nuitka_DictBuildIndicesUnicode(PyDictKeysObject *keys, PyDictUnicodeEntry *entries, Py_ssize_t n) {
    size_t mask = DK_MASK(keys);

    for (Py_ssize_t ix = 0; ix != n; ix++, entries++) {
        Py_hash_t hash = Nuitka_Py_unicode_get_hash(entries->me_key);
        assert(hash != -1);

        size_t i = (size_t)hash & mask;

        for (size_t perturb = hash; Nuitka_Py_dictkeys_get_index(keys, i) != DKIX_EMPTY;) {
            perturb >>= PERTURB_SHIFT;
            i = mask & (i * 5 + perturb + 1);
        }

        Nuitka_DictKeysSetIndex(keys, i, ix);
    }
}

static void Nuitka_DictBuildIndicesGeneral(PyDictKeysObject *keys, PyDictKeyEntry *entries, Py_ssize_t n) {
    size_t mask = DK_MASK(keys);

    for (Py_ssize_t ix = 0; ix != n; ix++, entries++) {
        Py_hash_t hash = entries->me_hash;
        size_t i = (size_t)hash & mask;

        for (size_t perturb = hash; Nuitka_Py_dictkeys_get_index(keys, i) != DKIX_EMPTY;) {
            perturb >>= PERTURB_SHIFT;
            i = mask & (i * 5 + perturb + 1);
        }

        Nuitka_DictKeysSetIndex(keys, i, ix);
    }
}

static int Nuitka_DictResize(PyThreadState *tstate, PyDictObject *mp, uint8_t log2_new_size, bool unicode) {
    assert(log2_new_size >= NUITKA_DICT_LOG_MINSIZE);

    PyDictKeysObject *oldkeys = mp->ma_keys;
    PyDictValues *oldvalues = mp->ma_values;

    if (!DK_IS_UNICODE(oldkeys)) {
        unicode = false;
    }

    PyDictKeysObject *new_keys = Nuitka_DictNewKeysObject(tstate, log2_new_size, unicode);

    if (unlikely(new_keys == NULL)) {
        return -1;
    }

    Py_ssize_t numentries = mp->ma_used;

    if (oldvalues != NULL) {
        PyDictUnicodeEntry *oldentries = DK_UNICODE_ENTRIES(oldkeys);

        if (new_keys->dk_kind == DICT_KEYS_GENERAL) {
            PyDictKeyEntry *newentries = DK_ENTRIES(new_keys);

            for (Py_ssize_t i = 0; i < numentries; i++) {
                int index = Nuitka_py_get_index_from_order(mp, i);
                PyDictUnicodeEntry *old_entry = &oldentries[index];

                assert(oldvalues->values[index] != NULL);

                newentries[i].me_key = Py_NewRef(old_entry->me_key);
                newentries[i].me_hash = Nuitka_Py_unicode_get_hash(old_entry->me_key);
                newentries[i].me_value = oldvalues->values[index];
            }

            Nuitka_DictBuildIndicesGeneral(new_keys, DK_ENTRIES(new_keys), numentries);
        } else {
            PyDictUnicodeEntry *newentries = DK_UNICODE_ENTRIES(new_keys);

            for (Py_ssize_t i = 0; i < numentries; i++) {
                int index = Nuitka_py_get_index_from_order(mp, i);
                PyDictUnicodeEntry *old_entry = &oldentries[index];

                assert(oldvalues->values[index] != NULL);

                newentries[i].me_key = Py_NewRef(old_entry->me_key);
                newentries[i].me_value = oldvalues->values[index];
            }

            Nuitka_DictBuildIndicesUnicode(new_keys, DK_UNICODE_ENTRIES(new_keys), numentries);
        }

        Nuitka_DictValuesFree(oldkeys, oldvalues);
        Nuitka_DictKeysDecref(tstate, oldkeys);
    } else {
        if (oldkeys->dk_kind == DICT_KEYS_GENERAL) {
            PyDictKeyEntry *oldentries = DK_ENTRIES(oldkeys);
            PyDictKeyEntry *newentries = DK_ENTRIES(new_keys);

            if (oldkeys->dk_nentries == numentries) {
                memcpy(newentries, oldentries, (size_t)numentries * sizeof(PyDictKeyEntry));
            } else {
                PyDictKeyEntry *entry = oldentries;

                for (Py_ssize_t i = 0; i < numentries; i++) {
                    while (entry->me_value == NULL) {
                        entry++;
                    }

                    newentries[i] = *entry++;
                }
            }

            Nuitka_DictBuildIndicesGeneral(new_keys, DK_ENTRIES(new_keys), numentries);
        } else {
            PyDictUnicodeEntry *oldentries = DK_UNICODE_ENTRIES(oldkeys);

            if (unicode) {
                PyDictUnicodeEntry *newentries = DK_UNICODE_ENTRIES(new_keys);

                if (oldkeys->dk_nentries == numentries) {
                    memcpy(newentries, oldentries, (size_t)numentries * sizeof(PyDictUnicodeEntry));
                } else {
                    PyDictUnicodeEntry *entry = oldentries;

                    for (Py_ssize_t i = 0; i < numentries; i++) {
                        while (entry->me_value == NULL) {
                            entry++;
                        }

                        newentries[i] = *entry++;
                    }
                }

                Nuitka_DictBuildIndicesUnicode(new_keys, DK_UNICODE_ENTRIES(new_keys), numentries);
            } else {
                PyDictKeyEntry *newentries = DK_ENTRIES(new_keys);
                PyDictUnicodeEntry *entry = oldentries;

                for (Py_ssize_t i = 0; i < numentries; i++) {
                    while (entry->me_value == NULL) {
                        entry++;
                    }

                    newentries[i].me_key = entry->me_key;
                    newentries[i].me_hash = Nuitka_Py_unicode_get_hash(entry->me_key);
                    newentries[i].me_value = entry->me_value;
                    entry++;
                }

                Nuitka_DictBuildIndicesGeneral(new_keys, DK_ENTRIES(new_keys), numentries);
            }
        }

        if (oldkeys == Nuitka_DictGetEmptyKeys()) {
#if PYTHON_VERSION < 0x3c0
            // Older Python versions release the reference to the empty keys object here.
            Nuitka_Py_DecRefTotal(tstate);
            oldkeys->dk_refcnt--;
#endif
        } else if (Nuitka_DictKeysIsEmpty(oldkeys) == false) {
            assert(oldkeys->dk_refcnt == 1);

            Nuitka_Py_DecRefTotal(tstate);

            Nuitka_DictKeysFreeStruct(oldkeys);
        }
    }

    mp->ma_keys = new_keys;
    mp->ma_values = NULL;

    new_keys->dk_usable -= numentries;
    new_keys->dk_nentries = numentries;

    return 0;
}

static int Nuitka_DictInsertionResize(PyThreadState *tstate, PyDictObject *mp, bool unicode) {
    return Nuitka_DictResize(tstate, mp, Nuitka_DictCalculateLog2Keysize(mp->ma_used * 3), unicode);
}

#if PYTHON_VERSION < 0x3d0
static int Nuitka_DictSetItemCompact(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash,
                                     PyObject *value) {
    PyObject *old_value = NULL;

    if (DK_IS_UNICODE(mp->ma_keys) && !PyUnicode_CheckExact(key)) {
        if (Nuitka_DictInsertionResize(tstate, mp, false) < 0) {
            return -1;
        }

        assert(mp->ma_keys->dk_kind == DICT_KEYS_GENERAL);
    }

    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(mp, key, hash, &value_addr);

    if (unlikely(ix == DKIX_ERROR)) {
        return -1;
    }

    if (ix >= 0) {
        old_value = *value_addr;
    }

    NUITKA_DICT_MAINTAIN_TRACKING(mp, key, value);

    if (ix == DKIX_EMPTY) {
        assert(old_value == NULL);

        if (mp->ma_keys->dk_usable <= 0) {
            if (Nuitka_DictInsertionResize(tstate, mp, true) < 0) {
                return -1;
            }
        }

        mp->ma_keys->dk_version = 0;

        Py_ssize_t hashpos = Nuitka_DictFindEmptySlot(mp->ma_keys, hash);

        Nuitka_DictKeysSetIndex(mp->ma_keys, hashpos, mp->ma_keys->dk_nentries);

        Py_INCREF(key);
        Py_INCREF(value);

        if (DK_IS_UNICODE(mp->ma_keys)) {
            PyDictUnicodeEntry *entry = &DK_UNICODE_ENTRIES(mp->ma_keys)[mp->ma_keys->dk_nentries];

            entry->me_key = key;

            if (mp->ma_values == NULL) {
                entry->me_value = value;
            }
        } else {
            PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[mp->ma_keys->dk_nentries];

            entry->me_key = key;
            entry->me_hash = hash;

            if (mp->ma_values == NULL) {
                entry->me_value = value;
            }
        }

        if (mp->ma_values != NULL) {
            mp->ma_values->values[mp->ma_keys->dk_nentries] = value;
        }

        mp->ma_used++;

        if (mp->ma_values != NULL) {
            Nuitka_DictValuesAddToInsertionOrder(mp->ma_values, mp->ma_keys->dk_nentries);
        }

        NUITKA_DICT_NEXT_VERSION(mp);
        mp->ma_keys->dk_usable--;
        mp->ma_keys->dk_nentries++;

        return 0;
    }

    if (old_value != value) {
        Py_INCREF(value);

        if (mp->ma_values != NULL) {
            mp->ma_values->values[ix] = value;

            if (old_value == NULL) {
                Nuitka_DictValuesAddToInsertionOrder(mp->ma_values, ix);
                mp->ma_used++;
            }
        } else {
            assert(old_value != NULL);

            if (DK_IS_UNICODE(mp->ma_keys)) {
                DK_UNICODE_ENTRIES(mp->ma_keys)[ix].me_value = value;
            } else {
                DK_ENTRIES(mp->ma_keys)[ix].me_value = value;
            }
        }

        NUITKA_DICT_NEXT_VERSION(mp);
        Py_XDECREF(old_value);
    }

    return 0;
}
#endif

#if PYTHON_VERSION >= 0x3d0
static Py_ssize_t Nuitka_DictInsertSplitKey(PyDictKeysObject *keys, PyObject *key, Py_hash_t hash) {
    Py_ssize_t ix = Nuitka_Py_unicodekeys_lookup_unicode(keys, key, hash);

    if (ix == DKIX_EMPTY && keys->dk_usable > 0) {
        keys->dk_version = 0;

        Py_ssize_t hashpos = Nuitka_DictFindEmptySlot(keys, hash);
        ix = keys->dk_nentries;
        Nuitka_DictKeysSetIndex(keys, hashpos, ix);

        PyDictUnicodeEntry *entry = &DK_UNICODE_ENTRIES(keys)[ix];
        entry->me_key = Py_NewRef(key);

        keys->dk_usable--;
        keys->dk_nentries++;
    }

    assert(ix < SHARED_KEYS_MAX_SIZE);

    return ix;
}

static void Nuitka_DictInsertSplitValue(PyDictObject *mp, PyObject *value, Py_ssize_t ix) {
    PyObject *old_value = mp->ma_values->values[ix];

    if (old_value == NULL) {
        mp->ma_values->values[ix] = Py_NewRef(value);
        Nuitka_DictValuesAddToInsertionOrder(mp->ma_values, ix);
        mp->ma_used++;
    } else if (old_value != value) {
        mp->ma_values->values[ix] = Py_NewRef(value);
        Py_DECREF(old_value);
    }
}

static int Nuitka_DictSetItem3x(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash,
                                PyObject *value) {
    PyObject *old_value = NULL;
    Py_ssize_t ix;

    NUITKA_DICT_MAINTAIN_TRACKING(mp, key, value);

    if (mp->ma_values != NULL && PyUnicode_CheckExact(key)) {
        ix = Nuitka_DictInsertSplitKey(mp->ma_keys, key, hash);

        if (ix != DKIX_EMPTY) {
            Nuitka_DictInsertSplitValue(mp, value, ix);
            return 0;
        }
    } else {
        PyObject **value_addr;
        ix = Nuitka_PyDictLookup(mp, key, hash, &value_addr);

        if (unlikely(ix == DKIX_ERROR)) {
            return -1;
        }

        if (ix >= 0) {
            old_value = *value_addr;
        }
    }

    if (old_value == NULL) {
        if (DK_IS_UNICODE(mp->ma_keys) && !PyUnicode_CheckExact(key)) {
            if (Nuitka_DictInsertionResize(tstate, mp, false) < 0) {
                return -1;
            }

            assert(mp->ma_keys->dk_kind == DICT_KEYS_GENERAL);
        } else if (mp->ma_values != NULL) {
            if (Nuitka_DictInsertionResize(tstate, mp, true) < 0) {
                return -1;
            }
        }

        if (mp->ma_keys->dk_usable <= 0) {
            if (Nuitka_DictInsertionResize(tstate, mp, true) < 0) {
                return -1;
            }
        }

        mp->ma_keys->dk_version = 0;

        Py_ssize_t new_ix = mp->ma_keys->dk_nentries;
        Py_ssize_t hashpos = Nuitka_DictFindEmptySlot(mp->ma_keys, hash);
        Nuitka_DictKeysSetIndex(mp->ma_keys, hashpos, new_ix);

        Py_INCREF(key);
        Py_INCREF(value);

        if (DK_IS_UNICODE(mp->ma_keys)) {
            PyDictUnicodeEntry *entry = &DK_UNICODE_ENTRIES(mp->ma_keys)[new_ix];

            entry->me_key = key;

            if (mp->ma_values != NULL) {
                mp->ma_values->values[new_ix] = value;
                Nuitka_DictValuesAddToInsertionOrder(mp->ma_values, new_ix);
            } else {
                entry->me_value = value;
            }
        } else {
            PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[new_ix];

            entry->me_key = key;
            entry->me_hash = hash;
            entry->me_value = value;
        }

        mp->ma_used++;
        NUITKA_DICT_NEXT_VERSION(mp);
        mp->ma_keys->dk_usable--;
        mp->ma_keys->dk_nentries++;

        return 0;
    }

    if (old_value != value) {
        Py_INCREF(value);

        if (mp->ma_values != NULL) {
            mp->ma_values->values[ix] = value;
        } else if (DK_IS_UNICODE(mp->ma_keys)) {
            DK_UNICODE_ENTRIES(mp->ma_keys)[ix].me_value = value;
        } else {
            DK_ENTRIES(mp->ma_keys)[ix].me_value = value;
        }

        NUITKA_DICT_NEXT_VERSION(mp);
        Py_DECREF(old_value);
    }

    return 0;
}
#endif

static int Nuitka_DictDeleteItemCompact(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash) {
    PyObject **value_addr;
    Py_ssize_t ix = Nuitka_PyDictLookup(mp, key, hash, &value_addr);

    if (unlikely(ix == DKIX_ERROR)) {
        return -1;
    }

    if (ix < 0 || *value_addr == NULL) {
        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);
        return -1;
    }

    PyObject *old_value = *value_addr;

    if (mp->ma_values != NULL) {
        mp->ma_values->values[ix] = NULL;
        Nuitka_DictValuesDeleteFromInsertionOrder(mp->ma_values, ix);
        mp->ma_used--;
        NUITKA_DICT_NEXT_VERSION(mp);
        Py_DECREF(old_value);

        return 0;
    }

    Py_ssize_t hashpos = Nuitka_DictFindIndex(mp->ma_keys, hash, ix);
    Nuitka_DictKeysSetIndex(mp->ma_keys, hashpos, DKIX_DUMMY);
    mp->ma_keys->dk_version = 0;

    PyObject *old_key;

    if (DK_IS_UNICODE(mp->ma_keys)) {
        PyDictUnicodeEntry *entry = &DK_UNICODE_ENTRIES(mp->ma_keys)[ix];

        old_key = entry->me_key;
        entry->me_key = NULL;
        entry->me_value = NULL;
    } else {
        PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[ix];

        old_key = entry->me_key;
        entry->me_key = NULL;
        entry->me_value = NULL;
        entry->me_hash = 0;
    }

    mp->ma_used--;
    NUITKA_DICT_NEXT_VERSION(mp);

    Py_DECREF(old_key);
    Py_DECREF(old_value);

    return 0;
}

#elif PYTHON_VERSION >= 0x360 && !defined(Py_GIL_DISABLED)

#define NUITKA_DICT_MINSIZE 8

#ifndef PERTURB_SHIFT
#define PERTURB_SHIFT 5
#endif

#ifndef DKIX_EMPTY
#define DKIX_EMPTY (-1)
#define DKIX_DUMMY (-2)
#define DKIX_ERROR (-3)
#endif

#if PYTHON_VERSION < 0x370
#define NUITKA_DICT_INDICES(keys) ((keys)->dk_indices.as_1)
#else
#define NUITKA_DICT_INDICES(keys) ((keys)->dk_indices)
#endif

static PyDictKeysObject *Nuitka_DictGetEmptyKeys(void) {
    if (const_dict_empty == NULL) {
        return NULL;
    }

    return ((PyDictObject *)const_dict_empty)->ma_keys;
}

static bool Nuitka_DictKeysIsEmpty(PyDictKeysObject *keys) { return keys->dk_usable == 0 && keys->dk_nentries == 0; }

static Py_ssize_t Nuitka_DictCalculateKeysize(Py_ssize_t minused) {
    Py_ssize_t new_size;

    for (new_size = NUITKA_DICT_MINSIZE; new_size <= minused && new_size > 0; new_size <<= 1) {
    }

    if (new_size <= 0) {
        new_size = 0;
    }

    return new_size;
}

static Py_ssize_t Nuitka_DictKeysGetIndex(PyDictKeysObject *keys, Py_ssize_t i) {
    size_t size = (size_t)DK_SIZE(keys);

    if (size <= 0xff) {
        return ((int8_t *)NUITKA_DICT_INDICES(keys))[i];
    } else if (size <= 0xffff) {
        return ((int16_t *)NUITKA_DICT_INDICES(keys))[i];
    }
#if SIZEOF_VOID_P > 4
    else if (size <= 0xffffffff) {
        return ((int32_t *)NUITKA_DICT_INDICES(keys))[i];
    } else {
        return ((int64_t *)NUITKA_DICT_INDICES(keys))[i];
    }
#else
    else {
        return ((int32_t *)NUITKA_DICT_INDICES(keys))[i];
    }
#endif
}

static void Nuitka_DictKeysSetIndex(PyDictKeysObject *keys, Py_ssize_t i, Py_ssize_t ix) {
    size_t size = (size_t)DK_SIZE(keys);

    if (size <= 0xff) {
        ((int8_t *)NUITKA_DICT_INDICES(keys))[i] = (int8_t)ix;
    } else if (size <= 0xffff) {
        ((int16_t *)NUITKA_DICT_INDICES(keys))[i] = (int16_t)ix;
    }
#if SIZEOF_VOID_P > 4
    else if (size <= 0xffffffff) {
        ((int32_t *)NUITKA_DICT_INDICES(keys))[i] = (int32_t)ix;
    } else {
        ((int64_t *)NUITKA_DICT_INDICES(keys))[i] = (int64_t)ix;
    }
#else
    else {
        ((int32_t *)NUITKA_DICT_INDICES(keys))[i] = (int32_t)ix;
    }
#endif
}

static PyDictKeysObject *Nuitka_DictNewKeysObject(PyThreadState *tstate, Py_ssize_t size) {
    Py_ssize_t usable = DK_USABLE_FRACTION(size);
    Py_ssize_t es;

    if (size <= 0xff) {
        es = 1;
    } else if (size <= 0xffff) {
        es = 2;
    }
#if SIZEOF_VOID_P > 4
    else if (size <= 0xffffffff) {
        es = 4;
    }
#endif
    else {
        es = sizeof(Py_ssize_t);
    }

    size_t keys_size = sizeof(PyDictKeysObject) + (size_t)es * (size_t)size + sizeof(PyDictKeyEntry) * (size_t)usable;

    PyDictKeysObject *keys = _Nuitka_AllocatePyDictKeysObject(tstate, keys_size);

    if (unlikely(keys == NULL)) {
        PyErr_NoMemory();
        return NULL;
    }

    // Account for the newly allocated keys object, like CPython's new_keys_object().
    Nuitka_Py_IncRefTotal(tstate);

    keys->dk_refcnt = 1;
    keys->dk_size = size;
    keys->dk_usable = usable;
    keys->dk_lookup = (dict_lookup_func)Nuitka_GetGenericDictLookup();
    keys->dk_nentries = 0;

    memset(NUITKA_DICT_INDICES(keys), 0xff, (size_t)es * (size_t)size);
    memset(DK_ENTRIES(keys), 0, sizeof(PyDictKeyEntry) * (size_t)usable);

    return keys;
}

static void Nuitka_DictKeysFreeStruct(PyDictKeysObject *keys) { PyObject_Free(keys); }

static void Nuitka_DictValuesFree(PyDictKeysObject *keys, PyDictValues *values) {
    if (values != NULL && Nuitka_DictKeysIsEmpty(keys) == false) {
        PyMem_Free(values);
    }
}

static void Nuitka_DictKeysDecref(PyThreadState *tstate, PyDictKeysObject *keys) {
    CHECK_OBJECT_X(keys);

    if (keys == NULL) {
        return;
    }

#if PYTHON_VERSION < 0x3c0
    // The empty keys object is shared and not immortal before Python 3.12.
    if (keys == Nuitka_DictGetEmptyKeys()) {
        Nuitka_Py_DecRefTotal(tstate);
        keys->dk_refcnt--;
        return;
    }
#endif

    if (Nuitka_DictKeysIsEmpty(keys)) {
        return;
    }

    // Account for the released keys object, like CPython's dictkeys_decref().
    Nuitka_Py_DecRefTotal(tstate);

    assert(keys->dk_refcnt > 0);

    if (--keys->dk_refcnt != 0) {
        return;
    }

    PyDictKeyEntry *entries = DK_ENTRIES(keys);
    Py_ssize_t i, n;

    for (i = 0, n = keys->dk_nentries; i < n; i++) {
        Py_XDECREF(entries[i].me_key);
        Py_XDECREF(entries[i].me_value);
    }

    Nuitka_DictKeysFreeStruct(keys);
}

static Py_ssize_t Nuitka_DictFindEmptySlot(PyDictKeysObject *keys, Py_hash_t hash) {
    size_t mask = (size_t)DK_MASK(keys);
    size_t i = (size_t)hash & mask;

    for (size_t perturb = hash; Nuitka_DictKeysGetIndex(keys, i) >= 0;) {
        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }

    return i;
}

static Py_ssize_t Nuitka_DictFindIndex(PyDictKeysObject *keys, Py_hash_t hash, Py_ssize_t wanted_ix) {
    size_t mask = (size_t)DK_MASK(keys);
    size_t i = (size_t)hash & mask;

    for (size_t perturb = hash;;) {
        Py_ssize_t ix = Nuitka_DictKeysGetIndex(keys, i);

        if (ix == wanted_ix) {
            return i;
        }

        if (ix == DKIX_EMPTY) {
            break;
        }

        perturb >>= PERTURB_SHIFT;
        i = mask & (i * 5 + perturb + 1);
    }

    NUITKA_CANNOT_GET_HERE("Nuitka_DictFindIndex failed");
}

static void Nuitka_DictBuildIndices(PyDictKeysObject *keys, PyDictKeyEntry *entries, Py_ssize_t n) {
    size_t mask = (size_t)DK_MASK(keys);

    for (Py_ssize_t ix = 0; ix != n; ix++, entries++) {
        Py_hash_t hash = entries->me_hash;
        size_t i = (size_t)hash & mask;

        for (size_t perturb = hash; Nuitka_DictKeysGetIndex(keys, i) != DKIX_EMPTY;) {
            perturb >>= PERTURB_SHIFT;
            i = mask & (i * 5 + perturb + 1);
        }

        Nuitka_DictKeysSetIndex(keys, i, ix);
    }
}

static int Nuitka_DictResize(PyThreadState *tstate, PyDictObject *mp, Py_ssize_t new_size) {
    assert(new_size > 0);
    assert((new_size & (new_size - 1)) == 0);

    PyDictKeysObject *oldkeys = mp->ma_keys;
    PyObject **oldvalues = mp->ma_values;

    PyDictKeysObject *new_keys = Nuitka_DictNewKeysObject(tstate, new_size);

    if (unlikely(new_keys == NULL)) {
        return -1;
    }

    Py_ssize_t numentries = mp->ma_used;

    if (oldvalues != NULL) {
        PyDictKeyEntry *oldentries = DK_ENTRIES(oldkeys);
        PyDictKeyEntry *newentries = DK_ENTRIES(new_keys);

        for (Py_ssize_t i = 0; i < numentries; i++) {
            PyObject *key = oldentries[i].me_key;

            Py_INCREF(key);

            newentries[i].me_key = key;
            newentries[i].me_hash = oldentries[i].me_hash;
            newentries[i].me_value = oldvalues[i];
        }

        Nuitka_DictBuildIndices(new_keys, newentries, numentries);

        Nuitka_DictValuesFree(oldkeys, oldvalues);
        Nuitka_DictKeysDecref(tstate, oldkeys);
    } else {
        PyDictKeyEntry *oldentries = DK_ENTRIES(oldkeys);
        PyDictKeyEntry *newentries = DK_ENTRIES(new_keys);

        if (oldkeys->dk_nentries == numentries) {
            memcpy(newentries, oldentries, (size_t)numentries * sizeof(PyDictKeyEntry));
        } else {
            PyDictKeyEntry *entry = oldentries;

            for (Py_ssize_t i = 0; i < numentries; i++) {
                while (entry->me_value == NULL) {
                    entry++;
                }

                newentries[i] = *entry++;
            }
        }

        Nuitka_DictBuildIndices(new_keys, newentries, numentries);

        if (oldkeys == Nuitka_DictGetEmptyKeys()) {
#if PYTHON_VERSION < 0x3c0
            // Older Python versions release the reference to the empty keys object here.
            Nuitka_Py_DecRefTotal(tstate);
            oldkeys->dk_refcnt--;
#endif
        } else if (Nuitka_DictKeysIsEmpty(oldkeys) == false) {
            assert(oldkeys->dk_refcnt == 1);

            Nuitka_Py_DecRefTotal(tstate);

            Nuitka_DictKeysFreeStruct(oldkeys);
        }
    }

    mp->ma_keys = new_keys;
    mp->ma_values = NULL;

    new_keys->dk_usable -= numentries;
    new_keys->dk_nentries = numentries;

    return 0;
}

static int Nuitka_DictInsertionResize(PyThreadState *tstate, PyDictObject *mp) {
#if PYTHON_VERSION < 0x370
    return Nuitka_DictResize(tstate, mp, Nuitka_DictCalculateKeysize(mp->ma_used * 2 + (DK_SIZE(mp->ma_keys) >> 1)));
#else
    return Nuitka_DictResize(tstate, mp, Nuitka_DictCalculateKeysize(mp->ma_used * 3));
#endif
}

static int Nuitka_DictSetItemCompact(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash,
                                     PyObject *value) {
    PyObject *old_value = NULL;

#if PYTHON_VERSION < 0x370
    PyObject **value_addr = NULL;
#endif

    if (mp->ma_values != NULL && !PyUnicode_CheckExact(key)) {
        if (Nuitka_DictInsertionResize(tstate, mp) < 0) {
            return -1;
        }
    }

#if PYTHON_VERSION < 0x370
    NUITKA_MAY_BE_UNUSED Py_ssize_t hashpos;
    Py_ssize_t ix = mp->ma_keys->dk_lookup(mp, key, hash, &value_addr, &hashpos);

    if (unlikely(ix == DKIX_ERROR)) {
        return -1;
    }

    if (value_addr != NULL) {
        old_value = *value_addr;
    }
#else
    Py_ssize_t ix = mp->ma_keys->dk_lookup(mp, key, hash, &old_value);

    if (unlikely(ix == DKIX_ERROR)) {
        return -1;
    }
#endif

    NUITKA_DICT_MAINTAIN_TRACKING(mp, key, value);

    if (mp->ma_values != NULL && ((ix >= 0 && old_value == NULL && mp->ma_used != ix) ||
                                  (ix == DKIX_EMPTY && mp->ma_used != mp->ma_keys->dk_nentries))) {
        if (Nuitka_DictInsertionResize(tstate, mp) < 0) {
            return -1;
        }

        ix = DKIX_EMPTY;
        old_value = NULL;
    }

    if (ix == DKIX_EMPTY) {
        assert(old_value == NULL);

        if (mp->ma_keys->dk_usable <= 0) {
            if (Nuitka_DictInsertionResize(tstate, mp) < 0) {
                return -1;
            }
        }

        if (!PyUnicode_CheckExact(key)) {
            mp->ma_keys->dk_lookup = (dict_lookup_func)Nuitka_GetGenericDictLookup();
        }

        Py_ssize_t new_hashpos = Nuitka_DictFindEmptySlot(mp->ma_keys, hash);
        PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[mp->ma_keys->dk_nentries];

        Nuitka_DictKeysSetIndex(mp->ma_keys, new_hashpos, mp->ma_keys->dk_nentries);

        Py_INCREF(key);
        Py_INCREF(value);

        entry->me_key = key;
        entry->me_hash = hash;

        if (mp->ma_values != NULL) {
            assert(mp->ma_values[mp->ma_keys->dk_nentries] == NULL);
            mp->ma_values[mp->ma_keys->dk_nentries] = value;
        } else {
            entry->me_value = value;
        }

        mp->ma_used++;
        NUITKA_DICT_NEXT_VERSION(mp);
        mp->ma_keys->dk_usable--;
        mp->ma_keys->dk_nentries++;

        return 0;
    }

    if (old_value != value) {
        Py_INCREF(value);

        if (mp->ma_values != NULL) {
            mp->ma_values[ix] = value;

            if (old_value == NULL) {
                assert(ix == mp->ma_used);
                mp->ma_used++;
            }
        } else {
            assert(old_value != NULL);
            DK_ENTRIES(mp->ma_keys)[ix].me_value = value;
        }

        NUITKA_DICT_NEXT_VERSION(mp);
        Py_XDECREF(old_value);
    }

    return 0;
}

static int Nuitka_DictDeleteItemCompact(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash) {
    PyObject *old_value = NULL;

#if PYTHON_VERSION < 0x370
    PyObject **value_addr = NULL;
    NUITKA_MAY_BE_UNUSED Py_ssize_t hashpos;
    Py_ssize_t ix = mp->ma_keys->dk_lookup(mp, key, hash, &value_addr, &hashpos);

    if (unlikely(ix == DKIX_ERROR)) {
        return -1;
    }

    if (value_addr != NULL) {
        old_value = *value_addr;
    }
#else
    Py_ssize_t ix = mp->ma_keys->dk_lookup(mp, key, hash, &old_value);

    if (unlikely(ix == DKIX_ERROR)) {
        return -1;
    }
#endif

    if (ix < 0 || old_value == NULL) {
        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);
        return -1;
    }

    if (mp->ma_values != NULL) {
        if (Nuitka_DictResize(tstate, mp, DK_SIZE(mp->ma_keys)) < 0) {
            return -1;
        }

#if PYTHON_VERSION < 0x370
        ix = mp->ma_keys->dk_lookup(mp, key, hash, &value_addr, &hashpos);
#else
        ix = mp->ma_keys->dk_lookup(mp, key, hash, &old_value);
#endif
        assert(ix >= 0);
    }

    Py_ssize_t found_hashpos = Nuitka_DictFindIndex(mp->ma_keys, hash, ix);
    Nuitka_DictKeysSetIndex(mp->ma_keys, found_hashpos, DKIX_DUMMY);

    mp->ma_keys->dk_lookup = (dict_lookup_func)Nuitka_GetGenericDictLookup();

    PyDictKeyEntry *entry = &DK_ENTRIES(mp->ma_keys)[ix];
    PyObject *old_key = entry->me_key;

    entry->me_key = NULL;
    entry->me_value = NULL;

    mp->ma_used--;
    NUITKA_DICT_NEXT_VERSION(mp);

    Py_DECREF(old_key);
    Py_DECREF(old_value);

    return 0;
}

#endif

#if PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x360

#ifndef PERTURB_SHIFT
#define PERTURB_SHIFT 5
#endif

#define NUITKA_DICT_MINSIZE 8

static PyDictKeysObject *Nuitka_DictGetEmptyKeys(void) {
    if (const_dict_empty == NULL) {
        return NULL;
    }

    return ((PyDictObject *)const_dict_empty)->ma_keys;
}

static bool Nuitka_DictKeysIsEmpty(PyDictKeysObject *keys) { return keys->dk_size == 1; }

static Py_ssize_t Nuitka_DictCalculateKeysize(Py_ssize_t minused) {
    Py_ssize_t new_size;

    for (new_size = NUITKA_DICT_MINSIZE; new_size <= minused && new_size > 0; new_size <<= 1) {
    }

    if (new_size <= 0) {
        new_size = 0;
    }

    return new_size;
}

static PyDictKeysObject *Nuitka_DictNewKeysObject(PyThreadState *tstate, Py_ssize_t size) {
    assert(size >= NUITKA_DICT_MINSIZE);
    assert((size & (size - 1)) == 0);

    size_t keys_size = sizeof(PyDictKeysObject) + sizeof(PyDictKeyEntry) * ((size_t)size - 1);

    PyDictKeysObject *keys = (PyDictKeysObject *)NuitkaMem_Malloc(keys_size);

    if (unlikely(keys == NULL)) {
        PyErr_NoMemory();
        return NULL;
    }

    // Account for the newly allocated keys object, like CPython's new_keys_object().
    Nuitka_Py_IncRefTotal(tstate);

    keys->dk_refcnt = 1;
    keys->dk_size = size;
    // Python 3.4/3.5 round the usable fraction up, unlike later versions.
    keys->dk_usable = (((size << 1) + 1) / 3);
    keys->dk_lookup = (dict_lookup_func)Nuitka_GetGenericDictLookup();

    PyDictKeyEntry *entries = DK_ENTRIES(keys);

    entries[0].me_hash = 0;

    for (Py_ssize_t i = 0; i < size; i++) {
        entries[i].me_key = NULL;
        entries[i].me_value = NULL;
    }

    return keys;
}

static void Nuitka_DictKeysFreeStruct(PyDictKeysObject *keys) { PyMem_Free(keys); }

static void Nuitka_DictValuesFree(PyDictKeysObject *keys, PyDictValues *values) {
    if (values != NULL && Nuitka_DictKeysIsEmpty(keys) == false) {
        PyMem_Free(values);
    }
}

static void Nuitka_DictKeysDecref(PyThreadState *tstate, PyDictKeysObject *keys) {
    CHECK_OBJECT_X(keys);

    if (keys == NULL) {
        return;
    }

#if PYTHON_VERSION < 0x3c0
    // The empty keys object is shared and not immortal before Python 3.12.
    if (keys == Nuitka_DictGetEmptyKeys()) {
        Nuitka_Py_DecRefTotal(tstate);
        keys->dk_refcnt--;
        return;
    }
#endif

    if (Nuitka_DictKeysIsEmpty(keys)) {
        return;
    }

    // Account for the released keys object, like CPython's dictkeys_decref().
    Nuitka_Py_DecRefTotal(tstate);

    assert(keys->dk_refcnt > 0);

    if (--keys->dk_refcnt != 0) {
        return;
    }

    PyDictKeyEntry *entries = DK_ENTRIES(keys);
    Py_ssize_t size = DK_SIZE(keys);

    for (Py_ssize_t i = 0; i < size; i++) {
        Py_XDECREF(entries[i].me_key);
        Py_XDECREF(entries[i].me_value);
    }

    Nuitka_DictKeysFreeStruct(keys);
}

static PyDictKeyEntry *Nuitka_DictFindEmptySlot(PyDictObject *mp, Py_hash_t hash, PyObject ***value_addr) {
    PyDictKeysObject *keys = mp->ma_keys;
    size_t mask = (size_t)DK_SIZE(keys) - 1;
    PyDictKeyEntry *entries = DK_ENTRIES(keys);
    size_t i = (size_t)hash & mask;
    PyDictKeyEntry *entry = &entries[i];

    for (size_t perturb = hash; entry->me_key != NULL; perturb >>= PERTURB_SHIFT) {
        i = (i << 2) + i + perturb + 1;
        entry = &entries[i & mask];
    }

    if (mp->ma_values != NULL) {
        *value_addr = &mp->ma_values[i & mask];
    } else {
        *value_addr = &entry->me_value;
    }

    return entry;
}

static void Nuitka_DictInsertDictClean(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject *value) {
    PyDictKeysObject *keys = mp->ma_keys;
    size_t mask = (size_t)DK_SIZE(keys) - 1;
    PyDictKeyEntry *entries = DK_ENTRIES(keys);
    size_t i = (size_t)hash & mask;
    PyDictKeyEntry *entry = &entries[i];

    for (size_t perturb = hash; entry->me_key != NULL; perturb >>= PERTURB_SHIFT) {
        i = (i << 2) + i + perturb + 1;
        entry = &entries[i & mask];
    }

    assert(entry->me_value == NULL);

    entry->me_key = key;
    entry->me_hash = hash;
    entry->me_value = value;
}

static int Nuitka_DictResize(PyThreadState *tstate, PyDictObject *mp, Py_ssize_t minused) {
    Py_ssize_t new_size = Nuitka_DictCalculateKeysize(minused);

    if (unlikely(new_size <= 0)) {
        PyErr_NoMemory();
        return -1;
    }

    PyDictKeysObject *oldkeys = mp->ma_keys;
    PyObject **oldvalues = mp->ma_values;
    Py_ssize_t oldsize = DK_SIZE(oldkeys);

    PyDictKeysObject *new_keys = Nuitka_DictNewKeysObject(tstate, new_size);

    if (unlikely(new_keys == NULL)) {
        return -1;
    }

    Py_ssize_t numentries = mp->ma_used;

    mp->ma_keys = new_keys;
    mp->ma_values = NULL;

    if (oldvalues != NULL) {
        for (Py_ssize_t i = 0; i < oldsize; i++) {
            if (oldvalues[i] != NULL) {
                Py_INCREF(DK_ENTRIES(oldkeys)[i].me_key);
                DK_ENTRIES(oldkeys)[i].me_value = oldvalues[i];
            }
        }
    }

    for (Py_ssize_t i = 0; i < oldsize; i++) {
        PyDictKeyEntry *entry = &DK_ENTRIES(oldkeys)[i];

        if (entry->me_value != NULL) {
            assert(entry->me_key != Nuitka_GetDictDummy());

            Nuitka_DictInsertDictClean(mp, entry->me_key, entry->me_hash, entry->me_value);
        }
    }

    new_keys->dk_usable -= numentries;

    if (oldvalues != NULL) {
        for (Py_ssize_t i = 0; i < oldsize; i++) {
            DK_ENTRIES(oldkeys)[i].me_value = NULL;
        }

        Nuitka_DictValuesFree(oldkeys, oldvalues);
        Nuitka_DictKeysDecref(tstate, oldkeys);
    } else {
        if (oldkeys == Nuitka_DictGetEmptyKeys()) {
#if PYTHON_VERSION < 0x3c0
            // Older Python versions release the reference to the empty keys object here.
            Nuitka_Py_DecRefTotal(tstate);
            oldkeys->dk_refcnt--;
#endif
        } else if (Nuitka_DictKeysIsEmpty(oldkeys) == false) {
            assert(oldkeys->dk_refcnt == 1);

            Nuitka_Py_DecRefTotal(tstate);

            Nuitka_DictKeysFreeStruct(oldkeys);
        }
    }

    return 0;
}

static Py_ssize_t Nuitka_DictGrowthRate(PyDictObject *mp) { return mp->ma_used * 2 + (DK_SIZE(mp->ma_keys) >> 1); }

static int Nuitka_DictSetItemCompact(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash,
                                     PyObject *value) {
    PyObject **value_addr;

    if (mp->ma_values != NULL && !PyUnicode_CheckExact(key)) {
        if (Nuitka_DictResize(tstate, mp, Nuitka_DictGrowthRate(mp)) < 0) {
            return -1;
        }
    }

    PyDictKeyEntry *entry = mp->ma_keys->dk_lookup(mp, key, hash, &value_addr);

    if (unlikely(entry == NULL)) {
        return -1;
    }

    NUITKA_DICT_MAINTAIN_TRACKING(mp, key, value);

    PyObject *old_value = *value_addr;

    if (old_value != NULL) {
        Py_INCREF(value);
        *value_addr = value;
        NUITKA_DICT_NEXT_VERSION(mp);
        Py_DECREF(old_value);

        return 0;
    }

    if (entry->me_key == NULL) {
        if (mp->ma_keys->dk_usable <= 0) {
            if (Nuitka_DictResize(tstate, mp, Nuitka_DictGrowthRate(mp)) < 0) {
                return -1;
            }

            entry = Nuitka_DictFindEmptySlot(mp, hash, &value_addr);
        }

        Py_INCREF(key);
        Py_INCREF(value);

        *value_addr = value;
        mp->ma_keys->dk_usable--;
        mp->ma_used++;

        entry->me_key = key;
        entry->me_hash = hash;

        NUITKA_DICT_NEXT_VERSION(mp);

        return 0;
    }

    Py_INCREF(value);

    *value_addr = value;
    mp->ma_used++;

    if (entry->me_key == Nuitka_GetDictDummy()) {
        Py_INCREF(key);

        entry->me_key = key;
        entry->me_hash = hash;
        Py_DECREF(Nuitka_GetDictDummy());
    } else {
        assert(mp->ma_values != NULL);
    }

    NUITKA_DICT_NEXT_VERSION(mp);

    return 0;
}

static int Nuitka_DictDeleteItemCompact(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash) {
    PyObject **value_addr;
    PyDictKeyEntry *entry = mp->ma_keys->dk_lookup(mp, key, hash, &value_addr);

    if (unlikely(entry == NULL)) {
        return -1;
    }

    PyObject *old_value = *value_addr;

    if (old_value == NULL) {
        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);
        return -1;
    }

    *value_addr = NULL;
    mp->ma_used--;
    NUITKA_DICT_NEXT_VERSION(mp);

    if (mp->ma_values == NULL) {
        mp->ma_keys->dk_lookup = (dict_lookup_func)Nuitka_GetGenericDictLookup();

        PyObject *old_key = entry->me_key;
        PyObject *dict_dummy = Nuitka_GetDictDummy();

        Py_INCREF(dict_dummy);
        entry->me_key = dict_dummy;
        Py_DECREF(old_key);
    }

    Py_DECREF(old_value);

    return 0;
}

#endif

#if PYTHON_VERSION < 0x300

#define NUITKA_DICT_MINSIZE 8

#ifndef PERTURB_SHIFT
#define PERTURB_SHIFT 5
#endif

static void Nuitka_DictInsertDictClean(PyDictObject *mp, PyObject *key, Py_hash_t hash, PyObject *value) {
    size_t mask = (size_t)mp->ma_mask;
    PyDictEntry *entries = mp->ma_table;
    size_t i = (size_t)hash & mask;
    PyDictEntry *entry = &entries[i];

    for (size_t perturb = hash; entry->me_key != NULL; perturb >>= PERTURB_SHIFT) {
        i = (i << 2) + i + perturb + 1;
        entry = &entries[i & mask];
    }

    assert(entry->me_value == NULL);

    mp->ma_fill++;

    entry->me_key = key;
    entry->me_hash = (Py_ssize_t)hash;
    entry->me_value = value;

    mp->ma_used++;
}

static int Nuitka_DictResizeLegacy(PyDictObject *mp, Py_ssize_t minused) {
    Py_ssize_t new_size;
    size_t new_size_bytes;
    PyDictEntry *oldtable, *new_table, *entry;
    Py_ssize_t i;
    int is_oldtable_malloced;
    PyDictEntry small_copy[NUITKA_DICT_MINSIZE];

    assert(minused >= 0);

    for (new_size = NUITKA_DICT_MINSIZE; new_size <= minused && new_size > 0; new_size <<= 1) {
    }

    if (unlikely(new_size <= 0)) {
        PyErr_NoMemory();
        return -1;
    }

    new_size_bytes = sizeof(PyDictEntry) * (size_t)new_size;

    oldtable = mp->ma_table;
    assert(oldtable != NULL);
    is_oldtable_malloced = oldtable != mp->ma_smalltable;

    if (new_size == NUITKA_DICT_MINSIZE) {
        new_table = mp->ma_smalltable;

        if (new_table == oldtable) {
            if (mp->ma_fill == mp->ma_used) {
                return 0;
            }

            assert(mp->ma_fill > mp->ma_used);
            memcpy(small_copy, oldtable, sizeof(small_copy));
            oldtable = small_copy;
        }
    } else {
#if defined(_WIN32)
        // Windows Python 2.x may use a different CRT than the compiled
        // program, so use the allocator functions to stay on CPython's heap.
        new_table = (PyDictEntry *)PyMem_Malloc(new_size_bytes);
#else
        new_table = (PyDictEntry *)PyMem_MALLOC(new_size_bytes);
#endif

        if (unlikely(new_table == NULL)) {
            PyErr_NoMemory();
            return -1;
        }
    }

    assert(new_table != oldtable);
    mp->ma_table = new_table;
    mp->ma_mask = new_size - 1;
    memset(new_table, 0, new_size_bytes);
    mp->ma_used = 0;
    i = mp->ma_fill;
    mp->ma_fill = 0;

    for (entry = oldtable; i > 0; entry++) {
        if (entry->me_value != NULL) {
            --i;
            Nuitka_DictInsertDictClean(mp, entry->me_key, (Py_hash_t)entry->me_hash, entry->me_value);
        } else if (entry->me_key != NULL) {
            --i;
            assert(entry->me_key == Nuitka_GetDictDummy());
            Py_DECREF(entry->me_key);
        }
    }

    if (is_oldtable_malloced) {
#if defined(_WIN32)
        PyMem_Free(oldtable);
#else
        PyMem_FREE(oldtable);
#endif
    }

    return 0;
}

static int Nuitka_DictSetItemLegacy(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash,
                                    PyObject *value) {
    assert(key != Nuitka_GetDictDummy());

    PyDictEntry *entry = (mp->ma_lookup)(mp, key, hash);

    if (unlikely(entry == NULL)) {
        return -1;
    }

    NUITKA_DICT_MAINTAIN_TRACKING(mp, key, value);

    if (entry->me_value != NULL) {
        PyObject *old_value = entry->me_value;

        Py_INCREF(value);
        entry->me_value = value;
        Py_DECREF(old_value);

        return 0;
    }

    Py_INCREF(key);
    Py_INCREF(value);

    if (entry->me_key == NULL) {
        mp->ma_fill++;
    } else {
        assert(entry->me_key == Nuitka_GetDictDummy());
        Py_DECREF(Nuitka_GetDictDummy());
    }

    entry->me_key = key;
    entry->me_hash = (Py_ssize_t)hash;
    entry->me_value = value;
    mp->ma_used++;

    if (mp->ma_fill * 3 >= (mp->ma_mask + 1) * 2) {
        if (Nuitka_DictResizeLegacy(mp, (mp->ma_used > 50000 ? 2 : 4) * mp->ma_used) < 0) {
            return -1;
        }
    }

    return 0;
}

static int Nuitka_DictDeleteItemLegacy(PyThreadState *tstate, PyDictObject *mp, PyObject *key, Py_hash_t hash) {
    PyDictEntry *entry = (mp->ma_lookup)(mp, key, hash);

    if (unlikely(entry == NULL)) {
        return -1;
    }

    if (entry->me_value == NULL) {
        SET_CURRENT_EXCEPTION_KEY_ERROR(tstate, key);
        return -1;
    }

    PyObject *old_key = entry->me_key;
    PyObject *old_value = entry->me_value;
    PyObject *dict_dummy = Nuitka_GetDictDummy();

    Py_INCREF(dict_dummy);
    entry->me_key = dict_dummy;
    entry->me_value = NULL;
    mp->ma_used--;

    Py_DECREF(old_value);
    Py_DECREF(old_key);

    return 0;
}

#endif

bool Nuitka_DictNext(PyObject *dict, Py_ssize_t *pos, PyObject **key_ptr, PyObject **value_ptr) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
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

#if PYTHON_VERSION >= 0x3f0
bool Nuitka_FrozenDictNext(PyObject *frozendict, Py_ssize_t *pos, PyObject **key_ptr, PyObject **value_ptr) {
    CHECK_OBJECT(frozendict);
    assert(PyFrozenDict_CheckExact(frozendict));
    assert(key_ptr != NULL);
    assert(value_ptr != NULL);

    PyDictObject *mp = (PyDictObject *)frozendict;

    // Frozens are always combined dictionaries, there is no split table.
    assert(mp->ma_values == NULL);

    Py_ssize_t i = *pos;
    assert(i >= 0);
    Py_ssize_t n = mp->ma_keys->dk_nentries;

    if (i >= n) {
        return false;
    }

    PyObject *key, *value;

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

    *pos = i + 1;

    *key_ptr = key;
    *value_ptr = value;

    return true;
}
#endif

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
                res = DICT_UPDATE_FROM(tstate, result, seq_obj);
            } else {
                res = DICT_UPDATE_FROM_SEQ(tstate, result, seq_obj);
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

        int res = DICT_UPDATE_FROM(tstate, result, dict_obj);

        if (unlikely(res == -1)) {
            return NULL;
        }
    }

    return result;
}

bool DICT_SET_ITEM(PyObject *dict, PyObject *key, PyObject *value) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    CHECK_OBJECT(key);
    CHECK_OBJECT(value);

#if !defined(Py_GIL_DISABLED) && PYTHON_VERSION >= 0x3c0
    if (unlikely(NUITKA_DICT_IS_WATCHED((PyDictObject *)dict))) {
        return PyDict_Type.tp_as_mapping->mp_ass_subscript(dict, key, value) == 0;
    }
#endif

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT || _NUITKA_EXPERIMENTAL_DISABLE_DICT_ACCESS_OPT
    return PyDict_SetItem(dict, key, value) == 0;
#elif PYTHON_VERSION >= 0x300 && !defined(Py_GIL_DISABLED)
    PyThreadState *tstate = PyThreadState_GET();
    Py_hash_t hash;

    if (unlikely(Nuitka_DictGetHash(tstate, key, &hash) == false)) {
        return false;
    }

#if PYTHON_VERSION >= 0x3d0
    return Nuitka_DictSetItem3x(tstate, (PyDictObject *)dict, key, hash, value) == 0;
#else
    return Nuitka_DictSetItemCompact(tstate, (PyDictObject *)dict, key, hash, value) == 0;
#endif
#elif PYTHON_VERSION < 0x300
    PyThreadState *tstate = PyThreadState_GET();
    Py_hash_t hash;

    if (unlikely(Nuitka_DictGetHash(tstate, key, &hash) == false)) {
        return false;
    }

    return Nuitka_DictSetItemLegacy(tstate, (PyDictObject *)dict, key, hash, value) == 0;
#else
    return PyDict_Type.tp_as_mapping->mp_ass_subscript(dict, key, value) == 0;
#endif
}

bool DICT_SET_ITEM_STRING(PyObject *dict, char const *key, PyObject *value) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    CHECK_OBJECT(value);
    assert(key != NULL);

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT || _NUITKA_EXPERIMENTAL_DISABLE_DICT_ACCESS_OPT
    return PyDict_SetItemString(dict, key, value) == 0;
#else
    PyObject *key_object = Nuitka_String_FromString(key);

    if (unlikely(key_object == NULL)) {
        return false;
    }

    bool result = DICT_SET_ITEM(dict, key_object, value);

    Py_DECREF(key_object);

    return result;
#endif
}

bool DICT_REMOVE_ITEM(PyObject *dict, PyObject *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    CHECK_OBJECT(key);

#if !defined(Py_GIL_DISABLED) && PYTHON_VERSION >= 0x3c0
    if (unlikely(NUITKA_DICT_IS_WATCHED((PyDictObject *)dict))) {
        return PyDict_Type.tp_as_mapping->mp_ass_subscript(dict, key, NULL) == 0;
    }
#endif

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT || _NUITKA_EXPERIMENTAL_DISABLE_DICT_ACCESS_OPT
    return PyDict_DelItem(dict, key) == 0;
#elif PYTHON_VERSION >= 0x300 && !defined(Py_GIL_DISABLED)
    PyThreadState *tstate = PyThreadState_GET();
    Py_hash_t hash;

    if (unlikely(Nuitka_DictGetHash(tstate, key, &hash) == false)) {
        return false;
    }

    return Nuitka_DictDeleteItemCompact(tstate, (PyDictObject *)dict, key, hash) == 0;
#elif PYTHON_VERSION < 0x300
    PyThreadState *tstate = PyThreadState_GET();
    Py_hash_t hash;

    if (unlikely(Nuitka_DictGetHash(tstate, key, &hash) == false)) {
        return false;
    }

    return Nuitka_DictDeleteItemLegacy(tstate, (PyDictObject *)dict, key, hash) == 0;
#else
    return PyDict_Type.tp_as_mapping->mp_ass_subscript(dict, key, NULL) == 0;
#endif
}

bool DICT_REMOVE_ITEM_STRING(PyObject *dict, char const *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    assert(key != NULL);

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT || _NUITKA_EXPERIMENTAL_DISABLE_DICT_ACCESS_OPT
    return PyDict_DelItemString(dict, key) == 0;
#else
    PyObject *key_object = Nuitka_String_FromString(key);

    if (unlikely(key_object == NULL)) {
        return false;
    }

    bool result = DICT_REMOVE_ITEM(dict, key_object);

    Py_DECREF(key_object);

    return result;
#endif
}

PyObject *DICT_GET_ITEM_STRING(PyObject *dict, char const *key) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    assert(key != NULL);

#if _NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT || _NUITKA_EXPERIMENTAL_DISABLE_DICT_ACCESS_OPT
    return PyDict_GetItemString(dict, key);
#else
    PyObject *key_object = Nuitka_String_FromString(key);

    if (unlikely(key_object == NULL)) {
        return NULL;
    }

    PyThreadState *tstate = PyThreadState_GET();
    PyObject *result = DICT_GET_ITEM0(tstate, dict, key_object);

    Py_DECREF(key_object);

    return result;
#endif
}

#if !_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT && PYTHON_VERSION >= 0x3a0 && !defined(Py_GIL_DISABLED)
static bool Nuitka_DictCopyWorthy(PyDictObject *mp) {
    PyDictKeysObject *keys = mp->ma_keys;

    if (mp->ma_values != NULL) {
        return false;
    }

    if (mp->ma_used != keys->dk_nentries) {
        return false;
    }

    if (DK_SIZE(keys) == 8) {
        return true;
    }

    return DK_USABLE_FRACTION(DK_SIZE(keys) / 2) < mp->ma_used;
}

bool DICT_CLONE_INTO(PyThreadState *tstate, PyObject *target, PyObject *dict_value) {
    CHECK_OBJECT(target);
    assert(PyDict_CheckExact(target));
    CHECK_OBJECT(dict_value);
    assert(PyDict_CheckExact(dict_value));

    PyDictObject *result_mp = (PyDictObject *)target;
    PyDictObject *dict_mp = (PyDictObject *)dict_value;

    assert(result_mp->ma_used == 0);
    assert(dict_mp->ma_values == NULL);
    assert(IS_COMPACT(dict_mp));
    assert(dict_mp->ma_keys->dk_refcnt == 1);

    Nuitka_DictValuesFree(result_mp->ma_keys, result_mp->ma_values);
    Nuitka_DictKeysDecref(tstate, result_mp->ma_keys);

    result_mp->ma_values = NULL;
    result_mp->ma_used = dict_mp->ma_used;

    Py_ssize_t keys_size = _Nuitka_Py_PyDict_KeysSize(dict_mp->ma_keys);
    result_mp->ma_keys = _Nuitka_AllocatePyDictKeysObject(tstate, keys_size);
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
            Py_INCREF(entry->me_key);
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
            Py_INCREF(*key_ptr);
        }

        value_ptr += entry_size;
        key_ptr += entry_size;
    }
#endif

    // Account for the newly allocated keys object, like CPython's new_keys_object().
    Nuitka_Py_IncRefTotal(tstate);

    if (_PyObject_GC_IS_TRACKED(dict_mp) && !_PyObject_GC_IS_TRACKED(result_mp)) {
        Nuitka_GC_Track(result_mp);
    }

    NUITKA_DICT_NEXT_VERSION(result_mp);

    return true;
}
#endif

int DICT_UPDATE_FROM(PyThreadState *tstate, PyObject *dict, PyObject *other) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    CHECK_OBJECT(other);

    if (other == dict) {
        return 0;
    }

    if (PyDict_Check(other) && ((PyDictObject *)other)->ma_used == 0) {
        return 0;
    }

#if PYTHON_VERSION < 0x300
    if (PyDict_Check(other)) {
#else
    if (PyDict_Check(other) && Py_TYPE(other)->tp_iter == PyDict_Type.tp_iter) {
        PyDictObject *other_mp = (PyDictObject *)other;
#endif

#if !_NUITKA_EXPERIMENTAL_DISABLE_DICT_OPT && PYTHON_VERSION >= 0x3a0 && !defined(Py_GIL_DISABLED)
        PyDictObject *target_mp = (PyDictObject *)dict;

        if (target_mp->ma_used == 0 &&
            (target_mp->ma_values == NULL || target_mp->ma_keys == Nuitka_DictGetEmptyKeys()) &&
            PyDict_CheckExact(other) && Nuitka_DictCopyWorthy(other_mp) && NUITKA_DICT_IS_WATCHED(target_mp) == false) {
            if (unlikely(DICT_CLONE_INTO(tstate, dict, other) == false)) {
                return -1;
            }

            return 0;
        }
#endif

#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION < 0x360
        Py_ssize_t orig_size = DK_SIZE(other_mp->ma_keys);
#elif PYTHON_VERSION < 0x3d0
        Py_ssize_t orig_size = other_mp->ma_keys->dk_nentries;
#else
        Py_ssize_t orig_size = other_mp->ma_used;
#endif
#endif
        Py_ssize_t pos = 0;
        PyObject *key, *value;

        while (Nuitka_DictNext(other, &pos, &key, &value)) {
            Py_INCREF(key);
            Py_INCREF(value);

            if (DICT_SET_ITEM(dict, key, value) == false) {
                Py_DECREF(key);
                Py_DECREF(value);
                return -1;
            }

            Py_DECREF(key);
            Py_DECREF(value);

#if PYTHON_VERSION >= 0x300
#if PYTHON_VERSION < 0x360
            if (orig_size != DK_SIZE(other_mp->ma_keys)) {
#elif PYTHON_VERSION < 0x3d0
            if (orig_size != other_mp->ma_keys->dk_nentries) {
#else
            if (orig_size != other_mp->ma_used) {
#endif
                PyErr_SetString(PyExc_RuntimeError, "dict mutated during update");
                return -1;
            }
#endif
        }

        if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
            return -1;
        }

        return 0;
    }

    PyObject *keys = Nuitka_Mapping_Keys(tstate, other);

    if (keys == NULL) {
        return -1;
    }

    PyObject *iter = MAKE_ITERATOR(tstate, keys);
    Py_DECREF(keys);

    if (iter == NULL) {
        return -1;
    }

    PyObject *key;

    while ((key = ITERATOR_NEXT(iter)) != NULL) {
        PyObject *value = LOOKUP_SUBSCRIPT(tstate, other, key);

        if (value == NULL) {
            Py_DECREF(key);
            Py_DECREF(iter);
            return -1;
        }

        bool status = DICT_SET_ITEM(dict, key, value);

        Py_DECREF(key);
        Py_DECREF(value);

        if (unlikely(status == false)) {
            Py_DECREF(iter);
            return -1;
        }
    }

    Py_DECREF(iter);

    if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
        if (!CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate)) {
            return -1;
        }
    }

    return 0;
}

int DICT_UPDATE_FROM_SEQ(PyThreadState *tstate, PyObject *dict, PyObject *seq) {
    CHECK_OBJECT(dict);
    assert(PyDict_Check(dict));
    CHECK_OBJECT(seq);

    PyObject *iter = MAKE_ITERATOR(tstate, seq);

    if (iter == NULL) {
        return -1;
    }

    Py_ssize_t i = 0;

    for (;; i++) {
        PyObject *item = ITERATOR_NEXT(iter);

        if (item == NULL) {
            if (unlikely(HAS_ERROR_OCCURRED(tstate))) {
                if (CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate)) {
                    break;
                }

                Py_DECREF(iter);
                return -1;
            }

            break;
        }

        PyObject *fast = PySequence_Fast(item, "");

        if (fast == NULL) {
            if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, GET_ERROR_OCCURRED(tstate), PyExc_TypeError)) {
                PyErr_Format(PyExc_TypeError, "cannot convert dictionary update sequence element #%zd to a sequence",
                             i);
            }

            Py_DECREF(item);
            Py_DECREF(iter);
            return -1;
        }

        Py_ssize_t n = PySequence_Fast_GET_SIZE(fast);

        if (n != 2) {
            PyErr_Format(PyExc_ValueError, "dictionary update sequence element #%zd has length %zd; 2 is required", i,
                         n);
            Py_DECREF(fast);
            Py_DECREF(item);
            Py_DECREF(iter);
            return -1;
        }

        PyObject *key = PySequence_Fast_GET_ITEM(fast, 0);
        PyObject *value = PySequence_Fast_GET_ITEM(fast, 1);

        Py_INCREF(key);
        Py_INCREF(value);

        bool status = DICT_SET_ITEM(dict, key, value);

        Py_DECREF(key);
        Py_DECREF(value);
        Py_DECREF(fast);
        Py_DECREF(item);

        if (unlikely(status == false)) {
            Py_DECREF(iter);
            return -1;
        }
    }

    Py_DECREF(iter);

    return 0;
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
#if PYTHON_VERSION < 0x3b0
    result_mp->ma_values = empty_dict_mp->ma_values;
#else
    assert(empty_dict_mp->ma_values == NULL);
    result_mp->ma_values = NULL;
#endif
    result_mp->ma_used = 0;
#if PYTHON_VERSION >= 0x3c0 && PYTHON_VERSION < 0x3e0
    result_mp->ma_version_tag = DICT_NEXT_VERSION(_PyInterpreterState_GET());
#elif PYTHON_VERSION >= 0x360 && PYTHON_VERSION < 0x3e0
    result_mp->ma_version_tag = 1;
#endif

    // Key reference needs to be counted on older Python
#if PYTHON_VERSION < 0x3c0
    Nuitka_Py_IncRefTotal(tstate);
#endif

    // Python 3.14 tracks even empty dicts, older versions did not.
#if PYTHON_VERSION >= 0x3e0
    Nuitka_GC_Track(result_mp);
#endif

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

        bool res = DICT_SET_ITEM(result, key, value);

        if (unlikely(res == false)) {
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

            bool res = DICT_SET_ITEM(result, key, value);

            if (unlikely(res == false)) {
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

            bool res = DICT_SET_ITEM_STRING(result, keys[i], value);

            if (unlikely(res == false)) {
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
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
